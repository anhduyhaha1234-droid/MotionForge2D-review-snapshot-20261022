"""Stall/terminal monitor for a long-running worker invocation (template).

Copy, set the CONFIG block, run via `terminal(background=true, notify_on_complete=true)`.
Read-only: never kills or writes anything.
Silent while healthy; exits WITH A NOTIFY when:
  0  WORKER_GONE  - worker process disappeared (go verify the terminal + resume/verify flow)
  2  STALL_ALERT  - alive but no log growth AND no secondary progress AND empty queue, twice in a row
  3  MONITOR_CAP  - hard cap reached (safety)
Key idea (2026-10-08 lesson): a quiet LOG during a long render is normal — a stall is only
declared when log growth, secondary-dir mtimes (outputs/receipts/evidence) and the render queue
are ALL silent. Detached renders run independently of the LLM: on WORKER_GONE, first check
whether the last action actually took effect (processes, queue, new files) before re-dispatching.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

# ---- CONFIG (edit these; Windows-native paths for Windows hosts) ----
WORKER_PID = 0            # exact pid recorded in the dispatch ledger (child_spawned)
LOG = r"C:/path/to/worker.log"
SECONDARY_DIRS = [        # dirs whose newest mtime proves real work (outputs/receipts/evidence)
    r"C:/path/to/outputs",
    r"C:/path/to/receipts",
]
QUEUE_URL = "http://127.0.0.1:8188/queue"   # render queue (or any heartbeat endpoint)
STALL_S = 480             # 8 min of total silence => stall candidate (2 hits in a row => alert)
CHECK_S = 180
MAX_S = 7 * 3600
# ----------------------------------------------------------------------


def child_alive():
    try:
        r = subprocess.run(["wmic", "process", "where", "ProcessId=%d" % WORKER_PID,
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
    for base in SECONDARY_DIRS:
        for root, _dirs, files in os.walk(base):
            for f in files:
                try:
                    newest = max(newest, os.path.getmtime(os.path.join(root, f)))
                except OSError:
                    pass
    try:
        with urllib.request.urlopen(QUEUE_URL, timeout=8) as r:
            qd = json.loads(r.read().decode())
        qrun = len(qd.get("queue_running") or [])
    except Exception:
        qrun = None
    return newest, qrun


T0 = time.time()
prev_size, prev_newest = log_size(), 0.0
last_growth, stall_hits = time.time(), 0

while time.time() - T0 < MAX_S:
    time.sleep(CHECK_S)
    alive, size = child_alive(), log_size()
    newest, qrun = secondary_progress()
    if size > prev_size or newest > prev_newest + 1 or (qrun or 0) > 0:
        last_growth, stall_hits = time.time(), 0
    else:
        since = time.time() - last_growth
        if alive and since >= STALL_S:
            stall_hits += 1
            if stall_hits >= 2:
                print(json.dumps({"status": "STALL_ALERT", "since_growth_s": int(since),
                                  "log_bytes": size, "queue_running": qrun}, ensure_ascii=False))
                sys.exit(2)
    if alive is False:
        print(json.dumps({"status": "WORKER_GONE", "log_bytes": size,
                          "note": "check if the last detached action took effect BEFORE resuming"},
                         ensure_ascii=False))
        sys.exit(0)
    prev_size, prev_newest = size, newest

print(json.dumps({"status": "MONITOR_CAP", "log_bytes": log_size()}, ensure_ascii=False))
sys.exit(3)
