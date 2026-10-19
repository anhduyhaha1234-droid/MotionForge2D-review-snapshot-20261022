# -*- coding: utf-8 -*-
"""R4 lease-vs-detached-runner probe (Manager). Uses the ACTUAL invocation_runtime
functions: a live `-B ... r4_build_*.py` runner must keep the GPU lease from being
released; once the runner is gone (and queue quiet) the lease releases cleanly.

Writes manager/evidence/r4/R4_LEASE_RUNNER_PROBE.json.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
RUN = TOOLS.parents[1]
EV = RUN / "manager" / "evidence" / "r4"
sys.path.insert(0, str(TOOLS))
os.environ.pop("MF_RUN_ROOT", None)  # use the real RUN root (lease dir under manager/leases)

import invocation_runtime as ir  # noqa: E402

TMP = Path(r"C:/Users/Admin/AppData/Local/Temp/mf_r4_lease_probe")
TMP.mkdir(parents=True, exist_ok=True)
runner_py = TMP / "r4_build_probe_runner.py"
runner_py.write_text("import time\ntime.sleep(120)\n", encoding="utf-8")

results = []
def rec(name, ok, detail):
    results.append({"name": name, "pass": bool(ok), "detail": detail})
    print(("[PASS] " if ok else "[FAIL] ") + name + " :: " + str(detail)[:180])

inv = "PROBE-LEASE-RUNNER"
lease_path = ir.leases_dir() / ("gpu_lease.%s.json" % inv)
proc = None
try:
    # baseline: quiet with no runner
    q0, d0 = ir.probe_render_quiet()
    rec("baseline_quiet", q0 is True, {"quiet": q0, "detail": d0})

    # lease with NO children; then start a detached-ish runner named r4_build_*
    ir.lease_acquire(inv, job="probe", owner_sid="probe", children=[])
    proc = subprocess.Popen([sys.executable, "-B", str(runner_py)])
    time.sleep(2.0)
    r1 = ir.lease_release_if_children_gone(inv, context="probe_runner_alive")
    rec("release_blocked_by_runner", (r1.get("released") is False and r1.get("reason") == "render active"),
        r1)
    spent = json.loads(lease_path.read_text(encoding="utf-8"))
    rec("lease_marked_detached", spent.get("detached") is True and spent.get("status") == "ACTIVE",
        {"detached": spent.get("detached"), "status": spent.get("status")})

    # stop runner -> release must succeed with quiet machine
    proc.kill(); proc.wait(timeout=30); proc = None
    time.sleep(1.5)
    r2 = ir.lease_release_if_children_gone(inv, context="probe_runner_gone")
    rec("released_after_runner_gone", r2.get("released") is True, r2)
finally:
    if proc is not None:
        try:
            proc.kill(); proc.wait(timeout=15)
        except Exception:
            pass

passed = sum(1 for r in results if r["pass"])
out = {"at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
       "scope": "ACTUAL invocation_runtime functions; detached r4_build_* runner keeps GPU lease; queue+runner quiet releases",
       "passed": passed, "total": len(results), "results": results}
(EV / "R4_LEASE_RUNNER_PROBE.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps({"passed": passed, "total": len(results), "evidence": str(EV / "R4_LEASE_RUNNER_PROBE.json")}))
raise SystemExit(0 if passed == len(results) else 1)
