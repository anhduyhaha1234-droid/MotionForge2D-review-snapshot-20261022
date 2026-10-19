# S02-T03 - Durable worker execution, retry and cancellation

**Status:** APPROVED
**Epic:** E01 - Durable Domain, Persistence and Jobs
**Sprint:** S02 - Durable processing
**Gate:** G1 - Foundation green
**Depends on:** S02-T02 (APPROVED)

## User outcome

A separately driven worker claims durable queued Jobs, executes registered step
handlers, heartbeats, checkpoints, retries transient failures and cooperatively
cancels without running long work inside an HTTP request.

## Required reading

1. `docs/pm/SESSION_PROTOCOL.md`
2. `docs/architecture/DURABLE_JOB_CONTRACT.md`
3. `docs/architecture/DURABLE_JOB_PERSISTENCE.md`
4. `app/persistence/jobs.py`
5. `app/persistence/artifacts.py`
6. `app/workflow/job_service.py` (legacy compatibility only)
7. `app/workflow/ingest_service.py`
8. `app/workflow/render_service.py`
9. `tests/test_durable_job_persistence.py`

## Allowed write scope

- `app/workflow/durable_worker.py`
- `app/persistence/jobs.py`
- `app/persistence/__init__.py`
- `app/workflow/__init__.py`
- `tests/test_durable_worker.py`
- `docs/architecture/DURABLE_WORKER.md`
- `docs/pm/sessions/S02-T03-durable-worker/`

## Forbidden scope

- API routes, frontend, legacy `job_service.py`, migrations/schema and deps.
- Reconciliation/startup recovery (T04) and runtime/API cutover (T05).
- Real GPU/model/network work; use synthetic deterministic handlers.
- User data, roadmap, PRD, Master Plan and prior session evidence.

## Acceptance criteria

- [ ] AC1 Worker has explicit start/stop/run-once lifecycle and atomic queue
      claim ordered by priority/time; no background work starts on import.
- [ ] AC2 Registered handlers receive versioned input/checkpoint context and
      fenced progress/checkpoint/cancel callbacks; unknown handler fails safely.
- [ ] AC3 Heartbeat keeps a live claim; lost/stale token aborts execution and
      cannot publish state or outputs.
- [ ] AC4 Transient failures use bounded deterministic-testable backoff and
      attempts; permanent/exhausted failures persist stable error envelopes.
- [ ] AC5 Cancel wins before next effect/step, drains to terminal cancelled and
      exposes no final output; completed-vs-cancel race is serialized.
- [ ] AC6 Step/job completion requires declared outputs ready/validated; worker
      never marks staging/missing output complete.
- [ ] AC7 No API cutover/reconciler/schema/dependency changes; targeted and 7/7 PASS.

## Required validation

```powershell
python -m pytest -q tests/test_durable_worker.py
python -m pytest -q tests/test_durable_job_persistence.py tests/test_durable_worker.py
python -m ruff check app tests
python -m mypy app
git diff --check
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
```
