# Fresh-session Hermes worker launcher for a PM-queued task (verified 2026-08-05).
# Copy to <worktree>\output\run-<task>-fresh.ps1, edit TASK_ID / REPO_ROOT / PROMPT,
# syntax-check with [System.Management.Automation.Language.Parser]::ParseFile,
# then launch:  powershell -NoProfile -ExecutionPolicy Bypass -File <script>
# (background=true + notify_on_complete=true). NEVER --resume an old session;
# each task gets a fresh compact session so Codex can review per-task.
$ErrorActionPreference = "Continue"
$repoRoot = "C:\Users\Admin\MotionForge2D-worktrees\<WORKTREE>"   # e.g. prepare-s05-t01
$logPath  = "C:\Users\Admin\MotionForge2D-worktrees\<WORKTREE>\output\<task>-hermes.log"
$prompt = @"
HARD WORKTREE GUARD: Before ANY write, run and verify:
1. `pwd` -> must be $repoRoot
2. `git rev-parse --show-toplevel` -> must be $repoRoot
3. `git status --short`
If `pwd` is wrong, `cd` to the expected root and re-verify. If git toplevel
differs, write NOTHING, report BLOCKED: WRONG_WORKTREE, exit immediately.
Every path you write MUST be under the expected root. NEVER write to
C:\Users\Admin\MotionForge2D (MAIN tree) or any other worktree.

TASK: <TASK_ID> - <TITLE> (fresh task, no resume)

Read completely:
- docs/pm/SESSION_PROTOCOL.md
- docs/pm/sessions/<TASK_ID>/TASK.md (full - your contract)
- docs/pm/sessions/<TASK_ID>/START_PROMPT.md
- (list the task's Required reading here, exact files)

IMPLEMENT: <one-paragraph contract; stay inside TASK.md allowed write scope;
bounded individual commands only; do NOT modify forbidden files>.
Sub-agents (Codex/Claude Code) MUST run in FOREGROUND blocking mode inside
your own tool call with a bounded timeout that blocks until they finish.
NEVER spawn a session-scoped background process and end your turn before it
completes - background children die when your CLI session exits and the task
silently writes NOTHING (verified incident S08-T01). Do not end your turn
until every validation command has run and REPORT.md is written.

VERIFY (each separately):
1. <new task tests>
2. <prior-task regressions>
3. Ruff
4. Mypy
5. git diff --check
6. Fresh scripts/quality-baseline.ps1 - record Run ID
7. <frontend/QA gates if any>

REPORT: update docs/pm/sessions/<TASK_ID>/LOG.md with real evidence, write
REPORT.md (changed files, exact test commands/results, Quality Run ID,
per-AC evidence), end with status SUBMITTED (never APPROVED, never
self-approve). Do NOT commit/push/deploy. No reset/checkout/clean/delete of
user data. Preserve all uncommitted changes. Do NOT touch channels.json,
data/, database, MAIN tree, or other worktrees. No mock/fake data.
"@
Set-Location $repoRoot
& hermes chat --query $prompt --source cli --max-turns 300 --provider custom --model ocg/deepseek-v4-flash --pass-session-id --checkpoints 2>&1 |
  Tee-Object -FilePath $logPath -Append
exit $LASTEXITCODE
