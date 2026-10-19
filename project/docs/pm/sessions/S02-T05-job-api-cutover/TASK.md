# S02-T05 - Durable Job API cutover and recovery acceptance

**Status:** APPROVED
**Epic:** E01 - Durable Domain, Persistence and Jobs
**Sprint:** S02 - Durable processing
**Gate:** G1 - Foundation green
**Depends on:** S02-T04 (APPROVED)

## User outcome

Every backend job exposed by the current API is durably submitted, polled and
cancelled; state survives application restart and no authoritative job truth
remains only in RAM.

## Required reading

1. `docs/pm/SESSION_PROTOCOL.md`
2. `docs/architecture/DURABLE_JOB_CONTRACT.md`
3. `docs/architecture/DURABLE_JOB_PERSISTENCE.md`
4. `docs/architecture/DURABLE_WORKER.md`
5. `docs/architecture/JOB_RECONCILIATION.md`
6. `app/api/deps.py`
7. `app/api/routes/jobs.py`
8. Job-creating blocks in `app/api/routes/projects.py`
9. `app/api/helpers.py`
10. `app/schemas/__init__.py` Job models/enums
11. `app/workflow/job_service.py`
12. `app/workflow/durable_worker.py`
13. `app/workflow/job_reconciler.py`
14. `app/main.py`
15. Existing API/job/cancel tests

## Allowed write scope

- `app/api/deps.py`
- `app/api/app.py`
- `app/api/helpers.py`
- `app/api/routes/jobs.py`
- `app/api/routes/projects.py`
- `app/schemas/__init__.py`
- `app/workflow/job_service.py`
- `app/workflow/durable_worker.py`
- `app/workflow/job_reconciler.py`
- `app/workflow/__init__.py`
- `app/persistence/jobs.py`
- `app/persistence/__init__.py`
- `app/main.py`
- `app/lifecycle.py`
- `app/workflow/job_handlers.py`
- `tests/test_api.py`
- `tests/test_clip_cancel_persist.py`
- `tests/test_durable_job_api.py`
- `tests/conftest.py`
- `docs/architecture/DURABLE_JOB_API_CUTOVER.md`
- `docs/pm/sessions/S02-T05-job-api-cutover/`

## Forbidden scope

- Schema/migrations/dependency changes.
- Frontend behavior or response-breaking changes.
- User/legacy JSON/media mutation outside explicit temp tests.
- Fake dual-write to RAM + DB or migration of impossible pre-cutover RAM jobs.
- Roadmap, PRD, Master Plan and prior evidence.

## Acceptance criteria

- [ ] AC1 Application lifecycle explicitly initializes/upgrades only via the
      approved bootstrap path, then reconciles before worker polling; shutdown
      stops/joins worker/reconciler without import-time side effects.
- [ ] AC2 All existing API job submissions use durable IDs/input manifests and
      reconstructable registered handlers; no endpoint passes an ephemeral
      closure as authoritative job definition.
- [ ] AC3 GET/cancel preserve existing response/status semantics (200/400/404)
      with additive durable fields and hide internal `fenced` state.
- [ ] AC4 Progress/error/result compatibility is backed by durable rows/artifact
      outputs; cancellation is durable and restart-safe.
- [ ] AC5 Restart integration through fresh app/engine proves queued/running job
      reconciliation and subsequent poll/cancel/complete without duplicates.
- [ ] AC6 Legacy RAM dictionaries/threads are removed from runtime authority;
      no dual-write and no long operation executes inside HTTP request.
- [ ] AC7 Full S02 acceptance covers double-submit, forced close, stale worker,
      cancel during retry, no false-ready artifact and 7/7 PASS.

## Required validation

```powershell
python -m pytest -q tests/test_durable_job_api.py
python -m pytest -q tests/test_api.py tests/test_clip_cancel_persist.py tests/test_durable_job_persistence.py tests/test_durable_worker.py tests/test_job_reconciliation.py tests/test_durable_job_api.py
python -m ruff check app tests
python -m mypy app
git diff --check
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
```
