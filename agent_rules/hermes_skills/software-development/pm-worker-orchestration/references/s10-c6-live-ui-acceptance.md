# S10-C6 real Apply UI acceptance — verified detail (2026-08-30)

## Context

S10-C5 = CHANGES_REQUESTED (Codex `reviews/S10_C5_PM_REVIEW_2026-08-30.md`).
F1 P1 = acceptance integrity: `frontend/e2e/s10-apply-ui.spec.ts` passed
without exercising the workflow — empty-state disjunctions, conditional
assertions, mobile `test.skip`, no Cancel/Retry/Resume clicks, no structural
Review decision. Backend/authority/recovery/structural/media/C5 2× vertical
runs all independently green. C6 = bounded exact-owner correction:
T04B `20260828_020206_b1f8af` (test/evidence only) → J6-UI → conditional
J6-BUILD + T04C-C5 only if production build inputs change → EXIT.

## C6 DAG

`PREP -> S10-T04B-C3 -> J6-UI -> EXIT` (linear default; T04C-C5 branch only
if production frontend bytes change → new BUILD_ID → mandatory 2 fresh
vertical runs on the new build).

## Preflight recorded (before dispatch)

- Rules 180L SHA `987386c59f72145bdeb203473a2e3949d46d309cca68fdc95b612925c8f5aa25`.
- HEAD d3f6f79, 47 porcelain, DB UNSET, J1-v4 13/13 + EOL PASS, alembic
  single head, backend 18-file aggregate `312ea89c…`, BUILD_ID
  `rbYCsFU8q82gvOvcRhJSA` (C5 build, 7/7 scanned 201).
- Smell baseline re-run: current UI suite contains `if (visible)` ×6,
  `.or(empty/loading/error)` for progress/evidence/actions, mobile
  `test.skip`, Project Detail `count()===0` early return — matches C5 F1.
- Public routes inspected from OpenAPI: 8 full-apply routes
  (`/projects/{id}/full-apply`, `/full-apply/{run_id}`, cancel, retry,
  resume, recompute, recompute/{correction_id}, structural-compare) +
  s09-corrections/confirm/cancel + s09-approvals/verify + structural-evidence.
- ESLint exact full 4-set exit 0 (baseline already clean post-C5):
  `src/features/apply/**/*.{ts,tsx}` + `src/app/(app)/apply/page.tsx` +
  `e2e/s10-apply-ui.spec.ts` + `e2e/s10-full-apply.spec.ts`.

## What the C6 worker packet must contain

1. Read C5 review F1 fully + reproduce the smell baseline.
2. Rewrite `frontend/e2e/s10-apply-ui.spec.ts` to 10 binary scenarios ×
   desktop+mobile (20 tests, zero skip):
   - approval gate: real `toBeDisabled()` + exact VN reason; create current
     approval via product contract → enabled.
   - submit: click → observe real 2xx request → durable run ID in displayed
     run + URL + localStorage + public status API.
   - reload/history: reload retains A; navigate B; Back/Forward switch
     identity; no replace loop; no stale storage override.
   - progress truth: real nonterminal queued/running run (controlled product
     process ownership, NO DB patch) → visible backend-derived status/progress
     vs public status response; empty/loading/error never counts as success.
   - cancel / retry / resume: real clicks, observed request/response, backend
     poll to terminal semantics, UI survives reload; separate controlled runs
     preferred; derive Retry semantics from product contract, don't assume.
   - structural evidence + Review: completed real run → UI-initiated compare
     → REVIEW_REQUIRED + actionable role/layer/segment/route evidence →
     Review enabled; genuine missing/tampered authority → BLOCKED → Review
     disabled; never inject the structural response.
   - project-detail entry: seeded project → link to /apply with expected
     selection; no count-0 early return.
   - mobile: EXECUTE 390x844 Chromium (overflow ≤1, buttons/helpers visible,
     no clipping); desktop also executes.
3. New bounded `frontend/playwright.s10-ui.config.ts` + helpers under
   `frontend/e2e/helpers/s10-apply-ui/**` only if needed for isolated
   service/fixture ownership. T04C files read-only (may import helpers).
4. Conditional production correction ONLY if live tests expose a real
   T04B-owned frontend defect (apply/** + features/apply/** + bounded
   api.ts + AppNav/projects entry) — append failing evidence + ownership
   rationale to LOG first; otherwise tests-only.
5. Gates: tsc 0; exact max-warning lint over apply features + page + both
   E2E specs + new helpers/config; live suite desktop+mobile zero skip on
   real product backend + current production frontend; fresh DB/runtime/
   output/ports; BUILD_ID manifest recorded; diff-check; write-set audit.
   Terminal `TASK_SUBMITTED`.

## Verified environment traps (hit live in T04B-C3 R1)

- BUILD-ORIGIN PORT: build bakes `NEXT_PUBLIC_API_URL=http://localhost:8201`
  (run-s10.js BUILD_ENV; manifest envContract). Suite launched backend on
  8212 → real UI `Failed to fetch` + select "(không có project)". Fix:
  launch backend on the baked port or drive via `node output/s10/run-s10.js`
  with its env. Harness environment error, NOT production defect.
- MOBILE BROWSER: `devices["iPhone 13"]` = WebKit; `ms-playwright/webkit-*`
  not installed → browserType.launch fails. Use explicit Chromium project
  with viewport 390x844; record config so mobile cannot be skipped.
- Do NOT rebuild just to change ports — rebuilding mutates BUILD_ID and
  forces the J6-BUILD/T04C-C5 branch. Keep the C5 build when only test
  config changes.

## J6-UI gate (Manager independent)

1. SHA/write-set audit: backend 18-file aggregate unchanged, J1 13/13,
   T04C files untouched, every frontend/test/config diff attributed to T04B.
2. Exact max-warning lint incl. new helper/config sources; `tsc --noEmit`.
3. Second fresh isolated env: full live UI suite, desktop + mobile, zero
   skip/flaky-retry/vacuous path.
4. Independently inspect trace/report evidence: Apply, Cancel, Retry,
   Resume, compare and Review were CLICKED and public product responses/
   states asserted — green Playwright summary alone insufficient.
5. If production source/build inputs byte-identical to C5 → keep C5 BUILD_ID
   and 2 vertical runs by hash/reference, record J6-UI = MANAGER_VERIFIED,
   proceed to EXIT WITHOUT rerunning T04C (don't create cost). Any flaky
   failure → resume same T04B owner with exact evidence; backend/cross-scope
   change → stop for Codex.