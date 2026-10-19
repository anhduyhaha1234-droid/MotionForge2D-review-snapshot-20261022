# S10-C4 — Codex final independent PM review (2026-08-30)

## Verdict

`S10-C4 = CHANGES_REQUESTED / NOT_APPROVED`.

C4 materially closes the backend authority, durable correction, structural
measurement, Windows long-path and restart/reuse findings from C3. The sprint
cannot yet be approved because the mandatory frontend Apply lint gate is red on
new S10-owned code. The bounded next round is S10-C5: resume the exact T04B
owner to correct the `/apply` state synchronization without suppressing lint,
then resume the exact T04C owner to validate the resulting current build with
two fresh vertical runs and the complete exit matrix.

S11-T02..T06 and production S13 remain blocked. This review does not authorize
commit, push, merge or production work in another sprint.

## Reviewed live state

- Integration authority:
  `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`, branch
  `codex/s08-integration`, HEAD
  `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`; dirty state is the retained S10
  implementation/evidence write-set.
- Protected MAIN: `C:\Users\Admin\MotionForge2D`, branch `master`, HEAD
  `f0ee4bd11f83fb6fed8c9a8f3924e85b903c3d3b`.
- `MOTIONFORGE_DATABASE_URL=UNSET`; no active S10 worker/writer was found.
  Hermes desktop/service processes were present but no task command line owned
  the S10 tree.
- Hermes terminal state in the S10 registry/report:
  `S10-C4 = SPRINT_SUBMITTED / TASK_MANAGER_VERIFIED /
  PENDING_CODEX_REREVIEW`.
- C4 exact owners retained: T01A `20260827_234001_9d7f39`, T01C
  `20260828_003035_859fe5`, T03 `20260828_011920_b79bd6`, T04A
  `20260828_014304_25d94a`, T04B `20260828_020206_b1f8af`, T04C
  `20260828_023122_76b87e`.

## Independent acceptance results

### Green backend, authority and evidence gates

- Exact Ruff `--select F` over nine S10 production files plus eight S10 test
  files: `All checks passed!`.
- Exact nine-file mypy: `Success: no issues found in 9 source files`.
- Alembic: exactly one head, `a10b11c12d3e`.
- Materialized OpenAPI: 261 paths, 327 operations, 327 distinct operation IDs,
  zero duplicates; all eight FullApply routes are present.
- J1-v4 freeze: direct current-file SHA-256 verification is 13/13, zero
  mismatch.
- S10 backend suite review run: 204 tests passed; the two long-path tests died
  in fixture setup only because Codex supplied an unnecessarily long
  `--basetemp` prefix. Re-running exactly those two tests under a unique short
  temp root passed 2/2. Hermes' retained final evidence also records 206/206
  twice on valid roots. This is not classified as a product failure.
- Direct code review confirms production no longer stages synthetic source
  truth, the S10 reconciler no longer bypasses input-change detection,
  recompute resolves a persisted `s09_correction`, and structural comparison
  derives source/rendered evidence independently with fail-closed missing or
  tampered authority.
- Both C4 vertical run DBs were opened independently with `query_only` enabled.
  Each has one durable S09 correction, 36 artifacts, two occurrence segments,
  two segment-motion rows, one contact row, seven route rows and zero foreign
  key violations.
- Run bundles are distinct and complete:
  `output/s10/c4/t04c-c3/run1-c4a-c3-green3` and
  `output/s10/c4/t04c-c3/run2-c4a-c3-green`. Evidence records real lease expiry
  and replacement ownership, long media paths, SHA/size/ffprobe facts,
  affected-only recompute, structural `REVIEW_REQUIRED` and tamper `BLOCKED`.
- TSC, Next production build and build validator 7/7 are green. The current
  local build after C4 has BUILD_ID `Ypg2OvkwfOy47aKRUCFMk`; the two retained
  vertical runs used the earlier validated build
  `KIWvay6FvLdiWmVFduSMG`.

### Blocking finding

#### F1 — P1 release gate: scoped Apply ESLint excludes and then fails the S10 route page

- **File:** `frontend/src/app/(app)/apply/page.tsx:90`
- **Actual:** an effect synchronously calls `setRunId(urlRunId)` and, on the
  next line, `setProjectIdForStatus(urlProject)`. Current ESLint reports
  `react-hooks/set-state-in-effect` and exits 1.
- **Scope truth:** the page is untracked S10 code inside the explicit T04B
  write-set. It is not a pre-existing product error outside S10. T04B's recorded
  lint command checked only `src/features/apply/**`, omitting the owned route
  page, while the sprint exit later described scoped Apply ESLint as green.
- **Impact:** the mandatory current-tree frontend gate is red and the pattern
  can cause cascading renders/URL-state loops. A successful TSC/build does not
  supersede an explicit lint failure.
- **Required correction:** resume exact T04B owner
  `20260828_020206_b1f8af`; preserve URL deep-link, reload, browser navigation
  and local-storage behavior while removing synchronous state mutation from the
  effect. No ESLint disable, config weakening or behavior-test deletion.
- **Downstream:** because production frontend bytes and BUILD_ID change, T04C
  must run acceptance on the new current build. Old-build vertical evidence is
  retained but cannot alone approve the changed tree.

### Non-blocking cleanup folded into C5

The same exact scoped lint invocation reports four unused-variable warnings:
one in `frontend/e2e/s10-apply-ui.spec.ts` and three in
`frontend/e2e/s10-full-apply.spec.ts`. They do not independently prove a product
defect, but each is in the corresponding T04B/T04C owner scope. C5 requires
those owners to make the full exact S10 Apply lint command green with
`--max-warnings 0`, without weakening assertions.

## Dependency and next action

The only authorized DAG is:

`PREP -> T04B-C2 -> J5 -> T04C-C4 -> EXIT -> CODEX_REREVIEW`

Backend files are frozen during C5. Any backend or domain drift is a blocker,
not a reason for T04B/T04C to expand scope. The bounded Manager prompt is:

`docs/pm/prompts/S10_C5_APPLY_LINT_CURRENT_BUILD_EXIT_MANAGER_2026-08-30.md`.

