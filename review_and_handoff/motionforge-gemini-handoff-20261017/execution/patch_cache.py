import os

cache_path = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_cache.py"
with open(cache_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add COMPLETE_ASSET_KIND
old1 = 'COMPLETE_KIND = "r6_key_deps_v4_per_actor"\n'
new1 = 'COMPLETE_KIND = "r6_key_deps_v4_per_actor"\nCOMPLETE_ASSET_KIND = "r6_key_deps_v4_asset"\n'
assert content.count(old1) == 1, f"old1 count: {content.count(old1)}"
content = content.replace(old1, new1)

# 2. Add build_complete_asset_deps and verification functions before verify_deps
funcs = '''
def build_complete_asset_deps(sid: str, fid: int, recipe: dict, consumed: dict, mode: str) -> dict:
    """Build the complete v4 asset contract."""
    from r6_key_recipe import current_asset_recipe
    if mode not in ("zero_shot_asset_restyle", "asset_black_passthrough"):
        raise ValueError(f"invalid asset mode: {mode}")
    cur_recipe = current_asset_recipe(sid, fid, MODEL_PATH)
    if json.dumps(recipe, sort_keys=True, allow_nan=False) != json.dumps(
            cur_recipe, sort_keys=True, allow_nan=False):
        raise ValueError("asset recipe changed during generation")

    consumed_rec = {
        "staged_source": _file_record(consumed["staged_source"], "staged_source"),
        "stage_receipt": _file_record(consumed["stage_receipt"], "stage_receipt")
    }
    if mode == "zero_shot_asset_restyle":
        consumed_rec["graph"] = _file_record(consumed["graph"], "graph")
        if "grey_ref" in consumed and consumed["grey_ref"]:
            consumed_rec["grey_ref"] = _file_record(consumed["grey_ref"], "grey_ref")
    else:
        consumed_rec["graph"] = None

    dep = {
        "kind": COMPLETE_ASSET_KIND,
        "shot": sid,
        "fid": fid,
        "mode": mode,
        "source": _file_record(K.SRC, "source"),
        "model": _file_record(MODEL_PATH, "model"),
        "recipe": recipe,
        "consumed": consumed_rec
    }
    dep["deps_sha"] = hashlib.sha256(json.dumps(dep, sort_keys=True).encode()).hexdigest()
    ok, why = verify_complete_asset_deps(dep, sid, fid)
    if not ok:
        raise ValueError(f"complete asset dependency claim invalid: {why}")
    return dep


def _verify_asset_graph(path: Path, recipe: dict, staged_source: Path) -> None:
    from r6_key_recipe import _strict_json
    graph = _strict_json(path)
    inp = lambda node, field: graph[node]["inputs"][field]
    if (type(inp("NOISE", "noise_seed")) is not int or inp("NOISE", "noise_seed") != recipe["seed"] or
            type(inp("SIGMAS", "steps")) is not int or inp("SIGMAS", "steps") != recipe["steps"] or
            type(inp("GUIDER", "cfg")) not in (int, float) or
            not math.isfinite(inp("GUIDER", "cfg")) or
            inp("GUIDER", "cfg") != recipe["cfg"] or
            inp("UNET", "unet_name") != recipe["model_name"] or
            inp("CLIP", "clip_name") != recipe["clip_name"] or
            inp("VAE", "vae_name") != recipe["vae_name"]):
        raise ValueError("generated asset graph effective model/settings differ from recipe")
    key_img = inp("KEY_LOAD", "image")
    if type(key_img) is not str or Path(key_img).name != staged_source.name:
        raise ValueError("generated asset graph KEY_LOAD input differs from consumed staged source")
    if inp("PROMPT", "text") != recipe["prompt"]:
        raise ValueError("generated asset graph prompt differs from recipe")
    if (inp("GUIDER", "positive") != ["R2_POS", 0] or
            inp("GUIDER", "negative") != ["R2_NEG", 0]):
        raise ValueError("generated asset graph guider chain changed")


def verify_complete_asset_deps(dep: dict, sid: str | None = None,
                               fid: int | None = None) -> tuple[bool, str]:
    """Verify current asset recipe, complete selected inputs and actual generated graphs."""
    from r6_key_recipe import current_asset_recipe
    try:
        if type(dep) is not dict or set(dep) != {"kind", "shot", "fid", "mode", "source", "model",
                                                "recipe", "consumed", "deps_sha"}:
            raise ValueError("complete asset record fields malformed")
        if dep["kind"] != COMPLETE_ASSET_KIND or type(dep["shot"]) is not str or type(dep["fid"]) is not int:
            raise ValueError("complete asset record kind/identity malformed")
        if sid is not None and (type(sid) is not str or dep["shot"] != sid):
            raise ValueError("complete asset record shot differs from request")
        if fid is not None and (type(fid) is not int or dep["fid"] != fid):
            raise ValueError("complete asset record fid differs from request")
        mode = dep["mode"]
        if mode not in ("zero_shot_asset_restyle", "asset_black_passthrough"):
            raise ValueError(f"invalid asset mode: {mode}")
        if not _json_value(dep):
            raise ValueError("complete asset record contains deep, non-JSON or nonfinite values")
        seal = dep["deps_sha"]
        if type(seal) is not str or not re.fullmatch(r"[0-9a-fA-F]{64}", seal):
            raise ValueError("complete asset self-digest malformed")
        body = {k: v for k, v in dep.items() if k != "deps_sha"}
        if hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest() != seal.lower():
            raise ValueError("complete asset self-digest mismatch")

        recipe = current_asset_recipe(dep["shot"], dep["fid"], MODEL_PATH)
        if (type(dep["recipe"]) is not dict or
                json.dumps(dep["recipe"], sort_keys=True) != json.dumps(recipe, sort_keys=True)):
            raise ValueError("current asset recipe changed")

        _check_complete_file(dep["source"], "source", K.SRC)
        _check_complete_file(dep["model"], "model", MODEL_PATH)
        consumed = dep["consumed"]
        if type(consumed) is not dict or not ({"staged_source", "stage_receipt"} <= set(consumed)):
            raise ValueError("complete asset consumed collection malformed")
        work = K.R6 / "work" / dep["shot"]
        staged = _check_complete_file(consumed["staged_source"], "staged_source",
                                      work / f"f_{dep['fid']:04d}_src.png")
        receipt = _check_complete_file(consumed["stage_receipt"], "stage_receipt",
                                       staged.with_name(staged.name + ".stage.json"))
        stage = K._stage_record(receipt)
        if (stage is None or stage["contract"] != K._STAGE_CONTRACT or
                stage["source_path"] != str(Path(K.SRC).resolve(strict=True)) or
                stage["source_sha256"] != dep["source"]["sha256"] or
                stage["sid"] != dep["shot"] or stage["gframe"] != recipe["gframe"] or
                stage["output_path"] != str(staged) or
                stage["output_sha256"] != consumed["staged_source"]["sha256"] or
                stage["output_size"] != staged.stat().st_size):
            raise ValueError("staged source receipt differs from source/frame/output")

        from PIL import Image
        import numpy as np
        with Image.open(staged) as img:
            arr = np.asarray(img.convert("RGB"))
        std = float(arr.std())
        if mode == "asset_black_passthrough":
            if std >= 6.0:
                raise ValueError(f"black passthrough claimed on non-flat frame (std={std:.2f} >= 6.0)")
            if consumed.get("graph") is not None:
                raise ValueError("black passthrough must not claim generated graph")
        else:
            if std < 6.0:
                raise ValueError(f"restyle claimed on flat black frame (std={std:.2f} < 6.0)")
            if "graph" not in consumed or consumed["graph"] is None:
                raise ValueError("restyle mode missing graph")
            gp = _check_complete_file(consumed["graph"], "graph",
                                      K.R6 / "workflows" / f"r6_asset_{dep['shot']}_f{dep['fid']}.json")
            if "grey_ref" in consumed and consumed["grey_ref"]:
                _check_complete_file(consumed["grey_ref"], "grey_ref", K.INP / "_grey_64.png")
            _verify_asset_graph(gp, recipe, staged)
        return True, "ok"
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, IndexError,
            AttributeError, RecursionError, OverflowError) as exc:
        return False, f"complete asset deps invalid: {exc}"
'''

old2 = 'def verify_deps(dep: dict, sid: str | None = None, fid: int | None = None) -> tuple[bool, str]:\n'
new2 = funcs + '\n\n' + old2
assert content.count(old2) == 1, f"old2 count: {content.count(old2)}"
content = content.replace(old2, new2)

# 3. Update verify_deps to route COMPLETE_ASSET_KIND
old3 = '    if type(dep) is dict and dep.get("kind") == COMPLETE_KIND:\n        return verify_complete_deps(dep, sid, fid)\n'
new3 = '    if type(dep) is dict:\n        if dep.get("kind") == COMPLETE_KIND:\n            return verify_complete_deps(dep, sid, fid)\n        if dep.get("kind") == COMPLETE_ASSET_KIND:\n            return verify_complete_asset_deps(dep, sid, fid)\n'
assert content.count(old3) == 1, f"old3 count: {content.count(old3)}"
content = content.replace(old3, new3)

# 4. Update skip_allowed to permit COMPLETE_ASSET_KIND
old4 = '    if dep.get("kind") != COMPLETE_KIND:\n        # v3 remains available to historical recorded-file gates, but cannot\n'
new4 = '    if dep.get("kind") not in (COMPLETE_KIND, COMPLETE_ASSET_KIND):\n        # v3 remains available to historical recorded-file gates, but cannot\n'
assert content.count(old4) == 1, f"old4 count: {content.count(old4)}"
content = content.replace(old4, new4)

with open(cache_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)
print("Successfully patched r6_cache.py!")
