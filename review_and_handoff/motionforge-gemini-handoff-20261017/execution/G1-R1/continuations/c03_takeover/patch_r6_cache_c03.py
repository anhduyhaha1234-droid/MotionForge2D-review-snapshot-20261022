import os

cache_path = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_cache.py"
with open(cache_path, "r", encoding="utf-8") as f:
    src = f.read()

old_verify_block = '''def _verify_asset_graph(path: Path, recipe: dict, staged_source: Path) -> None:
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

new_verify_block = '''def _verify_asset_graph(path: Path, recipe: dict, staged_source: Path) -> None:
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
    if "KEY_LOAD" not in graph:
        raise ValueError("generated asset graph missing KEY_LOAD node")
    key_img = inp("KEY_LOAD", "image")
    if type(key_img) is not str or Path(key_img).name != staged_source.name or not key_img.startswith("identity5m_20261008/r6/work"):
        raise ValueError(f"generated asset graph KEY_LOAD input differs from consumed staged source: {key_img}")
    if inp("PROMPT", "text") != recipe["prompt"]:
        raise ValueError("generated asset graph prompt differs from recipe")
    if (inp("GUIDER", "positive") != ["R2_POS", 0] or
            inp("GUIDER", "negative") != ["R2_NEG", 0]):
        raise ValueError("generated asset graph guider chain changed")
    for r_node in ("R1_LOAD", "R2_LOAD", "R3_LOAD"):
        if r_node not in graph:
            raise ValueError(f"generated asset graph missing required node {r_node}")
        r_img = inp(r_node, "image")
        if not (isinstance(r_img, str) and r_img == "identity5m_20261008/r6/_grey_64.png"):
            raise ValueError(f"generated asset graph {r_node} does not reference canonical grey ref 'identity5m_20261008/r6/_grey_64.png': {r_img}")'''

assert src.count(old_verify_block) == 1, "old_verify_block not found"
src = src.replace(old_verify_block, new_verify_block)

with open(cache_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)
print("Updated r6_cache.py with strict grey reference & node verification successfully")
