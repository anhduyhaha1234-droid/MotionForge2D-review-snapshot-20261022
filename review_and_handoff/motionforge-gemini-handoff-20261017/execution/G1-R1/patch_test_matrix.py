import os

test_path = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\tests\test_g1_r1_correction.py"
with open(test_path, "r", encoding="utf-8") as f:
    src = f.read()

# Replace setUp and test_m01 to test_m03
old_setup_block = '''        # Scaffold template
        tpl_path = self.task / "graph/reuse_bundle/shot_anchor_v1.baseline.api.json"
        tpl_path.parent.mkdir(parents=True, exist_ok=True)'''

new_setup_block = '''        # Scaffold template
        tpl_path = self.k.D / "graph/reuse_bundle/shot_anchor_v1.baseline.api.json"
        tpl_path.parent.mkdir(parents=True, exist_ok=True)'''

assert src.count(old_setup_block) == 1
src = src.replace(old_setup_block, new_setup_block)

# Add _stage helper
stage_helper = '''
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
'''

if "def _stage" not in src:
    idx = src.find("    # M01 (R01):")
    assert idx != -1
    src = src[:idx] + stage_helper + "\n" + src[idx:]

# Update test_m01
old_m01 = '''    # M01 (R01): Missing consumed grey_ref rejected even with valid self-digest
    def test_m01_asset_missing_grey_ref_rejected(self):
        dep = {
            "kind": "r6_key_deps_v4_asset",
            "shot": "S0035",
            "fid": 1,
            "mode": "zero_shot_asset_restyle",
            "source": {"role": "source", "path": str(self.k.SRC), "sha256": self.k.sha(self.k.SRC)},
            "model": {"role": "model", "path": str(self.cache.MODEL_PATH), "sha256": self.k.sha(self.cache.MODEL_PATH)},
            "recipe": self.recipe.current_asset_recipe("S0035", 1, self.cache.MODEL_PATH),
            "consumed": {
                "staged_source": {"role": "staged_source", "path": str(self.root / "src.png"), "sha256": "0"*64},
                "stage_receipt": {"role": "stage_receipt", "path": str(self.root / "rec.json"), "sha256": "0"*64},
                "graph": {"role": "graph", "path": str(self.root / "graph.json"), "sha256": "0"*64}
                # Missing grey_ref!
            }
        }
        body = {k: v for k, v in dep.items() if k != "deps_sha"}
        dep["deps_sha"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        
        ok, why = self.cache.verify_complete_asset_deps(dep, "S0035", 1)
        self.assertFalse(ok)
        self.assertIn("missing consumed grey_ref", why)'''

new_m01 = '''    # M01 (R01): Missing consumed grey_ref rejected even with valid self-digest
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
        self.assertIn("missing consumed grey_ref", why)'''

assert src.count(old_m01) == 1
src = src.replace(old_m01, new_m01)

with open(test_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)
print("Updated test_g1_r1_correction.py with stage helper and template path")
