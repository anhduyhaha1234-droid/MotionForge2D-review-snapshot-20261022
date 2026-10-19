# Sprint S00 Review - Isolate and record the baseline

**Status:** APPROVED  
**Epic:** E00 - Baseline and Change Safety  
**PM verification run:** `20260803-144737`

## Sprint outcome

MotionForge 2D now has a trustworthy development baseline: tests are isolated from production-root channel/preset data, quality checks are reproducible, runtime dependencies and FFmpeg discovery are explicit, Python typing is clean, and frontend ESLint has zero errors.

## Approved tasks

| Task | Outcome | Status |
|---|---|---|
| S00-T01 | Isolate test channel/preset storage from production-root data | APPROVED |
| S00-T02 | Add reproducible quality baseline runner and evidence | APPROVED |
| S00-T03 | Declare runtime dependencies and centralize FFmpeg discovery | APPROVED |
| S00-T04A1 | Eliminate Python typing errors outside the projects route | APPROVED |
| S00-T04A2 | Eliminate the remaining 81 projects-route typing errors | APPROVED |
| S00-T04B | Eliminate 28 frontend ESLint errors without redesign | APPROVED |

## Exit evidence

`scripts/quality-baseline.ps1` run `20260803-144737`:

| Gate | Result |
|---|---|
| Environment / preflight | PASS |
| Python tests | PASS - 160 passed, 8 skipped, 7 deselected |
| Python lint | PASS |
| Python typing | PASS - 0 errors in 41 source files |
| Frontend typecheck | PASS |
| Frontend lint | PASS - 0 errors, 8 accepted warnings |
| Frontend production build | PASS |

Overall result: **7/7 PASS**.

## Accepted baseline limitations

- Seven `@next/next/no-img-element` warnings remain because changing these media/canvas workflows to Next Image would alter delivery, optimization and cache behavior.
- One intentional ScreenB hook-dependency warning remains to force repaint when mask preview clears.
- GPU/SAM2/integration tests remain excluded from the routine non-GPU gate; they require their documented hardware/runtime environment.
- Full Playwright execution was not part of S00 because it requires a running backend and the slow workflow requires GPU/SAM2. Specs parse and typecheck successfully.

## Data and repository safety

- Root `channels.json` and user character assets were preserved.
- No commit, push or destructive cleanup was performed.
- Existing user/approved dirty changes remain in the working tree for the user's eventual checkpoint decision.

## Next gate

Do not start Sprint S01 until the user accepts this sprint review. S01 begins the durable persistence foundation; it does not yet implement the full reskin UI.
