# Template: Standalone background auto-nudge watchdog for Hermes sessions.
# Does NOT rely on `hermes gateway` or cron service. Runs via terminal(background=True).
# Monitors SQLite state.db for session idle > threshold, then injects resume nudge.
# Optionally pairs with Telegram True-Liveness heartbeat.

from __future__ import annotations
import datetime
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

HERMES = r"C:\Users\Admin\AppData\Local\Programs\Python\Python311\Scripts\hermes.exe"
SID = "<SESSION_ID>"
MODEL = "<MODEL>"          # from state.db sessions table
PROVIDER = "<PROVIDER>"    # from state.db sessions table
MSG = "tiếp tục làm việc đi"  # exact user nudge phrase
LOG = r"C:\Users\Admin\AppData\Local\hermes\logs\remind_<tag>.log"
STATE_DB = r"C:\Users\Admin\AppData\Local\hermes\state.db"
INTERVAL = 1800  # 30 minutes
IDLE_THRESHOLD = 600  # 10 minutes


def now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def is_session_idle(threshold_seconds=IDLE_THRESHOLD):
    if not os.path.exists(STATE_DB):
        return True
    try:
        conn = sqlite3.connect(STATE_DB, timeout=5)
        cur = conn.cursor()
        row = cur.execute(
            "SELECT timestamp FROM messages WHERE session_id=? ORDER BY id DESC LIMIT 1",
            (SID,)
        ).fetchone()
        conn.close()
        if not row or not row[0]:
            return True
        last_ts = float(row[0])
        return (time.time() - last_ts) > threshold_seconds
    except Exception as e:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"[{now_str()}] DB check error: {e}\n")
        return True


def run_nudge():
    cmd = [HERMES, "chat", "-q", MSG, "-r", SID, "-m", MODEL, "--provider", PROVIDER, "-Q"]
    with open(LOG, "a", encoding="utf-8", errors="replace") as f:
        f.write(f"\n=== {now_str()} [GIỜ NHẮC] start ===\n")
        f.flush()
        res = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, timeout=600)
        rc = res.returncode
        f.write(f"exit={rc}\n")
        if rc in (1, 2):
            f.write("--- retry after 20s ---\n")
            f.flush()
            time.sleep(20)
            res = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, timeout=600)
            rc = res.returncode
            f.write(f"retry exit={rc}\n")
        f.write(f"=== {now_str()} end ===\n")
    return rc


def main():
    Path(LOG).parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{now_str()}] Watchdog started for session {SID} (interval: {INTERVAL}s).\n")
    
    while True:
        time.sleep(INTERVAL)
        if is_session_idle():
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(f"[{now_str()}] Session {SID} idle > {IDLE_THRESHOLD}s -> Nudging...\n")
            try:
                run_nudge()
            except Exception as e:
                with open(LOG, "a", encoding="utf-8") as f:
                    f.write(f"[{now_str()}] Nudge error: {e}\n")
        else:
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(f"[{now_str()}] Session {SID} active -> Nudge skipped.\n")


if __name__ == "__main__":
    main()
