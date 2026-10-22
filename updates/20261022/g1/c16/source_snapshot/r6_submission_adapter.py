"""R6 Current Submission Adapter — validates gate and artifacts before atomic publication of TASK_SUBMITTED.

Features:
1. Recomputes SHA-256 for every manifest artifact (blocks same-size tamper ABCD -> WXYZ)
2. Classifies and wires artifacts list into gate_batch_conformance (supports final mode)
3. Validates gate_batch_conformance with genuine supporting proof
4. Exits nonzero (exit 1) on any validation failure and blocks publication
5. Writes TASK_SUBMITTED only upon 100% verified gate and artifact pass
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = Path("C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long")
R6 = RUN / "tasks/MF-DEMO-LONG-01/corrections/identity5m_20261008/r6"
sys.path.insert(0, str(R6 / "scripts"))
import r6_common as K  # noqa: E402
import r6_gate as G  # noqa: E402


def sha256_file(path: Path | str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def validate_and_submit(mode: str = "engineering", terminal_path: Path | None = None,
                        manifest_path: Path | None = None) -> bool:
    """Validate gates and artifacts before writing terminal submission."""
    ns = Path(os.environ.get("R6_INVOCATION_DIR", K.R6 / "continuations/LONG01-R6g-20261014T0725Z-1572"))
    
    # 1. Read matrix evidence
    mat_p = ns / "R6_MATRIX_EVIDENCE.json"
    if not mat_p.exists():
        print(f"SUBMIT BLOCKED: missing matrix evidence at {mat_p}", file=sys.stderr)
        return False
    
    mat_data = json.loads(mat_p.read_text(encoding="utf-8"))
    rows = mat_data.get("rows", {})
    verdicts = {}
    for i in range(1, 13):
        q = f"Q{i:02d}"
        if q in rows and isinstance(rows[q], dict) and "verdict" in rows[q]:
            verdicts[q] = rows[q]["verdict"]
        else:
            verdicts[q] = "UNKNOWN"
            
    proof = {q: v.get("proof", {}) for q, v in rows.items() if isinstance(v, dict) and "proof" in v}
    
    # 2. Read and validate manifest
    man_p = manifest_path or (ns / "R6G_MANIFEST.json")
    if not man_p.exists():
        print(f"SUBMIT BLOCKED: missing manifest at {man_p}", file=sys.stderr)
        return False
        
    man_data = json.loads(man_p.read_text(encoding="utf-8"))
    items = man_data.get("items", [])
    if len(items) == 0:
        print("SUBMIT BLOCKED: manifest is empty", file=sys.stderr)
        return False
        
    artifacts_list = []
    for item in items:
        p = Path(item["absolute_path"]) if "absolute_path" in item else K.R6 / item["path"]
        if not p.exists():
            print(f"SUBMIT BLOCKED: artifact missing: {p}", file=sys.stderr)
            return False
        if p.stat().st_size != item["bytes"]:
            print(f"SUBMIT BLOCKED: artifact size mismatch for {p}: {p.stat().st_size} vs {item['bytes']}", file=sys.stderr)
            return False
            
        # Recompute SHA-256 for all items (blocks same-size tamper)
        actual_sha = sha256_file(p)
        if actual_sha != item["sha256"]:
            print(f"SUBMIT BLOCKED: artifact hash mismatch for {p}: {actual_sha} vs {item['sha256']}", file=sys.stderr)
            return False
            
        # Classify kind for final gate compatibility
        kind = item.get("kind")
        if not kind or kind == "other":
            name_lower = p.name.lower()
            rel_lower = str(item.get("path", "")).lower()
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
        artifacts_list.append({"kind": kind, "path": str(p), "sha256": item["sha256"]})

    # 3. Validate gate_batch_conformance with wired artifacts and proof
    try:
        G.gate_batch_conformance({
            "invocation_id": ns.name,
            "invocation_dir": str(ns.resolve()),
            "matrix": verdicts,
            "evidence": rows,
            "proof": proof,
            "artifacts": artifacts_list
        }, mode=mode)
    except Exception as exc:
        print(f"SUBMIT GATE BLOCKED: {exc}", file=sys.stderr)
        return False

    # 4. Atomic terminal write
    if terminal_path:
        terminal_record = {
            "schema_version": "1.0",
            "run_id": "20261005T1643Z-wan-long",
            "task_id": "MF-DEMO-LONG-01",
            "revision": "r6",
            "invocation_id": ns.name,
            "status": "TASK_SUBMITTED",
            "mode": mode,
            "matrix": verdicts,
            "manifest": str(man_p),
            "manifest_items_count": len(items),
            "gate_batch_conformance": True,
            "at": man_data.get("at")
        }
        tmp_p = terminal_path.with_name(terminal_path.name + ".tmp")
        tmp_p.write_text(json.dumps(terminal_record, indent=2), encoding="utf-8")
        tmp_p.replace(terminal_path)
        print(f"RECORD_OK: {terminal_path.name} | status TASK_SUBMITTED | gate=PASS")
        
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--submitted", action="store_true", help="Submit task if gate passes")
    ap.add_argument("--verify", action="store_true", help="Verify gate and artifacts without publishing")
    ap.add_argument("--mode", default="engineering", choices=["engineering", "final"], help="Batch mode")
    ap.add_argument("--terminal", type=str, default=None, help="Terminal path to write")
    args = ap.parse_args()

    term_p = Path(args.terminal) if args.terminal else None
    if args.submitted and not term_p:
        ns = Path(os.environ.get("R6_INVOCATION_DIR", K.R6 / "continuations/LONG01-R6g-20261014T0725Z-1572"))
        term_p = ns / "evidence/terminal/terminal_submission.json"
        term_p.parent.mkdir(parents=True, exist_ok=True)

    ok = validate_and_submit(mode=args.mode, terminal_path=term_p if args.submitted else None)
    if not ok:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
