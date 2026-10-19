# S02-T04 - Restart reconciliation and safe resume

**Status:** APPROVED
**Epic:** E01 - Durable Domain, Persistence and Jobs
**Sprint:** S02 - Durable processing
**Gate:** G1 - Foundation green
**Depends on:** S02-T03 (APPROVED)

## User outcome

After a forced worker/application close, expired in-flight Jobs are fenced and
either resume safely from durable checkpoints or fail with an actionable stable
error; stale workers can never publish afterward.

## Required reading

1. `docs/pm/SESSION_PROTOCOL.md`
2. `docs/architecture/DURABLE_JOB_CONTRACT.md`
3. `docs/architecture/DURABLE_JOB_PERSISTENCE.md`
4. `docs/architecture/DURABLE_WORKER.md`
5. `app/persistence/jobs.py`
6. `app/workflow/durable_worker.py`
7. `tests/test_durable_job_persistence.py`
8. `tests/test_durable_worker.py`

## Allowed write scope

- `app/workflow/job_reconciler.py`
- `app/workflow/durable_worker.py`
- `app/workflow/__init__.py`
- `app/persistence/jobs.py`
- `app/persistence/__init__.py`
- `tests/test_job_reconciliation.py`
- `docs/architecture/JOB_RECONCILIATION.md`
- `docs/pm/sessions/S02-T04-restart-reconciliation/`

## Forbidden scope

- API routes/frontend/legacy JobService and runtime cutover.
- Schema/migrations/dependencies and user/legacy data.
- Job handlers for real GPU/network/media workloads.
- Roadmap, PRD, Master Plan and prior evidence.

## Acceptance criteria

- [ ] AC1 Explicit run-once/startup reconciler scans only expired active leases
      using bounded batches; no import-time execution.
- [ ] AC2 Reconciliation atomically invalidates old fence token and records
      `running|cancelling -> fenced -> queued|failed` events.
- [ ] AC3 Retryable Jobs with attempts remaining and valid versioned checkpoint
      requeue/resume; incompatible/missing-required checkpoint fails closed.
- [ ] AC4 Cancelling Jobs reconcile to cancelled without running new effects;
      exhausted/permanent/input-changed Jobs fail with stable envelope.
- [ ] AC5 Old worker token is rejected after reconciliation and cannot mutate or
      publish; new worker continues from committed checkpoint without duplicates.
- [ ] AC6 Forced-close/reopen integration tests prove state/events/attempts and
      artifact visibility across fresh engine/session instances.
- [ ] AC7 No API cutover/schema/deps; targeted tests and 7/7 PASS.

## Required validation

```powershell
python -m pytest -q tests/test_job_reconciliation.py
python -m pytest -q tests/test_durable_job_persistence.py tests/test_durable_worker.py tests/test_job_reconciliation.py
python -m ruff check app tests
python -m mypy app
git diff --check
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
```
