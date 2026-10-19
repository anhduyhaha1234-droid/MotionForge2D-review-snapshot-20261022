# -*- coding: utf-8 -*-
"""R4 heartbeat swap (Manager 2026-10-11): stop the two legacy heartbeat_long.py
processes via the STOP file (identity-verified), keep a census, then report.
The NEW heartbeat is started separately after this script returns."""
import json
import os
import time
from pathlib import Path

import psutil

RUN = Path("C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long")
EV = RUN / "manager/evidence/r4"
STOP = RUN / "manager/HEARTBEAT_STOP"


def census():
    out = []
    for p in psutil.process_iter(["pid", "name", "create_time", "cmdline", "cwd"]):
        try:
            cl = " ".join(p.info["cmdline"] or [])
            if "heartbeat_long.py" in cl:
                out.append({"pid": p.info["pid"], "name": p.info["name"],
                            "create": p.info["create_time"], "cmd": cl[:160],
                            "cwd": p.info.get("cwd")})
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            out.append({"pid": p.pid, "state": "AccessDenied/UNKNOWN"})
    return out


def main():
    before = census()
    rec = {"at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "legacy_heartbeat_census_before": before}
    STOP.write_text("swap to patched heartbeat 2026-10-11\n", encoding="utf-8")
    gone = False
    deadline = time.time() + 260
    while time.time() < deadline:
        time.sleep(6)
        now = census()
        if not now:
            gone = True
            break
    rec["legacy_heartbeat_gone_by_stop_file"] = gone
    rec["waited_s"] = round(260 - (deadline - time.time()), 1)
    if gone:
        STOP.unlink()
        rec["stop_file_removed"] = True
    else:
        rec["stop_file_removed"] = False
        rec["note"] = "legacy heartbeat did not exit; do NOT start a second loop before reconciling"
    (EV / "R4_HEARTBEAT_SWAP.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    print(json.dumps(rec, indent=1))
    return 0 if gone else 1


if __name__ == "__main__":
    raise SystemExit(main())
