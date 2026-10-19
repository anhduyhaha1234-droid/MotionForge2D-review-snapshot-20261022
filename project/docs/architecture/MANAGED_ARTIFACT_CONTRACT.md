# Managed Artifact Contract V1

**Status:** Implemented by S01-T03
**Epic:** E01 — Durable Domain, Persistence and Jobs
**Sprint:** S01 — Persistence foundation
**Owner module:** `app/persistence/artifacts.py`
**Companion:** `docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md` (Artifact aggregate)

## 1. Purpose

One containment-safe filesystem contract for every managed media write and
removal. Incomplete writes never appear as ready artifacts, and removal is
recoverable through Trash. The helpers are **pure filesystem helpers**: they
return explicit results and never commit database sessions or mutate
`Artifact` rows. Persisting the returned evidence is the caller's job.

## 2. Non-goals (this task)

- No database/ORM/engine imports, no repository methods, no `Artifact` row
  mutation, no runtime service wiring.
- No schema/migration changes, no API/frontend/cleanup behavior changes.
- No production file access: helpers are exercised only through pytest
  `tmp_path` directories.

## 3. Managed root

- `ManagedRoot(root, trash_dirname=".trash", database_path=None)` resolves the
  configured root **once** at construction (`Path.resolve()`).
- Every operation re-validates containment against the resolved root, so a
  path cannot escape even if the root or the target moves between calls.
- `database_path` (optional) protects the SQLite file that owns `Artifact`
  rows: it can never be written, trashed, or resolved as a managed artifact.

## 4. Path contract (AC1)

Only normalized relative paths are accepted. Rejected forms:

- Empty path, `.`/`./` (must name a file).
- Absolute paths (`/…`, `C:/…`, `\\…`).
- Drive paths (`C:`, `D:` prefix) and UNC paths (`//server/share`, `\\server\share`).
- Parent traversal: any `..` component (`../x`, `a/../../x`).
- Symlink/junction escapes: the resolved candidate must be inside the
  resolved root.
- The configured database file.

Normalization: `\` → `/`, redundant `.` segments removed, then validated as a
clean POSIX relative path. `resolve()` returns the absolute inside-root path;
`relative_path_of()` returns the normalized relative path of an absolute path;
`is_within(path, root)` is the shared boundary predicate (sibling
`root_evil` is never inside `root`).

## 5. Atomic write (AC2)

`atomic_write_bytes(rel, data, *, fsync=True, verify_sha256=True, expected_sha256=None, encoding=None)`
and `atomic_write_stream(rel, stream, ...)`:

1. Validate + resolve the target inside root; create parent directories.
2. Create a **same-directory unique staging file** (`.{name}.{uuid}.staging`)
   with `open("xb")`; write bytes/chunks.
3. Flush + `fsync` (unless `fsync=False`).
4. Optionally hash the staged file; when `expected_sha256` is given, a
   mismatch **aborts before publish** (AC3).
5. Publish with `os.replace` (atomic same-filesystem rename).
6. On any failure, unlink the staging file and re-raise; the prior content
   (if any) stays untouched.

Returns `(sha256, size_bytes)` of the published content. A reader can only
ever observe the final or the prior content — never a partial file.

## 6. Trash (AC4)

`trash(rel)`:

1. Validate source containment (and database-file exclusion); require a
   regular file that exists.
2. Create `{root}/.trash/{original_rel}-{random}/` (collision-safe random
   suffix) and move the file with `os.replace` to a random-named file inside
   that entry — the move never crosses managed boundaries.
3. Write `manifest.json` next to the trashed file recording
   `original_relative_path`, `sha256`, `size_bytes`, `trashed_at` (UTC ISO)
   and `trashed_name`.
4. If the manifest write fails, the move is rolled back (file restored,
   entry removed).

Returns `TrashMoveResult(trashed_relative_path, manifest_relative_path,
manifest)`.

## 7. Restore (AC5)

`restore(manifest_relative_path, *, verify_checksum=True)`:

- Validates **strict Trash containment**: the **manifest path** and the
  **trashed file** must both resolve strictly inside the configured Trash
  root (`.trash`), and the trashed file must live in the same Trash entry as
  the manifest — a manifest or payload merely inside the managed root but
  outside `.trash` is rejected.
- Validation itself never creates the Trash directory (no filesystem side
  effects on rejected paths).
- Validates the **original relative path** from the manifest and resolves it
  inside root.
- Refuses to overwrite an existing destination.
- Rejects when the trashed bytes no longer match the manifest checksum
  (unless `verify_checksum=False`).
- Moves the trashed file back to the original path, then removes the manifest
  and its (now empty) entry directory.

Returns `RestoreResult(restored_relative_path, sha256, size_bytes)`.

## 8. Result/error model

- `ManagedPathError(ValueError)` — invalid or non-contained path.
- `ArtifactWriteError(OSError)` — write/trash/restore operational failure.
- Success paths return dataclasses or `(sha256, size_bytes)` tuples — never
  `None`-only signals.
- No helper opens a database session or mutates an `Artifact` row.

## 9. Testing and isolation

`tests/test_managed_artifacts.py` covers AC1–AC5 using only pytest
`tmp_path`. Production output/projects/presets are never touched. Windows
symlink semantics are exercised with a skip guard when the platform cannot
create symlinks; junction escapes use the same `resolve()` containment check.

## 10. Acceptance invariants (from the domain contract)

1. Managed artifact paths cannot escape the configured root — enforced by
   every helper.
2. A database row becomes `ready` only after an atomic filesystem write
   succeeds — this task supplies the atomic write; row-state wiring is a
   later service task.
3. Hard delete is limited to managed Trash with recovery manifests — this
   task supplies Trash; purge/expiry policy is a later task.
