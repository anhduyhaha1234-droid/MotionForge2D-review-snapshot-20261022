# Durable Project API (S03-T02)

**Status:** Implemented for S03-T02 review (correction round — v2 namespace)
**Contract:** `docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md` §4 (project)
**Persistence:** `app/persistence/projects.py` (SQLite via the S01 `project`
table; **no new migration** — the existing schema already enforces the
contract)
**Routes:** `app/api/routes/durable_projects.py` (prefix `/api/v2/projects`)
**Scope:** Durable Project CRUD + archive.  No JSON dual-write, no hard
delete, `channels.json` and every legacy `/api/projects` route untouched.

## 1. Purpose

Users can create, list, read, update and archive durable Projects through
an explicit transition namespace, assigning an optional source Channel and
production Channel with actionable validation and without filesystem/JSON
dual-write.

## 2. Endpoints — `/api/v2/projects`

| Method | Path | Purpose | Status codes |
|---|---|---|---|
| GET | `/api/v2/projects` | List (workspace-scoped; `status`, `active_only` filters) | 200 |
| POST | `/api/v2/projects` | Create durable project (SQLite only) | 201, 422 |
| GET | `/api/v2/projects/statuses` | Exact approved status set | 200 |
| GET | `/api/v2/projects/{project_id:uuid}` | Read one within workspace (archived readable) | 200, 404 |
| PATCH | `/api/v2/projects/{project_id:uuid}` | Update with atomic revision CAS | 200, 404, 409, 422 |
| POST | `/api/v2/projects/{project_id:uuid}/archive` | Archive with atomic revision CAS (idempotent) | 200, 404, 409, 422 |

Query params: `workspace_id` (default `default`), `status`
(`draft`|`active`|`needs_review`|`rendering`|`completed`|`archived`),
`active_only` (default `true`).

**No hard-delete endpoint exists** — archive is the only removal path
(contract §4/§5, AC1/AC5).  A non-UUID path never matches the
UUID-constrained item routes (FastAPI returns 404 for a failed convertor).

## 3. Namespace isolation (AC7)

- All durable routes live under `/api/v2/projects`.  Every existing
  `/api/projects` route — base list/create, literal sub-routes
  (`/channels`, `/gpu-info`, `/presets/...`) and nested item routes — is
  untouched and keeps serving the current filesystem workflows until a
  later vertical-slice migration/cutover task.
- Durable endpoints write SQLite only; they never create a project
  directory or `project.json` and never invoke legacy filesystem
  services (no shadowing, no proxying).
- The UUID path convertor (`[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}`)
  guarantees v2 item paths never capture literal legacy paths or legacy
  12-hex project ids.

## 4. Semantics

### Statuses (AC2)
- `status` is exactly one of `draft`, `active`, `needs_review`,
  `rendering`, `completed`, `archived` (schema CHECK + DTO enum; the
  `/statuses` endpoint exposes the exact set).
- `name` is normalized (trimmed) to a non-empty 1-200 character string on
  create/update; blank names are 422.

### Channel references (AC3)
- `source_channel_id` / `production_channel_id` are nullable and
  clearable (explicit JSON `null` on PATCH clears; omitted = unchanged).
- Newly assigned references are validated atomically inside the caller's
  transaction: the channel must exist, belong to the same workspace, have
  the correct role (`source` → source slot, `production` → production
  slot) and be ACTIVE at assignment time.  Violations map to HTTP 422
  with a precise detail message.
- Existing references are NOT revalidated on later updates: a channel
  archived AFTER assignment keeps the project reference valid (no
  cascade, contract §5).

### Optimistic concurrency (AC4)
- `PATCH` and the first `POST .../archive` execute a conditional database
  UPDATE with `WHERE id = :id AND workspace_id = :ws AND revision =
  :expected` and inspect the affected row count:
  - 1 row → accepted; `revision` bumped exactly once by the SQL;
  - 0 rows + row exists in workspace → 409 with the current revision;
  - 0 rows + missing/other-workspace → 404.
- `POST .../archive` requires a body `{"revision": <expected>}`:
  - active + matching revision → archived (one bump);
  - already archived → idempotent 200 returning the current row (no bump,
    even with a stale revision);
  - active + stale revision → 409;
  - concurrent archive race: the caller that loses the CAS re-reads the
    row with a FRESH database SELECT (bypassing the identity map) and
    returns the now-archived row idempotently (200, no bump);
  - unknown/other-workspace → 404.

### Workspace ownership (AC6)
- `workspace_id` is threaded through GET/PATCH/archive and included in
  every repository predicate.  A project id from another workspace is a
  404 and can never be read or mutated.
- `POST /api/v2/projects` bootstraps the workspace row and creates the
  project in ONE transaction (`INSERT ... ON CONFLICT DO NOTHING` for
  the workspace — race-safe on first use).

### Archive (AC5)
- Archive sets `status=archived` + `archived_at` (UTC now); timestamps,
  channel references, metadata and revision history are preserved.  No
  cascade, no hard delete, no artifact-byte deletion.
- Archived projects are excluded by the default `active_only=true` list
  and remain readable via GET and filterable with `active_only=false` or
  `status=archived`.

## 5. DTO / ORM boundary (AC2/AC6)

- API responses are Pydantic DTOs (`DurableProjectData`); the repository
  returns plain dataclass read records (`ProjectRecord`).  No ORM
  instance, no `_sa_instance_state`, no absolute paths ever cross the API
  boundary.
- Response fields: `project_id`, `workspace_id`, `name`, `description`,
  `status`, `source_channel_id`, `production_channel_id`,
  `default_output_profile`, `resume_step`, `archived_at`, `created_at`,
  `updated_at`, `revision`.
- Timestamps: required timestamps serialize as ISO-8601 UTC-aware
  strings; the optional `archived_at` serializes as JSON `null` when
  unset.
- PATCH null semantics: omitted field = unchanged; explicit JSON `null`
  clears truly nullable metadata (`description`, channel references,
  `default_output_profile`, `resume_step`).  `name: null` / `status:
  null` are 422 validation errors.

## 6. Transactions

- `ProjectRepository` never commits on its own (contract §6); the
  `ProjectService` opens exactly ONE short session per request operation
  — every request is transaction-bounded.
- The workspace row is bootstrapped in the same transaction as the first
  project (atomic, race-safe).

## 7. Migration status (AC8)

- **No migration added.**  The S01 `project` table already enforces the
  approved project contract: `CHECK (length(name) BETWEEN 1 AND 200)`,
  exact `status` CHECK, `revision > 0` CHECK, RESTRICT FKs to
  `workspace`/`channel`.  The S03-T02 head is the S03-T01 head
  (`1c9f2a4b7d8e`); the table set is unchanged.
- Upgrade-from-S03-T01-head preservation evidence in
  `tests/test_persistence_bootstrap.py`:
  1. `test_s03t02_no_migration_needed_head_unchanged` — head is
     `1c9f2a4b7d8e`.
  2. `test_upgrade_from_s03t01_preserves_project_rows` — project rows +
     channel references survive byte-identically.
  3. `test_upgrade_from_s03t01_preserves_archived_project_and_references`
     — archived projects and archived channel references survive.
  4. `test_s03t02_head_table_set_unchanged` — no schema drift (table set
     identical to S02_HEAD_TABLES).
