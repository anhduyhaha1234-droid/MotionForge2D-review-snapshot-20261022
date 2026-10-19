# S02-T02 - Durable job schema and lifecycle repository

**Status:** APPROVED
**Epic:** E01 - Durable Domain, Persistence and Jobs
**Sprint:** S02 - Durable processing
**Gate:** G1 - Foundation green
**Depends on:** S02-T01 (APPROVED)

## User outcome

Jobs, steps, attempts, events, leases and idempotency survive database reopen,
and every lifecycle mutation is enforced transactionally without changing the
current runtime job API.

## Required reading

1. `docs/pm/SESSION_PROTOCOL.md`
2. `docs/architecture/DURABLE_JOB_CONTRACT.md`
3. `docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md`
4. `app/persistence/models.py`
5. `app/persistence/database.py`
6. `app/persistence/migrations.py`
7. `migrations/versions/`
8. `tests/test_persistence_bootstrap.py`
9. `app/workflow/job_service.py` (compatibility boundary only)

## Allowed write scope

- `app/persistence/models.py`
- `app/persistence/jobs.py`
- `app/persistence/__init__.py`
- `migrations/versions/`
- `tests/test_durable_job_persistence.py`
- `tests/test_persistence_bootstrap.py`
- `docs/architecture/DURABLE_JOB_PERSISTENCE.md`
- `docs/pm/sessions/S02-T02-job-persistence/`

## Forbidden scope

- Current runtime `app/workflow/job_service.py`, API routes and frontend.
- Dependency files, existing migrations, legacy JSON and user data.
- Worker loops, background threads/processes, reconciliation and API cutover.
- Roadmap, PRD, Master Plan and prior session evidence.

## Acceptance criteria

- [ ] AC1 Add immutable forward Alembic migration for Job, JobStep, JobAttempt,
      JobEvent and JobLease with contract constraints/FKs/indexes.
- [ ] AC2 Upgrade from the S01 revision preserves existing rows; fresh upgrade
      and database reopen work; downgrade is not assumed as recovery.
- [ ] AC3 Repository creates jobs/steps atomically and enforces one active or
      completed job per `(workspace, idempotency_key, input_generation)` while
      terminal failed/cancelled retry creates exactly one linked successor.
- [ ] AC4 Guarded state transitions validate allowed endpoints, revisions and
      fence tokens; every accepted transition appends a JobEvent in one tx.
- [ ] AC5 Attempt accounting, progress/checkpoint/error envelopes and lease
      acquire/heartbeat/release persist with bounded transactional behavior.
- [ ] AC6 No worker/API cutover or dual-write; targeted tests plus 7/7 PASS.

## Required validation

```powershell
python -m pytest -q tests/test_durable_job_persistence.py
python -m pytest -q tests/test_persistence_bootstrap.py tests/test_durable_job_persistence.py
python -m ruff check app tests
python -m mypy app
git diff --check
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
```
