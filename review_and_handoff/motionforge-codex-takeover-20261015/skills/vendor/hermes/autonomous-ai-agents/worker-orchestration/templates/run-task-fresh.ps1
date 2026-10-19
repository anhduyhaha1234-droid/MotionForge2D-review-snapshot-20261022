# Worker launcher — copy per task; replace <TASK>, <EXPECTED_ROOT>, <MAX_TURNS>
# Usage: run via `terminal(background=true, notify_on_complete=true)`.
# Key lesson: `hermes chat` CLI does NOT inherit Set-Location when the Hermes
# desktop daemon is running — the HARD WORKTREE GUARD must live in the PROMPT,
# and the manager must check MAIN git status before/after.
$ErrorActionPreference = "Continue"
$repoRoot = "<EXPECTED_ROOT>"   # e.g. C:\Users\Admin\MotionForge2D-worktrees\prepare-s05-t01
$logPath  = Join-Path $repoRoot "output\s0X-tYY-hermes.log"

$prompt = @"
HARD WORKTREE GUARD: Before ANY write, run and verify:
1. `pwd` -> must be <EXPECTED_ROOT>
2. `git rev-parse --show-toplevel` -> must be <EXPECTED_ROOT>
3. `git status --short`
If `pwd` is wrong, `cd` to the expected root and re-verify. If git toplevel
differs, write NOTHING, report BLOCKED: WRONG_WORKTREE, exit immediately.
Every path you write MUST be under the expected root. NEVER write to the MAIN
tree or other worktrees.

TASK: <TASK-ID> - <TASK TITLE> (fresh task, no resume)

Read completely:
- docs/pm/SESSION_PROTOCOL.md
- docs/pm/sessions/<TASK-PACKET>/TASK.md (full - your contract)
- docs/pm/sessions/<TASK-PACKET>/START_PROMPT.md
- docs/pm/ROADMAP.md
- <approved architecture contracts + prior task REPORT/LOG>
- current git status and focused diffs

IMPLEMENT: <outcome>. Stay inside TASK.md allowed write scope. Bounded
individual commands only.

VERIFY (each separately):
1. <new task tests>
2. <prior-task regressions>
3. Ruff
4. Mypy
5. git diff --check
6. Fresh scripts/quality-baseline.ps1 - record Run ID

REPORT: update <TASK-PACKET>/LOG.md with real evidence, write REPORT.md
(changed files, exact test commands/results, Quality Run ID, <task-specific
evidence>), end with status SUBMITTED (never APPROVED, never self-approve).
Do NOT commit/push/deploy. No reset/checkout/clean/delete of user data.
Preserve all uncommitted changes. Do NOT touch channels.json, data/, database,
MAIN tree, or other worktrees. NO MOCK/FAKE data.
"@

Set-Location $repoRoot
& hermes chat --query $prompt --source cli --max-turns <MAX_TURNS> --provider custom --model ocg/deepseek-v4-flash --pass-session-id --checkpoints 2>&1 |
  Tee-Object -FilePath $logPath -Append
exit $LASTEXITCODE
