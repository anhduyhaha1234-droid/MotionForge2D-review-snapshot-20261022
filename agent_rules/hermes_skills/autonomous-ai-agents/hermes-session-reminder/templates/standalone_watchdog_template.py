"""Template: Standalone Auto-Nudge Watchdog Daemon for Hermes Desktop Sessions.

Use when Hermes Gateway is down (cron jobs cannot fire) and the session needs
to be kept alive 24/24 with periodic nudges into the chat and heartbeats.
"""
import datetime
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

HERMES = r"C:\Users\Admin\AppData\Local\Programs\Python\Python311\Scripts\hermes.exe"
SID = "<SESSION_ID>"                # Target session ID from state.db
MODEL = "<MODEL>"                   # e.g. "ag/gemini-3.8-flash-high"
PROVIDER = "<PROVIDER>"             # e.g. "custom"
MSG = "tiếp tục làm việc đi"        # Short exact phrase (no task list)
LOG = r"C:\Users\Admin\AppData\Local\hermes\logs\remind_<tag>.log"
STATE_DB = r"C:\Users\Admin\AppData\Local\hermes\state.db"
INTERVAL = 1800                     # Cadence in seconds (e.g. 1800 = 30m, 600 = 10m)


def now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def is_session_idle(threshold_seconds=600):
    """Check if the session has had no new messages in the last threshold_seconds."""
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
    except Exception:
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
            time.sleep(20)
            res = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, timeout=600)
            f.write(f"retry exit={res.returncode}\n")
        f.write(f"=== {now_str()} end ===\n")
    return rc


def main():
    Path(LOG).parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{now_str()}] Watchdog started for session {SID} (interval: {INTERVAL}s).\n")
    while True:
        time.sleep(INTERVAL)
        if is_session_idle(threshold_seconds=600):
            run_nudge()


if __name__ == "__main__":
    main()
