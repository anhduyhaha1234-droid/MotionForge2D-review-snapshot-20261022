#!/usr/bin/env python
"""Prove the GPU lease survives a live detached batch runner (measured pattern, 2026-10-11).

Runs the REAL invocation_runtime functions from a tools dir against an ISOLATED run root
(never a live run):

    python scripts/lease-runner-probe.py --tools-dir <run>/manager/tools [--run-root <tmp>]

Cases (exit 0 only if all pass; JSON summary on stdout):
  1. baseline: Comfy queue + runner scan both quiet.
  2. lease with NO children + a live `-B <tmp>/r4_build_probe_runner.py` => release is
     BLOCKED. Reason is `render active` with a live Comfy server, or `render probe unknown`
     when no Comfy server is reachable -- BOTH fail closed (released=False) and the lease
     must stay ACTIVE with detached=true.
  3. runner killed => release succeeds (`released: true`).

Notes:
- Requires a Comfy /queue endpoint at 127.0.0.1:8188 for the quiet baseline (case 1) and
  for case 3's `released:true`; a machine without Comfy will fail cases 1 and 3 by design
  (fail-closed). Run it where the render server actually lives.
- The runner name `r4_build_probe_runner.py` is deliberate: it must match the lease watch
  list (`p4_wan_run* / wan_run* / render_run* / r4_render* / r4_build*`) that workers are
  instructed to name their batch launchers with.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tools-dir", required=True, help="dir containing invocation_runtime.py")
    ap.add_argument("--run-root", default=None, help="isolated run root (default: fresh temp dir)")
    a = ap.parse_args()

    root = Path(a.run_root) if a.run_root else Path(tempfile.mkdtemp(prefix="mf_lease_probe_"))
    os.environ["MF_RUN_ROOT"] = str(root)

    spec = importlib.util.spec_from_file_location(
        "invocation_runtime", Path(a.tools_dir) / "invocation_runtime.py")
    ir = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ir)

    runner = root / "r4_build_probe_runner.py"
    runner.write_text("import time\ntime.sleep(120)\n", encoding="utf-8")

    results = []

    def rec(name, ok, detail):
        results.append({"name": name, "pass": bool(ok), "detail": detail})
        print(("[PASS] " if ok else "[FAIL] ") + name + " :: " + json.dumps(detail)[:200])

    inv = "PROBE-LEASE-RUNNER"
    proc = None
    try:
        q0, d0 = ir.probe_render_quiet()
        rec("baseline_quiet", q0 is True, {"quiet": q0, "detail": d0})

        ir.lease_acquire(inv, job="probe", owner_sid="probe", children=[])
        proc = subprocess.Popen([sys.executable, "-B", str(runner)])
        time.sleep(2.0)

        r1 = ir.lease_release_if_children_gone(inv, context="probe_runner_alive")
        rec("release_blocked_by_runner",
            r1.get("released") is False and r1.get("reason") in ("render active", "render probe unknown"),
            r1)

        lease = json.loads((ir.leases_dir() / ("gpu_lease.%s.json" % inv)).read_text(encoding="utf-8"))
        rec("lease_stays_active_detached",
            lease.get("status") == "ACTIVE" and lease.get("detached") is True,
            {"status": lease.get("status"), "detached": lease.get("detached")})

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
    print(json.dumps({"passed": passed, "total": len(results), "run_root": str(root)}))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
