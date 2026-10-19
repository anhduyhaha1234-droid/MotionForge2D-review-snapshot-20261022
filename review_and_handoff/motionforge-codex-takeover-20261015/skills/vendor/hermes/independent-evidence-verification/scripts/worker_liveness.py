#!/usr/bin/env python
"""Read-only worker liveness prober for Hermes CLI worker sessions.

Why this exists
---------------
A worker dispatched via `hermes -z ... > worker.log` can keep `worker.log` at
**0 bytes** for its entire run while it is working normally, so log size/tail is
not a liveness signal in either direction.  The durable signal is the session
store: a rising `tool_call_count` plus a recent `messages` row.

This tool opens the state DB READ-ONLY (URI `mode=ro`) — never mutate it, and
never point it at a live production DB with write intent.

Usage
-----
  python worker_liveness.py --recent-minutes 120
  python worker_liveness.py --sessions 20260922_104627_73f18d 20260922_104630_0ca233
  python worker_liveness.py --recent-minutes 30 --json

Traps this encodes (both observed in the field)
-----------------------------------------------
  * `ended_at IS NULL` does NOT mean the worker is alive — dead sessions stay NULL
    forever when no close was recorded.
  * `exit_code == 0` does NOT mean the work was done — a 52-byte log holding
    "API call failed after 3 retries: Connection error." exited 0 with no artifacts.
    Always count the requested artifacts on disk as well.
  * `--resume <id>` may mint a NEW session id (ownership event): record
    parent -> actual, and confirm the parent is terminal.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path.home() / "AppData/Local/hermes/state.db"


def connect(db: Path) -> sqlite3.Connection:
    uri = f"file:{db.as_posix()}?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    con.row_factory = sqlite3.Row
    return con


def last_message(con: sqlite3.Connection, sid: str) -> sqlite3.Row | None:
    return con.execute(
        "SELECT role, tool_name, timestamp, substr(content,1,160) AS snippet "
        "FROM messages WHERE session_id=? ORDER BY id DESC LIMIT 1",
        (sid,),
    ).fetchone()


def first_user_message(con: sqlite3.Connection, sid: str) -> str:
    row = con.execute(
        "SELECT substr(content,1,140) AS s FROM messages "
        "WHERE session_id=? AND role='user' ORDER BY id LIMIT 1",
        (sid,),
    ).fetchone()
    return (row["s"] or "").replace("\n", " ") if row else ""


def probe(con: sqlite3.Connection, sid: str) -> dict:
    row = con.execute(
        "SELECT id, source, model, message_count, tool_call_count, ended_at, "
        "end_reason, started_at, cwd, parent_session_id, title "
        "FROM sessions WHERE id=?",
        (sid,),
    ).fetchone()
    if row is None:
        return {"session": sid, "verdict": "NO_SUCH_SESSION"}
    last = last_message(con, sid)
    rec = {
        "session": sid,
        "source": row["source"],
        "model": row["model"],
        "message_count": row["message_count"],
        "tool_call_count": row["tool_call_count"],
        "ended_at": row["ended_at"],
        "end_reason": row["end_reason"],
        "cwd": row["cwd"],
        "parent_session_id": row["parent_session_id"],
        "started_at_utc": (datetime.fromtimestamp(row["started_at"], timezone.utc).isoformat()
                           if row["started_at"] else None),
        "ended_at_utc": (datetime.fromtimestamp(row["ended_at"], timezone.utc).isoformat()
                         if row["ended_at"] else None),
        "last_message": ({"role": last["role"], "tool_name": last["tool_name"],
                          "snippet": last["snippet"]} if last else None),
        "packet_first_user_message": first_user_message(con, sid),
    }
    if row["ended_at"]:
        rec["verdict"] = "TERMINAL"
    elif last is not None and last["role"] == "tool":
        rec["verdict"] = "ALIVE_WORKING"
    else:
        # No close recorded and no tool row yet: could be mid-turn, could be a corpse.
        rec["verdict"] = "UNKNOWN_PROVE_BY_TOOL_COUNT_DELTA"
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--sessions", nargs="*", default=None)
    ap.add_argument("--recent-minutes", type=int, default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    db = Path(args.db)
    if not db.is_file():
        print(json.dumps({"error": "db not found", "db": str(db)}))
        return 2

    con = connect(db)
    ids: list[str] = list(args.sessions or [])
    if args.recent_minutes is not None:
        cutoff = time.time() - args.recent_minutes * 60
        ids += [r["id"] for r in con.execute(
            "SELECT id FROM sessions WHERE started_at > ? ORDER BY started_at", (cutoff,))]
    if not ids:
        ap.error("pass --sessions or --recent-minutes")

    results = [probe(con, sid) for sid in ids]
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            print(f"[{r['verdict']}] {r['session']} msgs={r.get('message_count')} "
                  f"tools={r.get('tool_call_count')} end={r.get('ended_at')} "
                  f"reason={r.get('end_reason')} cwd={r.get('cwd')}")
            lm = r.get("last_message")
            if lm:
                print(f"    last: {lm['role']} {lm['tool_name'] or ''} {str(lm['snippet'])[:110]}")
            if r.get("packet_first_user_message"):
                print(f"    packet: {r['packet_first_user_message'][:110]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
