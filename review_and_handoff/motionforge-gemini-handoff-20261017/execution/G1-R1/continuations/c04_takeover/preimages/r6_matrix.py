"""R6 S9 — canonical matrix (Q01–Q12 per U/CORRECTION_MATRIX), evidence-linked, no hardcoded PASS.

Enum: PASS | FAIL | UNKNOWN only. Evidence rows computed from artifacts present in this invocation.
Emits R6_MATRIX_EVIDENCE.json + R6_MANIFEST.json (recursive; manifest hash AFTER final record).
"""
from __future__ import annotations
import hashlib, json, os, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r6_common as K  # noqa: E402

NS = Path(os.environ.get("R6_INVOCATION_DIR", K.R6 / "continuations/LONG01-R6g-20261014T0725Z-1572"))


def _exists(p):
    return (K.R6 / p).exists() if not str(p).startswith("C:") else Path(p).exists()


def compute_rows() -> dict:
    import r6_evidence_contract as EVC
    rows = {}

    def R(q, name, verdict, evidence):
        assert verdict in ("PASS", "FAIL", "UNKNOWN"), verdict
        rows[q] = {"name": name, "verdict": verdict, "evidence": evidence}

    # Q01 CAST identity/refs/pose: requires valid decodable image + verified json
    ev1 = NS / "evidence/F01_excerpts_strip.png"
    ev1_json = NS / "evidence/F01_excerpts_verified.json"
    q01_v = "UNKNOWN"
    ok_img, _ = EVC.validate_evidence_image(ev1)
    ok_json, v_data, _ = EVC.validate_evidence_json(ev1_json, {"verdict", "shots"})
    if ok_img and ok_json and v_data.get("verdict") == "PASS":
        if isinstance(v_data.get("shots"), list) and len(v_data["shots"]) > 0:
            q01_v = "PASS"
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

    # Q05 semantic gate actual consumers: requires verified test file + gate receipt with all_passed
    q05_v = "UNKNOWN"
    test_file = NS / "tests/test_r6g_microfixes.py"
    q05_rec = NS / "receipts/R6_GATE_EVIDENCE.json"
    if test_file.exists() and test_file.stat().st_size > 100:
        ok_rec, g_data, _ = EVC.validate_evidence_json(q05_rec, {"all_passed"})
        if ok_rec and g_data.get("all_passed") is True and g_data.get("tests_run", 0) > 0:
            q05_v = "PASS"
    R("Q05", "semantic gate actual consumers", q05_v,
      "gate mandatory fields + gate_assemble wired + encoder-spy negative tests")

    # Q06 VACE
    R("Q06", "VACE paired/conformance", "UNKNOWN", "existing 3 trials + TrimVideoLatent; independence check pending")

    # Q07 deps/cache: verify genuine v4 dependency records with full validator
    q07_v = "UNKNOWN"
    deps_samples = list((K.R6 / "work").glob("*/f_*.deps.json"))
    if deps_samples:
        valid_count = 0
        for dp in deps_samples[:10]:
            ok_dep, _ = EVC.validate_deps_evidence(dp)
            if ok_dep:
                valid_count += 1
        if valid_count >= 1:
            q07_v = "PASS"
    R("Q07", "dependency/cache consumed bytes", q07_v,
      "deps v4: source sha + model sha + settings consumer recheck; same-size mutation probe blocked")

    # Q08 AV/frames/cuts (rerun on NEW candidate only; must be valid decodable video)
    master_new = NS / "outputs/R6G_MASTER.mp4"
    asm_rec = NS / "receipts/R6G_ASSEMBLY_RECEIPT.json"
    q08_v = "UNKNOWN"
    ok_vid, _ = EVC.validate_evidence_video(master_new, 9000)
    ok_rec, arec, _ = EVC.validate_evidence_json(asm_rec, {"frames", "master_bytes"})
    if ok_vid and ok_rec:
        if arec.get("frames") == 9000 and arec.get("master_bytes") == master_new.stat().st_size:
            q08_v = "PASS"
    R("Q08", "frames/cuts/AV/timeline", q08_v,
      "AV checks rerun on exact new candidate; old master not reused as evidence")

    # Q09 held-out QA (Manager's, not worker's)
    R("Q09", "Manager held-out QA", "UNKNOWN", "requires Manager independent pass on frozen candidate")

    # Q10 manifest/terminal truth
    R("Q10", "manifest/terminal/checkpoint", "UNKNOWN",
      "new terminal + checkpoint + manifest in namespace; closure after final record")

    # Q11 harness concurrency (manager proof, not rerun)
    R("Q11", "concurrency/lease/dispatch", "UNKNOWN", "Manager 51/51 + race34/34 proofs by hash; not independently rerun")

    # Q12 upstream adoption end-to-end
    R("Q12", "upstream adoption actuality", "UNKNOWN",
      "stitch+trim present; event/contact/end-to-end proof via F03/F04/F05 reruns")

    return rows


def build_manifest():
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
        if rel.startswith("work/") or rel.startswith("work\\") or "/work/" in rel:
            continue
        if "evidence/terminal" in rel or rel.endswith(".tmp") or p.name == "R6G_MANIFEST.json":
            continue
        items.append({"path": rel, "absolute_path": str(p), "bytes": p.stat().st_size, "sha256": H.sha256(p.read_bytes()).hexdigest()})
    if len(items) == 0:
        raise RuntimeError("build_manifest produced 0 items: check R6 root filtering")
    return {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "count": len(items), "items": items}


def main():
    import r6_evidence_contract as EVC
    rows = compute_rows()
    man = build_manifest()
    batch_mode = os.environ.get("GATE_BATCH_MODE", "engineering")
    
    # Atomic stage-validate-publish protocol
    EVC.stage_and_publish_matrix(rows, man, NS, batch_mode=batch_mode)
    print(json.dumps({"rows": len(rows), "manifest_files": man["count"],
                      "verdicts": {q: v["verdict"] for q, v in rows.items()}}))


if __name__ == "__main__":
    main()
