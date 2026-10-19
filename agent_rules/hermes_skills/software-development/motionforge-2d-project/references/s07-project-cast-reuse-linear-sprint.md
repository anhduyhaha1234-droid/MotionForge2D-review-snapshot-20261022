# S07 Project Cast Reuse — Linear Sprint, RO Snapshot Review & Migration-Head Ripple (verified 2026-08-21)

Sprint S07 (Project Cast Reuse) was the first strictly-linear production sprint after S08-A02
corrections: T01 (domain/API/migration) → T02 (picker + compatibility) → T03 (cross-project reuse,
version-isolation acceptance), each dispatched only after the previous = `MANAGER_VERIFIED`. This
reference captures what a full sprint adds to the per-cycle lessons in `background-worker-orchestration`.

## 1. Strict linear owning-session rules (T01→T02→T03)

- One Task ID = one owning writer session. A task's corrections resume THAT session (same model Muse,
  reasoning max) — never a fresh "correction session". Example: T01's two head-test corrections both
  resumed `20260821_011252_8f17a1`.
- Dispatch T(next) ONLY after T(prev) = `MANAGER_VERIFIED`. No parallelizing the three production tasks.
- T03 (acceptance) found a production defect → T03 does NOT edit production; Manager sent the exact
  reproduction to the owning T01 session via `hermes chat --resume <T01-session> -q "MANAGER_CORRECTION#2…"`;
  after T01 fixed it, T03 was resumed (`-q "…re-run acceptance…"`) to re-verify. Same pattern applies for
  frontend defects → resume T02 session.
- **T03 discovered a migration-head test file the T01 fix missed** (`test_s08_a02_structural_evidence_migration.py`
  still asserted the OLD head `a0b1c2d3e4f5`; 6 tests failed under new head `b2c3d4e5f6a7b`). This is why the
  migration-owning task's head-fix list must be COMPLETE: grep `-rln "<old_head>" tests/` and update EVERY hit
  (migration chain tests, persistence bootstrap `S08_HEAD_TABLES` set, object_* `assert version ==`, role
  taxonomy, structural-evidence migration `test_revision_chain_and_single_head`). The T01 head-fix earlier
  listed 8 files but missed this one; growing a 9th file later costs an extra resume round.

## 2. Read-only reviewers see a snapshot — treat early "BLOCKING" as expected, reconcile post-land

- S07-RO1 (domain/persistence review) and S07-RO2 (API/UI/test review) were dispatched in parallel with
  the T01 writer. Because they ran BEFORE code landed, their reports read "10 BLOCKING … 0% satisfied,
  project_cast_mapping table 0 hits, no app/persistence/project_cast.py …" — a correct snapshot of an
  empty pre-write tree, NOT evidence of a defect.
- Do not route those findings back as corrections. After each task lands, re-review each RO finding against
  the LANDED code (grep strict schemas `_StrictModel(extra=forbid, strict=True)`, server-owned `WORKSPACE_ID`,
  helper-text classes `text-gray-400`/`text-[11px]`, OpenAPI `$ref`, idempotency/CAS, FK RESTRICT) and close
  with "land verified". Record RO1/RO2 state in MANAGER_STATE as "snapshot findings — land verified".
- BA preflight verdict `SAFE_TO_PARALLELIZE_WITH_EVIDENCE` is READ-ONLY — it grants no implementation
  authority; still wait for a separate Codex/BA code grant before touching that sprint.

## 3. Head-constant fix may need an allowlist expansion (BLOCKED_SCOPE decision)

The migration-owning task's allowlist covered its own files, but the head-constant test fixes touched
BASELINE migration/persistence test files outside it. Manager logged a BLOCKED_SCOPE decision expanding the
allowlist for the EXACT head-constant files (only the string `old_head → new_head`, no test-logic change),
then resumed the owning session — matching the pattern a migration always implies: upstream head-sensitive
tests are effectively in scope of the migration change.

## 4. Sprint terminal state + stale notifications

- After all three tasks verified and the fresh 21-file combined gate passed ×2 consecutive (437 each,
  post flaky-fix), set `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`, stop ALL S07 lanes, and
  hand off: session lineage, recovery history (502×3 + CLI resume-syntax + head-test rounds + flaky round),
  exact changed files, protected hashes, dirty-worktree delta.
- Stale "Background process completed" notifications (for sessions that already exited and were already
  resumed/handled — e.g. RO1, RO2, RO2's 502, BA resume) keep arriving after the fact. Recognize them as
  historical, confirm the state is already captured in MANAGER_STATE, and do not relaunch or re-review.
- A manager turn interrupted mid-write still loses drafted prose (heartbeat/answering), but the background
  writers continue — repeat the current status in the next turn.

## 5. Post-correction Codex review round (2026-08-21 ~17:49+07) — BLOCKED_LIVENESS + cross-task drift

- T03 worker (resume of `20260821_051414_184fd2`, model alpha @ custom/9router per user override) died
  ~17:07–17:22+07 BEFORE SUBMITTED: log `output/s07-t03-c1/20260821_160800_writer-alpha.log` froze at
  24,881 B; LOG.md/REPORT.md kept pre-correction mtimes (05:46/05:45); `tests/test_s07_acceptance.py`
  left half-edited (11×E501, dangling "CORRECTION:" comment ~line 497). Verdict: BLOCKED_LIVENESS —
  resume the same session with the remaining findings; never a replacement session.
- **Cross-task contract drift**: T01-C1 (11:17) enforced compatibility AT THE WRITE BOUNDARY; T03's seed
  helpers written against the OLD lax policy (`CharacterPackVersion(status="published")` with ZERO
  assets in `_seed_one`/`_create_new_pack_for_char`) then failed 11/14 with
  `ProjectCastConflictError: incomplete_pack,missing_required_pose`. The policy was RIGHT; the seeds
  were stale. Lesson: after any correction tightens a domain invariant, immediately re-run DOWNSTREAM
  task suites — their fixtures encode yesterday's laxity. Fix seeds to build complete packs (all 6
  CORE_POSE_SLOTS assets, like `_seed_shared_pack_with_two_projects` did) rather than weakening policy.
- **API check-ordering defect (T01)**: DELETE route checked `revision is None → 422` BEFORE the
  workspace-scoped existence lookup → cross-workspace delete without revision returned 422 instead of
  404 no-leak (`test_workspace_a_cannot_mutate_b_mappings`: `assert 422 == 404`). Rule: ownership/
  existence checks FIRST (404), request-validation errors AFTER (422) — both contracts stay satisfiable.
- Real-vertical spec carried fail-open patterns (`if (map2Res.ok()) {…}` around mandatory cross-project
  asserts; `if (directRes.ok())` treating a 2xx incompatible write as acceptable; global-setup without
  temp-root wipe) — see e2e-workflow-validation skill, "Fail-open assertion patterns".
- Reviewer gates that stayed green this round: T01+T02 targeted 63 passed; alembic single head
  b2c3d4e5f6a7b; protected hashes unchanged; ruff/mypy failures confined to S11-owned files (parallel
  sprint in the same worktree) — attribute static-gate noise PER FILE before blaming the sprint under
  review.
