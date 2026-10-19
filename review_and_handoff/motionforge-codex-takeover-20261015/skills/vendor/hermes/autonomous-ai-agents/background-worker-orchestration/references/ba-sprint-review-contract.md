# BA Sprint Review Contract (MotionForge2D PM sprints)

Condensed from S07 review cycle (2026-08-21). Use whenever acting as the
independent review gate ("BA"/Codex reviewer) over a PM-gated sprint.

## Mandatory five-part output

1. **STATE_RECONCILIATION** — worktree, branch, pinned HEAD (from
   `git rev-parse`, never from snapshot), dirty status attributed per sprint,
   task/session/model map, latest worker log + timestamp, live PIDs mapped to
   sessions via CommandLine, S11-style parallel lanes, tree stable/moving,
   protected baseline checks.
2. **REVIEW_FINDINGS** — or literally `No actionable findings`. Each finding:
   Severity P0/P1/P2 · Task owner · owning session ID · file:line ·
   reproduction/evidence (real command output) · expected vs actual · impact ·
   missing/weak test · exact correction acceptance criteria · proposed
   exclusive write-set. No generic recommendations.
3. **INDEPENDENT_TEST_EVIDENCE** — per gate: command, run ID, temp root,
   result, first failure, rerun reason/count, evidence path, tests NOT run
   and why (e.g. "spec mid-edit by dead worker").
4. **S07_VERDICT** — exactly one: APPROVED · CHANGES_REQUESTED ·
   REVIEW_BLOCKED_ACTIVE_WRITER · BLOCKED_LIVENESS. Never DONE/CLOSED.
5. **EXACT_MANAGER_PROMPT** — complete copy-paste prompt for the Manager
   session (contract structure in SKILL.md § "Dispatch a dedicated MANAGER
   session"). Never sent to Hermes by the reviewer itself.

## Verdict decision shortcuts

- Worker PID gone + log frozen + packet LOG/REPORT mtimes stale + half-edited
  allowlisted files + no evidence dir ⇒ **BLOCKED_LIVENESS** (findings
  prepared but routed into the resume prompt; do NOT review the corpse as
  final).
- Log/process still advancing ⇒ **REVIEW_BLOCKED_ACTIVE_WRITER** — never
  review a moving tree, never run global gates on it.
- All corrections landed, writer exited, independent gates green, protected
  data untouched ⇒ APPROVED only then.

## Cross-task defect attribution (critical for fair routing)

A later task's red suite is often an EARLIER task's contract change, not a
production bug: e.g. T01 tightens write-boundary compatibility ⇒ T03 seed
fixtures creating published-but-incomplete packs now correctly fail with
`incomplete_pack`. Classify: production defect → owning session; stale seed/
fixture → correcting task's own scope. Verify by running the failing test and
reading the actual policy error before routing blame.

## Fail-open test patterns worth grepping for

- `if (response.ok()) { assert... }` — response failure silently passes.
- Direct incompatible write returning 2xx asserted only indirectly.
- Mobile viewport "tests" checking width/visibility but skipping the full
  scenario flow.
- Global-setup that doesn't wipe its temp root (residue-dependent passes).
- Configs still pointing at deleted test routes (`/test-*`) = stale, excluded
  from acceptance.

## Evidence hygiene rules

- Every claim backed by a command actually run this session; timestamps +07
  real (UTC = local − 7h).
- Protected data (channels.json SHA-256, main motionforge.db size/hash)
  re-checked AFTER validation.
- Never delete old evidence; classify mocked UI vs real-backend vs
  real-vertical — a mock test is never called real vertical.
- Test counts/reports are not proof until actual code+test read; run targeted
  suites yourself with unset MOTIONFORGE_DATABASE_URL, unique MOTIONFORGE_ROOT,
  Windows-native basetemp, `-p no:cacheprovider`.

## User expectations during the cycle

- "Bao lâu thì xong" → concrete stage table (elapsed vs remaining per stage)
  with risk factors (connection-error retries, parallel lanes holding the
  tree), updated as reality diverges. Update the ETA after each real slip
  (connection error, resume2/resume3) instead of repeating the stale one.
- One visible heartbeat per check-in; watchdog handles the gaps.
- User may promote the SAME agent from reviewer-only to "dispatch + monitor +
  review" ("bạn sẽ thay codex… gọi bạn là BA"): then BA dispatches the Manager
  session itself, arms watchdogs, answers progress pings, runs all gates at
  the end, and STOPS for the user to trigger external Codex as the FINAL
  sign-off. A BA "APPROVED (khuyến nghị)" recommendation ≠ sprint CLOSED —
  only the external reviewer closes.

## End-to-end BA cycle lessons (verified 2026-08-21→22)

- **Manager turn budget**: a poll-heavy manager burns ~1 turn/min; size
  `--max-turns` to the slowest lane's wall clock (3 resumes × E2E overran
  200 turns in 7h22m). Prefer completion-notification wakeups over sleep
  loops inside the manager prompt.
- **Post-mortem packet append with truthful attribution**: if the worker
  finishes code+tests but dies before LOG/REPORT append (or the manager dies
  first), BA may append the correction entry itself — recording which session
  died when, what the WORKER completed (mtimes, evidence dirs, test counts),
  and that BA appended post-mortem. Never fabricate worker claims or present
  BA-written text as worker-authored; keep provenance lines (original code by
  route X, correction by model Y) honest.
- **Verify fixes landed before trusting "done" claims**: grep the actual fix
  signatures (removed `if(...ok())` wrappers, fail-hard
  `expect([409,422,400]).toContain(status)`, config booting real backend,
  seed pose-slot counts) and check file mtimes against the claimed work
  window — a dead worker's last words are not proof its edits survived.
- **Playwright race root cause worth recognizing**: two concurrent Playwright
  instances (an orphaned foreground run past its timeout holding ports + a
  fresh background run) produce endless hangs/noise; the healthy fix observed
  was kill BOTH, restart exactly one instance, re-run. Budget such cleanup
  time into long E2E lanes.
- **Frontend gates without npm scripts**: no `typecheck` script → use
  `npx tsc --noEmit` directly (`npm run lint`, `npm run build` exist);
  test-route leakage into production build is greppable in
  `.next/app-path-routes-manifest.json`.
- **Alembic roundtrip**: `downgrade <rev>^` caret syntax unsupported — pass
  the literal parent revision id.
