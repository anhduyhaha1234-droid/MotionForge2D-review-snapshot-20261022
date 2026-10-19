"""Monitor C1 invocation: worker terminal / stall detection (Manager harness, read-only).

Loop every ~180s:
- worker child (pid 44260) alive?
- worker_C1.log size growing?
- secondary signals: comfy queue, outputs/receipts mtime growth
Exit 0 (notify): worker gone  -> invite Manager to verify terminal.
Exit 2 (notify): STALL - alive but no log growth for >= 8 min AND no secondary progress twice in a row.
Exit 3 (notify): watchdog cap 7h.
Never kills/writes anything.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

M = r"C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long"
D = M + "/tasks/MF-DEMO-LONG-01"
LOG = D + "/worker_C1.log"
CHILD_PID = 44260
T0 = time.time()
MAX_S = 7 * 3600
STALL_S = 480
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


def secondary_progress():
    newest = 0.0
    for sub in ("outputs", "receipts", "scratch", "evidence", "scripts"):
        base = os.path.join(D, "corrections", "identity5m_20261008", sub)
        for root, _dirs, files in os.walk(base):
            for f in files:
                try:
                    newest = max(newest, os.path.getmtime(os.path.join(root, f)))
                except OSError:
                    pass
    q = None
    try:
        with urllib.request.urlopen("http://127.0.0.1:8188/queue", timeout=8) as r:
            qd = json.loads(r.read().decode())
        q = len(qd.get("queue_running") or [])
    except Exception:
        q = None
    return newest, q


prev_size = log_size()
prev_newest = 0.0
last_growth = time.time()
stall_hits = 0

while time.time() - T0 < MAX_S:
    time.sleep(CHECK_S)
    alive = child_alive()
    size = log_size()
    newest, qrun = secondary_progress()
    grew = size > prev_size
    sec_grew = newest > prev_newest + 1
    if grew or sec_grew or (qrun or 0) > 0:
        last_growth = time.time()
        stall_hits = 0
    else:
        since = time.time() - last_growth
        if alive and since >= STALL_S:
            stall_hits += 1
            if stall_hits >= 2:
                print(json.dumps({"status": "STALL_ALERT", "since_growth_s": int(since),
                                  "log_bytes": size, "queue_running": qrun,
                                  "elapsed_s": int(time.time() - T0)}, ensure_ascii=False))
                sys.exit(2)
    if alive is False:
        print(json.dumps({"status": "WORKER_GONE", "log_bytes": size,
                          "elapsed_s": int(time.time() - T0),
                          "note": "verify terminal: receipt C1 + log tail, then Manager resume/verify flow"},
                         ensure_ascii=False))
        sys.exit(0)
    prev_size, prev_newest = size, newest

print(json.dumps({"status": "MONITOR_CAP_7H", "log_bytes": log_size()}, ensure_ascii=False))
sys.exit(3)
