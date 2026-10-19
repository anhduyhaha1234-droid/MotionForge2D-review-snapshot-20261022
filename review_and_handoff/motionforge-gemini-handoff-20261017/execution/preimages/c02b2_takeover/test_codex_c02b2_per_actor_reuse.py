"""C02B2: actual per-actor producer, cache and gate in isolated CPU fixtures."""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
import shutil
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
WORKER = Path(os.environ["C02B2_WORKER_DIR"]).resolve()
MODULES = ("r6_common", "r6_upload", "r6_adapter", "r6_graph", "r6_cache",
           "r6_key_recipe", "r6_keygen", "r6_gate")


class PerActorVerifiedReuseTests(unittest.TestCase):
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
        adapter.load_img = lambda path: self.frame.clone()
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
