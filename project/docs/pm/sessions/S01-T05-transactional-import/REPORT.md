# S01-T05 - Implementation Report

**Status:** SUBMITTED
**Started:** 2026-08-03 17:48 +07:00
**Submitted:** 2026-08-03 18:24 +07:00
**Resubmitted (PM CHANGES_REQUESTED round 1):** 2026-08-03 18:45 +07:00

## Outcome delivered

A transactional, backup-first legacy JSON importer (explicit library API —
no runtime cutover) that turns an approved S01-T04 `LegacyPreview` into one
SQLite transaction, with immutable manifest-backed backup, preflight
refusals, rollback on failure and idempotent re-import:

- `app/persistence/legacy_import.py` — `LegacyImporter(preview,
  session_factory, workspace_id, backup_root, token)`:
  - **Preflight (before any backup and any DB write):** refuses previews
    with blockers, changed source checksum/mtime (verified live before
    backup), unsafe references (never copied/followed), wrong confirmation
    token, or unsupported schema version — `LegacyImportRefused` with
    stable `reasons` + `reason_codes` (`BLOCKERS`, `NO_SOURCES`,
    `UNSAFE_REFERENCES`, `UNSUPPORTED_SCHEMA`, `WRONG_TOKEN`,
    `SOURCE_CHANGED`).
  - **Backup before business rows:** every inventoried source JSON +
    every safe referenced file is copied into a fresh collision-safe
    immutable directory `<backup_root>/backups/<backup_id>/` using S01-T03
    atomic writes (`expected_sha256` gated); `manifest.json` (source
    locator, sha256, size, backup relative path) written last, atomically,
    then directory fsync; partial backups are removed on failure.
  - **Revalidation immediately before the transaction** (sha256 + mtime of
    every source).
  - **One transaction** (`with session.begin()`): reuse/create workspace
    (explicit id), channels (role `source`, legacy ids preserved),
    projects (legacy id + deterministic proposed id, mapped status, source
    channel FK), one `video_item` per project (legacy id = project legacy
    id, deterministic public id, probe metadata from the revalidated
    project.json), valid `scene` rows, `artifact` rows (`ready`,
    sha256/size from manifest) + `artifact_owner` links (purpose
    `source`) for project and video item, and one `legacy_import` audit
    row (`status=completed`, summary with counts + backup id).
  - **Idempotent:** a completed `(source_kind, source_sha256)` is probed
    before backup — repeated import is a read-only no-op referencing the
    original backup (no duplicate rows, no second backup).
  - **Rollback:** any row failure rolls back the whole transaction; the
    backup remains valid; source bytes/mtime remain unchanged.
  - `confirmation_token(preview)` — deterministic SHA-256 over the
    preview's serialized content; wrong token is refused.
- `app/persistence/__init__.py` — exports the new API.
- `docs/architecture/LEGACY_TRANSACTIONAL_IMPORT.md` — contract doc.
- `tests/fixtures/legacy_import/importable/` — synthetic fixture
  (channels.json + projects/proj_001/project.json + video.mp4 +
  replacement.png; schema 2.0.0, 2 scenes, 2 objects).
- `tests/test_transactional_legacy_import.py` — 16 targeted tests.

No runtime API/workflow/service/frontend change, no schema/migration
change, no dependency change, no commits; `channels.json` user diff
preserved byte-identical.

## PM review corrections (CHANGES_REQUESTED round 1)

| # | Correction | Resolution |
|---|---|---|
| 1 | TOCTOU: `_revalidate_before_transaction()` checks live sources, but `_live_project_data()` reopens mutable `project.json` inside the transaction; imported data must come from the verified immutable backup | Removed `_live_project_data`/`_live_scenes` entirely. `_import_transaction` now reads project metadata/scenes exclusively from the backup via `_backup_payload(manifest, locator)` / `_backup_scenes(manifest, project)` (backup file located through `BackupManifest.entries[].backup_relative_path`). `_revalidate_before_transaction(manifest)` additionally hard-verifies the backed-up file's hash equals the preview checksum (`BACKUP_INCONSISTENT` refusal if not). After the final revalidation, no code path opens the live legacy tree for import data |
| 2 | Add deterministic regression test proving committed rows match backup (or safe refusal with zero writes) | `test_live_project_json_mutation_after_revalidation_does_not_leak_into_rows`: real revalidation runs, then the live project.json is mutated inside the revalidation seam (the exact TOCTOU window); committed rows still show backup content (duration 10000, 1920x1080, 30fps, scenes 0/1 @ 0-149/150-299). `test_live_project_json_mutation_is_refused_with_zero_writes_when_revalidation_runs`: tampered live file → `SOURCE_CHANGED` refusal with all 8 tables at zero rows |
| 3 | Update architecture/report/limitations so they no longer claim the known race | `docs/architecture/LEGACY_TRANSACTIONAL_IMPORT.md` §6 now states imported data never comes from the live tree after final revalidation (backup-only reads) and documents the backup-hash gate; REPORT limitations no longer contain the race paragraph |
| 4 | Re-run targeted persistence tests and the mandatory 7/7 quality baseline | All re-run green (see Tests and validation) |

## Acceptance criteria evidence

| AC | Status | Evidence |
|---|---|---|
| AC1 Valid fixture backs up all inventoried safe source/reference files with verifiable manifest before import | PASS | `test_backup_copies_all_sources_and_references`: manifest has 4 entries (channels.json, project.json, video.mp4, replacement.png), each with source_locator/sha256/size_bytes/backup_relative_path; every entry exists in the backup dir and its bytes hash to the manifest sha256; `test_backup_happens_before_db_rows` |
| AC2 Valid import creates expected related rows and legacy IDs in one transaction; reopening DB preserves them | PASS | `test_import_creates_expected_rows_and_legacy_ids`: counts = workspace 1, channel 2, project 1, video_item 1, scene 2, artifact 4, artifact_owner 2, legacy_import 1; channel legacy ids `ch_a`/`ch_b`; project legacy id `proj_001`, status active, source channel FK set; video legacy id `proj_001`, duration 10000ms, 1920x1080, 30fps, source_artifact_id set; scenes legacy ids [0,1], frames [0,150]/[149,299]; artifacts ready with sha256/size; owners purpose `source` for project+video_item; audit row completed with summary; `test_reopen_preserves_rows` (fresh engine/session after commit); `test_import_preserves_deterministic_proposed_ids` (channel/project ids == preview `proposed_id`) |
| AC3 Blocker/stale/tampered/wrong-token inputs are refused before DB business writes | PASS | `test_wrong_token_refused_without_db_writes` (WRONG_TOKEN, zero rows, no backup dir); `test_blocker_preview_refused_without_db_writes` (BLOCKERS, corrupt channels); `test_stale_preview_refused_after_source_change` (SOURCE_CHANGED raised pre-backup — no `backups/` dir); `test_unsafe_reference_refused_without_backup` (UNSAFE_REFERENCES, `C:/Windows/evil.mp4` never copied) |
| AC4 Injected mid-import failure leaves zero partial business/import rows and source unchanged; backup remains valid | PASS | `test_injected_row_failure_rolls_back_all_rows` (monkeypatched `_project_status` raises; all 8 tables zero rows; backup dir remains with 4 valid manifest entries); `test_failure_leaves_source_unchanged` (sha256+mtime snapshot identical) |
| AC5 Repeated completed import is idempotent with no duplicate rows or second backup | PASS | `test_repeated_import_is_idempotent`: second run `idempotent_skipped=True`, `backup_id == first.backup_id`, counts unchanged, exactly 1 backup dir; `test_import_after_rollback_is_not_idempotent`: a failed (rolled-back) import does not block a later successful import (2 backup dirs: failed + success) |
| AC6 No runtime cutover/dual-write/schema change; targeted tests and all seven quality gates PASS | PASS | `test_no_runtime_cutover_imports_dependencies` (module source has no fastapi/app.api/app.workflow); `test_import_creates_no_database_at_backup_root`; `test_import_uses_one_legacy_import_row`; TOCTOU regressions (backup-sourced rows + refusal with zero writes); targeted tests 18/18 twice; related persistence 117 passed; full suite 277 passed, 8 skipped; ruff clean; mypy clean (48 files); quality baseline OVERALL PASS (all 7 gates, exit 0); `git diff --check` exit 0 |

## Files changed

- `app/persistence/legacy_import.py` (new; transactional importer)
- `app/persistence/__init__.py` (exports added)
- `docs/architecture/LEGACY_TRANSACTIONAL_IMPORT.md` (new; contract doc)
- `tests/fixtures/legacy_import/importable/` (new; synthetic fixture:
  channels.json, projects/proj_001/{project.json, video.mp4,
  replacement.png})
- `tests/test_transactional_legacy_import.py` (new; 16 tests)
- `docs/pm/sessions/S01-T05-transactional-import/LOG.md` (appended)
- `docs/pm/sessions/S01-T05-transactional-import/REPORT.md` (this file)

## Tests and validation

| Command | Result | Notes |
|---|---|---|
| `python -m pytest -q tests/test_transactional_legacy_import.py` | PASS | 18 passed in 2.59s (run twice) |
| `python -m pytest -q tests/test_persistence_bootstrap.py tests/test_managed_artifacts.py tests/test_legacy_import_preview.py tests/test_transactional_legacy_import.py` | PASS | 117 passed in 4.4s |
| `python -m ruff check app tests` | PASS | All checks passed |
| `python -m mypy app` | PASS | Success: no issues found in 48 source files |
| `python -m pytest -q -m "not gpu and not sam2 and not integration"` | PASS | 277 passed, 8 skipped, 7 deselected, 12 warnings (resubmission) |
| `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1` | PASS | OVERALL: PASS, all 7 gates, exit 0 (run id 20260803-183835) |
| `git diff --check` | PASS | exit 0 (only LF→CRLF advisory on Windows) |
| `certutil -hashfile channels.json SHA256` | UNCHANGED | `dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555` identical before/after; user diff preserved |
| Stray scan | NONE | No *.db/sqlite/sqlite3 under repo or fixture roots; no stray backup dirs |

## Architecture/domain impact

- Additive library layer: `legacy_import.py` imports only stdlib +
  `sqlalchemy` (session factory) + S01-T03 `ManagedRoot`/`hash_file` +
  S01-T04 `LegacyPreview` + S01-T02 ORM models.  No API/workflow/service/
  frontend import; no engine/ORM import at module scope beyond models.
- Implements domain contract §6 (one transaction per atomic import unit,
  bounded busy timeout via S01-T02 engine, artifact rows become `ready`
  only after atomic filesystem write succeeded), §7 (source files backed
  up before cutover, timestamped+checksummed; failed import rolls back
  atomic unit and leaves source untouched; re-running same completed
  checksum is a no-op), §2 (legacy IDs preserved as `legacy_id`, never
  reused as PKs; public IDs are the preview's deterministic uuid5s —
  no invented replacement IDs).
- No schema/migration change, no dependency change, no runtime cutover,
  no job persistence, no artifact purge/delete.

## Known limitations/risks

- Idempotency boundary is `(source_kind, source_sha256)` on a `completed`
  row (domain contract §4).  A future explicit "new import generation"
  is out of scope.
- Objects are inventoried in the preview but are not persisted as rows
  (no object/character table exists in the S01 schema; deferred to its
  owning epic per the domain contract).
- `source_sha256` is a digest of per-source checksums; reference-file
  bytes are recorded per-file in the backup manifest rather than in the
  idempotency hash.

## Recommended PM decision

`PENDING` — awaiting PM review.
