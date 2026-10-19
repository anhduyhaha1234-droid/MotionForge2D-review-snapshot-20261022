import os

recipe_path = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_key_recipe.py"
with open(recipe_path, "r", encoding="utf-8") as f:
    content = f.read()

asset_recipe_code = '''

def current_asset_recipe(sid: str, fid: int, model_path: Path) -> dict:
    """Resolve effective settings for zero-shot asset keys without staging or ComfyUI calls."""
    import r6_graph as G

    if type(sid) is not str or not re.fullmatch(r"S[0-9]{4}", sid):
        raise ValueError("invalid shot")
    if type(fid) is not int or fid < 1:
        raise ValueError("invalid fid")
    plan = K.PLAN.get(sid)
    if type(plan) is not dict or type(plan.get("start_frame")) is not int or type(plan.get("frames")) is not int:
        raise ValueError("shot absent from plan")
    if fid > plan["frames"]:
        raise ValueError("fid outside shot plan")
    row = None
    for line in (K.R6 / "source_actor_ledger.jsonl").read_text(encoding="utf-8").splitlines():
        candidate = json.loads(line)
        if candidate.get("shot") == sid:
            row = candidate
            break
    if type(row) is not dict or row.get("zero_explicit") is not True:
        raise ValueError("asset ledger row absent or not ZERO_EXPLICIT")
    if (type(row.get("n")) is not int or row["n"] != plan["frames"] or
            row.get("src") != [plan["start_frame"], plan["start_frame"] + plan["frames"]]):
        raise ValueError("ledger row disagrees with current plan")
    board = _strict_json(K.R6 / "storyboard" / f"{sid}.json")
    if type(board) is not dict or board.get("zero_explicit") is not True:
        raise ValueError("asset storyboard absent or not ZERO_EXPLICIT")
    if "n" in board and (type(board["n"]) is not int or board["n"] != row["n"]):
        raise ValueError("storyboard span disagrees with ledger")

    try:
        off = int(os.environ.get("R6_SEED_OFF", "0"))
    except (ValueError, OverflowError) as exc:
        raise ValueError("invalid seed offset") from exc
    seed = 2026101500 + int(sid[1:]) * 1000 + fid + off
    if seed < 0 or seed > (1 << 64) - 1:
        raise ValueError("effective seed outside uint64")

    graph = _strict_json(G.TPL)
    try:
        steps = _node_input(graph, "SIGMAS", "steps", int)
        sampler = _node_input(graph, "SAMPLER", "sampler_name", str)
        cfg = graph["GUIDER"]["inputs"]["cfg"]
        unet = _node_input(graph, "UNET", "unet_name", str)
        clip = _node_input(graph, "CLIP", "clip_name", str)
        vae = _node_input(graph, "VAE", "vae_name", str)
    except (KeyError, TypeError) as exc:
        raise ValueError(f"incomplete graph template: {exc}") from exc
    if (steps < 1 or type(cfg) not in (int, float) or not math.isfinite(cfg) or cfg <= 0 or
            unet != Path(model_path).name):
        raise ValueError("invalid effective template steps/CFG/model")

    code = {name: K.sha(Path(__file__).parent / name) for name in
            ("r6_key_recipe.py", "r6_keygen_asset.py", "r6_graph.py", "r6_upload.py", "r6_common.py")}

    prompt_text = (
        "Restyle this frame into flat 2D cel-shaded animation style: solid flat colour fills, thin clean "
        "outlines, no gradients, no photographic texture, no 3D rendering. CRITICAL: keep the EXACT same "
        "composition, the EXACT same layout, and every piece of text, number, logo and document shape "
        "IDENTICAL and fully legible - do not redraw, move, add, remove or invent any glyph or object. "
        "The result must read as the same document/image, only in flat vector style."
    )

    return {
        "mode": "zero_shot_asset_restyle",
        "shot": sid,
        "fid": fid,
        "gframe": plan["start_frame"] + fid - 1,
        "span": [plan["start_frame"], plan["start_frame"] + plan["frames"]],
        "ledger_row_sha": _digest(row),
        "storyboard_sha": _digest(board),
        "seed_off": off,
        "seed": seed,
        "steps": steps,
        "sampler": sampler,
        "cfg": float(cfg),
        "model_name": unet,
        "clip_name": clip,
        "vae_name": vae,
        "template": {"path": str(G.TPL.resolve(strict=True)), "sha256": K.sha(G.TPL)},
        "code_sha256": code,
        "prompt": prompt_text
    }
'''

if "def current_asset_recipe" not in content:
    content = content.rstrip() + asset_recipe_code + "\n"
    with open(recipe_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Appended current_asset_recipe to r6_key_recipe.py")
else:
    print("current_asset_recipe already in r6_key_recipe.py")
