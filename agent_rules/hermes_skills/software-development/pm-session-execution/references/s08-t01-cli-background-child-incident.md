# S08-T01 CLI worker background-child death — incident record (2026-08-06)

## What happened

S08-T01 (Durable ObjectOccurrence/ObjectRole Domain) was launched via the
standard fresh launcher (`output/run-s08-t01-fresh.ps1`, `hermes chat --query
... --source cli --max-turns 300`). The launcher process exited **normally
(exit code 0)** after 14m24s. The log tail showed:

```
Resume this session with: hermes --resume 20260805_235138_61ad7a
Session:        20260805_235138_61ad7a
Duration:       14m 24s
Messages:       97 (1 user, 95 tool calls)
```

## Root cause

Inside the CLI session, the worker had:
1. Written a full implementation brief for Codex to
   `C:/Users/Admin/AppData/Local/Temp/s08t01_claude_prompt.txt` (28KB).
2. Launched Codex as a **session-scoped background process**
   (`proc_a4ab082b8cdf`) via `terminal(background=true)`.
3. Ended its turn with "waiting for the notification".

A `hermes chat --source cli` session ends when the turn ends. Session-scoped
background children are killed on session exit. So Codex never ran to
completion (or was killed at spawn), **no implementation files were written**,
and the manager's `notify_on_complete` fired on a hollow exit.

## Evidence at manager poll (00:05, right after exit)

- `git status --short | wc -l` in worktree: **100** — identical to pre-task
  P00 baseline (93 + 6 P00 packet files + 1 sprint contract). NO new files.
- `docs/pm/sessions/S08-T01-object-role-domain/REPORT.md` → **NOT_STARTED**.
- `process(action='list')` → Codex child `proc_a4ab082b8cdf` GONE.
- MAIN tree count 45 → 46 only because the manager's own watcher script
  (`scripts/watch-s08-t01.sh`) was added — not a worker write.
- Manager's own `find -newermt` scope probe timed out (scanned .git/output);
  NOT a worker fault — do not repeat that command without exclusions.

## Recovery performed

Resumed the **exact same session** (`20260805_235138_61ad7a`) via
`output/run-s08-t01-resume.ps1`:

```
hermes chat --resume 20260805_235138_61ad7a --query "<recovery prompt>" \
  --source cli --max-turns 300 --provider custom --model ocg/deepseek-v4-flash \
  --pass-session-id --checkpoints
```

Recovery prompt contents (the pattern to reuse):
- MANAGER NOTICE with root cause + disk evidence (worktree count unchanged,
  REPORT NOT_STARTED, background child killed on session exit).
- Re-run hard worktree guard; complete the task in THIS turn.
- Sub-agents allowed ONLY in foreground blocking mode (bounded timeout that
  blocks until done); NEVER background + end turn.
- Contract unchanged (TASK.md); may reuse the temp brief
  (`s08t01_claude_prompt.txt`) or rewrite it.
- All validations, LOG append, REPORT=SUBMITTED, then exit.

Tracking file got an INCIDENT row: first-run session ID + resume lineage, so
the Codex sprint review sees one session continuing, not two Task IDs.

## Rules extracted

1. Worker prompts MUST forbid "background process + end turn" delegation.
2. Manager must treat exit 0 of a CLI worker as unverified until artifacts
   prove work (status count delta, REPORT status, LOG evidence).
3. Same Task ID non-completion → resume exact session; never fresh session.
4. When a resumed run uses a new log file, kill the old watcher and start a
   new one pointed at the new log (watcher SRC is hard-coded per script).
