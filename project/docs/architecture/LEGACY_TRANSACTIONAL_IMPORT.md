# Legacy Transactional Import Contract V1

**Status:** Implemented by S01-T05
**Epic:** E01 — Durable Domain, Persistence and Jobs
**Sprint:** S01 — Persistence foundation
**Owner module:** `app/persistence/legacy_import.py`
**Companions:** `docs/architecture/LEGACY_IMPORT_PREVIEW.md` (preview input),
`docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md` (migration policy §7,
transaction contract §6)

## 1. Purpose

The explicitly approved, blocker-free legacy preview (S01-T04) can be
backed up and imported **once** into an initialized SQLite database.
Failure rolls back database rows; source data remains untouched and
recovery evidence (an immutable, manifest-backed backup) is retained.
No runtime route is cut over: this is an explicit library API only.

## 2. Non-goals (this task)

- No API/workflow/service/frontend cutover, no dual writes.
- No schema/migration revision changes, no dependency changes.
- No job persistence, no artifact purge or deletion.
- No production-file access: the importer is exercised only against
  explicit fixture roots, temporary databases and temporary backup roots.

## 3. Input contract

`LegacyImporter(preview, session_factory, workspace_id, backup_root, token)`

- `preview`: explicit `LegacyPreview` built by `LegacyPreviewer` (S01-T04).
- `session_factory`: initialized SQLAlchemy session factory bound to a
  schema-upgraded SQLite database (S01-T02 bootstrap).
- `workspace_id`: explicit workspace ID; reused when present, created
  otherwise.
- `backup_root`: managed root for immutable backup directories
  (S01-T03 `ManagedRoot`).
- `token`: confirmation token; must equal `confirmation_token(preview)`.

`confirmation_token(preview)` is a deterministic SHA-256 over the preview's
serialized content (channels, projects, source checksums before/after,
referenced files).  Any preview change yields a different token.

## 4. Preflight refusals (AC3)

All refusals happen **before any backup write and before any DB write**:

- Preview blockers (from S01-T04 issue model).
- Changed source checksum/mtime (stale preview) — verified live, before
  backup.
- Unsafe references (`PROJECTS_ROOT_UNSAFE`, `PROJECT_PATH_UNSAFE`,
  `PROJECT_SOURCE_ABSOLUTE`, `PROJECT_REFERENCE_UNSAFE`) — never copied,
  never followed.
- Wrong confirmation token.
- Unsupported schema version (only `2.0.0` is accepted).

Refusals raise `LegacyImportRefused` with stable `reasons` and
`reason_codes` (`BLOCKERS`, `NO_SOURCES`, `UNSAFE_REFERENCES`,
`UNSUPPORTED_SCHEMA`, `WRONG_TOKEN`, `SOURCE_CHANGED`).

## 5. Backup (AC1)

Before any DB business row:

1. Every inventoried source JSON (channels + project.json) and every safe
   referenced file (`inside_root and exists` from the preview) is copied
   into a fresh immutable directory `<backup_root>/backups/<backup_id>/`.
2. `<backup_id>` is collision-safe (`timestamp + random hex`); the
   directory is created with `mkdir` (fails if it already exists).
3. Each file is written with an atomic same-directory staging + replace
   (S01-T03 `atomic_write_bytes`, `expected_sha256` gating).
4. `manifest.json` is written last, atomically, recording for every entry:
   `source_locator`, `sha256`, `size_bytes`, `backup_relative_path`.
5. On any failure the partial directory is removed — an incomplete backup
   is never observable.

Layout:

```text
<backup_root>/backups/<backup_id>/
    source/<legacy-relative path>   # source JSON files
    files/<index>-<hex>             # referenced media files
    manifest.json
```

## 6. Transaction (AC2)

- Source checksums are revalidated immediately before the transaction:
  - live sha256 + mtime must still match the preview record, AND
  - the backed-up file's hash must equal the preview checksum (hard proof
    the immutable backup holds the approved generation).
  A changed/missing source or an inconsistent backup aborts before any DB
  write (`SOURCE_CHANGED` / `BACKUP_INCONSISTENT`).
- **Imported data never comes from the live legacy tree after the final
  revalidation.**  Project metadata and scene payloads are read exclusively
  from the verified immutable backup (`_backup_payload` /
  `_backup_scenes`), so a concurrent edit between revalidation and the
  transaction cannot leak unapproved bytes into committed rows.
- One SQLAlchemy transaction:
  - reuse/create `workspace` (explicit ID);
  - insert `channel` rows (role `source`, legacy ids, deterministic
    proposed ids from the preview — never invented replacement ids);
  - insert `project` rows (legacy id, deterministic proposed id, mapped
    status, source channel FK);
  - insert one `video_item` per project (legacy id = project legacy id,
    deterministic public id, probe metadata from the backed-up
    project.json);
  - insert valid `scene` rows (legacy scene ids, frames, times) from the
    backed-up project.json payloads;
  - insert `artifact` rows (`ready`, sha256/size from the backup manifest)
    plus `artifact_owner` links (`source` purpose) for every project and
    its video item;
  - insert one `legacy_import` audit row (`status=completed`,
    `summary_json` with counts + backup id).
- Any row/import failure rolls back the whole transaction; the backup
  remains available and source bytes/mtime remain unchanged.

## 7. Idempotency (AC5)

- The idempotency boundary is `(source_kind, source_sha256)` on a
  `completed` `legacy_import` row (domain contract §4).
- `source_sha256` is the SHA-256 over the preview's per-source checksums.
- A repeated completed import is a read-only no-op: no duplicate rows and
  **no second backup**; the result references the original backup.

## 8. Result model

- `ImportResult`: `backup_id`, `backup_manifest_path`, `legacy_import_id`,
  `workspace_id`, `channel_ids`, `project_ids`, `video_item_ids`,
  `scene_ids`, `artifact_ids`, `owner_count`, `skipped_reason`
  (`idempotent_skipped` when set).
- `LegacyImportRefused(LegacyImportError)`: preflight refusal with
  `reasons`/`reason_codes`.
- `BackupManifest` / `BackupEntry`: serialized audit evidence.

## 9. Testing and isolation

`tests/test_transactional_legacy_import.py` covers AC1–AC6 using only
pytest `tmp_path` databases (Alembic-upgraded), `tmp_path` backup roots and
a private copy of the synthetic fixture
`tests/fixtures/legacy_import/importable/`.  Repo-root production data is
never touched.

## 10. Acceptance invariants (from the domain contract)

1. Legacy preview is read-only and repeated import is idempotent.
2. Source files are backed up before cutover; backups are timestamped and
   checksummed.
3. A failed import rolls back database rows from its atomic unit and
   leaves source data untouched.
4. Re-running the same completed source checksum is a no-op, not a
   duplicate import.
5. No release may delete legacy source files in S01.
