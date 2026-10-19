# S03-T02 - Execution Log

Append-only.

## Baseline (2026-08-04, before any code change)

### Required reading (all read in full)
1. docs/pm/SESSION_PROTOCOL.md
2. docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md (project/channel/video
   aggregates, migration policy, acceptance invariants)
3. docs/architecture/CHANNEL_API.md (S03-T01 durable channel contract —
   CAS pattern, null semantics, workspace ownership)
4. docs/PRODUCT_REQUIREMENTS_V2.md §4.3 (Project fields/status)
5. app/persistence/models.py (Project/Channel/mixins + all entities)
6. app/persistence/channels.py (ChannelRepository/Service — the exact
   pattern to mirror: atomic CAS, fresh re-read, name backstop)
7. app/api/app.py, app/api/deps.py, app/api/routes/projects.py (legacy
   router — literal sub-routes `/channels`, `/gpu-info`, `/presets/...`
   and parameterized `/api/projects/{project_id}` with 12-hex ids)
8. S03-T01 task/report/review (APPROVED) + migration head
   `1c9f2a4b7d8e`; START_PROMPT.md
9. app/schemas/__init__.py (ChannelData DTO pattern), app/persistence/
   __init__.py, app/persistence/engine.py
10. tests/conftest.py, tests/test_channel_crud.py (full AC1-AC6 + PM
    race tests), tests/test_persistence_bootstrap.py (S02→S03 upgrade
    evidence), tests/test_api.py / test_list_projects.py /
    test_delete_and_autosegment.py / test_trailing_slash.py /
    test_list_objects.py / test_preset_manager.py (legacy base-route
    consumers that must keep working)

### Key facts verified from source (not assumed)
- Starlette `uuid` path convertor regex:
  `[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}`
  → literal `channels` does NOT match; legacy 12-hex dir ids do NOT
  match; 32-hex and dashed UUID4 DO match.
- Legacy `ProjectWorkflowService.create_project` ids are `uuid.uuid4().hex[:12]`
  (12 hex chars) → never captured by the durable `:uuid` routes; legacy
  base create/list replaced by route order as the contract requires.
- Legacy projects router (registered today before jobs/frames/channels)
  has NO `/api/projects/statuses` route; the durable router adds it.
- S03-T01 head `1c9f2a4b7d8e`; `project` table already carries CHECK
  constraints (name 1-200, status exact set, revision>0) and nullable
  channel FKs with RESTRICT — the schema CAN enforce the project
  contract without a migration.
- `app/api/app.py` currently imports `from app.api.routes import
  channels, frames, jobs, projects` and includes projects FIRST.
- conftest `_patch_project_root` already resets `deps._channel_service`;
  it will need a matching `_project_service` reset for the lazy durable
  ProjectService singleton.

### Protected user changes (pre-existing)
- `channels.json` modified in the working tree (M, +224 insertions vs
  HEAD, SHA256 dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555).
  PRESERVE byte-for-byte (same hash as the S03-T01 final evidence).
- `docs/architecture/UI_UX_DESIGN_STANDARD.md` untracked (user file) —
  leave untouched.
- No other modified/untracked files.

### Baseline commands + results
- `git status --short` → `M channels.json` only
- `git log --oneline -3` → 6d5ebbf (S03 durable project management
  start), a688d86 (S03-T01), f3c6b70 (S03 start)
- Alembic chain: a1b2c3d4e5f6 → 23b308b1fd0b → 1c9f2a4b7d8e (head)
- channels.json SHA256 (baseline):
  dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555
- `python -m pytest -q tests/test_channel_crud.py` → (baseline, S03-T01
  head): 28 passed (recorded in S03-T01 LOG; rerun below in validation)

### Plan (≤7 steps)
1. Add durable Project DTOs (ProjectStatus/ProjectData/ProjectCreate/
   ProjectUpdate/ProjectArchiveRequest/ProjectListResponse) to
   app/schemas/__init__.py (mirror Channel DTOs; no ORM/absolute paths).
2. Create app/persistence/projects.py: ProjectRepository (transaction-
   bounded; create/list/get/update/archive; atomic revision CAS; no hard
   delete; channel-aware validation: same workspace, correct role, active
   when newly assigned; existing references survive channel archive) +
   ProjectService (one session per operation; workspace bootstrap
   idempotent). Export from app/persistence/__init__.py.
3. Wire deps.get_project_service() (lazy singleton over the durable DB —
   mirror get_channel_service).
4. Create app/api/routes/durable_projects.py: `/api/projects` base
   list/create + `/{project_id:uuid}` get/patch/archive + `/statuses`
   discovery; no DELETE; register in app/api/app.py BEFORE the legacy
   projects router (literal legacy sub-routes remain reachable).
5. Tests: NEW tests/test_project_crud.py (AC1-AC7: lifecycle, CAS races,
   channel-role/workspace/active validation, archive preservation,
   workspace isolation, DTO boundary, route-order literal-path
   compatibility, no project.json/JSON dual-write); extend
   tests/test_persistence_bootstrap.py with S03-T01-head preservation
   (rows + references survive; no new tables → no migration).
6. Write docs/architecture/PROJECT_API.md.
7. Run full validation (targeted pytest, ruff, mypy, git diff --check,
   quality-baseline.ps1), record evidence, fill REPORT.md as SUBMITTED.
   No commit, no roadmap/PRD edits.

## ARCHITECTURE CORRECTION 1 (PM) — 2026-08-04

### PM directive
The original `/api/projects` shadowing contract was unsafe: durable base
create produces no project directory while current object/scene endpoints
still require the legacy filesystem aggregate.  Moved the durable API to
`/api/v2/projects` (statuses + UUID item routes).  All existing
`/api/projects` routes remain untouched.  Reverted ALL S03-T02 changes to
legacy test files; removed temp repro files; retained the durable
repository/DTO/CAS/channel-validation work.

### Changes applied
1. `app/api/routes/durable_projects.py` — router prefix changed to
   `/api/v2/projects`; module docstring rewritten for the v2 namespace
   isolation contract (AC7).  Endpoints unchanged otherwise.
2. `app/api/app.py` — durable router now included AFTER the legacy
   routers (no shadowing possible; v2 prefix is disjoint from
   `/api/projects`).
3. Reverted legacy test files to HEAD (byte-identical):
   tests/test_api.py, tests/test_clip_cancel_persist.py,
   tests/test_delete_and_autosegment.py, tests/test_list_projects.py,
   tests/test_list_objects.py, tests/test_preset_manager.py,
   tests/test_trailing_slash.py — `git checkout HEAD -- <files>`.
4. Removed scratch files: scripts/_tmp_repro.py, scripts/_tmp_trace.txt.
5. `tests/test_project_crud.py` — all durable calls now use
   `/api/v2/projects`; AC7 section rewritten as three isolation tests:
   - test_v2_never_shadows_legacy_literal_routes
   - test_v2_base_and_legacy_base_are_isolated
   - test_v2_item_route_never_matches_legacy_paths
   (non-UUID on v2 :uuid route → 404 in FastAPI 0.139, not 422).
6. `docs/architecture/PROJECT_API.md` — written for the v2 contract.
7. Lint/typing fixes: removed unused CHANNEL_ROLES import and duplicate
   DEFAULT_WORKSPACE_ID export (F401/F811); removed unused before_dirs
   (F841); mypy no-any-return in ProjectService.update resolved with a
   cast; ruff --fix sorted app/persistence/__init__.py imports (I001).

### Validation (correction round)
- pytest tests/test_project_crud.py → 26 passed
- pytest tests/test_channel_crud.py tests/test_project_crud.py
  tests/test_persistence_bootstrap.py → 86 passed
- Legacy regression (unchanged files): test_api.py, test_list_projects.py,
  test_delete_and_autosegment.py, test_trailing_slash.py,
  test_list_objects.py, test_preset_manager.py, test_clip_cancel_persist.py,
  test_channel_crud.py, test_durable_job_api.py,
  test_durable_job_persistence.py → 170 passed, 6 skipped
- ruff check app tests → All checks passed!
- mypy app → Success: no issues found in 57 source files
- git diff --check → exit 0 (CRLF warnings only)
- channels.json SHA256 unchanged:
  dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555
- Full quality baseline: recorded below.

## FULL VALIDATION (S03-T02) — 2026-08-04
### Full quality baseline (7 gates) — run 20260804-031608
```
Gate 1 - Environment/Preflight   PASS  exit=0    0s
Gate 2 - Python tests            PASS  exit=0    269.51s
Gate 3 - Python lint             PASS  exit=0    0.06s
Gate 4 - Python typing           PASS  exit=0    0.55s
Gate 5 - Frontend typecheck      PASS  exit=0    1.59s
Gate 6 - Frontend lint           PASS  exit=0    3.3s
Gate 7 - Frontend build          PASS  exit=0    5.42s
OVERALL: PASS (exit code 0)
summary: output/quality-baseline/20260804-031608/summary.json
```

### FINAL GATE (S03-T02, correction round)
- pytest tests/test_project_crud.py → 26 passed
- pytest tests/test_channel_crud.py tests/test_project_crud.py
  tests/test_persistence_bootstrap.py → 86 passed
- Legacy regression (unchanged files) → 78 passed, 6 skipped
  (test_api/test_list_projects/test_delete_and_autosegment/
  test_trailing_slash/test_list_objects/test_preset_manager/
  test_clip_cancel_persist) + 92 passed (channel_crud/durable_job_*)
  = 170 passed, 6 skipped overall legacy sweep
- ruff check app tests → All checks passed!
- mypy app → Success: no issues found in 57 source files
- git diff --check → exit 0 (CRLF warnings only)
- git diff app/api/routes/projects.py → empty (legacy router untouched)
- channels.json SHA256:
  dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555
  (unchanged; git diff --numstat channels.json = 224 insertions, identical
  to the pre-existing user modification)
- No stray files: scripts/_tmp_repro.py and scripts/_tmp_trace.txt removed.
- No commit, no roadmap/PRD edits.

## PM correction round 2 and approval (2026-08-04)

- Independent review found non-atomic Channel validation/assignment, archive
  lifecycle bypass through PATCH, and a non-deterministic archive race test.
- Correction packet: `CORRECTION_02.md`.
- Hermes MAX resume/recovery requests repeatedly timed out at the local proxy
  before emitting edits; PM applied a narrowly scoped, disclosed hotfix.
- Added SQLite `BEGIN IMMEDIATE` writer reservation before Project CREATE,
  PATCH, and archive write transactions.
- Generic PATCH now rejects entry into archived and archived rows are immutable.
- Added deterministic CREATE/PATCH-vs-Channel-archive coverage and a true
  post-read archive CAS interleaving test.
- Independent evidence: Project 29 passed; combined durable 89 passed; legacy
  API/import regression 46 passed; Ruff and mypy pass.
- Mandatory baseline `20260804-041036`: all 7 gates PASS, exit 0.
- PM decision: APPROVED.
