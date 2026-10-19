# Read-Only Helper Parallelization (RO-1/RO-2 pattern, verified 2026-08-17 S08 correction run)

## When to use
PM-gated sprint/correction run where the user mandates: "sử dụng tối đa 2 helper thread READ-ONLY để chuẩn bị trước công việc", strictly no additional writer, no filesystem/runtime changes, helpers return only in chat.

## Dispatch shape
Use `delegate_task` (batch ≤2 tasks, or single re-dispatch after a 502). Each brief must be fully self-contained (helpers have NO conversation context):

- Role: leaf; no nested delegation.
- Context: worktree path + branch, current writer identity (task ID + session ID + launcher/log), the approved dependency sequence, which task is LIVE (helpers must not read it), protected-data baseline VALUES (given, never hashed/opened by helper).
- Goal: produce ONE report in the exact output format; end after one report; no background, no polling.
- Tools: only read_file, search_files, terminal for read-only ls/stat/pwd.
- Forbidden: write_file, patch, pytest/Playwright/npm/build/lint/mypy/ruff, app/worker/browser/server/model startup, SQLite, migrations, cache/output/log/evidence creation, git commit/push/merge/reset/checkout/restore/clean/stash, git diff/status of live writer changes, reading app/** frontend/** tests/** migrations/**, reading the live writer's log.
- Escalation rule verbatim: "Nếu không chắc một thao tác có read-only không → BỎ QUA thao tác đó."
- Reply language: match the user's language (Vietnamese here).

## RO-1 brief — NEXT-GATE READINESS
Allowed reads: CODEX_PM_HANDOFF.md, SESSION_PROTOCOL.md, sprint contract, packets (TASK/START_PROMPT/REPORT/LOG) of DONE/stable tasks, tracking file, architecture contracts listed as Required reading.

Output format (verbatim):
```
RO-1 READINESS REPORT
- Next Task ID:
- Required dependencies:
- Binary acceptance checklist:
- Likely scope conflicts:
- Contract ambiguities:
- Stop/block conditions:
- Recommendation: READY_AFTER_CURRENT_GATE hoặc BLOCKED
```

## RO-2 brief — VALIDATION & EVIDENCE PLANNER
Allowed reads: sprint contract + sprint report, task packets (TASK/REPORT/LOG), tracking file, docs/architecture/*. NEVER executes; plans only.

Output format (verbatim):
```
RO-2 VALIDATION PLAN
- Targeted gates:
- Integration gates:
- Production/GPU evidence:
- UI/Playwright evidence:
- Security checks:
- Isolation requirements:
- Protected-state checks:
- Commands to run later:
- Evidence expected:
- Risks/gaps:
```

## Manager handling sequence
1. BEFORE dispatch: confirm single-writer liveness — log mtime fresh (<60s) + tail shows tool-call lines; note that a `CommandLine -match 'hermes chat'` process query matches your OWN bash wrapper chain (inspect full CommandLine + ParentProcessId).
2. Dispatch; writer continues normally; manager stays read-only. Do NOT act on helper findings until the writer exits.
3. After the batch completes: check EACH task result — `status=completed` AND a report body present. A 502'd helper returns a note + transcript, no report → re-dispatch a fresh identical brief (idempotent, ~20 min).
4. Verify helper claims on disk yourself (e.g. helper says "TASK.md lacks Required reading" → read the file; "finding list absent" → grep docs/pm) before treating them as basis for the next task.
5. After writer exit + manager gate: use the RO-1 checklist, run RO-2 commands on isolated temp roots, record MANAGER_VERIFIED_PENDING_SPRINT_REVIEW, then open the next dependency.

## Setup confirmation format (deliver in chat right after dispatch)
```
READ-ONLY PARALLELIZATION ACTIVE
- Active coding writer: <task + session id + launcher>
- Active Task ID/session:
- RO-1 scope:
- RO-2 scope:
- Confirmation that only one writer exists: <live evidence>
- Confirmation helpers cannot write/run runtime/tests:
- Any safety limitation:
```

## Timeline estimation (verified 2026-08-17)
- Ground truth: `stat -c 'birth: %w | mtime: %y | size: %s'` on the writer log; fresh mtime = alive and working.
- Writer phase from log tail: "N/N green. Now adding the correction-specific tests" = implementation done, near end; "submitting" = last stretch.
- Historical durations from the tracking file (original runs + prior corrections) for the remaining tasks; add ~20-30m manager gate per task (review + pytest; +E2E/dev-server for frontend tasks) and ~45-75m for sprint exit (fresh 7/7 baseline + exit report + protected-state comparison).
- Biggest pessimistic swing: GPU/production-provider smokes (+30-60m); an unexpected Codex CHANGES_REQUESTED round adds +2-3h (not in the base estimate).
