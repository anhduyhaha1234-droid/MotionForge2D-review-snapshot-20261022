# S01-T03 - Managed artifact paths, atomic writes and safe Trash

**Status:** APPROVED  
**Epic:** E01 - Durable Domain, Persistence and Jobs  
**Sprint:** S01 - Persistence foundation  
**Gate:** G1 - Foundation green  
**Depends on:** S01-T02 (APPROVED)

## User outcome

All future managed media writes and removals have one containment-safe filesystem contract; incomplete writes cannot appear as ready artifacts and removal is recoverable through Trash.

## Required reading

1. `docs/pm/SESSION_PROTOCOL.md`
2. `docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md`
3. `app/persistence/models.py`
4. `app/config.py`
5. `app/services/cleanup_service.py`
6. `tests/conftest.py`

## Allowed write scope

- `app/persistence/artifacts.py`
- `app/persistence/__init__.py`
- `tests/test_managed_artifacts.py`
- `docs/architecture/MANAGED_ARTIFACT_CONTRACT.md`
- `docs/pm/sessions/S01-T03-managed-artifacts/LOG.md`
- `docs/pm/sessions/S01-T03-managed-artifacts/REPORT.md`

## Forbidden scope

- Existing cleanup/project/workflow/API/frontend behavior.
- Database schema/migration revisions, dependencies, legacy import or Job persistence.
- User files, root JSON, presets and production output.
- Roadmap, TASK and PM_REVIEW.

## Target behavior

- A configured managed root is resolved once; only normalized relative paths are accepted.
- Reject absolute paths, drive/UNC paths, empty paths, `..`, symlink/junction escape and the database file.
- Atomic write uses a same-directory unique staging file, flush/fsync, `os.replace`, optional SHA-256 verification and cleanup on failure.
- Trash move stays under a configured Trash root, uses collision-safe names and writes a recovery manifest containing original relative path/checksum/time.
- Restore validates containment and never overwrites an existing destination.
- Filesystem helpers return explicit results; they do not commit database sessions or mutate Artifact rows.

## Acceptance criteria

- [ ] AC1 Valid paths resolve within the managed root; all path escape forms are rejected.
- [ ] AC2 Atomic bytes/stream writes expose only final or prior content and clean staging files after failure.
- [ ] AC3 Hash/size evidence is returned and optional expected checksum mismatch cannot publish.
- [ ] AC4 Trash move is recoverable, collision-safe, manifest-backed and cannot cross managed boundaries.
- [ ] AC5 Restore refuses overwrite and validates both original and Trash containment.
- [ ] AC6 Targeted tests and all seven quality gates PASS.

## Required validation

```powershell
python -m pytest -q tests/test_managed_artifacts.py
python -m ruff check app tests
python -m mypy app
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
git diff --check
```

## Stop conditions

- A safe behavior requires deleting or moving existing user data.
- Cross-platform junction/symlink semantics cannot be tested safely.
- Write scope must expand into existing runtime services or schema.
