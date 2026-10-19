# S01-T02 - SQLite engine, session and schema migrations

**Status:** APPROVED  
**Epic:** E01 - Durable Domain, Persistence and Jobs  
**Sprint:** S01 - Persistence foundation  
**Gate:** G1 - Foundation green  
**Depends on:** S01-T01 (APPROVED)

## User outcome

MotionForge has a portable SQLite/SQLAlchemy persistence bootstrap with an explicit, testable Alembic schema revision; no production route is cut over yet.

## Why now

The approved domain contract is the prerequisite for creating storage infrastructure. Artifact management and legacy import depend on a stable engine/session/migration layer.

## Required reading

1. `docs/pm/SESSION_PROTOCOL.md`
2. `docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md`
3. `docs/quality/QUALITY_BASELINE.md`
4. `pyproject.toml`
5. `app/config.py`
6. `tests/conftest.py`

## Allowed write scope

- `pyproject.toml`
- `app/persistence/`
- `alembic.ini`
- `migrations/`
- `tests/test_persistence_bootstrap.py`
- `docs/pm/sessions/S01-T02-sqlite-bootstrap/LOG.md`
- `docs/pm/sessions/S01-T02-sqlite-bootstrap/REPORT.md`

## Forbidden scope

- Existing API routes, workflow/services, frontend and legacy JSON/assets.
- PRD, Master Plan, roadmap, contract and task file.
- Runtime cutover, legacy import, artifact writes and Job persistence.

## Target behavior

- SQLAlchemy 2.x and Alembic are declared runtime dependencies.
- A dedicated persistence package creates engines/session factories from explicit database paths.
- Every SQLite connection enables foreign keys and a bounded busy timeout.
- Initial Alembic revision implements only the approved S01 entities and constraints.
- Schema creation/upgrade is explicit, never a module-import or request side effect.
- Tests use temporary databases and cover fresh upgrade, reopen, FK enforcement and unsupported-newer revision behavior.

## Acceptance criteria

- [ ] AC1 Portable engine/session factory uses an explicit path and creates no database on import.
- [ ] AC2 SQLite connections enable foreign keys and configured busy timeout.
- [ ] AC3 Initial migration represents the approved S01 contract without Job tables or API cutover.
- [ ] AC4 Alembic upgrade from empty to head passes twice on independent temp databases.
- [ ] AC5 Reopening preserves data; invalid FK fails; application refuses a newer unknown revision with actionable error.
- [ ] AC6 Targeted tests and all seven quality gates PASS.

## Required validation

```powershell
python -m pytest -q tests/test_persistence_bootstrap.py
python -m alembic upgrade head
python -m ruff check app tests
python -m mypy app
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
git diff --check
```

For the direct Alembic command, set its database URL/path to a temporary location. Never create or upgrade a database under production project/user data.

## Stop conditions

- The approved contract cannot be represented without changing it.
- A migration could touch existing JSON/assets or a non-temporary database.
- Dependency resolution changes unrelated packages or requires a lockfile policy decision.
- Required write scope must expand.
