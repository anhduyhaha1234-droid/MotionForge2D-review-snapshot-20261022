import os

asset_keygen_path = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_keygen_asset.py"
with open(asset_keygen_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add import r6_key_recipe as KR
old_import = "import r6_cache as CA  # noqa: E402\n"
new_import = "import r6_cache as CA  # noqa: E402\nimport r6_key_recipe as KR  # noqa: E402\n"
assert content.count(old_import) == 1
content = content.replace(old_import, new_import)

# 2. Update run_key implementation
old_run_key = '''def run_key(sid, fid):
    sd = json.loads((K.R6 / "storyboard" / f"{sid}.json").read_text(encoding="utf-8"))
    if not sd.get("zero_explicit"):
        raise SystemExit(f"{sid} is not zero_explicit")
    n = sd["n"]
    if fid > n:
        raise SystemExit(f"fid {fid} > n {n}")
    keydir = K.R6 / "keys" / sid
    keydir.mkdir(parents=True, exist_ok=True)
    keypng = keydir / f"f_{fid:04d}_key.png"
    work = K.R6 / "work" / sid
    work.mkdir(parents=True, exist_ok=True)
    src = K.stage_frame(sid, K.gframe_of(sid, fid), work / f"f_{fid:04d}_src.png")
    t0 = time.time()
    import numpy as _np
    from PIL import Image as _I
    _a = _np.asarray(_I.open(src).convert("RGB"))
    if float(_a.std()) < 6.0:  # black/flat source (e.g. S0032 intro) -> explicit passthrough
        _I.fromarray(_a).save(keypng)
        rec = {"shot": sid, "fid": fid, "mode": "asset_black_passthrough", "key": str(keypng),
               "key_sha256": K.sha(keypng), "wall_s": round(time.time() - t0, 2),
               "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        with open(REC, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + chr(10))
        print(json.dumps({"shot": sid, "fid": fid, "mode": "black_pass", "sha16": K.sha16(keypng)}))
        return
    seed = 2026101500 + int(sid[1:]) * 1000 + fid
    g = whole_graph(sid, src, seed)
    gp = K.R6 / "workflows"
    (gp / f"r6_asset_{sid}_f{fid}.json").write_text(json.dumps(g, indent=1), encoding="utf-8")
    r = K.post(g)
    hist = K.wait(r["prompt_id"], timeout=900)
    outs = K.collect_outputs(hist)
    if not outs:
        raise SystemExit(f"NO OUTPUT {sid} f{fid}")
    from PIL import Image
    im = Image.open(outs[-1]).convert("RGB")
    if im.size != (640, 360):
        im = im.resize((640, 360))
    im.save(keypng)
    deps = CA.build_deps(sid, fid, {"source_span_lo": K.PLAN[sid]["start_frame"],
                                    "source_span_hi": K.PLAN[sid]["start_frame"] + n,
                                    "gframe": K.gframe_of(sid, fid), "casts": [], "masks": [],
                                    "graph": gp / f"r6_asset_{sid}_f{fid}.json"},
                         {"mode": "zero_shot_asset_restyle", "steps": 4})
    (work / f"f_{fid:04d}.deps.json").write_text(json.dumps(deps, ensure_ascii=False, indent=1), encoding="utf-8")
    rec = {"shot": sid, "fid": fid, "mode": "asset", "key": str(keypng), "key_sha256": K.sha(keypng),
           "wall_s": round(time.time() - t0, 1), "prompt_id": r["prompt_id"],
           "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with open(REC, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + chr(10))
    print(json.dumps({"shot": sid, "fid": fid, "wall": rec["wall_s"], "sha16": K.sha16(keypng)}))'''

new_run_key = '''def run_key(sid, fid):
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
    print(json.dumps({"shot": sid, "fid": fid, "wall": rec["wall_s"], "sha16": K.sha16(keypng)}))'''

assert content.count(old_run_key) == 1
content = content.replace(old_run_key, new_run_key)

with open(asset_keygen_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)
print("Successfully patched r6_keygen_asset.py!")
