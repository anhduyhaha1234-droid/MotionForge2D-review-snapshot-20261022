# MotionForge2D S09 Full-Sprint Manager Run — Session Reference (2026-08-23/24)

Condensed from the S09 sprint where one manager chat ran 11 tasks (T00-I01..I05, T01..T06B) to
`TASK_MANAGER_VERIFIED` in ~28h. Environment: Windows worktree `s08-integration`, workers are
`hermes chat --provider custom --model alpha -q "$(cat prompt.txt)" --yolo --pass-session-id -Q`
run as background processes with per-task output lanes.

## What actually worked

### Dispatch pattern
- One TASK.md packet per task under `docs/pm/sessions/<ID>/TASK.md` containing: Role + model route,
  Step 0 (read rules → print RULES_LOADED), verified-context summary (what previous workers left on
  disk), Outcome list, Acceptance gate with BINARY evidence requirements, strict Write allowlist,
  FORBIDDEN list, end condition (STATUS: TASK_SUBMITTED then STOP).
- Prompt file per task under `output/s09/<run>/tXX/prompt.txt` is a thin pointer: "Đọc TASK.md đầy
  đủ tại <path> ... Write-set chỉ đúng allowlist trong TASK.md."
- Parallel waves only when write-sets are disjoint (I02 services/adapters ∥ I03 scripts/fixtures).
  Sequential chain T01→T02→… otherwise.

### Verify-by-hand every submission (never trust worker REPORT)
- Re-run the focused suites twice with different basetemps (`--basetemp=%TEMP%/mgr-X-v1`, `-v2`)
  and compare pass counts.
- Alembic: `ScriptDirectory.from_config(Config('alembic.ini')).get_heads()` — assert single head.
- models.py additive proof: difflib vs saved baseline file, count lines starting `-`.
- OpenAPI path counts before/after (removed must be 0).
- Write-set audit: `find app tests migrations -newermt "<dispatch time>" -type f ! -path "*__pycache__*"`
  and diff against allowlist.
- ruff/mypy spot-check on exactly the files the worker owned (NOT on .ts files — ruff is a Python
  linter; running it on TypeScript produced a meaningless "561 errors" scare).
- Frontend gates are worker-reported (tsc/eslint) unless time permits; Playwright specs live under
  `frontend/e2e/` not repo-root `e2e/`.

### Failure modes seen (all recovered via owner-session resume)
1. **EXIT=4 crash mid-edit** — resume same session with a correction packet listing exact findings
   (file, line-ish, expected behavior). Workers fixed both ORM-parity CHECK mismatch and test-seed
   PK duplication cleanly this way.
2. **EXIT=0 but died before REPORT.md** — most common. Core work was done; write a resume packet
   that says "Manager verified state X/Y/Z on disk; remaining work is only REPORT+LOG; STOP after".
3. **Silent process death** (no wrapper EXIT line, log frozen, python.exe gone from tasklist):
   happened twice mid-wave, plus single-task repeats. Always: verify log size frozen over 60–90s,
   check PID via `wmic process where "ProcessId=<pid>"`, then re-dispatch resume to owner session.
4. **"No reply: model returned empty content after retries"** — upstream model returning empties in
   bursts (3× in 2 hours at sprint end). Router /v1/models stays 200 so health checks don't catch it.
   Countermeasure: shorter resume prompts, instruct worker to log progress after each small step so
   each surviving window banks progress.

### Session-id discovery
Wrapper logs don't reliably echo the session id. Query Hermes state.db:
```sql
SELECT id, started_at FROM sessions WHERE started_at > <epoch> ORDER BY started_at;
SELECT content FROM messages WHERE session_id=? AND role='user' ORDER BY rowid LIMIT 1;
```
First user message identifies which task owns which session. Resume with
`hermes chat --resume <session_id> -q "$(cat correction.txt)" --yolo -Q >> dispatch.log 2>&1`.

### Final gate reality
Full-repo regression immediately caught a stale allowlist test (`test_durable_job_persistence.py`
expected-tables set missing 6 additive tables — pre-existing gap outside I04's allowlist). Handle
as a narrow correction worker (one test file + adversarial plant-table proof), never as a manager
hand-edit. Note: downgrade-to-base may be blocked by earlier-sprint irreversible migrations by
design — round-trip to parent revision instead.

## Pitfalls
- Don't run ruff on `.ts` files.
- Playwright "skipped" can be by-design mobile checks — read the spec before treating skip as fail.
- Worker EXIT=0 ≠ done: always check REPORT.md exists AND has STATUS line.
- Log-size delta over 60–90s is the reliable liveness signal on Windows (tasklist/wmic for PID
  confirmation); MSYS `ps` PIDs don't map.
- Keep correction packets short and specific; giant prompts raise the odds of hitting the
  empty-content failure mode.
