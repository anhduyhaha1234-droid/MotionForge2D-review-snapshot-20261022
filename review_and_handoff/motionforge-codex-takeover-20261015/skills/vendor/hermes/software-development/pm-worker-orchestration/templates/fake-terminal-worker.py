#!/usr/bin/env python
"""Fake TERMINAL worker for structured-terminal consumer tests (starter template).

Wire it as the child command through the dispatcher's argv-prefix override so the
REAL dispatcher runs against a temp scaffold without touching the real CLI:

    DISPATCH_TEST=1
    MF_RUN_ROOT=<scaffold>                     # root override in dispatcher/heartbeat
    DISPATCH_HERMES_ARGV_PREFIX='["<python>","<path to this file>"]'
    FAKE_MODE=<mode>  FAKE_ALLOWED_ROOT=<scaffold>/<allowed_root>  [FAKE_EXIT=N]

It parses the binding (invocation id, packet sha256, resume sid) OUT OF THE PROMPT
exactly like a real worker would, then writes a mode-driven terminal record with
atomic publication (tmp + os.replace).

Modes: ok_continue | future_pass | quoted | ok_submitted | prose_only | truncated |
       dupkeys | wrong_owner | wrong_invocation | wrong_packet | missing_artifact |
       matrix_mismatch | api_error | empty_cont

Expected consumer results (see references/structured-terminal-contract.md):
  ok_continue -> CONTINUE_REQUIRED / PENDING_SAME_OWNER_CONTINUATION
  ok_submitted -> TASK_SUBMITTED / VERIFIABLE_SUBMISSION_PENDING_MANAGER_QA
  every other mode -> NEEDS_RECONCILIATION
Fill RUN_ID / TASK_ID / REVISION with your run's constants before use.
"""
import hashlib
import json
import os
import re
import sys
from pathlib import Path

RUN_ID = "REPLACE_run_id"
TASK_ID = "REPLACE_task_id"
REVISION = "REPLACE_revision"

argv = sys.argv[1:]
prompt = argv[2] if len(argv) > 2 else ""          # child argv: [python, file, "chat", "-q", PROMPT, ...]
inv = (re.search(r"Invocation ID:\s*(\S+)", prompt) or [None, None])[1]
psha = (re.search(r"Packet SHA256:\s*([0-9a-f]{64})", prompt) or [None, None])[1]
sid = argv[argv.index("--resume") + 1] if "--resume" in argv else None
mode = os.environ.get("FAKE_MODE", "ok_continue")
exit_code = int(os.environ.get("FAKE_EXIT", "0"))
root = Path(os.environ["FAKE_ALLOWED_ROOT"])
tdir = root / "evidence" / "terminal"
tdir.mkdir(parents=True, exist_ok=True)
print("[fake] mode=%s inv=%s sid=%s" % (mode, inv, sid))

if mode == "future_pass":
    print("Plan: after all gates -> SELF_REVIEW_PASS_PENDING_CODEX; earlier PASS claim retracted.")
if mode == "quoted":
    print('plan says "PASS" but we are NOT PASS; remain open.')
if mode == "api_error":
    print("API call failed after 3 retries: HTTP 503 Service Unavailable")
if mode in ("ok_continue", "prose_only"):
    print("CONTINUE_REQUIRED - next action: fixture step; resume SID %s" % sid)
if mode == "prose_only":
    sys.exit(exit_code)                             # deliberately NO record

matrix = {("Q%02d" % i): "PASS" for i in range(1, 13)}
rec = {"run_id": RUN_ID, "task_id": TASK_ID, "revision": REVISION, "owner_sid": sid or "new",
       "invocation_id": inv, "packet_sha256": psha, "schema_version": "1.0",
       "status": "CONTINUE_REQUIRED", "reason": "fixture " + mode,
       "remaining_work": ["fixture step"], "artifacts": [], "matrix": {}}


def sha_file(p):
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def build_artifacts(matrix_content, absent_one=False):
    out = []
    for kind in ("master", "comparison", "checkpoint", "receipts"):
        p = root / (kind + ".fixture")
        if absent_one and kind == "master":
            p = root / "absent_master.bin"          # non-existent ON PURPOSE
        else:
            p.write_text(kind + ": synthetic fixture", encoding="utf-8")
        out.append({"kind": kind, "path": str(p), "sha256": sha_file(p) if p.exists() else "0" * 64})
    pm = root / "matrix.fixture.json"
    pm.write_text(json.dumps({"rows": matrix_content}), encoding="utf-8")
    out.append({"kind": "matrix", "path": str(pm), "sha256": sha_file(pm)})
    return out


if mode == "ok_submitted":
    rec.update(status="TASK_SUBMITTED", remaining_work=[], artifacts=build_artifacts(matrix), matrix=matrix)
elif mode == "missing_artifact":
    rec.update(status="TASK_SUBMITTED", remaining_work=[], artifacts=build_artifacts(matrix, True), matrix=matrix)
elif mode == "matrix_mismatch":
    bad = dict(matrix)
    bad["Q01"] = "FAIL"
    rec.update(status="TASK_SUBMITTED", remaining_work=[], artifacts=build_artifacts(bad), matrix=matrix)
elif mode == "wrong_owner":
    rec["owner_sid"] = "other-owner"
elif mode == "wrong_invocation":
    rec["invocation_id"] = "stale-old-invocation"
elif mode == "wrong_packet":
    rec["packet_sha256"] = "b" * 64
elif mode == "empty_cont":
    rec["remaining_work"] = []

text = json.dumps(rec, indent=1)
if mode == "truncated":
    text = '{"status":'
elif mode == "dupkeys":
    text = json.dumps(rec)[:-1] + ',"status":"CONTINUE_REQUIRED"}'
tp = tdir / (inv + ".json")
tmp = tp.with_name(tp.name + ".tmp")
tmp.write_text(text, encoding="utf-8")
os.replace(tmp, tp)
print("[fake] terminal written: %s" % tp)
sys.exit(exit_code)
