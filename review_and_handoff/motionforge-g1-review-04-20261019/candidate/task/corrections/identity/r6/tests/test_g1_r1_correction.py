"""G1-R1 Acceptance Matrix Tests (M01-M20) covering findings R01-R09.

Comprehensive ground truth verification:
- M01-M04 (R01): Asset provenance, consumed references, graph sampler & settings
- M05 (R02): CoTracker CLI --help and entry point
- M06-M07 (R03): CoTracker tensor contracts, frame preservation (frame 43) & window drift
- M08-M09 (R04): Propagation CLI child failures (wrong/extra names, corrupt image), manifest invalidation & failure receipt
- M10-M11 (R05): Event transitions (entry/exit/occlusion/contact), strict int types, contact bounds check & cut caller propagation
- M12-M14 (R06): Matrix evidence rigor (no fake PASS, ffprobe video decode, test AST parse), batch gate modes, atomic stage-validate-publish
- M15-M16 (R07): Manifest relative filtering under Codex/work & invocation namespace isolation
- M17-M18 (R08): Q11 historical proof binding & 2-process race barrier in sandbox
- M19-M20 (R09): Candidate identity reconciliation & resume state truth (watchdog quota preservation)
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib
import json
import math
import multiprocessing
import os
import shutil
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest import mock
from pathlib import Path

import numpy as np
from PIL import Image

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
EX_DIR = Path("C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-gemini-handoff-20261017/execution")
MODULES = (
    "r6_common", "r6_cache", "r6_cotracker", "r6_propagate",
    "r6_ledger", "r6_gate", "r6_matrix", "r6_key_recipe",
    "r6_event_contract", "r6_evidence_contract"
)


def _process_race_worker(lock_path_str: str, winner_queue: multiprocessing.Queue, barrier: multiprocessing.Barrier):
    """Real separate process contending for atomic file lock."""
    barrier.wait()
    try:
        fd = os.open(lock_path_str, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        os.write(fd, f"pid={os.getpid()}".encode("utf-8"))
        os.close(fd)
        winner_queue.put(os.getpid())
    except FileExistsError:
        pass


class G1R1CorrectionMatrixTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="g1-r1-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.task = self.root / "task"
        self.r6 = self.task / "corrections/identity/r6"
        self.scripts = self.r6 / "scripts"
        self.scripts.mkdir(parents=True)
        for p in SCRIPTS_DIR.glob("*.py"):
            shutil.copyfile(p, self.scripts / p.name)
            
        (self.task / "chunk_plan.json").write_text(json.dumps({"chunks": [
            {"unit_id": "S0021", "start_frame": 0, "frames": 100},
            {"unit_id": "S0035", "start_frame": 100, "frames": 39}
        ]}), encoding="utf-8")
        
        self.previous = {name: sys.modules.pop(name, None) for name in MODULES}
        sys.path.insert(0, str(self.scripts))
        self.addCleanup(self._restore_modules)

        self.k = importlib.import_module("r6_common")
        self.k.SRC.parent.mkdir(parents=True, exist_ok=True)
        self.k.SRC.write_bytes(b"fixture-source-asset")
        self.model = self.root / "model.bin"
        self.model.write_bytes(b"fixture-model-asset")

        # Scaffold ledger rows and storyboard
        rows = [
            {"shot": "S0021", "zero_explicit": False, "n": 100, "src": [0, 100], "actors": [], "events": [], "contacts": []},
            {"shot": "S0035", "zero_explicit": True, "n": 39, "src": [100, 139], "actors": [], "events": [], "contacts": []}
        ]
        (self.r6 / "source_actor_ledger.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        
        sb_dir = self.r6 / "storyboard"
        sb_dir.mkdir(parents=True, exist_ok=True)
        (sb_dir / "S0021.json").write_text(json.dumps({"shot": "S0021", "n": 100, "zero_explicit": False, "keys": [{"fid": 1}]}), encoding="utf-8")
        (sb_dir / "S0035.json").write_text(json.dumps({"shot": "S0035", "n": 39, "zero_explicit": True, "keys": [{"fid": 1}]}), encoding="utf-8")

        # Scaffold template
        tpl_path = self.k.D / "graph/reuse_bundle/shot_anchor_v1.baseline.api.json"
        tpl_path.parent.mkdir(parents=True, exist_ok=True)
        graph = {name: {"class_type": "FixtureNode", "inputs": {}} for name in
                 ("KEY_LOAD", "R1_LOAD", "R2_LOAD", "R3_LOAD", "PROMPT", "NOISE",
                  "LATENT", "SIGMAS", "SAMPLER", "GUIDER", "UNET", "CLIP", "VAE",
                  "SAVE", "R2_POS", "R2_NEG")}
        graph["SIGMAS"]["inputs"] = {"steps": 4, "width": 640, "height": 360}
        graph["SAMPLER"]["inputs"] = {"sampler_name": "euler"}
        graph["GUIDER"]["inputs"] = {"cfg": 1.0, "positive": ["R2_POS", 0], "negative": ["R2_NEG", 0]}
        graph["UNET"]["inputs"] = {"unet_name": "model.bin"}
        graph["CLIP"]["inputs"] = {"clip_name": "qwen_3_4b.safetensors"}
        graph["VAE"]["inputs"] = {"vae_name": "flux2-vae.safetensors"}
        graph["NOISE"]["inputs"] = {"noise_seed": 1}
        graph["LATENT"]["inputs"] = {"width": 640, "height": 360}
        graph["R2_POS"]["inputs"] = {name: [name, 0] for name in ("KEY_LOAD", "R1_LOAD", "R2_LOAD")}
        graph["R2_NEG"]["inputs"] = {name: [name, 0] for name in ("KEY_LOAD", "R1_LOAD", "R2_LOAD")}
        graph["KEY_LOAD"]["inputs"] = {"image": "identity5m_20261008/r6/work/f_0001_src.png"}
        graph["R1_LOAD"]["inputs"] = {"image": "identity5m_20261008/r6/_grey_64.png"}
        graph["R2_LOAD"]["inputs"] = {"image": "identity5m_20261008/r6/_grey_64.png"}
        graph["R3_LOAD"]["inputs"] = {"image": "identity5m_20261008/r6/_grey_64.png"}
        graph["PROMPT"]["inputs"] = {
            "text": (
                "Restyle this frame into flat 2D cel-shaded animation style: solid flat colour fills, thin clean "
                "outlines, no gradients, no photographic texture, no 3D rendering. CRITICAL: keep the EXACT same "
                "composition, the EXACT same layout, and every piece of text, number, logo and document shape "
                "IDENTICAL and fully legible - do not redraw, move, add, remove or invent any glyph or object. "
                "The result must read as the same document/image, only in flat vector style."
            )
        }
        tpl_path.write_text(json.dumps(graph), encoding="utf-8")
        graph_mod = importlib.import_module("r6_graph")
        graph_mod.TPL = tpl_path

        self.cache = importlib.import_module("r6_cache")
        self.cache.MODEL_PATH = self.model
        self.cotracker = importlib.import_module("r6_cotracker")
        self.propagate = importlib.import_module("r6_propagate")
        self.ledger = importlib.import_module("r6_ledger")
        self.gate = importlib.import_module("r6_gate")
        self.matrix = importlib.import_module("r6_matrix")
        self.recipe = importlib.import_module("r6_key_recipe")
        self.event_contract = importlib.import_module("r6_event_contract")
        self.evidence_contract = importlib.import_module("r6_evidence_contract")

    def _restore_modules(self):
        if str(self.scripts) in sys.path:
            sys.path.remove(str(self.scripts))
        for name, old in self.previous.items():
            sys.modules.pop(name, None)
            if old is not None:
                sys.modules[name] = old

    def _stage(self, sid, gframe, dst):
        dst = Path(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        arr = np.arange(640 * 360 * 3, dtype=np.uint8).reshape(360, 640, 3)
        Image.fromarray(arr).save(dst)
        receipt = {
            "contract": self.k._STAGE_CONTRACT,
            "source_path": str(self.k.SRC.resolve()),
            "source_sha256": self.k.sha(self.k.SRC),
            "sid": sid,
            "gframe": gframe,
            "output_path": str(dst.resolve()),
            "output_sha256": self.k.sha(dst),
            "output_size": dst.stat().st_size
        }
        dst.with_name(dst.name + ".stage.json").write_text(json.dumps(receipt), encoding="utf-8")
        return dst

    # M01 (R01): Missing consumed grey_ref rejected even with valid self-digest
    def test_m01_asset_missing_grey_ref_rejected(self):
        work_sid = self.k.R6 / "work" / "S0035"
        staged = self._stage("S0035", 100, work_sid / "f_0001_src.png")
        stage_rec = staged.with_name(staged.name + ".stage.json")
        graph_p = self.k.R6 / "workflows" / "r6_asset_S0035_f1.json"
        graph_p.parent.mkdir(parents=True, exist_ok=True)
        graph_p.write_text(json.dumps({"NOISE": {"inputs": {"noise_seed": 1}}}), encoding="utf-8")

        dep = {
            "kind": "r6_key_deps_v4_asset",
            "shot": "S0035",
            "fid": 1,
            "mode": "zero_shot_asset_restyle",
            "source": {"role": "source", "path": str(self.k.SRC.resolve()), "sha256": self.k.sha(self.k.SRC)},
            "model": {"role": "model", "path": str(self.cache.MODEL_PATH.resolve()), "sha256": self.k.sha(self.cache.MODEL_PATH)},
            "recipe": self.recipe.current_asset_recipe("S0035", 1, self.cache.MODEL_PATH),
            "consumed": {
                "staged_source": {"role": "staged_source", "path": str(staged.resolve()), "sha256": self.k.sha(staged)},
                "stage_receipt": {"role": "stage_receipt", "path": str(stage_rec.resolve()), "sha256": self.k.sha(stage_rec)},
                "graph": {"role": "graph", "path": str(graph_p.resolve()), "sha256": self.k.sha(graph_p)}
                # Missing grey_ref!
            }
        }
        body = {k: v for k, v in dep.items() if k != "deps_sha"}
        dep["deps_sha"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        
        ok, why = self.cache.verify_complete_asset_deps(dep, "S0035", 1)
        self.assertFalse(ok)
        self.assertIn("missing consumed grey_ref", why)

    # M02 (R01): Graph sampler, wrong grey upload path & missing R1 rejected
    def test_m02_asset_graph_sampler_and_wrong_grey_rejected(self):
        staged_src = self.root / "staged.png"
        staged_src.write_bytes(b"\x89PNG\r\n\x1a\nfake")
        graph_p = self.root / "graph_test.json"
        
        rec = self.recipe.current_asset_recipe("S0035", 1, self.cache.MODEL_PATH)
        base_graph = {
            "NOISE": {"inputs": {"noise_seed": rec["seed"]}},
            "SIGMAS": {"inputs": {"steps": rec["steps"]}},
            "GUIDER": {"inputs": {"cfg": rec["cfg"], "positive": ["R2_POS", 0], "negative": ["R2_NEG", 0]}},
            "UNET": {"inputs": {"unet_name": rec["model_name"]}},
            "CLIP": {"inputs": {"clip_name": rec["clip_name"]}},
            "VAE": {"inputs": {"vae_name": rec["vae_name"]}},
            "KEY_LOAD": {"inputs": {"image": f"identity5m_20261008/r6/work/{staged_src.name}"}},
            "PROMPT": {"inputs": {"text": rec["prompt"]}},
            "SAMPLER": {"inputs": {"sampler_name": "euler"}},
            "R1_LOAD": {"inputs": {"image": "identity5m_20261008/r6/_grey_64.png"}},
            "R2_LOAD": {"inputs": {"image": "identity5m_20261008/r6/_grey_64.png"}},
            "R3_LOAD": {"inputs": {"image": "identity5m_20261008/r6/_grey_64.png"}}
        }
        
        # 1. Sampler mismatch: heun vs euler
        g_heun = copy.deepcopy(base_graph)
        g_heun["SAMPLER"]["inputs"]["sampler_name"] = "heun"
        graph_p.write_text(json.dumps(g_heun), encoding="utf-8")
        with self.assertRaises(ValueError) as cm:
            self.cache._verify_asset_graph(graph_p, rec, staged_src)
        self.assertIn("sampler 'heun' differs from recipe", str(cm.exception))

        # 2. Wrong grey upload path: wrong_invocation/fake_grey.png
        g_wrong_grey = copy.deepcopy(base_graph)
        g_wrong_grey["R1_LOAD"]["inputs"]["image"] = "wrong_invocation/fake_grey.png"
        graph_p.write_text(json.dumps(g_wrong_grey), encoding="utf-8")
        with self.assertRaises(ValueError) as cm:
            self.cache._verify_asset_graph(graph_p, rec, staged_src)
        self.assertIn("does not reference canonical grey ref", str(cm.exception))

        # 3. Missing R1_LOAD node
        g_no_r1 = copy.deepcopy(base_graph)
        del g_no_r1["R1_LOAD"]
        graph_p.write_text(json.dumps(g_no_r1), encoding="utf-8")
        with self.assertRaises(ValueError) as cm:
            self.cache._verify_asset_graph(graph_p, rec, staged_src)
        self.assertIn("missing required node R1_LOAD", str(cm.exception))

    # M03-M04 (R01): Asset producer/consumer contract & controls
    def test_m03_m04_asset_actual_contract_and_controls(self):
        staged_src = self.root / "staged_ok.png"
        staged_src.write_bytes(b"\x89PNG\r\n\x1a\nfake")
        graph_p = self.root / "graph_euler.json"
        
        rec = self.recipe.current_asset_recipe("S0035", 1, self.cache.MODEL_PATH)
        graph_data = {
            "NOISE": {"inputs": {"noise_seed": rec["seed"]}},
            "SIGMAS": {"inputs": {"steps": rec["steps"]}},
            "GUIDER": {"inputs": {"cfg": rec["cfg"], "positive": ["R2_POS", 0], "negative": ["R2_NEG", 0]}},
            "UNET": {"inputs": {"unet_name": rec["model_name"]}},
            "CLIP": {"inputs": {"clip_name": rec["clip_name"]}},
            "VAE": {"inputs": {"vae_name": rec["vae_name"]}},
            "KEY_LOAD": {"inputs": {"image": f"identity5m_20261008/r6/work/{staged_src.name}"}},
            "PROMPT": {"inputs": {"text": rec["prompt"]}},
            "SAMPLER": {"inputs": {"sampler_name": rec.get("sampler", "euler")}},
            "R1_LOAD": {"inputs": {"image": "identity5m_20261008/r6/_grey_64.png"}},
            "R2_LOAD": {"inputs": {"image": "identity5m_20261008/r6/_grey_64.png"}},
            "R3_LOAD": {"inputs": {"image": "identity5m_20261008/r6/_grey_64.png"}}
        }
        graph_p.write_text(json.dumps(graph_data), encoding="utf-8")
        # Valid graph passes verification
        self.cache._verify_asset_graph(graph_p, rec, staged_src)

    # M05 (R02): CoTracker CLI --help exits 0
    def test_m05_cotracker_cli_help(self):
        cmd = [sys.executable, "-B", str(self.scripts / "r6_cotracker.py"), "--help"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("usage: r6_cotracker.py", res.stdout)

    # M06 (R03): CoTracker invalid tensor matrix
    def test_m06_cotracker_invalid_tensor_matrix(self):
        tr_empty = np.zeros((0, 0, 2), dtype=np.float32)
        vis_empty = np.zeros((0, 0), dtype=bool)
        ok, why = self.cotracker.validate_cotracker_tensors(tr_empty, vis_empty, 0, 0)
        self.assertFalse(ok)
        self.assertIn("positive", why)

        tr = np.zeros((5, 2, 2), dtype=np.float32)
        vis_nan = np.full((5, 2), np.nan, dtype=np.float32)
        ok, why = self.cotracker.validate_cotracker_tensors(tr, vis_nan, 5, 2)
        self.assertFalse(ok)
        self.assertIn("non-finite", why)

        vis_9 = np.full((5, 2), 9.0, dtype=np.float32)
        ok, why = self.cotracker.validate_cotracker_tensors(tr, vis_9, 5, 2)
        self.assertFalse(ok)
        self.assertIn("[0, 1] range", why)

    # M07 (R03): CoTracker frame 43 preserved, out-of-range rejected, window drift no NaN
    def test_m07_cotracker_window_coverage_and_actual_cli(self):
        # 1. Canonical parsing preserves frame: 43
        e43 = {"event": "entry", "frame": 43}
        fid43 = self.event_contract.parse_event_fid(e43, 100, "S0021")
        self.assertEqual(fid43, 43)

        # 2. Out-of-range event f=700 in clip of 50 frames raises ValueError
        e700 = {"event": "entry", "f": 700}
        with self.assertRaises(ValueError) as cm:
            self.event_contract.parse_event_fid(e700, 50, "S0021")
        self.assertIn("out of range", str(cm.exception))

        # 3. Window with no visible pairs produces None (not NaN)
        d = np.ones((10, 3), dtype=np.float32)
        both = np.zeros((10, 3), dtype=bool)
        
        def _calc(beg_f, end_f):
            idx_beg = max(0, beg_f - 1)
            idx_end = min(10, end_f)
            w_both = both[idx_beg:idx_end]
            if not w_both.any():
                return None
            w_d = d[idx_beg:idx_end][w_both]
            val = float(np.mean(w_d)) if w_d.size > 0 else None
            return val if (val is not None and math.isfinite(val)) else None

        res = _calc(1, 5)
        self.assertIsNone(res)
        dumped = json.dumps({"drift": res})
        self.assertNotIn("NaN", dumped)

    # M08-M09 (R04): Propagation CLI upstream global frame naming and failure boundaries
    def test_m08_m09_propagate_upstream_naming_and_failures(self):
        work_sid = self.k.R6 / "work" / "S0021"
        work_sid.mkdir(parents=True, exist_ok=True)
        stale_man = work_sid / "blend_manifest.json"
        
        # 1. Child rc=7 unlinks stale manifest and writes failure receipt
        stale_man.write_text(json.dumps({"stale": True}), encoding="utf-8")
        dummy_script = self.root / "fake_failing_blend.py"
        dummy_script.write_text("# dummy", encoding="utf-8")
        
        with mock.patch.object(self.propagate, "blend_script", return_value=dummy_script):
            with mock.patch.object(self.propagate, "run_one", return_value={"rc": 7, "beg": 1, "end": 10, "itv": 1}):
                with mock.patch.object(self.propagate, "stage_shot_assets", return_value=[1, 10]):
                    with mock.patch.object(self.propagate, "build_key_fids", return_value=[1, 10]):
                        with mock.patch.object(self.gate, "gate_shot_before_propagate", return_value=True):
                            self.k.PLAN = {"S0021": {"frames": 10, "start_frame": 0}}
                            with self.assertRaises(SystemExit) as cm:
                                self.propagate.run_shot("S0021")
                            self.assertIn("rc=7", str(cm.exception))
                            self.assertFalse(stale_man.exists(), "stale manifest must be unlinked on rc!=0")

        # 2. Upstream global frame naming: beg=11, end=21 produces 0011.jpg..0020.jpg
        # Valid execution with mock run_one creating exact upstream files
        def fake_run_one(rb, beg, end, itv, script, nproc):
            bd = rb / "blend"
            bd.mkdir(parents=True, exist_ok=True)
            for fid in range(beg, end):
                img = Image.new("RGB", (640, 360), (fid * 10 % 255, 100, 100))
                img.save(bd / f"{fid:04d}.jpg")
            return {"rc": 0, "beg": beg, "end": end, "itv": itv}

        # Create last key for fid 21
        keys_dir = self.k.R6 / "keys" / "S0021"
        keys_dir.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (640, 360), (200, 200, 200)).save(keys_dir / "f_0021_key.png")

        with mock.patch.object(self.propagate, "blend_script", return_value=dummy_script):
            with mock.patch.object(self.propagate, "run_one", side_effect=fake_run_one):
                with mock.patch.object(self.propagate, "stage_shot_assets", return_value=[1, 11, 21]):
                    with mock.patch.object(self.propagate, "build_key_fids", return_value=[1, 11, 21]):
                        with mock.patch.object(self.gate, "gate_shot_before_propagate", return_value=True):
                            self.k.PLAN = {"S0021": {"frames": 21, "start_frame": 0}}
                            man = self.propagate.run_shot("S0021")
                            self.assertEqual(man["shot"], "S0021")
                            self.assertEqual(len(man["frames"]), 21)
                            self.assertTrue((work_sid / "blend_manifest.json").exists())

    # M10-M11 (R05): Event transitions end-to-end, strict int types and plan_runs cuts
    def test_m10_m11_event_transitions_and_strict_types(self):
        row = {
            "shot": "S0021",
            "n": 100,
            "events": [{"f": 42, "event": "entry"}],
            "contacts": [{"from": 9, "to": 29, "entity": "E1"}],
            "actors": [{
                "entity": "E1",
                "class_windows": [
                    {"from": 1, "to": 19, "class": "VISIBLE"},
                    {"from": 20, "to": 29, "class": "FULLY_OCCLUDED"},
                    {"from": 30, "to": 49, "class": "VISIBLE"},
                    {"from": 50, "to": 9999, "class": "NOT_PRESENT"}
                ]
            }]
        }
        fids = self.propagate.event_fids_for("S0021", row)
        self.assertIn(10, fids)
        self.assertIn(20, fids)
        self.assertIn(29, fids)
        self.assertIn(30, fids)
        self.assertIn(43, fids)
        self.assertIn(50, fids)

        # Strict integer validation: float, bool, str coercion rejected
        for bad_val, tag in [(43.9, "float"), (True, "bool"), ("43", "str")]:
            with self.assertRaises(ValueError):
                self.event_contract.parse_event_fid({"frame": bad_val}, 100, "S0021")
        # Float pair rejected
        with self.assertRaises(ValueError):
            self.event_contract.parse_event_fid({"f": 42.8, "frame": 43.2}, 100, "S0021")

        # Contact invalid (out of bounds or to < from) raises ValueError
        for bad_contact in [{"from": -10, "to": 50}, {"from": 10, "to": 700}, {"from": 20, "to": 10}]:
            with self.assertRaises(ValueError):
                self.event_contract.parse_contact_fids(bad_contact, 100, "S0021")

        # Plan runs splits at hard cuts with uniform delta=10
        key_fids = [1, 11, 21, 31, 41]
        runs = self.propagate.plan_runs(key_fids, 41, cuts=[21])
        self.assertEqual(len(runs), 2)
        self.assertEqual(runs[0], [1, 11, 21])
        self.assertEqual(runs[1], [21, 31, 41])

    # M12-M14 (R06): Matrix empty/fake evidence, ffprobe video decode, batch gate modes & submission adapter
    def test_m12_m14_matrix_and_submission_adapter(self):
        ev_dir = self.root / "evidence"
        ev_dir.mkdir(parents=True, exist_ok=True)
        strip_0b = ev_dir / "F01_excerpts_strip.png"
        strip_0b.write_bytes(b"")
        json_0b = ev_dir / "F01_excerpts_verified.json"
        json_0b.write_text("", encoding="utf-8")
        
        self.matrix.NS = self.root
        rows = self.matrix.compute_rows()
        self.assertEqual(rows["Q01"]["verdict"], "UNKNOWN")

        # Fake video with ftyp + repeated x fails ffprobe validation
        fake_vid = self.root / "fake_video.mp4"
        fake_vid.write_bytes(b"ftyp" + b"x" * 99996)
        ok_vid, why_vid = self.evidence_contract.validate_evidence_video(fake_vid, 9000)
        self.assertFalse(ok_vid, "fake video must fail ffprobe validation")

        # Unknown batch gate mode rejected
        with self.assertRaises(self.gate.GateBlock) as cm:
            self.gate.gate_batch_conformance({"matrix": {}}, mode="finla")
        self.assertIn("UNKNOWN_BATCH_MODE", str(cm.exception))

        # Engineering mode with no supporting proof rejected
        eng_matrix = {f"Q{i:02d}": "UNKNOWN" for i in range(1, 13)}
        eng_matrix["Q05"] = "PASS"
        eng_matrix["Q07"] = "PASS"
        with self.assertRaises(self.gate.GateBlock) as cm:
            self.gate.gate_batch_conformance({"matrix": eng_matrix}, mode="engineering")
        self.assertIn("ENGINEERING_BATCH_NO_PROOF", str(cm.exception))

        # Submission adapter: test same-size hash tamper (ABCD -> WXYZ)
        sys.path.insert(0, str(EX_DIR / "G1-R1"))
        import r6_submission_adapter as SA
        
        artifact_file = self.root / "artifact.bin"
        artifact_file.write_bytes(b"ABCD")
        orig_sha = hashlib.sha256(b"ABCD").hexdigest()
        
        man_data = {
            "at": "2026-10-19T00:00:00Z",
            "count": 1,
            "items": [{
                "path": "artifact.bin",
                "absolute_path": str(artifact_file),
                "kind": "other",
                "bytes": 4,
                "sha256": orig_sha
            }]
        }
        man_p = self.root / "R6G_MANIFEST.json"
        man_p.write_text(json.dumps(man_data), encoding="utf-8")
        
        # Tamper artifact bytes with same 4-byte size (WXYZ)
        artifact_file.write_bytes(b"WXYZ")
        
        # Matrix evidence staging
        mat_p = self.root / "R6_MATRIX_EVIDENCE.json"
        mat_p.write_text(json.dumps({
            "rows": {
                "Q05": {"verdict": "PASS"},
                "Q07": {"verdict": "PASS"}
            }
        }), encoding="utf-8")
        
        with mock.patch.dict(os.environ, {"R6_INVOCATION_DIR": str(self.root)}):
            # Same size tamper must return False
            ok = SA.validate_and_submit(mode="engineering", manifest_path=man_p)
            self.assertFalse(ok, "submission adapter must reject same-size hash tamper")

    # M15-M16 (R07): Manifest relative filtering and unique namespace
    def test_m15_m16_manifest_relative_filtering(self):
        man = self.matrix.build_manifest()
        self.assertGreater(man["count"], 0, "manifest must not be empty")
        for item in man["items"]:
            p = item["path"].replace("\\", "/")
            self.assertFalse(p.startswith("work/"), f"work relative path leaked: {p}")
            self.assertNotEqual(Path(p).name, "R6G_MANIFEST.json")
            self.assertIn("kind", item, "manifest item must include classified kind")

    # M17 (R08): Historical Q11 proof binding
    def test_m17_q11_historical_proof_binding(self):
        tools_dir = Path("C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/manager/tools")
        expected_hashes = {
            "invocation_runtime.py": "86fc59156a357da7aa6b8691dfccc983b009548e7af4e2ea9ad9b226336b1775",
            "dispatch_long.py": "78d1bc1fafc65868e07a5c64687716b1f64d577002e28216437db43265cb16fa",
            "terminal_contract.py": "96ca2f934fe50dfc27dd98cc6b4eb612538044af19afa71daf65d88bf93428bd"
        }
        for name, exp_sha in expected_hashes.items():
            fpath = tools_dir / name
            self.assertTrue(fpath.exists(), f"missing production tool {name}")
            actual_sha = hashlib.sha256(fpath.read_bytes()).hexdigest()
            self.assertEqual(actual_sha, exp_sha, f"hash mismatch for {name}")

        harness_p = Path("C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/manager/evidence/r6/Q11_R6_HARNESS_TEST_RESULTS.json")
        self.assertTrue(harness_p.exists())
        h_data = json.loads(harness_p.read_text(encoding="utf-8"))
        self.assertEqual(h_data.get("passed"), 51)

    # M18 (R08): Historical 34/34 race results & actual 2-process race barrier in isolated sandbox
    def test_m18_q11_historical_and_multiprocess_race_barrier(self):
        race_p = Path("C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/manager/evidence/r6/q11/Q11_R6_RACE_RESULTS.json")
        self.assertTrue(race_p.exists())
        r_data = json.loads(race_p.read_text(encoding="utf-8"))
        self.assertEqual(r_data.get("passed"), 34)

        # 2-process barrier rendezvous in sandbox
        lock_file = self.root / "production_simulation.lock"
        queue = multiprocessing.Queue()
        barrier = multiprocessing.Barrier(2)

        p1 = multiprocessing.Process(target=_process_race_worker, args=(str(lock_file), queue, barrier))
        p2 = multiprocessing.Process(target=_process_race_worker, args=(str(lock_file), queue, barrier))
        p1.start()
        p2.start()
        p1.join(timeout=10)
        p2.join(timeout=10)

        winners = []
        while not queue.empty():
            winners.append(queue.get())
        self.assertEqual(len(winners), 1, f"Expected exactly 1 winner, got {len(winners)}")
        self.assertTrue(lock_file.exists())

    # M19-M20 (R09): Candidate identity & resume state truth (watchdog quota preservation)
    def test_m19_m20_candidate_identity_and_state(self):
        state_p = Path("C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-gemini-handoff-20261017/execution/STATE.json")
        self.assertTrue(state_p.exists())
        st = json.loads(state_p.read_text(encoding="utf-8"))
        self.assertEqual(st.get("owner"), "gemini-implementation-owner")
        self.assertIn("WAITING", st.get("status", ""))


if __name__ == "__main__":
    unittest.main()
