import os

prop_path = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_propagate.py"
with open(prop_path, "r", encoding="utf-8") as f:
    src = f.read()

# 1. Replace event_fids_for
old_ev = '''def event_fids_for(sid: str, row: dict) -> set:
    ev = set()
    for e in row.get("events", []):
        if isinstance(e, dict):
            if "frame" in e:
                ev.add(int(e["frame"]))
            elif "f" in e:
                ev.add(int(e["f"]) + 1)
    for c in row.get("contacts", []):
        if isinstance(c, dict) and "from" in c:
            ev.add(int(c["from"]) + 1)
    for a in row.get("actors", []):
        for w in a.get("class_windows", []):
            if w.get("from", 0) > 1 and w.get("class") in ("VISIBLE", "PARTIALLY_VISIBLE"):
                ev.add(int(w["from"]))
    return ev'''

new_ev = '''def event_fids_for(sid: str, row: dict) -> set:
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

assert src.count(old_ev) == 1
src = src.replace(old_ev, new_ev)

# 2. Update run_shot child failure handling
old_child_check = '''        if rec["rc"] != 0:
            raise SystemExit(f"PROPAGATE BLOCK [{sid}] run {ri} rc={rec['rc']}")
        bd = rb / "blend"
        frames = sorted(bd.glob("*.jpg"))
        expect = end - beg  # upstream writes 1..end-1 (last frame from NEXT key); final run patched below
        if len(frames) < expect:
            raise SystemExit(f"PROPAGATE BLOCK [{sid}] run {ri} partial {len(frames)}/{expect}")'''

new_child_check = '''        if rec["rc"] != 0:
            man_p = K.R6 / "work" / sid / "blend_manifest.json"
            if man_p.exists():
                try:
                    man_p.unlink()
                except Exception:
                    pass
            with open(REC, "a", encoding="utf-8") as f:
                f.write(json.dumps({"shot": sid, "n": n, "m": m, "rc": rec["rc"], "runs": len(child),
                                    "failed_run": ri, "blocked": f"run {ri} rc={rec['rc']}",
                                    "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}) + "\\n")
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
                                    "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}) + "\\n")
            raise SystemExit(f"PROPAGATE BLOCK [{sid}] run {ri} partial {len(frames)}/{expect}")'''

assert src.count(old_child_check) == 1
src = src.replace(old_child_check, new_child_check)

# 3. Update main() in r6_propagate.py to exit nonzero on any failure
old_main = '''def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shots", nargs="+")
    ap.add_argument("--nproc", type=int, default=3)
    args = ap.parse_args()
    for sid in args.shots:
        try:
            run_shot(sid, nproc=args.nproc)
        except SystemExit as e:
            print(f"BLOCK {sid}: {e}", flush=True)'''

new_main = '''def main():
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
        sys.exit(f"PROPAGATE_FAILED: {len(failed)} shots failed: {failed}")'''

assert src.count(old_main) == 1
src = src.replace(old_main, new_main)

with open(prop_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)
print("Updated r6_propagate.py with canonical event transitions & fail-closed child CLI successfully")
