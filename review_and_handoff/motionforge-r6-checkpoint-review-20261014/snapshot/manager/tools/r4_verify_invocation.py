# -*- coding: utf-8 -*-
"""R4 Manager post-invocation verification: re-validate a terminal record from bytes.

usage: r4_verify_invocation.py --invocation <id> --receipt <receipt.json> --out <verify.json>
Exit 0 iff decision is one of the four contract actions AND every artifact hash recomputes.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from terminal_contract import Binding, validate_result  # noqa: E402


def sha256f(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--invocation", required=True)
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    receipt = json.loads(Path(a.receipt).read_text(encoding="utf-8"))
    root = Path(receipt["allowed_root"])
    record_path = root / "evidence" / "terminal" / (a.invocation + ".json")
    binding = Binding(run_id=receipt["run_id"], task_id=receipt["task_id"], revision=receipt["revision"],
                      owner_sid=receipt["owner_sid"], invocation_id=receipt["invocation_id"],
                      packet_sha256=receipt["packet_file_sha256"])
    verdict = validate_result(record_path, binding, root, invocation_terminal=True,
                              exit_code=receipt.get("exit_code"), infrastructure_error=False)
    artifact_check = []
    if record_path.exists():
        rec = json.loads(record_path.read_text(encoding="utf-8"))
        for art in rec.get("artifacts", []):
            p = Path(art["path"])
            got = sha256f(p) if p.is_file() else None
            artifact_check.append({"kind": art["kind"], "file": p.name,
                                   "hash_ok": got == art["sha256"], "exists": p.is_file()})
    out = {
        "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "invocation_id": a.invocation,
        "record_file": str(record_path),
        "record_sha256": sha256f(record_path) if record_path.exists() else None,
        "decision": verdict.get("decision"),
        "error": verdict.get("error"),
        "status": (verdict.get("result") or {}).get("status"),
        "artifacts_recheck": artifact_check,
        "all_artifact_hashes_ok": bool(artifact_check) and all(x["hash_ok"] for x in artifact_check),
        "receipt_utc_start": receipt.get("utc_start"), "receipt_utc_end": receipt.get("utc_end"),
        "receipt_exit_code": receipt.get("exit_code"),
    }
    Path(a.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("decision", "status", "all_artifact_hashes_ok", "error")}, indent=1))
    ok = verdict.get("decision") in ("PENDING_SAME_OWNER_CONTINUATION", "VERIFIABLE_SUBMISSION_PENDING_MANAGER_QA",
                                     "VERIFY_USER_STOP_AUTHORITY", "VERIFY_EXTERNAL_BLOCKER") and out["all_artifact_hashes_ok"]
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
