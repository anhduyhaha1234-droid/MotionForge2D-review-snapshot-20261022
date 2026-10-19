# Durable Project Summary API (S03-T04)

**Status:** Implemented for S03-T04 review (correction round 1 applied)
**Contract:** `docs/pm/sessions/S03-T04-project-summary/TASK.md`
**Corrections:** `docs/pm/sessions/S03-T04-project-summary/CORRECTION_01.md`
**Read model:** `app/persistence/summaries.py` (`SummaryRepository`)
**Routes:** `app/api/routes/durable_summaries.py` (prefix
`/api/v2/projects`, registered in `app/api/app.py`)
**DTOs:** `app/schemas/__init__.py` (S03-T04 block)
**Scope:** Read-only, live, durable Project summaries for the S04
dashboard.  No migration, no cache, no persisted aggregate, no
filesystem/JSON write, no legacy `/api/projects` route change.

## 1. Purpose

The upcoming dashboard and Project Overview load one honest, durable,
workspace-scoped summary per Project containing project identity,
channel references, Video Item state, a deterministic next action,
active jobs, recent activity and known managed storage — without
navigating the filesystem or polling many endpoints (TASK user outcome).

## 2. Endpoints

| Method | Path | Purpose | Status codes |
|---|---|---|---|
| GET | `/api/v2/projects/summaries` | Collection (active by default; exact `status` filter; bounded `limit`/`offset`) | 200, 422 |
| GET | `/api/v2/projects/summaries/` | Trailing-slash alias of the collection | 200, 422 |
| GET | `/api/v2/projects/{project_id:uuid}/summary` | One Project summary (archived readable) | 200, 404 |
| GET | `/api/v2/projects/{project_id:uuid}/summary/` | Trailing-slash alias of the item route | 200, 404 |

Query params: `workspace_id` (default `default`), `status`
(`draft`|`active`|`needs_review`|`rendering`|`completed`|`archived`),
`limit` (1..200, default 50), `offset` (>= 0, default 0).

**Read-only only (AC1):** both routes expose GET alone; POST/PATCH/
DELETE/PUT are 405.  A non-UUID path never matches the UUID-constrained
item route (FastAPI returns 404 for a failed convertor).  A Project that
does not exist — or exists in another workspace — is a plain 404 (AC6).
An invalid `status` filter is a 422 (FastAPI enum validation); invalid
`limit`/`offset` are 422 (FastAPI query validation).

## 3. Namespace isolation (AC1/AC9/AC10)

- All durable summary routes live under `/api/v2/projects`.  Every
  legacy `/api/projects` route is untouched and keeps serving the
  current filesystem workflows.
- The collection route is declared **before** the UUID-constrained item
  route so `summaries` is never captured as a project id (FastAPI
  ordering; same pattern as `list_all_projects`).
- Durable endpoints read SQLite only; they never create a project
  directory, `project.json`, media bytes, or any JSON dual-write, and
  never invoke legacy filesystem services.

## 4. Read-model contract (derived live, one read boundary)

`SummaryRepository` derives every value **live** from durable rows inside
ONE consistent read boundary (a single request-bounded Session).  There
is no cache, no aggregate table, no migration, no filesystem/JSON write
(AC10).  `summarize_one` and `list_summaries` both call the same
`_summarize` algorithm, so the collection and item routes can never
disagree (AC9).

### 4.1 Project identity, channels, status, revision (AC2/AC8)

- Project identity/status/revision/timestamps come straight from the
  `project` row.
- `source_channel` / `production_channel` are **display-only** Channel
  references (`channel_id`, `name`, `role`, `status`).  Archived
  referenced Channels remain visible (AC8) — the summary never
  revalidates a channel role or status.  The display lookup includes the
  **workspace predicate** (CORRECTION P2.8): a malformed/imported
  cross-workspace reference resolves to an empty display record
  (`name`/`role`/`status` = `""`) — the other workspace's channel
  metadata is never disclosed.

### 4.2 Video counts (AC3)

- Counts come from a `GROUP BY status` over `video_item` (one row per
  video — **no join inflation**).
- `by_status` always contains all 13 approved statuses including zeroes:
  `imported`, `analyzing`, `objects_ready`, `mapping_required`,
  `demo_required`, `demo_approved`, `applying_reskin`, `needs_review`,
  `ready_to_export`, `rendering`, `completed`, `failed`, `archived`.
- `active` = total minus archived; `total` = every row; `completed` =
  count of `completed`; `attention` = `needs_review` + `failed` +
  `mapping_required` + `demo_required`.
- **`completion_percent` = `completed / active * 100`** (zero when there
  are no active videos — CORRECTION P1.3).  The DTO exposes the raw
  counts and the exact completion ratio and **never invents ordinal
  pipeline progress** (contract: "never invent ordinal pipeline
  progress").

### 4.3 Next action (AC4) — deterministic, state-driven, capability-honest

The backend returns **codes, not localized UI prose**.  One stable
semantic `next_action`:

| Field | Meaning |
|---|---|
| `code` | Stable code: `none`, `analyze_video`, `map_objects`, `create_demo`, `apply_reskin`, `review_work`, `export_video`, `retry_failed` |
| `video_item_id` | The exact Video Item the action applies to (nullable) |
| `enabled` | Whether the capability is available today |
| `blocker` | Stable blocker code when disabled: `qc_unavailable`, `output_unavailable`, `capability_unavailable` (nullable) |

Selection is deterministic:
1. Archived Project, or no non-archived videos → `none`, disabled, no
   blocker.
2. A `failed` video anywhere wins (retry first); otherwise the first
   non-archived video by `(position, id)` wins.
3. The Video Item status maps to the code:
   `imported|analyzing → analyze_video`, `objects_ready|mapping_required
   → map_objects`, `demo_required → create_demo`,
   `demo_approved|applying_reskin → apply_reskin`,
   `needs_review → review_work`, `ready_to_export|rendering →
   export_video`, `failed → retry_failed`, `completed|archived → none`.

**Capability honesty (AC4 — the S03-T04 fix).**  Every semantic action
whose fulfilling capability has not landed yet (roadmap PLANNED sprints)
returns `enabled=false` **with a stable blocker** instead of advertising
an unavailable button as enabled:

| code | blocker | owning sprint (PLANNED) |
|---|---|---|
| `analyze_video` | `capability_unavailable` | S05 import/analyze |
| `map_objects` | `capability_unavailable` | S08 object intelligence |
| `create_demo` | `capability_unavailable` | S09 demo-first reskin |
| `apply_reskin` | `capability_unavailable` | S10 full apply |
| `review_work` | `qc_unavailable` | S11 QC/review queue |
| `export_video` | `output_unavailable` | S12 validated output |
| `retry_failed` | `capability_unavailable` | video retry pipeline |

The mapping lives in one explicit constant
(`FUTURE_CAPABILITY_BLOCKERS` in `app/persistence/summaries.py`).  When
a sprint lands, its entry moves to `None` and the action becomes
enabled — the dashboard never needs to re-learn the vocabulary.  No QC
blocker, output version, ETA, human activity or capability/system
readiness is fabricated from other domains before their authoritative
sources exist (contract §read-model).

### 4.4 Active jobs (AC5)

- Exact active states: `pending`, `queued`, `running`, `cancelling`.
- Membership is restricted to jobs owned by the Project itself
  (`owner_type='project'`) or by its **real** Video Items
  (`owner_type='video_item'` + id in the Project's actual video id set,
  active + archived).  Orphan owner ids, cross-workspace owners,
  archived-video owners and terminal states are excluded by
  construction.
- The list is newest-first (`created_at DESC`) with a deterministic
  `created_at DESC, id ASC` tie order (CORRECTION P2.9) and **bounded
  to 10**; `active_job_count` is the full active count (a separate COUNT
  query over the SAME owner predicate, so membership and count agree
  exactly, including the 10-row boundary).
- The DTO exposes only `job_id`, `job_type`, `owner_type`, `owner_id`,
  `state`, `progress`, `created_at` — **no internal/error JSON**.

### 4.5 Storage (AC6)

- Artifact ownership is restricted to the owning Workspace's `artifact`
  rows (`Artifact.workspace_id == workspace_id`) joined to
  `artifact_owner` for the Project or its real Video Items.
- `artifact_count` **deduplicates Artifact ids** (a shared artifact
  owned by several Video Items of the same Project is counted once;
  another workspace's artifacts are never counted).
- `total_bytes` sums `size_bytes` **only for `ready`** artifacts.
  `missing_count` / `trash_count` report the other durable states and
  never contribute bytes; **every** deduplicated artifact with a `NULL`
  size is counted in `unknown_size_count` **regardless of its state**
  (CORRECTION P2.6) and excluded from the byte total.
- Absolute paths are never exposed — only counts/bytes.

### 4.6 last_activity_at (AC7, CORRECTION P1.2/P1.5)

`last_activity_at` = `max(project.updated_at, newest video
updated_at, newest owned-Job activity)` where **owned-Job activity
includes ALL Project- and real-Video-owned Jobs of ANY state** (active
AND terminal) using the authoritative Job `updated_at` (and
`created_at` when a job has never been updated).  `None` only when no
activity exists anywhere (sorts last).

## 5. Collection semantics (AC7/AC9, CORRECTION P1.1/P1.2/P2.7)

- Default filter: active Projects only (`status != 'archived'`);
  `status=<exact>` overrides with that single status
  (`active_only=false` in the response).
- **Global ordering (CORRECTION P1.2):** page selection orders by the
  authoritative `last_activity_at` — `max(project.updated_at, newest
  video updated_at, newest owned-Job activity)` — computed in SQL
  BEFORE `ORDER BY ... LIMIT/OFFSET`, then by project id ASC on ties.
  This is a global order across page boundaries: an old Project with a
  newer Video or terminal Job outranks a recently updated Project.
- `limit`/`offset` bound the page; `total` is the **exact filtered
  count** (a COUNT over the same workspace/filter predicate);
  `has_more` is `true` only when more rows exist after this page
  (`offset + len(page) < total`) — an exactly-full FINAL page reports
  `has_more=false` (CORRECTION P2.7).  The page is fetched with
  `limit + 1` rows so the boundary is exact; the extra row is never
  composed.
- **Query count is CONSTANT** independently of the number of Projects
  and of the page size (CORRECTION P1.1): one page-select + one exact
  total COUNT + the batch composer's fixed query set (video status
  GROUP BY, video ids, max video updated_at, all-Job activity keys,
  next-action videos, active-job list, active-job COUNT, artifact
  ownership, artifact state/size, channel display) — no per-Project
  query anywhere.  The acceptance suite instruments the engine with a
  SQLAlchemy `before_execute` listener and asserts the count for page
  size 1 equals the count for page size N (the pre-correction
  implementation ran 7 queries for 1 Project and 43 for 7).

## 6. DTO / ORM boundary (AC2)

- API responses are Pydantic DTOs (`ProjectSummaryData`,
  `ProjectSummaryListResponse`); the repository returns plain frozen
  dataclasses (`ProjectSummaryRecord`, `VideoCountsRecord`,
  `ActiveJobRecord`, `StorageRecord`, `ChannelDisplayRecord`).  No ORM
  instance, no `_sa_instance_state`, no absolute path ever crosses the
  API boundary.
- Required timestamps serialize as ISO-8601 UTC-aware strings; optional
  timestamps (`archived_at`, `last_activity_at`, job `created_at`)
  serialize as JSON `null` when unset.

## 7. Transactions (CORRECTION P1.4)

`SummaryRepository` never commits/rolls back — reads only, bound to one
request-scoped Session (`get_summary_repository` in `app/api/deps.py`
yields a fresh session per request).

**Explicit read snapshot.**  A single SQLAlchemy Session does NOT by
itself prove one SQLite snapshot for many SELECTs: the SQLite dialect
(pysqlite legacy mode) treats `session.begin()` as a no-op at the DBAPI
level, so the connection stays in implicit autocommit and separate
statements may observe different committed versions.  The dependency
therefore issues a literal `BEGIN` on the driver connection at the
request boundary and closes it with `ROLLBACK` in a `finally` — every
SELECT of the request runs inside ONE SQLite snapshot, and the shared
lock blocks concurrent writers until the request ends.  Zero writes can
escape (AC10).

## 8. Migration status (AC10)

**No migration added.**  The read model reads the S03-T03 head table set
(`1c9f2a4b7d8e`); the schema is unchanged.  No persistent aggregate,
cache or filesystem write exists.

## 9. Acceptance-criteria evidence map

| AC | Evidence |
|---|---|
| 1 | `test_routes_are_read_only_and_workspace_scoped`, `test_item_route_is_read_only_405`, `test_unknown_project_404`, `test_cross_workspace_project_is_404`, `test_cross_workspace_collection_returns_empty` |
| 2 | `test_dto_exact_and_no_leaks`, `test_collection_dto_exact_and_no_leaks`, `test_no_sensitive_job_error_in_dto` |
| 3 | `test_video_counts_exact_no_join_inflation`, `test_completion_ratio_never_invents_progress`, mapping `test_by_status_has_all_13_statuses_with_zeroes`, correction `test_completion_percent_present_and_exact` |
| 4 | `test_next_action_maps_status_deterministically`, `test_next_action_future_capability_disabled_with_blocker`, `test_next_action_capability_honesty_vocabulary`, `test_next_action_imported_uses_earliest_position`, `test_next_action_failed_video_wins_anywhere`, `test_next_action_archived_project_is_none`, `test_next_action_all_completed_is_none`, mapping `test_next_action_future_capabilities_emit_stable_blockers` |
| 5 | `test_active_jobs_only_project_or_video_owned`, `test_active_jobs_exclude_terminal_states`, `test_active_jobs_ordered_newest_first_and_bounded`, `test_cross_workspace_jobs_excluded` |
| 6 | `test_storage_deduplicates_and_policies`, `test_storage_never_counts_other_workspace`, `test_storage_empty_project_zero` |
| 7 | `test_last_activity_reflects_video_update`, `test_collection_ordering_deterministic`, `test_pagination_bounded`, `test_pagination_last_page_has_more_false`, `test_status_filter_exact`, `test_invalid_status_filter_is_422`, `test_invalid_pagination_is_422`, correction `test_old_project_with_newer_video_outranks_recently_updated`, `test_old_project_with_terminal_job_outranks_recently_updated`, `test_has_more_false_when_page_exactly_fills_total`, `test_last_activity_includes_terminal_job_updates`, `test_last_activity_uses_job_updated_at_not_only_created` |
| 8 | `test_archived_project_readable_with_none_action`, `test_archived_project_excluded_from_collection`, `test_archived_channel_reference_visible`, `test_production_channel_display` |
| 9 | `test_collection_and_item_agree`, `test_query_count_bounded`, correction `test_collection_query_count_constant_across_page_sizes`, `test_item_route_query_count_equals_one_page` |
| 10 | `test_no_db_rows_written_by_reads`, `test_legacy_routes_and_files_untouched` |
| 11 | Focused suites `tests/test_project_summary.py` + `tests/test_project_summary_mapping.py`, Ruff, mypy, diff-check (LOG/REPORT) |
| 12 | `test_channels_json_byte_identical_and_unstaged` + LOG/REPORT hash evidence |
