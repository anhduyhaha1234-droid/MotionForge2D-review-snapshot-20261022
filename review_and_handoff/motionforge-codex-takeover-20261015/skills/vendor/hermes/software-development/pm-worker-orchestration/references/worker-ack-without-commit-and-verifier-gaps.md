# Worker ack-without-commit, verifier gaps, and gate-execution traps (S12-C1)

Session evidence: S12-C1 (2026-09-08/09, MotionForge2D). Lessons generalize to any
PM-gated sprint where workers run as separate `hermes chat -r <owner>` sessions.

## 1. Workers frequently ACK without doing the work — verify on disk, never trust the reply

Pattern seen repeatedly (T03C, T06A, T06B):
- Worker replies like `RULES_LOADED ... TARGET checklist ...` then exits — no gates run, no commit.
- Worker replies `SHA` / `Committing now` / `Gates xanh hết` but the worktree
  `git rev-parse --short HEAD` is UNCHANGED and `git status --porcelain` still shows the dirty files.
- Even `TASK_SUBMITTED — ... SHA 48bf514` can be a **zero-byte claim**: a read-only
  verifier (T06B) reports TASK_SUBMITTED with tip unchanged and porcelain clean —
  nothing new landed. Always confirm with `git log --oneline -2` + `git status`.

Manager response (works reliably):
1. Do NOT re-dispatch the same big prompt expecting a different result.
2. Read the real state yourself: `git log`, `git status -uall`, and run the decisive
   gate in the worktree (`pytest <dir> --basetemp=<short> -p no:cacheprovider`,
   `ruff check --select F`, `git diff --check`). Manager running gates = verification, not coding.
3. When gates are genuinely green in the worktree, dispatch a **narrow commit-only** instruction:
   "git add <allowlist> && git commit -m '<msg>' && git rev-parse --short HEAD && git status",
   KHÔNG push/merge, no prose. This converts a stalled worker into a 1-command finisher.
4. If the worker STILL only acks the commit instruction, the Manager may commit the
   allowlist itself when the prompt grants Manager Git authority and the diff is verified —
   but prefer 2 attempts at the worker first (ownership §4).

## 2. `$TEMP`/`$TMP` hijack by another session — always pass explicit short basetemp

Another concurrent session (demo-v3 sandbox) had exported
`TEMP=C:/Users/Admin/MotionForge2D-evidence/demo-v3-r2/.../_mgr-verify3-tmp` into the
shared shell. `--basetemp="$TEMP/s12t03c_fin"` then failed with
`FileNotFoundError: .../_mgr-verify3-tmp/s12t03c_diag` (parent dir missing).

Fix: never rely on `$TEMP`/`$TMP` in this repo. Always pass an explicit short absolute path:
`--basetemp="C:/Users/Admin/AppData/Local/Temp/s12t03c_fin"`.
Long basetemp paths also break on Windows (WinError 206) — keep them short.

## 3. Full-tree pytest collection fails on duplicate test basenames — run per-dir

`pytest tests/s12/` (single command) fails collection:
```
import file mismatch:
imported module 'test_c1_closure' has this __file__ attribute: .../s12-t01/test_c1_closure.py
which is not the same as the test file we want to collect: .../s12-t02/test_c1_closure.py
HINT: remove __pycache__ / .pyc files and/or use a unique basename
```
Root cause: multiple test packages each have `test_c1_closure.py` (C1 closure tests)
but some dirs (`s12-t01`, `s12-t02`, `s12-t04a`) lack `__init__.py`, so pytest treats
all as the same top-level module. Pre-existing, not a code defect.

`--import-mode=importlib` does NOT help — it then fails `from conftest import ...`
(ModuleNotFoundError) in tests that import conftest by bare name.

Fix for the gate: run **per-directory** (`pytest tests/s12/s12-t01/` … ) and sum the
pass counts. Do NOT add `__init__.py` yourself if ownership forbids touching test dirs —
report it as an open item for a future correction instead.

## 4. Watchdog / loop script edits do NOT reload a running process

Editing `watch_24.sh` (e.g. switching `-m cmc/...` to `-m ocgfree/...`) does nothing to
the ALREADY-RUNNING `bash watch_24.sh` PID — it keeps executing the old in-memory code
(observed: nudge still used the old model after patch). Must `kill <pid>` the old loop,
then relaunch `bash watch_24.sh >> log 2>&1` in background. Verify with
`ps -ef | grep watch_24` and the new START line in the log. Also kill BOTH the parent
(`C1=...; bash watch_24.sh`) and child wrapper PID — kill one leaves the other alive.

## 5. Model quota exhaustion mid-sprint — diagnose, report, fall back

cmc route hit: `HTTP 503 ... [429]: You've reached your weekly usage limit for your plan.
Your limit resets at 2026-09-11T17:23Z`. This is a DEFINITIVE quota error — do NOT retry
the same model in a loop (rules §7: quota = diagnose + report blocker). Fall back to a
route the user previously approved (here `ocgfree/muse-spark-1.3-contributor-free`,
already used earlier the same day), record the fallback in a BLOCKER_LOG, and surface the
reset time so the user can re-decide after reset.
