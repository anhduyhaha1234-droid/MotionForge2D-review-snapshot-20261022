"""C01 review binding regressions, including the real isolated assembler entry point.

Run with C01_WORKER_DIR set to the task's c01-worker evidence directory. The
production modules are loaded from their source paths against an isolated K.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
WORKER = Path(os.environ.get("C01_WORKER_DIR", tempfile.gettempdir())).resolve()


def load_source(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReviewBindingTests(unittest.TestCase):
    def setUp(self):
        self.sandbox = tempfile.TemporaryDirectory(prefix="c01-fixture-", dir=WORKER)
        self.addCleanup(self.sandbox.cleanup)
        self.root = Path(self.sandbox.name)
        self.k = types.ModuleType("r6_common")
        self.k.R6 = self.root / "r6"
        self.k.D = self.root / "data"
        self.k.R5 = self.root / "r5"
        self.k.SHOTS = ["S0099"]
        self.k.PLAN = {"S0099": {"start_frame": 0, "frames": 9000}}
        self.k.SPAN_B = 9000
        self.k.SRC = self.root / "source.mp4"
        self.k.SRC.write_bytes(b"c01 fixture source")
        self.model = self.root / "model.safetensors"
        self.model.write_bytes(b"c01 fixture model")
        self.k.AUDIO_SS = 94
        self.k.sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
        self.k.run = lambda *args, **kwargs: self.fail("encoder reached")
        with patch.dict(sys.modules, {"r6_common": self.k}):
            self.cache = load_source("c01_isolated_cache", SCRIPTS / "r6_cache.py")
        self.cache.MODEL_PATH = self.model
        with patch.dict(sys.modules, {"r6_common": self.k, "r6_cache": self.cache}):
            self.gate = load_source("c01_isolated_gate", SCRIPTS / "r6_gate.py")
        self.name = "S0099_f0001"
        self.artifact = self.k.R6 / "keys" / "S0099" / "f_0001_key.png"
        self.artifact.parent.mkdir(parents=True)
        self.artifact.write_bytes(b"key-artifact")
        self.inputs = {"ledger_row_sha": "a" * 64, "deps_sha": "b" * 64}
        self.gate.write_review(
            "keys", self.name, self.artifact, self.inputs,
            {"shot": "S0099", "fid": 1}, "PASS", "sampled frames checked",
            reviewer="reviewer", frames=[1],
        )

    @property
    def review_path(self):
        return self.gate.REV / "keys" / f"{self.name}.review.json"

    def record(self):
        return json.loads(self.review_path.read_text(encoding="utf-8"))

    def save_record(self, record):
        self.review_path.write_text(json.dumps(record), encoding="utf-8")

    def write_deps_fixture(self):
        """Supply the real v3 producer record required by the key consumer gate."""
        dep = self.cache.build_deps(
            "S0099", 1, {"source_span_lo": 0, "source_span_hi": 9000,
                          "gframe": 0, "casts": [], "masks": [], "graph": None},
            {"mode": "keep_source_no_visible_actor"},
        )
        target = self.k.R6 / "work" / "S0099" / "f_0001.deps.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(dep), encoding="utf-8")

    def require(self, artifact=None, inputs=None):
        return self.gate.require_review(
            "keys", self.name, artifact or self.artifact,
            self.inputs if inputs is None else inputs,
        )

    def blocked(self, code, artifact=None, inputs=None):
        with self.assertRaisesRegex(self.gate.GateBlock, code):
            self.require(artifact, inputs)

    def test_current_producer_record_passes(self):
        self.assertEqual(self.require()["review_id"], f"keys:{self.name}")

    def test_missing_recorded_dependency_blocks(self):
        record = self.record()
        record["inputs"].pop("deps_sha")
        self.save_record(record)
        self.blocked("INPUT_SET")

    def test_missing_current_dependency_blocks(self):
        self.blocked("INPUT", inputs={"ledger_row_sha": self.inputs["ledger_row_sha"]})

    def test_changed_dependency_blocks(self):
        self.blocked("STALE", inputs={**self.inputs, "deps_sha": "c" * 64})

    def test_extra_recorded_and_current_dependencies_block(self):
        record = self.record()
        record["inputs"]["extra"] = "x"
        self.save_record(record)
        self.blocked("INPUT")
        record["inputs"].pop("extra")
        self.save_record(record)
        self.blocked("INPUT_SET", inputs={**self.inputs, "extra": "x"})

    def test_stale_artifact_blocks(self):
        self.artifact.write_bytes(b"changed-artifact")
        self.blocked("TAMPERED")

    def test_other_path_with_identical_bytes_blocks(self):
        other = self.root / "other" / "f_0001_key.png"
        other.parent.mkdir()
        other.write_bytes(self.artifact.read_bytes())
        self.blocked("ARTIFACT_PATH", artifact=other)

    def test_review_identity_must_match_requested_kind_and_name(self):
        record = self.record()
        record["review_id"] = "keys:S0098_f0001"
        self.save_record(record)
        self.blocked("IDENTITY")

    def test_bad_json_and_non_object_are_gate_blocks(self):
        self.review_path.write_text("{bad json", encoding="utf-8")
        self.blocked("MALFORMED")
        self.review_path.write_text("[]", encoding="utf-8")
        self.blocked("MALFORMED")

    def test_required_field_types_and_frames(self):
        base = self.record()
        bad_cases = (
            ("reviewer", 7), ("evidence", ["text"]), ("reviewed_at", False),
            ("frames", ["1"]), ("frames", [True]), ("frames", [0]),
            ("expected", {"shot": "S0099", "fid": False}),
            ("artifact", {"path": False, "sha256": self.k.sha(self.artifact)}),
        )
        for field, value in bad_cases:
            with self.subTest(field=field, value=value):
                self.save_record({**base, field: value})
                self.blocked("MALFORMED")

    def test_false_and_numeric_dependency_values_do_not_bind(self):
        record = self.record()
        record["inputs"]["deps_sha"] = False
        self.save_record(record)
        self.blocked("INPUT", inputs={"ledger_row_sha": self.inputs["ledger_row_sha"], "deps_sha": 0})

    def test_numeric_sha_and_missing_verdict_are_gate_blocks(self):
        record = self.record()
        record["inputs"]["deps_sha"] = 0
        self.save_record(record)
        self.blocked("INPUTS_MALFORMED", inputs={"ledger_row_sha": self.inputs["ledger_row_sha"], "deps_sha": 0})
        record = self.record()
        record["inputs"]["deps_sha"] = self.inputs["deps_sha"]
        record.pop("verdict")
        self.save_record(record)
        self.blocked("MALFORMED")

    def test_expected_and_reviewed_frame_identity(self):
        base = self.record()
        for field, value in (("shot", "S0098"), ("fid", 2)):
            with self.subTest(field=field):
                self.save_record({**base, "expected": {**base["expected"], field: value}})
                self.blocked("IDENTITY")
        self.save_record({**base, "frames": [2]})
        self.blocked("FRAME_IDENTITY")

    def test_nonstandard_json_constant_is_malformed(self):
        raw = self.review_path.read_text(encoding="utf-8")
        self.review_path.write_text(raw[:-1] + ', "unexpected": NaN}', encoding="utf-8")
        self.blocked("MALFORMED")

    def test_blend_producer_schema_and_full_mapping(self):
        manifest = self.k.R6 / "work" / "S0099" / "blend_manifest.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text('{"frames": 1}', encoding="utf-8")
        inputs = {
            "ledger_row_sha": "a" * 64,
            "blend_manifest_sha": self.k.sha(manifest),
            "frames": [{"name": "0001.jpg", "size": 3, "sha256": "b" * 64}],
            "key_set_sha": "c" * 64,
            "child_outcomes_sha": "d" * 64,
        }
        self.gate.write_review(
            "blend", "S0099_blend", manifest, inputs,
            {"shot": "S0099", "frames": 1}, "PASS", "frame checked",
            reviewer="reviewer", frames=[1],
        )
        self.gate.require_review("blend", "S0099_blend", manifest, inputs)
        malformed_inputs = {
            **inputs,
            "frames": [{**inputs["frames"][0], "name": "frame-one.jpg"}],
        }
        self.gate.write_review(
            "blend", "S0099_blend", manifest, malformed_inputs,
            {"shot": "S0099", "frames": 1}, "PASS", "frame checked",
            reviewer="reviewer", frames=[1],
        )
        with self.assertRaisesRegex(self.gate.GateBlock, "CURRENT_FRAMES_MALFORMED"):
            self.gate.require_review("blend", "S0099_blend", manifest, malformed_inputs)
        self.gate.write_review(
            "blend", "S0099_blend", manifest, inputs,
            {"shot": "S0099", "frames": 1}, "PASS", "frame checked",
            reviewer="reviewer", frames=[1],
        )
        review_path = self.gate.REV / "blend" / "S0099_blend.review.json"
        record = json.loads(review_path.read_text(encoding="utf-8"))
        record["inputs"].pop("child_outcomes_sha")
        review_path.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaisesRegex(self.gate.GateBlock, "INPUT_SET"):
            self.gate.require_review("blend", "S0099_blend", manifest, inputs)

    def test_real_gate_assemble_binds_review_to_consumed_blend_frames(self):
        sid = "S0099"
        row = {"shot": sid, "n": 3, "events": [], "contacts": [], "actors": []}
        self.k.R6.mkdir(exist_ok=True)
        (self.k.R6 / "source_actor_ledger.jsonl").write_text(
            json.dumps(row) + "\n", encoding="utf-8",
        )
        storyboard = self.k.R6 / "storyboard" / f"{sid}.json"
        storyboard.parent.mkdir()
        storyboard.write_text(json.dumps({"keys": [{"fid": 1}]}), encoding="utf-8")
        self.write_deps_fixture()
        self.gate.write_review(
            "keys", self.name, self.artifact,
            self.gate.key_inputs_now(sid, 1, self.artifact),
            {"shot": sid, "fid": 1}, "PASS", "key checked",
            reviewer="reviewer", frames=[1],
        )
        blend_dir = self.k.R6 / "work" / sid / "blend"
        blend_dir.mkdir(parents=True)
        current_frames = []
        for fid in range(1, 4):
            frame = blend_dir / f"{fid:04d}.jpg"
            frame.write_bytes(f"fixture frame {fid}".encode())
            current_frames.append({
                "name": frame.name,
                "size": frame.stat().st_size,
                "sha256": self.k.sha(frame),
            })
        manifest = blend_dir.parent / "blend_manifest.json"
        for label, manifest_frames, reviewed, count, accepted in (
            ("full", current_frames, [1, 2, 3], 3, True),
            ("truncated", current_frames, [1], 1, False),
            ("overlong", current_frames, [1, 2, 3, 4], 4, False),
            ("reordered", [current_frames[0], current_frames[2], current_frames[1]],
             [1, 2, 3], 3, False),
        ):
            with self.subTest(case=label):
                manifest.write_text(json.dumps({
                    "frames": manifest_frames,
                    "blend_dir": str(blend_dir),
                    "child_outcomes": [{"rc": 0}],
                    "decode_ok": True,
                    "key_set_sha": "c" * 64,
                    "child_outcomes_sha": "d" * 64,
                }), encoding="utf-8")
                self.gate.write_review(
                    "blend", f"{sid}_blend", manifest,
                    self.gate.blend_inputs_now(sid),
                    {"shot": sid, "frames": count}, "PASS", "blend checked",
                    reviewer="reviewer", frames=reviewed,
                )
                if accepted:
                    self.assertTrue(self.gate.gate_assemble([(sid, 3)]))
                else:
                    with self.assertRaisesRegex(self.gate.GateBlock, "ASSEMBLE_BLOCKED.*FRAME_IDENTITY"):
                        self.gate.gate_assemble([(sid, 3)])
        manifest.write_text(json.dumps({
            "frames": [True, current_frames[1], current_frames[2]],
            "blend_dir": str(blend_dir),
            "child_outcomes": [{"rc": 0}],
            "decode_ok": True,
        }), encoding="utf-8")
        with self.assertRaisesRegex(self.gate.GateBlock, "CURRENT_FRAMES_MALFORMED"):
            self.gate.gate_assemble([(sid, 3)])
        manifest.write_text(json.dumps({"frames": 3}), encoding="utf-8")
        with self.assertRaisesRegex(self.gate.GateBlock, "BLEND_MANIFEST_COUNT"):
            self.gate.gate_assemble([(sid, 3)])

    def test_real_assembler_main_rejects_before_copy_and_encoder(self):
        self.inputs = {"ledger_row_sha": "a" * 64, "deps_sha": "b" * 64}
        record = self.record()
        record["inputs"].pop("deps_sha")
        self.save_record(record)
        self.k.R6.mkdir(exist_ok=True)
        (self.k.R6 / "source_actor_ledger.jsonl").write_text(
            json.dumps({"shot": "S0099", "n": 9000, "events": [], "contacts": [], "actors": []}) + "\n",
            encoding="utf-8",
        )
        storyboard = self.k.R6 / "storyboard" / "S0099.json"
        storyboard.parent.mkdir()
        storyboard.write_text(json.dumps({"keys": [{"fid": 1}]}), encoding="utf-8")
        self.write_deps_fixture()
        self.k.D.mkdir()
        (self.k.D / "chunk_plan.json").write_text(
            json.dumps({"chunks": [{"unit_id": "S0099", "start_frame": 0, "frames": 9000}]}),
            encoding="utf-8",
        )
        # The gate's ledger hash must reflect the actual fixture row.
        record = self.record()
        record["inputs"]["ledger_row_sha"] = self.gate.ledger_row_sha("S0099")
        self.save_record(record)
        calls = []
        self.k.run = lambda *args, **kwargs: calls.append(args) or self.fail("encoder reached")
        with patch.dict(sys.modules, {"r6_common": self.k, "r6_gate": self.gate}):
            assemble = load_source("c01_isolated_assemble", SCRIPTS / "r6_assemble.py")
        self.assertFalse(assemble.FR.exists())
        with self.assertRaisesRegex(self.gate.GateBlock, "ASSEMBLE_BLOCKED.*INPUT_SET"):
            assemble.main()
        self.assertFalse(assemble.FR.exists(), "assembly copied frames before review gate")
        self.assertEqual(calls, [], "assembly reached encoder after invalid review")


if __name__ == "__main__":
    unittest.main()
