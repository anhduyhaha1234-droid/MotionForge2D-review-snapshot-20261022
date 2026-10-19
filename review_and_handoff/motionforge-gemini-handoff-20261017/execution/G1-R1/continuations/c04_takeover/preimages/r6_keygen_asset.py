"""R6 zero-shot ASSET keygen — whole-frame klein restyle for document/prop/background shots.

No actors by ledger (ZERO_VISIBLE): single whole-frame pass with style text; prompt demands the
document text/layout be preserved (checked text kept; review decides). No masks needed.
usage: python -B r6_keygen_asset.py S0032 [S0035 ...]   (or --key fid)
"""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r6_common as K  # noqa: E402
import r6_cache as CA  # noqa: E402
import r6_key_recipe as KR  # noqa: E402

REC = K.R6 / "receipts/R6_ASSET_RUNS.jsonl"


def whole_graph(sid, frame_png, seed):
    """whole-frame klein restyle; returns (graph, upload_ref)."""
    import r6_graph as G

    ref = K.upload_image_helper = None
    up = __import__("r6_upload")
    key_ref = up.upload_image(frame_png, "identity5m_20261008/r6/work")
    g = json.loads(G.TPL.read_text(encoding="utf-8"))
    g["KEY_LOAD"]["inputs"]["image"] = key_ref
    # reuse CAST slot? No cast for docs: point R1/R2 to the SAME frame (style-only edit) but that would
    # violate the no-multi-ref rule; instead neutral grey refs (kept out of prompt scope).
    from PIL import Image
    grey = K.INP / "_grey_64.png"
    if not grey.exists():
        Image.new("RGB", (64, 64), (127, 127, 127)).save(grey)
    r1 = up.upload_image(grey, "identity5m_20261008/r6")
    g["R1_LOAD"]["inputs"]["image"] = r1
    g["R2_LOAD"]["inputs"]["image"] = r1
    g["R3_LOAD"]["inputs"]["image"] = r1
    g["PROMPT"]["inputs"]["text"] = (
        "Restyle this frame into flat 2D cel-shaded animation style: solid flat colour fills, thin clean "
        "outlines, no gradients, no photographic texture, no 3D rendering. CRITICAL: keep the EXACT same "
        "composition, the EXACT same layout, and every piece of text, number, logo and document shape "
        "IDENTICAL and fully legible - do not redraw, move, add, remove or invent any glyph or object. "
        "The result must read as the same document/image, only in flat vector style.")
    g["NOISE"]["inputs"]["noise_seed"] = seed
    w, h = Image.open(frame_png).size
    g["LATENT"]["inputs"]["width"] = w
    g["LATENT"]["inputs"]["height"] = h
    g["SIGMAS"]["inputs"]["width"] = w
    g["SIGMAS"]["inputs"]["height"] = h
    g["GUIDER"]["inputs"]["positive"] = ["R2_POS", 0]
    g["GUIDER"]["inputs"]["negative"] = ["R2_NEG", 0]
    g["SAVE"]["inputs"]["filename_prefix"] = f"identity5m_20261008/r6/r6_keys/{sid}_asset"
    return g


def run_key(sid, fid):
    sd = json.loads((K.R6 / "storyboard" / f"{sid}.json").read_text(encoding="utf-8"))
    if not sd.get("zero_explicit"):
        raise SystemExit(f"{sid} is not zero_explicit")
    n = sd["n"]
    if fid > n:
        raise SystemExit(f"fid {fid} > n {n}")
    keydir = K.R6 / "keys" / sid
    keydir.mkdir(parents=True, exist_ok=True)
    keypng = keydir / f"f_{fid:04d}_key.png"
    ok, why = CA.skip_allowed(sid, fid, keypng)
    if ok:
        print(json.dumps({"shot": sid, "fid": fid, "skipped": why}))
        return
    recipe = KR.current_asset_recipe(sid, fid, CA.MODEL_PATH)
    work = K.R6 / "work" / sid
    work.mkdir(parents=True, exist_ok=True)
    src = K.stage_frame(sid, K.gframe_of(sid, fid), work / f"f_{fid:04d}_src.png")
    t0 = time.time()
    import numpy as _np
    from PIL import Image as _I
    _a = _np.asarray(_I.open(src).convert("RGB"))
    if float(_a.std()) < 6.0:  # black/flat source (e.g. S0032 intro) -> explicit passthrough
        _I.fromarray(_a).save(keypng)
        deps = CA.build_complete_asset_deps(
            sid, fid, recipe,
            {"staged_source": src, "stage_receipt": src.with_name(src.name + ".stage.json")},
            mode="asset_black_passthrough"
        )
        (work / f"f_{fid:04d}.deps.json").write_text(json.dumps(deps, ensure_ascii=False, indent=1), encoding="utf-8")
        rec = {"shot": sid, "fid": fid, "mode": "asset_black_passthrough", "key": str(keypng),
               "key_sha256": K.sha(keypng), "wall_s": round(time.time() - t0, 2),
               "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        with open(REC, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + chr(10))
        print(json.dumps({"shot": sid, "fid": fid, "mode": "black_pass", "sha16": K.sha16(keypng)}))
        return
    seed = recipe["seed"]
    g = whole_graph(sid, src, seed)
    gp = K.R6 / "workflows"
    gp.mkdir(parents=True, exist_ok=True)
    graph_path = gp / f"r6_asset_{sid}_f{fid}.json"
    graph_path.write_text(json.dumps(g, indent=1), encoding="utf-8")
    grey_file = K.INP / "_grey_64.png"
    CA._verify_asset_graph(graph_path, recipe, src)
    r = K.post(g)
    hist = K.wait(r["prompt_id"], timeout=900)
    outs = K.collect_outputs(hist)
    if not outs:
        raise SystemExit(f"NO OUTPUT {sid} f{fid}")
    from PIL import Image
    im = Image.open(outs[-1]).convert("RGB")
    if im.size != (640, 360):
        im = im.resize((640, 360))
    if float(_np.asarray(im).std()) < 0.01:
        raise SystemExit(f"BLANK EDIT {sid} f{fid}")
    im.save(keypng)
    deps = CA.build_complete_asset_deps(
        sid, fid, recipe,
        {"staged_source": src, "stage_receipt": src.with_name(src.name + ".stage.json"),
         "graph": graph_path, "grey_ref": grey_file},
        mode="zero_shot_asset_restyle"
    )
    (work / f"f_{fid:04d}.deps.json").write_text(json.dumps(deps, ensure_ascii=False, indent=1), encoding="utf-8")
    rec = {"shot": sid, "fid": fid, "mode": "asset", "key": str(keypng), "key_sha256": K.sha(keypng),
           "wall_s": round(time.time() - t0, 1), "prompt_id": r["prompt_id"],
           "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with open(REC, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + chr(10))
    print(json.dumps({"shot": sid, "fid": fid, "wall": rec["wall_s"], "sha16": K.sha16(keypng)}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shots", nargs="+")
    ap.add_argument("--key", type=int, default=None)
    args = ap.parse_args()
    for sid in args.shots:
        sd = json.loads((K.R6 / "storyboard" / f"{sid}.json").read_text(encoding="utf-8"))
        fids = [args.key] if args.key else [k["fid"] for k in sd["keys"] if k["fid"] <= sd["n"]]
        for fid in fids:
            run_key(sid, fid)


if __name__ == "__main__":
    main()
