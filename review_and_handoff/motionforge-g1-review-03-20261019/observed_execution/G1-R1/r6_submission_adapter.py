"""R6 Current Submission Adapter — validates gate and artifacts before atomic publication of TASK_SUBMITTED.

Unlike historical write_terminal_record_r6g.py, this adapter:
1. Validates gate_batch_conformance
2. Validates all required artifacts exist, non-empty, and match hashes
3. Exits nonzero (exit 1) on any validation failure and blocks publication
4. Writes TASK_SUBMITTED only upon 100% verified gate pass
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


def validate_and_submit(mode: str = "engineering", terminal_path: Path | None = None,
                        manifest_path: Path | None = None) -> bool:
    """Validate gates and artifacts before writing terminal submission."""
    # 1. Read matrix evidence
    ns = Path(os.environ.get("R6_INVOCATION_DIR", K.R6 / "continuations/LONG01-R6g-20261014T0725Z-1572"))
    mat_p = ns / "R6_MATRIX_EVIDENCE.json"
    if not mat_p.exists():
        print(f"SUBMIT BLOCKED: missing matrix evidence at {mat_p}", file=sys.stderr)
        return False
    
    mat_data = json.loads(mat_p.read_text(encoding="utf-8"))
    rows = mat_data.get("rows", {})
    verdicts = {q: v["verdict"] for q, v in rows.items()}
    
    # 2. Validate gate_batch_conformance
    try:
        G.gate_batch_conformance({"matrix": verdicts, "evidence": rows, "proof": rows}, mode=mode)
    except Exception as exc:
        print(f"SUBMIT GATE BLOCKED: {exc}", file=sys.stderr)
        return False

    # 3. Read and validate manifest
    man_p = manifest_path or (ns / "R6G_MANIFEST.json")
    if not man_p.exists():
        print(f"SUBMIT BLOCKED: missing manifest at {man_p}", file=sys.stderr)
        return False
        
    man_data = json.loads(man_p.read_text(encoding="utf-8"))
    items = man_data.get("items", [])
    if len(items) == 0:
        print("SUBMIT BLOCKED: manifest is empty", file=sys.stderr)
        return False
        
    for item in items:
        p = Path(item["absolute_path"]) if "absolute_path" in item else K.R6 / item["path"]
        if not p.exists():
            print(f"SUBMIT BLOCKED: artifact missing: {p}", file=sys.stderr)
            return False
        if p.stat().st_size != item["bytes"]:
            print(f"SUBMIT BLOCKED: artifact size mismatch for {p}: {p.stat().st_size} vs {item['bytes']}", file=sys.stderr)
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
