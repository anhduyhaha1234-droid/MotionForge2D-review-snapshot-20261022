# CORRECTION launcher (Codex CHANGES_REQUESTED) - resume SAME session, SAME model.
# Copy to <worktree>\output\run-<task>-cN.ps1, fill TASK_ID / SESSION_ID / MODEL / PROMPT.
# Verified pattern 2026-08-16/17 (S08 correction cycle). NEVER --resume a DIFFERENT task's session.
$ErrorActionPreference = "Continue"
$repoRoot = "C:\Users\Admin\MotionForge2D-worktrees\<WORKTREE>"
$logPath  = "C:\Users\Admin\MotionForge2D-worktrees\<WORKTREE>\output\<task>-c<N>-hermes.log"
$prompt = @"
HARD WORKTREE GUARD: before ANY write verify pwd = <repoRoot>; git rev-parse
--show-toplevel = same; git branch --show-current = <branch>; then git status
--short snapshot. If ANY differs, write NOTHING, report BLOCKED:
WRONG_WORKTREE, exit immediately. Never write MAIN or other worktrees.

CORRECTION ROUND (Codex CHANGES_REQUESTED). Fix ONLY the findings below, in
THIS session. Append a CORRECTION ROUND section to LOG.md and REPORT.md
(preserve history; keep status SUBMITTED). Do NOT self-approve, do NOT touch
PM_REVIEW.md.

<Codex findings verbatim, numbered B1..Bn / C1..Cn etc.>

VALIDATION (fresh isolated roots, cache disabled, shallow basetemps under
C:/Users/Admin/AppData/Local/Temp/<task>-c<N>-*):
1. Focused new/corrected tests
2. Dependency suites of prior tasks (all manager-verified)
3. Migration round-trip if schema changed (isolated subshell env, unset after)
4. Cross-sprint regressions (S05 41-suite shallow basetemp; S02/S03/S06 relevant)
5. ruff changed files; mypy app; git diff --check; final git status --short
6. Protected-data comparison: MAIN channels.json SHA-256 <hash>; MAIN
   data/motionforge.db <bytes> bytes

SAFETY LESSONS (mandatory): never bare TestClient(app) outside the conftest
client fixture; pytest fixtures only for isolated DBs; never spawn background
coding children (codex FOREGROUND blocking only). Do NOT end your turn until
every validation ran and LOG/REPORT append is done. Stop after SUBMITTED and exit.
"@
Set-Location $repoRoot
& hermes chat --resume <SESSION_ID> --query $prompt --source cli --max-turns 300 --provider custom --model <SESSION_ORIGINAL_MODEL> --pass-session-id --checkpoints 2>&1 |
  Tee-Object -FilePath $logPath -Append
exit $LASTEXITCODE
