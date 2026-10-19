# S01-T02 - Implementation Report

**Status:** SUBMITTED
**Started:** 2026-08-03 16:20 +07:00
**Submitted:** 2026-08-03 16:44 +07:00
**Resubmitted (after PM CHANGES_REQUESTED):** 2026-08-03 16:55 +07:00

## Outcome delivered

Portable SQLite/SQLAlchemy persistence bootstrap with an explicit, testable
Alembic schema revision:

- `app/persistence/engine.py` — explicit-path engine + session factory; SQLite
  connections enable `PRAGMA foreign_keys=ON` and a bounded 5s busy timeout.
  Creating an engine never creates a database file (no side effects on import).
- `app/persistence/models.py` — the 8 approved S01 entities (Workspace,
  Channel, Project, VideoItem, Scene, Artifact, ArtifactOwner, LegacyImport)
  with FK/CHECK constraints, indexes, UTC timestamps, optimistic `revision`,
  NOCASE unique channel names. No Job/JobStep tables (deferred to S02-T01).
- `app/persistence/revision.py` — schema-revision guard: a database at a newer
  unknown Alembic revision is refused with an actionable error naming the
  revision id and database path.
- `alembic.ini` + `migrations/` — explicit bootstrap; migration refuses to run
  without an explicit database target (`-x db_url=...`, `MOTIONFORGE_DATABASE_URL`,
  or a configured URL). Initial revision `a1b2c3d4e5f6` implements the contract.
  `migrations/env.py` reuses the shared engine factory, so the Alembic online
  connection enables `PRAGMA foreign_keys=ON` like application connections.
- `tests/test_persistence_bootstrap.py` — 18 tests using only temporary
  databases.

No production route was cut over; no legacy data imported; no artifact
management implemented; no Job persistence added.

## PM review corrections (CHANGES_REQUESTED round)

| # | Correction | Resolution |
|---|---|---|
| 1 | `channel.avatar_artifact_id` and `video_item.source_artifact_id` must be nullable FKs to `artifact` with ON DELETE RESTRICT | Added `ForeignKey("artifact.id", ondelete="RESTRICT")` to both ORM columns and `fk_channel_avatar_artifact` / `fk_video_item_source_artifact` constraints in the initial revision (in-place, not shipped). `alembic check` reports zero drift |
| 2 | `migrations/env.py` raw engine lacks FK pragma | `run_migrations_online` now uses `create_engine_for_path`; verified PRAGMA foreign_keys = 1 on the migration-style connection |
| 3 | Focused tests for artifact references and Alembic online FK | Added `test_channel_avatar_artifact_id_rejects_nonexistent_artifact`, `test_video_item_source_artifact_id_rejects_nonexistent_artifact`, `test_alembic_online_connection_has_foreign_keys_enabled` |
| 4 | Re-run all validation | All re-run green (see Tests and validation) |

## Acceptance criteria evidence

| AC | Status | Evidence |
|---|---|---|
| AC1 Portable engine/session factory, explicit path, no DB on import | PASS | `test_engine_creation_does_not_create_database_file`, `test_engine_accepts_explicit_path`, `test_session_factory_is_bound_to_engine` |
| AC2 SQLite FK + bounded busy timeout | PASS | `test_foreign_keys_enabled_on_connection` (PRAGMA foreign_keys = 1), `test_busy_timeout_is_bounded` (5000ms), `test_alembic_online_connection_has_foreign_keys_enabled` |
| AC3 Initial migration = approved S01 contract, no Job tables / API cutover | PASS | `test_initial_schema_has_expected_tables`, `test_no_job_tables`, `test_no_api_cutover_tables`; FK list shows both artifact references with RESTRICT |
| AC4 Alembic empty→head twice on independent temp DBs | PASS | `test_upgrade_from_empty_to_head`, `test_upgrade_twice_on_independent_databases` + direct CLI `alembic upgrade head` on temp DB |
| AC5 Reopen preserves data; invalid FK fails; newer revision refused with actionable error | PASS | `test_reopen_preserves_data`, `test_invalid_foreign_key_fails`, `test_channel_avatar_artifact_id_rejects_nonexistent_artifact`, `test_video_item_source_artifact_id_rejects_nonexistent_artifact`, `test_newer_revision_refused`, `test_newer_revision_check_raises_actionable_error`, `test_current_revision_is_supported` |
| AC6 Targeted tests and all seven quality gates PASS | PASS | 18/18 targeted; full suite 178 passed, 8 skipped, 7 deselected; quality baseline OVERALL: PASS (all 7 gates, exit 0) |

## Files changed

- `pyproject.toml` — added runtime dependency `alembic==1.18.5`.
- `app/persistence/__init__.py` (new)
- `app/persistence/engine.py` (new)
- `app/persistence/models.py` (new; artifact FK corrections)
- `app/persistence/revision.py` (new)
- `alembic.ini` (new)
- `migrations/env.py` (new; shared engine factory correction)
- `migrations/script.py.mako` (new)
- `migrations/versions/a1b2c3d4e5f6_initial_s01_persistence_schema.py` (new; artifact FK corrections)
- `tests/test_persistence_bootstrap.py` (new; 18 tests)
- `docs/pm/sessions/S01-T02-sqlite-bootstrap/LOG.md` (appended)

## Architecture/schema/API impact

- New package `app.persistence` is additive; no existing route/service imports
  it. Schema creation/upgrade is explicit only (`alembic upgrade head`), never
  a module-import or request side effect.
- `alembic check` reports zero drift between the migration and the ORM models.
- No public API contract changed.

## Tests and validation

| Command | Result | Notes |
|---|---|---|
| `python -m pytest -q tests/test_persistence_bootstrap.py` | PASS | 18 passed |
| `MOTIONFORGE_DATABASE_URL=<temp> python -m alembic upgrade head` | PASS | temp DB upgraded to head; downgrade base + re-upgrade OK |
| `MOTIONFORGE_DATABASE_URL=<temp> python -m alembic check` | PASS | "No new upgrade operations detected" |
| PRAGMA foreign_key_list on temp DB | PASS | channel: avatar_artifact_id→artifact RESTRICT, workspace_id→workspace RESTRICT; video_item: source_artifact_id→artifact RESTRICT, source_channel_id→channel RESTRICT, project_id→project RESTRICT |
| `python -m ruff check app tests` | PASS | All checks passed |
| `python -m mypy app` | PASS | Success: no issues in 45 source files |
| `python -m pytest -q -m "not gpu and not sam2 and not integration"` | PASS | 178 passed, 8 skipped, 7 deselected |
| `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1` | PASS | OVERALL: PASS, all 7 gates, exit 0 |
| `git diff --check` | PASS | exit 0 (only documented CRLF warnings on Windows) |

All database paths used for validation were under the OS temp directory
(`C:/Users/Admin/AppData/Local/Temp/mf_s01t02/`), removed after validation.
No database was created or upgraded under production project/user data.

## Migration and rollback

- Initial revision `a1b2c3d4e5f6` (empty→head) implements the full S01
  contract; `downgrade base` drops all 8 tables (verified).
- Migration policy from the contract is honored: DB revision is authoritative;
  newer unknown revisions are refused at startup with an actionable error.
- Because the initial revision has not shipped, the two artifact FK
  constraints were added to it in place; ORM/migration drift remains zero.

## Known limitations/risks

- Alembic 1.18.5 CLI `revision --autogenerate` produced empty `pass` bodies
  despite correctly detecting all schema ops programmatically; the initial
  revision was therefore hand-authored (equivalent operations, verified by
  `alembic check` zero drift). Future revisions should hand-write or use
  programmatic autogenerate until the CLI quirk is confirmed fixed.
- Contract item "unique case-insensitively among active channels" is
  represented with `COLLATE NOCASE` on `channel.name`; the "among active"
  filter is a repository-layer rule to be enforced by later service tasks.

## Recommended PM decision

`PENDING` — awaiting PM review of the resubmission.
