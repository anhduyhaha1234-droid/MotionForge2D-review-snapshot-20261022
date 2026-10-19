# S08 writer premature-exit recovery

Use this reference when a MotionForge2D spawned writer process exits normally (`exit code 0`) but the task may not actually be submitted.

## Trigger signals

- Background writer completes with exit 0, but output ends mid-thought or mid-edit (e.g. “let me write models.py”, “now I will patch…”).
- The writer says it stopped because “user didn't respond in time”.
- No explicit `SUBMITTED` line appears in the task `REPORT.md`.
- Expected allowlist artifacts are missing even though the process exited normally.

## Required manager recovery sequence

1. **Do not trust exit code 0 as completion**
   - Treat process exit as only “the subprocess stopped”, not “task complete”.
   - Audit disk state before reporting success.

2. **Check submission artifacts first**
   - Read/check the task `REPORT.md`; it must be `SUBMITTED`, not `PLANNED`.
   - Tail the task `LOG.md`; writer should have appended implementation and validation evidence.
   - Check expected files from `TASK.md` exist (migration, repository, schema, route, tests, evidence root).
   - Check `git status --short` for new/modified task files, but do not reset/clean.

3. **Check whether the writer actually wrote code**
   - Grep for task nouns in expected files (e.g. `Structural`, `OccurrenceSegment`, `SceneGraph`, `s08_a02`).
   - Inspect specific tails/regions rather than assuming from process output.

4. **If incomplete, resume the SAME writer session**
   - Use the session id printed by Hermes (`Resume this session with: hermes --resume <id>`).
   - Do not create a second writer session.
   - Keep the exact same provider/model/reasoning flags required by the user.
   - Tell the resumed writer explicitly what the audit found: `REPORT.md still PLANNED`, missing files, no tests, etc.

5. **Only report success after manager verification**
   - After writer `SUBMITTED`, manager independently runs diff/allowlist/migration/tests/static/protected-hash/port checks.
   - Stop at the required manager state (e.g. `MANAGER_VERIFIED_PENDING_CODEX_REVIEW`); do not auto-start the next task.

## Command pattern

```bash
# Audit after a normal-looking writer exit
cat docs/pm/sessions/<task>/REPORT.md | head -30
cat docs/pm/sessions/<task>/REPORT.md | tail -60
cat docs/pm/sessions/<task>/LOG.md | tail -80
ls app/persistence/structural_evidence.py app/schemas/structural_evidence.py \
   app/api/routes/structural_evidence.py migrations/versions/*s08_a02* \
   tests/test_s08_a02* 2>&1
grep -n "Structural\|OccurrenceSegment\|SceneGraph" app/persistence/models.py | head -60

# Resume same session if incomplete
hermes chat --resume <session_id> --no-restore-cwd -q "Continue <task> from exact current state..." \
  --provider custom:vietapi --model deepseek-v4-flash \
  --max-turns 500 --pass-session-id --accept-hooks --yolo --source tool
```

## Pitfalls

- A writer can exit code 0 after only reading or planning. Exit code is not an acceptance gate.
- Do not claim “launched” or “submitted” from intent or partial stdout; require real process/session evidence and disk artifacts.
- If a prior writer died before writing anything, resuming is still preferred because it preserves model-quality/session lineage and avoids two-writer contamination.
