# Manager-mode: multi-wave sprint orchestration (full-sprint C1/fast-track class)

Lessons from S09 full-sprint + S09-C1 fast-track (Aug 2026). Apply when acting as
Hermes Manager over many worker sessions with waves, join gates, and a Codex gate.

## Session-ID resolution (never trust memory)
- Owner session IDs come from the CURRENT Codex prompt. Verify each exists and is
  resumable by querying the Hermes state DB (`SELECT id FROM sessions WHERE id=?`)
  AND checking the first user message matches the expected task before resuming.
- Wrong-owner resume silently corrupts attribution — reviewers check for this.

## Workers die mid-work with EXIT=0 constantly
- Causes seen: upstream model returns empty content ("No reply: empty content after
  retries"), transient router drops, lazy-refresh venv warnings then stall.
- Signature: log size frozen, no wrapper `EXIT=` line appended, process gone.
- ALWAYS verify disk state yourself (files written, tests run) BEFORE writing the
  resume prompt; name the exact stopping point ("you were patching X; Y/Z already
  written") so no work is redone.
- For repeat offenders: SHORTER step-numbered resumes ("do step 1, log it
  immediately") and instruct the worker to log each small step so progress
  survives interruptions. Long resumes die again.

## Join gates between workers
- When the prompt defines joins (contract freeze J1, production-API mount J2),
  verify conditions then IMMEDIATELY resume the SAME owner session with a
  "PHASE 2" prompt naming the gate that opened. Don't batch with other actions.
- Watch for cross-worker write-set bleed: a mypy error in file A may be caused by
  worker B editing a shared import in-flight (e.g. select_route signature change).
  Attribute to the in-flight owner in the registry and re-check at final gate
  instead of blocking.

## Full-sprint regression gating
- Run full regression WITHOUT `-x` at least once: an early `-x` run stopped at
  238 passed missed 6 failures that only appeared in the full 1754-pass run.
- Windows PermissionError noise on basetemp rmtree (sqlite handle still open) is
  infrastructure noise — judge pass/fail counts, not error counts.
- Stale hard-coded assertions are the #1 recurring failure class after any
  migration-adding task: alembic head constants (`HEAD = "old_rev"`), expected-
  tables sets missing newly added tables.
- Fix pattern: live discovery (`ScriptDirectory.from_config(cfg).get_heads()`) or
  additive expected-set extension with source comment naming the sprint/task that
  added each table. NEVER hard-code the new head value (it goes stale again).
- Adversarial control is mandatory proof of normalization quality: plant a fake
  table/revision into a DB copy → assertion must STILL fail naming exactly the
  planted artifact; clean DB copy must pass.
- Final-gate corrections get NARROW allowlists (exact file list), a known-good
  normalized sibling file as pattern reference, and "×2 PASS + adversarial proof"
  acceptance.

## Terminal-state hygiene
- Registry carries Task ID → exact session → model → state → write-set → evidence
  → hashes. Reconcile ANY off-map task IDs explicitly (mark authority gap, keep
  fixes on disk for attribution) — reviewers check for retroactive legitimation.
- MAIN protected tree: confirm NO sprint production files appear in its dirty
  list. docs/pm prompts/handoffs from other lanes (Codex/S11/S13) are expected
  noise — check mtimes to attribute.
- Cleanup on Windows: pytest basetemp dirs need explicit `rm -rf` loops (file-
  locked dirs survive one pass — loop until remaining=0). Confirm zero live
  pytest/uvicorn/playwright processes via wmic/tasklist — NEVER MSYS ps (PID
  mapping lies).
- MOTIONFORGE_DATABASE_URL must be UNSET at every checkpoint; verify with env.

## Model routing discipline
- Every dispatch/resume uses provider/model/reasoning/fallback from the CURRENT
  prompt (custom @ 9Router, alpha, max, fallback disabled in recent sprints).
- Resume keeps the exact same route; route mismatch = BLOCKED_MODEL_ROUTE.
- Verify router health independently (curl /v1/models) but note: /v1/models can
  return 200 while chat completions intermittently return empty — health check is
  necessary, not sufficient.

## Reporting rhythm
- Heartbeat ≤20 min while any worker runs; liveness audit at 8 min frozen logs.
- Registry append-only rows: timestamp, task, event, verification numbers (×2 run
  times), hashes-before for hot files.
- Terminal states only: TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW or
  BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW. Never APPROVED/CLOSED.
