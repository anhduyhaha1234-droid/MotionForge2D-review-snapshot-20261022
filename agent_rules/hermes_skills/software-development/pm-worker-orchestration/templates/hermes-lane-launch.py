#!/usr/bin/env python
"""Shell-free launcher for one Hermes CLI worker turn (copy + adapt).

WHY THIS EXISTS
---------------
Two independent failure classes disappear when the prompt is passed as an argv
LIST instead of through a shell:

1. FLAG ORDER.  `hermes chat -q -Q -r <sid> ... "$(cat prompt.md)"` exits 2 with
   `argument -q/--query: expected one argument` — argparse will not take a token
   starting with `-` as the `-q` value, and the prompt arriving last cannot
   rescue it.  No session is created, and the usage dump reads like a
   route/worker fault, so the mis-dispatch can burn a whole monitor cycle.
   Here the prompt is ALWAYS the element immediately after "-q".
2. SHELL QUOTING / MSYS PATH MANGLING of large multi-line prompts (quotes,
   backticks, `$(...)`, CRLF).  subprocess with a list bypasses the shell
   entirely.

USAGE
-----
    python launch.py <prompt_file> <log_file> <workdir> <max_turns> [session_id|-]

    <session_id>  resume that exact owner session  (correction / continuation)
    -             start a NEW session              (route smoke probe, new task)

Always pass a Windows-native workdir ("C:/Users/..."), never "/c/Users/...":
Windows binaries rewrite the MSYS form into "C:\\c\\Users\\...".

The log is APPENDED and records argv + UTC start/end + exit code, so one file
doubles as the command ledger.  Give each turn a NEW log filename; never
overwrite a dead turn's log — that log is incident evidence.

AFTER LAUNCH (manager duty)
---------------------------
Prove the turn actually took before entering monitor waits: the log must EXIST
and GROW past the launch banner.  Exit 2 + a usage dump means nothing ran.
Liveness afterwards: log size/mtime advancing, or the session DB's newest
message timestamp — not the wrapper's exit code, which is not proof of
completion in either direction.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- adapt these three to the host -------------------------------------------
HERMES = r"C:\Users\Admin\AppData\Local\Programs\Python\Python311\Scripts\hermes.exe"
MODEL = "ocg/deepseek-v4.1-flash"   # exact route; never a near-miss id
PROVIDER = "custom"                 # must match config.yaml providers.<name>
# -----------------------------------------------------------------------------


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    prompt_file = Path(sys.argv[1])
    log_file = Path(sys.argv[2])
    workdir = Path(sys.argv[3])
    max_turns = str(sys.argv[4])
    session_id = sys.argv[5] if len(sys.argv) > 5 else "-"

    prompt = prompt_file.read_text(encoding="utf-8")

    # "-q" is IMMEDIATELY followed by its prompt. Do not reorder.
    cmd = [HERMES, "chat", "-q", prompt, "-Q"]
    if session_id and session_id != "-":
        cmd += ["-r", session_id]          # same owner session = correction
    cmd += [
        "-m", MODEL,
        "--provider", PROVIDER,
        "--max-turns", max_turns,
        "--yolo",                          # non-interactive: no approval prompts
    ]

    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as fh:
        fh.write(f"\n=== LAUNCH {utc()} exec={HERMES}\n")
        fh.write(f"=== prompt={prompt_file} bytes={len(prompt.encode('utf-8'))}\n")
        fh.write(f"=== workdir={workdir} session={session_id} max_turns={max_turns}\n")
        fh.write(f"=== model/provider={MODEL}/{PROVIDER} fallback=OFF\n")
        fh.flush()
        # argv list, not a shell string: the prompt is delivered verbatim.
        proc = subprocess.run(
            cmd, cwd=str(workdir), stdout=fh, stderr=subprocess.STDOUT, text=True
        )
        fh.write(f"\n=== EXIT={proc.returncode} END={utc()}\n")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
