#!/usr/bin/env python
"""Reconcile an append-only dispatch ledger against the receipts on disk.

Generalised from the MF2D CMC-correction round (2026-09-29). Catches the three
silent defect classes of a hand-appended dispatch ledger:

  1. duplicate dispatch rows for one round (backfill re-append);
  2. a dispatch whose receipt file does not exist (launcher died pre-write);
  3. rounds paired by receipt path, so a re-dispatch under the same receipt name
     is visible instead of silently overwriting round one's identity.

usage:
    python reconcile_dispatch_ledger.py <run_root> [--emit]

Expected layout under <run_root>:
    ledgers/dispatch-ledger.jsonl      rows with action in {dispatch, exit}
    manager/receipts/*.json            one receipt per dispatch

Ledger row fields consumed: action, task_id, receipt, log, utc_start, at_utc,
resume_session_requested, model, cwd, packet_sha256, packet_bytes, exit_code.

--emit writes ledgers/dispatch-ledger.reconciled.jsonl and
manager/DISPATCH_RECONCILIATION.md. Run WITHOUT --emit first and read the
counters; only emit once the numbers make sense.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    run = Path(sys.argv[1])
    ledger = run / "ledgers" / "dispatch-ledger.jsonl"
    if not ledger.is_file():
        print(f"REFUSED: no ledger at {ledger}")
        return 2

    rows = [json.loads(ln) for ln in ledger.read_text(encoding="utf-8").splitlines() if ln.strip()]
    dispatches = [r for r in rows if r.get("action") == "dispatch"]
    exits = [r for r in rows if r.get("action") == "exit"]

    pairs = []
    for d in dispatches:
        m = [e for e in exits if e.get("receipt") == d.get("receipt")]
        pairs.append({
            "task_id": d.get("task_id"),
            "utc_start": d.get("utc_start") or d.get("at_utc"),
            "resume_session_requested": d.get("resume_session_requested"),
            "model": d.get("model"),
            "cwd": d.get("cwd"),
            "receipt": d.get("receipt"),
            "log": d.get("log"),
            "packet_sha256": d.get("packet_sha256"),
            "packet_bytes": d.get("packet_bytes"),
            "utc_end": m[0].get("at_utc") if m else None,
            "exit_code": m[0].get("exit_code") if m else None,
            "outcome": "EXITED" if m else "STILL_RUNNING_OR_KILLED",
            "receipt_exists": bool(d.get("receipt") and Path(str(d["receipt"])).is_file()),
        })

    dupes = {f"{k[0]} :: {k[1]}": v
             for k, v in Counter((p["task_id"], p["receipt"]) for p in pairs).items() if v > 1}
    missing = [p for p in pairs if not p["receipt_exists"]]
    running = [p for p in pairs if p["outcome"] != "EXITED"]
    receipts_dir = run / "manager" / "receipts"
    on_disk = len(list(receipts_dir.glob("*.json"))) if receipts_dir.is_dir() else 0

    report = {
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "ledger": ledger.as_posix(),
        "rows_total": len(rows),
        "dispatches": len(dispatches),
        "exits": len(exits),
        "receipt_files_on_disk": on_disk,
        "duplicate_dispatch_rows": dupes,
        "dispatches_missing_receipt": [p["task_id"] for p in missing],
        "not_yet_exited": [{"task_id": p["task_id"], "started": p["utc_start"]} for p in running],
    }

    if "--emit" in sys.argv:
        # Every sentence below is DERIVED from the reconciled rows. Do not add
        # narrative recollections here: an incident that died before the launcher's
        # append has NO row, and claiming one in the note is a fabricated record.
        out = run / "ledgers" / "dispatch-ledger.reconciled.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(json.dumps(p, ensure_ascii=False, sort_keys=True)
                                 for p in pairs) + "\n", encoding="utf-8")
        note = run / "manager" / "DISPATCH_RECONCILIATION.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(
            "# Dispatch ledger reconciliation\n\n"
            f"Generated {report['at_utc']} from `{ledger.as_posix()}`.\n\n"
            "| metric | value |\n|---|---|\n"
            f"| rows in append-only ledger | {report['rows_total']} |\n"
            f"| dispatch rows | {report['dispatches']} |\n"
            f"| exit rows | {report['exits']} |\n"
            f"| receipt files on disk | {report['receipt_files_on_disk']} |\n"
            f"| duplicate dispatch rows | {len(dupes)} |\n"
            f"| dispatches missing a receipt | {len(missing)} |\n"
            f"| dispatches not yet exited | {len(running)} |\n\n"
            "A row appears here only if it exists in the ledger. A launch that died\n"
            "before the ledger append has no row by construction; describe such an\n"
            "incident in the incident narrative, never in this table.\n\n"
            + "\n".join(
                f"- `{p['task_id']}` start={p['utc_start']} exit={p['exit_code']} "
                f"resume={p['resume_session_requested']} receipt_on_disk={p['receipt_exists']}"
                for p in pairs) + "\n",
            encoding="utf-8")
        print(f"emitted {out} and {note}")

    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
