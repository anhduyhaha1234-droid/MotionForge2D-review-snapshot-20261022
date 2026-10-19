# S00-T04A2 - Projects route typing baseline

**Status:** APPROVED  
**Epic:** E00  
**Sprint:** S00  
**Gate:** G1  
**Depends on:** S00-T04A1 APPROVED

## Outcome

Resolve the remaining 81 mypy errors in `app/api/routes/projects.py` without changing API payloads, aliases, runtime behavior or media semantics, making `python -m mypy app` pass.

## Required reading

1. `docs/pm/SESSION_PROTOCOL.md`
2. This TASK.md.
3. Latest mypy log showing 81 projects-route errors.
4. `app/api/routes/projects.py` and only directly referenced schemas/tests needed for truthful fixes.

## Allowed write scope

- `app/api/routes/projects.py`
- Direct route tests under `tests/` only if needed to lock existing behavior.
- Session REPORT.md and LOG.md.

## Forbidden scope

- Other production modules, frontend, dependencies/config.
- API path/payload/alias/status behavior changes.
- Blanket ignores, new `type: ignore`, casts without runtime/type proof, mypy weakening.
- Refactoring/splitting the monolith; that belongs to later architecture work.

## Acceptance criteria

- [ ] AC1: `python -m mypy app` passes with zero errors.
- [ ] AC2: No suppression or strictness weakening; aliases such as `assetPath` and enums are constructed through the existing schema contract.
- [ ] AC3: Existing API payloads/status codes and media behavior remain unchanged, protected by targeted tests.
- [ ] AC4: Full non-GPU tests and Ruff pass.
- [ ] AC5: Quality runner has no regression beyond unchanged frontend ESLint baseline.
- [ ] AC6: Scope/user changes preserved; report/log complete.

## Required validation

```powershell
python -m mypy app
python -m pytest -q <targeted route tests>
python -m pytest -q -m "not gpu and not sam2 and not integration"
python -m ruff check app tests
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
git diff --check
git status --short
```

## Stop conditions

- A fix requires changing API/schema/media behavior.
- Need to edit outside allowed scope or suppress type checking.
