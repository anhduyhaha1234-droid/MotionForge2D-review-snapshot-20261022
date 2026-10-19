"""Wait for the W5 block12 render to settle (Manager harness, read-only).

Settle = comfy queue empty AND no p4_wan_run_v2 process, sustained 2 checks.
Exit 0 with a compact JSON summary (block12 ok-count + missing + runner tail);
exit 2 on 3h timeout. Never kills anything, never writes D.
"""
import json
import re
import subprocess
import sys
import time
import urllib.request

D = r"C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/tasks/MF-DEMO-LONG-01"
LOG = D + "/work/wan_runner_v2.log"
REC = D + "/evidence/WAN_RUNS_R2.jsonl"
CONF = "http://127.0.0.1:8188"
T0 = time.time()
MAX_S = 3 * 3600
BLOCK12 = ["S%04d" % i for i in range(166, 181)]


def queue_empty():
    try:
        with urllib.request.urlopen(CONF + "/queue", timeout=8) as r:
            q = json.loads(r.read().decode())
        return (not q.get("queue_running")) and (not q.get("queue_pending"))
    except Exception:
        return None


def runner_alive():
    try:
        r = subprocess.run(["wmic", "process", "where", "name like '%python%'",
                            "get", "CommandLine", "/format:list"],
                           capture_output=True, text=True, errors="replace", timeout=60)
        return bool(re.search(r"-B\s+\S*p4_wan_run_v2\.py", r.stdout or ""))
    except Exception:
        return None


def block12_state():
    try:
        got = set()
        for line in open(REC, encoding="utf-8", errors="replace"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("chunk") in BLOCK12 and r.get("ok"):
                got.add(r["chunk"])
        return len(got), [c for c in BLOCK12 if c not in got]
    except OSError:
        return 0, list(BLOCK12)


def tail(n=8):
    try:
        return open(LOG, encoding="utf-8", errors="replace").read().splitlines()[-n:]
    except OSError:
        return []


strikes = 0
while time.time() - T0 < MAX_S:
    qe, ra = queue_empty(), runner_alive()
    if qe is True and ra is False:
        strikes += 1
        if strikes >= 2:
            n, missing = block12_state()
            status = "RENDER_SETTLED" if not missing else "RENDER_IDLE_PENDING"
            print(json.dumps({"status": status, "elapsed_s": int(time.time() - T0),
                              "block12_ok": n, "missing": missing, "log_tail": tail()},
                             ensure_ascii=False))
            sys.exit(0)
        time.sleep(60)
    else:
        strikes = 0
        print("waiting: queue_empty=%s runner_alive=%s elapsed=%ds" % (qe, ra, int(time.time() - T0)),
              flush=True)
        time.sleep(120)
print(json.dumps({"status": "TIMEOUT_3H", "log_tail": tail()}, ensure_ascii=False))
sys.exit(2)
