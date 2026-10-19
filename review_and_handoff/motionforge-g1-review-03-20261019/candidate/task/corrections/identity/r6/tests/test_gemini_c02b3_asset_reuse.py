"""C02B3: actual asset producer, cache and gate in isolated CPU fixtures."""

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
WORKER = Path(os.environ.get("C02B3_WORKER_DIR", Path(__file__).resolve().parents[1] / "work/c02b3-worker")).resolve()
MODULES = ("r6_common", "r6_upload", "r6_adapter", "r6_graph", "r6_cache",
           "r6_key_recipe", "r6_keygen_asset", "r6_gate")


class BaseAssetFixture(unittest.TestCase):
    shot = "S0035"
    frames = 3
    is_black = False

    def setUp(self):
        WORKER.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="c02b3-fixture-", dir=WORKER)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.task = self.root / "task"
        self.r6 = self.task / "corrections/identity/r6"
        self.scripts = self.r6 / "scripts"
        self.scripts.mkdir(parents=True)
        for path in SOURCE_SCRIPTS.glob("*.py"):
            shutil.copyfile(path, self.scripts / path.name)
        (self.task / "chunk_plan.json").write_text(json.dumps({"chunks": [
            {"unit_id": self.shot, "start_frame": 100, "frames": self.frames}]}), encoding="utf-8")
        self.previous = {name: sys.modules.pop(name, None) for name in MODULES}
        sys.path.insert(0, str(self.scripts))
        self.addCleanup(self._restore_modules)
        self.previous_env = {name: os.environ.pop(name, None) for name in
                             ("R6_CTX_FACTOR", "R6_SEED_OFF", "R6_ONLY_ENTITY")}
        self.addCleanup(self._restore_env)

        self.k = importlib.import_module("r6_common")
        self.k.SRC.parent.mkdir(parents=True, exist_ok=True)
        self.k.SRC.write_bytes(b"fixture-source-asset")
        self.model = self.root / "model.bin"
        self.model.write_bytes(b"fixture-model-asset")
        self._write_row()
        (self.r6 / f"storyboard/{self.shot}.json").write_text(json.dumps({
            "shot": self.shot, "n": self.frames, "zero_explicit": True,
            "keys": [{"fid": 1}]}), encoding="utf-8")
        self._write_template()

        self.calls = {name: 0 for name in ("stage", "upload", "post")}
        self.graphs = []
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
        self.recipe_mod = importlib.import_module("r6_key_recipe")
        self.producer = importlib.import_module("r6_keygen_asset")
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
        row = {"shot": self.shot, "zero_explicit": True, "n": self.frames, "src": [100, 100 + self.frames],
               "actors": [], "events": [], "contacts": []}
        (self.r6 / "source_actor_ledger.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")

    def _write_template(self):
        path = self.task / "graph/reuse_bundle/shot_anchor_v1.baseline.api.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        graph = {name: {"class_type": "FixtureNode", "inputs": {}} for name in
                 ("KEY_LOAD", "R1_LOAD", "R2_LOAD", "R3_LOAD", "PROMPT", "NOISE",
                  "LATENT", "SIGMAS", "SAMPLER", "GUIDER", "UNET", "CLIP", "VAE",
                  "SAVE", "R2_POS", "R2_NEG")}
        graph["SIGMAS"]["inputs"] = {"steps": 4, "width": 640, "height": 360}
        graph["SAMPLER"]["inputs"] = {"sampler_name": "euler"}
        graph["GUIDER"]["inputs"] = {"cfg": 1.0}
        graph["UNET"]["inputs"] = {"unet_name": "model.bin"}
        graph["CLIP"]["inputs"] = {"clip_name": "qwen_3_4b.safetensors"}
        graph["VAE"]["inputs"] = {"vae_name": "flux2-vae.safetensors"}
        graph["NOISE"]["inputs"] = {"noise_seed": 1}
        graph["LATENT"]["inputs"] = {"width": 640, "height": 360}
        graph["R2_POS"]["inputs"] = {name: [name, 0] for name in ("KEY_LOAD", "R1_LOAD", "R2_LOAD")}
        graph["R2_NEG"]["inputs"] = {"from": ["R2_POS", 0]}
        path.write_text(json.dumps(graph), encoding="utf-8")

    def _stage(self, sid, gframe, dst):
        self.calls["stage"] += 1
        dst = Path(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if self.is_black:
            Image.new("RGB", (640, 360), (0, 0, 0)).save(dst)
        else:
            arr = np.arange(640 * 360 * 3, dtype=np.uint8).reshape(360, 640, 3)
            Image.fromarray(arr).save(dst)
        receipt = {"contract": self.k._STAGE_CONTRACT,
                   "source_path": str(self.k.SRC.resolve()), "source_sha256": self.k.sha(self.k.SRC),
                   "sid": sid, "gframe": gframe, "output_path": str(dst.resolve()),
                   "output_sha256": self.k.sha(dst), "output_size": dst.stat().st_size}
        dst.with_name(dst.name + ".stage.json").write_text(json.dumps(receipt), encoding="utf-8")
        return dst

    def _upload(self, path, folder):
        self.calls["upload"] += 1
        return folder + "/" + Path(path).name

    def _post(self, graph):
        self.calls["post"] += 1
        self.graphs.append(copy.deepcopy(graph))
        return {"prompt_id": f"fixture-asset-{self.calls['post']}"}

    def _collect(self, history):
        path = self.k.D / "output" / f"edited-asset-{self.calls['post']}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        arr = ((np.arange(640 * 360 * 3, dtype=np.int32).reshape(360, 640, 3) + 10) % 256).astype(np.uint8)
        Image.fromarray(arr).save(path)
        return [path]

    def key(self):
        return self.r6 / f"keys/{self.shot}/f_0001_key.png"

    def deps_path(self):
        return self.r6 / f"work/{self.shot}/f_0001.deps.json"

    def generate(self, review=True):
        self.producer.run_key(self.shot, 1)
        dep = json.loads(self.deps_path().read_text(encoding="utf-8"))
        if review:
            self.gate.write_review("keys", f"{self.shot}_f0001", self.key(),
                                   self.gate.key_inputs_now(self.shot, 1, self.key()),
                                   {"shot": self.shot, "fid": 1}, "PASS", "isolated asset fixture only",
                                   frames=[1], reviewer="fixture-asset-reviewer")
        return dep

    def reseal(self, dep):
        dep["deps_sha"] = hashlib.sha256(json.dumps({k: v for k, v in dep.items()
                                                  if k != "deps_sha"}, sort_keys=True).encode()).hexdigest()
        return dep

    def write_dep(self, dep):
        self.deps_path().write_text(json.dumps(dep), encoding="utf-8")


class AssetRestyleVerifiedReuseTests(BaseAssetFixture):
    is_black = False

    def test_t1_asset_restyle_replay_unchanged(self):
        dep = self.generate(review=True)
        first_calls = dict(self.calls)
        self.assertEqual(first_calls["stage"], 1)
        self.assertEqual(first_calls["post"], 1)
        self.assertEqual(first_calls["upload"], 2)  # key + grey ref
        self.assertEqual(dep["kind"], "r6_key_deps_v4_asset")
        self.assertEqual(dep["mode"], "zero_shot_asset_restyle")
        key_bytes = self.key().read_bytes()
        deps_bytes = self.deps_path().read_bytes()

        ok, why = self.cache.skip_allowed(self.shot, 1, self.key())
        self.assertTrue(ok, f"expected asset verified-reuse, got: {why}")
        self.assertEqual(why, "verified-reuse")

        self.producer.run_key(self.shot, 1)
        self.assertEqual(self.calls, first_calls)
        self.assertEqual(self.key().read_bytes(), key_bytes)
        self.assertEqual(self.deps_path().read_bytes(), deps_bytes)

    def test_t1_missing_review_blocks_skip(self):
        self.generate(review=False)
        ok, why = self.cache.skip_allowed(self.shot, 1, self.key())
        self.assertFalse(ok)
        self.assertIn("review", why.lower())
        self.producer.run_key(self.shot, 1)
        self.assertEqual(self.calls["post"], 2)

    def test_t1_wrong_review_blocks_skip(self):
        self.generate(review=True)
        review_path = self.r6 / f"reviews/keys/{self.shot}_f0001.review.json"
        self.assertTrue(review_path.exists())
        rev = json.loads(review_path.read_text(encoding="utf-8"))
        rev["verdict"] = "FAIL"
        review_path.write_text(json.dumps(rev), encoding="utf-8")
        ok, why = self.cache.skip_allowed(self.shot, 1, self.key())
        self.assertFalse(ok)
        self.assertIn("review", why.lower())

        rev["verdict"] = "PASS"
        rev["artifact"]["sha256"] = "0" * 64
        review_path.write_text(json.dumps(rev), encoding="utf-8")
        ok, why = self.cache.skip_allowed(self.shot, 1, self.key())
        self.assertFalse(ok)
        self.assertIn("review", why.lower())

    def test_t2_same_path_same_size_mutations_and_restores(self):
        self.generate(review=True)
        self.assertTrue(self.cache.skip_allowed(self.shot, 1, self.key())[0])

        def check_mutate(path):
            orig = path.read_bytes()
            self.assertTrue(len(orig) > 0)
            mutated = (bytearray(orig)[:-1] + bytes([orig[-1] ^ 0xFF]) if len(orig) == 1
                       else bytearray(orig)[:-1] + bytes([(orig[-1] + 1) % 256]))
            path.write_bytes(bytes(mutated))
            ok, why = self.cache.skip_allowed(self.shot, 1, self.key())
            self.assertFalse(ok, f"{path} mutation should have invalidated: {why}")
            path.write_bytes(orig)
            ok, why = self.cache.skip_allowed(self.shot, 1, self.key())
            self.assertTrue(ok, f"{path} restore should have been valid: {why}")

        check_mutate(self.k.SRC)
        check_mutate(self.model)
        check_mutate(self.r6 / f"work/{self.shot}/f_0001_src.png")
        check_mutate(self.r6 / f"work/{self.shot}/f_0001_src.png.stage.json")
        check_mutate(self.r6 / f"workflows/r6_asset_{self.shot}_f1.json")
        check_mutate(self.k.INP / "_grey_64.png")

    def test_t2_settings_and_storyboard_mutations(self):
        self.generate(review=True)
        self.assertTrue(self.cache.skip_allowed(self.shot, 1, self.key())[0])

        # Seed offset mutation
        os.environ["R6_SEED_OFF"] = "99"
        self.assertFalse(self.cache.skip_allowed(self.shot, 1, self.key())[0])
        os.environ.pop("R6_SEED_OFF")
        self.assertTrue(self.cache.skip_allowed(self.shot, 1, self.key())[0])

        # Storyboard mutation
        sb_p = self.r6 / f"storyboard/{self.shot}.json"
        orig_sb = sb_p.read_text(encoding="utf-8")
        sb = json.loads(orig_sb)
        sb["n"] = 999
        sb_p.write_text(json.dumps(sb), encoding="utf-8")
        self.assertFalse(self.cache.skip_allowed(self.shot, 1, self.key())[0])
        sb_p.write_text(orig_sb, encoding="utf-8")
        self.assertTrue(self.cache.skip_allowed(self.shot, 1, self.key())[0])

    def test_t4_legacy_v3_asset_record_denial(self):
        self.generate(review=True)
        cur_settings = self.cache.settings_now(self.shot, 1)
        v3_dep = self.cache.build_deps(self.shot, 1,
                                       {"source_span_lo": 100, "source_span_hi": 103,
                                        "gframe": 100, "casts": [], "masks": [],
                                        "graph": self.r6 / f"workflows/r6_asset_{self.shot}_f1.json"},
                                       cur_settings)
        ok, why = self.cache.verify_deps(v3_dep, self.shot, 1)
        self.assertTrue(ok, f"legacy v3 verify_deps should pass: {why}")

        self.write_dep(v3_dep)
        ok, why = self.cache.skip_allowed(self.shot, 1, self.key())
        self.assertFalse(ok)
        self.assertIn("legacy v3 lacks complete", why)

    def test_t5_injected_post_failure_does_not_publish_deps(self):
        def post_fail(g):
            raise RuntimeError("injected ComfyUI asset communication failure")
        self.k.post = post_fail
        with self.assertRaises(RuntimeError):
            self.producer.run_key(self.shot, 1)
        self.assertFalse(self.deps_path().exists())

    def test_t5_blank_edit_failure_does_not_publish_deps(self):
        blank_path = self.k.D / "output" / "blank_asset.png"
        blank_path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (640, 360), (0, 0, 0)).save(blank_path)
        self.k.collect_outputs = lambda h: [blank_path]
        with self.assertRaises(SystemExit):
            self.producer.run_key(self.shot, 1)
        self.assertFalse(self.deps_path().exists())


class AssetBlackPassthroughTests(BaseAssetFixture):
    is_black = True

    def test_t3_black_passthrough_replay_unchanged(self):
        dep = self.generate(review=True)
        first_calls = dict(self.calls)
        self.assertEqual(first_calls["stage"], 1)
        self.assertEqual(first_calls["post"], 0)
        self.assertEqual(first_calls["upload"], 0)
        self.assertEqual(dep["kind"], "r6_key_deps_v4_asset")
        self.assertEqual(dep["mode"], "asset_black_passthrough")
        self.assertIsNone(dep["consumed"]["graph"])

        ok, why = self.cache.skip_allowed(self.shot, 1, self.key())
        self.assertTrue(ok, f"black passthrough skip failed: {why}")

        self.producer.run_key(self.shot, 1)
        self.assertEqual(self.calls, first_calls)

    def test_t3_black_passthrough_rejects_non_flat_source(self):
        dep = self.generate(review=True)
        # Mutate staged source to non-flat pixels (std >= 6.0)
        arr = np.arange(640 * 360 * 3, dtype=np.uint8).reshape(360, 640, 3)
        staged = self.r6 / f"work/{self.shot}/f_0001_src.png"
        Image.fromarray(arr).save(staged)
        ok, why = self.cache.skip_allowed(self.shot, 1, self.key())
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
