# S08 Correction Cycle (2026-08-16) — Codex CHANGES_REQUESTED full-cycle pattern

Codex rejected the S08 sprint exit with a FULL correction cycle, not a single
round. This file distills (1) the execution-shape rules and (2) the A–G
findings as a predictive checklist for future sprint exits.

## Execution shape (new, differs from S05 single-round corrections)

- Two NEWLY AUTHORIZED Task IDs (S08-R01-runtime-lifecycle-safety,
  S08-H01-production-authority) → materialize TASK/START_PROMPT/LOG/REPORT
  packets FROM the Codex prompt BEFORE launching; brand-new sessions; record
  exact new session IDs; never reuse a closed/existing session.
- EXISTING Task IDs (T02/T03/T04/T05/T06) → resume their EXACT stored
  session IDs (T02 20260816_140218_d4c20a, T03 20260816_151439_21e306,
  T05 20260816_185020_83fd62, T04 20260816_170337_74161b,
  T06 20260816_203312_e9f2b). Append correction rounds to existing LOG/REPORT.
- EXECUTION ORDER IS REORDERED BY DEPENDENCY, not task number:
  R01 → T02 → T03 → T05 → **T04** → H01 → T06. T04 (gallery) resumes only
  after T02/T03/T05 backend contracts are manager-verified, because it
  consumes their new contracts. Always derive order from the Codex packet,
  never from numeric order.
- Model policy: new sessions use the current pinned worker model; resumed
  sessions keep the session's original model (a resume is not a "new session").
- New protected asset class in the baseline: read-only SAM2.1 checkpoint
  `models_checkpoints/sam2.1_hiera_large.pt` — never modify/copy/replace/
  regenerate; QA smoke must be read-only + isolated output.

## Findings A–G distilled (predictive checklist for the next sprint exit)

A. **Generic lifecycle, not handler patches:** queued-cancel must reach
   terminal `cancelled` deterministically (zero effects, no orphan lease, no
   pending-forever). Managed artifact root must come from the CONFIGURED
   absolute project root (never process CWD) across worker/reconciler/
   orchestrator/API/manifests. QA/test mode must REJECT the protected MAIN
   root and require an explicit absolute isolated root. QA launchers must not
   rely on `cd` for storage correctness.

B. **Real production provider, no stub:** functional local-first
   implementation (SAM2.1 checkpoint) decoding real frames into real
   masks/crops/occurrences; inference ONLY inside the durable worker; no
   download/network fallback; fail closed on missing capability.
   Deterministic provider is QA/test-only and must NOT be selectable via
   request JSON in production. `available()` must verify a real locator/
   capability, not a non-empty env string. Stable candidate/role IDs — display
   names never identity. Durable ObjectRole↔Artifact association (forward
   migration + round-trip). Contained content endpoint: ManagedRoot-only
   resolution, no client paths, allowlisted MIME, size/hash check, ETag from
   SHA-256, `X-Content-Type-Options: nosniff`, 404/409 for missing/stale/
   non-ready. Backend-authoritative lookup of current completed extraction
   (no browser-storage requirement). Source-generation filtering for gallery/
   grouping. Real read-only GPU smoke with honest perf/memory numbers.

C. **Current-generation grouping:** group only the explicit current
   video/source generation; stable role IDs in every suggestion/operation;
   display name never identity authority; backend-exposed policy metadata
   (algorithm version, confidence semantics, review threshold, calibration
   version); everything advisory — never auto-confirm/auto-merge; adversarial
   tests: duplicate names, renamed roles, cross-generation.

D. **Correction media becomes canonical:** RECOMPUTE publishes replacement
   media links for affected stable role IDs; gallery/API resolves newest valid
   media; unaffected bytes/hashes identical; superseded artifacts auditable
   but not current; rename-only correction must not lose media;
   geometry/reassign must show regenerated media after completion AND after
   app/browser restart; cover queued cancel; preserve retry/fencing/
   idempotency/concurrency/impacted-scope-preview/no-orphan.

E. **Real media + scalable gallery:** no matching by candidate.name/role.name;
   render real bytes via the stable content URL; tests assert decoded
   `naturalWidth/naturalHeight` (not labels/MIME text); fresh browser with
   empty sessionStorage must restore roles/extraction/media from backend
   truth; source replacement never shows previous-generation media; explicit
   project video selector for multi-video projects; confidence/review
   thresholds from backend policy metadata (no duplicated hardcoded 0.65/0.5
   in UI); paginate/infinite-load role summaries, fetch heavy occurrence
   detail on expand (never eagerly render 200 occurrence-heavy roles); split
   the 1,611-line panel into bounded hooks/components; preserve a11y/dialog/
   focus-return/loading/empty/partial/stale/error/retry/cancel/390px states.

F. **Production authority (frontend):** remove fabricated fallback project/
   video data; API failure → honest error/retry/not-found; project/video
   identity from durable backend + URL (never Zustand/localStorage as sole
   truth); LegacyWorkspace may not fabricate projects/videos, must hydrate +
   validate durable IDs; project detail → processing → gallery navigation
   preserves selection explicitly; desktop + 390px tests for API failure,
   retry, refresh, multi-video navigation; no S06 redesign.

G. **True vertical golden:** brand-new root/DB; real `app.main:app` + real
   lifespan; NO `deps._job_service`/`deps._lifecycle_db` injection; import →
   analyze → discover → group → correct → render all through real public
   APIs; primary vertical roles NOT seeded via the T01 role-creation API; the
   QA provider must emit a meaningful cross-scene identity case so T02 output
   itself feeds T03 grouping; prove T02→T03→T05→gallery, real thumbnail/mask
   decoding, app restart over same DB/root, browser restart without
   sessionStorage, no duplicate effects, source replacement/current-generation
   isolation, stable ID after rename + duplicate display names, queued AND
   running cancel, retry/successor, correction media refresh, unaffected
   hashes byte-identical, no "job service not initialized" loop. Separate
   metrics honestly: deterministic contract correctness vs provider quality
   vs grouping precision/recall/false-merge vs calibration (Brier/ECE only if
   sample size permits). Never derive a quality threshold from the same
   observed output and call it independent; never claim real-world accuracy
   without a labeled dataset. SAM2.1 GPU smoke as a SEPARATE integration gate
   (read-only checkpoint, isolated output). New screenshots under a NEW Run
   ID (never overwrite T04/T05/T06 evidence). Launcher scripts via PowerShell
   Parser / `bash -n` / functional smoke — never pytest.

## Reporting rules that Codex enforces verbatim

- Preserve all old LOG/REPORT content; append honest correction evidence.
- Record every Task ID, session ID, correction round, command, result, run
  root, port, Quality Run ID.
- Explicitly list any test not run and why.
- Do NOT call a configured-but-nonfunctional provider "production ready".
- Do NOT call metadata tiles "thumbnail/mask rendering".
- Do NOT call role-seeded tests a vertical extraction proof.
- No writer/process active at submission; every corrected task SUBMITTED or
  MANAGER_VERIFIED_PENDING_SPRINT_REVIEW; SPRINT_REPORT = SPRINT_SUBMITTED;
  stop; tell the owner the cycle is ready for ONE Codex sprint-exit review.

## Progress log (manager-maintained, 2026-08-16/17)

- **R01 — DONE, MANAGER_VERIFIED_PENDING_SPRINT_REVIEW.** Session
  `20260816_225849_3788f0` (pro-max, 45m, exit 0). Generic fix: `drain` flag
  on the durable_worker claim path (all job types), root resolution from
  configured absolute project root, QA fail-closed reject MAIN root.
  Manager independent: focused 18/18 (6.26s) + durable regressions 121/121
  (73.07s) + S05 wiring/lifecycle 4/4 (45.74s). Scope: config.py, deps.py,
  durable_worker/job_reconciler/job_service.py + 2 new test files +
  test_s05_orchestrator_binding.py update; `app/lifecycle.py` and
  `app/api/app.py` NOT touched. Protected unchanged.
- **T02 correction (finding B) — IN FLIGHT** since 2026-08-17 09:41: resume
  session `20260816_140218_d4c20a` (flash), launcher `output/run-s08-t02-c1.ps1`,
  log `output/s08-t02-c1-hermes.log`, watcher MAIN
  `scripts/watch-s08-t02c1.sh`. Findings: SAM2.1 production provider,
  deterministic=QA-only, stable media identity, role↔artifact association
  migration, content endpoint, source-generation filtering, GPU smoke.
- T03/T05/T04/H01/T06: NOT STARTED at time of writing.
