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
    T = min(len(src), len(gen))
    src, gen = src[:T], gen[:T]
    # queries: 8x8 grid over center region + actor-anchor points at event contact frames
    ev = json.loads((K.R6 / "event_map.json").read_text(encoding="utf-8"))
    events = [e for e in ev.get(sid, [])] if isinstance(ev.get(sid), list) else ev.get(sid, {}).get("events", [])
    qs = []
    for gy in range(8):
        for gx in range(8):
            qs.append([0, 100 + gx * 55, 80 + gy * 25])
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
    # drift: mean per-frame displacement difference between TRACKS (only where both visible)
    tr_s = np.load(OUTD / f"{sid}_source_tracks.npy")
    tr_g = np.load(OUTD / f"{sid}_r6_tracks.npy")
    d = np.linalg.norm(tr_g - tr_s, axis=-1)  # (T,N)
    both = np.logical_and(np.load(OUTD / f"{sid}_source_vis.npy") > 0,
                          np.load(OUTD / f"{sid}_r6_vis.npy") > 0)  # (T,N)
    dm = float(d[both].mean()) if both.any() else None
    windows = []
    for e in events if isinstance(events, list) else []:
        f0 = int(e.get("f0", 1)); f1 = int(e.get("f1", f0 + 10))
        windows.append({"event": e.get("kind", "?"), "before": [f0 - 5, f0], "contact": [f0, f0 + 3],
                        "hold": [f0 + 3, f1 - 3], "release": [f1 - 3, f1],
                        "drift_contact_mean": float(np.nanmean(d[max(0, f0 - 1):f0 + 3][both[max(0, f0 - 1):f0 + 3]]) ) if both.any() else None})
    vram = round(torch.cuda.max_memory_allocated() / 2**20) if torch.cuda.is_available() else 0
    rec = {"shot": sid, "T": T, "grid": "8x8", "runs": out, "drift_mean_px": dm,
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
