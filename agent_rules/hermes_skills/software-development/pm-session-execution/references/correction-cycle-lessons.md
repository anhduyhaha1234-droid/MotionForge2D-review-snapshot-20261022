# Correction-cycle lessons (verified 2026-08-21 — Sprint S07 Codex CHANGES_REQUESTED; extended 2026-08-22 with C3/C4 rounds)

Durable lessons from full Codex CHANGES_REQUESTED correction cycles
(T01 → T02 → T03 sequential owning-session resumes → fresh final gate;
then multi-wave corrections C3/C4 on top).

## 1. Session ownership — no replacement writers
- Corrections resume the SAME owning session ID; never create correction Task
  IDs (`S07-T01-C1` etc.) or replacement writers while the owning session lives.
- Sequence enforced by manager: resume T01 → manager review/verify → resume T02
  → review → resume T03 → review → fresh S07 final gate → stop at
  `MANAGER_VERIFIED_PENDING_CODEX_REVIEW`. Never self-approve.
- One production writer active at a time (T02 only after T01 verified, etc.).

## 2. Frozen authoritative policy pattern
- Manager writes the FROZEN policy into the correction prompt verbatim:
  fail-closed rules, exact allowed-file allowlist, forbidden paths, required
  test list (numbered), validation commands, "finish SUBMITTED only".
- Writer implements the policy; it does NOT redesign. If a file outside the
  allowlist is needed → STOP, BLOCKED_SCOPE, report manager/user.

## 3. Write-boundary enforcement (Codex F1)
- Compatibility/policy gate must be single-sourced in the domain/repository
  layer: route evaluate + create_mapping + update_mapping/repin all call the
  SAME function (`_check_compatibility_or_raise` → `evaluate_compatibility`).
  A client that skips evaluate must still be rejected at the write boundary.
- `compatible=false` → no create, no repin; `fallback_allowed` is advisory ONLY
  until a durable fallback-acceptance snapshot exists (correction stays
  fail-closed; no fallback persistence, no migration for it).
- Rejected writes: typed conflict (409), stable reason, zero mutation, no
  idempotency-key consumption.

## 4. Cross-domain identifier comparison (Codex F2)
- Never compare `role.source_generation == str(pack.version)`: video-analysis
  generation vs pack version number are unrelated concepts.
- Generation authority: `ObjectIntelligenceRepository.current_generation(
  workspace_id, role.video_item_id)`; role is current iff
  `role.source_generation == current_generation`.
- Edge cases that must hold: current gen1 + pack version 2 → NO mismatch;
  stale gen1 when backend current gen2 → mismatch; gen2 + pack v2 with backend
  current ≠ 2 → rejected.

## 5. CAS / optional-param traps (Codex F6)
- `revision: Annotated[int | None, Query(ge=1)] = None` only complies if the
  route explicitly 422s when None. Verify by reading the route body, not the
  docstring comment.

## 6. Test-only routes vs real product surfaces (Codex F3)
- `/test-s07-*` harness pages in the production app must be REMOVED once real
  integration exists. `ls frontend/src/app/test-*` to verify removal; confirm
  the production build contains no test routes.
- ProjectCastPicker-style features integrate into the REAL product page with
  real IDs from route/state (no hardcoded test IDs), reload authoritative
  mapping after success and after 409 stale-revision.

## 7. Real vertical E2E vs mocked UI tests (Codex F4)
- Mocked component tests (loading/error states via `route.fulfill`) are fine
  but MUST be labeled `MOCKED UI TESTS — NOT end-to-end` in the source header
  AND in the REPORT.
- A real vertical Scenario I: real UI route (not /test-s07-*) → real API →
  real repository → real temp SQLite → reload UI; ZERO `route.fulfill` on
  `/api/v2/project-cast*`, `/picker/packs`, `/compatibility/evaluate`.
- Seed via production API/repository with temp `MOTIONFORGE_ROOT`, not by mock.

## 8. Weak assertions (Codex F5)
- `isinstance(value, bool)` on policy results is a blocker. Assert exact
  contract: compatible=false, blocked=true, submit rejected, zero mapping rows,
  status/reason, original mapping fields, revision, idempotency-key
  availability, zero unintended mutation.

## 9. Alembic head-constant sweep
- Adding a migration changes the single head; EVERY baseline test hardcoding
  the old head fails afterwards. Before scoping the fix run
  `grep -rln <old-head> tests/` and include ALL hits in the allowlist.
- Real miss in S07: scoped 7 files, but an 8th
  (`test_s08_a02_structural_evidence_migration.py`) broke the combined suite
  and forced a second correction round. Count first, then scope.
- The T01 migration itself stays correct (one new migration, down_revision =
  old head, single new head).

## 10. Order-dependent flaky tests from shared global session factories
- Cause: tests using the app-global `deps._job_service._session_factory()` and
  seeding the same default workspace → rare (1/13 combined runs) order-
  dependent failure.
- Fix (verified): autouse per-test fixture `_s07_isolated_workspace` that
  clears the task's tables BEFORE and AFTER each test. Fail-clear, never
  weaken assertions.
- Proof: isolated repeats (22 pass ×6) + consecutive full combined runs
  (437 ×2) after the fix → flaky resolved.

## 11. Huge-session upstream timeouts (9Router / codex_responses)
- Symptom pattern at >380k-token session context: "No first byte from provider
  in 120s", `APIConnectionError`, `[WinError 10058]` socket shutdown,
  "Codex Responses stream did not emit a terminal response", slow-response
  400-800s retries.
- Recovery: probe upstream alive →
  `curl -s -o /dev/null -w "%{http_code}" -m 20 http://127.0.0.1:20128/v1/models`
  (must be 200); then resume the SAME session with a TERSE continue prompt
  ("only these remaining steps: 1) ... 2) ... finish SUBMITTED").
- A user-mandated model switch mid-sprint works with
  `hermes chat --resume <id> --provider custom --model alpha -q "..."` —
  session history survives provider/model changes. Verify the new model first
  with a one-shot probe (`hermes chat -q "..." --provider custom --model alpha
  --yolo --pass-session-id --source tool -Q`).
- Model `alpha` on 9Router self-identifies as `ox-alpha`
  (openrouter/stealth/ox-alpha); it has no config alias — pass the raw id.

## 12. Null bytes inside Python literals
- `data = bytes.fromhex("89504e470d0a1a0a") + b"\x00" * 10` contains the TEXT
  `\x00` inside a string literal — that is NOT file corruption. `grep`/`cat -v`
  will show "null bytes"; use `python -m py_compile <file>` as the syntax
  arbiter. Do not burn turns rewriting literals.

## 13. Manager adversarial verification checklist
- Re-run every suite yourself (writer counts are self-reports).
- Grep for forbidden comparisons (`source_generation.*str(pack.version)` →
  must be zero hits).
- `ls` removed test routes; grep `canSubmit`-style gates in frontend source;
  check DELETE 422-on-None in the route body.
- Use file mtimes (`ls -la --time-style=full-iso`) to prove WHICH session
  touched which file — an interrupted resume that wrote nothing is safe to
  re-resume; a no-op `onCast={() => {}}` in a real integration is a flag to
  check whether the real picker is rendered elsewhere.
- Gates: ruff 0, mypy 0, alembic single head, git diff --check 0, frontend
  typecheck/eslint/build, OpenAPI $ref-typed schemas, protected hashes
  (channels.json, data/motionforge.db) unchanged, MAIN HEAD unchanged,
  no listeners/writers.

## 14. MSYS / Windows operational notes (this machine)
- `tee -u` is NOT supported on MSYS (`unknown option -- u`) — use plain `tee`
  or per-run `> run$i.log` redirects; always `mkdir -p` the evidence dir first
  or the tee fails silently.
- Foreground pytest combined suites can exceed the 600s tool cap — run them
  background with `notify_on_complete=true`.
- 9Router CLI quirk: `hermes --resume` opens the TUI (NoConsoleScreenBufferError
  in background) — the working pattern is `hermes chat --resume <id> ... -q`.

## 15. Fail-open authority broad-catch (C3-P1, verified pattern)
- `except Exception: <authority_result> = None` around a backend-authority
  call is ALWAYS fail-open: an outage becomes "skip the check" and writes
  succeed while the source of truth is broken. If the repository contract is
  "returns a value OR raises a typed NotFound", the no-data case is already
  represented as a VALID value — any remaining broad catch only swallows real
  errors. Fix: keep ONLY the typed except; let everything else propagate so
  the API returns 5xx, never 2xx-on-broken-authority.
- Regression protocol that Codex accepts: new test monkeypatches the authority
  to raise RuntimeError; assert status >= 500, DB rows unchanged (query real
  state), idempotency key NOT consumed, retry with the SAME key succeeds.
- Mutation ordering matters: the evaluate/authority check must run BEFORE
  `session.add/flush` — prove it with line numbers when reporting.

## 16. Weak assertions are P2 findings every round (C3-P2 / C4-P2)
- Patterns Codex flags: `assert x == "1" or x == "2"`, `if cond: ... else:
  pass`, `or not j["compatible"]` (tautology — passes whenever the test's own
  premise fails). Sweep candidates with grep before submitting; exact-value
  asserts + deterministic seed construction (fixed SHA sources, completed
  jobs) are the expected fix.

## 17. Client-controlled workspace = P1 security finding (C4)
- A handler parameter `workspace_id: str = SOME_DEFAULT` in FastAPI becomes a
  CLIENT QUERY PARAMETER — the default does not make it server-owned. Probe
  truth via `/openapi.json` (TestClient(app).get("/openapi.json")) and list
  every `(method, path, param)` triple; any `workspace_id (in=query)` on a
  multi-tenant surface is a finding even if behavior is currently safe.
- Fix: remove the parameter from signatures; use the server-owned constant
  inside the body or a client-input-free dependency. Regression: OpenAPI
  assert zero workspace_id parameters + adversarial request
  `?workspace_id=<other-real-workspace>` proving authority unchanged.

## 18. Cross-workspace existence oracle (C4)
- Natural-key lookup without a workspace filter leaks existence: occupied
  pair → 409 Conflict, unoccupied → workspace_mismatch. Two different
  responses for in/out-of-workspace state = information disclosure.
  Fix: scope EVERY lookup by workspace_id first; cross-workspace requests
  must get ONE consistent fail-closed result regardless of occupancy.
  Regression must cover BOTH occupied and unoccupied cases with zero-mutation
  asserts.

## 19. Multi-wave correction bookkeeping (manager)
- Each wave gets its own evidence dir (`output/<task>-c<N>/<run-id>/`) and
  its own prompt file in Temp; worker log named
  `<ts>_worker-c<N>.log`. Watchdog glob list must be extended per-wave
  BEFORE dispatch (patch WATCH_GLOBS, restart watchdog).
- Long sessions compact on resume ("Preflight compression ~200k tokens" pause
  of several minutes right after dispatch) — this is NORMAL, not a hang;
  audit at 8 min, don't panic-resume at 2.
- Attribution audit for out-of-scope file changes in the run window: check
  git tracked status (`??` = untracked lane), grep the worker transcript for
  the filename, and match mtime against OTHER active lanes before declaring a
  scope violation. Parallel sprint lanes legitimately touch their own files.

## 20. Test-harness process-ownership for leak/orphan checks (S11 R3/R4)
- Machine-wide name-only scans (`psutil.process_iter` matching "ffmpeg") make
  two concurrently-running suites blame each other's processes as orphans.
  Ownership needs TWO independent signals agreeing: (1) process-tree — pid is
  a recursive descendant of the current pytest process, AND (2) cmdline
  marker — the run's unique managed-root/basetemp path appears in the
  process command line.
- Descendants-only checks still miss re-parented processes: once the direct
  parent dies, an orphan leaves the descendant set and a scan-at-assert-time
  silently drops it (false-negative leak gate). Re-parent-proof pattern:
  snapshot owned PIDs AT SPAWN TIME (wrap the engine's `subprocess_popen` to
  record pids of ffmpeg/ffprobe children) plus a low-frequency sampler thread
  while the engine runs; after exit, poll exactly THAT fixed pid-set via
  `psutil.Process(pid)` until each is gone or a bounded deadline lapses —
  no parent relationship required at poll time.
- Guard Windows PID reuse: a recorded pid that comes back alive must ALSO
  match the expected binary name, else count it as exited.
- Never fixed-sleep over teardown races; bounded polling with hard deadline.
- Cross-run isolation regression Codex accepts: two real pytest invocations
  with separate basetemp+managed roots running simultaneously, each asserting
  its own scope reports CLEAN while the sibling provably has live processes.

## 21. Nested-pytest PIPE deadlock (acceptance harness)
- Symptom: OUTER test spawns INNER `python -m pytest` with stdout/stderr=PIPE
  but only polls `child.poll()` without draining streams and without a total
  deadline. INNER finishes all tests (py-spy: MainThread idle in
  `_pytest/config/__init__.py` `_console_main`, ~0 CPU) yet never exits —
  blocked writing to a full pipe — and OUTER waits forever (observed 80+
  min).
- Fix: dedicated reader threads drain BOTH streams into buffers while the
  poll loop runs, plus ONE hard wall-clock deadline for the whole child run;
  on expiry kill the child, harvest partial output, and fail the test with
  both bounded tails + "[harness] child killed at <N>s" note.
- Diagnosis tooling: `pip install py-spy`; `py-spy dump --pid <pid>` (and
  `--nonblocking`) distinguishes "still working" vs "finished but stuck";
  psutil cpu-times delta over a few seconds proves true idleness; PowerShell
  `Get-Process ... Threads` WaitReason corroborates.
- Corollary: any long-lived subprocess wrapper needs a total deadline — a
  per-read timeout is not enough when the hang is in the child's exit path.

## 22. Cross-lane expectation ripple → route, don't cross-edit
- A correctness fix in one owner's write-set can invalidate ANOTHER task's
  test expectation even when both are fail-closed (real case: adding a
  source-hash preflight moved same-size-mutation rejection earlier, changing
  the observed code from ENGINE_FAILED to SOURCE_NOT_READY in a different
  task's integration test).
- Protocol: worker reports the ripple + evidence; MANAGER verifies semantics
  are preserved (still fail-closed, zero publication, clean staging), then
  dispatches a mini-correction resuming the OWNING session of the stale test
  with an explicit expectation-update instruction. Workers never edit files
  outside their own write-set, even for "obvious" expectation bumps.

## 23. Source-artifact integrity checkpoints (same-size mutation class)
- Size-only validation of a cached/checkpointed artifact defeats itself:
  same-length different-bytes mutation returns True. Verify SHA-256 at EVERY
  trust boundary: first resolve (disk hash == DB artifact hash), checkpoint
  reuse (size AND hash re-hashed from disk), post-engine (engine-reported
  source hash and post-engine source hash match evidence), and immediately
  pre-publication (disk-now vs recorded; drift list in error details).
- Failure shape Codex accepts: stable existing error envelope, typed code,
  details naming expected sha256 + mismatch sources, ZERO rows/files written,
  staging cleaned scoped to THIS run only (rmtree of own engine dir, not the
  shared managed root).

## 24. Session-specific detail
See `references/s07-correction-waves-c3-c4.md` for the S07 C3/C4 trail and
`references/s11-t01-correction-rounds-r3-r4-c3.md` for the S11-T01 R3/R4/C3
trail (process-ownership leak gates, nested-pytest PIPE deadlock diagnosis,
cross-lane expectation ripple routing, source-integrity checkpoints).
See `references/s07-correction-waves-c3-c4.md` for the full S07 C3/C4
finding/evidence trail (file:line, probes, gate numbers).

## 25. Global gates vs writer-scoped gates; late edits invalidate green runs (S07 round 2, 2026-08-22)
- Writers ran focused lints on their own files and passed, yet repo-wide gates
  found NEW errors: `ruff check app tests` → 19 I001 in one new test's inline
  import block; `eslint .` → 4 no-explicit-any + 1 unused var across two spec
  files; `tsc --noEmit` → 2 TS18047 ('possibly null') introduced by the
  eslint-fix correction itself (removed an unused var but left unguarded
  `patchBody.x` reads).
- Corollary 1: after EVERY writer exits, run the FULL matrix yourself
  (ruff app+tests, mypy app, `npx tsc --noEmit`, `eslint .`, `next build`) —
  writer-scoped lint runs are not proof of repo-wide cleanliness.
- Corollary 2: any edit after a green gate invalidates it. A 17:54 spec edit
  silently voided the 17:43 tsc gate; only the final re-run caught it.
  Re-run the whole battery after the LAST change of the round; compare file
  mtimes against gate-log timestamps before citing a result as current.
- Corollary 3: verify writer smoke evidence — a REPORT claimed "SMOKE PASS"
  while its own smoke.log contained a Traceback (NoneType `_session_factory`).
  Grep raw logs for Traceback/EXIT codes; a broken ad-hoc smoke script must be
  replaced by real pytest/PW gates run by the manager, not narrated around.
- `npx tsc --incremental=false` is NOT a valid flag (TS5023 Unknown compiler
  option) — use plain `npx tsc --noEmit`.

## 26. BLOCKED_DEPENDENCY as designed evidence + parallel correction waves (S07 round 2)
- Dependency-ordered verification: T03's repin-via-UI real vertical ran BEFORE
  T02's production fix landed and failed 0/4 — that red run is the EXPECTED
  BLOCKED_DEPENDENCY_T02 evidence, not a defect. State the predicted outcome in
  the worker prompt; re-run the dependent suite after the upstream fix lands to
  convert BLOCKED → PASSED (0/4 → 4/4 proved both fixes end-to-end).
- Parallel wave: two corrections (T02 backend+picker, T03 e2e-only) dispatched
  simultaneously with disjoint write-sets AND disjoint ports (T02 self-managed
  8014/3024; T03 standard 8004/3014), temp roots and basetemps; global gates
  only after BOTH writers exited (mutex). Read-only static checks may overlap
  the pytest battery; PW suites run serially after everything settles.
- Mini-correction dispatch that worked: tight single-defect prompt file in
  Temp → `PROMPT=$(cat …) && hermes chat --resume <owner-sid> --provider muse
  --model ocg/muse-spark-1.2-contributor -q "$PROMPT" --yolo --pass-session-id
  --max-turns 60 --source tool > log 2>&1` as background+notify; ALWAYS resume
  the same owner session (C4b/C4c/C4d and C2b each took 4-20 min).
- Alembic on a temp DB: `-x db_url=` is NOT honored by this project — export
  `MOTIONFORGE_DATABASE_URL="sqlite:///<temp>/x.db"` AND `mkdir -p` the parent
  dir first (SQLite "unable to open database file" if the folder is missing).
- Don't assume test filenames for regression clusters — `ls tests/ | grep`
  first (guessed `test_s06_surface_api.py`-style names do not exist; the real
  cluster is channel×2, video_item, s08 taxonomy/structural-evidence/security/
  root-resolution).
- Full round-2 trail (fallback matrix, repin-via-UI, gate-catch sequence,
  final battery numbers): `references/s07-correction-round2-fallback-repin-ui.md`.