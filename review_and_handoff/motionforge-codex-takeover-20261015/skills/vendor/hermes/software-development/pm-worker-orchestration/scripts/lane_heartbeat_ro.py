#!/usr/bin/env python
"""Lane heartbeat: per-lane progress from a read-only Hermes state.db + launcher logs.

Why this exists: with `hermes -z --resume <parent>` workers, the launcher log can stay
0 bytes for minutes while the run is healthy, and a heartbeat pointed at the REQUESTED
PARENT id shows a day-old timestamp that reads as a stall. Always resolve the ACTUAL
continuation ids first (first-user-message == own packet head), then drive this script
with them.

usage:
    python lane_heartbeat_ro.py lanes.json
or:
    python lane_heartbeat_ro.py --db <state.db> --lane NAME=SESSION_ID[,LOG_PATH] ...

lanes.json shape:
{
  "db": "C:/Users/<u>/AppData/Local/hermes/state.db",
  "lanes": {
    "COMFY":    {"session": "20260924_175709_40429c", "log": "C:/.../logs/MF-V1-COMFY.log"},
    "CONTRACT": {"session": "20260924_175837_9e0d2c"}
  }
}

Read-only (mode=ro). Rows are materialised before inner queries on purpose: a sqlite
cursor reused inside its own iteration silently truncates the loop.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
import sys
from pathlib import Path


def load_config(argv: list[str]) -> tuple[str, dict[str, dict]]:
    if argv and argv[0].endswith(".json"):
        cfg = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
        return cfg["db"], cfg["lanes"]
    db = None
    lanes: dict[str, dict] = {}
    i = 0
    while i < len(argv):
        if argv[i] == "--db":
            db = argv[i + 1]
            i += 2
        elif argv[i] == "--lane":
            name, rest = argv[i + 1].split("=", 1)
            parts = rest.split(",")
            lanes[name] = {"session": parts[0], "log": parts[1] if len(parts) > 1 else None}
            i += 2
        else:
            i += 1
    if not db:
        raise SystemExit(__doc__)
    return db, lanes


def main() -> int:
    db, lanes = load_config(sys.argv[1:])
    con = sqlite3.connect(f"file:{Path(db).as_posix()}?mode=ro", uri=True, timeout=25)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    now = dt.datetime.now(dt.timezone.utc)
    print(f"HEARTBEAT {now.strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print(f"{'lane':12} {'rows':>6} {'last_utc':20} {'age_m':>7} {'last_tool':16} {'log_B':>8}")
    for lane, spec in lanes.items():
        sid = spec["session"]
        rows = list(cur.execute(
            "SELECT role, tool_name, timestamp FROM messages WHERE session_id=? "
            "ORDER BY id DESC LIMIT 1", (sid,)))
        count = list(cur.execute(
            "SELECT COUNT(*) FROM messages WHERE session_id=?", (sid,)))[0][0]
        log = spec.get("log")
        lb = Path(log).stat().st_size if log and Path(log).is_file() else -1
        if not rows:
            print(f"{lane:12} {count:>6} {'(no rows)':20} {'-':>7} {'-':16} {lb:>8}")
            continue
        try:
            ts = dt.datetime.fromtimestamp(float(rows[0]["timestamp"] or 0), dt.timezone.utc)
            age = round((now - ts).total_seconds() / 60.0, 1)
            ts_s = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            ts_s, age = str(rows[0]["timestamp"])[:19], -1.0
        print(f"{lane:12} {count:>6} {ts_s:20} {age:>7} "
              f"{str(rows[0]['tool_name'])[:16]:16} {lb:>8}")
    print("\nreading: age < ~2 min = actively turning. age > 8 min AND rows flat = audit now\n"
          "(process alive? tool child spawned recently? socket ESTABLISHED? CPU delta ≈0 = "
          "waiting on upstream, not hung).")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
