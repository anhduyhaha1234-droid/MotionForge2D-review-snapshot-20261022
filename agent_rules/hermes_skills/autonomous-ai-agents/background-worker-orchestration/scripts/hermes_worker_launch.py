"""Dispatch a Hermes worker / correction turn WITHOUT shell quoting.

Why this exists (verified 2026-09-16, S12-R7): the same multi-line Markdown
packet that dispatches flawlessly through this launcher died instantly with

    hermes chat: error: argument -q/--query: expected one argument

when passed as a shell argument (`hermes chat -q "$(cat packet.md)" ...` inside a
compound `&&` chain). No shell -> no quoting, no length limit, no `$(...)`
expansion, no MSYS path mangling.

Usage
-----
  python hermes_worker_launch.py \
      --prompt  C:/.../A/packets/RETRY_turn1_packet.md \
      --log     C:/.../A/RETRY/turn1_run.log \
      --cwd     C:/Users/Admin/MotionForge2D-worktrees/s12-lc3-luna-retry \
      --model   ocg/deepseek-v4.1-flash --provider custom \
      --session 20260915_201417_80e003   # omit / pass --new for a fresh session
      [--max-turns 60] [--hermes <path to hermes.exe>]

Rules baked in
--------------
* argv list only — never `shell=True`, never a string command.
* cwd is passed explicitly (worker MUST run inside its own worktree; the
  Hermes daemon cwd is NOT inherited reliably).
* stdout+stderr stream straight into the log file (fd-direct, not
  capture_output) with UTC start/end, argv, model, provider, session, exit.
* ALWAYS pass Windows-native `C:/...` paths: an MSYS `$VAR` handed to python.exe
  arrives as `C:\\c\\Users\\...` -> `[Errno 2] No such file or directory`.
* Launch it via terminal(background=true, notify_on_complete=true) so the exit
  notification wakes you; keep one log per dispatch attempt
  (`turn1_run.log`, `resume1_run.log`, ...) so attempts stay auditable.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_HERMES = (
    r"C:\Users\Admin\AppData\Local\Programs\Python\Python311\Scripts\hermes.exe"
)


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prompt", required=True, help="packet/contract .md or .txt file")
    ap.add_argument("--log", required=True, help="append-only dispatch log")
    ap.add_argument("--cwd", required=True, help="worker worktree (Windows-native path)")
    ap.add_argument("--model", required=True)
    ap.add_argument("--provider", required=True)
    ap.add_argument("--session", default=None, help="exact owner session id to RESUME")
    ap.add_argument("--new", action="store_true", help="start a NEW session instead")
    ap.add_argument("--max-turns", type=int, default=60)
    ap.add_argument("--hermes", default=DEFAULT_HERMES)
    ap.add_argument("--quiet", action="store_true", default=True)
    ap.add_argument("--extra", nargs="*", default=[], help="extra CLI flags")
    a = ap.parse_args(argv)

    if a.session and a.new:
        ap.error("pass either --session <sid> or --new, not both")

    prompt = Path(a.prompt).read_text(encoding="utf-8")
    cmd = [a.hermes, "chat", "-q", prompt, "-Q"]
    if a.session:
        cmd += ["-r", a.session]
    cmd += [
        "-m", a.model,
        "--provider", a.provider,
        "--max-turns", str(a.max_turns),
        "--yolo",
    ] + list(a.extra)

    log = Path(a.log)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(f"\n=== LAUNCH {utc()}\n")
        fh.write(f"=== prompt={a.prompt} bytes={len(prompt.encode('utf-8'))}\n")
        fh.write(f"=== cwd={a.cwd} session={a.session or 'NEW'} turns={a.max_turns}\n")
        fh.write(f"=== model={a.model} provider={a.provider} fallback=OFF\n")
        fh.flush()
        proc = subprocess.run(
            cmd, cwd=a.cwd, stdout=fh, stderr=subprocess.STDOUT, text=True
        )
        fh.write(f"\n=== EXIT={proc.returncode} END={utc()}\n")
    print(f"exit={proc.returncode} log={log}", flush=True)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
