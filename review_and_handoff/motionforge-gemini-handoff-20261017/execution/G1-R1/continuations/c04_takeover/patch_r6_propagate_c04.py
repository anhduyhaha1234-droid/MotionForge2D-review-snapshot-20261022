import os

prop_path = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_propagate.py"
with open(prop_path, "r", encoding="utf-8") as f:
    src = f.read()

# 1. Add from PIL import Image at top level
old_hdr = """from __future__ import annotations
import argparse, json, os, shutil, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))"""

new_hdr = """from __future__ import annotations
import argparse, json, os, shutil, sys, time
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))"""

assert src.count(old_hdr) == 1, "old_hdr not found"
src = src.replace(old_hdr, new_hdr)

# 2. Rewrite run_shot
old_run_shot_start = "def run_shot(sid: str, nproc: int = 3, cuts: list | None = None):"
old_main_start = "def main():"

idx1 = src.find(old_run_shot_start)
assert idx1 != -1, "run_shot not found"
idx2 = src.find(old_main_start)
assert idx2 != -1, "main not found"

new_run_shot_func = '''def run_shot(sid: str, nproc: int = 3, cuts: list | None = None):
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
                                "manifest": str(man_p), "at": man["at"]}) + "\\n")
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
                                "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}) + "\\n")
        raise SystemExit(f"PROPAGATE BLOCK [{sid}] {exc}")
'''

src = src[:idx1] + new_run_shot_func + "\n\n" + src[idx2:]

with open(prop_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)
print("Updated r6_propagate.py successfully")
