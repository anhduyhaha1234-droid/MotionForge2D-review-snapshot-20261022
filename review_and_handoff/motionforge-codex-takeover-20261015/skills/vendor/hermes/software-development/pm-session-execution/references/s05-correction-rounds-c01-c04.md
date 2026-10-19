# Sprint S05 correction chain C01 → C04 (verified 2026-08-05)

Codex rejected the S05 sprint exit four times. Each round's findings are
quoted from the actual CHANGES_REQUESTED prompts so a future session can
recognize the same review patterns.

## C01 — "SPRINT S05 EXIT CORRECTION — CHANGES_REQUESTED"

Blockers:
1. The S05-T05 UI calls `POST /api/projects/{project_id}/ingest`. That
   endpoint creates the legacy "ingest" job and runs the old
   probe → PySceneDetect → scene slicing pipeline. It does not drive the
   approved S05 pipeline: S05-T02 ANALYZE_MEDIA import → S05-T03
   GENERATE_PROXY → S05-T04 ANALYZE_MEDIA scene_detect.
2. Retry is not functional. Re-submitting the same legacy ingest endpoint
   returns 500 IdempotencyKeyInUse. Rendering that refusal honestly does not
   satisfy the retry acceptance criterion.

Fix: approved API orchestration driving real T02→T03→T04 + successor-job
retry (owner validation, idempotency, refetch).

## C02 — "S05-C02 — DURABLE CHAIN PROGRESSION CORRECTION"

Codex: "Manager verification must test the acceptance outcome adversarially.
Do not approve a pipeline merely because tests call helper/read endpoints
that secretly advance it. Read-only endpoints must not mutate state."

1. GET /api/projects/{id}/analyze must be read-only — must not create proxy
   or scene-detection Jobs.
2. After exactly one POST /analyze, the T02→T03→T04 chain must progress under
   worker/reconciler ownership even when the browser closes immediately, no
   GET polling occurs, and the API process restarts between steps.
3. Move chain progression out of the projects route into a focused durable
   workflow/orchestration service; no JobService private members from routes.
4. Bind chain identity to immutable input evidence: source SHA-256 +
   generation/version. Replacing the project source must not silently reuse
   results from the previous video.
5. Independent tests: POST-once-no-GET; API restart after import and after
   proxy; GET repeated/concurrent → zero DB mutations; replace source → stale
   chain not reused; concurrent advancement → exactly one successor per step;
   failure/cancel successor retry idempotent; CFR/VFR + containment + SHA/size
   + Scene IDs + orphan cleanup regressions.

## C03 — "S05-C03 — FINAL LIFECYCLE CORRECTION"

1. Start and stop AnalyzeChainOrchestrator through the real FastAPI
   application lifespan. On startup it must scan and resume incomplete chains
   WITHOUT POST, GET, browser polling or manual advance_once() calls.
2. True process-lifecycle test: POST once → complete only import → fully shut
   down the first TestClient/app lifespan → fresh app/TestClient over the same
   database → issue no analyze API request → prove proxy and scene jobs
   materialize and complete. Repeat restart after proxy.
3. Replacing a source with different SHA must produce a NEW valid chain that
   reaches completed; do not overwrite or silently reuse old Scene evidence;
   explicit VideoItem/version/supersession lifecycle.
4. Test: old jobs/artifacts/scenes immutable; new source distinct identity +
   outputs; new chain completes; chain state exposes only current source.

## C04 — "S05-C04 — PRODUCTION JOB SERVICE WIRING" (the root cause)

Confirmed defect (from the packet):
`deps.get_job_service()` constructs default `JobService()`. Its constructor
creates a `DurableWorker` bound to a placeholder factory that raises
`RuntimeError("job service not initialized")`. `JobService.initialize()` later
creates the real service factory, but does not rebind/rebuild that worker.
`start_worker()` therefore starts the stale placeholder-bound worker.
Current `app/api/app.py` and the process-wide analyze orchestrator also
inspect private `JobService` attributes to infer factories/roots.

Key constraints for the fix:
- app.py must not read/patch/infer private JobService attributes.
- No competing engines/session factories; JobService, DurableWorker,
  JobReconciler, AnalyzeChainOrchestrator share ONE authoritative factory +
  managed root.
- Pristine production-wiring test: temp configured root only; no
  `deps._job_service` / `deps._lifecycle_db` assignment or monkeypatch; real
  `app.main:app` default dependency path; real FastAPI lifespan; POST analyze
  exactly once; prove default DurableWorker claims/completes T02→T03→T04;
  full shutdown; second lifecycle over same temp DB with genuinely fresh
  production module/singleton state (subprocess); no second POST, no manual
  advance_once; startup-owned resume completes; no duplicate jobs/artifacts/
  durable effects/Scene rows; old identifiers stable across restart; capture
  worker-loop logging and assert "job service not initialized" never occurs.
  "Merely opening two TestClient contexts over the same already-bound
  singleton is insufficient evidence of production restart."

## C04 round 2 — "CODEX REVIEW CORRECTION ROUND 2" (CHANGES_REQUESTED again)

1. BLOCKER — competing/cached orchestrator factory: analyze_orchestrator.py
   still created a separate factory when `JobService.session_factory is
   None`, then cached the orchestrator by JobService object identity. Codex
   reproduced: `fallback_is_service_factory=False`,
   `cached_orchestrator_same=True`,
   `cached_orchestrator_uses_service_factory=False`. Fix: remove the
   competing-factory fallback; factory + managed root only through the
   initialized public JobService binding; fail-closed or explicit public bind
   replacing stale bindings; no private reads; regression test that
   access-before-init → initialize → obtain/start → proves the exact
   authoritative factory + root, and no stale cached orchestrator survives.
2. BLOCKER — restart test must enforce stage boundaries: gen1 POST once,
   import completes, proxy=0/scene=0, full shutdown; gen2 no analyze POST/no
   manual advance, startup resumes proxy, scene=0, full shutdown; gen3
   startup resumes scene; gen4 no duplicates. Fresh subprocess/module state +
   same temp DB every generation. Test must FAIL if successors complete
   before the intended restart.
3. Required verification omitted: Playwright desktop, Playwright mobile/390px,
   fresh 7/7 baseline — run them with NEW isolated C04 temp root/evidence
   dirs; never overwrite existing screenshots/reports/.last-run.json/fixtures/
   DBs/quality runs; stop BLOCKED if isolation can't be established.
4. Status inconsistency: LOG.md still "Status: READY" while TASK/REPORT said
   SUBMITTED — change ONLY the LOG status line, append correction section,
   never rewrite history, never APPROVED.

## The pristine production-wiring test recipe (from the C04 worker)

- MOTIONFORGE_ROOT → a `tempfile.mkdtemp()` root; DB under
  `root / "data" / "motionforge.db"`; artifacts under `root / "artifacts"`.
- Each "generation" = a fresh `subprocess` running a small script that
  imports `app.main`, builds the app, enters the real FastAPI lifespan
  (TestClient context manager), does its one action, exits. Same root passed
  across generations → same DB.
- gen1: upload real isolated fixture (e.g. 4s CFR mp4) via the video upload
  route, POST /analyze exactly once, then poll-assert (inside the subprocess)
  import completed; assert proxy job count 0 and scene rows 0 at shutdown.
- gen2: start fresh process over same root; NO analyze calls; wait for the
  lifespan's startup scan to resume; assert proxy=1 completed, scene=0.
- gen3: same again; assert scene rows materialize and complete.
- gen4: same again; assert job/artifact/Scene counts unchanged (no
  duplicates); assert staging dirs clean.
- Capture worker-loop logs and assert the literal string
  "job service not initialized" never appears.
- A single pytest function orchestrates the subprocess generations; the test
  takes ~22s and is the strongest evidence the default production path works.
