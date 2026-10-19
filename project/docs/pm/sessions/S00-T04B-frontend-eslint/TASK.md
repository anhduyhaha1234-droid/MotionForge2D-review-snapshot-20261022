# S00-T04B - Frontend ESLint baseline

**Status:** APPROVED  
**Epic:** E00  
**Sprint:** S00  
**Gate:** G1  
**Depends on:** S00-T04A2 APPROVED

## Outcome

Eliminate the 28-error frontend ESLint baseline without changing user-visible behavior, API contracts, navigation, media semantics or visual design. Remove safe mechanical warnings where possible and document any intentionally retained warnings.

## Required reading

1. `docs/pm/SESSION_PROTOCOL.md`
2. This `TASK.md`
3. `docs/quality/QUALITY_BASELINE.md`
4. `frontend/AGENTS.md`
5. Relevant local Next.js/React guidance under `frontend/node_modules/next/dist/docs/` before changing hooks or image behavior
6. Only the files named by the current `npm run lint` output and their direct tests/types

## Baseline

`npm run lint` reports 49 findings: 28 errors and 21 warnings. Errors occur in the two Playwright specs, `AssemblyModal.tsx`, `CompositeCanvas.tsx`, `ScreenA.tsx`, `ScreenB.tsx`, `ScreenD.tsx`, and `useProjectRehydration.ts`.

## Allowed write scope

- `frontend/e2e/gpu-workflow.spec.ts`
- `frontend/e2e/happy-path.spec.ts`
- Frontend source files currently named by ESLint under `frontend/src/`
- Direct frontend tests only when needed to preserve existing behavior
- This session's `REPORT.md` and `LOG.md`

## Forbidden scope

- Backend/Python files, dependencies, configs, PRD, Master Plan, roadmap, task contract and PM review
- Disabling or weakening ESLint rules, blanket suppressions, `eslint-disable`, or replacing type safety with `any`
- UI redesign, copy changes beyond character escaping, API/path/payload changes, new product features
- Commit, push, approval or starting another task

## Acceptance criteria

- [ ] AC1: `npm run lint` exits 0 with zero errors; retained warnings are enumerated and justified.
- [ ] AC2: Hook fixes preserve loading, image refresh, canvas drawing and rehydration behavior; no synchronous-effect or render-purity violation is hidden by suppression.
- [ ] AC3: `npm run typecheck` and `npm run build` pass.
- [ ] AC4: Relevant Playwright/unit checks run where supported; any not run are named with the exact reason.
- [ ] AC5: `scripts/quality-baseline.ps1` finishes with all seven gates PASS.
- [ ] AC6: `git diff --check` passes; existing dirty/user files are preserved; REPORT/LOG are complete and status is SUBMITTED.

## Required validation

```powershell
Set-Location frontend
npm run lint
npm run typecheck
npm run build
Set-Location ..
python -m pytest -q -m "not gpu and not sam2 and not integration"
python -m mypy app
python -m ruff check app tests
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
git diff --check
git status --short
```

## Stop conditions

Stop as `BLOCKED` if a lint-compliant fix requires a user-visible redesign, public contract change, dependency/config change, backend edit or rule suppression.
