# S00-T04A1 - Python typing outside projects route

**Status:** APPROVED  
**Epic:** E00  
**Sprint:** S00  
**Gate:** G1  
**Depends on:** S00-T03 APPROVED

## Outcome

`mypy app` errors outside `app/api/routes/projects.py` are resolved with truthful types and runtime guards, without changing behavior. The projects-route errors remain explicitly baselined for S00-T04A2.

## Required reading

1. `docs/pm/SESSION_PROTOCOL.md`
2. This TASK.md.
3. `pyproject.toml` mypy settings.
4. Latest `Gate_4_-_Python_typing.log` under `output/quality-baseline/`.
5. Only source files outside `app/api/routes/projects.py` reported by that log.
6. Direct tests for changed modules.

## Allowed write scope

- Mypy-reported Python files under `app/`, except `app/api/routes/projects.py`.
- Direct tests required to protect runtime behavior.
- Session REPORT.md and LOG.md.

## Forbidden scope

- `app/api/routes/projects.py`.
- Frontend, dependencies, configs and roadmap docs.
- Blanket `ignore`, per-module suppression, new `type: ignore`, weakening strict mypy, or casts used only to silence errors without proof.
- Business/API/media behavior changes.
- User data/assets.

## Acceptance criteria

- [ ] AC1: `mypy app` reports no errors outside `app/api/routes/projects.py`.
- [ ] AC2: Fixes use concrete types, narrowing and runtime guards; no suppression/strictness weakening.
- [ ] AC3: Existing user changes in preset/channel areas are preserved.
- [ ] AC4: Targeted and full non-GPU tests pass; Ruff passes.
- [ ] AC5: Remaining mypy errors are only in projects route and are inventoried exactly for S00-T04A2.
- [ ] AC6: Quality runner has no new regression; report/log complete.

## Required validation

```powershell
python -m mypy app
python -m pytest -q <targeted tests>
python -m pytest -q -m "not gpu and not sam2 and not integration"
python -m ruff check app tests
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
git diff --check
git status --short
```

## Stop conditions

- A type fix requires behavior/schema/API change.
- Existing user change intent cannot be preserved.
- Need to edit projects route or weaken mypy.
