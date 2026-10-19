# S07 correction round 2 — P1 fallback matrix, P1 repin-via-UI, P2 acceptance bypass (2026-08-22, 16:20–19:15+07)

Session-level trail behind `correction-cycle-lessons.md` §25–§26.
Worktree s08-integration @ a43b20da (unchanged). Owner sessions: T02
20260821_044658_7fde0f (4 resumes: C4/C4b/C4c/C4d), T03 20260821_051414_184fd2
(2 resumes: C2/C2b). Route held: muse / ocg/muse-spark-1.2-contributor /
reasoning max / fallback disabled.

## Codex findings → fixes verified on disk

P1-A partial fallback was dead code:
- `project_cast.py` returned hardcode `fallback_allowed=False`; `blocked = not
  compatible` made every incompatible result blocked; picker L99-103/151
  disabled submit for every compatible=false; e2e asserted the WRONG contract
  (fallback-supported still disabled).
- Fix (verified in source): deterministic matrix in
  `_evaluate_compatibility_pure` + re-evaluation after additional workspace
  checks. Supported set = {generation_mismatch, incomplete_pack} (+ companion
  missing_required_pose); everything else fail-closed. Vietnamese descriptions
  per reason class. `blocked = not compatible and not fallback_allowed`.
  Picker: submit allowed iff `(compatible || fallback_allowed)`, button label
  "Ghim bất chấp khác biệt" when fallback.
- Regression proof: fail_before.log 3 failed (test_21/test_22/api fallback on
  old code) → pass_after 6 passed. Exact-value asserts only.

P1-B repin via Object Gallery UI hit POST-create conflict:
- fetchPinned dropped `found.id`; `effectiveMappingId = mappingId ?? null`;
  parent didn't pass mappingId → natural key existed → POST create → 409 from
  project_cast.py conflict branch.
- Fix: `pinnedMappingId` state set from `found.id` (L39), effective id =
  prop ?? pinned (L60), PATCH via `api.updateProjectCastMapping(id,
  {revision: currentRevision, …})` (L112-118); POST only when no mapping.

P2 acceptance test bypassed the UI:
- real-vertical spec used direct `page.request.patch` for primary repin → hid
  P1-B entirely. Fix: reload gallery → expand role → ProjectCastPicker → pick
  new published version → cast-submit → submit-success → GET assert revision
  n+1 + new pack_version_id. ZERO route.fulfill on /api/v2/project-cast*;
  direct PATCH remains ONLY in the stale-revision negative test.

## Dependency DAG executed

T03-C2 ran FIRST and correctly failed 0/4 with BLOCKED_DEPENDENCY_T02 (its own
spec comment documents this as expected evidence). After T02-C4 landed, the
re-run passed 4/4 — converting BLOCKED → PASSED proves both fixes end-to-end
through the production picker.

## Global-gate catches (each routed back to owner session)

1. ruff I001 ×19 (writer ran focused lint only) → C4b resume.
2. eslint no-explicit-any ×4 + unused patchUrl ×1 across both spec files →
   C4c + C2b parallel mini-corrections (disjoint files).
3. tsc TS18047 ×2 introduced BY C4c at 17:54 — AFTER my 17:43 tsc gate; caught
   by the final full battery re-run → C4d resume (guard `expect(patchBody)
   .not.toBeNull()` + optional chaining).

## Final gate battery (all green, output/s07-final/20260822_1900/)

Full nine-file S07: 91 passed (72.4s) · T02 focused 34 · T03 focused 19 ·
regression cluster 233 passed (131.2s) · PW s07t02 26 passed (desktop+390) ·
PW s07t03 real vertical 4 passed · ruff app tests clean · mypy 96 files clean ·
tsc exit 0 · eslint 0 errors · next build exit 0 · alembic single head
b2c3d4e5f6a7b + round-trip upgrade→downgrade→upgrade OK · PRAGMA
foreign_key_check [] (28 tables) · git diff --check clean · HEAD a43b20da ·
MAIN motionforge.db 311296 B unchanged · netstat :8004/:3014/:3012 empty ·
0 orphan processes.

## Ops notes

- Alembic temp-DB check needs `MOTIONFORGE_DATABASE_URL=sqlite:///<temp>` env
  AND pre-created parent dir (`mkdir -p`) — `-x db_url=` not honored here;
  SQLite fails with "unable to open database file" when the folder is missing.
- Don't guess regression-cluster filenames: guessed test_s06_surface_api.py-
  style names don't exist (pytest exit 4 "no tests ran"); `ls tests/ | grep`
  first. Real cluster: channel×2, video_item_crud, s08_a01_role_taxonomy,
  s08_a02_structural_evidence_api, s08_h02_security, s08_r01_root_resolution.
- Writer smoke.log contained a Traceback while REPORT claimed SMOKE PASS —
  grep raw logs for Traceback/EXIT before citing writer narrative; coverage
  stood on pytest/PW gates instead.
- models.py/migrations mtimes checked to prove writers never touched schema
  (project_cast.py edit is domain-layer logic inside the verdict-named
  location, no migration change).
- Sprint report appended (append-only) at
  docs/pm/sprints/S07-SPRINT_REPORT.md 19:12+07 entry; manager report at
  output/s07-manager-verification/20260822_1810/manager_correction_round2.md.
