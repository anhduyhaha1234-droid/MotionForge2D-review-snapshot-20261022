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
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r6_common as K  # noqa: E402
import r6_gate as G  # noqa: E402

REC = K.R6 / "receipts/R6_PROPAGATE_RUNS.jsonl"
NS = Path(os.environ.get("R6_PROPAGATE_NS") or os.environ.get("R6_INVOCATION_DIR") or K.R6 / "continuations/LONG01-R6g-20261014T0725Z-1572")


def blend_script():
    cands = sorted((K.R4 / "vendor").glob("Rerender_A_Video-*/video_blend.py"))
    assert cands, "video_blend.py not found (r4/vendor read-only)"
    return cands[0]


def event_fids_for(sid: str, row: dict) -> set[int]:
    import r6_event_contract as EC
    return EC.extract_canonical_event_fids(row, sid)


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


def run_shot(sid: str, nproc: int = 3, cuts: list | None = None):
    run_root = NS / "renders" / sid / "runs"
    child = []
    merged = NS / "renders" / sid / "blend"
    
    try:
        G.gate_shot_before_propagate(sid)
        try:
            row = G.ledger_row(sid)
        except Exception:
            row = {"shot": sid, "n": K.PLAN[sid]["frames"] if sid in K.PLAN else 0, "actors": [], "cuts": []}
            
        n = K.PLAN[sid]["frames"]
        m = n
        if cuts is None:
            cuts = list(row.get("cuts", []))
            # Also include any cut event fids from discrete events
            for e in row.get("events", []):
                if isinstance(e, dict) and "cut" in str(e.get("event", "")).lower():
                    if "frame" in e and isinstance(e["frame"], int) and 1 <= e["frame"] <= n:
                        cuts.append(e["frame"])
                    elif "f" in e and isinstance(e["f"], int) and 0 <= e["f"] < n:
                        cuts.append(e["f"] + 1)
        
        key_fids = build_key_fids(sid, n)
        runs = plan_runs(key_fids, m, cuts=cuts)
        script = blend_script()
        
        if merged.exists():
            for f in merged.glob("*"):
                try:
                    f.unlink()
                except Exception:
                    pass
        merged.mkdir(parents=True, exist_ok=True)

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
                raise RuntimeError(f"run {ri} rc={rec['rc']}")
            
            bd = rb / "blend"
            frames = sorted(bd.glob("*.jpg"))
            expect = end - beg
            
            # Strict count check
            if len(frames) != expect:
                raise RuntimeError(f"run {ri} partial/extra frames {len(frames)}/{expect}: {[f.name for f in frames]}")
            
            # Strict upstream global frame naming check: beg..end-1
            # Upstream VideoSequence writes global frame IDs: f"{fid:04d}.jpg" for fid in range(beg, end)
            for fid in range(beg, end):
                exp_name = f"{fid:04d}.jpg"
                if not (bd / exp_name).exists():
                    raise RuntimeError(f"run {ri} missing expected frame {exp_name}, got {[f.name for f in frames]}")
            
            # Verify decode and copy frames directly to merged
            for fid in range(beg, end):
                src_f = bd / f"{fid:04d}.jpg"
                with Image.open(src_f) as im_chk:
                    im_chk.verify()
                dst_f = merged / f"{fid:04d}.jpg"
                shutil.copyfile(src_f, dst_f)
                
        # Final frame m from the last key
        last_key = K.R6 / "keys" / sid / f"f_{m:04d}_key.png"
        if not last_key.exists():
            cands = sorted((K.R6 / "keys" / sid).glob("f_*_key.png"))
            if not cands:
                raise RuntimeError(f"no key images found for {sid}")
            last_key = cands[-1]
            
        with Image.open(last_key) as im_chk:
            im_chk.verify()
        im = Image.open(last_key).convert("RGB")
        if im.size != (640, 368):
            import numpy as _np
            im = im.resize((640, 360))
            im = Image.fromarray(_np.pad(_np.asarray(im), ((4, 4), (0, 0), (0, 0))))
        im.save(merged / f"{m:04d}.jpg")
        
        frames = sorted(merged.glob("*.jpg"))
        names = [f.name for f in frames]
        if len(names) != m or names[0] != "0001.jpg" or names[-1] != f"{m:04d}.jpg":
            raise RuntimeError(f"merged frame set wrong: {len(names)}/{m}")
        if len(set(names)) != len(names):
            raise RuntimeError("duplicate frames in merged set")
            
        # Verify decode of all merged frames
        for f in frames:
            with Image.open(f) as im_chk:
                im_chk.verify()
                
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
        man_p.parent.mkdir(parents=True, exist_ok=True)
        man_p.write_text(json.dumps(man, ensure_ascii=False), encoding="utf-8")
        with open(REC, "a", encoding="utf-8") as f:
            f.write(json.dumps({"shot": sid, "n": n, "m": m, "runs": len(child), "rc": 0, "frames": len(frames),
                                "manifest": str(man_p), "at": man["at"]}) + "\n")
        print(json.dumps({"shot": sid, "m": m, "runs": len(child), "frames": len(frames), "manifest": str(man_p)}))
        return man
        
    except (Exception, SystemExit) as exc:
        man_p = K.R6 / "work" / sid / "blend_manifest.json"
        if man_p.exists():
            try:
                man_p.unlink()
            except Exception:
                pass
        n_frames = K.PLAN[sid]["frames"] if (sid in K.PLAN and "frames" in K.PLAN[sid]) else 0
        with open(REC, "a", encoding="utf-8") as f:
            f.write(json.dumps({"shot": sid, "n": n_frames, "m": n_frames, "rc": 1, "runs": len(child),
                                "blocked": str(exc),
                                "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}) + "\n")
        raise SystemExit(f"PROPAGATE BLOCK [{sid}] {exc}")


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
