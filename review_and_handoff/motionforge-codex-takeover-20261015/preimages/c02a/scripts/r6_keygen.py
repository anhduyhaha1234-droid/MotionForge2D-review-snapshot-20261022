"""R6 keygen — per-actor klein edit through UPSTREAM crop+stitch, class-driven masks, gates.

Flow per key:
  stage canonical frame -> per actor (class VISIBLE/PARTIALLY_VISIBLE at fid):
    mask from R6/masks/<sid>/<entity>/ (missing/empty in visible window -> FAIL)
    upstream crop -> klein edit -> UPSTREAM stitch (same transform) -> bound_check
  save key + deps (r6_cache) + receipt. Skip ONLY via verified-reuse (deps+review).
usage: python -B r6_keygen.py S0023 --key 1
"""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "env/pylibs"))
import r6_common as K  # noqa: E402
import r6_adapter as A  # noqa: E402
import r6_graph as G  # noqa: E402
import r6_cache as CA  # noqa: E402

REC = K.R6 / "receipts/R6_KEYGEN_RUNS.jsonl"


def ledger_row(sid):
    for line in (K.R6 / "source_actor_ledger.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["shot"] == sid:
            return r
    raise KeyError(sid)


def class_at(row, entity, fid):
    for a in row["actors"]:
        if a["entity"] == entity:
            for w in a["class_windows"]:
                if w["from"] <= fid <= w["to"]:
                    return w["class"]
    return None


def run_key(sid, fid):
    row = ledger_row(sid)
    if row["zero_explicit"]:
        raise SystemExit(f"{sid}: ZERO_EXPLICIT shot — asset-pass path (S7), not keygen")
    n = row["n"]
    if fid > n:
        raise SystemExit(f"{sid}: fid {fid} > n {n}")
    keydir = K.R6 / "keys" / sid
    keydir.mkdir(parents=True, exist_ok=True)
    keypng = keydir / f"f_{fid:04d}_key.png"
    ok, why = CA.skip_allowed(sid, fid, keypng)
    if ok:
        print(json.dumps({"shot": sid, "fid": fid, "skipped": why}))
        return
    gframe = K.gframe_of(sid, fid)
    work = K.R6 / "work" / sid
    work.mkdir(parents=True, exist_ok=True)
    src = K.stage_frame(sid, gframe, work / f"f_{fid:04d}_src.png")
    frame_t = A.load_img(src)
    t0 = time.time()
    per_actor, used_casts, used_masks = [], [], []
    target_entities = [a["entity"] for a in row["actors"]
                       if class_at(row, a["entity"], fid) in ("VISIBLE", "PARTIALLY_VISIBLE")]
    import os as _os2
    _only = _os2.environ.get("R6_ONLY_ENTITY")
    if _only:
        target_entities = [e for e in target_entities if e == _only]
    if not target_entities:
        # frame with no visible actors (e.g., between entries): keep source as key, explicit
        from PIL import Image
        Image.open(src).convert("RGB").save(keypng)
        deps = CA.build_deps(sid, fid, {"source_span_lo": row["src"][0], "source_span_hi": row["src"][1],
                                        "gframe": gframe, "casts": [], "masks": [], "graph": None},
                             {"mode": "keep_source_no_visible_actor"})
        (work / f"f_{fid:04d}.deps.json").write_text(json.dumps(deps, ensure_ascii=False, indent=1), encoding="utf-8")
        rec = {"shot": sid, "fid": fid, "mode": "keep_source_no_visible_actor", "key": str(keypng),
               "key_sha256": K.sha(keypng), "wall_s": round(time.time() - t0, 1)}
        with open(REC, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(json.dumps(rec))
        return
    for entity in target_entities:
        cls = class_at(row, entity, fid)
        mp = K.R6 / "masks" / sid / entity / f"f_{fid:04d}.png"
        if not mp.exists() or mp.stat().st_size == 0:
            raise SystemExit(f"REJECT: mask missing {sid}/{entity}/f_{fid:04d} (class {cls})")
        mask_t = A.load_mask(mp)
        if float(mask_t.sum()) < 4:
            raise SystemExit(f"REJECT: mask empty while {cls} {sid}/{entity}/f_{fid:04d}")
        # z-order: a later (further-back) actor must not re-edit pixels already claimed by
        # an earlier-processed (front) actor on this frame — subtract prior masks.
        import numpy as _np
        if used_masks:
            m = mask_t[0].numpy() > 0.5
            for pm in used_masks:
                pmk = A.load_mask(pm)[0].numpy() > 0.5
                if pmk.shape == m.shape:
                    m = m & ~pmk
            mask_t = __import__("torch").from_numpy(m.astype(_np.float32))[None, ...]
            if float(mask_t.sum()) < 4:
                per_actor.append({"entity": entity, "class": cls, "skipped": "fully-covered-by-front-actor-on-this-frame"})
                continue
        import os as _os
        _ctx = float(_os.environ.get('R6_CTX_FACTOR', '1.02'))
        res, region = A.crop_for_mask(frame_t, mask_t, context_factor=_ctx)
        crop_im = res[5]
        crop_png = work / f"f_{fid:04d}_{entity}_crop.png"
        A.save_img(crop_im, crop_png)
        seed = 2026101400 + int(sid[1:]) * 1000 + fid + int(_os.environ.get('R6_SEED_OFF', '0'))
        g, refmap = G.build_actor_crop_graph(sid, entity, crop_png, seed, (crop_im.shape[2], crop_im.shape[1]))
        gp = K.R6 / "workflows"
        gp.mkdir(exist_ok=True)
        (gp / f"r6_crop_{sid}_f{fid}_{entity}.json").write_text(json.dumps(g, indent=1), encoding="utf-8")
        r = K.post(g)
        hist = K.wait(r["prompt_id"], timeout=900)
        outs = K.collect_outputs(hist)
        if not outs:
            raise SystemExit(f"NO OUTPUT {sid} f{fid} {entity}")
        ed = outs[-1]
        ed_t = A.load_img(ed)
        if ed_t.shape[1:3] != crop_im.shape[1:3]:
            raise SystemExit(f"CROP SIZE MISMATCH {tuple(ed_t.shape[1:3])} vs {tuple(crop_im.shape[1:3])}")
        if float(ed_t.std()) < 0.01:
            raise SystemExit(f"BLANK EDIT {sid} f{fid} {entity}")
        before = frame_t
        stitched = A.stitch_back(res, ed_t)  # UPSTREAM stitch, same transform
        bc = A.bound_check(before, stitched, mask_t)
        if not bc["ok"]:
            if bc["frac_core8"] < 8e-3 and bc["frac_outside"] < 5e-3:
                bc["soft_flag"] = "resampler-band outlier; key kept, review must judge"
            else:
                raise SystemExit(f"STITCH BOUND VIOLATION {sid} f{fid} {entity}: {bc}")
        frame_t = stitched
        per_actor.append({"entity": entity, "class": cls, "refmap": refmap,
                          "region": {k: region[k] for k in ("x", "y", "w", "h", "mask_px", "target")},
                          "bound": bc, "prompt_id": r["prompt_id"], "crop": str(crop_png)})
        used_casts += [K.INP / "keys/cast_refs" / refmap[1]["file"], K.INP / "keys/cast_refs" / refmap[2]["file"]]
        used_masks.append(mp)
    A.save_img(frame_t, keypng)
    deps = CA.build_deps(sid, fid, {"source_span_lo": row["src"][0], "source_span_hi": row["src"][1],
                                    "gframe": gframe, "casts": used_casts, "masks": used_masks,
                                    "graph": gp / f"r6_crop_{sid}_f{fid}_{target_entities[0]}.json"},
                         {"model": "flux-2-klein-4b-fp8", "steps": 4, "sampler": "euler", "cfg": 1.0,
                          "seed": 2026101400 + int(sid[1:]) * 1000 + fid})
    (work / f"f_{fid:04d}.deps.json").write_text(json.dumps(deps, ensure_ascii=False, indent=1), encoding="utf-8")
    rec = {"shot": sid, "fid": fid, "key": str(keypng), "key_sha256": K.sha(keypng),
           "wall_s": round(time.time() - t0, 1), "actors": per_actor, "deps_sha": deps["deps_sha"],
           "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with open(REC, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps({"shot": sid, "fid": fid, "wall": rec["wall_s"], "sha16": K.sha16(keypng),
                      "actors": [a["entity"] for a in per_actor]}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shot")
    ap.add_argument("--key", type=int, default=None)
    ap.add_argument("--itv", type=int, default=10)
    ns = ap.parse_args()
    sb = json.loads((K.R6 / "storyboard" / f"{ns.shot}.json").read_text(encoding="utf-8"))
    fids = [ns.key] if ns.key else [k["fid"] for k in sb["keys"] if k["fid"] <= sb["n"]]
    for fid in fids:
        run_key(ns.shot, fid)


if __name__ == "__main__":
    main()
