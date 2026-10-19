# S03-T01 - Durable Channel CRUD API

**Status:** APPROVED
**Epic:** E02 - Production Management and Product Shell
**Sprint:** S03 - Production management API
**Gate:** G2 - Production shell
**Depends on:** E01/S02 exit (APPROVED)

## User outcome

Users can create, list, read, update and archive source/production Channels
through one durable API with actionable validation and no JSON dual-write.

## Required reading

1. `docs/pm/SESSION_PROTOCOL.md`
2. `docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md`
3. `docs/architecture/DURABLE_JOB_API_CUTOVER.md`
4. Channel requirements in `docs/PRODUCT_REQUIREMENTS_V2.md`
5. `app/persistence/models.py`
6. `app/persistence/database.py`
7. `app/api/deps.py`
8. Current channel schemas/services/routes and tests
9. Latest Alembic head and persistence tests

## Allowed write scope

- `app/persistence/channels.py`
- `app/persistence/models.py`
- `app/persistence/__init__.py`
- `app/api/routes/channels.py`
- `app/api/app.py`
- `app/api/deps.py`
- `app/schemas/__init__.py`
- `migrations/versions/`
- `tests/test_channel_crud.py`
- `tests/test_persistence_bootstrap.py`
- `docs/architecture/CHANNEL_API.md`
- `docs/pm/sessions/S03-T01-channel-crud/`

## Forbidden scope

- Project/VideoItem CRUD, frontend, jobs/worker behavior and legacy JSON writes.
- Dependency changes, destructive data migration and user data.
- Roadmap/PRD/MP/prior evidence.

## Acceptance criteria

- [ ] AC1 List/read/create/update/archive API for explicit workspace; no hard
      delete endpoint and no JSON dual-write.
- [ ] AC2 Roles are exactly source/production and cross-field validation follows
      the approved domain contract.
- [ ] AC3 Active names are normalized and case-insensitively unique per
      `(workspace, role)`; conflict responses are stable/actionable.
- [ ] AC4 PATCH uses revision/optimistic concurrency; stale updates return 409
      and every accepted business update increments revision once.
- [ ] AC5 Archive is idempotent, preserves references and timestamps; archived
      channels are filterable/readable and excluded by active default.
- [ ] AC6 API DTOs never expose ORM objects/absolute paths and preserve existing
      legacy channel response compatibility where applicable.
- [ ] AC7 Migration from S02 head preserves all rows; targeted tests and 7/7 PASS.

## Required validation

```powershell
python -m pytest -q tests/test_channel_crud.py
python -m pytest -q tests/test_persistence_bootstrap.py tests/test_channel_crud.py
python -m ruff check app tests
python -m mypy app
git diff --check
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
```
