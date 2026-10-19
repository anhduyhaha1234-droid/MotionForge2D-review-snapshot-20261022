"""R6 CoTracker — raw tracks for events on PROPAGATED outputs vs SOURCE (paired S34/S61/S73).

Outputs per shot: tracks (T,N,2) float32, visibility (T,N) bool, queries (N,2),
event windows (before/contact/hold/release) + drift metrics vs source-tracked same points.
usage: python -B r6_cotracker.py S0034 S0061 S0073
"""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r6_common as K  # noqa: E402
import numpy as np
from PIL import Image

VEND = K.R4 / "vendor/co-tracker"
OUTD = K.R6 / "evidence/cotracker"
OUTD.mkdir(parents=True, exist_ok=True)
REC = K.R6 / "receipts/R6_COTRACKER_RUNS.jsonl"


def ckpt():
    cands = sorted(K.R5.glob("models/co-tracker/scaled_offline.pth")) + sorted(K.R4.glob("vendor/**/scaled_offline.pth"))
    assert cands, "scaled_offline.pth missing"
    return cands[0]


def load_frames(sid, kind):
    if kind == "blend":
        bd = K.R6 / "work" / sid / "blend"
        man_p = K.R6 / "work" / sid / "blend_manifest.json"
        if man_p.exists():
            m = json.loads(man_p.read_text(encoding="utf-8"))
            if m.get("blend_dir"):
                bd = Path(m["blend_dir"])
        fs = sorted(bd.glob("*.jpg"))
        frames = []
        for f in fs:
            im = Image.open(f).convert("RGB")
            if im.size == (640, 368):
                im = im.crop((0, 4, 640, 364))
            frames.append(np.asarray(im))
        return np.stack(frames)
    # source window (canonical 360)
    n = K.PLAN[sid]["frames"]
    a0 = K.PLAN[sid]["start_frame"]
    import subprocess
    td = K.TMPD / f"ct_{sid}"
    td.mkdir(parents=True, exist_ok=True)
    K.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a0/30:.6f}", "-i", str(K.SRC),
           "-frames:v", str(n), "-start_number", "1", str(td / "%04d.png")])
    frames = [np.asarray(Image.open(p).convert("RGB")) for p in sorted(td.glob("*.png"))]
    return np.stack(frames)


def run(sid, device="cuda"):
    import torch
    dev = torch.device(device if torch.cuda.is_available() else "cpu")
    pathV = str(VEND)
    if pathV not in sys.path:
        sys.path.insert(0, pathV)
    from cotracker.predictor import CoTrackerPredictor
    model = CoTrackerPredictor(checkpoint=str(ckpt()), v2=False, offline=True)
    model = model.to(dev)
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    src = load_frames(sid, "src")
    gen = load_frames(sid, "blend")
    # F04: reject silent length mismatch (no min()).
    if len(src) != len(gen):
        raise SystemExit(f"COTRACKER_LENGTH_MISMATCH {sid}: source {len(src)} vs r6 {len(gen)}")
    T = len(src)
    ev_all = json.loads((K.R6 / "event_map.json").read_text(encoding="utf-8"))
    shot_ev = (ev_all.get("shots") or {}).get(sid) or {}
    events = shot_ev.get("events") or []
    contacts = shot_ev.get("contacts") or []
    # semantic hand/prop queries per clip (canonical 640x360; explicit, not a frame0 grid)
    SEMANTIC_Q = {
        "S0034": {"pts": [[440, 190], [400, 175], [500, 205], [305, 140], [330, 160]],  # phone on chest + hand
                  "label": "E8 hand/phone + bed grab zone"},
        "S0061": {"pts": [[300, 200], [330, 208], [360, 220], [420, 210], [520, 240], [100, 250]],  # 2 people + car
                  "label": "E1/E2 walking + car region"},
        "S0073": {"pts": [[320, 175], [300, 185], [355, 190], [360, 210], [250, 200]],  # book/hand at counter
                  "label": "book/hand pick-hold-release region"},
    }
    sq = SEMANTIC_Q.get(sid)
    if sq is None:
        raise SystemExit(f"COTRACKER_NO_SEMANTIC_QUERIES {sid}")
    qs = []
    for t in range(T):
        for (x, y) in sq["pts"]:
            qs.append([t, x, y])
    qarr = np.array(qs, dtype=np.float32)
    out = {}
    for kind, arr in (("source", src), ("r6", gen)):
        vid = torch.from_numpy(arr).permute(0, 3, 1, 2)[None].float().to(dev)
        q = torch.from_numpy(qarr)[None].to(dev)
        t0 = time.time()
        tr, vis = model(vid, queries=q)
        tr = tr[0].detach().cpu().numpy(); vis = vis[0].detach().cpu().numpy()
        wall = round(time.time() - t0, 1)
        np.save(OUTD / f"{sid}_{kind}_tracks.npy", tr)
        np.save(OUTD / f"{sid}_{kind}_vis.npy", vis)
        out[kind] = {"wall_s": wall, "T": int(tr.shape[0]), "N": int(tr.shape[1])}
    # drift between tracks where both visible
    tr_s = np.load(OUTD / f"{sid}_source_tracks.npy")
    tr_g = np.load(OUTD / f"{sid}_r6_tracks.npy")
    if tr_s.shape != tr_g.shape:
        raise SystemExit(f"COTRACKER_SHAPE_MISMATCH {sid}: {tr_s.shape} vs {tr_g.shape}")
    d = np.linalg.norm(tr_g - tr_s, axis=-1)  # (T,N)
    both = np.logical_and(np.load(OUTD / f"{sid}_source_vis.npy") > 0,
                          np.load(OUTD / f"{sid}_r6_vis.npy") > 0)  # (T,N)
    dm = float(d[both].mean()) if both.any() else None
    # F04 windows: from events (f) and contacts (from, 0-based -> fid from+1); non-empty required.
    windows = []
    for e in events:
        f0 = int(e.get("f", 1)) + 1  # event f is 0-based in the map; fid = f+1
        f1 = min(T, f0 + 12)
        windows.append({"kind": "event", "event": e.get("event", "?"), "fid": f0,
                        "before": [max(1, f0 - 5), f0],
                        "contact": [f0, min(T, f0 + 3)],
                        "hold": [min(T, f0 + 3), f1],
                        "release": [min(T, f1), min(T, f1 + 5)],
                        "drift_contact_mean": float(np.nanmean(d[max(0, f0 - 1):min(T, f0 + 3)][both[max(0, f0 - 1):min(T, f0 + 3)]])) if both.any() else None})
    for c in contacts:
        f0 = int(c.get("from", 0)) + 1  # 0-based -> fid
        f1 = min(T, f0 + 12)
        windows.append({"kind": "contact", "entity": c.get("entity"), "prop": c.get("prop"),
                        "part": c.get("part"), "fid": f0,
                        "before": [max(1, f0 - 5), f0],
                        "contact": [f0, min(T, f0 + 3)],
                        "hold": [min(T, f0 + 3), f1],
                        "release": [min(T, f1), min(T, f1 + 5)],
                        "drift_contact_mean": float(np.nanmean(d[max(0, f0 - 1):min(T, f0 + 3)][both[max(0, f0 - 1):min(T, f0 + 3)]])) if both.any() else None})
    if not windows:
        raise SystemExit(f"COTRACKER_NO_WINDOWS {sid}: neither events nor contacts in event map")
    # evidence frames: before/contact/hold/release of the first window (source|r6 side by side)
    from PIL import Image as _I, ImageDraw as _D, ImageFont as _F
    try:
        font = _F.truetype("C:/Windows/Fonts/arialbd.ttf", 12)
    except Exception:
        font = _F.load_default()
    w0 = windows[0]
    ev_dir = K.R6 / "continuations/LONG01-R6g-20261014T0725Z-1572/evidence/cotracker"
    ev_dir.mkdir(parents=True, exist_ok=True)
    tiles = []
    for tag in ("before", "contact", "hold", "release"):
        f0, f1 = w0[tag]
        fmid = min(T, max(1, (f0 + f1) // 2))
        a = src[max(0, fmid - 1)]; b = gen[max(0, fmid - 1)]
        tiles.append((f"{tag} f{fmid}", a, b))
    c = _I.new("RGB", (4 * (320 + 6) + 8, 2 * (180 + 22) + 8), (10, 10, 10))
    dr = _D.Draw(c)
    for j, (tag, a, b) in enumerate(tiles):
        x = 4 + j * (320 + 6)
        dr.text((x, 4), f"{sid} {tag}", fill=(255, 220, 80), font=font)
        c.paste(_I.fromarray(a).resize((320, 180)), (x, 20))
        c.paste(_I.fromarray(b).resize((320, 180)), (x, 20 + 190)) if False else None
    c.save(ev_dir / f"{sid}_windows_strip.png")
    vram = round(torch.cuda.max_memory_allocated() / 2**20) if torch.cuda.is_available() else 0
    qsnap = OUTD / f"{sid}_queries.npy"
    np.save(qsnap, qarr)
    rec = {"shot": sid, "T": T, "semantic_queries": sq["label"], "queries_npy": str(qsnap), "runs": out, "drift_mean_px": dm,
           "windows": windows, "peak_vram_mb": vram, "ckpt": str(ckpt()),
           "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with open(REC, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    print(json.dumps({k: rec[k] for k in ("shot", "T", "drift_mean_px", "peak_vram_mb")}))
    # free
    del model
    import torch as _t
    if _t.cuda.is_available():
        _t.cuda.empty_cache()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shots", nargs="+")
    args = ap.parse_args()
    for sid in args.shots:
        run(sid)


if __name__ == "__main__":
    main()
