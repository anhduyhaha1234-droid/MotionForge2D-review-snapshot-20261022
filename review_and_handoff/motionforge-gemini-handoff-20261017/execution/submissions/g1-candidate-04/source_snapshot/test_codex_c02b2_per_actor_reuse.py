"""C02B2: actual per-actor producer, cache and gate in isolated CPU fixtures."""

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
from unittest.mock import patch

import numpy as np
import torch
from PIL import Image


SOURCE_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
WORKER = Path(os.environ.get("C02B2_WORKER_DIR", Path(__file__).resolve().parents[1] / "work/c02b2-worker")).resolve()
MODULES = ("r6_common", "r6_upload", "r6_adapter", "r6_graph", "r6_cache",
           "r6_key_recipe", "r6_keygen", "r6_gate")


class BasePerActorFixture(unittest.TestCase):
    actors = ("E1",)
    masks = {"E1": "full"}
    visible = True

    def setUp(self):
        WORKER.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="c02b2-fixture-", dir=WORKER)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.task = self.root / "task"
        self.r6 = self.task / "corrections/identity/r6"
        self.scripts = self.r6 / "scripts"
        self.scripts.mkdir(parents=True)
        for path in SOURCE_SCRIPTS.glob("*.py"):
            shutil.copyfile(path, self.scripts / path.name)
        (self.task / "chunk_plan.json").write_text(json.dumps({"chunks": [
            {"unit_id": "S0021", "start_frame": 0, "frames": 3}]}), encoding="utf-8")
        self.previous = {name: sys.modules.pop(name, None) for name in MODULES}
        sys.path.insert(0, str(self.scripts))
        self.addCleanup(self._restore_modules)
        self.previous_env = {name: os.environ.pop(name, None) for name in
                             ("R6_CTX_FACTOR", "R6_SEED_OFF", "R6_ONLY_ENTITY")}
        self.addCleanup(self._restore_env)

        self.k = importlib.import_module("r6_common")
        self.k.SRC.parent.mkdir(parents=True, exist_ok=True)
        self.k.SRC.write_bytes(b"fixture-source")
        self.model = self.root / "model.bin"
        self.model.write_bytes(b"fixture-model")
        self._write_row()
        (self.r6 / "storyboard/S0021.json").write_text(json.dumps({
            "shot": "S0021", "n": 3, "zero_explicit": False,
            "keys": [{"fid": 1}]}), encoding="utf-8")
        self._write_template()
        self.mask_arrays = {}
        for entity in self.actors:
            front_name = self.k.CASTB_OF_ENTITY[entity]
            for name in (front_name, front_name.replace("_front_bust", "_profile")):
                cast = self.k.R4 / "assets/cast_b" / name
                cast.parent.mkdir(parents=True, exist_ok=True)
                cast.write_bytes(("cast-" + name).encode())
            mask = self.r6 / "masks/S0021" / entity / "f_0001.png"
            mask.parent.mkdir(parents=True, exist_ok=True)
            array = np.zeros((8, 8), dtype=np.float32)
            shape = self.masks[entity]
            if shape == "full":
                array[:, :] = 1
            elif shape == "left":
                array[:, :4] = 1
            elif shape == "right":
                array[:, 4:] = 1
            self.mask_arrays[entity] = array
            Image.fromarray((array * 255).astype(np.uint8)).save(mask)

        self.calls = {name: 0 for name in ("stage", "crop", "upload", "post")}
        self.crop_factors = []
        self.graphs = []
        self.frame = torch.arange(1 * 8 * 8 * 3, dtype=torch.float32).reshape(1, 8, 8, 3) / 192
        adapter = types.ModuleType("r6_adapter")
        adapter.__file__ = str(self.scripts / "r6_adapter.py")
        def _load_img(path):
            if "blank" in Path(path).name:
                return torch.zeros((1, 8, 8, 3), dtype=torch.float32)
            return self.frame.clone()
        adapter.load_img = _load_img
        adapter.load_mask = lambda path: torch.from_numpy(self.mask_arrays[Path(path).parent.name].copy())[None, ...]
        adapter.save_img = self._save_img
        adapter.crop_for_mask = self._crop
        adapter.stitch_back = lambda res, edited: edited.clone()
        adapter.bound_check = lambda before, after, mask: {"ok": True}
        sys.modules["r6_adapter"] = adapter
        upload = types.ModuleType("r6_upload")
        upload.__file__ = str(self.scripts / "r6_upload.py")
        upload.upload_image = self._upload
        sys.modules["r6_upload"] = upload

        self.k.stage_frame = self._stage
        self.k.post = self._post
        self.k.wait = lambda *args, **kwargs: {}
        self.k.collect_outputs = self._collect
        self.cache = importlib.import_module("r6_cache")
        self.cache.MODEL_PATH = self.model
        self.producer = importlib.import_module("r6_keygen")
        self.gate = importlib.import_module("r6_gate")

    def _restore_modules(self):
        sys.path.remove(str(self.scripts))
        for name, old in self.previous.items():
            sys.modules.pop(name, None)
            if old is not None:
                sys.modules[name] = old

    def _restore_env(self):
        for name, value in self.previous_env.items():
            os.environ.pop(name, None)
            if value is not None:
                os.environ[name] = value

    def _write_row(self):
        row = {"shot": "S0021", "zero_explicit": False, "n": 3, "src": [0, 3],
               "actors": [{"entity": entity, "class_windows": [
                   {"from": 1, "to": 3, "class": "VISIBLE" if self.visible else "NOT_PRESENT"}]}
                          for entity in self.actors], "events": [], "contacts": []}
        (self.r6 / "source_actor_ledger.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")

    def _write_template(self):
        path = self.task / "graph/reuse_bundle/shot_anchor_v1.baseline.api.json"
        path.parent.mkdir(parents=True)
        graph = {name: {"class_type": "FixtureNode", "inputs": {}} for name in
                 ("KEY_LOAD", "R1_LOAD", "R2_LOAD", "R3_LOAD", "PROMPT", "NOISE",
                  "LATENT", "SIGMAS", "SAMPLER", "GUIDER", "UNET", "CLIP", "VAE",
                  "SAVE", "R2_POS", "R2_NEG")}
        graph["SIGMAS"]["inputs"] = {"steps": 4, "width": 8, "height": 8}
        graph["SAMPLER"]["inputs"] = {"sampler_name": "euler"}
        graph["GUIDER"]["inputs"] = {"cfg": 1.0}
        graph["UNET"]["inputs"] = {"unet_name": "model.bin"}
        graph["CLIP"]["inputs"] = {"clip_name": "qwen_3_4b.safetensors"}
        graph["VAE"]["inputs"] = {"vae_name": "flux2-vae.safetensors"}
        graph["NOISE"]["inputs"] = {"noise_seed": 1}
        graph["LATENT"]["inputs"] = {"width": 8, "height": 8}
        graph["R2_POS"]["inputs"] = {name: [name, 0] for name in ("KEY_LOAD", "R1_LOAD", "R2_LOAD")}
        graph["R2_NEG"]["inputs"] = {"from": ["R2_POS", 0]}
        path.write_text(json.dumps(graph), encoding="utf-8")

    def _stage(self, sid, gframe, dst):
        self.calls["stage"] += 1
        dst = Path(dst)
        Image.new("RGB", (8, 8), (10, 20, 30)).save(dst)
        receipt = {"contract": self.k._STAGE_CONTRACT,
                   "source_path": str(self.k.SRC.resolve()), "source_sha256": self.k.sha(self.k.SRC),
                   "sid": sid, "gframe": gframe, "output_path": str(dst.resolve()),
                   "output_sha256": self.k.sha(dst), "output_size": dst.stat().st_size}
        dst.with_name(dst.name + ".stage.json").write_text(json.dumps(receipt), encoding="utf-8")
        return dst

    def _save_img(self, tensor, path):
        array = (tensor[0].clamp(0, 1).numpy() * 255).astype(np.uint8)
        Image.fromarray(array).save(path)

    def _crop(self, frame, mask, context_factor):
        self.calls["crop"] += 1
        self.crop_factors.append(context_factor)
        return [None, None, None, None, None, frame.clone()], {
            "x": 0, "y": 0, "w": 8, "h": 8, "mask_px": int(mask.sum()), "target": [8, 8]}

    def _upload(self, path, folder):
        self.calls["upload"] += 1
        return folder + "/" + Path(path).name

    def _post(self, graph):
        self.calls["post"] += 1
        self.graphs.append(copy.deepcopy(graph))
        return {"prompt_id": f"fixture-{self.calls['post']}"}

    def _collect(self, history):
        path = self.k.D / "output" / f"edited-{self.calls['post']}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (8, 8), (40 + self.calls["post"], 50, 60)).save(path)
        return [path]

    def key(self):
        return self.r6 / "keys/S0021/f_0001_key.png"

    def deps_path(self):
        return self.r6 / "work/S0021/f_0001.deps.json"

    def generate(self, review=True):
        self.producer.run_key("S0021", 1)
        dep = json.loads(self.deps_path().read_text(encoding="utf-8"))
        if review:
            self.gate.write_review("keys", "S0021_f0001", self.key(),
                                   self.gate.key_inputs_now("S0021", 1, self.key()),
                                   {"shot": "S0021", "fid": 1}, "PASS", "isolated fixture only",
                                   frames=[1], reviewer="fixture-reviewer")
        return dep

    def reseal(self, dep):
        dep["deps_sha"] = hashlib.sha256(json.dumps({k: v for k, v in dep.items()
                                                  if k != "deps_sha"}, sort_keys=True).encode()).hexdigest()
        return dep

    def write_dep(self, dep):
        self.deps_path().write_text(json.dumps(dep), encoding="utf-8")


class SingleActorVerifiedReuseTests(BasePerActorFixture):
    actors = ("E1",)
    masks = {"E1": "full"}
    visible = True

    def test_p1_single_actor_replay_unchanged(self):
        dep = self.generate(review=True)
        first_calls = dict(self.calls)
        self.assertEqual(first_calls["stage"], 1)
        self.assertEqual(first_calls["crop"], 1)
        self.assertEqual(first_calls["upload"], 4)
        self.assertEqual(first_calls["post"], 1)
        key_bytes = self.key().read_bytes()
        deps_bytes = self.deps_path().read_bytes()

        ok, why = self.cache.skip_allowed("S0021", 1, self.key())
        self.assertTrue(ok, f"expected verified-reuse, got: {why}")
        self.assertEqual(why, "verified-reuse")

        self.producer.run_key("S0021", 1)
        self.assertEqual(self.calls, first_calls)
        self.assertEqual(self.key().read_bytes(), key_bytes)
        self.assertEqual(self.deps_path().read_bytes(), deps_bytes)

    def test_p1_missing_review_blocks_skip(self):
        self.generate(review=False)
        ok, why = self.cache.skip_allowed("S0021", 1, self.key())
        self.assertFalse(ok)
        self.assertTrue("review" in why.lower())
        self.producer.run_key("S0021", 1)
        self.assertEqual(self.calls["post"], 2)

    def test_p1_wrong_review_blocks_skip(self):
        self.generate(review=True)
        review_path = self.r6 / "reviews/keys/S0021_f0001.review.json"
        self.assertTrue(review_path.exists())
        rev = json.loads(review_path.read_text(encoding="utf-8"))
        rev["verdict"] = "FAIL"
        review_path.write_text(json.dumps(rev), encoding="utf-8")
        ok, why = self.cache.skip_allowed("S0021", 1, self.key())
        self.assertFalse(ok)
        self.assertTrue("review" in why.lower())

        rev["verdict"] = "PASS"
        rev["artifact"]["sha256"] = "0" * 64
        review_path.write_text(json.dumps(rev), encoding="utf-8")
        ok, why = self.cache.skip_allowed("S0021", 1, self.key())
        self.assertFalse(ok)
        self.assertTrue("review" in why.lower())

    def test_p2_effective_settings_independent_mutations(self):
        self.generate(review=True)
        self.assertTrue(self.cache.skip_allowed("S0021", 1, self.key())[0])

        # 1. R6_CTX_FACTOR
        os.environ["R6_CTX_FACTOR"] = "1.5"
        self.assertFalse(self.cache.skip_allowed("S0021", 1, self.key())[0])
        os.environ.pop("R6_CTX_FACTOR")
        self.assertTrue(self.cache.skip_allowed("S0021", 1, self.key())[0])

        # 2. R6_SEED_OFF
        os.environ["R6_SEED_OFF"] = "42"
        self.assertFalse(self.cache.skip_allowed("S0021", 1, self.key())[0])
        os.environ.pop("R6_SEED_OFF")
        self.assertTrue(self.cache.skip_allowed("S0021", 1, self.key())[0])

        # 3. R6_ONLY_ENTITY
        os.environ["R6_ONLY_ENTITY"] = "E9"
        self.assertFalse(self.cache.skip_allowed("S0021", 1, self.key())[0])
        os.environ.pop("R6_ONLY_ENTITY")
        self.assertTrue(self.cache.skip_allowed("S0021", 1, self.key())[0])

        # 4. Ledger class mutation
        ledger_path = self.r6 / "source_actor_ledger.jsonl"
        orig_ledger = ledger_path.read_text(encoding="utf-8")
        row = json.loads(orig_ledger)
        row["actors"][0]["class_windows"][0]["class"] = "NOT_PRESENT"
        ledger_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
        self.assertFalse(self.cache.skip_allowed("S0021", 1, self.key())[0])
        ledger_path.write_text(orig_ledger, encoding="utf-8")
        self.assertTrue(self.cache.skip_allowed("S0021", 1, self.key())[0])

        # 5. Storyboard mutation
        sb_path = self.r6 / "storyboard/S0021.json"
        orig_sb = sb_path.read_text(encoding="utf-8")
        sb = json.loads(orig_sb)
        sb["keys"] = [{"fid": 1}, {"fid": 2}]
        sb_path.write_text(json.dumps(sb), encoding="utf-8")
        self.assertFalse(self.cache.skip_allowed("S0021", 1, self.key())[0])
        sb_path.write_text(orig_sb, encoding="utf-8")
        self.assertTrue(self.cache.skip_allowed("S0021", 1, self.key())[0])

        # 6. Template mutation (steps)
        tpl_path = self.task / "graph/reuse_bundle/shot_anchor_v1.baseline.api.json"
        orig_tpl = tpl_path.read_text(encoding="utf-8")
        tpl = json.loads(orig_tpl)
        tpl["SIGMAS"]["inputs"]["steps"] = 8
        tpl_path.write_text(json.dumps(tpl), encoding="utf-8")
        self.assertFalse(self.cache.skip_allowed("S0021", 1, self.key())[0])
        tpl_path.write_text(orig_tpl, encoding="utf-8")
        self.assertTrue(self.cache.skip_allowed("S0021", 1, self.key())[0])

        # 7. Code hash mutation
        code_path = self.scripts / "r6_keygen.py"
        orig_code = code_path.read_bytes()
        code_path.write_bytes(orig_code + b"\n# comment\n")
        self.assertFalse(self.cache.skip_allowed("S0021", 1, self.key())[0])
        code_path.write_bytes(orig_code)
        self.assertTrue(self.cache.skip_allowed("S0021", 1, self.key())[0])

    def test_p3_same_path_same_size_mutations_and_restores(self):
        self.generate(review=True)
        self.assertTrue(self.cache.skip_allowed("S0021", 1, self.key())[0])

        def check_mutate(path):
            orig = path.read_bytes()
            self.assertTrue(len(orig) > 0)
            mutated = (bytearray(orig)[:-1] + bytes([orig[-1] ^ 0xFF]) if len(orig) == 1
                       else bytearray(orig)[:-1] + bytes([(orig[-1] + 1) % 256]))
            path.write_bytes(bytes(mutated))
            ok, why = self.cache.skip_allowed("S0021", 1, self.key())
            self.assertFalse(ok, f"{path} mutation should have invalidated: {why}")
            path.write_bytes(orig)
            ok, why = self.cache.skip_allowed("S0021", 1, self.key())
            self.assertTrue(ok, f"{path} restore should have been valid: {why}")

        check_mutate(self.k.SRC)
        check_mutate(self.model)
        front_name = self.k.CASTB_OF_ENTITY["E1"]
        check_mutate(self.k.R4 / "assets/cast_b" / front_name)
        profile_name = front_name.replace("_front_bust", "_profile")
        check_mutate(self.k.R4 / "assets/cast_b" / profile_name)
        check_mutate(self.k.INP / "keys/cast_refs" / front_name)
        check_mutate(self.k.INP / "keys/cast_refs" / profile_name)
        check_mutate(self.r6 / "work/S0021/f_0001_src.png")
        check_mutate(self.r6 / "work/S0021/f_0001_src.png.stage.json")
        check_mutate(self.r6 / "masks/S0021/E1/f_0001.png")
        check_mutate(self.r6 / "work/S0021/f_0001_E1_crop.png")
        check_mutate(self.k.D / "output/edited-1.png")
        check_mutate(self.r6 / "workflows/r6_crop_S0021_f1_E1.json")

    def test_p4_malformed_and_truncated_records(self):
        dep = self.generate(review=True)
        self.assertTrue(self.cache.skip_allowed("S0021", 1, self.key())[0])

        # 1. Tampered deps_sha
        bad_seal = copy.deepcopy(dep)
        bad_seal["deps_sha"] = "0" * 64
        self.write_dep(bad_seal)
        ok, why = self.cache.skip_allowed("S0021", 1, self.key())
        self.assertFalse(ok)
        self.assertIn("self-digest mismatch", why)

        # 2. Truncated consumed actors list with recomputed self-digest
        trunc_actors = copy.deepcopy(dep)
        trunc_actors["consumed"]["actors"] = []
        self.write_dep(self.reseal(trunc_actors))
        ok, why = self.cache.skip_allowed("S0021", 1, self.key())
        self.assertFalse(ok)
        self.assertIn("actor", why.lower())

        # 3. Truncated consumed masks list with recomputed self-digest
        trunc_masks = copy.deepcopy(dep)
        trunc_masks["consumed"]["masks"] = []
        self.write_dep(self.reseal(trunc_masks))
        ok, why = self.cache.skip_allowed("S0021", 1, self.key())
        self.assertFalse(ok)
        self.assertIn("mask", why.lower())

        # 4. Type bool for number (fid)
        bad_type = copy.deepcopy(dep)
        bad_type["fid"] = True
        self.write_dep(self.reseal(bad_type))
        ok, why = self.cache.skip_allowed("S0021", 1, self.key())
        self.assertFalse(ok)

        # 5. Non-finite JSON value
        bad_num = copy.deepcopy(dep)
        bad_num["recipe"]["cfg"] = float("nan")
        with open(self.deps_path(), "w", encoding="utf-8") as f:
            json.dump(bad_num, f, allow_nan=True)
        ok, why = self.cache.skip_allowed("S0021", 1, self.key())
        self.assertFalse(ok)

        # 6. Duplicate JSON keys
        self.write_dep(dep)
        raw_text = self.deps_path().read_text(encoding="utf-8")
        dup_text = raw_text.replace('"shot": "S0021"', '"shot": "S0021", "shot": "S0021"')
        self.deps_path().write_text(dup_text, encoding="utf-8")
        ok, why = self.cache.skip_allowed("S0021", 1, self.key())
        self.assertFalse(ok)

        # 7. Extreme depth (> 256)
        deep = "leaf"
        for _ in range(300):
            deep = [deep]
        dep_deep = copy.deepcopy(dep)
        dep_deep["consumed"]["excessive"] = deep
        self.write_dep(self.reseal(dep_deep))
        ok, why = self.cache.skip_allowed("S0021", 1, self.key())
        self.assertFalse(ok)

        # 8. Request shot / fid mismatch
        ok, why = self.cache.verify_complete_deps(dep, "S0022", 1)
        self.assertFalse(ok)
        self.assertIn("shot differs", why)
        ok, why = self.cache.verify_complete_deps(dep, "S0021", 2)
        self.assertFalse(ok)
        self.assertIn("fid differs", why)

        # 9. Legacy v3 recorded positive vs complete skip denial
        cur_settings = self.cache.settings_now("S0021", 1)
        graph_file = self.r6 / "workflows/r6_crop_S0021_f1_E1.json"
        v3_dep = self.cache.build_deps("S0021", 1,
                                       {"gframe": 0, "source_span_lo": 0, "source_span_hi": 3,
                                        "casts": [], "masks": [], "graph": graph_file},
                                       cur_settings)
        ok, why = self.cache.verify_deps(v3_dep, "S0021", 1)
        self.assertTrue(ok, f"legacy v3 recorded validation should pass: {why}")

        self.write_dep(v3_dep)
        ok, why = self.cache.skip_allowed("S0021", 1, self.key())
        self.assertFalse(ok)
        self.assertIn("legacy v3 lacks complete per-actor provenance", why)

    def test_p5_injected_generation_failure_does_not_publish_deps(self):
        def post_fail(g):
            raise RuntimeError("injected ComfyUI communication failure")
        self.k.post = post_fail
        with self.assertRaises(RuntimeError):
            self.producer.run_key("S0021", 1)
        self.assertFalse(self.deps_path().exists())

    def test_p5_blank_edit_failure_does_not_publish_deps(self):
        blank_path = self.k.D / "output" / "blank.png"
        blank_path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (8, 8), (0, 0, 0)).save(blank_path)
        self.k.collect_outputs = lambda h: [blank_path]
        with self.assertRaises(SystemExit):
            self.producer.run_key("S0021", 1)
        self.assertFalse(self.deps_path().exists())

    def test_p5_bound_check_failure_does_not_publish_deps(self):
        sys.modules["r6_adapter"].bound_check = lambda b, a, m: {"ok": False, "frac_core8": 0.5, "frac_outside": 0.5}
        with self.assertRaises(SystemExit):
            self.producer.run_key("S0021", 1)
        self.assertFalse(self.deps_path().exists())

    def test_p5_standalone_gate_import(self):
        proc = subprocess.run([
            sys.executable, "-c",
            f"import sys; sys.path.insert(0, r'{self.scripts}'); import r6_gate; assert 'r6_adapter' not in sys.modules; assert 'torch' not in sys.modules; print('STANDALONE_GATE_OK')"
        ], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("STANDALONE_GATE_OK", proc.stdout)


class MultiActorVerifiedReuseTests(BasePerActorFixture):
    actors = ("E1", "E2")
    masks = {"E1": "left", "E2": "right"}
    visible = True

    def test_p1_multi_actor_replay_unchanged(self):
        dep = self.generate(review=True)
        first_calls = dict(self.calls)
        self.assertEqual(first_calls["crop"], 2)
        self.assertEqual(first_calls["post"], 2)
        self.assertEqual(first_calls["upload"], 8)
        self.assertEqual(len(dep["consumed"]["actors"]), 2)

        ok, why = self.cache.skip_allowed("S0021", 1, self.key())
        self.assertTrue(ok, f"expected multi-actor verified-reuse, got: {why}")

        self.producer.run_key("S0021", 1)
        self.assertEqual(self.calls, first_calls)

    def test_p3_multi_actor_nonfirst_graph_mutation(self):
        self.generate(review=True)
        nonfirst_graph = self.r6 / "workflows/r6_crop_S0021_f1_E2.json"
        self.assertTrue(nonfirst_graph.exists())
        orig = nonfirst_graph.read_bytes()
        mutated = (bytearray(orig)[:-1] + bytes([orig[-1] ^ 0xFF]) if len(orig) == 1
                   else bytearray(orig)[:-1] + bytes([(orig[-1] + 1) % 256]))
        nonfirst_graph.write_bytes(bytes(mutated))
        ok, why = self.cache.skip_allowed("S0021", 1, self.key())
        self.assertFalse(ok)
        self.assertIn("hash changed", why)
        nonfirst_graph.write_bytes(orig)
        ok, why = self.cache.skip_allowed("S0021", 1, self.key())
        self.assertTrue(ok)


class NoVisibleActorVerifiedReuseTests(BasePerActorFixture):
    actors = ("E1",)
    masks = {"E1": "full"}
    visible = False

    def test_no_visible_actor_positive(self):
        dep = self.generate(review=True)
        self.assertEqual(self.calls["crop"], 0)
        self.assertEqual(self.calls["post"], 0)
        self.assertEqual(self.calls["upload"], 0)
        self.assertEqual(dep["recipe"]["mode"], "keep_source_no_visible_actor")
        self.assertEqual(len(dep["consumed"]["actors"]), 0)
        self.assertTrue(self.key().exists())

        ok, why = self.cache.skip_allowed("S0021", 1, self.key())
        self.assertTrue(ok, f"no-visible-actor skip failed: {why}")

        calls_before = dict(self.calls)
        self.producer.run_key("S0021", 1)
        self.assertEqual(self.calls, calls_before)


class FullyCoveredActorReuseTests(BasePerActorFixture):
    actors = ("E1", "E2")
    masks = {"E1": "full", "E2": "full"}
    visible = True

    def test_fully_covered_actor_fewer_graphs(self):
        dep = self.generate(review=True)
        self.assertEqual(self.calls["crop"], 1)
        self.assertEqual(self.calls["post"], 1)
        actors = dep["consumed"]["actors"]
        self.assertEqual(len(actors), 2)
        self.assertEqual(actors[0]["status"], "generated")
        self.assertEqual(actors[1]["status"], "fully_covered")
        self.assertNotIn("graph", actors[1])

        ok, why = self.cache.skip_allowed("S0021", 1, self.key())
        self.assertTrue(ok, f"covered actor skip failed: {why}")

        calls_before = dict(self.calls)
        self.producer.run_key("S0021", 1)
        self.assertEqual(self.calls, calls_before)


if __name__ == "__main__":
    unittest.main()





