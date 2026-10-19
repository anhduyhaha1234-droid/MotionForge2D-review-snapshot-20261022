# S03-T03 - Durable Video Item lifecycle and ordering

**Status:** APPROVED
**Epic:** E02 - Production Management and Product Shell
**Sprint:** S03 - Production management API
**Gate:** G2 - Production shell
**Depends on:** S03-T02 (APPROVED)

## User outcome

Users can add, inspect, update, archive, and atomically reorder durable Video
Items inside a durable Project without touching legacy filesystem workflows.

## Required reading

1. `docs/pm/SESSION_PROTOCOL.md`
2. `docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md`
3. `docs/architecture/PROJECT_API.md`
4. `docs/PRODUCT_REQUIREMENTS_V2.md`
5. S03-T01 and S03-T02 task/report/review
6. Current persistence models, repositories, route registration, schemas, and
   bootstrap tests

## Route contract

Use only the isolated namespace
`/api/v2/projects/{project_id:uuid}/videos`:

- list/create, exact status discovery, read, PATCH, explicit archive;
- one atomic full-list reorder endpoint;
- no DELETE route, no legacy route changes, no JSON/filesystem/media writes.

## Domain contract

- Every Video Item belongs to exactly one Project and is workspace-scoped via
  that Project.
- Exact statuses: `imported`, `analyzing`, `objects_ready`,
  `mapping_required`, `demo_required`, `demo_approved`, `applying_reskin`,
  `needs_review`, `ready_to_export`, `rendering`, `completed`, `failed`,
  `archived`.
- Title is trimmed, non-empty, maximum 240 characters.
- Position is non-negative and unique within a Project. Create appends at the
  end. Active list is ordered by position and excludes archived by default.
  Logical active order is gap-tolerant after archive: archive preserves
  positions and reorder maps the requested active order onto the sorted
  existing active position slots, so a reorder never collides with an
  archived row and never rewrites archived positions.
- Generic PATCH must not enter or leave archived. Archive is idempotent and
  preserves all metadata and relationships.
- New source Channel assignment requires active, same workspace, `source`
  role at the atomic write boundary. Existing references survive later archive.
- Archived Projects remain readable but reject new Video Items, reorder, and
  active workflow mutation until a restore policy exists.
- Source artifact/probe metadata are read-only in this task; S05 owns import
  and media probing.

## Concurrency and ordering

- PATCH/archive use revision CAS and return stable 409 on stale writes.
- Reorder request carries the expected Project revision and the complete set
  of active Video Item IDs exactly once. Missing/extra/duplicate/cross-project
  IDs fail without partial writes.
- Reorder is one transaction, bumps Project revision once, and bumps only
  Video Items whose positions change. Use collision-safe two-phase positions
  for SQLite uniqueness.
- Concurrent create append cannot leak raw `IntegrityError`; serialize/retry
  deterministically.
- Channel validation plus assignment must use the S03-T02 atomic writer policy.

## Acceptance criteria

1. Durable CRUD/list/read/archive/reorder works only under the v2 namespace.
2. DTO/status/title/position contract is exact and leaks no ORM/path objects.
3. Append/reorder maintain a stable logical active ordering: every
   position is a unique non-negative integer within its Project, append
   goes after the current max, reorder maps the requested active order
   onto the existing active position slots (preserving archived
   positions and introducing no new gaps), and the active list is
   ordered by position then creation time.
4. PATCH/archive/reorder CAS is atomic; stale/conflicting requests are 409.
5. Archive is idempotent, timestamp-safe, and never cascades/hard-deletes.
6. Workspace, Project, Channel, and cross-project ownership return safe 404/422.
7. Archived Project and archived Video Item invariants are enforced.
8. Migration is added only if the current S01 schema cannot enforce the
   approved contract; upgrade preserves current-head data.
9. Legacy routes/imports/filesystem behavior remain byte-for-byte unaffected.
10. Focused, combined, race, upgrade, Ruff, mypy, diff, and full 7/7 baseline
    all pass.

## Ownership and exclusions

Likely owned files: new Video Item repository/router/tests/API doc plus minimal
registration/schema/bootstrap changes. Do not modify `channels.json`. Do not
commit. Leave implementation `SUBMITTED` for PM review.
