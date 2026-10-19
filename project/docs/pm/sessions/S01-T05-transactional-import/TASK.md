# S01-T05 - Transactional legacy import, backup and migration tests

**Status:** APPROVED
**Epic:** E01 - Durable Domain, Persistence and Jobs
**Sprint:** S01 - Persistence foundation
**Gate:** G1 - Foundation green
**Depends on:** S01-T03, S01-T04 (APPROVED)

## User outcome

An explicitly approved, blocker-free legacy preview can be backed up and imported once into an initialized SQLite database; failure rolls back database rows, source data remains untouched and recovery evidence is retained.

## Required reading

1. `docs/pm/SESSION_PROTOCOL.md`
2. `docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md`
3. `docs/architecture/MANAGED_ARTIFACT_CONTRACT.md`
4. `docs/architecture/LEGACY_IMPORT_PREVIEW.md`
5. `app/persistence/models.py`
6. `app/persistence/artifacts.py`
7. `app/persistence/legacy_preview.py`
8. `tests/test_persistence_bootstrap.py`
9. `tests/test_legacy_import_preview.py`

## Allowed write scope

- `app/persistence/legacy_import.py`
- `app/persistence/__init__.py`
- `tests/test_transactional_legacy_import.py`
- `tests/fixtures/legacy_import/importable/`
- `docs/architecture/LEGACY_TRANSACTIONAL_IMPORT.md`
- `docs/pm/sessions/S01-T05-transactional-import/LOG.md`
- `docs/pm/sessions/S01-T05-transactional-import/REPORT.md`

## Forbidden scope

- Existing JSON/project/assets, root data, production DB/output/presets.
- API/workflow/service/frontend cutover or dual writes.
- Schema/migration revision changes and dependency changes.
- Job persistence, artifact purge or deletion.
- Roadmap, TASK and PM_REVIEW.

## Target behavior

- Import requires an explicit `LegacyPreview`, initialized session factory, workspace ID, managed backup root and confirmation token derived from preview content.
- Refuse previews with blockers, changed source checksum/mtime, unsafe references, wrong confirmation token or unsupported schema.
- Before any DB business rows, copy all inventoried source JSON and safe referenced files to a collision-safe immutable backup directory using atomic writes; write a manifest with source locator, checksum, size and backup relative path.
- Revalidate source checksums immediately before transaction.
- One transaction creates/reuses workspace and imports channels, projects, one legacy VideoItem per project, valid scenes, source Artifact rows/owners and one LegacyImport audit row.
- Preserve legacy IDs and deterministic proposed IDs from preview. Do not invent replacement IDs during import.
- Same completed preview/source generation is idempotent and creates no duplicate rows or backup.
- Any row/import failure rolls back the whole import transaction. Backup remains available; source bytes/mtime remain unchanged.
- No existing runtime route is cut over; importer is explicit library API only.

## Acceptance criteria

- [ ] AC1 Valid fixture backs up all inventoried safe source/reference files with verifiable manifest before import.
- [ ] AC2 Valid import creates expected related rows and legacy IDs in one transaction; reopening DB preserves them.
- [ ] AC3 Blocker/stale/tampered/wrong-token inputs are refused before DB business writes.
- [ ] AC4 Injected mid-import failure leaves zero partial business/import rows and source unchanged; backup remains valid.
- [ ] AC5 Repeated completed import is idempotent with no duplicate rows or second backup.
- [ ] AC6 No runtime cutover/dual-write/schema change; targeted tests and all seven quality gates PASS.

## Required validation

```powershell
python -m pytest -q tests/test_transactional_legacy_import.py
python -m pytest -q tests/test_persistence_bootstrap.py tests/test_managed_artifacts.py tests/test_legacy_import_preview.py tests/test_transactional_legacy_import.py
python -m ruff check app tests
python -m mypy app
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
git diff --check
```

## Stop conditions

- Import cannot preserve a required legacy value without schema change.
- Source mutation, runtime cutover or destructive cleanup becomes necessary.
- Atomic filesystem/DB ordering cannot be made recoverable under this contract.
