#!/usr/bin/env python
"""One-shot Hermes worker launcher: argv transport, unbuffered log, JSON receipt.

Usage
-----
    python hermes-oneshot-launcher.py <packet.md> <cwd> <log> <receipt.json> \\
        [-m <model>] [--pass-session-id] [--resume <session_id>] [any extra hermes args]

Run it with the runner's background mode + notify_on_complete -- never with
`nohup` / `&`, which bypasses lifecycle tracking and readiness checks.

Why each piece exists (all three were verified failures in the field)
--------------------------------------------------------------------
1. ARGV TRANSPORT. Passing a packet through a shell breaks it:
   `hermes -z "$(cat packet.md)"` dies with
   `argument -q/--query: expected one argument` (exit 2), because the shell
   re-splits the multi-line prompt before argparse sees it. Here the packet is
   one argv element and no shell is involved, so multi-line / quoted / unicode
   content passes verbatim. `cwd=` replaces `cd` interpolation entirely.
2. UNBUFFERED LOG. With `stdout=<file>` a Python CLI child is block-buffered, so
   the "live" log stays 0 bytes for the whole run and reads like a hung worker.
   PYTHONUNBUFFERED / PYTHONIOENCODING fix the log; for LIVENESS never trust the
   log tail -- query state.db read-only (per-session message count / max rowid).
3. AUDITABLE RECEIPT. Exit code 0 is NOT completion: `hermes -z` stops at its
   tool-calling budget (`agent.max_iterations`, default 90/run, no env override)
   and can exit 0 with an empty deliverable tree. The receipt records enough to
   tie the run to a tree (cwd, argv SHAPE, packet sha256 + byte count, start/end,
   duration, exit) so the next step is verifying the ARTIFACT PATHS ON DISK, plus
   the cap marker read out of state.db if the deliverable is missing.

Always pass Windows-native paths (`C:/Users/...`) to this script; an MSYS
`/c/Users/...` argument can resolve to `C:\\c\\Users\\...` and fail.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Only used when the caller does not supply its own -m/--model in the extras.
DEFAULT_MODEL = os.environ.get("HERMES_WORKER_MODEL", "ocg/deepseek-v4.1-flash")


def main() -> int:
    if len(sys.argv) < 5:
        print(__doc__)
        return 2

    packet_path = Path(sys.argv[1])
    cwd = sys.argv[2]
    log_path = Path(sys.argv[3])
    receipt_path = Path(sys.argv[4])
    extra = list(sys.argv[5:])

    if not packet_path.is_file():
        print(f"packet not found: {packet_path}", file=sys.stderr)
        return 2
    if not Path(cwd).is_dir():
        print(f"cwd not found: {cwd}", file=sys.stderr)
        return 2

    prompt = packet_path.read_text(encoding="utf-8")

    # The packet is ONE argv element -> nothing to split, quote or escape.
    argv = ["hermes", "-z", prompt]
    if not any(a in ("-m", "--model") for a in extra):
        argv += ["-m", DEFAULT_MODEL]
    argv += extra

    started = datetime.now(timezone.utc)
    receipt = {
        "task_packet": str(packet_path),
        "packet_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest().upper(),
        "packet_bytes": len(prompt.encode("utf-8")),
        "cwd": cwd,
        "argv_shape": ["hermes", "-z", "<PACKET>", *argv[3:]],
        "started_at_utc": started.isoformat(),
        "pid": os.getpid(),
    }

    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["PYTHONUNBUFFERED"] = "1"      # else the log stays empty for the whole run
    env["PYTHONIOENCODING"] = "utf-8"

    with log_path.open("wb") as log:
        proc = subprocess.run(
            argv, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, env=env
        )

    ended = datetime.now(timezone.utc)
    receipt.update(
        {
            "exit_code": proc.returncode,
            "ended_at_utc": ended.isoformat(),
            "duration_seconds": round((ended - started).total_seconds(), 3),
            "log": str(log_path),
            "reminder": (
                "exit_code 0 is NOT completion -- verify the deliverable paths on "
                "disk, and read the iteration-cap marker out of state.db if absent."
            ),
        }
    )
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(
        f"exit={proc.returncode} duration={receipt['duration_seconds']}s "
        f"log={log_path} receipt={receipt_path}"
    )
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
