# S03-T01 - Execution Log

Append-only.

## Baseline (2026-08-04, before any code change)

### Required reading (all read in full)
1. docs/pm/SESSION_PROTOCOL.md
2. docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md
3. docs/architecture/DURABLE_JOB_API_CUTOVER.md
4. docs/PRODUCT_REQUIREMENTS_V2.md §4.1/4.2 (Channel requirements)
5. app/persistence/models.py (Channel + mixins + all entities)
6. app/persistence/engine.py (database.py does not exist; engine/session
   bootstrap lives here — confirmed)
7. app/api/deps.py
8. Current channel schemas/services/routes and tests:
   - app/schemas/__init__.py (ChannelWorkspace, JobInfo, JobState)
   - app/workflow/channel_service.py (legacy JSON ChannelService)
   - app/api/routes/projects.py (legacy channel endpoints, lines 1764-1825)
   - tests/test_channel_workspace.py (legacy service tests, 10 pass)
9. Latest Alembic head + persistence tests:
   - migrations/versions/a1b2c3d4e5f6 (S01 initial), 23b308b1fd0b (S02 jobs)
   - tests/test_persistence_bootstrap.py (19 pass)
   - app/persistence/revision.py, app/lifecycle.py, app/workflow/job_service.py
   - tests/conftest.py (isolated root + durable DB fixtures)

### Protected user changes (pre-existing)
- `channels.json` is modified in the working tree (M, +224 lines vs HEAD):
  it is a user/test data file — PRESERVE byte-for-byte. Evidence: diff adds
  only appended legacy channel entries (Test Channel/Channel A/B/Find Me).
- `docs/architecture/UI_UX_DESIGN_STANDARD.md` is untracked (user file,
  Aug 4 00:31) — leave untouched.
- No other modified/untracked files.

### Baseline commands + results
- `git status --short` → `M channels.json`
- `git log --oneline -5` → f3c6b70 (S03 start), dcd9022, 068b46f, ...
- `python -m pytest -q tests/test_channel_workspace.py` → 10 passed
- `python -m pytest -q tests/test_persistence_bootstrap.py` → 19 passed
- channels.json SHA256 (baseline): dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555

### Plan (≤7 steps)
1. Add Channel DTOs (ChannelData/ChannelCreate/ChannelUpdate/ChannelList
   response) to app/schemas/__init__.py.
2. Create app/persistence/channels.py: ChannelRepository (transaction-
   bounded, optimistic revision, case-insensitive unique active names,
   archive = status/archived_at, no hard delete) + ChannelService facade.
3. Wire deps.get_channel_service() (lazy singleton over the durable
   database path) and register routes in app/api/app.py.
4. Create app/api/routes/channels.py: explicit-workspace CRUD + archive
   endpoints; no hard delete; DTO responses only; legacy channels.json
   endpoints untouched.
5. Extend tests/test_persistence_bootstrap.py with S02→S03 upgrade
   preservation tests (AC7) and create tests/test_channel_crud.py (AC1-AC6).
6. Write docs/architecture/CHANNEL_API.md.
7. Run full validation (pytest targeted + bootstrap, ruff, mypy, git diff
   --check, quality-baseline.ps1), record evidence, fill REPORT.md as
   SUBMITTED. No commit, no roadmap edits.

## Implementation (2026-08-04)

### Files changed (within allowed scope)
- NEW `app/persistence/channels.py` — ChannelRepository (create/list/get/
  update/archive; no hard delete; revision guard; case-insensitive
  active-name pre-check; IntegrityError backstop) + ChannelService
  (request-bounded one-session-per-operation facade; on-demand workspace).
- NEW `app/api/routes/channels.py` — `/api/channels` CRUD + archive +
  roles/statuses discovery; static routes declared before `/{channel_id}`.
- MODIFIED `app/persistence/__init__.py` — export channel module symbols.
- MODIFIED `app/api/deps.py` — lazy `get_channel_service()` bound to the
  durable database (job service's session factory or lifecycle DB path).
- MODIFIED `app/api/app.py` — register channels router.
- MODIFIED `app/schemas/__init__.py` — ChannelRole/ChannelStatus/
  ChannelData/ChannelCreate/ChannelUpdate/ChannelListResponse DTOs +
  `_dt_iso` UTC normalization.
- MODIFIED `app/api/routes/projects.py` — legacy-channel compatibility
  shims (see deviations): `get_project` returns the legacy channel JSON
  list for `project_id == "channels"`; legacy list handlers return `[]`
  when the legacy store is absent; no other legacy behavior changed.
- MODIFIED `tests/test_persistence_bootstrap.py` — +3 AC7 upgrade
  preservation tests (S02→head rows, referencing projects, no schema drift).
- NEW `tests/test_channel_crud.py` — 14 AC1-AC6 endpoint tests.
- NEW `docs/architecture/CHANNEL_API.md`.

### Deviations / decisions
1. **No migration added.** The S01 `channel` table already satisfies every
   AC constraint (verified: table DDL carries role/status CHECKs, NOCASE
   name, unique (workspace,role,name), revision, archived_at).
2. **S01 uniqueness is stronger than the contract**: `uq_channel_workspace_role_name`
   applies to ALL rows (active + archived) — SQLite NOCASE collation is not
   applied to index keys, so an archived channel's exact-case name stays
   reserved (409 on reuse).  Contract requires uniqueness only "among
   active channels"; the existing schema is a strict superset, so per the
   start prompt no migration was added.  Documented in CHANNEL_API.md §3
   and covered by `test_archived_name_cannot_be_reused`.
3. **Legacy route capture**: the legacy projects router registers
   `GET /{project_id}` before the literal `GET /channels`, so
   `GET /api/projects/channels` is served by `get_project` with
   `project_id="channels"`.  A shim preserves the legacy JSON-list
   contract (returns the channel workspace list for that literal id) —
   this is a bug-compatible preservation, not a behavior change.
4. The repository raises `ValueError` when the workspace row is missing
   (FK RESTRICT); the service creates the `default` workspace on demand.

## Validation (2026-08-04)

### Targeted tests (AC1-AC7)
```
python -m pytest -q tests/test_channel_crud.py
-> 14 passed, 1 warning in 4.92s
python -m pytest -q tests/test_persistence_bootstrap.py tests/test_channel_crud.py
-> 36 passed, 1 warning in 8.48s
python -m pytest -q tests/test_channel_workspace.py tests/test_channel_crud.py tests/test_persistence_bootstrap.py
-> 46 passed, 1 warning in 8.56s
```

### Lint / typing / diff
```
python -m ruff check app tests   -> All checks passed!
python -m mypy app               -> Success: no issues found in 55 source files
git diff --check                 -> exit 0 (CRLF warnings only)
```

### Full quality baseline (7 gates)
```
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
Gate 1 - Environment/Preflight  PASS  exit=0
Gate 2 - Python tests           PASS  exit=0  258.53s
Gate 3 - Python lint            PASS  exit=0
Gate 4 - Python typing          PASS  exit=0
Gate 5 - Frontend typecheck     PASS  exit=0
Gate 6 - Frontend lint          PASS  exit=0
Gate 7 - Frontend build         PASS  exit=0
OVERALL: PASS (exit code 0)
summary: output/quality-baseline/20260804-005408/summary.json
```

### channels.json preservation (SHA256 identical before/after)
```
baseline: dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555
after impl + full suite: dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555
after baseline rerun:     dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555
```
`git diff --stat channels.json` unchanged: `1 file changed, 224 insertions(+)`
(identical to the pre-existing user modification at baseline).

### User files untouched
- `channels.json` — hash identical, diff identical.
- `docs/architecture/UI_UX_DESIGN_STANDARD.md` — untracked, untouched.

## CORRECTION (PM review round 1) — 2026-08-04

### Review read
docs/pm/sessions/S03-T01-channel-crud/PM_REVIEW.md (all 9 blocking findings).

### Fixes implemented
1. P1 active-name uniqueness: NEW migration
   `migrations/versions/1c9f2a4b7d8e_active_only_channel_name_uniqueness.py`
   (S02 head 23b308b1fd0b → S03 head): batch rebuild drops the
   unconditional UNIQUE(workspace_id, role, name), creates partial unique
   index `uq_channel_active_workspace_role_name ON channel (workspace_id,
   role, lower(name)) WHERE status='active'` (PRAGMA foreign_keys=OFF for
   the copy-and-move window; rows + FK references preserved).  Model
   updated (Index with func.lower("name") + sqlite_where).  Non-reversible.
2. P1 atomic PATCH CAS: conditional UPDATE
   WHERE id+workspace+revision, rowcount check; stale → 409 with current
   revision; missing/cross-workspace → 404.  Two-thread race test added.
3. P1 archive CAS: POST /{id}/archive now requires
   `{"revision": N}` (ChannelArchiveRequest); active+match → archived (one
   bump); already archived → idempotent 200 no bump; active+stale → 409.
4. P1 projects.py revert: `git checkout HEAD -- app/api/routes/projects.py`;
   `git diff` shows no S03-T01 diff (verified).
5. P2 explicit-null PATCH: model_fields_set + UNSET sentinel; omitted =
   unchanged, explicit null = clear (color/target_language/
   default_output_profile/avatar_artifact_id).  Tests for both.
6. P2 workspace ownership: workspace_id threaded through GET/PATCH/archive
   and every repository predicate; cross-workspace id = 404 (test).
7. P2 one-transaction create: workspace bootstrapped in the same
   transaction via sqlite INSERT..ON CONFLICT DO NOTHING (race-safe);
   removed two-transaction _ensure_workspace.
8. P2 timestamp serialization: _dt_iso (required) vs _dt_iso_optional
   (None → JSON null); archived_at never "".
9. P2 metadata boundary: avatar_artifact_id supported on create/update/
   clear with FK validation; unknown artifact propagates the real
   IntegrityError (not masked as name conflict) — test added.

### New deterministic tests (fail on the previous implementation)
- test_concurrent_case_variant_create_one_wins (racing case-variant create)
- test_two_session_revision_race_exactly_one_wins (CAS race)
- test_cross_workspace_channel_is_404 (workspace isolation)
- test_patch_explicit_null_clears_nullable_fields / omitted-keeps
- test_archive_stale_revision_409_and_idempotent_repeat
- test_archived_name_can_be_reused (was: cannot)
- test_avatar_artifact_id_set_and_cleared / rejects_unknown_artifact
- test_upgrade_from_s02_preserves_referenced_archived_channel
- test_s03_head_index_is_active_only_and_case_insensitive
- conftest: deps._channel_service reset per test (singleton rebind)

### Validation (correction round)
- pytest tests/test_channel_crud.py → 22 passed
- pytest tests/test_persistence_bootstrap.py tests/test_channel_crud.py
  → 46 passed
- pytest tests/test_channel_workspace.py tests/test_channel_crud.py
  tests/test_persistence_bootstrap.py → 56 passed
- ruff check app tests → All checks passed!
- mypy app → Success: no issues found in 55 source files
- git diff --check → exit 0 (PM_REVIEW.md restored from HEAD)
- channels.json SHA256: dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555
  (unchanged; UI_UX_DESIGN_STANDARD.md untouched)
- Full quality baseline: pending run (recorded below)
- Full suite (gate 2 marker): 424 passed, 8 skipped, 7 deselected
  (261.86s) — after updating the two durable-job tests that pinned the
  S02 head revision (now S03 head 1c9f2a4b7d8e; S02 revision is an
  ancestor).
- Quality baseline run 20260804-014257: OVERALL PASS — all 7 gates
  (Python tests 265.42s, lint, typing, tsc, eslint, next build).
- FINAL GATE: targeted suites 56 passed; ruff clean; mypy clean;
  git diff --check exit 0; channels.json SHA256 unchanged
  (dd7aae2609...); projects.py zero diff; no stray files.

## CORRECTION (PM review round 2) — 2026-08-04

### Review read
docs/pm/sessions/S03-T01-channel-crud/PM_REVIEW.md round 2 (6 findings).

### Fixes implemented
1. P1 ORM index DDL: models.py now uses `sa_text("lower(name)")` — compiled
   DDL is `lower(name)` (verified via CreateIndex compile + a new
   test_orm_metadata_index_ddl_matches_migration that also creates a schema
   from ORM metadata and proves case-variant active duplicates fail while
   archived-name reuse succeeds; migration DDL asserted identical).
2. P1 avatar FK → actionable 4xx: new ArtifactReferenceError + pre-CAS
   validation in the repository (missing / cross-workspace / non-image);
   routes map it to HTTP 422 with a precise detail.  No raw IntegrityError
   escapes.  Tests: rejects_unknown_artifact (exact 422 + detail),
   rejects_cross_workspace (exact 422 + detail).
3. P2 name/description null contract: PATCH with `name: null` → 422
   (validated in the route BEFORE repository binding);
   `description: null` → normalized to "" (required empty string, never
   NULL).  Only nullable metadata uses the clear sentinel.  Tests:
   test_patch_name_null_is_422, test_patch_description_null_normalizes_to_empty.
4. P2 concurrent archive idempotency: after a zero-row archive CAS the
   repository re-reads within the transaction and returns the current
   archived row idempotently (200, no bump) when another caller already
   archived; stale active revision still 409.  Deterministic two-thread
   test: test_concurrent_archive_race_both_idempotent → [200, 200], one bump.
5. P2 migration FK evidence: test_s03_upgrade_preserves_fk_integrity
   asserts PRAGMA foreign_keys=1 AND PRAGMA foreign_key_check returns zero
   violations after S02→head (project + video_item references included).
6. P3 ancestry evidence: test_s03_head_descends_from_s02_revision walks
   the Alembic revision graph (ScriptDirectory.walk_revisions) and proves
   `23b308b1fd0b` is an ancestor of head `1c9f2a4b7d8e`.

### Validation (correction round 2)
- pytest tests/test_channel_crud.py tests/test_persistence_bootstrap.py
  → 52 passed
- + tests/test_channel_workspace.py → 63 passed
- ruff check app tests → All checks passed!
- mypy app → Success: no issues found in 55 source files
- git diff --check → exit 0
- channels.json SHA256 unchanged (dd7aae2609...); UI_UX file untouched;
  projects.py zero-diff; PM_REVIEW.md restored from HEAD (not overwritten);
  no data/ dir (no scratch production DB).
- Full quality baseline: recorded below.
- Full quality baseline run 20260804-020357: OVERALL PASS — all 7 gates
  (Python tests 262.38s, lint, typing, tsc, eslint, next build).

## CORRECTION (PM review round 3 — final) — 2026-08-04

### Review read
docs/pm/sessions/S03-T01-channel-crud/PM_REVIEW.md round 3 (3 findings).

### Fixes implemented
1. Fresh read after zero-row archive CAS (finding 1): the re-read after a
   lost archive CAS now uses an explicit SELECT (bypassing the identity
   map — `session.get` would return the caller's stale in-session ACTIVE
   object).  Deterministic repository-level interleaving test
   `test_archive_interleaving_both_callers_read_active_then_cas`: two
   sessions both read ACTIVE, pause on a barrier before their CAS; A
   archives (revision 2), B's zero-row CAS re-reads fresh and returns the
   archived row idempotently → [archived:2, archived:2], final revision 2.
2. UPDATE-time unique-index backstop (finding 2): `update_channel` now
   wraps the CAS UPDATE in try/except IntegrityError; ONLY
   `"UNIQUE constraint failed"` is mapped to NameConflictError (HTTP 409),
   all other integrity errors propagate unmasked.  Deterministic
   concurrent two-channel rename-to-one-free-name test
   `test_concurrent_rename_to_one_free_name_exactly_one_wins` instruments
   the pre-check to prove it saw NO blocker at read time for both callers,
   so the loser's NameConflictError is provably the UPDATE-time partial
   unique-index violation.  Exactly one rename wins, one conflict.
3. Future-safe durable-job head tests (finding 3): both
   `test_head_revision_is_durable_job_schema` and
   `test_initialize_existing_s01_db_backs_up_before_upgrade` now resolve
   the CURRENT Alembic head dynamically (ScriptDirectory.get_current_head)
   and prove `23b308b1fd0b` ancestry via walk_revisions — no hard-coded
   S03 head constant; future migrations cannot break them.  Removed the
   `S03_HEAD_REVISION` constant.

### Validation (correction round 3)
- pytest tests/test_channel_crud.py → 28 passed (incl. both new
  deterministic interleaving tests)
- pytest tests/test_channel_crud.py tests/test_persistence_bootstrap.py
  tests/test_channel_workspace.py + durable-job head tests → 67 passed
- ruff check app tests → All checks passed!
- mypy app → Success: no issues found in 55 source files
- git diff --check → exit 0
- channels.json SHA256 unchanged (dd7aae2609...); UI_UX file untouched;
  projects.py zero-diff; PM_REVIEW.md restored from HEAD; no data/ dir.
- Full quality baseline: recorded below.
- Full quality baseline run 20260804-022303: OVERALL PASS — all 7 gates
  (Python tests 262.94s, lint, typing, tsc, eslint, next build).
