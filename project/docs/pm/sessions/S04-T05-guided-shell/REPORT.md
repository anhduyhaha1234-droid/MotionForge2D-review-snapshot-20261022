# S04-T05 - Implementation Report

**Status:** SUBMITTED
**Quality Baseline:** `20260804-124750` — OVERALL PASS (7/7 gates, exit 0; fresh re-run after final edits)
**Session:** 20260804_121845_83641c (new Hermes MAX session; single-writer handshake honored — no commit, no next-task packet)

## Summary

Corrected the guided six-stage production shell and made resume persistence durable:

- **StageRail** now renders exactly the six stages (`Nhập video`, `Đối tượng`, `Demo thay thế`, `Áp dụng`, `Kiểm tra`, `Xuất 4K`), maps each stage explicitly to the existing application screen/domain state, keeps unique display IDs for the duplicated screen mapping (demo + apply both drive the `replacement` screen), allows navigation only to current/completed stages, and exposes an accessible reason/tool-tip on disabled stages.
- **Resume persistence** now goes through the typed API client (`api.ts` → `apiFetch` → configured `API_BASE`), sends the required `revision` on every durable PATCH, refetches + retries once on `409`, never swallows persistence failure (visible `resumeError` in the store), and never sends legacy/non-UUID project IDs to the UUID-constrained `/api/v2` endpoints.
- **Project detail page** switched from raw relative `/api/v2` fetches + mock fallbacks to the typed durable client with real empty/error/legacy states.

## Acceptance criteria evidence

| AC | Result | Evidence |
|---|---|---|
| 1. StageRail shows exactly the six stages | PASS | `PRODUCTION_STAGES` in `frontend/src/components/layout/StageRail.tsx`; structural check confirmed each label exactly once (count=1) and all six keys (`import/objects/demo/apply/review/export`) present. |
| 2. Display stages map explicitly to screen/domain states; duplicated mappings use unique display IDs | PASS | Each stage carries an explicit `screen` field; `stageIndexForScreen()` maps store screen → stage; `demo` + `apply` both map to `replacement` with unique keys (`demo`/`apply`) and unique durable domain states (`demo_approved`/`applying_reskin`). Structural checks: 6 `screen:` fields, 2 replacement mappings, 6 unique keys. |
| 3. Navigation only to current/completed stages; disabled stages expose accessible reason/tool-tip | PASS | `navigateToStage` guards `index > activeIndex || !projectId`; unreachable stages get `aria-disabled`, an `aria-label` with the reason, `title` tooltip, and `cursor-not-allowed` styling; every stage has a `disabledReason`. |
| 4. Resume persistence through typed API client; no raw relative `/api/v2` fetch | PASS | Durable calls go through `api.getDurableProject` / `api.updateDurableProject` / `api.listDurableProjectVideos` (all `apiFetch` → `API_BASE`). Structural check: raw `fetch(\`/api/v2` count = 0 in `api.ts` AND `page.tsx`. |
| 5. Durable PATCH includes required `revision`, handles 409 by refetching, never swallows failure | PASS | `patchDurableProject()` sends `revision` (fetches it first when unknown), detects `API 409`, refetches the project and retries (bounded), propagates all other failures; store `persistResumeStep` sets visible `resumeError` ("Không thể lưu bước tiếp tục: …") on failure. Backend contract confirmed by 73 passing durable tests (`tests/test_project_crud.py`, `tests/test_video_item_crud.py`). |
| 6. Legacy/non-UUID IDs not sent to durable UUID endpoint | PASS | `isUuid()` guard at three layers: `patchDurableProject` rejects non-UUID outright; store `persistResumeStep` no-ops for non-UUID; page skips durable load and shows a legacy notice. |
| 7. `channels.json` byte-identical and unstaged | PASS | SHA256 before = after = `dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555`; still unstaged in `git status`. |
| 8. Typecheck, lint, build, focused tests, fresh 7/7 baseline | PASS | `tsc --noEmit` exit 0; eslint on 4 scope files exit 0 (0 problems); `npm run build` exit 0; 73 targeted durable tests passed; quality-baseline run `20260804-124750` 7/7 PASS exit 0. |

## Validation commands (real output)

```text
npx tsc --noEmit                          → PASS (exit 0)
./node_modules/.bin/eslint <4 scope files> → PASS (exit 0, 0 problems)
npm run build                              → PASS (exit 0; /projects/[id] dynamic route built)
node structural-check (40 checks)          → ALL CHECKS PASSED (exit 0)
python -m pytest tests/test_project_crud.py tests/test_video_item_crud.py -q --cache-clear
                                          → 73 passed (exit 0)
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
                                          → OVERALL: PASS (exit 0), run 20260804-124750 (fresh re-run)
certutil -hashfile channels.json SHA256    → dd7aae26… (identical before/after)
git diff --check <4 changed files>         → clean
```

## Changed files (allowed scope only)

- `frontend/src/lib/api.ts` — durable v2 DTOs + `isUuid` + durable client methods + `patchDurableProject` (409-aware CAS helper)
- `frontend/src/stores/project.ts` — `durableRevision`/`resumeError` state + `persistResumeStep` action + `resetAll` reset
- `frontend/src/components/layout/StageRail.tsx` — six-stage guided shell (explicit mapping, gated navigation, accessible reasons, resume persistence on navigation)
- `frontend/src/app/(app)/projects/[id]/page.tsx` — typed client, UUID guard/legacy notice, no mock data, corrected VideoItem shape, visible error state
- `docs/pm/sessions/S04-T05-guided-shell/LOG.md`, `REPORT.md`

## Deviations / limitations

- **Focused frontend tests:** the existing frontend test layout is Playwright e2e only (no unit runner configured). E2E requires a running backend + dev server + ffmpeg fixture; they exercise the whole app, not these files. Per the task's "if the existing test layout supports them" clause, focused verification was done via tsc + eslint + build + a 40-check structural contract script (AC1–AC6) against the actual source, plus 73 targeted backend contract tests for the revision/409 CAS the client implements.
- **StageRail highlight on `/`:** `frontend/src/app/(app)/page.tsx` (out of allowed scope) still passes `currentIndex={stageMap[screen]}`; the explicit `stageIndexForScreen` mapping in StageRail yields identical indices for all five screens, so behavior is consistent. The rail now self-derives when no prop is passed.
- **Full-apply stage:** stage `apply` has no dedicated screen in the legacy workspace (it is driven by the `replacement` screen); it remains reachable as a completed/current stage and persists its own `applying_reskin` resume step.

## Out-of-scope findings (recorded, not fixed)

- `frontend/src/components/Dashboard.tsx` lines 41 & 50 still use raw relative `fetch("/api/v2/projects")` and `fetch("/api/v2/jobs?state=running")` — the same AC4 anti-pattern, but the file is outside the allowed write scope. Recommend a follow-up task to route the dashboard through `api.ts` (note: `/api/v2/jobs?state=running` does not appear to be a registered backend route; `jobs.router` serves the legacy `/api/jobs` namespace).
- S04-T04 page.tsx previously shipped mock fallback data (project detail + video items) — removed in this task within scope.

## Test pass/fail/not-run

- Targeted durable backend tests: 73 passed.
- Full quality baseline: 7/7 PASS (python tests, ruff, mypy, tsc, eslint, next build; environment preflight).
- E2E Playwright suite: NOT RUN (requires full-stack runtime; not part of the 7-gate baseline).
