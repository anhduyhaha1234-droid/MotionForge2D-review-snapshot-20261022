# S00-T04B - Session Log

Append-only implementation log. Hermes must record baseline, decisions, changed files and validation evidence here.

## Baseline (2026-08-03, before changes)

`npm run lint` (frontend/): 49 findings = 28 errors + 21 warnings, exit 1.

Errors by file (28):
- `e2e/gpu-workflow.spec.ts:11` — @typescript-eslint/no-require-imports (`require("fs")`)
- `e2e/happy-path.spec.ts:11` — @typescript-eslint/no-require-imports (`require("fs")`)
- `src/components/AssemblyModal.tsx:113` — react/no-unescaped-entities ×4 (raw `"` in JSX text)
- `src/components/CompositeCanvas.tsx` — react-hooks/set-state-in-effect ×6 (setState(null)/setState(new Map()) in effect bodies at 157,169,181,193,205,219); prefer-const ×2 (cx, cy at 496-497)
- `src/components/ScreenA.tsx` — react/no-unescaped-entities ×6 (299:57, 299:75, 302:57, 302:69, 366:25, 366:37)
- `src/components/ScreenB.tsx:145` — react-hooks/immutability (drawCanvas accessed before declaration inside mask onload)
- `src/components/ScreenD.tsx` — react-hooks/purity ×2 (Date.now() during render at 159, 166); react/no-unescaped-entities ×2 (484:61, 484:69)
- `src/hooks/useProjectRehydration.ts:61` — react-hooks/set-state-in-effect (setIsRehydrating(false) synchronous in effect)

Warnings (21, non-blocking): unused imports/vars (`ChannelWorkspace` ChannelDashboard:5; `clipOpFor` CompositeCanvas:116; `anchorAbsX`/`anchorAbsY` CompositeCanvas:587/594; `transcribeResult` DubbingPanel:42; `ArrowRight` ScreenA:16; `scaleToCanvas` ScreenB:11; `selection`/`setSelection` ScreenB:22-23; `useState`/`useMutation` ScreenC:3-4), exhaustive-deps warnings (ScreenB:148, 210; ScreenC:30), and @next/next/no-img-element warnings (9× across ScreenB/ScreenC/ScreenD).

## Round 1 decisions (2026-08-03)

- Fix all 28 errors with real code changes — no NEW eslint-disable, no config edits, no `any`. (Two pre-existing `eslint-disable` comments in ScreenD:306 and useProjectRehydration:83 remain untouched — they suppress warnings only, were present in HEAD, and were not introduced by this task.)
- E2E specs: replace `require("fs")` with top-level `import fs from "fs"` (identical behavior, ESM-clean).
- Unescaped entities: replace raw `"` inside JSX text with `&quot;` (HTML entity) — preserves rendered copy exactly (also `&` → `&amp;` in one ScreenB string).
- CompositeCanvas effects: removed the synchronous early-return `setState(null)`/`setState(new Map())` calls from effect bodies (satisfies react-hooks/set-state-in-effect). ⚠️ PM review found this Round-1 approach left a stale-image regression: when a URL becomes null/empty the old image state remained and the draw effect consumed it directly. Corrected in Round 2 (below).
- prefer-const cx/cy: `let` → `const` (no reassignment).
- ScreenB: hoist `drawCanvas` useCallback above the image-loading effects so `img.onload` closures reference the declared const (fixes react-hooks/immutability error at 145 + the exhaustive-deps warning at 148). Added `drawCanvas` to the mask-load effect deps. Effect ordering and redraw triggers otherwise unchanged.
- ScreenD Date.now(): replace render-time cache-busting with `reloadNonce` state bumped in `uploadMut.onSuccess`/`presetMut.onSuccess` — the exact moments the old timestamp refreshed URLs; `&v=` asset_path version still busts replacement cache. Render purity preserved.
- useProjectRehydration: defer no-session `setIsRehydrating(false)` into a `queueMicrotask` so no synchronous setState happens in the effect body.
- Warnings: fixed safe mechanical ones (all unused imports/vars), retained with justification: 8× @next/next/no-img-element and 1× ScreenB useCallback unnecessary-dep (maskPreview — intentionally kept because clearing the mask preview must change drawCanvas identity to repaint without the stale overlay).

## Round 2 — PM CHANGES_REQUESTED fix (2026-08-03)

PM finding: "A URL changing to null/empty can therefore keep an old frame, mask, replacement or multi-object asset visible."

Root cause: Round 1 removed the synchronous `setState(null)` resets but the draw effect consumed the raw state (`frameImg`, `maskImg`, `inpaintedImg`, `repImg`, `sequenceFrameImg`, `multiObjImgs`), so a previous successful image remained visible after its URL became null/empty.

Fix (frontend/src/components/CompositeCanvas.tsx only):
1. Added `interface LoadedImage { url: string; img: HTMLImageElement }` and a pure helper `effectiveImage(loaded, currentUrl)` — returns null unless `currentUrl` is truthy AND `loaded.url === currentUrl`.
2. State changed to URL-paired records: `useState<LoadedImage | null>` for the five single images; `useState<Map<string, LoadedImage>>` for multi-object.
3. Derived effective images (`effFrameImg`, `effMaskImg`, `effInpaintedImg`, `effRepImg`, `effSequenceFrameImg`) via `effectiveImage(...)` at render; the draw effect uses ONLY these — a null/empty/changed URL immediately yields null with no timing dependence and no setState-in-effect.
4. Multi-object: entries are `{ url, img }` records; the draw loop validates `entry.url === obj.replacementUrl` (and `obj.replacementUrl` truthy) before rendering. Removed objects aren't in `allObjects` so are never iterated; changed/null URLs yield null.
5. Image-loading effects only kick off async loads; onload stores `{ url, img }`, onerror stores null. No synchronous setState in effect bodies (rule still satisfied).

Corrected statements: LOG/REPORT no longer claim "the previous image stays until the next successful load — no stale state is ever drawn". The accurate description is the URL-association derivation above: stale images can exist in state but are never exposed/rendered for a non-matching or empty URL.

Test: no unit-test runner exists in frontend (no vitest/jest/tsx/ts-node; only Playwright e2e which needs a live backend). Provided a standalone runtime proof (temp file, since scripts/ is outside allowed write scope): mirrored `effectiveImage` + multi-object rule and asserted the four PM scenarios — null URL → null, URL change → null, matching URL → img, multi-object removed/changed/null → no stale render. All passed (evidence below).

## Files changed (frontend/)

- `frontend/e2e/gpu-workflow.spec.ts` — import fs (no-require-imports fix)
- `frontend/e2e/happy-path.spec.ts` — import fs (no-require-imports fix)
- `frontend/src/components/AssemblyModal.tsx` — escape 4 quotes
- `frontend/src/components/ChannelDashboard.tsx` — drop unused ChannelWorkspace import
- `frontend/src/components/CompositeCanvas.tsx` — 6 effects de-synced + URL-association (LoadedImage/effectiveImage), prefer-const, drop dead clipOpFor, drop unused anchorAbsX/Y
- `frontend/src/components/DubbingPanel.tsx` — drop unused transcribeResult
- `frontend/src/components/ScreenA.tsx` — escape 6 quotes, drop unused ArrowRight
- `frontend/src/components/ScreenB.tsx` — hoist drawCanvas, escape 2 quotes + 1 `&`, drop unused scaleToCanvas/selection/setSelection
- `frontend/src/components/ScreenC.tsx` — drop unused useState/useMutation imports, add setGallery dep
- `frontend/src/components/ScreenD.tsx` — reloadNonce purity fix, escape 2 quotes
- `frontend/src/hooks/useProjectRehydration.ts` — queueMicrotask defer of no-session setState

## Validation evidence

Round 1 (2026-08-03): lint 0 errors / 8 warnings; tsc exit 0; build exit 0; pytest 160 passed/8 skipped/7 deselected; mypy exit 0; ruff exit 0; quality-baseline run 20260803-143205 all 7 gates PASS; git diff --check exit 0.

Round 2 (2026-08-03, after URL-association fix):
| Command | Result |
|---|---|
| `npm run lint` (frontend/) | exit 0 — 0 errors, 8 warnings (same retained set) |
| `npm run typecheck` (`npx tsc --noEmit`) | exit 0 |
| `npm run build` | exit 0 — ✓ Compiled successfully |
| `python -m pytest -q -m "not gpu and not sam2 and not integration"` | 160 passed, 8 skipped, 7 deselected, exit 0 |
| `python -m mypy app` | Success: no issues found in 41 source files, exit 0 |
| `python -m ruff check app tests` | All checks passed!, exit 0 |
| `scripts/quality-baseline.ps1` | run 20260803-144413 — all 7 gates PASS (exit 0) |
| `git diff --check` | exit 0 (CRLF warnings only, cosmetic) |
| `git status --short` | only expected frontend files + pre-existing dirty/untracked; stray `frontend/playwright-report/index.html` (touched by `playwright test --list`) restored to HEAD |

URL-association runtime proof (temp file, removed after run):
```
PASS 1: null/empty/undefined URL yields null even with loaded img
PASS 2: URL change (t=1 -> t=2) hides old frame
PASS 3: matching URL exposes loaded img; no load yet -> null
PASS 4a: removed object is not iterated -> never drawn
PASS 4b: changed/null/matching replacement URL handled
ALL URL-ASSOCIATION CHECKS PASSED (exit 0)
```

Playwright: `npx playwright test e2e/*.spec.ts --list` — both specs parse and list (1 test each); `npx tsc --noEmit` covers e2e files with no errors. Full E2E execution NOT run: requires backend on port 8000 (not running) and the GPU SAM2 workflow needs RTX GPU + SAM2 model; specs are @slow GPU tests. Fixture `e2e/fixtures/test-2s.mp4` present; generation logic preserved (now using top-level fs import).
