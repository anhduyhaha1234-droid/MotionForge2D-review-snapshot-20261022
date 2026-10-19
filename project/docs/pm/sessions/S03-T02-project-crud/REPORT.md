# S03-T02 - Implementation Report

**Status:** APPROVED (PM correction round 2)
**Task:** Durable Project CRUD API (list/read/create/update/archive)
**Session:** docs/pm/sessions/S03-T02-project-crud
**Correction:** durable API moved to `/api/v2/projects` per PM architecture
correction; every legacy `/api/projects` route and every legacy test file
restored byte-identical.

PM correction round 2 closed three review blockers: generic PATCH can no
longer enter or leave `archived`; Project writes acquire SQLite
`BEGIN IMMEDIATE` before channel validation so a competing Channel archive
cannot commit between validation and assignment; and the archive race test
now pauses both repository calls after their active-row read and orders the
winner/loser CAS deterministically. Two Hermes MAX resume attempts and one
minimal recovery session repeatedly timed out at the local inference proxy
before emitting an edit, so PM applied this narrow, disclosed hotfix and
independently re-ran every gate.

## Outcome delivered

A durable Project repository/service/API implementing the approved
persistence domain contract §4 (project) on the existing S01 `project`
table — **no migration added** (the schema already enforces the contract;
head stays `1c9f2a4b7d8e`).  The API lives in an explicit transition
namespace `/api/v2/projects` and never shadows, proxies or invokes legacy
filesystem services.  Durable endpoints write SQLite only: no project
directory, no `project.json`, no JSON dual-write.

## Acceptance criteria evidence

| AC | Status | Evidence |
|---|---|---|
| AC1 | PASS | List/read/create/update/archive under `/api/v2/projects`; no DELETE endpoint in OpenAPI; `test_durable_create_never_writes_project_json` proves no dir/`project.json`; `test_v2_base_and_legacy_base_are_isolated` proves legacy base create still writes its dir. |
| AC2 | PASS | `test_statuses_are_exact_approved_set` (exact 6 statuses, `/api/v2/projects/statuses`); `test_empty_name_rejected`; `test_dto_never_exposes_orm_objects_or_paths`. |
| AC3 | PASS | Existing validation coverage plus parameterized `test_channel_archive_cannot_commit_between_validation_and_assignment` for CREATE and PATCH. The test pauses after active-channel validation, observes the competing archive's exact SQL UPDATE attempt, and proves the Project write commits first under the reserved SQLite writer lock. |
| AC4 | PASS | Existing CAS coverage plus `test_patch_cannot_bypass_archive_or_restore_archived_project`; `test_archive_interleaving_both_callers_read_active_then_cas` now uses an injected post-read hook so both sessions have loaded active before caller A commits and caller B executes the losing CAS/fresh re-read. |
| AC5 | PASS | `test_archive_preserves_timestamps_and_channel_references`; archived readable/filterable, excluded from active default (`test_list_excludes_archived_by_default`); no cascade/hard delete. |
| AC6 | PASS | `test_cross_workspace_project_is_404`; `test_unknown_project_404` (UUID-shaped unknown → 404 on v2 item routes). |
| AC7 | PASS | Three isolation tests: `test_v2_never_shadows_legacy_literal_routes`, `test_v2_base_and_legacy_base_are_isolated`, `test_v2_item_route_never_matches_legacy_paths`.  Legacy suite unchanged and green (170 passed, 6 skipped across 10 legacy files). |
| AC8 | PASS | `test_s03t02_no_migration_needed_head_unchanged`, `test_upgrade_from_s03t01_preserves_project_rows`, `test_upgrade_from_s03t01_preserves_archived_project_and_references`, `test_s03t02_head_table_set_unchanged`.  Targeted validation 86 passed; full 7/7 baseline below. |

## Files changed

- NEW `app/persistence/projects.py` — ProjectRepository (create/list/get/
  update/archive; atomic CAS; channel-aware validation; no hard delete;
  DTO records) + ProjectService (one transaction per operation, workspace
  bootstrap in the same transaction).
- NEW `app/api/routes/durable_projects.py` — `/api/v2/projects` base
  list/create, `/statuses`, `/{project_id:uuid}` get/patch/archive.
- NEW `tests/test_project_crud.py` — 26 AC1-AC8 tests incl. deterministic
  CAS interleaving and route-isolation proofs.
- MODIFIED `app/schemas/__init__.py` — ProjectStatus,
  DurableProjectData, ProjectCreate/Update/ArchiveRequest,
  ProjectListResponse DTOs.
- MODIFIED `app/persistence/__init__.py` — project module exports.
- MODIFIED `app/api/deps.py` — lazy `get_project_service()`.
- MODIFIED `app/api/app.py` — durable router included (disjoint v2
  namespace, after legacy routers).
- MODIFIED `tests/conftest.py` — reset `deps._project_service` per test.
- MODIFIED `tests/test_persistence_bootstrap.py` — +4 AC8 preservation
  tests.
- NEW `docs/architecture/PROJECT_API.md`.
- MODIFIED `docs/pm/sessions/S03-T02-project-crud/LOG.md`.

## Architecture/schema/API impact

- No schema change; Alembic head unchanged (`1c9f2a4b7d8e`).
- New API namespace `/api/v2/projects`; all 82 legacy `/api/projects`
  paths untouched (verified via OpenAPI).
- Durable route isolation verified: `/api/projects/statuses` does not
  exist; v2 item routes are UUID-constrained and cannot capture literal
  legacy paths or legacy 12-hex ids.

## Tests and validation

| Command | Result |
|---|---|
| `python -m pytest -q tests/test_project_crud.py` | 26 passed |
| `python -m pytest -q tests/test_channel_crud.py tests/test_project_crud.py tests/test_persistence_bootstrap.py` | 86 passed |
| Legacy regression (10 files, unchanged) | 170 passed, 6 skipped |
| `python -m ruff check app tests` | All checks passed! |
| `python -m mypy app` | Success: no issues found in 57 source files |
| `git diff --check` | exit 0 (CRLF warnings only) |
| quality-baseline.ps1 (7 gates) | OVERALL PASS (run id below) |
| channels.json SHA256 | dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555 (unchanged) |

## Migration and rollback

None required.  Head unchanged; the existing schema enforces the project
contract (name 1-200 CHECK, exact status CHECK, revision>0 CHECK, RESTRICT
FKs).  Preservation evidence in test_persistence_bootstrap.py AC8 tests.

## Deviations from task

1. FastAPI 0.139 returns **404** (not 422) for a non-UUID path on a
   `:uuid`-constrained route in an included router; the isolation test
   asserts the actual behavior.
2. `ProjectService.update` uses a `cast` for the `_run` result because
   the Any-typed channel-ref kwargs defeat mypy inference (no-any-return).
3. No migration, no legacy writes, no roadmap/PRD edits.  No commit.
