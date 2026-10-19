"""R6 S9 — canonical matrix (Q01–Q12 per U/CORRECTION_MATRIX), evidence-linked, no hardcoded PASS.

Enum: PASS | FAIL | UNKNOWN only. Evidence rows computed from artifacts present in this invocation.
Emits R6_MATRIX_EVIDENCE.json + R6G_MANIFEST.json (recursive; manifest hash AFTER final record).
"""
from __future__ import annotations
import ast
import hashlib
import json
import os
import sys
import time
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

    def R(q, name, verdict, evidence, proof=None):
        assert verdict in ("PASS", "FAIL", "UNKNOWN"), verdict
        rec = {"name": name, "verdict": verdict, "evidence": evidence}
        if proof:
            rec["proof"] = proof
        rows[q] = rec

    # Q01 CAST identity/refs/pose: requires valid decodable image + verified json binding hash & invocation
    ev1 = NS / "evidence/F01_excerpts_strip.png"
    ev1_json = NS / "evidence/F01_excerpts_verified.json"
    q01_v = "UNKNOWN"
    q01_proof = None
    ok_img, _ = EVC.validate_evidence_image(ev1)
    ok_json, v_data, _ = EVC.validate_evidence_json(ev1_json, {"verdict", "shots", "image_sha256", "invocation_id"})
    if ok_img and ok_json and v_data.get("verdict") == "PASS":
        if (v_data.get("image_sha256") == EVC.sha256_file(ev1) and
                v_data.get("invocation_id") == NS.name and
                isinstance(v_data.get("shots"), list) and len(v_data["shots"]) >= 5):
            q01_v = "PASS"
            q01_proof = {"image_sha256": v_data["image_sha256"], "shots": v_data["shots"], "invocation_id": v_data["invocation_id"]}
    R("Q01", "CAST identity/refs/pose", q01_v,
      f"F01 excerpt strip {ev1.name}; S22/S31/S41/S33/S61/S73 windows regen; perturb evidence VACE receipts", proof=q01_proof)

    # Q02 role/count/visibility/ledger
    R("Q02", "role/count/visibility/ledger", "UNKNOWN",
      "ledger rows + class windows; S62 entry/S63/S64 occlusion under re-review")

    # Q03 contact/events
    R("Q03", "contact/events", "UNKNOWN",
      "event-exact keys (F03) + segmented propagate + cotracker windows (F04) in progress")

    # Q04 ghost/props/background
    R("Q04", "ghost/props/background", "UNKNOWN", "S33/S61 portraits + S73 book + S57 car re-render under review")

    # Q05 semantic gate actual consumers: requires verified parseable test file + gate receipt with all_passed, exit_code 0, node_ids
    q05_v = "UNKNOWN"
    q05_proof = None
    test_file = NS / "tests/test_r6g_microfixes.py"
    q05_rec = NS / "receipts/R6_GATE_EVIDENCE.json"
    if test_file.exists() and test_file.stat().st_size > 100:
        try:
            ast.parse(test_file.read_text(encoding="utf-8"))
            test_syntax_ok = True
        except Exception:
            test_syntax_ok = False
        if test_syntax_ok:
            ok_rec, g_data, _ = EVC.validate_evidence_json(q05_rec, {"all_passed", "tests_run", "exit_code", "test_file_sha256", "node_ids"})
            if (ok_rec and g_data.get("all_passed") is True and
                    g_data.get("tests_run", 0) > 0 and g_data.get("exit_code") == 0 and
                    g_data.get("test_file_sha256") == EVC.sha256_file(test_file) and
                    isinstance(g_data.get("node_ids"), list) and len(g_data["node_ids"]) > 0):
                q05_v = "PASS"
                q05_proof = {
                    "exit_code": 0,
                    "tests_run": g_data["tests_run"],
                    "all_passed": True,
                    "test_file_sha256": g_data["test_file_sha256"],
                    "node_ids": g_data["node_ids"]
                }
    R("Q05", "semantic gate actual consumers", q05_v,
      "gate mandatory fields + gate_assemble wired + encoder-spy negative tests", proof=q05_proof)

    # Q06 VACE
    R("Q06", "VACE paired/conformance", "UNKNOWN", "existing 3 trials + TrimVideoLatent; independence check pending")

    # Q07 deps/cache: verify genuine v4 dependency records with full validator
    q07_v = "UNKNOWN"
    q07_proof = None
    deps_samples = list((K.R6 / "work").glob("*/f_*.deps.json"))
    if deps_samples:
        valid_count = 0
        valid_kinds = set()
        for dp in deps_samples[:10]:
            ok_dep, _ = EVC.validate_deps_evidence(dp)
            if ok_dep:
                valid_count += 1
                try:
                    dep_obj = json.loads(dp.read_text(encoding="utf-8"))
                    valid_kinds.add(dep_obj.get("kind", ""))
                except Exception:
                    pass
        if valid_count >= 1:
            q07_v = "PASS"
            q07_proof = {
                "verified_deps_count": valid_count,
                "required_shots": list(K.PLAN.keys()) if hasattr(K, "PLAN") else [],
                "kinds": sorted(valid_kinds)
            }
    R("Q07", "dependency/cache consumed bytes", q07_v,
      "deps v4: source sha + model sha + settings consumer recheck; same-size mutation probe blocked", proof=q07_proof)

    # Q08 AV/frames/cuts (rerun on NEW candidate only; must be valid decodable video via ffprobe)
    master_new = NS / "outputs/R6G_MASTER.mp4"
    asm_rec = NS / "receipts/R6G_ASSEMBLY_RECEIPT.json"
    q08_v = "UNKNOWN"
    q08_proof = None
    ok_vid, _ = EVC.validate_evidence_video(master_new, 9000)
    ok_rec, arec, _ = EVC.validate_evidence_json(asm_rec, {"frames", "master_bytes", "master_sha256"})
    if ok_vid and ok_rec:
        if (arec.get("frames") == 9000 and
                arec.get("master_bytes") == master_new.stat().st_size and
                arec.get("master_sha256") == EVC.sha256_file(master_new)):
            q08_v = "PASS"
            q08_proof = {"master_sha256": arec["master_sha256"], "frames": 9000}
    R("Q08", "frames/cuts/AV/timeline", q08_v,
      "AV checks rerun on exact new candidate; old master not reused as evidence", proof=q08_proof)

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
        if rel.startswith("work/") or rel.startswith("work\\\\") or "/work/" in rel:
            continue
        if "evidence/terminal" in rel or rel.endswith(".tmp") or p.name == "R6G_MANIFEST.json":
            continue
            
        # Classify kind for final gate compatibility
        name_lower = p.name.lower()
        rel_lower = rel.lower()
        if name_lower.endswith(".mp4") and "master" in name_lower:
            kind = "master"
        elif name_lower.endswith(".mp4") and "comparison" in name_lower:
            kind = "comparison"
        elif "matrix" in name_lower or "r6_matrix" in name_lower:
            kind = "matrix"
        elif "checkpoint" in name_lower or "checkpoint" in rel_lower:
            kind = "checkpoint"
        elif "receipt" in rel_lower or name_lower.endswith(".jsonl"):
            kind = "receipts"
        else:
            kind = "other"
            
        items.append({
            "path": rel,
            "absolute_path": str(p),
            "kind": kind,
            "bytes": p.stat().st_size,
            "sha256": H.sha256(p.read_bytes()).hexdigest()
        })
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
