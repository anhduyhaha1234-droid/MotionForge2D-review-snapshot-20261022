# Durable Video Item API (S03-T03)

**Status:** Implemented for S03-T03 review
**Contract:** `docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md` §4 (`video_item`)
**Persistence:** `app/persistence/videos.py` (SQLite via the S01 `video_item`
table; **no new migration** — the existing schema already enforces the
contract)
**Routes:** `app/api/routes/durable_videos.py` (prefix
`/api/v2/projects/{project_id:uuid}/videos`)
**Scope:** Durable Video Item lifecycle + atomic ordering.  No JSON
dual-write, no filesystem/media writes, no hard delete; `channels.json`
and every legacy `/api/projects` route untouched.

## 1. Purpose

Users can add, inspect, update, archive, and atomically reorder durable
Video Items inside a durable Project through an explicit transition
namespace, without touching legacy filesystem workflows.  Every Video
Item belongs to exactly one Project and is workspace-scoped through that
Project.  Source artifact/probe metadata (`duration_ms`, `width`,
`height`, `fps_num`, `fps_den`, `source_artifact_id`) is read-only in
this task — S05 owns import and media probing.

## 2. Endpoints — `/api/v2/projects/{project_id:uuid}/videos`

| Method | Path | Purpose | Status codes |
|---|---|---|---|
| GET | `/api/v2/projects/{project_id:uuid}/videos` | List (workspace-scoped; `status`, `active_only` filters; archived excluded by default) | 200, 404 |
| POST | `/api/v2/projects/{project_id:uuid}/videos` | Append Video Item at end (SQLite only) | 201, 404, 409, 422 |
| GET | `/api/v2/projects/{project_id:uuid}/videos/statuses` | Exact approved pipeline status set | 200 |
| GET | `/api/v2/projects/{project_id:uuid}/videos/{video_id:uuid}` | Read one within project (archived readable) | 200, 404 |
| PATCH | `/api/v2/projects/{project_id:uuid}/videos/{video_id:uuid}` | Update with atomic revision CAS | 200, 404, 409, 422 |
| POST | `/api/v2/projects/{project_id:uuid}/videos/{video_id:uuid}/archive` | Archive with atomic revision CAS (idempotent) | 200, 404, 409, 422 |
| POST | `/api/v2/projects/{project_id:uuid}/videos/reorder` | Atomic full-list reorder (complete active set, exactly once) | 200, 404, 409, 422 |

Query params: `workspace_id` (default `default`), `status` (one of the 13
exact statuses), `active_only` (default `true`).

**No DELETE route exists** — archive is the only removal path (contract
§4/§5, AC1/AC5).  A non-UUID path never matches the UUID-constrained
routes (FastAPI returns 404 for a failed convertor).

## 3. Namespace isolation (AC1/AC9)

- All durable Video Item routes live under the UUID-constrained v2
  project path.  Every existing `/api/projects` route — base
  list/create, literal sub-routes (`/channels`, `/gpu-info`,
  `/presets/...`, `/video`) and nested item routes — is untouched and
  keeps serving the current filesystem workflows until a later
  vertical-slice migration/cutover task.
- Durable endpoints write SQLite only; they never create a project
  directory, `project.json`, media bytes, or any JSON dual-write, and
  never invoke legacy filesystem services (no shadowing, no proxying).
- The UUID path convertors guarantee v2 item paths never capture literal
  legacy paths or legacy 12-hex project ids.

## 4. Semantics

### Statuses (AC2)

- `status` is exactly one of the 13 approved states: `imported`,
  `analyzing`, `objects_ready`, `mapping_required`, `demo_required`,
  `demo_approved`, `applying_reskin`, `needs_review`,
  `ready_to_export`, `rendering`, `completed`, `failed`, `archived`
  (schema CHECK + DTO enum; the `/statuses` endpoint exposes the exact
  set).
- `title` is normalized (trimmed) to a non-empty 1-240 character string
  on create/update; blank or >240 titles are 422.

### Positions and ordering (AC3)

- `position` is non-negative and unique within a Project
  (`UNIQUE(project_id, position)` in the S01 schema).
- Create appends at the end: `MAX(position) + 1` over ALL rows (active +
  archived) so positions stay unique; archiving the middle leaves
  positions stable and a new append goes after the max (no duplicates;
  archived slots are intentionally preserved, so numeric gaps may exist
  after archive).
- The active list is ordered by `position`, then `created_at`, and
  excludes archived by default.
- **Logical active order is gap-tolerant after archive.**  Archive
  preserves positions; reorder maps the requested active order onto the
  SORTED existing active position slots, so a reorder never collides
  with an archived row and never rewrites archived positions (e.g. with
  A=0, B=1 archived, C=2, reorder `[C, A]` places C at 0 and A at 2 —
  never A at 1, which would collide with the archived B).  The domain
  contract only requires a unique non-negative position and owned
  ordering, not gap-free numeric positions.

### Channel references (AC3/AC4)

- `source_channel_id` is nullable and clearable (explicit JSON `null`
  on PATCH clears; omitted = unchanged).
- NEW references are validated atomically inside the caller's
  transaction at the write boundary: the channel must exist, belong to
  the same workspace, have role `source` and be ACTIVE at assignment
  time.  Violations map to HTTP 422 with a precise detail message.
- Existing references are NOT revalidated on later updates: a channel
  archived AFTER assignment keeps the Video Item reference valid (no
  cascade, contract §5).

### Optimistic concurrency (AC4)

- `PATCH` and `POST .../archive` execute a conditional database UPDATE
  with `WHERE id = :id AND project_id = :pid AND revision =
  :expected` (archive additionally guards `status != 'archived'`) and
  inspect the affected row count:
  - 1 row → accepted; `revision` bumped exactly once by the SQL;
  - 0 rows + row exists (wrong revision) → 409 with the current
    revision;
  - 0 rows + missing/other-workspace/other-project → 404.
- Generic PATCH can never enter or leave `archived` (422 for
  `status: "archived"`; 409 for any update against an archived row —
  the archive endpoint is the only removal path).
- `POST .../archive` requires a body `{"revision": <expected>}`:
  - active + matching revision → archived (one bump);
  - already archived → idempotent 200 returning the current row (no
    bump, even with a stale revision);
  - active + stale revision → 409;
  - concurrent archive race: the caller that loses the CAS re-reads the
    row with a FRESH database SELECT (`populate_existing=True`,
    bypassing the identity map) and returns the now-archived row
    idempotently (200, no bump);
  - unknown/cross-project → 404.

### Concurrent create append (task concurrency bullet)

- Append is serialized by the SQLite writer reservation (`BEGIN
  IMMEDIATE` in the service) and backed by the `UNIQUE(project_id,
  position)` index.  If a concurrent append loses the position race the
  repository raises `AppendRetry` (only for a position-uniqueness
  violation; every other integrity error propagates as the real
  failure), and the service retries once deterministically inside the
  same reserved write transaction.  A raw `IntegrityError` never leaks
  to the API (deterministic seam coverage in
  `tests/test_video_item_crud.py`).

### Reorder (AC3/AC4)

- The request carries the expected Project revision and the COMPLETE set
  of active Video Item ids exactly once, in the desired order:
  - duplicate ids → 422 (`"exactly once"`);
  - missing/extra/cross-project ids → 422 (`"missing=... extra=..."`)
    BEFORE any write (no partial writes);
  - stale `project_revision` → 409.
- Reorder is one transaction: the Project row is bumped exactly once
  (CAS on `project_revision`); only Video Items whose position changes
  are bumped; the requested active order is mapped onto the sorted
  existing active position slots and positions are rewritten with
  collision-safe two-phase offsets (`MAX(position)+N+1` first, then the
  desired active slots) so the `UNIQUE(project_id, position)` index
  never fires mid-transaction and archived positions are never touched.

### Workspace ownership (AC6)

- `workspace_id` is threaded through every route and repository
  predicate (via the owning Project join).  A Project or Video Item
  from another workspace is a 404 and can never be read or mutated.
- A Video Item id from another Project is a 404 within the requesting
  project's namespace.

### Archive (AC5)

- Archive sets `status=archived` + `archived_at` (UTC now); timestamps,
  channel references, probe metadata, title and revision history are
  preserved.  No cascade, no hard delete, no artifact-byte deletion.
- Archived Video Items are excluded by the default `active_only=true`
  list and remain readable via GET and filterable with
  `active_only=false` or `status=archived`.

### Archived Project invariants (AC7)

- Archived Projects remain readable (list/read) but reject new Video
  Items, reorder, and active workflow mutation (PATCH) with 409 until a
  restore policy exists.  Archived Videos remain archivable idempotently.

## 5. DTO / ORM boundary (AC2/AC6)

- API responses are Pydantic DTOs (`VideoItemData`); the repository
  returns plain dataclass read records (`VideoItemRecord`).  No ORM
  instance, no `_sa_instance_state`, no absolute paths ever cross the API
  boundary.
- Response fields: `video_item_id`, `project_id`, `workspace_id`,
  `legacy_id`, `title`, `position`, `status`, `source_artifact_id`,
  `source_channel_id`, `duration_ms`, `width`, `height`, `fps_num`,
  `fps_den`, `resume_step`, `resume_payload_json`, `created_at`,
  `updated_at`, `archived_at`, `revision`.
- Timestamps: required timestamps serialize as ISO-8601 UTC-aware
  strings; optional `archived_at` serializes as JSON `null` when unset.
- PATCH null semantics: omitted field = unchanged; explicit JSON `null`
  clears truly nullable metadata (`source_channel_id`, `resume_step`).
  `title: null` / `status: null` are 422 validation errors; probe
  metadata is read-only.
- Create payload (`POST .../videos`): `title` (1-240, trimmed),
  `source_channel_id` (nullable), `resume_step` (nullable) only.  The
  request model **forbids unknown fields** (`extra: forbid`), so probe
  fields (`duration_ms`, `width`, `height`, `fps_num`, `fps_den`) sent
  on create are rejected with 422 — they are read-only in S03 and S05
  owns import/probing.  They remain in the response DTO
  (`VideoItemData`) for later S05 population.

## 6. Transactions

- `VideoItemRepository` never commits on its own (contract §6); the
  `VideoItemService` opens exactly ONE short session per request
  operation — every request is transaction-bounded.  Writes acquire the
  SQLite writer reservation (`BEGIN IMMEDIATE`) from their first read,
  so a competing Channel/Project archive cannot commit between channel
  validation and the Video Item write (S03-T02 atomic writer policy).

## 7. Migration status (AC8)

- **No migration added.**  The S01 `video_item` table already enforces
  the approved Video Item contract: `CHECK (length(title) BETWEEN 1 AND
  240)`, `CHECK (position >= 0)` + `UNIQUE(project_id, position)`, exact
  13-state status CHECK, `revision > 0` CHECK, RESTRICT FKs to
  `project`/`channel`/`artifact`.  The S03-T03 head is the S03-T02 head
  (`1c9f2a4b7d8e`); the table set is unchanged.
