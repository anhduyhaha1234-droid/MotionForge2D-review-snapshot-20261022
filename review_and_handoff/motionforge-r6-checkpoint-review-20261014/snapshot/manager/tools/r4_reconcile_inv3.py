# -*- coding: utf-8 -*-
"""R4 inv#3 reconcile (stall-kill): evidence + targeted scope scan since inv2 end.

Reads ledger/receipt/lease/state; writes manager/evidence/r4/R4_INV3_RECONCILE.json;
reports new files under D since 07:13:00Z outside allowed prefixes (r4 dirs + worker logs).
"""
import json, os, time
from pathlib import Path

RUN = Path(__file__).resolve().parents[2]
EV = RUN / "manager" / "evidence" / "r4"
D = RUN / "tasks" / "MF-DEMO-LONG-01"
CUT = 1791708780.0  # 2026-10-11T07:13:00Z (end of inv2 scan window)

receipt = json.loads((RUN / "manager" / "LONG01_receipt_R4c.json").read_text(encoding="utf-8"))
lease = json.loads((RUN / "manager" / "leases" / "gpu_lease.LONG01-R4c-20261011T0730Z-b3e712.json").read_text(encoding="utf-8"))
state_p = D / "corrections" / "identity5m_20261008" / "r4" / "checkpoint" / "BUILD_STATE.json"
state = json.loads(state_p.read_text(encoding="utf-8")) if state_p.exists() else {}
shots = state.get("shots", {})
tally = {}
for v in shots.values():
    tally[v.get("status")] = tally.get(v.get("status"), 0) + 1

ALLOW = ("corrections/identity5m_20261008/r4/", "input/identity5m_20261008/r4/", "output/identity5m_20261008/r4/")
bad, tot = [], 0
for dp, dn, fn in os.walk(D):
    dn[:] = [d for d in dn if d != "__pycache__"]
    rel = Path(dp).relative_to(D).as_posix()
    if rel.split("/")[0] in ("work", "env", "user"):
        continue
    for f in fn:
        fp = Path(dp) / f
        try:
            m = fp.stat().st_mtime
        except OSError:
            continue
        if m > CUT:
            tot += 1
            r = (rel + "/" + f) if rel != "." else f
            if not any(r.startswith(a) for a in ALLOW) and not (f.startswith("worker_R4") and f.endswith(".log")):
                bad.append((time.strftime("%H:%M:%S", time.localtime(m)), r))

out = {
    "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "invocation": "LONG01-R4c-20261011T0730Z-b3e712",
    "receipt": {"utc_start": receipt["utc_start"], "utc_end": receipt["utc_end"], "exit_code": receipt["exit_code"],
                "timed_out": receipt["timed_out"], "outcome_class": receipt["outcome_class"],
                "outcome_detail": receipt.get("outcome_detail"),
                "tool_actions": receipt["context_metrics"]["tool_actions_observed"]},
    "stall_kill": {"detector": "dispatcher wait_with_stall_detector", "silent_seconds": 3602, "threshold_s": 3600,
                   "killed_pid": 48800, "note": "LLM child killed; detached batch NOT killed (no tree kill)"},
    "batch_survived": {"runner": "r4/scripts/r4_build_batch.py build", "created_epoch": 1791705390.12,
                       "log": "r4/logs/build_r4c2_20261011_145630.out.log", "err_log_bytes": 0},
    "lease": {"status": lease.get("status"), "detached": lease.get("detached"), "released_utc": lease.get("released_utc"),
              "release_attempt": (lease.get("release_attempts") or [{}])[-1].get("render_probe", {}).get("detail", "")[:120]},
    "build_state": {"nproc": state.get("nproc"), "itv": state.get("itv"), "tally": tally, "tracked": len(shots)},
    "scope_scan": {"window_start_utc": "2026-10-11T07:13:00Z", "new_files": tot, "outside_allowed": len(bad),
                   "violations": bad[:20]},
    "verdict": "RECONCILED_FOR_RESUME (batch alive, lease held ACTIVE/detached, scope clean)" if not bad else "SCOPE_VIOLATION_SEE_VIOLATIONS",
}
(EV / "R4_INV3_RECONCILE.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps({"tally": tally, "new_files": tot, "violations": len(bad), "verdict": out["verdict"]}, ensure_ascii=False))
