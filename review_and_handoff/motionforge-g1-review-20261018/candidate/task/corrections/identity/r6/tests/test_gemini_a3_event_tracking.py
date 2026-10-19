"""A3: event timing, child outcomes fail-closed, cotracker contracts and crop/stitch roundtrip."""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

import numpy as np
import torch
from PIL import Image

SOURCE_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
VENDOR_CROP = Path(__file__).resolve().parents[2] / "r5/vendor/cropandstitch_8584b08d"
MODULES = ("r6_common", "r6_gate", "r6_cotracker", "r6_propagate", "r6_ledger", "r6_adapter")


class EventTimingAndTrackingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="a3-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.task = self.root / "task"
        self.r6 = self.task / "corrections/identity/r6"
        self.scripts = self.r6 / "scripts"
        self.scripts.mkdir(parents=True)
        for path in SOURCE_SCRIPTS.glob("*.py"):
            shutil.copyfile(path, self.scripts / path.name)
        (self.task / "chunk_plan.json").write_text(json.dumps({"chunks": [
            {"unit_id": "S0021", "start_frame": 0, "frames": 100}
        ]}), encoding="utf-8")

        self.previous = {name: sys.modules.pop(name, None) for name in MODULES}
        sys.path.insert(0, str(self.scripts))
        sys.path.insert(0, str(VENDOR_CROP))
        self.addCleanup(self._restore_modules)

        self.k = importlib.import_module("r6_common")
        self.gate = importlib.import_module("r6_gate")
        self.cotracker = importlib.import_module("r6_cotracker")
        self.propagate = importlib.import_module("r6_propagate")
        self.adapter = importlib.import_module("r6_adapter")

    def _restore_modules(self):
        if str(VENDOR_CROP) in sys.path:
            sys.path.remove(str(VENDOR_CROP))
        if str(self.scripts) in sys.path:
            sys.path.remove(str(self.scripts))
        for name, old in self.previous.items():
            sys.modules.pop(name, None)
            if old is not None:
                sys.modules[name] = old

    # E1: Event Keys Mapping & Discovery
    def test_e1_event_fids_mapping_both_f_and_frame(self):
        row = {
            "shot": "S0021",
            "n": 100,
            "events": [
                {"f": 43, "event": "entry via f field"},
                {"frame": 75, "event": "event via frame field"}
            ],
            "contacts": [
                {"from": 10, "entity": "E1", "prop": "P1"}
            ],
            "actors": [
                {"entity": "E1", "class_windows": [{"from": 25, "to": 100, "class": "VISIBLE"}]}
            ]
        }
        fids = self.propagate.event_fids_for("S0021", row)
        # f: 43 -> 44; frame: 75 -> 75; contact from: 10 -> 11; actor from: 25 -> 25
        self.assertIn(44, fids)
        self.assertIn(75, fids)
        self.assertIn(11, fids)
        self.assertIn(25, fids)
        self.assertEqual(fids, {11, 25, 44, 75})

    # E2: Plan runs split at hard cut boundaries
    def test_e2_plan_runs_split_at_hard_cuts(self):
        # Without cuts: uniform spacing (delta = 10: 1, 11, 21, 31, 41)
        key_fids = [1, 11, 21, 31, 41]
        runs = self.propagate.plan_runs(key_fids, 41)
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0], [1, 11, 21, 31, 41])

        # With hard cut at frame 21: must split so run does not interpolate across 21
        runs_cut = self.propagate.plan_runs(key_fids, 41, cuts=[21])
        self.assertEqual(len(runs_cut), 2)
        self.assertEqual(runs_cut[0], [1, 11, 21])
        self.assertEqual(runs_cut[1], [21, 31, 41])

    # E3: Stage-2 Child Outcomes Fail-Closed
    def test_e3_child_outcome_nonzero_rc_fails(self):
        base = self.root / "run_test"
        base.mkdir(parents=True)
        dummy_script = self.root / "video_blend.py"
        dummy_script.write_text("# dummy", encoding="utf-8")
        # Mock run_one returning rc != 0
        with unittest.mock.patch.object(self.propagate, "blend_script", return_value=dummy_script):
            with unittest.mock.patch.object(self.propagate, "run_one", return_value={"rc": 1, "beg": 1, "end": 10, "itv": 1}):
                with unittest.mock.patch.object(self.propagate, "stage_shot_assets", return_value=[1, 10]):
                    with unittest.mock.patch.object(self.propagate, "build_key_fids", return_value=[1, 10]):
                        with unittest.mock.patch.object(self.gate, "gate_shot_before_propagate", return_value=True):
                            self.k.PLAN = {"S0021": {"frames": 10, "start_frame": 0}}
                            with self.assertRaises(SystemExit) as cm:
                                self.propagate.run_shot("S0021")
                            self.assertIn("rc=1", str(cm.exception))

    def test_e3_child_outcome_partial_frames_fails(self):
        base = self.root / "run_test_partial"
        base.mkdir(parents=True)
        dummy_script = self.root / "video_blend.py"
        dummy_script.write_text("# dummy", encoding="utf-8")
        # Mock run_one returning rc == 0 but frames count < expect
        with unittest.mock.patch.object(self.propagate, "blend_script", return_value=dummy_script):
            with unittest.mock.patch.object(self.propagate, "run_one", return_value={"rc": 0, "beg": 1, "end": 10, "itv": 1}):
                with unittest.mock.patch.object(self.propagate, "stage_shot_assets", return_value=[1, 10]):
                    with unittest.mock.patch.object(self.propagate, "build_key_fids", return_value=[1, 10]):
                        with unittest.mock.patch.object(self.gate, "gate_shot_before_propagate", return_value=True):
                            self.k.PLAN = {"S0021": {"frames": 10, "start_frame": 0}}
                            with self.assertRaises(SystemExit) as cm:
                                self.propagate.run_shot("S0021")
                            self.assertIn("partial", str(cm.exception))

    # E4: CoTracker Tensor Contract Validation
    def test_e4_cotracker_tensor_contract(self):
        # Valid tensors: (T=10, N=5, 2) and (T=10, N=5)
        tr = np.zeros((10, 5, 2), dtype=np.float32)
        tr[:, :, 0] = 320.0
        tr[:, :, 1] = 180.0
        vis = np.ones((10, 5), dtype=bool)

        ok, why = self.cotracker.validate_cotracker_tensors(tr, vis, 10, 5)
        self.assertTrue(ok, f"valid tensors should pass: {why}")

        # Invalid shape
        ok, why = self.cotracker.validate_cotracker_tensors(tr[:5], vis, 10, 5)
        self.assertFalse(ok)
        self.assertIn("shape mismatch", why)

        # Non-finite (NaN)
        tr_nan = tr.copy()
        tr_nan[2, 1, 0] = np.nan
        ok, why = self.cotracker.validate_cotracker_tensors(tr_nan, vis, 10, 5)
        self.assertFalse(ok)
        self.assertIn("non-finite", why)

        # Far outside canvas bounds
        tr_out = tr.copy()
        tr_out[0, 0, 0] = 1500.0
        ok, why = self.cotracker.validate_cotracker_tensors(tr_out, vis, 10, 5)
        self.assertFalse(ok)
        self.assertIn("outside canvas bounds", why)

    # E5: CoTracker Side-by-Side Sửa Lỗi
    def test_e5_cotracker_strip_pastes_both_frames(self):
        # Verify that line 158 of r6_cotracker pastes frame b
        cotracker_path = self.scripts / "r6_cotracker.py"
        src = cotracker_path.read_text(encoding="utf-8")
        self.assertNotIn("if False else None", src)
        self.assertIn("c.paste(_I.fromarray(b).resize((320, 180)), (x, 20 + 190))", src)

    # E6: CropAndStitch Landmark Roundtrip and Bounds
    def test_e6_crop_stitch_landmark_roundtrip_and_bounds(self):
        res = self.adapter.landmark_roundtrip(size=(640, 360))
        self.assertTrue(res["ok"], f"landmark roundtrip should pass: {res}")
        self.assertEqual(res["outside_max"], 0.0)

        # Test bound check detects leak outside mask
        canvas = torch.zeros((1, 360, 640, 3), dtype=torch.float32)
        mask = torch.zeros((1, 360, 640), dtype=torch.float32)
        mask[0, 100:150, 100:150] = 1.0

        # Identical before and after: bound check passes
        bc_good = self.adapter.bound_check(canvas, canvas, mask)
        self.assertTrue(bc_good["ok"])

        # Leakage far outside mask (at 300, 300): bound check fails
        leaked = canvas.clone()
        leaked[0, 300:350, 300:350, :] = 1.0
        bc_bad = self.adapter.bound_check(canvas, leaked, mask)
        self.assertFalse(bc_bad["ok"])
        self.assertGreater(bc_bad["max_outside"], 0.5)


if __name__ == "__main__":
    unittest.main()
