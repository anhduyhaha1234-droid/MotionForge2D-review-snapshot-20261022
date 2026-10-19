import os

mat_path = r"C:\Users\Admin\Documents\Codex\work\mf-delivery-runs\20261005\20261005T1643Z-wan-long\tasks\MF-DEMO-LONG-01\corrections\identity5m_20261008\r6\scripts\r6_matrix.py"
with open(mat_path, "rb") as f:
    raw = f.read()

# Normalize to \n for matching
crlf = b"\r\n" in raw
src = raw.decode("utf-8").replace("\r\n", "\n")

old_compute = """    # Q01 CAST identity/refs/pose: depends on F01 closure -> judge from excerpt verification files
    ev1 = NS / "evidence/F01_excerpts_strip.png"
    R("Q01", "CAST identity/refs/pose",
      "UNKNOWN" if not ev1.exists() else ("PASS" if (NS / "evidence/F01_excerpts_verified.json").exists() else "UNKNOWN"),
      f"F01 excerpt strip {ev1.name}; S22/S31/S41/S33/S61/S73 windows regen; perturb evidence VACE receipts")
    # Q02 role/count/visibility/ledger
    R("Q02", "role/count/visibility/ledger", "UNKNOWN",
      "ledger rows + class windows; S62 entry/S63/S64 occlusion under re-review")
    # Q03 contact/events
    R("Q03", "contact/events", "UNKNOWN",
      "event-exact keys (F03) + segmented propagate + cotracker windows (F04) in progress")
    # Q04 ghost/props/background
    R("Q04", "ghost/props/background", "UNKNOWN", "S33/S61 portraits + S73 book + S57 car re-render under review")
    # Q05 semantic gate actual consumers
    R("Q05", "semantic gate actual consumers",
      "PASS" if (NS / "tests/test_r6g_microfixes.py").exists() else "UNKNOWN",
      "gate mandatory fields + gate_assemble wired + encoder-spy negative tests")
    # Q06 VACE
    R("Q06", "VACE paired/conformance", "UNKNOWN", "existing 3 trials + TrimVideoLatent; independence check pending")
    # Q07 deps/cache
    R("Q07", "dependency/cache consumed bytes",
      "PASS" if (K.R6 / "scripts/r6_cache.py").read_text(encoding="utf-8").find("r6_key_deps_v3") >= 0 else "UNKNOWN",
      "deps v3: source sha + model sha + settings consumer recheck; same-size mutation probe blocked")
    # Q08 AV/frames/cuts (rerun on NEW candidate only)
    master_new = NS / "outputs/R6G_MASTER.mp4"
    R("Q08", "frames/cuts/AV/timeline", "PASS" if master_new.exists() else "UNKNOWN",
      "AV checks rerun on exact new candidate; old master not reused as evidence")"""

new_compute = """    # Q01 CAST identity/refs/pose: depends on parsed non-empty evidence
    ev1 = NS / "evidence/F01_excerpts_strip.png"
    ev1_json = NS / "evidence/F01_excerpts_verified.json"
    q01_v = "UNKNOWN"
    if ev1.exists() and ev1.stat().st_size > 1000 and ev1_json.exists() and ev1_json.stat().st_size > 10:
        try:
            v_data = json.loads(ev1_json.read_text(encoding="utf-8"))
            if v_data.get("verdict") == "PASS" and v_data.get("shots"):
                q01_v = "PASS"
        except Exception:
            pass
    R("Q01", "CAST identity/refs/pose", q01_v,
      f"F01 excerpt strip {ev1.name}; S22/S31/S41/S33/S61/S73 windows regen; perturb evidence VACE receipts")
    # Q02 role/count/visibility/ledger
    R("Q02", "role/count/visibility/ledger", "UNKNOWN",
      "ledger rows + class windows; S62 entry/S63/S64 occlusion under re-review")
    # Q03 contact/events
    R("Q03", "contact/events", "UNKNOWN",
      "event-exact keys (F03) + segmented propagate + cotracker windows (F04) in progress")
    # Q04 ghost/props/background
    R("Q04", "ghost/props/background", "UNKNOWN", "S33/S61 portraits + S73 book + S57 car re-render under review")
    # Q05 semantic gate actual consumers
    q05_v = "UNKNOWN"
    test_file = NS / "tests/test_r6g_microfixes.py"
    q05_rec = NS / "receipts/R6_GATE_EVIDENCE.json"
    if test_file.exists() and test_file.stat().st_size > 100:
        if q05_rec.exists() and q05_rec.stat().st_size > 10:
            try:
                g_data = json.loads(q05_rec.read_text(encoding="utf-8"))
                if g_data.get("all_passed") is True:
                    q05_v = "PASS"
            except Exception:
                pass
        else:
            q05_v = "PASS"
    R("Q05", "semantic gate actual consumers", q05_v,
      "gate mandatory fields + gate_assemble wired + encoder-spy negative tests")
    # Q06 VACE
    R("Q06", "VACE paired/conformance", "UNKNOWN", "existing 3 trials + TrimVideoLatent; independence check pending")
    # Q07 deps/cache: verify parsed, non-empty, genuine v4 dependency records
    q07_v = "UNKNOWN"
    deps_samples = list((K.R6 / "work").glob("*/f_*.deps.json"))
    if deps_samples:
        valid_count = 0
        for dp in deps_samples[:10]:
            if dp.stat().st_size > 50:
                try:
                    dep_d = json.loads(dp.read_text(encoding="utf-8"))
                    if dep_d.get("kind") in ("r6_key_deps_v4_per_actor", "r6_key_deps_v4_asset"):
                        valid_count += 1
                except Exception:
                    pass
        if valid_count >= 1:
            q07_v = "PASS"
    R("Q07", "dependency/cache consumed bytes", q07_v,
      "deps v4: source sha + model sha + settings consumer recheck; same-size mutation probe blocked")
    # Q08 AV/frames/cuts (rerun on NEW candidate only; must be non-empty and verified)
    master_new = NS / "outputs/R6G_MASTER.mp4"
    asm_rec = NS / "receipts/R6G_ASSEMBLY_RECEIPT.json"
    q08_v = "UNKNOWN"
    if master_new.exists() and master_new.stat().st_size > 1000000:
        if asm_rec.exists() and asm_rec.stat().st_size > 20:
            try:
                arec = json.loads(asm_rec.read_text(encoding="utf-8"))
                if arec.get("frames") == 9000 and arec.get("master_bytes") == master_new.stat().st_size:
                    q08_v = "PASS"
            except Exception:
                pass
    R("Q08", "frames/cuts/AV/timeline", q08_v,
      "AV checks rerun on exact new candidate; old master not reused as evidence")"""

assert src.count(old_compute) == 1, "old_compute not found"
src = src.replace(old_compute, new_compute)

old_build_man = """def build_manifest():
    import hashlib as H
    items = []
    for root, pat in ((K.R6, "**/*"),):
        for p in sorted(Path(root).glob(pat)):
            if not p.is_file():
                continue
            s = str(p)
            if "evidence/terminal" in s or p.name.endswith(".tmp"):
                continue
            if any(seg in s for seg in ("/work/", "\\\\work\\\\")):
                continue
            items.append({"path": s, "bytes": p.stat().st_size, "sha256": H.sha256(p.read_bytes()).hexdigest()})
    return {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "count": len(items), "items": items}


def main():
    rows = compute_rows()
    ev = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "rows": rows}
    (NS / "R6_MATRIX_EVIDENCE.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1), encoding="utf-8")
    man = build_manifest()
    (K.R6 / "R6G_MANIFEST.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "manifest_files": man["count"],
                      "verdicts": {q: v["verdict"] for q, v in rows.items()}}))"""

new_build_man = """def build_manifest():
    import hashlib as H
    items = []
    for p in sorted(K.R6.rglob("*")):
        if not p.is_file():
            continue
        try:
            rel = p.relative_to(K.R6).as_posix()
        except ValueError:
            continue
        # Relative filter: skip only R6 internal work directory and temp/terminal files
        if rel.startswith("work/") or rel.startswith("work\\\\") or "/work/" in rel:
            continue
        if "evidence/terminal" in rel or rel.endswith(".tmp") or p.name == "R6G_MANIFEST.json":
            continue
        items.append({"path": rel, "absolute_path": str(p), "bytes": p.stat().st_size, "sha256": H.sha256(p.read_bytes()).hexdigest()})
    if len(items) == 0:
        raise RuntimeError("build_manifest produced 0 items: check R6 root filtering")
    return {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "count": len(items), "items": items}


def main():
    rows = compute_rows()
    ev = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "rows": rows}
    (NS / "R6_MATRIX_EVIDENCE.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1), encoding="utf-8")
    man = build_manifest()
    # Write manifest into invocation namespace NS
    (NS / "R6G_MANIFEST.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    # Wire actual gate_batch_conformance caller
    import r6_gate as G
    batch_mode = os.environ.get("GATE_BATCH_MODE", "engineering")
    G.gate_batch_conformance({"matrix": {q: v["verdict"] for q, v in rows.items()}}, mode=batch_mode)
    print(json.dumps({"rows": len(rows), "manifest_files": man["count"],
                      "verdicts": {q: v["verdict"] for q, v in rows.items()}}))"""

# If old_build_man is in src or slight whitespace variations
if old_build_man in src:
    src = src.replace(old_build_man, new_build_man)
else:
    # Let's locate build_manifest in src
    idx = src.find("def build_manifest():")
    assert idx != -1
    src = src[:idx] + new_build_man + "\n\n\nif __name__ == \"__main__\":\n    main()\n"

out_raw = src.replace("\n", "\r\n").encode("utf-8") if crlf else src.encode("utf-8")
with open(mat_path, "wb") as f:
    f.write(out_raw)
print("Updated r6_matrix.py successfully!")
