# S01-T04 - Read-only legacy JSON inventory and import preview

**Status:** APPROVED  
**Epic:** E01 - Durable Domain, Persistence and Jobs  
**Sprint:** S01 - Persistence foundation  
**Gate:** G1 - Foundation green  
**Depends on:** S01-T02 (APPROVED)

## User outcome

Before migration, the user can obtain a deterministic report of legacy channels/projects/assets, validation issues and proposed identity mappings without changing any source file or database.

## Required reading

1. `docs/pm/SESSION_PROTOCOL.md`
2. `docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md`
3. `app/schemas/__init__.py`
4. `app/workflow/channel_service.py`
5. `app/services/project_service.py`
6. `tests/conftest.py`
7. `examples/example_project.json`

## Allowed write scope

- `app/persistence/legacy_preview.py`
- `app/persistence/__init__.py`
- `tests/test_legacy_import_preview.py`
- `tests/fixtures/legacy_import/`
- `docs/architecture/LEGACY_IMPORT_PREVIEW.md`
- `docs/pm/sessions/S01-T04-legacy-preview/LOG.md`
- `docs/pm/sessions/S01-T04-legacy-preview/REPORT.md`

## Forbidden scope

- Root `channels.json`, `projects/`, presets, output and any user source file.
- SQLite/database creation, ORM writes, backups, cutover or transactional import.
- Existing API/workflow/service/frontend behavior.
- Migration revisions, roadmap, TASK and PM_REVIEW.

## Target behavior

- Explicit input paths only; inventory never assumes or writes repo-root data.
- Preview computes SHA-256 before/after and proves source bytes/mtime unchanged.
- Parses channel list and project JSON defensively; one corrupt item becomes an issue rather than aborting all inventory.
- Reports counts, legacy IDs, proposed deterministic new IDs, source relationships, referenced files and missing/unsafe paths.
- Issues have stable severity/code/location/message; blockers are separated from warnings.
- Unknown JSON fields are listed/preserved in preview audit data, not silently discarded.
- Output DTO can serialize deterministically to JSON but serialization is caller-controlled.

## Acceptance criteria

- [ ] AC1 Valid fixture inventory produces deterministic entity/file counts and ID mapping.
- [ ] AC2 Corrupt JSON/schema/reference/path cases produce stable actionable issues without source mutation.
- [ ] AC3 Unsafe absolute/traversal/symlink references are blockers and are never followed outside the supplied legacy root.
- [ ] AC4 Unknown fields and checksums are recorded for S01-T05 audit/import.
- [ ] AC5 Repeated preview is byte-identical and leaves all source bytes/mtime unchanged; no DB is created.
- [ ] AC6 Targeted tests and all seven quality gates PASS.

## Required validation

```powershell
python -m pytest -q tests/test_legacy_import_preview.py
python -m ruff check app tests
python -m mypy app
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
git diff --check
```

## Stop conditions

- Preview requires guessing a destructive correction or mutating legacy data.
- A required legacy format cannot be represented without a product decision.
- Write scope must expand into importer/runtime services.
