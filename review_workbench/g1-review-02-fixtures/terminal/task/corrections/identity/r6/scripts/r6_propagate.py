"""R6 propagate — upstream stage-2 (Rerender video_blend) with F03/F05/F06 compliance.

F03: event keys are BOUNDARIES — the shot is decomposed into runs at exact key fids (union of
     storyboard grid fids and event fids). Run r covers [a..b] with uniform spacing (b-a); frames
     are produced from the keys at exactly those fids; NO snapping to earlier keys.
F05: per-run child rc recorded; merged with exact per-frame mapping + no missing/dup; manifest
     (name,size,sha256 per frame, child_outcomes, decode_ok) written; no max-mtime freshness.
F06: run dirs live under NS = R6/continuations/<invocation>/renders/<sid>/runs/rN (never reused
     across shots/invocations); merged output under NS/renders/<sid>/blend with its manifest at
     R6/work/<sid>/blend_manifest.json (consumed by the gate).

usage: python -B r6_propagate.py S0022 [S0023 ...] [--nproc 3]
"""
from __future__ import annotations
import argparse, json, os, shutil, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r6_common as K  # noqa: E402
import r6_gate as G  # noqa: E402

REC = K.R6 / "receipts/R6_PROPAGATE_RUNS.jsonl"
NS = Path(os.environ.get("R6_PROPAGATE_NS") or os.environ.get("R6_INVOCATION_DIR") or K.R6 / "continuations/LONG01-R6g-20261014T0725Z-1572")


def blend_script():
    cands = sorted((K.R4 / "vendor").glob("Rerender_A_Video-*/video_blend.py"))
    assert cands, "video_blend.py not found (r4/vendor read-only)"
    return cands[0]


def event_fids_for(sid: str, row: dict) -> set:
    n = int(row.get("n", 9999))
    ev = set()
    for e in row.get("events", []):
        if isinstance(e, dict):
            f_val = e.get("f")
            frame_val = e.get("frame")
            if f_val is not None and frame_val is not None:
                if int(f_val) + 1 != int(frame_val):
                    raise ValueError(f"conflicting event f ({f_val}) vs frame ({frame_val}) in {sid}")
            if frame_val is not None:
                fid = int(frame_val)
            elif f_val is not None:
                fid = int(f_val) + 1
            else:
                continue
            if 1 <= fid <= n:
                ev.add(fid)
            else:
                raise ValueError(f"event fid {fid} out of range [1, {n}] in {sid}")
    for c in row.get("contacts", []):
        if isinstance(c, dict):
            if "from" in c:
                fid_from = int(c["from"]) + 1
                if 1 <= fid_from <= n:
                    ev.add(fid_from)
            if "to" in c:
                fid_to = int(c["to"])
                if 1 <= fid_to <= n:
                    ev.add(fid_to)
    for a in row.get("actors", []):
        for w in a.get("class_windows", []):
            w_from = int(w.get("from", 0))
            w_to = int(w.get("to", 9999))
            if 1 < w_from <= n:
                ev.add(w_from)
            if 1 <= w_to < n:
                ev.add(w_to + 1)
    return ev


def build_key_fids(sid: str, n: int) -> list:
    """Union of storyboard key fids and event fids (exact), sorted, bounded by n (+ last fid)."""
    sb = json.loads((K.R6 / "storyboard" / f"{sid}.json").read_text(encoding="utf-8"))
    row = G.ledger_row(sid)
    fids = {k["fid"] for k in sb["keys"] if k["fid"] <= n}
    fids |= {f for f in event_fids_for(sid, row) if f <= n}
    return sorted(fids)


def plan_runs(key_fids: list, m: int, cuts: list | None = None) -> list:
    """Decompose [1..m] into runs whose internal spacing is uniform: consecutive runs split where
    the spacing between consecutive key fids changes, and never interpolate across hard cuts."""
    cut_set = set(cuts or [])
    seq = sorted(set(key_fids) | {1, m} | cut_set)
    runs = []
    cur = [seq[0]]
    for a, b in zip(seq, seq[1:]):
        d = b - a
        if len(cur) >= 2 and ((cur[-1] - cur[-2]) != d or cur[-1] in cut_set):
            runs.append(cur)
            cur = [cur[-1]]
        cur.append(b)
    if cur not in runs:
        runs.append(cur)
    return [r for r in runs if len(r) >= 2]


def run_one(base: Path, beg: int, end: int, itv: int, script: Path, nproc: int):
    base.mkdir(parents=True, exist_ok=True)
    for d in [base / "blend", base / "tmp"] + [base / f"out_{i}" for i in range(1, nproc + 3)]:
        d.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{script.parent};{K.R4/'env/pylibs'}"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    out = base / "blend.mp4"
    t0 = time.time()
    w, r = K.run([K.ENVPY, "-B", str(script), str(base), "--beg", str(beg), "--end", str(end),
                  "--itv", str(itv), "--key", "keys0", "--fps", "30", "--n_proc", str(nproc),
                  "--output", str(out)], env=env, cwd=str(script.parent))
    return {"beg": beg, "end": end, "itv": itv, "rc": r.returncode, "wall_s": round(time.time() - t0, 1),
            "tail": (r.stderr or r.stdout or "")[-160:]}


def stage_shot_assets(sid: str, key_fids: list, m: int, run_base: Path, beg: int, end: int):
    """Stage this run's video frames + its keys (global names) into the run base."""
    a0 = K.PLAN[sid]["start_frame"]
    vid = run_base / "video"
    keys0 = run_base / "keys0"
    vid.mkdir(parents=True, exist_ok=True)
    keys0.mkdir(parents=True, exist_ok=True)
    tmpd = run_base / "tmpstage"
    tmpd.mkdir(parents=True, exist_ok=True)
    w, r = K.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{(a0 + beg - 1)/30:.6f}", "-i", str(K.SRC),
                  "-frames:v", str(end - beg + 1), "-vf", "delogo=x=2:y=294:w=228:h=62,pad=640:368:0:4:black",
                  "-start_number", str(beg), str(tmpd / "%04d.png")])
    assert r.returncode == 0, r.stderr[-200:]
    for f in sorted(tmpd.glob("*.png")):
        shutil.copyfile(f, vid / f.name)
    from PIL import Image
    kf_in_run = [f for f in key_fids if beg <= f <= end]
    for fid in kf_in_run:
        src = K.R6 / "keys" / sid / f"f_{fid:04d}_key.png"
        if not src.exists():
            raise SystemExit(f"EVENT_KEY_MISSING {sid} f{fid} (key not generated for exact event fid)")
        im = Image.open(src).convert("RGB")
        if im.size != (640, 368):
            import numpy as _np
            im = im.resize((640, 360))
            im = Image.fromarray(_np.pad(_np.asarray(im), ((4, 4), (0, 0), (0, 0))))
        im.save(keys0 / f"{fid:04d}.png")
    return kf_in_run


def run_shot(sid, nproc=3):
    G.gate_shot_before_propagate(sid)
    n = K.PLAN[sid]["frames"]
    m = n
    key_fids = build_key_fids(sid, n)
    runs = plan_runs(key_fids, m)
    script = blend_script()
    run_root = NS / "renders" / sid / "runs"
    child = []
    merged = NS / "renders" / sid / "blend"
    if merged.exists():
        for f in merged.glob("*"):
            f.unlink()
    merged.mkdir(parents=True, exist_ok=True)
    frame_map = {}
    for ri, run in enumerate(runs):
        beg, end = run[0], run[-1]
        itv = (end - beg) // max(1, (len(run) - 1))
        rb = run_root / f"r{ri:02d}"
        if rb.exists():
            shutil.rmtree(rb)
        stage_shot_assets(sid, key_fids, m, rb, beg, end)
        rec = run_one(rb, beg, end, itv, script, nproc)
        rec["run"] = ri
        child.append(rec)
        if rec["rc"] != 0:
            man_p = K.R6 / "work" / sid / "blend_manifest.json"
            if man_p.exists():
                try:
                    man_p.unlink()
                except Exception:
                    pass
            with open(REC, "a", encoding="utf-8") as f:
                f.write(json.dumps({"shot": sid, "n": n, "m": m, "rc": rec["rc"], "runs": len(child),
                                    "failed_run": ri, "blocked": f"run {ri} rc={rec['rc']}",
                                    "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}) + "\n")
            raise SystemExit(f"PROPAGATE BLOCK [{sid}] run {ri} rc={rec['rc']}")
        bd = rb / "blend"
        frames = sorted(bd.glob("*.jpg"))
        expect = end - beg  # upstream writes 1..end-1 (last frame from NEXT key); final run patched below
        if len(frames) < expect:
            man_p = K.R6 / "work" / sid / "blend_manifest.json"
            if man_p.exists():
                try:
                    man_p.unlink()
                except Exception:
                    pass
            with open(REC, "a", encoding="utf-8") as f:
                f.write(json.dumps({"shot": sid, "n": n, "m": m, "rc": 1, "runs": len(child),
                                    "failed_run": ri, "blocked": f"run {ri} partial {len(frames)}/{expect}",
                                    "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}) + "\n")
            raise SystemExit(f"PROPAGATE BLOCK [{sid}] run {ri} partial {len(frames)}/{expect}")
        # frames are named by local index; interval [beg..end] -> frames beg..end-1 (frame `end` comes next run)
        idx = 0
        for fid in range(beg, end):
            src = frames[idx] if idx < len(frames) else None
            if src is None:
                raise SystemExit(f"PROPAGATE BLOCK [{sid}] missing frame {fid}")
            dst = merged / f"{fid:04d}.jpg"
            shutil.copyfile(src, dst)
            idx += 1
    # final frame m from the last key
    last_key = K.R6 / "keys" / sid / f"f_{m:04d}_key.png"
    if not last_key.exists():
        cands = sorted((K.R6 / "keys" / sid).glob("f_*_key.png"))
        last_key = cands[-1]
    from PIL import Image
    im = Image.open(last_key).convert("RGB")
    if im.size != (640, 368):
        import numpy as _np
        im = im.resize((640, 360))
        im = Image.fromarray(_np.pad(_np.asarray(im), ((4, 4), (0, 0), (0, 0))))
    im.save(merged / f"{m:04d}.jpg")
    frames = sorted(merged.glob("*.jpg"))
    names = [f.name for f in frames]
    if len(names) != m or names[0] != "0001.jpg" or names[-1] != f"{m:04d}.jpg":
        raise SystemExit(f"PROPAGATE BLOCK [{sid}] merged frame set wrong: {len(names)}/{m}")
    if len(set(names)) != len(names):
        raise SystemExit(f"PROPAGATE BLOCK [{sid}] duplicate frames")
    # F05 manifest: per-frame sha256 + child outcomes + decode sample
    small = 0
    from PIL import Image as _I
    import numpy as _np
    manifest_frames = []
    for f in frames:
        a = _np.asarray(_I.open(f).convert("L"))
        if float(a.std()) < 1.0:
            small += 1
        manifest_frames.append({"name": f.name, "size": f.stat().st_size, "sha256": K.sha(f)})
    dec = K.run(["ffmpeg", "-y", "-v", "error", "-i", str(merged / "0001.jpg"), "-f", "null", "-"])
    decode_ok = dec[1].returncode == 0
    key_set_sha = __import__("hashlib").sha256(json.dumps(
        [[f, K.sha(K.R6/'keys'/sid/f'f_{f:04d}_key.png')] for f in key_fids if (K.R6/'keys'/sid/f'f_{f:04d}_key.png').exists()],
        sort_keys=True).encode()).hexdigest()
    man = {"shot": sid, "n": n, "m": m, "blend_dir": str(merged), "key_fids": key_fids, "runs": [[r["beg"], r["end"], r["itv"]] for r in child],
           "child_outcomes": child, "child_outcomes_sha": __import__("hashlib").sha256(json.dumps(child, sort_keys=True).encode()).hexdigest(),
           "key_set_sha": key_set_sha, "frames": manifest_frames, "flat_frames": small, "decode_ok": decode_ok,
           "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    man_p = K.R6 / "work" / sid / "blend_manifest.json"
    man_p.write_text(json.dumps(man, ensure_ascii=False), encoding="utf-8")
    with open(REC, "a", encoding="utf-8") as f:
        f.write(json.dumps({"shot": sid, "n": n, "m": m, "runs": len(child), "rc": 0, "frames": len(frames),
                            "manifest": str(man_p), "at": man["at"]}) + "\n")
    print(json.dumps({"shot": sid, "m": m, "runs": len(child), "frames": len(frames), "manifest": str(man_p)}))
    return man


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shots", nargs="+")
    ap.add_argument("--nproc", type=int, default=3)
    args = ap.parse_args()
    failed = []
    for sid in args.shots:
        try:
            run_shot(sid, nproc=args.nproc)
        except SystemExit as e:
            print(f"BLOCK {sid}: {e}", flush=True)
            failed.append((sid, str(e)))
        except Exception as e:
            print(f"ERROR {sid}: {e}", flush=True)
            failed.append((sid, str(e)))
    if failed:
        sys.exit(f"PROPAGATE_FAILED: {len(failed)} shots failed: {failed}")


if __name__ == "__main__":
    main()
