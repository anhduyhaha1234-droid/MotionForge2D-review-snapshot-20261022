"""Synthetic, CPU-only negative and positive tests for G2-B1 readiness."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import unittest
from uuid import uuid4

from PIL import Image

import readiness as R


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def fixture() -> tuple[Path, Path, str, tuple[int, str]]:
    root = R.WRITE_ROOT / "fixtures" / uuid4().hex
    root.mkdir(parents=True)
    chunks = []
    cursor = R.SPAN_A
    for i in range(21, 75):
        length = 167 if i <= 72 else 175 if i == 73 else 301
        end = cursor + length
        chunks.append({"unit_id": f"S{i:04d}", "start_frame": cursor, "end_frame": end, "frames": length, "trim": {"start_frame": cursor, "end_frame": end}})
        cursor = end
    assert chunks[-1]["start_frame"] == 11679 and cursor == 11980
    plan_path = root / R.PLAN_REL
    write_json(plan_path, {"chunks": chunks})

    cast_dir = root / "task/corrections/identity/r4/assets/cast_b"
    cast_dir.mkdir(parents=True)
    entities = {}
    for i in range(1, 8):
        views = {}
        for view in ("front", "profile"):
            name = f"B{i:02d}_{view}.png"
            path = cast_dir / name
            seed = f"{i}-{view}".encode()
            raw = hashlib.shake_256(seed).digest(64 * 64 * 3)
            Image.frombytes("RGB", (64, 64), raw).save(path)
            assert path.stat().st_size > 1024
            views[view] = {"file": name, "sha256": sha(path)}
        entities[f"E{i}"] = views
    atlas = root / "task/corrections/identity/r6/cast_atlas.json"
    write_json(atlas, {"entities": entities})
    source = root / R.SOURCE_REL
    source.parent.mkdir(parents=True)
    source.write_bytes(b"synthetic-source-frames-no-decoder")
    source_pin = (source.stat().st_size, sha(source))

    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path not in (source,):
            files.append({"relative": path.relative_to(root).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
    manifest = root / "MANIFEST.json"
    write_json(manifest, {"total_files": len(files), "files": files})
    return root, atlas, sha(manifest), source_pin


class ReadinessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root, self.atlas, self.manifest_sha, self.source_pin = fixture()
        self.cast_dir = self.root / "task/corrections/identity/r4/assets/cast_b"

    def tearDown(self) -> None:
        expected_parent = (R.WRITE_ROOT / "fixtures").resolve(strict=True)
        actual = self.root.resolve(strict=True)
        if actual.parent != expected_parent:
            raise AssertionError(f"fixture cleanup escaped write-set: {actual}")
        shutil.rmtree(actual)

    def test_positive_synthetic(self) -> None:
        self.assertEqual(R.check_manifest_tree(self.root, self.manifest_sha, self.source_pin)["status"], "PASS")
        plan = R.check_plan(self.root / R.PLAN_REL)
        self.assertEqual(plan["status"], "PASS", plan)
        self.assertEqual(plan["evidence"]["last_shot"]["pilot_frames"], 141)
        self.assertEqual(plan["evidence"]["last_shot_excluded_tail_frames"], 160)
        self.assertTrue(all(c["status"] == "PASS" for c in R.check_cast(self.atlas, sha(self.atlas), self.cast_dir)))

    def test_missing_cast(self) -> None:
        path = self.cast_dir / "B01_front.png"
        path.rename(path.with_suffix(".missing"))
        checks = R.check_cast(self.atlas, sha(self.atlas), self.cast_dir)
        self.assertEqual([c for c in checks if c["id"] == "cast:B01_front.png"][0]["status"], "FAIL")

    def test_tampered_cast(self) -> None:
        path = self.cast_dir / "B01_front.png"
        path.write_bytes(path.read_bytes() + b"tamper")
        checks = R.check_cast(self.atlas, sha(self.atlas), self.cast_dir)
        self.assertEqual([c for c in checks if c["id"] == "cast:B01_front.png"][0]["status"], "FAIL")

    def test_tiny_fixture_rejected(self) -> None:
        path = self.cast_dir / "B01_front.png"
        path.write_bytes(b"fixture-not-png")
        checks = R.check_cast(self.atlas, sha(self.atlas), self.cast_dir)
        self.assertEqual([c for c in checks if c["id"] == "cast:B01_front.png"][0]["status"], "FAIL")

    def test_source_mismatch(self) -> None:
        (self.root / R.SOURCE_REL).write_bytes(b"changed")
        self.assertEqual(R.check_manifest_tree(self.root, self.manifest_sha, self.source_pin)["status"], "FAIL")

    def test_candidate_inventory_extra(self) -> None:
        (self.root / "extra.txt").write_text("extra", encoding="utf-8")
        result = R.check_manifest_tree(self.root, self.manifest_sha, self.source_pin)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["evidence"]["extra"], ["extra.txt"])

    def test_absent_runtime_python(self) -> None:
        result = R.check_runtime_python(self.root / "missing-runtime/python.exe")
        self.assertEqual(result["status"], "FAIL")

    def test_bad_plan_gap(self) -> None:
        path = self.root / R.PLAN_REL
        plan = R.read_json(path)
        plan["chunks"][1]["start_frame"] += 1
        plan["chunks"][1]["frames"] -= 1
        plan["chunks"][1]["trim"]["start_frame"] += 1
        write_json(path, plan)
        self.assertEqual(R.check_plan(path)["status"], "FAIL")

    def test_duplicate_and_escape_paths(self) -> None:
        for bad in ("../outside", "a/../b", "a\\b", "C:/outside", "/absolute"):
            with self.assertRaises(ValueError):
                R.safe_relative(bad)
        manifest = self.root / "MANIFEST.json"
        doc = R.read_json(manifest)
        doc["files"].append({**doc["files"][0], "relative": doc["files"][0]["relative"].swapcase()})
        doc["total_files"] += 1
        write_json(manifest, doc)
        self.assertEqual(R.check_manifest_tree(self.root, sha(manifest), self.source_pin)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main(verbosity=2)
