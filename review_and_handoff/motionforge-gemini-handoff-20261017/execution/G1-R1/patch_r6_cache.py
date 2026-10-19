import os

cache_path = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_cache.py"
with open(cache_path, "r", encoding="utf-8") as f:
    src = f.read()

# 1. Update build_complete_asset_deps to require grey_ref in zero_shot_asset_restyle
old_build_block = '''    if mode == "zero_shot_asset_restyle":
        consumed_rec["graph"] = _file_record(consumed["graph"], "graph")
        if "grey_ref" in consumed and consumed["grey_ref"]:
            consumed_rec["grey_ref"] = _file_record(consumed["grey_ref"], "grey_ref")
    else:
        consumed_rec["graph"] = None'''

new_build_block = '''    if mode == "zero_shot_asset_restyle":
        consumed_rec["graph"] = _file_record(consumed["graph"], "graph")
        if "grey_ref" not in consumed or not consumed["grey_ref"]:
            raise ValueError("restyle mode requires grey_ref in consumed")
        consumed_rec["grey_ref"] = _file_record(consumed["grey_ref"], "grey_ref")
    else:
        consumed_rec["graph"] = None'''

assert src.count(old_build_block) == 1, "build_complete_asset_deps block not found"
src = src.replace(old_build_block, new_build_block)

# 2. Update _verify_asset_graph to strictly verify SAMPLER and grey references
old_verify_graph = '''def _verify_asset_graph(path: Path, recipe: dict, staged_source: Path) -> None:
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
        raise ValueError("generated asset graph guider chain changed")'''

new_verify_graph = '''def _verify_asset_graph(path: Path, recipe: dict, staged_source: Path) -> None:
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
    if "SAMPLER" not in graph:
        raise ValueError("generated asset graph missing SAMPLER node")
    sampler_name = inp("SAMPLER", "sampler_name")
    if sampler_name != recipe.get("sampler", "euler"):
        raise ValueError(f"generated asset graph sampler '{sampler_name}' differs from recipe '{recipe.get('sampler', 'euler')}'")
    key_img = inp("KEY_LOAD", "image")
    if type(key_img) is not str or Path(key_img).name != staged_source.name:
        raise ValueError("generated asset graph KEY_LOAD input differs from consumed staged source")
    if inp("PROMPT", "text") != recipe["prompt"]:
        raise ValueError("generated asset graph prompt differs from recipe")
    if (inp("GUIDER", "positive") != ["R2_POS", 0] or
            inp("GUIDER", "negative") != ["R2_NEG", 0]):
        raise ValueError("generated asset graph guider chain changed")
    for r_node in ("R1_LOAD", "R2_LOAD", "R3_LOAD"):
        if r_node in graph:
            r_img = inp(r_node, "image")
            if not (isinstance(r_img, str) and ("_grey_64" in r_img or "grey" in Path(r_img).name.lower())):
                raise ValueError(f"generated asset graph {r_node} does not reference grey ref: {r_img}")'''

assert src.count(old_verify_graph) == 1, "_verify_asset_graph block not found"
src = src.replace(old_verify_graph, new_verify_graph)

# 3. Update verify_complete_asset_deps to strictly require grey_ref in consumed
old_check_grey = '''            if "grey_ref" in consumed and consumed["grey_ref"]:
                _check_complete_file(consumed["grey_ref"], "grey_ref", K.INP / "_grey_64.png")
            _verify_asset_graph(gp, recipe, staged)'''

new_check_grey = '''            if "grey_ref" not in consumed or consumed["grey_ref"] is None or not consumed["grey_ref"]:
                raise ValueError("restyle mode missing consumed grey_ref")
            _check_complete_file(consumed["grey_ref"], "grey_ref", K.INP / "_grey_64.png")
            _verify_asset_graph(gp, recipe, staged)'''

assert src.count(old_check_grey) == 1, "check_grey block not found"
src = src.replace(old_check_grey, new_check_grey)

with open(cache_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)
print("Updated r6_cache.py with strict asset provenance & sampler checks successfully")
