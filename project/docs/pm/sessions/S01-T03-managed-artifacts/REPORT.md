# S01-T03 - Implementation Report

**Status:** SUBMITTED
**Started:** 2026-08-03 17:00 +07:00
**Submitted:** 2026-08-03 17:12 +07:00
**Resubmitted (after PM CHANGES_REQUESTED):** 2026-08-03 17:22 +07:00

## Outcome delivered

One containment-safe filesystem contract for all managed media writes and
removals — a pure helper layer, independent of database transactions and
existing runtime services:

- `app/persistence/artifacts.py` — `ManagedRoot` + pure helpers:
  - Path contract (AC1): configured root resolved once; only normalized
    relative paths accepted; rejects absolute, drive/UNC, empty, `.`, `..`
    traversal, symlink/junction escapes and the protected database file.
    `normalize_managed_path`, `resolve`, `relative_path_of`, `is_within`.
  - Atomic write (AC2/AC3): same-directory unique staging file, flush +
    `os.fsync`, `os.replace` publish, optional SHA-256 verification where an
    expected-checksum mismatch aborts before publish, staging cleanup on any
    failure; returns `(sha256, size_bytes)` evidence.
  - Trash (AC4): collision-safe entry/name under the configured Trash root,
    recovery manifest (original relative path / sha256 / size / UTC time),
    manifest-write rollback, containment enforced on both sides.
  - Restore (AC5): validates manifest + trashed-file + original-path
    containment, refuses overwrite, optional checksum verification; returns
    explicit `RestoreResult`.
- `app/persistence/__init__.py` — exports the new API (no engine/ORM imports
  added; the module stays database-free).
- `docs/architecture/MANAGED_ARTIFACT_CONTRACT.md` — the task's contract doc.
- `tests/test_managed_artifacts.py` — 42 targeted tests using only pytest
  `tmp_path`.

No database/schema/migration change; no cleanup/project/workflow/API/
frontend change; no production output/projects/presets touched; no commits.

## PM review corrections (CHANGES_REQUESTED round)

| # | Correction | Resolution |
|---|---|---|
| 1 | `restore()` must enforce strict Trash containment: manifest + trashed file strictly under the configured Trash root, not merely managed root | `restore()` now resolves the Trash root (`_trash_root()`) and requires both the manifest path and the trashed file to resolve strictly under it; the trashed file must live in the same Trash entry as the manifest (`trashed file must live in the manifest entry`). Error messages updated to name the Trash root |
| 2 | Regression tests: valid manifest+payload inside managed root but outside `.trash` must be rejected; manifest under `.trash` whose payload resolves outside Trash root must be rejected | Added `test_restore_rejects_manifest_inside_root_but_outside_trash` (valid manifest + payload at `not-trash/`, restore rejected, payload untouched) and `test_restore_rejects_trashed_file_outside_trash_root` (manifest under `.trash`, payload escapes the Trash root/entry) |
| 3 | Validation must not create the Trash directory as a side effect | Added `test_restore_validation_does_not_create_trash_dir`; `_trash_root()` resolves the configured Trash root without materializing it, so rejected-path validation leaves `.trash` absent |
| 4 | Re-run targeted tests, Ruff, mypy, full seven-gate baseline and diff check; append LOG, update REPORT, resubmit | All re-run green (see Tests and validation); LOG appended; REPORT resubmitted |

Existing recovery/overwrite/checksum behavior is unchanged: `test_trash_is_recoverable_via_restore`, `test_restore_refuses_overwrite`, `test_restore_checksum_mismatch_rejected`, `test_restore_without_checksum_verification` all still pass.

## Acceptance criteria evidence

| AC | Status | Evidence |
|---|---|---|
| AC1 Valid paths resolve within the managed root; all path escape forms rejected | PASS | `test_valid_relative_paths_resolve`, `test_empty_path_rejected`, `test_dot_path_rejected`, `test_absolute_path_rejected`, `test_drive_path_rejected`, `test_unc_path_rejected`, `test_parent_traversal_rejected`, `test_symlink_escape_rejected`, `test_database_file_rejected`, `test_sibling_root_is_not_inside` (10 tests) |
| AC2 Atomic bytes/stream writes expose only final or prior content and clean staging files after failure | PASS | `test_atomic_write_bytes_publishes_content`, `test_atomic_write_no_staging_leftovers`, `test_atomic_write_overwrites_prior_content`, `test_atomic_write_creates_parent_dirs`, `test_atomic_write_stream_publishes`, `test_atomic_write_failure_cleans_staging`, `test_atomic_write_stream_failure_cleans_staging` (7 tests) |
| AC3 Hash/size evidence returned and optional expected checksum mismatch cannot publish | PASS | `test_atomic_write_returns_hash_and_size`, `test_atomic_write_encoding_parameter`, `test_expected_checksum_mismatch_cannot_publish`, `test_expected_checksum_match_publishes`, `test_checksum_mismatch_preserves_prior_content` (5 tests) |
| AC4 Trash move is recoverable, collision-safe, manifest-backed and cannot cross managed boundaries | PASS | `test_trash_moves_file_into_trash_with_manifest`, `test_trash_is_recoverable_via_restore`, `test_trash_names_are_collision_safe`, `test_trash_missing_file_fails`, `test_trash_directory_fails`, `test_trash_cannot_cross_managed_boundary`, `test_trash_rejects_database_file`, `test_manifest_records_original_path_checksum_time`, `test_trash_manifest_round_trip_after_rename` (9 tests) |
| AC5 Restore refuses overwrite and validates both original and Trash containment | PASS | `test_restore_refuses_overwrite`, `test_restore_checksum_mismatch_rejected`, `test_restore_without_checksum_verification`, `test_restore_rejects_manifest_outside_root`, `test_restore_rejects_escaped_original_path`, `test_restore_rejects_trashed_file_escape`, `test_restore_malformed_manifest_rejected` (7 tests) |
| AC6 Targeted tests and all seven quality gates PASS | PASS | 42/42 targeted (twice); `ruff` clean; `mypy` clean (46 files); full suite 227 passed, 8 skipped; 220 passed, 8 skipped, 7 deselected; quality baseline OVERALL: PASS (all 7 gates, exit 0); `git diff --check` exit 0 |

## Files changed

- `app/persistence/artifacts.py` (new)
- `app/persistence/__init__.py` (exports added)
- `tests/test_managed_artifacts.py` (new; 42 tests)
- `docs/architecture/MANAGED_ARTIFACT_CONTRACT.md` (new)
- `docs/pm/sessions/S01-T03-managed-artifacts/LOG.md` (appended)
- `docs/pm/sessions/S01-T03-managed-artifacts/REPORT.md` (this file)

## Tests and validation

| Command | Result | Notes |
|---|---|---|
| `python -m pytest -q tests/test_managed_artifacts.py` | PASS | 42 passed (run twice) |
| `python -m pytest -q tests/test_managed_artifacts.py tests/test_persistence_bootstrap.py` | PASS | 60 passed |
| `python -m ruff check app tests` | PASS | All checks passed |
| `python -m mypy app` | PASS | Success: no issues found in 46 source files |
| `python -m pytest -q -m "not gpu and not sam2 and not integration" --cache-clear` | PASS | 220 passed, 8 skipped, 7 deselected |
| `python -m pytest -q --cache-clear` | PASS | 227 passed, 8 skipped, 12 warnings |
| `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1` | PASS | OVERALL: PASS, all 7 gates, exit 0 (run id 20260803-170854) |
| `git diff --check` | PASS | exit 0 (only documented CRLF warnings on Windows) |
| `certutil -hashfile channels.json SHA256` | UNCHANGED | dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555 (identical before/after; user diff preserved) |

## Architecture/domain impact

- Additive filesystem layer only: no imports of engine/ORM/models/repositories/
  services anywhere in `app/persistence/artifacts.py`; helpers return explicit
  results and never commit database sessions or mutate `Artifact` rows.
- No schema, migration, API, cleanup-service, workflow or frontend change.
- Production directories verified untouched (newest project mtime 11:40,
  presets 02:13 — all before this session).

## Known limitations/risks

- Junction/symlink escape on Windows is guarded by the same `resolve()`
  containment check; the symlink test skips when the platform cannot create
  symlinks (Git Bash on Windows can). Trash purge/expiry policy and wiring of
  atomic write + row-state (`staging`→`ready`) into a service are later tasks.
- `ManagedRoot` resolves its root at construction; callers must pass the
  resolved root if the working directory changes later.

## Recommended PM decision

`PENDING` — awaiting PM review.
