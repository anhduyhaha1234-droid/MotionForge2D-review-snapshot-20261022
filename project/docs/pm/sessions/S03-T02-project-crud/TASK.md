# S03-T02 - Durable Project CRUD API

**Status:** APPROVED
**Epic:** E02 - Production Management and Product Shell
**Sprint:** S03 - Production management API
**Gate:** G2 - Production shell
**Depends on:** S03-T01 (APPROVED)

## User outcome

Users can create, list, read, update and archive durable Projects, assigning an
optional source Channel and production Channel with actionable validation and
without filesystem/JSON dual-write.

## Required reading

1. `docs/pm/SESSION_PROTOCOL.md`
2. `docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md`
3. `docs/architecture/CHANNEL_API.md`
4. `docs/PRODUCT_REQUIREMENTS_V2.md` project and channel requirements
5. `app/persistence/models.py`
6. `app/persistence/channels.py`
7. `app/api/app.py`, `app/api/deps.py`, and current project routes
8. S03-T01 task/report/review and migration head
9. Current project schemas/services/tests and persistence bootstrap tests

## Durable route contract

- Durable routes use the explicit transition namespace `/api/v2/projects`
  with UUID-constrained item paths (`/{project_id:uuid}`).
- All existing `/api/projects` base, literal and nested legacy routes remain
  unchanged and continue serving the current filesystem workflows until a
  later vertical-slice migration/cutover task can move their downstream data.
- Durable endpoints write SQLite only and never create `project.json` or a
  project directory. They must not shadow, proxy, or invoke legacy services.
- Workspace ownership is explicit on every operation; the local default remains
  `default`.

## Allowed write scope

- `app/persistence/projects.py`
- `app/persistence/models.py`
- `app/persistence/__init__.py`
- `app/api/routes/durable_projects.py`
- `app/api/app.py`
- `app/api/deps.py`
- `app/schemas/__init__.py`
- `migrations/versions/`
- `tests/conftest.py`
- `tests/test_project_crud.py`
- `tests/test_persistence_bootstrap.py`
- narrowly required route-isolation compatibility tests
- `docs/architecture/PROJECT_API.md`
- `docs/pm/sessions/S03-T02-project-crud/`

## Forbidden scope

- VideoItem CRUD, frontend, job/worker behavior, legacy JSON/filesystem writes,
  migration of legacy projects, deletion/purge, dependency changes, user data,
  roadmap/PRD/MP/prior session evidence.
- Do not edit the implementation of `app/api/routes/projects.py`; prove legacy
  literal-route compatibility through registration and tests.

## Acceptance criteria

- [ ] AC1 Durable list/read/create/update/archive API; no hard-delete endpoint,
      project directory creation, `project.json`, or JSON dual-write.
- [ ] AC2 Project fields follow the approved domain contract; names normalize
      to non-empty 1-200 characters, statuses are exact, and DTOs expose no ORM
      object or absolute path.
- [ ] AC3 Source and production Channel references are nullable/clearable and
      validated atomically: same workspace, correct role, and active when newly
      assigned. Existing references survive later Channel archive.
- [ ] AC4 PATCH and first archive use atomic revision CAS; stale updates return
      stable 409, every accepted business update bumps exactly once, and
      concurrent archive repeats are idempotent.
- [ ] AC5 Archive preserves timestamps, channel references and future child
      relationships; archived Projects remain readable/filterable and are
      excluded from the active default. No cascade/hard delete.
- [ ] AC6 Every item operation enforces workspace ownership. Unknown or
      cross-workspace IDs return 404 without data leakage or mutation.
- [ ] AC7 `/api/v2/projects` is isolated from every existing `/api/projects`
      route; durable endpoints do not invoke legacy filesystem services and
      the existing legacy API test suite remains unchanged and green.
- [ ] AC8 Upgrade from the S03-T01 head preserves all Project/Channel rows and
      references; add a migration only when the existing schema cannot enforce
      the contract. Targeted validation and full quality baseline are 7/7.

## Required validation

```powershell
python -m pytest -q tests/test_project_crud.py
python -m pytest -q tests/test_channel_crud.py tests/test_project_crud.py tests/test_persistence_bootstrap.py
python -m ruff check app tests
python -m mypy app
git diff --check
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
```
