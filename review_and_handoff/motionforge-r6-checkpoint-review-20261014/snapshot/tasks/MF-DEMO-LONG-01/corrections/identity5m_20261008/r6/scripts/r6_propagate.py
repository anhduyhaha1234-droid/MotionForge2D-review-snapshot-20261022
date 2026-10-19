"""R6 propagation — upstream stage-2 (Rerender_A_Video video_blend) over REVIEWED keys.

T-F03/R5-F07 compliance:
  * only keys with PASS review enter (gate_shot_before_propagate blocks otherwise);
  * rc != 0 OR incomplete output OR stale output => BLOCK, no tail-fill;
  * completed runs only: materialize trailing frame(s) m from the final key (upstream convention 1..m-1).
usage: python -B r6_propagate.py S0022 [S0023 ...] [--nproc 3] [--itv 10]
"""
from __future__ import annotations
import argparse, json, os, shutil, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r6_common as K  # noqa: E402
import r6_gate as G  # noqa: E402

REC = K.R6 / "receipts/R6_PROPAGATE_RUNS.jsonl"


def blend_script():
    cands = sorted((K.R4 / "vendor").glob("Rerender_A_Video-*/video_blend.py"))
    assert cands, "video_blend.py not found (r4/vendor read-only)"
    return cands[0]


def run_shot(sid, itv=10, nproc=3):
    t_start = time.time()
    G.gate_shot_before_propagate(sid)  # all keys reviewed PASS + event keys present
    n = K.PLAN[sid]["frames"]
    m = n
    while (m - 1) % itv != 0:
        m += 1
    base = K.R6 / "work" / sid
    vid = base / "video"
    keys0 = base / "keys0"
    vid.mkdir(parents=True, exist_ok=True)
    keys0.mkdir(parents=True, exist_ok=True)
    for d in [base / "blend", base / "tmp"] + [base / f"out_{i}" for i in range(1, nproc + 3)]:
        d.mkdir(parents=True, exist_ok=True)
    a0 = K.PLAN[sid]["start_frame"]
    have = len(list(vid.glob("*.png")))
    if have != n:
        tmpd = K.TMPD / f"stage_{sid}"
        tmpd.mkdir(parents=True, exist_ok=True)
        w, r = K.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a0/30:.6f}", "-i", str(K.SRC),
                      "-frames:v", str(n), "-vf", "delogo=x=2:y=294:w=228:h=62,pad=640:368:0:4:black",
                      "-start_number", "1", str(tmpd / "%04d.png")])
        assert r.returncode == 0, r.stderr[-200:]
        for f in sorted(tmpd.glob("*.png")):
            shutil.copyfile(f, vid / f.name)
    lastf = vid / f"{n:04d}.png"
    for fid in range(n + 1, m + 1):
        dst = vid / f"{fid:04d}.png"
        if not dst.exists():
            shutil.copyfile(lastf, dst)
    keydir = K.R6 / "keys" / sid
    kfids = sorted(int(p.name.split("_")[1]) for p in keydir.glob("f_*_key.png"))
    assert kfids and kfids[0] == 1, f"{sid}: no keys"
    from PIL import Image
    for fid in range(1, m + 1, itv):
        if fid in kfids:
            src = keydir / f"f_{fid:04d}_key.png"
        else:
            src = keydir / f"f_{max(f for f in kfids if f <= fid):04d}_key.png"
        im = Image.open(src).convert("RGB")
        if im.size != (640, 368):
            im = im.resize((640, 360))
            import numpy as _np
            im = Image.fromarray(_np.pad(_np.asarray(im), ((4, 4), (0, 0), (0, 0))))
        im.save(keys0 / f"{fid:04d}.png")
    script = blend_script()
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{script.parent};{K.R4/'env/pylibs'}"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    out = base / "blend.mp4"
    t0 = time.time()
    w, r = K.run([K.ENVPY, "-B", str(script), str(base), "--beg", "1", "--end", str(m), "--itv", str(itv),
                  "--key", "keys0", "--fps", "30", "--n_proc", str(nproc), "--output", str(out)],
                 env=env, cwd=str(script.parent))
    bd = base / "blend"
    frames_out = len(list(bd.glob("*.jpg"))) if bd.exists() else 0
    block = None
    if r.returncode != 0:
        block = f"rc={r.returncode}"
    elif frames_out < m - 1:
        block = f"partial {frames_out}/{m-1}"
    else:
        newest = max((f.stat().st_mtime for f in bd.iterdir() if f.is_file()), default=0)
        if newest < t0:
            block = "stale outputs (no writes during run)"
    if block:
        rec = {"shot": sid, "n": n, "m": m, "itv": itv, "rc": r.returncode, "blocked": block,
               "frames_out": frames_out, "wall_s": round(time.time() - t0, 1),
               "out": str(out), "tail": (r.stderr or r.stdout or "")[-200:],
               "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        with open(REC, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        raise SystemExit(f"PROPAGATE BLOCK [{sid}]: {block}")
    # completed: materialize tail frame(s) from the final key
    for fid in range(frames_out + 1, m + 1):
        src_k = keys0 / f"{fid:04d}.png"
        if not src_k.exists():
            cands = sorted(keys0.glob("*.png"))
            src_k = cands[-1] if cands else None
        if src_k and src_k.exists():
            Image.open(src_k).convert("RGB").save(bd / f"{fid:04d}.jpg", quality=95)
    wall = round(time.time() - t0, 1)
    rec = {"shot": sid, "n": n, "m": m, "itv": itv, "rc": 0, "frames_out": len(list(bd.glob("*.jpg"))),
           "wall_s": wall, "fresh_complete": True, "out": str(out),
           "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with open(REC, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    print(json.dumps(rec, ensure_ascii=False), flush=True)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shots", nargs="+")
    ap.add_argument("--nproc", type=int, default=3)
    ap.add_argument("--itv", type=int, default=10)
    args = ap.parse_args()
    for sid in args.shots:
        try:
            run_shot(sid, itv=args.itv, nproc=args.nproc)
        except SystemExit as e:
            print(f"BLOCK {sid}: {e}", flush=True)


if __name__ == "__main__":
    main()
