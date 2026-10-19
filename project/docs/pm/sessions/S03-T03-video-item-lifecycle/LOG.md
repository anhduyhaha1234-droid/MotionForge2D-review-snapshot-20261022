# S03-T03 - Execution Log

Append-only.

## Baseline (2026-08-04, before any code change)

### Required reading (all read in full)
1. `docs/pm/SESSION_PROTOCOL.md`
2. `docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md` (video_item entity,
   aggregate boundaries, transaction contract, migration policy,
   acceptance invariants)
3. `docs/architecture/PROJECT_API.md` (S03-T02 approved durable project
   contract — CAS pattern, workspace ownership, namespace isolation)
4. `docs/PRODUCT_REQUIREMENTS_V2.md` §4.4 (Video Item pipeline states)
5. S03-T01 task/report/review (APPROVED) + S03-T02 task/report/review
   (APPROVED) + migration head `1c9f2a4b7d8e`
6. `app/persistence/models.py` (VideoItem/Project/Channel/mixins — the
   S01 schema already carries the full video_item CHECK constraints:
   title 1-240, position >= 0 + per-project unique, exact status set,
   revision > 0, RESTRICT FKs)
7. `app/persistence/channels.py` + `app/persistence/projects.py`
   (repository/service pattern to mirror: atomic CAS with conditional
   UPDATE, fresh re-read after lost archive CAS, `BEGIN IMMEDIATE`
   write reservation, workspace bootstrap in the same transaction)
8. `app/api/app.py`, `app/api/deps.py`, `app/api/routes/durable_projects.py`
9. `app/schemas/__init__.py`, `app/persistence/__init__.py`,
   `app/persistence/engine.py`
10. `tests/conftest.py`, `tests/test_project_crud.py`,
    `tests/test_channel_crud.py`, `tests/test_persistence_bootstrap.py`

### Key facts verified from source (not assumed)
- S03-T02 head `1c9f2a4b7d8e`; the S01 `video_item` table already
  carries CHECK constraints: title length 1-240, `position >= 0`,
  `UNIQUE(project_id, position)`, exact 13-state status CHECK, positive
  revision, RESTRICT FKs to `project`/`channel`/`artifact`.  The
  approved VideoItem contract is fully enforceable WITHOUT a new
  migration (AC8 — migration only if the schema cannot enforce).
- S03-T02 atomic-writer policy: CREATE/PATCH/archive acquire
  `BEGIN IMMEDIATE` before channel validation so a competing channel
  archive cannot commit between validation and assignment.  The same
  policy must guard Video Item source-channel assignment (task
  concurrency bullet).
- S03-T02 idempotent-archive pattern: already-archived row returns the
  current row without bump; lost archive CAS re-reads with a FRESH
  database SELECT (`populate_existing=True`) bypassing the identity map.
- `Project.video_items` relationship already exists with
  `order_by="VideoItem.position"`; no model change needed.
- conftest `_patch_project_root` already resets `_channel_service` and
  `_project_service`; a `_video_service` reset must be added the same
  way (lazy singleton).
- Legacy routes are untouched: the durable v2 namespace
  `/api/v2/projects/{project_id:uuid}/videos` is UUID-constrained and
  disjoint from every legacy `/api/projects` route.

### Protected user changes (pre-existing)
- `channels.json` modified in the working tree (M, +224 insertions vs
  HEAD, SHA256 dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555).
  PRESERVE byte-for-byte (same hash as the S03-T02 final evidence).
- `docs/pm/sessions/S03-T03-video-item-lifecycle/run-hermes.ps1`
  untracked (user file) — leave untouched.
- No other modified/untracked files.

### Baseline commands + results
- `git status --short` → `M channels.json` + untracked run-hermes.ps1
- Alembic chain: a1b2c3d4e5f6 → 23b308b1fd0b → 1c9f2a4b7d8e (head)
- channels.json SHA256 (baseline):
  dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555
- `python -m pytest -q tests/test_channel_crud.py
  tests/test_project_crud.py tests/test_persistence_bootstrap.py
  --cache-clear` → **89 passed** (baseline green)

### Plan (≤7 steps)
1. Add durable Video Item DTOs to `app/schemas/__init__.py` (VideoStatus
   exact 13 states, VideoItemData/VideoCreate/VideoUpdate/
   VideoArchiveRequest/VideoReorderRequest/VideoListResponse — mirror
   Project DTOs; no ORM/absolute paths).
2. Create `app/persistence/videos.py`: VideoRepository (transaction-
   bounded; create appends at end, list/read, PATCH CAS, explicit
   archive idempotent, one-transaction reorder with two-phase positions,
   channel-aware source assignment at the atomic boundary; no hard
   delete) + VideoService (one session per operation; workspace/project
   validation; archived-project guard).  Export from
   `app/persistence/__init__.py`.
3. Wire `deps.get_video_service()` (lazy singleton over the durable DB)
   + register the router in `app/api/app.py` after durable_projects.
4. Create `app/api/routes/durable_videos.py` — `/api/v2/projects/
   {project_id:uuid}/videos` list/create/statuses/read/PATCH/archive +
   atomic full-list reorder; no DELETE; archived-project guard (404/409);
   exact 404/409/422 mapping.
5. Create `tests/test_video_item_crud.py` — AC1-AC10 incl. deterministic
   append/reorder CAS interleavings, archive identity-map behavior,
   Channel archive vs new assignment, archived-project invariants,
   namespace isolation, channels.json hash snapshot.
6. Run focused + combined + race + bootstrap + upgrade suites, Ruff,
   mypy, `git diff --check`, then the full 7/7 quality baseline.
7. Update `docs/architecture/VIDEO_ITEM_API.md`, `LOG.md`, `REPORT.md`;
   leave status SUBMITTED (no commit).

## Resume round 1 (2026-08-04) — deadlocking append test replaced

### Problem reproduced (real output)
- `python -m pytest -q tests/test_video_item_crud.py -k append_interleaving --cache-clear -x` → **timed out after 120s** (deadlock).
- Root cause (test-only, NOT production): the service thread acquires the
  SQLite writer reservation (`BEGIN IMMEDIATE`) before reaching the test's
  `Barrier(2)`, so the raw thread waited at the barrier forever.  The
  production `VideoItemService.create` retry path is correct (rollback +
  re-`BEGIN IMMEDIATE` + one deterministic retry); the test's thread
  interleaving could never release its own barrier.
- `python -m pytest -q tests/test_video_item_crud.py -k "not append_interleaving" --cache-clear` → **34 passed** (only the append test hung).

### Change (allowed scope: tests/test_video_item_crud.py)
- REPLACED `test_append_interleaving_retries_deterministically` with
  `test_append_retry_seam_one_retry_never_leaks_integrity_error` — a fully
  deterministic repository/service seam (no threads, no barriers, no sleeps):
  1. Repository seam: monkeypatch `repo._next_position` to collide with an
     existing row → `create_video` must translate the SQLite UNIQUE
     violation into `AppendRetry` (raw `IntegrityError` never escapes).
  2. Service seam: monkeypatch `VideoItemRepository.create_video` to raise
     `AppendRetry` exactly once then delegate to the real implementation →
     `VideoItemService.create` retries exactly once (asserted via a call
     log) inside its reserved transaction, succeeds at the next free
     position, and never leaks `IntegrityError`.
- Kept the real-concurrency API coverage (`test_concurrent_append_never_leaks_integrity_error`).
- Production code untouched by this round (no semantics weakened).

### Resume round 1 validation
- Focused: `python -m pytest -q tests/test_video_item_crud.py --cache-clear` → **35 passed** (10.46s)
- Combined: `python -m pytest -q tests/test_channel_crud.py tests/test_project_crud.py tests/test_persistence_bootstrap.py tests/test_video_item_crud.py --cache-clear` → **124 passed** (29.77s)
- Legacy: `python -m pytest -q tests/test_api.py tests/test_preset_manager.py tests/test_clip_cancel_persist.py tests/test_delete_and_autosegment.py tests/test_list_projects.py tests/test_channel_workspace.py tests/test_list_objects.py tests/test_trailing_slash.py tests/test_performance_automation.py tests/test_video_slicing.py --cache-clear` → **103 passed, 6 skipped** (202.86s)
- Ruff: `python -m ruff check app tests` → **5 pre-existing findings** (I001 app/persistence/__init__.py + app/persistence/videos.py, N818 AppendRetry, B007 videos.py:744, F841 test_video_item_crud.py:1137) — all present in the earlier implementation; the new seam test introduced ZERO new findings.
- mypy: `python -m mypy app` → **3 pre-existing findings** (videos.py:933/934 valid-type, durable_videos.py:290 attr-defined) — none in the seam test (mypy checks `app` only; tests are not type-checked).
- `git diff --check` → **exit 0** (CRLF warnings only)
- channels.json SHA256: **dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555** (unchanged from baseline)
- New doc: `docs/architecture/VIDEO_ITEM_API.md` written.

## Resume round 1 — gate cleanup (2026-08-04)

The first 7/7 baseline run (run id 20260804-050624) showed Gate 3 (Ruff)
and Gate 4 (mypy) FAIL with the 5+3 pre-existing findings listed in the
previous entry.  Per TASK.md these files are task-owned, so the findings
were resolved in-scope (mechanical, zero behavior change):

- Ruff: `ruff check --fix` sorted the two I001 import blocks; renamed the
  internal signal class `AppendRetry` → `AppendRetryError` (N818, all
  references in app/persistence + tests updated); `_i` loop var (B007);
  removed unused `pid`/`project` locals (F841).
- mypy 2.3.0 rejects a method literally named `list` returning `list[...]`
  (`valid-type`); renamed `VideoItemService.list` → `list_videos`
  (consistent with `VideoItemRepository.list_videos`; single call site in
  durable_videos.py updated).  The remaining `attr-defined` in the reorder
  route disappeared once the service method returned a properly typed list.
- Re-verified after cleanup: Ruff **All checks passed!**, mypy **Success:
  no issues found in 59 source files**, focused+project 64 passed, combined
  124 passed.

### Final validation (after gate cleanup)
- Focused: `python -m pytest -q tests/test_video_item_crud.py --cache-clear` → **35 passed**
- Combined: `python -m pytest -q tests/test_channel_crud.py tests/test_project_crud.py tests/test_persistence_bootstrap.py tests/test_video_item_crud.py --cache-clear` → **124 passed**
- Legacy: 10 files → **103 passed, 6 skipped** (202.86s, run before cleanup; unchanged by cleanup)
- Ruff: `python -m ruff check app tests` → **All checks passed!**
- mypy: `python -m mypy app` → **Success: no issues found in 59 source files**
- `git diff --check` → **exit 0** (CRLF warnings only)
- quality-baseline.ps1 (7 gates) run id **20260804-051459** → **OVERALL PASS (exit 0)**:
  Gate 2 Python tests PASS 282.27s, Gate 3 Ruff PASS, Gate 4 mypy PASS,
  Gate 5 tsc PASS, Gate 6 frontend lint PASS, Gate 7 build PASS
- channels.json SHA256:
  **dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555** (unchanged)

## PM correction round 1 (2026-08-04) — CORRECTION_01.md findings

### Baseline (before any correction code change)
- `git status --short` → same 9 modified + 6 untracked as the resume round;
  user files `channels.json` (M) and `run-hermes.ps1` (untracked) untouched.
- channels.json SHA256: **dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555**
- Focused: `python -m pytest -q tests/test_video_item_crud.py --cache-clear` → **35 passed** (10.63s)
- Combined: `python -m pytest -q tests/test_channel_crud.py tests/test_project_crud.py tests/test_persistence_bootstrap.py tests/test_video_item_crud.py --cache-clear` → **124 passed** (29.67s)
- Ruff: `python -m ruff check app tests` → **All checks passed!**
- mypy: `python -m mypy app` → **Success: no issues found in 59 source files**
- `git diff --check` → **exit 0** (CRLF warnings only)

### Plan (≤7 steps)
1. Reorder: map requested active order onto the sorted EXISTING active
   position slots (gap-tolerant; archived positions preserved untouched);
   add reorder-after-middle-archive + rollback/error regression tests.
2. Probe read-only: remove `duration_ms`/`width`/`height`/`fps_num`/
   `fps_den` from `VideoItemCreate` and from the S03 create write path
   (repository/service/route); keep them in `VideoItemData` read DTO.
   Configure the create request model to forbid unknown fields; add a
   rejection test.
3. Ownership-first PATCH: verify Project/workspace and target Video
   ownership before any channel reference validation; add cross-workspace
   and cross-project PATCH tests with invalid + foreign Channel IDs (all
   404, state intact).
4. Append retry: match ONLY the exact `(project_id, position)` uniqueness
   failure (`uq_video_item_project_position`); other UNIQUE violations
   propagate (regression tests for `(project_id, legacy_id)`).
5. `update_video` 240-char title validation before SQL (same as create);
   direct service/repository tests.
6. AC8 current-head/no-op upgrade preservation test: seed a Video Item
   with Channel reference, probe metadata, resume data, archived state,
   timestamps/revision/position; run `upgrade head` on a fresh engine;
   prove exact preservation + unchanged migration head.
7. Writer-reservation proof: SQL-event deterministic proof that
   `VideoItemService` write reservation (`BEGIN IMMEDIATE`) is entered
   before validation/current-state reads; route the CREATE/PATCH Channel
   races and reorder/append production paths through the real service.
8. Update TASK.md / VIDEO_ITEM_API.md / LOG.md / REPORT.md; leave
   SUBMITTED (no commit).

### Correction round 1 implementation log
- F4 (exact unique match): `create_video` now matches ONLY the
  `(project_id, position)` failure via `_is_position_unique_failure`
  (SQLite message contains `video_item.position`); other UNIQUE
  violations propagate.  Verified SQLite emits
  `UNIQUE constraint failed: video_item.project_id, video_item.position`
  for the position index.
- F2 (probe read-only): removed `duration_ms`/`width`/`height`/
  `fps_num`/`fps_den` from `VideoItemCreate` (+ `extra: forbid`), from
  `VideoItemRepository.create_video`, `VideoItemService.create` and the
  route; kept in `VideoItemRecord`/`VideoItemData` read models.  The
  S05-owned legacy import path still writes probe columns directly
  (untouched).  `test_archive_preserves_metadata_and_relationships`
  updated to no longer send probe fields on create.
- F1 (gap-tolerant reorder): `reorder_videos` maps the requested active
  order onto sorted existing active position slots
  (`_active_positions()`); archived positions never rewritten.
- F3 (ownership-first PATCH): `update_video` calls `_load_video` before
  any channel validation; missing/cross-workspace/cross-project targets
  are always 404.
- F5 (title cap): `update_video` now raises ValueError for >240 chars
  before SQL (same guard as create).
- F6 (AC8 evidence): added `test_upgrade_from_current_head_noop_preserves_full_video_item`
  to tests/test_persistence_bootstrap.py (fresh-engine no-op upgrade,
  full VideoItem seed, exact preservation + unchanged head).
- F7 (writer reservation): added
  `test_service_write_reservation_before_validation_and_reads` (SQL
  events prove `BEGIN IMMEDIATE` precedes channel validation + channel
  SELECT); production CREATE/PATCH channel races and reorder/append
  paths exercise the real `VideoItemService`; repository hook tests for
  the losing-CAS fresh read retained.

### Correction round 1 validation (real output)
- Focused: `python -m pytest -q tests/test_video_item_crud.py --cache-clear` → **43 passed** (12.83s)
- Focused+bootstrap: `python -m pytest -q tests/test_video_item_crud.py tests/test_persistence_bootstrap.py --cache-clear` → **75 passed**
- Combined: `python -m pytest -q tests/test_channel_crud.py tests/test_project_crud.py tests/test_persistence_bootstrap.py tests/test_video_item_crud.py --cache-clear` → **133 passed** (35.38s)
- Legacy: 10 files (unchanged) → **103 passed, 6 skipped** (204.05s)
- Ruff: `python -m ruff check app tests` → **All checks passed!**
- mypy: `python -m mypy app` → **Success: no issues found in 59 source files**
- `git diff --check` → **exit 0** (CRLF warnings only)
- channels.json SHA256 (before/after): **dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555** (unchanged)

### Correction round 1 — fresh full 7/7 baseline
- quality-baseline.ps1 (7 gates) run id **20260804-054059** → **OVERALL
  PASS (exit 0)**: Gate 2 Python tests PASS 285.98s, Gate 3 Ruff PASS,
  Gate 4 mypy PASS, Gate 5 tsc PASS, Gate 6 frontend lint PASS, Gate 7
  build PASS.  Summary:
  `output/quality-baseline/20260804-054059/summary.json`.

## PM correction round 2 (2026-08-04) — CORRECTION_02.md findings

### Baseline (before any correction-2 code change)
- `git status --short` → same 9 modified + 6 untracked as round 1; user
  files `channels.json` (M) and `run-hermes.ps1` (untracked) untouched.
- channels.json SHA256: **dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555**
- Focused: `python -m pytest -q tests/test_video_item_crud.py tests/test_persistence_bootstrap.py --cache-clear` → **75 passed** (18.5s)
- Ruff: `python -m ruff check app tests` → **All checks passed!**
- mypy: `python -m mypy app` → **Success: no issues found in 59 source files**
- `git diff --check` → **exit 0** (CRLF warnings only)

### Plan (≤7 steps)
1. TASK.md AC3: replace "stable contiguous ordering without
   duplicates/gaps" with the corrected domain policy — stable logical
   active ordering, unique non-negative positions, no newly introduced
   gaps, preservation of archived positions.  Sweep every stale
   "no holes"/"contiguous" claim in REPORT/API-doc/code comments so
   evidence matches behavior.
2. Upgrade test: seed EXPLICIT distinguishable `created_at`,
   `updated_at`, `archived_at` (UTC-aware fixed instants), snapshot
   EVERY column before the fresh-engine `upgrade head`, and compare the
   full before/after record exactly with a documented SQLite
   timezone-normalization (`dt.replace(tzinfo=UTC)`).
3. `_is_position_unique_failure`: parse the column list after
   `UNIQUE constraint failed: ` and compare EXACTLY (order+membership)
   to `[video_item.project_id, video_item.position]`; add a pure unit
   test covering exact pair (True) and partial/reordered/legacy-id/other
   messages (False).
4. Focused tests + Ruff + mypy + `git diff --check`.
5. Fresh full 7/7 quality baseline (new run id; never reuse 20260804-054059).
6. Update LOG.md/REPORT.md; leave SUBMITTED (no commit).

### Correction round 2 implementation log
- F1 (AC3 wording): TASK.md AC3 now requires "stable logical active
  ordering: every position is a unique non-negative integer within its
  Project, append goes after the current max, reorder maps the requested
  active order onto the existing active position slots (preserving
  archived positions and introducing no new gaps), and the active list
  is ordered by position then creation time."  Removed the stale
  "no holes"/"no gaps"/"contiguous" phrasing from REPORT.md AC3 row,
  VIDEO_ITEM_API.md "Positions and ordering", the test module docstring,
  the AC3 section comment, the append-after-archive test comment, and a
  "contiguous, no gaps" assertion comment.  The remaining "gap-free
  numeric positions" phrases are intentional contract statements
  (the domain does NOT require gap-free numerics).
- F2 (upgrade test): `_seed_video_item_for_upgrade` now sets explicit
  distinguishable UTC-aware timestamps (`created_at=2026-01-03
  04:05:06.123456+00:00`, `updated_at=2026-02-04 05:06:07.654321+00:00`,
  `archived_at=2026-03-05 06:07:08.321098+00:00`); the test snapshots
  EVERY column via `_snapshot_video_item` before the fresh-engine
  `upgrade head`, then asserts `after == before` (full-record exact
  compare) plus the normalized timestamp equality checks.  The SQLite
  timezone normalization (SQLite stores ISO-8601 UTC text and returns
  naive datetimes; both sides compared as `dt.replace(tzinfo=UTC)`) is
  documented in the test docstring and in `_snapshot_video_item`.
- F3 (exact pair match): `_is_position_unique_failure` now finds the
  LAST `UNIQUE constraint failed: ` marker, parses the column list, and
  compares it exactly (`== ["video_item.project_id",
  "video_item.position"]`).  Partial text (`video_item.position` alone),
  reordered columns (`video_item.position, video_item.project_id`) and
  the legacy-id unique error (`video_item.project_id,
  video_item.legacy_id`) all return False.  New unit test
  `test_position_unique_failure_matches_exact_column_pair` (pure string
  logic over a fake `IntegrityError`, no DB/session).

### Correction round 2 validation (real output)
- Focused: `python -m pytest -q tests/test_video_item_crud.py tests/test_persistence_bootstrap.py --cache-clear` → **76 passed** (18.77s)
- Ruff: `python -m ruff check app tests` → **All checks passed!**
- mypy: `python -m mypy app` → **Success: no issues found in 59 source files**
- `git diff --check` → **exit 0** (CRLF warnings only)
- channels.json SHA256 (before/after): **dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555** (unchanged)

### Correction round 2 — fresh full 7/7 baseline
- Initial round-2 baseline `20260804-055553` exposed a timing flaw in the
  inherited S03-T01 concurrent-rename test. PM added a pre-check barrier so
  both reads deterministically complete before either UPDATE; the exact race
  passed 15/15 repetitions and the combined durable suite passed 134 tests.
- Independent final review: no blocker; Channel + Video + bootstrap 105 passed,
  Ruff/mypy/diff-check passed.
- Fresh mandatory quality baseline run `20260804-060649`: **7/7 PASS**, exit 0
  (512 passed, 8 skipped, 7 deselected in Gate 2).
- PM decision: **APPROVED**.
