#!/usr/bin/env python
"""Worker-lane launcher template (Manager tool). Copy and adapt per run.

Proven shape (MF2D CMC correction, 2026-09-29): a pure-argv passthrough that
launches one Hermes worker lane, records a receipt, and appends an append-only
dispatch ledger row BEFORE the child starts so a launcher crash is still logged.

usage:
  python dispatch_lane.py <packet.md> <task_id> <cwd> <log> <receipt.json>
                          [--resume <session_id>] [--max-turns N]

Why each piece exists (each one cost a real cycle to learn):

* PACKET AS A REAL ARGV ELEMENT — `hermes chat -q "<the whole packet>"`. This is
  the proven multi-KB prompt shape. Do NOT build the prompt by shell
  interpolation: compose it in Python and pass it as one argv item.

* PACKET SIZE REFUSAL BEFORE LAUNCH — Windows CreateProcess has a hard argv
  ceiling (~32.5K chars measured; 32,500 spawns, 32,700 fails with
  `[WinError 206] The filename or extension is too long`). Refuse early with a
  clear message instead of surfacing an opaque OS error mid-run. Keep a margin.

* NATIVE `C:/...` PATHS ONLY — never hand a `/c/...`-shaped value to this script
  or to `git worktree add`; MSYS rewrites it into a phantom `C:\\c\\...` that
  reports success while sitting somewhere nobody will `cd` into. Normalise a
  leading `/c/` to `C:/` inside the tool so a reviewer copying the command
  verbatim cannot hit the trap.

* PROVIDER/MODEL PINNED PER LANE, FALLBACK OFF — the route is a per-run decision
  (`--provider custom -m <exact-model>`), and the receipt records what was
  REQUESTED. The per-request proof of what actually ran is the
  `agent.conversation_loop: API call #N: model=... provider=... ` line in
  `~/AppData/Local/hermes/logs/agent.log` — parse that, not the flag.

* RECEIPT WRITTEN TWICE (pre-launch + post-exit) — the pre-launch version makes
  the lane visible to a monitor while it runs; the post-exit version adds
  `exit_code`. A monitor reading a receipt with no `log` key yet must treat it
  as "still running", not as a filesystem error (`Path("") == Path(".")`, and
  `read_bytes('.')` raises `PermissionError: [Errno 13]`).

* LEDGER ROW APPENDED BEFORE LAUNCH — mode `"a"` always. A dispatch that dies
  pre-append simply has no row; never backfill it later, or the ledger gains a
  duplicate and points at a receipt that was overwritten by the re-dispatch.

* `exit_code` IS NOT COMPLETION — say so in the receipt itself. `exit 0` is
  returned both by clean finishes and by rounds cut short by the per-response
  OUTPUT token limit (mid-`patch`, with the runtime correctly refusing an
  incomplete tool call). Always read the log payload + measure the disk.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- edit these three per run -------------------------------------------------
PROVIDER = "custom"
MODEL = "cmc/deepseek/deepseek-v4.1-flash"
BASE_URL = "http://127.0.0.1:20128/v1"
API_MODE = "chat_completions"
RUN_ROOT = Path("C:/path/to/run-root")
# -----------------------------------------------------------------------------

MAX_PACKET_BYTES = 28000  # argv ceiling margin (measured failure beyond ~32.5K)
LEDGER = RUN_ROOT / "ledgers" / "dispatch-ledger.jsonl"


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def native(p: str) -> str:
    """Normalise a `/c/...` MSYS path to `C:/...` so Windows binaries resolve it."""
    if p.startswith("/c/"):
        return "C:/" + p[3:]
    return p


def append_ledger(row: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as fh:  # ALWAYS append
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    packet_path = Path(native(sys.argv[1]))
    task_id = sys.argv[2]
    cwd = native(sys.argv[3])
    log_path = Path(native(sys.argv[4]))
    receipt_path = Path(native(sys.argv[5]))
    extra = sys.argv[6:]

    prompt = packet_path.read_text(encoding="utf-8")
    nbytes = len(prompt.encode("utf-8"))
    if nbytes > MAX_PACKET_BYTES:
        print(f"REFUSED: packet {nbytes} bytes > {MAX_PACKET_BYTES} (argv ceiling)")
        return 2

    resume = extra[extra.index("--resume") + 1] if "--resume" in extra else None
    max_turns = extra[extra.index("--max-turns") + 1] if "--max-turns" in extra else "160"

    argv = ["hermes", "chat", "-q", prompt, "--provider", PROVIDER, "-m", MODEL,
            "--pass-session-id", "--no-restore-cwd", "--max-turns", max_turns]
    if resume:
        argv += ["--resume", resume]

    started = utc()
    receipt = {
        "task_id": task_id,
        "round": packet_path.stem,
        "packet": str(packet_path),
        "packet_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "packet_bytes": nbytes,
        "cwd": cwd,
        "provider": PROVIDER,
        "model": MODEL,
        "base_url": BASE_URL,
        "api_mode": API_MODE,
        "fallback": False,
        "resume_session_requested": resume,
        "max_turns": max_turns,
        "argv_shape": argv[:4] + ["<PACKET>"] + argv[5:],
        "utc_start": started,
        "launcher_pid": os.getpid(),
        "note": "exit_code is NOT completion proof - read the log payload",
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_ledger({"action": "dispatch", "task_id": task_id, "at_utc": started,
                   "model": MODEL, "cwd": cwd, "resume_session_requested": resume,
                   "packet": str(packet_path), "packet_sha256": receipt["packet_sha256"],
                   "packet_bytes": nbytes, "receipt": str(receipt_path),
                   "log": str(log_path), "launcher_pid": os.getpid()})

    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    with log_path.open("wb") as log:
        proc = subprocess.run(argv, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, env=env)

    ended = utc()
    receipt.update({"exit_code": proc.returncode, "utc_end": ended, "log": str(log_path)})
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_ledger({"action": "exit", "task_id": task_id, "at_utc": ended,
                   "exit_code": proc.returncode, "receipt": str(receipt_path),
                   "log": str(log_path),
                   "log_bytes": log_path.stat().st_size if log_path.exists() else 0})
    print(f"exit={proc.returncode} log={log_path}")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
