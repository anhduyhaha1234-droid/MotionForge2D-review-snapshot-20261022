#!/usr/bin/env python
"""Bounded read-only heartbeat monitor for long-running CLI worker lanes.

One `iter ` line per tick so a launch like

    terminal(background=True, watch_patterns=["iter "],
             command='python -B bounded_monitor.py --db <state.db> --run-root <run> '
                     '--lanes "A=20260927_130100_1dc76b,B=20260927_122444_50c9d6"')

wakes the agent once per tick (~8 min) for heartbeat + stall-audit duty, without cron and
without an unbounded watcher. READ-ONLY against the session DB (mode=ro); writes only under
<run-root>/manager/. Exits by itself after --iterations ticks — kill it once all lanes are
terminal so its remaining ticks stop waking the agent.

Notes
  * <run-root>/<LANE>/ is expected to hold the lane's evidence files (counted per tick as ev=).
  * lane -> session id must be the LIVE id (the one whose first user message == packet head).
    `--resume` mints a new id and stamps the parent `end_reason=agent_close`, so a map that
    still points at the parent will print a dead row with a growing age.
  * Do NOT also set notify_on_complete on the launch (mutually exclusive with watch_patterns).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sqlite3
import sys
import time
from pathlib import Path


def parse_lanes(spec: str) -> dict[str, str]:
    lanes: dict[str, str] = {}
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        name, _, sid = part.partition("=")
        if not name or not sid:
            raise SystemExit(f"bad --lanes entry: {part!r} (want NAME=session_id)")
        lanes[name.strip()] = sid.strip()
    if not lanes:
        raise SystemExit("--lanes is empty")
    return lanes


def poll(db: str, run_root: Path, lanes: dict[str, str]) -> dict:
    con = sqlite3.connect(f"file:{Path(db).as_posix()}?mode=ro", uri=True, timeout=30)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    out: dict[str, dict] = {}
    for name, sid in lanes.items():
        # materialise before any inner query (cursor-reuse truncates the loop)
        rows = list(cur.execute("SELECT COUNT(*) AS n FROM messages WHERE session_id=?", (sid,)))
        last = list(cur.execute(
            "SELECT timestamp FROM messages WHERE session_id=? ORDER BY id DESC LIMIT 1", (sid,)))
        sess = list(cur.execute(
            "SELECT api_call_count, end_reason FROM sessions WHERE id=?", (sid,)))
        ev = run_root / name
        ev_files = len([p for p in ev.rglob("*") if p.is_file()]) if ev.exists() else 0
        age = round(time.time() - float(last[0]["timestamp"]), 1) if last else None
        out[name] = {
            "messages": rows[0]["n"] if rows else 0,
            "api": (sess[0]["api_call_count"] if sess else None),
            "end": (sess[0]["end_reason"] if sess else None),
            "age_s": age,
            "ev_files": ev_files,
        }
    con.close()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="path to the session state.db")
    ap.add_argument("--run-root", required=True, help="evidence root (lanes are subdirs)")
    ap.add_argument("--lanes", required=True, help="NAME=session_id,NAME=session_id")
    ap.add_argument("--iterations", type=int, default=6)
    ap.add_argument("--sleep", type=int, default=480, help="seconds per tick (480 = 8 min)")
    ap.add_argument("--tag", default="hb", help="log name suffix: monitor_<tag>.log")
    args = ap.parse_args()

    run_root = Path(args.run_root)
    lanes = parse_lanes(args.lanes)
    log = run_root / "manager" / f"monitor_{args.tag}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    prev: dict | None = None
    with log.open("a", encoding="utf-8") as f:
        f.write(f"=== monitor start {dt.datetime.now(dt.timezone.utc).isoformat()} "
                f"({args.iterations} iters x {args.sleep}s) lane={lanes} ===\n")
        for i in range(args.iterations):
            time.sleep(args.sleep)
            snap = poll(args.db, run_root, lanes)
            stamp = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%SZ")
            bits = []
            for name, d in snap.items():
                delta = f" (+{d['messages'] - prev[name]['messages']}msg)" if prev else ""
                stall = ""
                if d["age_s"] is not None and d["age_s"] > 8 * 60 and d["end"] is None:
                    stall = " STALL_AUDIT>8min"
                bits.append(f"{name}: {d['messages']}msg{delta} api={d['api']} "
                            f"ev={d['ev_files']} age={d['age_s']}s end={d['end']}{stall}")
            line = f"[{stamp}] iter {i + 1}/{args.iterations} | " + " | ".join(bits)
            print(line, flush=True)  # watch_patterns=["iter "] matches this line
            f.write(line + "\n")
            f.flush()
            (run_root / "manager" / "monitor_last.json").write_text(
                json.dumps({"stamp": stamp, "iter": i + 1, "snap": snap}, indent=2),
                encoding="utf-8")
            prev = snap
        f.write(f"=== monitor stop {dt.datetime.now(dt.timezone.utc).isoformat()} ===\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
