import os

prop_path = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_propagate.py"
with open(prop_path, "r", encoding="utf-8") as f:
    src = f.read()

# 1. Update event_fids_for to use r6_event_contract
old_ev = '''def event_fids_for(sid: str, row: dict) -> set:
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
    return ev'''

new_ev = '''def event_fids_for(sid: str, row: dict) -> set[int]:
    import r6_event_contract as EC
    return EC.extract_canonical_event_fids(row, sid)'''

assert src.count(old_ev) == 1, "old_ev not found"
src = src.replace(old_ev, new_ev)

# 2. Update run_shot
idx_run_shot = src.find("def run_shot(sid, nproc=3):")
assert idx_run_shot != -1, "run_shot not found"
idx_main = src.find("def main():")
assert idx_main != -1, "main not found"

new_run_shot = '''def run_shot(sid: str, nproc: int = 3, cuts: list | None = None):
    G.gate_shot_before_propagate(sid)
    row = G.ledger_row(sid)
    n = K.PLAN[sid]["frames"]
    m = n
    if cuts is None:
        cuts = list(row.get("cuts", []))
    key_fids = build_key_fids(sid, n)
    runs = plan_runs(key_fids, m, cuts=cuts)
    script = blend_script()
    run_root = NS / "renders" / sid / "runs"
    child = []
    merged = NS / "renders" / sid / "blend"
    if merged.exists():
        for f in merged.glob("*"):
            f.unlink()
    merged.mkdir(parents=True, exist_ok=True)
    
    try:
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
                raise RuntimeError(f"run {ri} expected {expect} frames, got {len(frames)}: {[f.name for f in frames]}")
            
            # Strict expected filename check: 0001.jpg .. expect.jpg
            for i in range(1, expect + 1):
                exp_name = f"{i:04d}.jpg"
                if not (bd / exp_name).exists():
                    raise RuntimeError(f"run {ri} missing expected frame {exp_name}, got {[f.name for f in frames]}")
            
            # Verify decode and copy frames
            for i in range(1, expect + 1):
                src_f = bd / f"{i:04d}.jpg"
                with Image.open(src_f) as im_chk:
                    im_chk.verify()
                dst_f = merged / f"{beg + i - 1:04d}.jpg"
                shutil.copyfile(src_f, dst_f)
                
        # final frame m from last key
        last_key = K.R6 / "keys" / sid / f"f_{m:04d}_key.png"
        if not last_key.exists():
            cands = sorted((K.R6 / "keys" / sid).glob("f_*_key.png"))
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
        man_p.write_text(json.dumps(man, ensure_ascii=False), encoding="utf-8")
        with open(REC, "a", encoding="utf-8") as f:
            f.write(json.dumps({"shot": sid, "n": n, "m": m, "runs": len(child), "rc": 0, "frames": len(frames),
                                "manifest": str(man_p), "at": man["at"]}) + "\\n")
        print(json.dumps({"shot": sid, "m": m, "runs": len(child), "frames": len(frames), "manifest": str(man_p)}))
        return man
        
    except Exception as exc:
        man_p = K.R6 / "work" / sid / "blend_manifest.json"
        if man_p.exists():
            try:
                man_p.unlink()
            except Exception:
                pass
        with open(REC, "a", encoding="utf-8") as f:
            f.write(json.dumps({"shot": sid, "n": n, "m": m, "rc": 1, "runs": len(child),
                                "blocked": str(exc),
                                "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}) + "\\n")
        raise SystemExit(f"PROPAGATE BLOCK [{sid}] {exc}")
'''

src = src[:idx_run_shot] + new_run_shot + "\n\n" + src[idx_main:]

with open(prop_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)
print("Updated r6_propagate.py with strict frame naming, decode verification and comprehensive fail-closed error handling successfully")
