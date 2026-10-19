# Manager-Lane Sprint Orchestration Lessons (MotionForge2D, 2026-08-23/24)

Hard-won patterns from running a full 11-task sprint (S09: T00×5 + T01..T06B) as HERMES MANAGER dispatching worker sessions via `hermes chat --provider custom --model alpha -q ... --yolo --pass-session-id`.

## 1. Worker early-exit without REPORT — the dominant failure mode (~6 of 13 dispatches)

Symptoms: `EXIT=0`, log frozen (size stable across 30–120s samples), no wrapper EXIT line appended, no REPORT.md. Causes observed:
- Model returns "⚠️ No reply: empty content after retries and any fallback providers" (transient upstream instability; `/v1/models` still returns 200 so health checks alone are insufficient).
- Worker considers itself done after its last tool call but before writing REPORT.md.

Response protocol (worked every time):
1. **Verify disk state FIRST** before writing any resume prompt: `ls` the deliverable files, run the focused test suites yourself. The work is usually mostly done; the resume prompt should say exactly what remains.
2. **Resume the EXACT owner session** (`--resume <session-id>`) with a finding-list packet:
   - What's already on disk (verified by manager, listed file-by-file)
   - Exact remaining items with line-level findings where applicable
   - Same write-set constraint restated
   - "STATUS: TASK_SUBMITTED rồi STOP"
3. **Never create a new session for corrections.** Session lineage is how attribution survives Codex review.

Finding-list resume packets with line numbers ("line 31: HEAD = \"d8e9f0a1b2c3\" stale") consistently produced one-shot fixes.

## 2. Manager verification = run tests yourself, never trust worker reports

Worker self-reports were wrong or incomplete repeatedly (claimed gates not run, REPORT missing, tests failing at handoff). Acceptance for EVERY task:
- Focused suite ×2 consecutive PASS with different basetemp dirs
- `ruff check` on write-set files
- `mypy` spot-check on new app files
- Alembic live heads via `ScriptDirectory.from_config(cfg).get_heads()`
- Zero-removed diff proof for additive-only files (difflib vs baseline snapshot)
- Write-set audit via `find -newermt <dispatch-time>` filtered to allowlist

Note: ruff is a Python linter — running it on `.ts` files produces hundreds of meaningless "invalid-syntax" errors. Frontend gates are tsc/eslint only.

## 3. Cross-task assertion staleness after migrations

When any worker adds a migration, the alembic head moves and OTHER pre-existing test files that hard-code the old head break — even though those files belong to nobody in the current wave. The final full-suite gate caught two systematic classes:
- Expected-tables allowlists missing additive tables from other tasks' migrations (fix: extend set additively with source comments, keep unexpected-tables assertion fail-closed)
- Single-head assertions hard-coding an old revision string

Fix pattern: normalize to live discovery (`ScriptDirectory.from_config(Config('alembic.ini')).get_heads()`), NEVER hard-code the NEW head either (it goes stale on the next migration). Keep revision-identity asserts (`mig.revision == "d8e9f..."`) intact — those test the file itself.

Budget 1–2 correction rounds in the final sprint gate for exactly this class of breakage.

## 4. Windows SQLite basetemp teardown noise

Full-suite runs produce hundreds of `PermissionError [WinError 32]` errors from pytest's temp-dir rmtree racing sqlite engine handles (`refuse.db`, `c3.db` etc). These are infrastructure noise — the tests themselves passed/fail correctly before cleanup. Judge gates by the FAILED count and pass counts; use a fresh basetemp per run; don't let the error count alarm you into re-running.

## 5. Dispatch hygiene

- `mkdir -p` the log directory BEFORE redirecting `> path/log` — bash dies instantly otherwise, hermes never starts.
- Dispatch/resume always `terminal(background=true, notify_on_complete=true)`.
- Foreground timeout kills the parent shell while the child keeps running orphaned — background always.
- Liveness = log-size delta over 60–240s samples + wmic/tasklist process existence. MSYS `ps` maps PIDs wrong.
- When model-empty exits cluster (>2/hour), shorten resume prompts to step lists ("làm tuần tự, mỗi bước ghi log ngay") — smaller turns survive better.

## 6. Registry / report discipline

- Append registry entries only at safe boundaries (between waves / after worker exit).
- When a prior conclusion was wrong (declared dead but alive), append an explicit CORRECTION entry — transparent corrections beat silent rewrites during Codex review.
- Terminal state vocabulary: per-task `TASK_MANAGER_VERIFIED_PENDING_CODEX_REVIEW`; whole-sprint `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`. Workers never self-APPROVE; manager never APPROVES — only Codex.
