# S00-T04B - Implementation Report

**Status:** SUBMITTED

## Outcome

Frontend ESLint baseline eliminated: `npm run lint` now exits 0 with zero errors (was 28 errors + 21 warnings). All fixes are real code changes — no rule disabling, no config edits, no `any`, no UI/API/navigation/copy-semantics/image-refresh/canvas/rehydration behavior changes. 8 warnings retained, each justified below.

Round 2 (PM CHANGES_REQUESTED) additionally fixed a stale-image behavior regression in `CompositeCanvas.tsx` by associating every loaded image with the URL that produced it and deriving effective images at render time, so a null/empty/changed URL immediately yields null — restoring the pre-task null-reset semantics without synchronous setState in effects and without suppression.

## Acceptance evidence

| AC | Status | Evidence |
|---|---|---|
| AC1 | PASS | `npm run lint` exit 0, 0 errors, 8 warnings. Retained warnings: 7× `@next/next/no-img-element` (ScreenB:428,467; ScreenC:172; ScreenD:427,546,779,803) — converting to `next/image` would change image delivery (optimizer, layout, caching of cache-busted URLs) and is out of scope; 1× ScreenB:186 `useCallback` unnecessary-dep `maskPreview` — intentionally kept: when mask preview clears (null), drawCanvas identity must change so the draw effect re-runs and repaints without the stale mask overlay. |
| AC2 | PASS | Hook/effect fixes preserve behavior and no violation is hidden by suppression. CompositeCanvas: each image state is a `{ url, img }` record; the draw effect consumes only effective images derived by `effectiveImage(state, currentUrl)` which returns null unless the loaded URL still equals the current prop URL. A null/empty/changed URL therefore renders null immediately (no timing dependence, no setState-in-effect). Multi-object entries are URL-validated (`entry.url === obj.replacementUrl` and truthy URL) before rendering; removed objects are never iterated. ScreenB `drawCanvas` hoisted above referencing effects (fixes access-before-declaration); same redraw triggers. ScreenD `Date.now()` during render replaced with a `reloadNonce` bumped in `uploadMut.onSuccess`/`presetMut.onSuccess` — the exact moments the old timestamp refreshed URLs; `&v=` asset_path param still busts replacement cache. useProjectRehydration defers no-session setState into a microtask — splash gating unchanged. |
| AC3 | PASS | `npm run typecheck` exit 0; `npm run build` exit 0 (Next.js 16.2.12, ✓ Compiled successfully, TypeScript passed). |
| AC4 | PASS | Playwright specs parse/list cleanly (`--list` shows 1 test each) and typecheck. Unit checks: `python -m pytest -q -m "not gpu and not sam2 and not integration"` → 160 passed, 8 skipped, 7 deselected. Focused component test: NOT ADDED — no unit-test runner exists in frontend (no vitest/jest/mocha/tsx/ts-node; only Playwright e2e which needs a live backend on port 8000, not running). Exact code-level proof instead: standalone runtime proof mirroring `effectiveImage` + multi-object rule, asserting the four PM scenarios (null URL → null even with loaded img; URL change → old img hidden; matching URL → img exposed; multi-object removed/changed/null → no stale render). All checks passed (see LOG). Full E2E execution NOT run — exact reason: backend on port 8000 not running; GPU SAM2 spec needs RTX GPU/SAM2. Fixture `test-2s.mp4` present; generation logic preserved. |
| AC5 | PASS | `scripts/quality-baseline.ps1` run `20260803-144413`: all 7 gates PASS (Environment, Python tests, Python lint, Python typing, Frontend typecheck, Frontend lint, Frontend build), overall exit 0. |
| AC6 | PASS | `git diff --check` exit 0 (CRLF warnings only, cosmetic). `git status --short` shows only the 11 expected frontend files + this session's REPORT/LOG; all pre-existing dirty files and untracked user content (channels.json, presets, docs) untouched; stray `frontend/playwright-report/index.html` (touched by `playwright test --list`) restored to HEAD. REPORT complete, status SUBMITTED. |

## Files changed

- `frontend/e2e/gpu-workflow.spec.ts` — `require("fs")` → top-level `import fs from "fs"`
- `frontend/e2e/happy-path.spec.ts` — same
- `frontend/src/components/AssemblyModal.tsx` — escape 4 raw quotes (`&quot;`)
- `frontend/src/components/ChannelDashboard.tsx` — drop unused `ChannelWorkspace` import
- `frontend/src/components/CompositeCanvas.tsx` — URL-association: `LoadedImage` records, `effectiveImage()` derivation, effective-image draw paths, URL-validated multi-object entries; 6 image effects no longer call setState synchronously; `let`→`const` cx/cy; drop dead `clipOpFor`; drop unused `anchorAbsX`/`anchorAbsY`
- `frontend/src/components/DubbingPanel.tsx` — drop unused `transcribeResult` assignment
- `frontend/src/components/ScreenA.tsx` — escape 6 quotes; drop unused `ArrowRight`
- `frontend/src/components/ScreenB.tsx` — hoist `drawCanvas` above referencing effects; escape 2 quotes + `&`→`&amp;`; drop unused `scaleToCanvas`, `selection`, `setSelection`
- `frontend/src/components/ScreenC.tsx` — drop unused `useState`/`useMutation` imports; add stable `setGallery` dep
- `frontend/src/components/ScreenD.tsx` — replace `Date.now()` render impurity with `reloadNonce` state (bumped on upload/preset success); escape 2 quotes
- `frontend/src/hooks/useProjectRehydration.ts` — defer no-session `setIsRehydrating(false)` via `queueMicrotask`

## Deviations / limitations

- 8 warnings intentionally retained (see AC1).
- Two pre-existing `eslint-disable` comments (ScreenD:306 debounce effect, useProjectRehydration:83 empty-deps) were present in HEAD and are untouched; they suppress warnings only and were not introduced here.
- No unit-test runner exists for a focused component test; provided a standalone runtime proof of the URL-association semantics instead (exact commands/asserts in LOG).
- E2E Playwright execution requires a live backend (port 8000 down) and GPU/SAM2 for the @slow spec — not run, reasons recorded (AC4).

## Test pass/fail/not-run

- PASS: pytest (160 passed, 8 skipped, 7 deselected), mypy app, ruff check app tests, tsc --noEmit, next build, npm run lint (0 errors), quality-baseline.ps1 (7/7 gates), URL-association runtime proof (4 scenarios).
- NOT RUN: Playwright E2E execution (backend 8000 not running; GPU/SAM2 required for @slow spec). Specs verified via `--list` parse and tsc.

## Recommended PM decision

APPROVE — all acceptance criteria met; Round-2 stale-image regression fixed with URL-association (immediate null on null/empty/changed URL, no suppression/config change, no timing-dependent reset); retained warnings are justified and behavior-preserving.
