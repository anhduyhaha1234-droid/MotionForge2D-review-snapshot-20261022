# Persistence Domain Contract V1

**Status:** Proposed for S01-T01 review  
**Scope:** SQLAlchemy domain boundary and migration policy  
**Database target:** SQLite 3  
**ORM target:** SQLAlchemy 2.x  

## 1. Purpose

This contract defines the durable authority that later S01 tasks must implement. It does not add an engine, ORM models, migrations, or import code. Existing JSON remains the active runtime authority until S01-T05 completes and the import is explicitly committed.

## 2. Governing rules

- SQLite is the single authority for durable business state after cutover.
- Filesystem artifacts contain media bytes; the database stores identity, ownership, lifecycle and managed relative paths.
- Pydantic request/response schemas remain separate from SQLAlchemy persistence models.
- Every write spanning multiple related rows is one transaction.
- Public IDs are opaque UUIDv7-compatible strings stored as `VARCHAR(36)`; implementations may initially generate UUID4. Existing legacy IDs are retained in `legacy_id`, never reused as a primary key.
- All timestamps are timezone-aware UTC values. SQLite stores ISO-8601 UTC text through a common type adapter.
- Rows use optimistic concurrency through integer `revision`, starting at 1 and incrementing on every business update.
- User-owned records are archived or moved to managed Trash. Hard delete is limited to unreferenced temporary/import-staging rows in a transaction.
- Arbitrary absolute paths are never persisted as managed artifact locations.

## 3. Aggregate boundaries

### Workspace aggregate

`Workspace` is the root ownership boundary for channels, projects and future libraries. V1 creates exactly one local workspace but keeps the key explicit to avoid a later schema rewrite.

### Project aggregate

`Project` owns `VideoItem` ordering and project defaults. A Project may reference at most one source channel and one production channel. Channel deletion cannot cascade into a Project.

### Video aggregate

`VideoItem` is the pipeline unit. It owns its scene records and references its source media artifact. Deleting or archiving a project cannot directly delete artifact bytes.

### Artifact aggregate

`Artifact` records managed files independently from their business owner. An owner link must be explicit so shared or versioned artifacts are not deleted by path guessing.

Jobs, job steps and retry semantics are intentionally deferred to S02-T01. S01 only reserves artifact ownership and import audit fields needed by persistence migration.

## 4. Entity contract

### `workspace`

| Field | Contract |
|---|---|
| `id` | PK, opaque string |
| `name` | Required, 1-120 characters |
| `created_at`, `updated_at` | UTC timestamps |
| `revision` | Positive integer |

### `channel`

| Field | Contract |
|---|---|
| `id` | PK |
| `workspace_id` | Required FK to workspace, restrict delete |
| `legacy_id` | Nullable legacy identifier; unique per workspace when present |
| `role` | `source` or `production` |
| `name` | Required, normalized non-empty display name |
| `description` | Required string, default empty |
| `color`, `avatar_artifact_id` | Optional presentation metadata |
| `target_language` | Optional extension field; does not activate localization |
| `default_output_profile` | Optional string |
| `status` | `active` or `archived` |
| `created_at`, `updated_at`, `archived_at` | UTC timestamps |
| `revision` | Positive integer |

Constraints: `(workspace_id, role, name)` is unique case-insensitively among active channels. Archiving a referenced channel is allowed; hard deletion is restricted.

### `project`

| Field | Contract |
|---|---|
| `id` | PK |
| `workspace_id` | Required FK, restrict delete |
| `legacy_id` | Nullable, unique per workspace when present |
| `name` | Required, 1-200 characters |
| `description` | Required string, default empty |
| `status` | `draft`, `active`, `needs_review`, `rendering`, `completed`, `archived` |
| `source_channel_id` | Nullable FK to a source channel |
| `production_channel_id` | Nullable FK to a production channel |
| `default_output_profile` | Optional string |
| `resume_step` | Nullable stable workflow-step code |
| `created_at`, `updated_at`, `archived_at` | UTC timestamps |
| `revision` | Positive integer |

Cross-row validation must reject a source-channel reference whose role is not `source`, a production-channel reference whose role is not `production`, or any channel from another workspace.

### `video_item`

| Field | Contract |
|---|---|
| `id` | PK |
| `project_id` | Required FK, restrict delete |
| `legacy_id` | Nullable, unique per project when present |
| `title` | Required, 1-240 characters |
| `position` | Non-negative integer; unique per project |
| `status` | Stable pipeline state listed below |
| `source_artifact_id` | Nullable FK until managed import completes |
| `source_channel_id` | Nullable FK; preserves per-video source metadata |
| `duration_ms`, `width`, `height` | Nullable validated probe metadata |
| `fps_num`, `fps_den` | Nullable positive rational frame rate |
| `resume_step`, `resume_payload_json` | Nullable resumable UI state; payload is schema-versioned |
| `created_at`, `updated_at`, `archived_at` | UTC timestamps |
| `revision` | Positive integer |

Pipeline states: `imported`, `analyzing`, `objects_ready`, `mapping_required`, `demo_required`, `demo_approved`, `applying_reskin`, `needs_review`, `ready_to_export`, `rendering`, `completed`, `failed`, `archived`.

`resume_payload_json` is not a second source of truth for domain state. It may contain navigation details such as selected tab, scene or playhead only.

### `scene`

| Field | Contract |
|---|---|
| `id` | PK |
| `video_item_id` | Required FK, cascade row deletion only inside an authorized VideoItem purge transaction |
| `legacy_scene_id` | Nullable integer |
| `position` | Non-negative integer; unique per video |
| `start_frame`, `end_frame` | Zero-based inclusive frame indices |
| `start_time_ms`, `end_time_ms` | Canonical integer time values |
| `status` | `pending`, `draft`, `approved` |
| `created_at`, `updated_at` | UTC timestamps |
| `revision` | Positive integer |

Constraints: start values are non-negative, end values are not before start, and scene ranges cannot overlap after analysis is finalized.

### `artifact`

| Field | Contract |
|---|---|
| `id` | PK |
| `workspace_id` | Required FK |
| `kind` | Stable artifact-kind code |
| `relative_path` | Normalized path relative to the configured managed root |
| `state` | `staging`, `ready`, `trash`, `missing`, `failed` |
| `sha256`, `size_bytes`, `mime_type` | Validation metadata |
| `created_at`, `updated_at`, `trashed_at` | UTC timestamps |
| `revision` | Positive integer |

Constraints: `(workspace_id, relative_path)` is unique. Paths must not be absolute, contain `..`, escape the resolved managed root or point to the database file. A database row becomes `ready` only after an atomic filesystem write succeeds.

### `artifact_owner`

| Field | Contract |
|---|---|
| `artifact_id` | FK to artifact |
| `owner_type` | Allowed entity type code |
| `owner_id` | Owner public ID |
| `purpose` | Stable purpose code such as `source`, `proxy`, `cover`, `render` |

Primary key: `(artifact_id, owner_type, owner_id, purpose)`. Polymorphic ownership is enforced by repository/service validation. An artifact may enter Trash only when no live owner link remains.

### `legacy_import`

| Field | Contract |
|---|---|
| `id` | PK |
| `source_kind`, `source_locator` | Non-secret origin descriptor |
| `source_sha256` | Required checksum |
| `status` | `previewed`, `importing`, `completed`, `failed`, `rolled_back` |
| `summary_json`, `error_json` | Versioned audit payloads |
| `started_at`, `completed_at` | UTC timestamps |

The checksum plus source kind is an idempotency boundary: a completed source cannot be imported twice unless an explicit new import generation is created.

## 5. Relationships and delete behavior

```text
Workspace
  ├─ Channel
  ├─ Project ── optional Source Channel / Production Channel
  │    └─ VideoItem ── optional per-video Source Channel
  │         └─ Scene
  └─ Artifact ── ArtifactOwner ── business entity

LegacyImport records migration attempts independently.
```

- Foreign keys are enabled on every SQLite connection.
- Default relationship deletion is `RESTRICT`.
- ORM cascades must not imply filesystem deletion.
- Project archive cascades no state automatically; VideoItems remain queryable under the archived project.
- Physical purge is a future explicit workflow requiring reference checks and managed Trash evidence.

## 6. Transaction contract

- Service layer opens and owns the transaction; repositories never commit independently.
- Request handlers do not pass ORM instances outside the transaction boundary.
- Artifact creation uses: write temporary file -> fsync/close -> atomic rename -> insert/update artifact row -> commit. On database failure, the finalized file is recorded for reconciliation, never silently deleted outside managed scope.
- Import uses one database transaction per atomic import unit and records progress in `legacy_import`; S01-T05 defines the exact batch boundary.
- SQLite write transactions use a bounded busy timeout. Retry is allowed only for known transient lock errors and must not duplicate entities.

## 7. Migration policy

### Schema versioning

- Use Alembic revision files with immutable revision identifiers.
- The database's Alembic revision is authoritative; application constants cannot impersonate migration state.
- Every schema change has one forward migration and an automated upgrade test from the previous supported revision.
- Destructive or lossy changes require an expand/migrate/contract sequence across releases.

### Startup behavior

- A missing database may be initialized only by an explicit bootstrap path in S01-T02.
- If the database revision is newer than the application supports, startup fails read-only with an actionable error.
- Pending migrations are never applied as a side effect of importing a Python module or serving a normal API request.
- Automatic migration, if later enabled, requires an on-disk backup first and a clearly logged result.

### Legacy JSON migration

- Inventory/preview is read-only and never mutates source JSON or assets.
- Import validates schema, references, paths and checksums before writing business rows.
- Source files are backed up before cutover; backups are timestamped and checksummed.
- Cutover is explicit. Until success, existing JSON remains runtime authority.
- A failed import rolls back database rows from its atomic unit and leaves source data untouched.
- Unknown fields are preserved in a versioned audit payload or reported; they are never silently discarded.
- Re-running the same completed source checksum is a no-op/report, not a duplicate import.

### Rollback and compatibility

- Database backup restore is the rollback mechanism for data migrations; Alembic downgrade is not assumed safe for lossy revisions.
- At least the immediately previous application schema revision remains upgrade-tested.
- No release may delete legacy source files in S01. Removal requires a later user-approved retention task.

## 8. Repository and API boundary

- SQLAlchemy models live in a dedicated persistence package and are not exported as API schemas.
- Repositories accept/return domain DTOs or explicit scalar records, not long-lived sessions.
- Existing APIs keep their response contract during S01 unless a separate approved task changes it.
- Dual writes to JSON and SQLite are forbidden unless a later task defines failure ordering, reconciliation and tests. S01 uses preview/import/cutover instead.

## 9. Reserved decisions for later tasks

- S01-T02 chooses package names, engine configuration and concrete Alembic bootstrap.
- S01-T03 defines managed-root layout, atomic file helper and Trash recovery UX.
- S01-T04 defines legacy discovery and preview report schemas.
- S01-T05 defines transactional import batching, backup format and cutover command.
- S02 defines Job, JobStep, retries, leases, cancellation and restart reconciliation.
- Character Library, ObjectRole, QC and render-version tables are added by their owning epics, following this contract.

## 10. Acceptance invariants

Future implementation must prove:

1. Foreign keys are active and invalid cross-workspace references fail.
2. A project can reference only correctly typed channels.
3. Scene/frame/time constraints reject invalid ranges.
4. Managed artifact paths cannot escape the configured root.
5. Archive does not hard-delete referenced rows or artifact bytes.
6. Migration from the previous supported revision preserves row identity and required data.
7. Legacy preview is read-only and repeated import is idempotent.
8. The full seven-gate quality baseline remains PASS for every S01 task.
