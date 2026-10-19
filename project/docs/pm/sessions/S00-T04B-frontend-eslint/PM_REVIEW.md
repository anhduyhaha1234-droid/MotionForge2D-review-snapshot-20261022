# S00-T04B - PM Review

**Decision:** APPROVED

## Round 1 finding

### Required change 1 - Preserve null/empty image reset semantics

`frontend/src/components/CompositeCanvas.tsx` removed every synchronous reset when an input URL becomes null and removed the empty-map resets for `allObjects`. The new comment and REPORT claim stale images are not rendered, but the draw code consumes `frameImg`, `maskImg`, `inpaintedImg`, `repImg`, `sequenceFrameImg` and `multiObjImgs` directly; those states can still contain the previous successful image. A URL changing to null/empty can therefore keep an old frame, mask, replacement or multi-object asset visible. This is a runtime behavior regression and fails AC2.

Implement a lint-compliant association between each loaded image and the URL that produced it, then derive the effective image as null unless the loaded URL still equals the current prop URL. Apply the same principle to multi-object images so removed objects or changed/null replacement URLs cannot reuse stale entries. Do not use an ESLint suppression, config change or a delayed reset whose correctness depends on timing.

Add focused frontend tests if a suitable existing test setup is available; otherwise provide a precise static/runtime proof and run the complete required validation. Correct the inaccurate LOG/REPORT statements and submit again.

No other redesign or cleanup is authorized.

## Correction verification

Correction pass 1 associates every loaded image with its source URL and derives an effective image only when that URL still matches the current prop. Multi-object entries are also checked against the current object's replacement URL. This restores immediate null/changed-URL behavior without synchronous state updates or lint suppression.

## Independent PM evidence

- Reviewed all frontend diffs, with specific attention to canvas image lifecycle, ScreenB draw ordering, ScreenD cache invalidation and project rehydration.
- `scripts/quality-baseline.ps1` run `20260803-144737` -> all seven gates PASS, overall exit 0.
- Python tests: `160 passed, 8 skipped, 7 deselected` within the quality run.
- Frontend lint: exit 0 with zero errors and eight explicitly baselined warnings.
- Frontend typecheck and production build: PASS.
- No new rule suppression, config weakening, dependency change or backend edit was introduced by this task.

## PM disposition

Approved after one correction attempt. `S00-T04B` and the Sprint S00 exit gate are complete. The retained image-element and intentional redraw-dependency warnings are accepted baseline items, not errors.
