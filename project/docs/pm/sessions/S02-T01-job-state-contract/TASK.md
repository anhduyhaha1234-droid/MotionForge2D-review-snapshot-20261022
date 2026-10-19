# S02-T01 - Durable job state-machine contract

**Status:** APPROVED
**Epic:** E01 - Durable Domain, Persistence and Jobs
**Sprint:** S02 - Durable processing
**Gate:** G1 - Foundation green
**Depends on:** S01 exit (APPROVED)

## User outcome

The durable Job/JobStep boundary, retry/error/cancellation semantics, leases,
checkpoints and artifact publication rules are unambiguous before schema or
worker implementation begins.

## Required reading

1. `docs/pm/SESSION_PROTOCOL.md`
2. `docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md`
3. `docs/MASTER_PLAN_V1.md` (job framework and worker sections)
4. `docs/PRODUCT_REQUIREMENTS_V2.md` (durable job requirements)
5. `app/schemas/__init__.py`
6. `app/workflow/job_service.py`
7. `app/persistence/models.py`
8. `app/persistence/artifacts.py`
9. `app/api/routes/jobs.py`
10. `tests/test_api.py` job tests
11. `tests/test_clip_cancel_persist.py`

## Allowed write scope

- `docs/architecture/DURABLE_JOB_CONTRACT.md`
- `docs/pm/sessions/S02-T01-job-state-contract/`

## Forbidden scope

- Runtime source, migrations, dependencies, database files and user data.
- PRD, Master Plan, roadmap and prior sprint evidence.
- Job/JobStep ORM implementation, worker implementation and API cutover.

## Acceptance criteria

- [ ] AC1 Job and JobStep identity, ownership, dependency, resource class,
      priority, progress and timestamps are explicit.
- [ ] AC2 Allowed states/transitions and terminal-state invariants are complete,
      including cooperative cancellation and retry classification.
- [ ] AC3 Lease ownership/expiry/heartbeat, stale-worker fencing and restart
      reconciliation decisions are explicit.
- [ ] AC4 Idempotency, attempt accounting, checkpoints and artifact staging/
      publication rules prevent duplicate effects and false-ready outputs.
- [ ] AC5 Transaction boundaries, error envelope, observability and API/domain
      compatibility with the legacy in-memory service are explicit.
- [ ] AC6 S02-T02..T05 implementation ownership and mandatory 7/7 gates are clear.

## Required validation

```powershell
rg -n "^## |JobStep|transition|lease|heartbeat|fenc|retry|cancel|idempoten|checkpoint|artifact|7/7" docs/architecture/DURABLE_JOB_CONTRACT.md
git diff --check -- docs/architecture/DURABLE_JOB_CONTRACT.md docs/pm/sessions/S02-T01-job-state-contract
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
```
