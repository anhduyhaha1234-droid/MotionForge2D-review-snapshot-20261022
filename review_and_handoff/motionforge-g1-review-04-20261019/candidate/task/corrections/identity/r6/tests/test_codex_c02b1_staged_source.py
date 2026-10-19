"""C02B1 staged source provenance tests against the real isolated common helper."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image


SOURCE_COMMON = Path(__file__).resolve().parents[1] / "scripts" / "r6_common.py"
WORKER = Path(os.environ["C02B1_WORKER_DIR"]).resolve()


class StagedSourceTests(unittest.TestCase):
    def setUp(self):
        WORKER.mkdir(parents=True, exist_ok=True)
        self.sandbox = tempfile.TemporaryDirectory(prefix="c02b1-fixture-", dir=WORKER)
        self.addCleanup(self.sandbox.cleanup)
        self.root = Path(self.sandbox.name)
        task = self.root / "task"
        scripts = task / "corrections" / "identity" / "r6" / "scripts"
        scripts.mkdir(parents=True)
        shutil.copyfile(SOURCE_COMMON, scripts / "r6_common.py")
        (task / "chunk_plan.json").write_text(json.dumps({"chunks": [
            {"unit_id": "S0021", "start_frame": 0, "frames": 10}
        ]}), encoding="utf-8")
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("c02b1_isolated_common", scripts / "r6_common.py")
        self.k = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.k)
        self.k.SRC.parent.mkdir(parents=True)
        self.k.SRC.write_bytes(b"SOURCE-A")
        self.dst = self.root / "frame.png"
        self.calls = []

    def fake_extract(self, cmd, **kwargs):
        self.calls.append(list(cmd))
        frame = round(float(cmd[cmd.index("-ss") + 1]) * 30)
        source = Path(cmd[cmd.index("-i") + 1]).read_bytes()
        Path(cmd[-1]).write_bytes(b"FRAME-" + source + b"-" + str(frame).encode())
        return types.SimpleNamespace(returncode=0, stderr="", stdout="")

    @property
    def receipt(self):
        return self.dst.with_name(self.dst.name + ".stage.json")

    def stage_fake(self, frame=0, dst=None, sid="S0021"):
        with patch.object(self.k.subprocess, "run", side_effect=self.fake_extract):
            return self.k.stage_frame(sid, frame, dst or self.dst)

    def test_same_path_same_size_source_mutation_reextracts(self):
        with patch.object(self.k.subprocess, "run", side_effect=self.fake_extract):
            self.assertEqual(self.k.stage_frame("S0021", 0, self.dst), self.dst)
            self.assertEqual(self.dst.read_bytes(), b"FRAME-SOURCE-A-0")
            self.k.SRC.write_bytes(b"SOURCE-B")
            self.assertEqual(self.k.stage_frame("S0021", 0, self.dst), self.dst)
            self.assertEqual(self.dst.read_bytes(), b"FRAME-SOURCE-B-0")
            self.assertEqual(len(self.calls), 2)

    def test_first_extract_and_unchanged_reuse(self):
        self.assertEqual(self.stage_fake(), self.dst)
        first = self.dst.read_bytes()
        self.assertEqual(first, b"FRAME-SOURCE-A-0")
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(Path(self.calls[0][-1]).parent, self.dst.parent)
        self.assertEqual(Path(self.calls[0][-1]).suffix, ".png")
        self.assertNotEqual(Path(self.calls[0][-1]), self.dst)
        self.assertFalse(Path(self.calls[0][-1]).exists())
        with patch.object(self.k.subprocess, "run", side_effect=AssertionError("unexpected FFmpeg call")):
            self.assertEqual(self.k.stage_frame("S0021", 0, self.dst), self.dst)
        self.assertEqual(self.dst.read_bytes(), first)
        record = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertEqual(record["gframe"], 0)
        self.assertEqual(record["sid"], "S0021")
        self.assertEqual(record["source_path"], str(self.k.SRC.resolve()))
        self.assertEqual(record["output_path"], str(self.dst.resolve()))

    def test_source_path_frame_output_and_restore_invalidate(self):
        self.stage_fake()
        self.k.SRC.write_bytes(b"SOURCE-B")
        self.stage_fake()
        self.assertEqual(self.dst.read_bytes(), b"FRAME-SOURCE-B-0")
        self.k.SRC.write_bytes(b"SOURCE-A")
        self.stage_fake()
        self.assertEqual(self.dst.read_bytes(), b"FRAME-SOURCE-A-0")
        other = self.k.SRC.parent / "other.mp4"
        other.write_bytes(b"SOURCE-A")
        self.k.SRC = other
        self.stage_fake()
        self.assertEqual(self.dst.read_bytes(), b"FRAME-SOURCE-A-0")
        self.stage_fake(frame=1)
        self.assertEqual(self.dst.read_bytes(), b"FRAME-SOURCE-A-1")
        self.dst.write_bytes(b"TAMPERED-FRAME")
        self.stage_fake(frame=1)
        self.assertEqual(self.dst.read_bytes(), b"FRAME-SOURCE-A-1")
        self.assertEqual(len(self.calls), 6)

    def test_legacy_empty_missing_and_copied_receipts(self):
        self.dst.write_bytes(b"LEGACY")
        self.stage_fake()
        self.assertEqual(self.dst.read_bytes(), b"FRAME-SOURCE-A-0")
        self.assertEqual(len(self.calls), 1)
        self.dst.write_bytes(b"")
        self.stage_fake()
        self.dst.unlink()
        self.stage_fake()
        self.assertEqual(len(self.calls), 3)
        copied = self.root / "copy.png"
        copied.write_bytes(self.dst.read_bytes())
        copied_receipt = copied.with_name(copied.name + ".stage.json")
        copied_receipt.write_bytes(self.receipt.read_bytes())
        self.stage_fake(dst=copied)
        self.assertEqual(len(self.calls), 4)
        self.receipt.write_bytes(copied_receipt.read_bytes())
        self.stage_fake(frame=1)
        self.assertEqual(len(self.calls), 5)

    def test_malformed_and_wrong_receipts_reextract(self):
        self.stage_fake()
        good = json.loads(self.receipt.read_text(encoding="utf-8"))
        variants = [
            b"{bad", b"[]", b'{"contract":"x","contract":"y"}',
            b"[" * 1500 + b"0" + b"]" * 1500,
            b" " * 5000,
            json.dumps({**good, "gframe": True}).encode(),
            json.dumps({key: value for key, value in good.items() if key != "sid"}).encode(),
            json.dumps({**good, "sid": "S0022"}).encode(),
            json.dumps({**good, "gframe": 1}).encode(),
            json.dumps({**good, "source_sha256": "0" * 64}).encode(),
            json.dumps({**good, "output_sha256": "0" * 64}).encode(),
            json.dumps({**good, "output_size": "wrong"}).encode(),
        ]
        for raw in variants:
            with self.subTest(receipt=raw[:40]):
                before = len(self.calls)
                self.receipt.write_bytes(raw)
                self.stage_fake()
                self.assertEqual(len(self.calls), before + 1)
                self.assertEqual(self.dst.read_bytes(), b"FRAME-SOURCE-A-0")

    def test_failed_extractor_and_empty_result_preserve_previous_pair(self):
        self.stage_fake()
        old_output, old_receipt = self.dst.read_bytes(), self.receipt.read_bytes()
        self.k.SRC.write_bytes(b"SOURCE-B")

        def failed(cmd, **kwargs):
            Path(cmd[-1]).write_bytes(b"PARTIAL")
            return types.SimpleNamespace(returncode=1, stderr="injected error", stdout="")

        def missing(cmd, **kwargs):
            Path(cmd[-1]).unlink()
            return types.SimpleNamespace(returncode=0, stderr="", stdout="")

        def empty(cmd, **kwargs):
            Path(cmd[-1]).write_bytes(b"")
            return types.SimpleNamespace(returncode=0, stderr="", stdout="")

        for injected in (failed, missing, empty):
            with self.subTest(injected=injected.__name__):
                with patch.object(self.k.subprocess, "run", side_effect=injected):
                    with self.assertRaises(RuntimeError):
                        self.k.stage_frame("S0021", 0, self.dst)
                self.assertEqual(self.dst.read_bytes(), old_output)
                self.assertEqual(self.receipt.read_bytes(), old_receipt)
                self.assertEqual(list(self.root.glob(".*.stage-*")), [])

    def test_missing_unreadable_source_and_invalid_frames(self):
        self.stage_fake()
        old_output, old_receipt = self.dst.read_bytes(), self.receipt.read_bytes()
        for frame in (True, -1, 10, 1.0):
            with self.subTest(frame=frame):
                with self.assertRaises(ValueError):
                    self.stage_fake(frame=frame)
        with self.assertRaises(ValueError):
            self.stage_fake(sid="S9999")
        self.assertEqual(len(self.calls), 1)
        original_sha = self.k.sha

        def unreadable(path):
            if Path(path) == self.k.SRC:
                raise PermissionError("injected unreadable source")
            return original_sha(path)

        with patch.object(self.k, "sha", side_effect=unreadable):
            with self.assertRaises(RuntimeError):
                self.stage_fake()
        self.k.SRC.unlink()
        with self.assertRaises(RuntimeError):
            self.stage_fake()
        self.assertEqual(self.dst.read_bytes(), old_output)
        self.assertEqual(self.receipt.read_bytes(), old_receipt)
        self.assertEqual(len(self.calls), 1)

    def test_source_change_during_extraction_preserves_previous_pair(self):
        self.stage_fake()
        old_output, old_receipt = self.dst.read_bytes(), self.receipt.read_bytes()
        self.k.SRC.write_bytes(b"SOURCE-B")

        def changing(cmd, **kwargs):
            Path(cmd[-1]).write_bytes(b"FRAME-SOURCE-B-0")
            self.k.SRC.write_bytes(b"SOURCE-C")
            return types.SimpleNamespace(returncode=0, stderr="", stdout="")

        with patch.object(self.k.subprocess, "run", side_effect=changing):
            with self.assertRaisesRegex(RuntimeError, "source changed during extraction"):
                self.k.stage_frame("S0021", 0, self.dst)
        self.assertEqual(self.dst.read_bytes(), old_output)
        self.assertEqual(self.receipt.read_bytes(), old_receipt)

    def test_partial_publication_cannot_bless_old_receipt(self):
        self.stage_fake()
        self.k.SRC.write_bytes(b"SOURCE-B")
        replace = self.k.os.replace
        publications = []

        def fail_final_receipt(src, target):
            publications.append((Path(src), Path(target)))
            if len(publications) == 3:
                raise OSError("injected final receipt failure")
            return replace(src, target)

        with patch.object(self.k.os, "replace", side_effect=fail_final_receipt):
            with self.assertRaisesRegex(RuntimeError, "staging failed"):
                self.stage_fake()
        self.assertEqual(len(publications), 3)
        self.assertEqual(self.dst.read_bytes(), b"FRAME-SOURCE-B-0")
        self.assertEqual(self.receipt.read_bytes(), b'{"state":"pending"}')
        before = len(self.calls)
        self.stage_fake()
        self.assertEqual(len(self.calls), before + 1)
        self.assertEqual(self.dst.read_bytes(), b"FRAME-SOURCE-B-0")
        with patch.object(self.k.subprocess, "run", side_effect=AssertionError("unexpected FFmpeg call")):
            self.assertEqual(self.k.stage_frame("S0021", 0, self.dst), self.dst)

    def test_real_ffmpeg_30fps_640x360_frame_mapping_and_replacement(self):
        evidence = Path(tempfile.mkdtemp(prefix="real-ffmpeg-", dir=WORKER))
        commands = []
        pixels = {}

        def encode(name, colors):
            raw = b"".join(bytes(color) * (640 * 360) for color in colors)
            cmd = ["ffmpeg", "-v", "error", "-nostdin", "-y", "-f", "rawvideo",
                   "-pixel_format", "rgb24", "-video_size", "640x360", "-framerate", "30",
                   "-i", "pipe:0", "-frames:v", "3", "-an", "-c:v", "libx264",
                   "-pix_fmt", "yuv420p", "-g", "1", "-bf", "0", "-threads", "1",
                   str(self.k.SRC)]
            result = subprocess.run(cmd, input=raw, capture_output=True)
            commands.append({"command": cmd, "input_sha256": hashlib.sha256(raw).hexdigest(),
                             "returncode": result.returncode,
                             "stdout": result.stdout.decode(errors="replace"),
                             "stderr": result.stderr.decode(errors="replace")})
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
            shutil.copyfile(self.k.SRC, evidence / f"{name}.mp4")

        def read_pixel(label, expected):
            with Image.open(self.dst) as image:
                self.assertEqual(image.size, (640, 360))
                pixel = image.convert("RGB").getpixel((320, 180))
            pixels[label] = pixel
            self.assertTrue(all(abs(actual - target) < 16 for actual, target in zip(pixel, expected)),
                            (label, pixel, expected))
            shutil.copyfile(self.dst, evidence / f"{label}.png")

        try:
            encode("source_a", [(255, 0, 0), (0, 255, 0), (0, 0, 255)])
            self.assertEqual(self.k.stage_frame("S0021", 0, self.dst), self.dst)
            read_pixel("a_frame_0", (255, 0, 0))
            self.assertEqual(self.k.stage_frame("S0021", 1, self.dst), self.dst)
            read_pixel("a_frame_1", (0, 255, 0))
            before = self.dst.read_bytes()
            with patch.object(self.k.subprocess, "run", side_effect=AssertionError("unexpected FFmpeg call")):
                self.assertEqual(self.k.stage_frame("S0021", 1, self.dst), self.dst)
            self.assertEqual(self.dst.read_bytes(), before)
            encode("source_b", [(0, 0, 255), (255, 0, 0), (0, 255, 0)])
            self.assertEqual(self.k.stage_frame("S0021", 1, self.dst), self.dst)
            read_pixel("b_frame_1", (255, 0, 0))
            self.assertNotEqual(pixels["a_frame_1"], pixels["b_frame_1"])
            (evidence / "RESULT.json").write_text(json.dumps({
                "commands": commands, "pixels": pixels, "frame_requests": [0, 1, 1],
                "source_a_sha256": hashlib.sha256((evidence / "source_a.mp4").read_bytes()).hexdigest(),
                "source_b_sha256": hashlib.sha256((evidence / "source_b.mp4").read_bytes()).hexdigest(),
                "unchanged_reuse_without_ffmpeg": True,
            }, indent=2), encoding="utf-8")
        except BaseException:
            (evidence / "FAILED.txt").write_text("Real FFmpeg fixture failed; inspect unittest log.\n", encoding="utf-8")
            raise


if __name__ == "__main__":
    unittest.main()
