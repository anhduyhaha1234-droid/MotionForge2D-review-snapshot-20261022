"""Monitor C2: detect LLM-checkpoint silence (>20 min while alive) and worker terminal.

- checks every 180s
- exit 0 (notify): worker 39104 gone -> verify terminal (receipt C2 + log tail)
- exit 2 (notify): worker alive but worker_C2.log silent >= 20 min sustained 2 checks
  (C1#1 lesson: detached renders keep disk growing, masking LLM stalls; this timer
  watches the LOG ONLY, so we can intervene BEFORE the harness 60-min stall-kill)
- exit 3: cap 4h. Read-only; never kills/writes.
"""
import json
import os
import subprocess
import sys
import time

M = r"C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long"
D = M + "/tasks/MF-DEMO-LONG-01"
LOG = D + "/worker_C2.log"
CHILD_PID = 39104
T0 = time.time()
MAX_S = 4 * 3600
SILENT_S = 1200
CHECK_S = 180


def child_alive():
    try:
        r = subprocess.run(["wmic", "process", "where", "ProcessId=%d" % CHILD_PID,
                            "get", "ProcessId", "/format:list"],
                           capture_output=True, text=True, errors="replace", timeout=60)
        return "ProcessId=" in (r.stdout or "")
    except Exception:
        return None


def log_size():
    try:
        return os.path.getsize(LOG)
    except OSError:
        return -1


prev = log_size()
last_growth = time.time()
hits = 0

while time.time() - T0 < MAX_S:
    time.sleep(CHECK_S)
    alive = child_alive()
    size = log_size()
    if size > prev:
        last_growth = time.time()
        hits = 0
    prev = size
    if alive is False:
        print(json.dumps({"status": "WORKER_GONE", "log_bytes": size,
                          "elapsed_s": int(time.time() - T0)}, ensure_ascii=False))
        sys.exit(0)
    silent = time.time() - last_growth
    if alive and silent >= SILENT_S:
        hits += 1
        if hits >= 2:
            print(json.dumps({"status": "LLM_SILENT_20M", "silent_s": int(silent),
                              "log_bytes": size, "elapsed_s": int(time.time() - T0),
                              "note": "worker alive but log silent >=20min - audit before 60min stall-kill"},
                             ensure_ascii=False))
            sys.exit(2)
print(json.dumps({"status": "MONITOR_CAP_4H"}, ensure_ascii=False))
sys.exit(3)
