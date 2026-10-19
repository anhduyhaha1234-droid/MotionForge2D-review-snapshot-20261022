# Durable Channel API (S03-T01)

**Status:** Implemented for S03-T01 review (correction round 1)
**Contract:** `docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md` §4 (channel)
**Persistence:** `app/persistence/channels.py` (SQLite via the S01 `channel`
table + S03 migration `1c9f2a4b7d8e`)
**Routes:** `app/api/routes/channels.py` (prefix `/api/channels`)
**Scope:** Durable source/production Channel CRUD + archive.  No JSON
dual-write, no hard delete, `channels.json` untouched.

## 1. Purpose

Users can create, list, read, update and archive source/production Channels
through one durable API with actionable validation and no JSON dual-write.
The legacy `channels.json` workspace store (dashboard compatibility,
`/api/projects/channels`) remains byte-identical and untouched; the durable
Channel rows live only in SQLite.

## 2. Endpoints

| Method | Path | Purpose | Status codes |
|---|---|---|---|
| GET | `/api/channels` | List (workspace-scoped; `role`, `active_only` filters) | 200 |
| POST | `/api/channels` | Create active channel (role `source`\|`production`) | 201, 409, 422 |
| GET | `/api/channels/{channel_id}` | Read one within workspace (archived readable) | 200, 404 |
| PATCH | `/api/channels/{channel_id}` | Update with atomic revision CAS | 200, 404, 409, 422 |
| POST | `/api/channels/{channel_id}/archive` | Archive with atomic revision CAS (idempotent) | 200, 404, 409, 422 |
| GET | `/api/channels/roles` | Exact approved role set | 200 |
| GET | `/api/channels/statuses` | Exact approved status set | 200 |

Query params: `workspace_id` (default `default`), `role`
(`source`|`production`), `active_only` (default `true`).

**No hard-delete endpoint exists** — archive is the only removal path
(contract §4/§5, AC1/AC5).

## 3. Semantics

### Roles / statuses (AC2)
- `role` is exactly `source` or `production` (schema CHECK + DTO enum).
- `status` is exactly `active` or `archived` (schema CHECK + DTO enum).

### Names (AC3) — active-only, case-insensitive (PM review finding 1)
- Names are normalized (trimmed) on create/update and kept in display case.
- Active names are unique case-insensitively per `(workspace_id, role)`.
  **Migration `1c9f2a4b7d8e`** replaced the S01 unconditional
  `UNIQUE(workspace_id, role, name)` with a partial unique index
  `uq_channel_active_workspace_role_name ON channel (workspace_id, role,
  lower(name)) WHERE status = 'active'`.  The migration is atomic
  (batch copy-and-move with FK references preserved — verified by
  upgrade-from-S02 tests including a referenced archived channel) and
  non-reversible (backup restore per contract §7).
- Archive-then-recreate is now valid: an archived channel's name is
  immediately reusable (covered by `test_archived_name_can_be_reused`).
- Conflicts return **409** with an actionable message; the repository
  pre-check plus the partial unique index backstop make racing
  case-variant creates deterministic (one 201, one 409 — covered by
  `test_concurrent_case_variant_create_one_wins`).

### Optimistic concurrency (AC4) — atomic CAS (PM review finding 2)
- `PATCH` executes a conditional database UPDATE with
  `WHERE id = :id AND workspace_id = :ws AND revision = :expected` and
  inspects the affected row count:
  - 1 row → accepted; `revision` bumped exactly once by the SQL;
  - 0 rows + row exists in workspace → 409 with the current revision;
  - 0 rows + missing/other-workspace → 404.
- `POST .../archive` requires a body `{"revision": <expected>}` and uses
  the same atomic CAS (PM review finding 3):
  - active + matching revision → archived (one bump);
  - already archived → idempotent 200 returning the current row (no bump,
    even with a stale revision);
  - active + stale revision → 409;
  - **concurrent archive race** (PM review round 2 finding 4 / round 3
    finding 1): a caller that loses the CAS to another archiver re-reads
    the row with a FRESH database SELECT (bypassing the identity map —
    `session.get` would return the caller's stale in-session object) and
    returns the now-archived row idempotently (200, no bump) — never a
    spurious 409;
  - unknown/other-workspace → 404.
- Rename races (PM review round 3 finding 2): a concurrent
  two-channel rename-to-one-free-name loses via the active-name partial
  unique index at UPDATE time; the repository maps that UNIQUE violation
  to `NameConflictError` (HTTP 409) without masking unrelated integrity
  errors.
- `test_two_session_revision_race_exactly_one_wins` proves exactly one
  writer wins with a real two-thread race;
  `test_concurrent_archive_race_both_idempotent` proves concurrent
  archives both return 200 with exactly one revision bump;
  `test_archive_interleaving_both_callers_read_active_then_cas` proves
  the fresh-read idempotent path with a deterministic interleaving;
  `test_concurrent_rename_to_one_free_name_exactly_one_wins` proves the
  UPDATE-time index backstop (instrumented pre-check sees no blocker).

### Workspace ownership (PM review finding 6)
- `workspace_id` is threaded through GET/PATCH/archive and included in
  every repository predicate.  A channel id from another workspace is a
  404 and can never be read or mutated
  (`test_cross_workspace_channel_is_404`).
- `POST /api/channels` bootstraps the workspace row and creates the
  channel in **ONE transaction** (`INSERT ... ON CONFLICT DO NOTHING` for
  the workspace — race-safe on first use, PM review finding 7).

### Archive (AC5)
- Archive sets `status=archived` + `archived_at` (UTC now); references,
  timestamps, metadata and revision history are preserved.
- Archived channels are excluded by the default `active_only=true` list
  and remain readable via GET and filterable with `active_only=false`.

## 4. DTO / ORM boundary (AC6)

- API responses are Pydantic DTOs (`ChannelData`); repository returns
  plain dataclass read records (`ChannelRecord`).  No ORM instance, no
  `_sa_instance_state`, no absolute paths ever cross the API boundary.
- Response fields: `channel_id`, `workspace_id`, `name`, `role`,
  `description`, `color`, `avatar_artifact_id`, `target_language`,
  `default_output_profile`, `status`, `archived_at`, `created_at`,
  `updated_at`, `revision`.
- Timestamps: required timestamps (`created_at`, `updated_at`) serialize
  as ISO-8601 UTC-aware strings; the optional `archived_at` serializes as
  JSON **null** when unset (PM review finding 8 — never `""`).
- **PATCH null semantics** (PM review round 1 finding 5 + round 2 finding
  3): an omitted field is unchanged; an explicit JSON `null` is only a
  "clear" for truly nullable metadata (`color`, `target_language`,
  `default_output_profile`, `avatar_artifact_id`) — implemented via
  Pydantic `model_fields_set` + an `UNSET` sentinel.  `name: null` is a
  **422** validation error (name is required); `description: null` is
  normalized to `""` (the NOT NULL column default), never bound as NULL.
- **Metadata boundary** (PM review round 1 finding 9 + round 2 finding 2):
  `avatar_artifact_id` is fully supported (set on create, updated,
  cleared).  References are validated BEFORE any repository binding:
  missing / cross-workspace / non-image artifacts raise
  `ArtifactReferenceError` mapped to **HTTP 422** with a precise detail
  (``avatar_artifact_id 'X' does not reference an existing artifact`` /
  ``belongs to a different workspace`` / ``is not an image artifact``).
  No raw `IntegrityError` escapes the API.
- Legacy channel response compatibility: the legacy
  `/api/projects/channels` endpoints are preserved byte-for-byte; no
  S03-T01 edits exist in `app/api/routes/projects.py` (PM review finding
  4 — verified via `git diff`).

## 5. Transactions

- `ChannelRepository` never commits on its own (contract §6); the
  `ChannelService` opens exactly **one** short session per request
  operation — every request is transaction-bounded (PM review finding 7).
- The workspace row is bootstrapped in the same transaction as the first
  channel (atomic, race-safe).

## 6. Migration status (AC7)

- **Migration `1c9f2a4b7d8e`** (S02 head `23b308b1fd0b` → S03 head):
  active-only case-insensitive unique index (see §3 Names).
- Upgrade-from-S02 preservation evidence in
  `tests/test_persistence_bootstrap.py`:
  1. `test_upgrade_from_s02_preserves_all_channel_rows` — active/archived/
     legacy_id rows survive byte-identically.
  2. `test_upgrade_from_s02_preserves_referencing_project_rows` — project
     FK references survive.
  3. `test_upgrade_from_s02_preserves_referenced_archived_channel` — an
     archived channel referenced by a project survives the batch table
     rebuild.
  4. `test_s03_head_reuses_s01_channel_schema_no_new_tables` — head table
     set identical to S02 (no schema drift).
  5. `test_s03_head_index_is_active_only_and_case_insensitive` — the new
     index allows archive-then-recreate and rejects case-variant actives.
