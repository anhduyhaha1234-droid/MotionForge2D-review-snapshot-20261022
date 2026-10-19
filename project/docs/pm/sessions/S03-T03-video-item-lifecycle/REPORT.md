# S03-T03 - Implementation Report

**Status:** APPROVED (PM correction round 2)
**Task:** Durable Video Item lifecycle and ordering
**Session:** docs/pm/sessions/S03-T03-video-item-lifecycle
**Resume note:** This report covers the full S03-T03 implementation
(durable Video Item repository/service/API + tests), the resume-round
fix that replaced the deadlocking append-interleaving test with a fully
deterministic repository/service seam, and the PM correction round 1
(CORRECTION_01.md findings 1-7).

## Outcome delivered

A durable Video Item repository/service/API implementing the approved
persistence domain contract §4 (`video_item`) on the existing S01
`video_item` table — **no migration added** (the schema already enforces
the contract; head stays `1c9f2a4b7d8e`).  The API lives in an explicit
transition namespace `/api/v2/projects/{project_id:uuid}/videos` and
never shadows, proxies or invokes legacy filesystem services.  Durable
endpoints write SQLite only: no project directory, no `project.json`, no
JSON dual-write, no media bytes, no hard delete.

## Acceptance criteria evidence

| AC | Status | Evidence |
|---|---|---|
| AC1 | PASS | CRUD/list/read/archive/reorder only under `/api/v2/projects/{project_id:uuid}/videos`; no DELETE route in OpenAPI (`test_create_read_update_archive_reorder_lifecycle`, `test_durable_video_create_never_writes_filesystem`); namespace isolation (`test_v2_videos_namespace_never_shadows_legacy_routes`). |
| AC2 | PASS | `test_statuses_are_exact_approved_set` (exact 13 statuses incl. archived); `test_empty_title_rejected_and_max_length` (1-240, trimmed); `test_dto_never_exposes_orm_objects_or_paths`; probe fields read-only on create (`test_create_rejects_extra_probe_fields`, `test_create_rejects_probe_fields_direct_service`). |
| AC3 | PASS | `test_append_is_contiguous_and_after_archive` (fresh appends 0,1,2; after middle archive a new append goes after the max — unique positions, archived slots preserved); `test_reorder_full_list_contiguous` (fresh reorder maps requested order onto 0..N-1 with no new gaps); **gap-tolerant reorder after archive** (`test_reorder_after_middle_archive_gap_tolerant` — archived positions preserved, requested order mapped onto existing active slots; `test_reorder_rollback_on_error_leaves_state_intact`). Logical active ordering is stable and gap-tolerant after archive; the contract requires unique non-negative positions, not gap-free numerics (see TASK.md AC3). |
| AC4 | PASS | `test_stale_revision_returns_409`, `test_every_accepted_update_bumps_revision_once`, `test_two_session_revision_race_exactly_one_wins`, `test_archive_stale_revision_409_and_idempotent_repeat`, `test_patch_cannot_bypass_archive_or_restore_archived_video`, `test_concurrent_archive_race_both_idempotent`, `test_reorder_rejects_duplicate_ids`/`missing_and_extra_ids`/`cross_project_ids`, `test_reorder_stale_project_revision_409`; atomic writer policy `test_channel_archive_cannot_commit_between_validation_and_assignment` (CREATE+PATCH through the real service); append race: `test_concurrent_append_never_leaks_integrity_error` (real threads) + `test_append_retry_seam_one_retry_never_leaks_integrity_error` + **`test_append_retry_does_not_swallow_other_unique_violations`** (only the exact `(project_id, position)` failure retries; `(project_id, legacy_id)` violations propagate and roll back). |
| AC5 | PASS | `test_archive_preserves_metadata_and_relationships`; archived readable/filterable (`test_list_excludes_archived_by_default_and_orders`); idempotent repeat no-bump (`test_archive_stale_revision_409_and_idempotent_repeat`); no cascade/hard delete (no DELETE route). |
| AC6 | PASS | `test_cross_workspace_project_is_404`; `test_video_from_another_project_is_404`; `test_create_rejects_unknown_or_wrong_role_channel`; `test_create_rejects_archived_channel_and_cross_workspace_channel`; `test_patch_assigns_clears_and_validates_channel`; **ownership-first PATCH** (`test_update_ownership_before_channel_validation` — cross-workspace/cross-project/missing targets always 404 even with invalid/foreign Channel IDs, state intact). |
| AC7 | PASS | `test_archived_project_rejects_new_videos_reorder_and_mutation` (409s; archived project remains readable; archived video remains archivable idempotently). |
| AC8 | PASS | No migration needed — S01 schema already enforces the contract (head unchanged `1c9f2a4b7d8e`); **current-head no-op upgrade preservation** (`test_upgrade_from_current_head_noop_preserves_full_video_item` seeds a Video Item with Channel reference, probe metadata, resume data, archived state, timestamps/revision/position, re-runs `upgrade head` through a fresh engine and proves exact preservation + unchanged head). |
| AC9 | PASS | `test_v2_videos_namespace_never_shadows_legacy_routes` (legacy `POST /api/projects/{project_id}/video` still registered; `GET /api/projects/gpu-info` 200); channels.json SHA256 identical before/after; legacy 10-file suite passed (below). |
| AC10 | PASS | Focused 43 passed; combined 133 passed; legacy passed; Ruff/mypy clean; `git diff --check` exit 0; fresh 7/7 baseline below. |

## PM correction round 1 (CORRECTION_01.md)

### Finding 1 — reorder collided with archived positions (fixed)

The old reorder compacted active rows to `0..N-1`.  With positions A=0,
B=1 archived, C=2, reorder `[C,A]` attempted A=1 and collided with the
archived B (leaking IntegrityError/500).  The domain contract only
requires a unique non-negative position and owned ordering — not
gap-free numeric positions.

- **Fix:** `reorder_videos` now maps the requested active order onto the
  SORTED existing active position slots (`_active_positions()`), leaving
  archived rows untouched.  The two-phase collision-safe write still
  applies; the `UNIQUE(project_id, position)` index never fires
  mid-transaction and archived positions are never rewritten.
- **Tests:** `test_reorder_after_middle_archive_gap_tolerant` (A=0,
  B=1 archived, C=2; reorder `[C,A]` → C at 0, A at 2; B untouched at
  1; append D at 3) and `test_reorder_rollback_on_error_leaves_state_intact`
  (stale project revision → 409, no partial writes).
- **Docs:** TASK.md domain bullet + VIDEO_ITEM_API.md "Positions and
  ordering" / reorder sections now state the logical active order is
  gap-tolerant after archive.

### Finding 2 — probe metadata read-only on create (fixed)

`VideoItemCreate`, the route, repository/service and tests accepted
`duration_ms`, `width`, `height`, `fps_num`, `fps_den` on create.

- **Fix:** removed the five probe fields from `VideoItemCreate` and from
  the S03 create write path (`VideoItemRepository.create_video`,
  `VideoItemService.create`, the route).  The request model now forbids
  unknown fields (`model_config = {"extra": "forbid"}`) so extra probe
  fields are rejected with 422 instead of silently accepted.  The
  fields remain in the read DTO (`VideoItemData`/`VideoItemRecord`) for
  later S05 population.  The S05-owned legacy import path
  (`app/persistence/legacy_import.py`) still writes probe columns
  directly — untouched.
- **Tests:** `test_create_rejects_extra_probe_fields` (422 + nothing
  created + read DTO still exposes the fields as null) and
  `test_create_rejects_probe_fields_direct_service` (no write path
  accepts probe data).

### Finding 3 — PATCH ownership verified after channel validation (fixed)

`update_video` validated a source Channel before proving the target
Video belongs to the requested Project/workspace, so missing/
cross-workspace targets could return channel-dependent 422.

- **Fix:** `update_video` now verifies Project/workspace and target
  Video ownership (`_load_video`) BEFORE any channel-reference
  validation or mutation.  Missing/cross-workspace/cross-project
  targets are always a safe 404 regardless of the payload's channel id.
- **Tests:** `test_update_ownership_before_channel_validation` —
  cross-project + invalid/foreign channel, cross-workspace + invalid/
  foreign channel, missing target + invalid channel: all 404, state
  intact.

### Finding 4 — append retry swallowed non-position UNIQUE failures (fixed)

The append retry treated any SQLite `UNIQUE constraint failed` as a
position race.

- **Fix:** `create_video` now matches ONLY the exact
  `(project_id, position)` uniqueness failure (the SQLite message
  contains `video_item.position`); every other unique violation (e.g.
  `(project_id, legacy_id)`) propagates as `IntegrityError` and rolls
  back.
- **Tests:** `test_append_retry_does_not_swallow_other_unique_violations`
  (legacy-id collision propagates + rolls back; position collision is
  still `AppendRetryError`; only the seeded rows remain).

### Finding 5 — update_video missing 240-char title validation (fixed)

`update_video` trimmed the title but did not enforce the maximum 240
used by create.

- **Fix:** the same `len(normalized) > 240 → ValueError` guard now runs
  in `update_video` before any SQL (the API Pydantic `max_length` also
  rejects it as 422; the repository/service guard makes the DB
  `IntegrityError` never the public validation mechanism).
- **Tests:** `test_update_rejects_overlong_title_before_sql` (API 422 +
  direct service `ValueError`, state intact).

### Finding 6 — AC8 upgrade preservation evidence was false (fixed)

No S03-T03 bootstrap/upgrade preservation test existed.

- **Test added:** `test_upgrade_from_current_head_noop_preserves_full_video_item`
  in `tests/test_persistence_bootstrap.py` — builds a database at the
  current head, seeds a fully-populated Video Item (Channel reference,
  probe metadata, resume data, archived state, custom
  timestamps/revision/position), re-runs `alembic upgrade head` through
  a FRESH engine, and proves every field survived byte-identically plus
  the migration head is unchanged (`1c9f2a4b7d8e`).

### Finding 7 — writer reservation + production-path races (fixed/covered)

- **Writer reservation proof:** `test_service_write_reservation_before_validation_and_reads`
  uses deterministic SQL events (no sleeps/timing) to prove the
  production `VideoItemService` write reservation (`BEGIN IMMEDIATE`)
  is entered BEFORE channel validation and BEFORE the channel
  current-state SELECT.
- **Production paths:** the CREATE/PATCH channel races
  (`test_channel_archive_cannot_commit_between_validation_and_assignment`)
  and the reorder/append production paths exercise the real
  `VideoItemService` (the bare-repository hooks for the otherwise
  unreachable losing-CAS fresh read are retained as
  `test_archive_interleaving_both_callers_read_active_then_cas` and
  `test_reorder_interleaving_two_callers_one_wins_one_conflicts`).

## Resume-round change (deadlock fix, round 1 of the original session)

- REPLACED `test_append_interleaving_retries_deterministically` (which
  **deadlocked**: the service thread took the SQLite writer lock before
  reaching the test barrier, so the raw thread waited forever) with
  `test_append_retry_seam_one_retry_never_leaks_integrity_error` — a fully
  deterministic, thread-free seam:
  1. Repository seam: forced `_next_position` collision → `create_video`
     translates the UNIQUE violation into `AppendRetryError` (raw
     `IntegrityError` never escapes).
  2. Service seam: `create_video` raises `AppendRetryError` exactly once
     then delegates to the real implementation → `VideoItemService.create`
     retries exactly once inside its reserved transaction and succeeds at
     the next free position (call log asserts `["attempt","attempt"]`).
- The real-concurrency coverage was kept: `test_concurrent_append_never_leaks_integrity_error`
  (3 threads, all 201, contiguous 0-2) still proves the API-level behavior.
- Production concurrency semantics untouched by that round (the
  correction round tightened the retry predicate — see Finding 4).

## Files changed (correction round 1)

- MODIFIED `app/persistence/videos.py` — gap-tolerant reorder mapping
  onto existing active slots (F1); probe fields removed from the create
  write path (F2); ownership-first update ordering (F3); exact
  position-unique match for append retry (F4); 240-char title
  validation in update_video (F5).
- MODIFIED `app/schemas/__init__.py` — `VideoItemCreate` drops probe
  fields + `extra: forbid` (F2).
- MODIFIED `app/api/routes/durable_videos.py` — create no longer
  forwards probe fields (F2).
- MODIFIED `tests/test_video_item_crud.py` — 43 tests (was 35): 8 new
  correction tests + archive-preserve test updated (probe fields no
  longer writable on create).
- MODIFIED `tests/test_persistence_bootstrap.py` — new current-head
  no-op upgrade preservation test (F6).
- MODIFIED `docs/pm/sessions/S03-T03-video-item-lifecycle/TASK.md` —
  gap-tolerant ordering wording (F1).
- MODIFIED `docs/architecture/VIDEO_ITEM_API.md` — gap-tolerant
  ordering + create-payload probe read-only wording (F1/F2).
- MODIFIED `docs/pm/sessions/S03-T03-video-item-lifecycle/LOG.md`
  (append-only baseline + plan + results).
- MODIFIED `docs/pm/sessions/S03-T03-video-item-lifecycle/REPORT.md`
  (this file).
- UNCHANGED `channels.json` (byte-for-byte, hash below).

## Tests and validation (correction round 1)

| Command | Result |
|---|---|
| `python -m pytest -q tests/test_video_item_crud.py --cache-clear` | **43 passed** |
| `python -m pytest -q tests/test_video_item_crud.py tests/test_persistence_bootstrap.py --cache-clear` | **75 passed** |
| `python -m pytest -q tests/test_channel_crud.py tests/test_project_crud.py tests/test_persistence_bootstrap.py tests/test_video_item_crud.py --cache-clear` | **133 passed** |
| Legacy regression (10 files, unchanged) | **passed** (see LOG) |
| `python -m ruff check app tests` | **All checks passed!** |
| `python -m mypy app` | **Success: no issues found in 59 source files** |
| `git diff --check` | exit 0 (CRLF warnings only) |
| quality-baseline.ps1 (7 gates) | **OVERALL PASS** — fresh run id **20260804-054059** (Gate 2 Python tests PASS 285.98s, Gates 3-7 PASS) |
| channels.json SHA256 | dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555 (unchanged) |

## Migration and rollback

None required.  Head unchanged (`1c9f2a4b7d8e`); the existing schema
enforces the Video Item contract (title 1-240 CHECK, position >= 0 +
UNIQUE(project_id, position), exact 13-state status CHECK, revision > 0
CHECK, RESTRICT FKs).  The no-op upgrade preservation test proves
current-head data survives re-running `upgrade head` unchanged.

## Deviations from task

1. The append race test is a deterministic repository/service seam
   (monkeypatch-forced collision + one-shot AppendRetryError) instead of
   a thread race — the thread version deadlocked on SQLite writer-lock
   ordering and could never exercise the retry path deterministically.
2. Gate cleanup in the original round renamed the internal signal
   `AppendRetry` → `AppendRetryError` and the service method `list` →
   `list_videos` to satisfy Ruff N818 / mypy 2.3.0 `valid-type`; zero
   behavior change, all references updated.
3. No migration, no legacy writes, no roadmap/PRD edits.  No commit.

## PM correction round 2 (CORRECTION_02.md)

Closed the final three evidence inconsistencies:

### Finding 1 — stale AC3 "contiguous/no-gap" contract (fixed)

`TASK.md` AC3 still claimed append/reorder produce "stable contiguous
ordering without duplicates/gaps", contradicting the corrected domain
policy (archive preserves slots; logical active order is gap-tolerant).

- **Fix:** TASK.md AC3 now formally requires a **stable logical active
  ordering**: every position is a unique non-negative integer within its
  Project, append goes after the current max, reorder maps the requested
  active order onto the existing active position slots (preserving
  archived positions and introducing no new gaps), and the active list
  is ordered by position then creation time.
- **Stale-claim sweep:** removed the "no holes"/"no gaps"/"contiguous"
  phrasing from the REPORT AC3 evidence row, VIDEO_ITEM_API.md
  "Positions and ordering" (`no duplicates, no gaps` → archived slots
  intentionally preserved, numeric gaps may exist after archive), the
  test module docstring, the AC3 section comment, the
  append-after-archive test comment, and the "contiguous, no gaps"
  assertion comment.  The only remaining "gap-free numeric positions"
  phrases are deliberate contract statements (the domain does NOT
  require gap-free numerics).

### Finding 2 — upgrade test used automatic timestamps (fixed)

`test_upgrade_from_current_head_noop_preserves_full_video_item` seeded
auto `created_at`/`updated_at` and only asserted non-null — so it could
not actually prove timestamp preservation.

- **Fix:** `_seed_video_item_for_upgrade` now seeds explicit
  distinguishable UTC-aware timestamps (`created_at=2026-01-03
  04:05:06.123456+00:00`, `updated_at=2026-02-04 05:06:07.654321+00:00`,
  `archived_at=2026-03-05 06:07:08.321098+00:00`).
- The test snapshots EVERY persisted column (`_snapshot_video_item`)
  before the fresh-engine `upgrade head` and asserts `after == before`
  — a full before/after record comparison, not field-by-field spot
  checks.  Exact timestamp equality is also asserted on the loaded
  record after normalization.
- The SQLite timezone-normalization comparison is documented in the
  test docstring and in `_snapshot_video_item`: SQLite stores
  `DateTime(timezone=True)` columns as ISO-8601 UTC text and returns
  naive datetimes, so both sides are compared as
  `dt.replace(tzinfo=UTC)` (aware UTC equality); the stored ISO text is
  preserved byte-identically through the no-op upgrade.

### Finding 3 — `_is_position_unique_failure` substring match (fixed)

The append-retry predicate matched the substring `video_item.position`,
so a reordered column list (`video_item.position, video_item.project_id`)
would be misclassified as the append race.

- **Fix:** `_is_position_unique_failure` now finds the LAST
  `UNIQUE constraint failed: ` marker, parses the column list, and
  compares it EXACTLY (order and membership) to
  `["video_item.project_id", "video_item.position"]`.  Partial text
  (`video_item.position` alone), reordered columns, and the legacy-id
  unique error (`video_item.project_id, video_item.legacy_id`) all
  return False; only the exact pair is True.
- **Tests:** new `test_position_unique_failure_matches_exact_column_pair`
  — pure string-logic unit test over a fake `IntegrityError` (no DB):
  exact pair True (both bare and `(sqlite3.IntegrityError)`-prefixed
  messages); partial/reordered/legacy-id/FK messages False.

### Correction round 2 validation (real output)

| Command | Result |
|---|---|
| `python -m pytest -q tests/test_video_item_crud.py tests/test_persistence_bootstrap.py --cache-clear` | **76 passed** (18.77s) |
| `python -m ruff check app tests` | **All checks passed!** |
| `python -m mypy app` | **Success: no issues found in 59 source files** |
| `git diff --check` | exit 0 (CRLF warnings only) |
| channels.json SHA256 | dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555 (unchanged) |
| quality-baseline.ps1 (7 gates) | **7/7 PASS**, run `20260804-060649`, exit 0 |

### Files changed (correction round 2)

- MODIFIED `app/persistence/videos.py` — exact column-pair match in
  `_is_position_unique_failure` (F3) + reorder docstring/comment
  clarification ("no NEW gaps introduced; archived positions never
  rewritten", "archived slots are intentionally preserved").
- MODIFIED `tests/test_video_item_crud.py` — new
  `test_position_unique_failure_matches_exact_column_pair`; stale
  "contiguous/no gaps" comments/docstring updated to the gap-tolerant
  contract (F1/F3).
- MODIFIED `tests/test_persistence_bootstrap.py` — explicit
  distinguishable timestamps + full-record snapshot compare with
  documented timezone normalization (F2).
- MODIFIED `docs/pm/sessions/S03-T03-video-item-lifecycle/TASK.md` —
  AC3 formally revised (F1).
- MODIFIED `docs/architecture/VIDEO_ITEM_API.md` — "no duplicates, no
  gaps" claim corrected (F1).
- MODIFIED `docs/pm/sessions/S03-T03-video-item-lifecycle/LOG.md`
  (append-only round-2 entry) and `REPORT.md` (this section).
- UNCHANGED `channels.json` (byte-for-byte, hash above).  No commit.
