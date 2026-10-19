#!/usr/bin/env python
"""Receipt-aware lane watchdog for long CLI-agent worker waves.

Why this exists (measured 2026-09-24): a watchdog that samples worker progress purely from
the Hermes state DB reads every FINISHED lane as stalled — a completed lane's message count
is frozen for ever, so 8 minutes after it exits the sample is indistinguishable from a hang.
Two further traps it closes: it watches the MINTED continuation session ids (a `--resume`
never writes to the parent id again), and it treats an existing launcher receipt as terminal.

Edit the CONFIG block, then run with terminal(background=true, notify_on_complete=true):
    python receipt_aware_lane_watchdog.py
Exit codes: 0 = all watched processes gone; 3 = real stall flagged (receipt absent AND rows
frozen AND process alive); 4 = window exhausted with everything healthy.

IMPORTANT: re-run the parent->actual id resolution after EVERY resume round and re-edit
LANES — a stale id list is the main source of false STALL_ALERTs.
"""

from __future__ import annotations

import datetime as dt
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

# ------------------------------- CONFIG ------------------------------------
DB = "C:/Users/Admin/AppData/Local/hermes/state.db"
RUN = Path("C:/path/to/wave/outputs/<UTC-run-id>")          # evidence root of the wave
LOG = RUN / "manager/heartbeat.log"                          # append-only sample log

# lane name -> ACTUAL (minted) session id, resolved by first-user-message match
LANES = {
    "LANE-A": "20260101_000000_aaaaaa",
    "LANE-B": "20260101_000001_bbbbbb",
}
# lane name -> launcher receipt filename(s) under RUN/manager/receipts/ ; receipt == DONE
FINISHED_RECEIPTS = {
    "LANE-A": ["LANE-A-round1.json"],
    "LANE-B": ["LANE-B-round1.json"],
}
# live hermes/python pid pairs, re-derive by cmdline before each arming
WORKER_PIDS = [1111, 2222, 3333, 4444]

STALL_WINDOW_MIN = 8.0    # RULES section 7: audit after 8 quiet minutes
MAX_HOURS = 3.0
POLL_SECONDS = 60
# ---------------------------------------------------------------------------


def sample() -> dict[str, tuple[int, float, str]]:
    """Read-only: rows, newest timestamp and newest tool per lane (no mutation)."""
    con = sqlite3.connect(f"file:{Path(DB).as_posix()}?mode=ro", uri=True, timeout=25)
    cur = con.cursor()
    out: dict[str, tuple[int, float, str]] = {}
    for lane, sid in LANES.items():
        rows = list(cur.execute(  # materialise BEFORE any inner query (cursor-reuse trap)
            "SELECT role, tool_name, timestamp FROM messages WHERE session_id=? "
            "ORDER BY id DESC LIMIT 1", (sid,)))
        n = list(cur.execute("SELECT COUNT(*) FROM messages WHERE session_id=?", (sid,)))[0][0]
        if rows:
            out[lane] = (n, float(rows[0][2] or 0), str(rows[0][1] or rows[0][0]))
        else:
            out[lane] = (n, 0.0, "-")
    con.close()
    return out


def receipt_present(lane: str) -> bool:
    return any((RUN / "manager/receipts" / r).is_file() for r in FINISHED_RECEIPTS.get(lane, []))


def processes_alive() -> int:
    p = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-Process -Id %s -ErrorAction SilentlyContinue | Measure-Object).Count"
         % ",".join(str(x) for x in WORKER_PIDS)],
        capture_output=True, text=True)
    try:
        return int((p.stdout or "0").strip() or 0)
    except ValueError:
        return -1


def main() -> int:
    started = time.time()
    last: dict[str, int] = {}
    while time.time() - started < MAX_HOURS * 3600:
        now = dt.datetime.now(dt.timezone.utc)
        snap = sample()
        line = now.strftime("%Y-%m-%dT%H:%M:%SZ") + " WATCH"
        stall = False
        for lane, (n, ts, tool) in snap.items():
            age = (now.timestamp() - ts) / 60.0 if ts else 1e9
            done = receipt_present(lane)
            line += (f" | {lane} rows={n} age={age:.1f}m tool={tool}"
                     f"{' DONE(exit, not stalled)' if done else ''}")
            if lane in last and n == last[lane] and age > STALL_WINDOW_MIN and not done:
                line += "  <-- STALL"
                stall = True
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        last = {k: v[0] for k, v in snap.items()}
        if stall:
            (RUN / "manager/audit/STALL_FLAG.txt").write_text(line + "\n", encoding="utf-8")
            print("STALL DETECTED (audit receipt + log before escalating): " + line)
            return 3
        if processes_alive() == 0:
            with LOG.open("a", encoding="utf-8") as fh:
                fh.write(now.strftime("%Y-%m-%dT%H:%M:%SZ") + " WATCH: all watched worker processes exited\n")
            print("ALL WATCHED WORKERS EXITED")
            return 0
        time.sleep(POLL_SECONDS)
    print("watchdog window exhausted (healthy)")
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
