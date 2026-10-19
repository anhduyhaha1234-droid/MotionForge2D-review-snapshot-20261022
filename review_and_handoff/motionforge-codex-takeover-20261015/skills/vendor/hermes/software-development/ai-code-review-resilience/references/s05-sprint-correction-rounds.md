# Sprint S05 Correction Rounds C01→C04 — Session Evidence (2026-08-05)

Full chronology of an adversarial Codex review loop on the MotionForge2D S05
sprint. Each round's reviewer finding, the root cause, and the fix that
satisfied the reviewer. The systematic root cause: every pre-C01 test
monkeypatched `deps._job_service` / `deps._lifecycle_db`, so the real
production path was never exercised; each round forced tests one layer closer
to production and exposed a new real defect.

## Round C01 — CHANGES_REQUESTED (approved-pipeline orchestration)

Findings:
1. S05-T05 UI called `POST /api/projects/{id}/ingest` — legacy
   probe→PySceneDetect→slicing pipeline, NOT the approved chain
   T02 ANALYZE_MEDIA import → T03 GENERATE_PROXY → T04 scene_detect.
2. Retry was not functional: re-submitting the legacy endpoint returned
   500 IdempotencyKeyInUse; rendering that refusal honestly did not satisfy
   the retry acceptance criterion.

Fix: UI-facing orchestration endpoint driving the real T02→T03→T04 durable
jobs with backend-owned chain state; successor-job retry (§8.5) with owner
validation + idempotency. Evidence: 12 orchestration tests; baseline 7/7
`20260805-152346`; Playwright 6/6+6/6.

## Round C02 — CHANGES_REQUESTED (durable chain progression)

Reviewer quote: "Do not approve a pipeline merely because tests call
helper/read endpoints that secretly advance it. Read-only endpoints must not
mutate state."

Findings:
1. `GET /api/projects/{id}/analyze` created proxy/scene-detection Jobs — not
   read-only.
2. Chain progression lived in the projects route and accessed JobService
   private members.
3. Chain identity not bound to immutable input evidence (source SHA-256 +
   generation) — replacing the source could silently reuse stale results.

Fix: read-only GET (zero mutations verified); chain progression moved into a
focused durable orchestration service (`app/workflow/analyze_orchestrator.py`);
chain identity bound to source SHA-256 + generation; adversarial tests
(POST-once-no-GET completes chain; API restart after import/proxy; GET
concurrent zero mutations; source replacement not reused; one successor per
step). Evidence: 9 chain-progression + 12 orchestration + 271 regressions;
baseline 7/7 `20260805-163430`.

## Round C03 — CHANGES_REQUESTED (final lifecycle)

Findings:
1. Orchestrator started only via POST `ensure_started()` — not wired into the
   FastAPI app lifespan; startup must scan and resume incomplete chains
   without POST/GET/polling/manual `advance_once()`.
2. No true process-lifecycle test (shut down app → fresh app over same DB →
   no API request → chain completes; repeat after proxy).
3. Source replacement with different SHA must produce a NEW chain (explicit
   VideoItem/version/supersession), old evidence immutable, chain state
   exposes only current source.

Fix: lifespan wiring (startup scan/resume; shutdown stop orchestrator before
worker); 3 lifecycle tests (restart after import, after proxy, supersession);
live crash-restart smoke. Evidence: baseline 7/7 `20260805-181617` (719
passed); Playwright 6/6+6/6.

## Round C04 — CHANGES_REQUESTED (production job service wiring)

Confirmed defect: `deps.get_job_service()` constructs default `JobService()`
whose constructor creates a DurableWorker bound to a placeholder factory that
raises `RuntimeError("job service not initialized")`; `initialize()` creates
the real factory but never rebinds the worker; `start_worker()` starts the
stale placeholder-bound worker. App also inspected private JobService
attributes to infer factories/roots.

Fix: public explicit lifecycle binding contract; pristine production-wiring
test `tests/test_s05_production_wiring.py` (temp root, real app.main:app,
real lifespan, 4 fresh-process generations, no DI, no monkeypatch, no
"job service not initialized"). Evidence: pristine 1 passed (22.53s);
5-file suite 34; regressions 297; Playwright/baseline deferred per AC7.

## Round C04-R2 — CHANGES_REQUESTED (correction round 2)

Findings:
1. **BLOCKER — competing/cached orchestrator factory**: analyze_orchestrator
   still created a separate factory when `JobService.session_factory is
   None`, cached by object identity; if `get_analyze_orchestrator()` ran
   before `initialize()`, the cache permanently kept the competing factory.
   Fix: remove fallback → fail-closed (raise); factory/root come ONLY from
   the initialized public lifecycle binding; regression test
   `tests/test_s05_orchestrator_binding.py` (access before init → init →
   obtain → prove authoritative factory used; no stale cache).
2. **BLOCKER — restart test lacked stage boundaries**: assert gen1
   proxy=0/scene=0, gen2 proxy=1/scene=0, gen3 scene=1, gen4 no duplicates;
   test must FAIL if successors complete before the intended restart.
3. **Omitted verification**: Playwright desktop + mobile/390px + fresh 7/7
   baseline must run with NEW isolated C04 temp root/evidence dirs; if safe
   isolation impossible → BLOCKED, never claim pass.
4. **Status inconsistency**: LOG.md stayed "Status: READY" while TASK/REPORT
   said SUBMITTED. Fix: flip ALL THREE status lines; append correction-round
   section; never rewrite prior evidence.

Evidence: binding 2 passed; pristine+lifecycle 4; 5-file suite 34; durable/S05
297; baseline 7/7 `20260805-203459` (722 passed); Playwright desktop 5/6
(cancel E2E race documented honestly — backend cancel path green via pytest)
+ 390px 6/6 + 10 new screenshots in `output/s05-c04-r2-evidence/`.

## Round C04-R3 — CHANGES_REQUESTED (correction round 3)

Findings:
1. **RED gate — cancel user flow not reliable**: desktop interaction
   `5 passed, 1 failed`; cancel test reproduced failure 2/2; ZERO /cancel
   requests reached the backend. UI derived the cancel target (active job id)
   from a polled chain snapshot; during import→proxy→scene transitions the
   snapshot went stale before handleCancel dispatched → click sent no request
   or targeted a terminal job. Reviewer explicitly forbade: sleeps, slowing
   production processing, enlarging fixtures, removing assertions, marking
   flaky. Required: smallest robust design — re-resolve chain state at cancel
   time + safe retry when the observed job became terminal, OR an atomic
   project-chain cancel API that resolves the active job server-side; fail
   honestly when genuinely completed; preserve idempotency + GET read-only.
   Evidence required: cancel reaches the real isolated backend; job enters
   cancelling/cancelled; retry available; no successor/orphan; 3 consecutive
   passes; full desktop suite 6/6; 390px cancel variant.
2. **Binding test not fully isolated**: default-JobService test's managed
   root `Path("artifacts")` resolved into the worktree under pytest CWD, not
   tmp_path. Fix without weakening the production-default assertion:
   `monkeypatch.chdir(tmp_path)` (or fresh-process boundary); assert resolved
   root inside tmp_path; assert no worktree/root artifacts dir created;
   keep session-factory identity + fail-closed assertions; all test files/DBs
   under pytest temp storage.
3. **Visual completion evidence internally inconsistent**: completed
   desktop/mobile screenshots showed step 3 labelled 100% while its progress
   bar was still partially rendered. Determine CSS-transition vs product-bug;
   if transition-only wait for full-width bar before capture; if product bug
   fix smallest rendering issue; add assertion every completed step displays
   100% AND visually full bar; regenerate only C04-specific screenshots in
   new evidence dirs.

In-flight at session end: runner dispatched to fix all three; manager
verification pattern for this round = same independent re-run + grep the code
for the removed stale-snapshot cancel path + chdir isolation proof + screenshot
bar-width assertion.

## Cross-cutting lessons (see SKILL.md checklist)

- DI tests hide production wiring defects — pristine no-DI test from the
  first task.
- Read-only endpoints truly read-only; retry = successor; lifespan-owned
  lifecycle; immutable-input chain identity; stage-boundary assertions;
  fail-closed cached factories; deferred verification = rejection; status
  lines consistent; baseline on final code.
- Windows dispatch: short quote-free prompts; one runner instance at a time;
  wrapper PID ≠ worker PID; `Set-Location` not inherited by CLI workers.
