# S02-T05 - Implementation Report

**Status:** SUBMITTED
**Hermes session:** 20260803_223827_91193e
**Started:** 2026-08-03 22:38 +07:00
**Submitted:** 2026-08-04 01:00 +07:00
**Resubmitted (after PM CHANGES_REQUESTED):** 2026-08-04 01:00 +07:00

## Outcome delivered

Durable job API cutover: every backend job exposed by the current API
(`POST /api/projects/{id}/ingest`, `.../objects/{oid}/propagate`,
`.../preview`, `.../render`) is now durably submitted, polled and cancelled
through the S02-T02 `JobRepository` + S02-T03 worker, with restart-safe
recovery via the S02-T04 reconciler wired into an explicit application
lifecycle.  The audit found exactly four `create_job` call sites, all
legacy closures; each maps 1:1 to a registered durable job type
(`ingest`/`propagate`/`preview`/`render`) with a schema-versioned input
manifest carrying the resolved project root and durable owner ids — every
mapping is faithfully reconstructable after restart, so **no BLOCKED
items** and no RAM authority / dual-write was preserved.  The legacy
in-memory `JobService` (RAM dicts + threads) is retired: the same module
path now hosts the API-compatible durable service.  HTTP requests are
submission-only (validate → durable insert → return); long pipelines run
exclusively in the worker.  No schema/migration/dependency changes, no
frontend response-field changes, `channels.json` untouched.

**PM CHANGES_REQUESTED round (5 blockers) — all fixed:**

1. **CR1** — `scripts/debug_repro.py` (out-of-scope temp file) deleted.
2. **CR2** — deps/job service fully lazy: importing `app.api.deps` /
   `app.api.app` / `app.main` performs no mkdir, no DB/engine creation, no
   thread start, no filesystem mutation.  Service, engine and managed-root
   construction happen only in explicit lifespan/fixture setup.
   `test_import_is_pristine_on_nonexistent_project_root` (pristine
   subprocess on a nonexistent temp project root) proves no path is
   created on import.
3. **CR3** — S01 migration policy enforced in `JobService.initialize()`:
   missing DB bootstraps; an existing DB with pending revision is backed
   up on-disk (collision-safe name, fsync, sha256+size evidence, verified
   copy) BEFORE Alembic; backup failure aborts the upgrade; a DB already
   at head performs no redundant backup.  Four tests:
   `test_initialize_missing_db_bootstraps`,
   `test_initialize_existing_s01_db_backs_up_before_upgrade`,
   `test_initialize_backup_failure_aborts_upgrade`,
   `test_initialize_head_db_is_noop_without_backup`.
4. **CR4** — legacy `create_job(job_type, callable)` closure shim and the
   synthetic handler RAM registry removed from production `JobService`
   (`create_job` now takes `(job_type, input_manifest, **kwargs)` only;
   `LEGACY_SYNTH_PREFIX`, `_register_synthetic`, `_has_handler`,
   `get_service` all gone).  Old tests register explicit stable test job
   types/handlers on the injected worker and submit versioned manifests;
   `test_create_job_rejects_callable` proves no unreconstructable callable
   is accepted after cutover.
5. **CR5** — targeted/combined suite, ruff, mypy, diff check and a
   genuinely completed 7/7 baseline all re-run; final run id/status
   recorded below.  Response compatibility, all four real API handlers,
   restart tests and `channels.json` preservation kept.  LOG/REPORT set to
   SUBMITTED; no roadmap edits, no commit.

## Acceptance criteria evidence

| AC | Status | Evidence |
|---|---|---|
| AC1 Application lifecycle explicitly initializes/upgrades only via the approved bootstrap path, then reconciles before worker polling; shutdown stops/joins worker/reconciler without import-time side effects | PASS | `app/lifecycle.py` + FastAPI lifespan (`app/api/app.py`): `initialize()` = Alembic upgrade on explicit target behind `assert_schema_revision_supported` **and the S01 pre-upgrade backup policy (CR3)**; `start()` = one bounded reconcile pass **before** `start_worker()`; `stop()` joins worker (reconciler runs in caller thread, bounded). `test_import_starts_no_threads_or_db` (thread-count + no DB file on import), `test_import_is_pristine_on_nonexistent_project_root` (CR2 pristine subprocess), `test_service_lifecycle_start_stop_joins_worker`, S02-T03/T04 pristine-subprocess probes still pass |
| AC2 All existing API job submissions use durable IDs/input manifests and reconstructable registered handlers; no endpoint passes an ephemeral closure as authoritative job definition | PASS | Cutover map (DURABLE_JOB_API_CUTOVER.md §1): 4/4 endpoints now submit manifest Job rows with stable idempotency keys; `job_handlers.py` registers all four handlers; `test_api_submit_creates_durable_row_with_manifest` (manifest + one `run` step persisted), `test_registered_handler_job_is_durable` (registered handler + versioned manifest, durable row), `test_create_job_rejects_callable` (CR4) |
| AC3 GET/cancel preserve existing response/status semantics (200/400/404) with additive durable fields and hide internal `fenced` state | PASS | `job_response` unchanged; `GET /api/jobs/{id}` keeps job_id/status/progress/message/error/job_type; `POST .../cancel` keeps 200 cancel_requested / 400 terminal / 404 unknown + idempotent 200 while cancelling; `test_get_job_preserves_legacy_fields_and_hides_fenced`, `test_cancel_semantics_200_400_404` |
| AC4 Progress/error/result compatibility is backed by durable rows/artifact outputs; cancellation is durable and restart-safe | PASS | progress/error live on the durable row; cancel is a guarded `queued\|running → cancelling` transition with `CANCEL_REQUESTED`; `test_forced_close_reconciles_and_completes_without_duplicates` proves restart-safe cancel/complete semantics (fresh engine + reconciler + worker, exactly one attempt row) |
| AC5 Restart integration through fresh app/engine proves queued/running job reconciliation and subsequent poll/cancel/complete without duplicates | PASS | `test_forced_close_reconciles_and_completes_without_duplicates`: phase-1 worker dies mid-step with an expired lease → fresh reconciler fences + requeues → fresh worker completes exactly once (len(completed)==1, one attempt row, zero duplicates) |
| AC6 Legacy RAM dictionaries/threads removed from runtime authority; no dual-write and no long operation executes inside HTTP request | PASS | `app/workflow/job_service.py` replaced the RAM service; no `_jobs` dict / `_threads` remain; no closure shim (CR4). `test_http_submit_is_fast_and_submission_only` — ingest submit returns while the Job is durably `queued`, well under the request budget |
| AC7 Full S02 acceptance covers double-submit, forced close, stale worker, cancel during retry, no false-ready artifact | PASS | double-submit: stable idempotency keys + repository partial unique index (S02-T02); forced close + stale worker: forced-close test (stale phase-1 worker can never publish; fresh reconciler requeues); `test_cancel_during_retry_backoff_wins`; `test_no_false_ready_artifact` (declared output missing → failed with validation envelope, never completed) |

## Files changed

- `app/workflow/job_handlers.py` (new) — registered durable handlers for
  ingest/propagate/preview/render + declared final outputs.
- `app/workflow/job_service.py` (rewritten) — API-compatible durable
  service; legacy RAM authority retired; synthetic shim for legacy
  callables.
- `app/api/deps.py` — `get_job_service()` returns the durable service.
- `app/api/routes/jobs.py` — unchanged route contract over the durable
  service (200/400/404; `fenced` never exposed).
- `app/api/routes/projects.py` — 4 endpoints cut over to manifest-based
  durable submission (HTTP is submission-only).
- `app/api/helpers.py` — unchanged response shape (additive fields only).
- `app/schemas/__init__.py` — `JobState.PENDING` added (additive, never
  reordered).
- `app/lifecycle.py` (new) — explicit bootstrap → reconcile → worker
  lifecycle controller.
- `app/api/app.py` — FastAPI lifespan wiring (startup/shutdown).
- `app/main.py` — docstring only (lifespan moved to `app/api/app.py`).
- `app/workflow/__init__.py` — exports handlers/reconciler only (import
  hygiene: `durable_worker` no longer pulls in the API service).
- `tests/conftest.py` — temp-DB durable JobService fixture + `_lifecycle_db`
  patch + autouse worker teardown.
- `tests/test_api.py`, `tests/test_clip_cancel_persist.py` — legacy
  API/cancel tests use the explicit durable worker lifecycle (start worker,
  poll states, stop worker) instead of wall-clock sleeps.
- `tests/test_durable_job_api.py` (new) — 10 S02-T05 acceptance tests.
- `docs/architecture/DURABLE_JOB_API_CUTOVER.md` (new).
- `docs/pm/sessions/S02-T05-job-api-cutover/LOG.md`, `REPORT.md`.

Untouched: migrations/schema, dependency files, frontend, ROADMAP/PRD/MP,
PM-owned `TASK.md`/`START_PROMPT.md`/`PM_REVIEW.md`, user data and
`channels.json`.

## Architecture/schema/API impact

- **Schema/migration:** none.  The durable tables already exist (S02-T02);
  the API service creates the logical `default` workspace row on demand so
  Job FK constraints hold.
- **API:** response contract preserved (AC3); the four submit endpoints
  return the same `job_response` shape (with the durable job id).
- **Runtime authority:** the legacy in-memory `JobService` (RAM dicts +
  threads) is removed from runtime authority — `deps._job_service` is the
  durable service.  No dual-write anywhere.

## Tests and validation

| Command | Result | Notes |
|---|---|---|
| `python -m pytest -q tests/test_durable_job_api.py` | PASS | 16 passed in ~12s (post-CR: includes CR2 pristine-import, CR3 migration-policy x4, CR4 no-callable tests) |
| `python -m pytest -q tests/test_api.py tests/test_clip_cancel_persist.py tests/test_durable_job_persistence.py tests/test_durable_worker.py tests/test_job_reconciliation.py tests/test_durable_job_api.py --cache-clear` | PASS | 152 passed, 6 skipped, 1 warning in 234s (post-CR) |
| `python -m ruff check app tests` | PASS | All checks passed (post-CR) |
| `python -m mypy app` | PASS | Success: no issues found in 53 source files (post-CR) |
| `git diff --check` | PASS | exit 0 (LF→CRLF advisory only) |
| `scripts/quality-baseline.ps1` | PASS | **OVERALL: PASS (exit 0), run id `20260804-000329`** — 7/7 gates: env, python tests, ruff, mypy, tsc, eslint, build |
| `sha256sum channels.json` | UNCHANGED | `dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555` (identical at session start and end) |

## Manual UX/media verification

Not applicable — API cutover task, no UI or media changes; the four submit
endpoints were exercised through HTTP (TestClient) in
`test_http_submit_is_fast_and_submission_only`.

## Migration and rollback

None — no schema or migration change.

## Deviations from task

None after the CHANGES_REQUESTED round.  Notes (updated):
- The legacy `create_job(job_type, callable)` closure shim was **removed**
  (CR4) — after cutover no unreconstructable callable is accepted.  Old
  API/cancel tests now register explicit stable test job types/handlers on
  the injected worker and submit versioned manifests.
- `app/main.py` keeps the uvicorn entry (`app.main:app`); the lifespan is
  defined in `app/api/app.py` where the app object lives.
- Tests inject `deps._lifecycle_db` so the FastAPI lifespan in tests never
  touches the production database path.
- `JobService.initialize()` implements the S01 migration policy (CR3):
  collision-safe on-disk backup with fsync + sha256/size evidence before
  any upgrade of an existing DB; head DBs are no-ops; missing DBs
  bootstrap.

## Out-of-scope findings

- `chunk_scenes`, `stitch_scenes`, `full_dubbing_pipeline` and the other
  long-running endpoints are **synchronous by design** (existing public
  contract, out of this task's job-cutover scope).  They were not converted
  to durable jobs; a future task can reuse the handler registry pattern.
- `JobStatus` enum (`pending/running/completed/failed`) in `app/schemas`
  remains used only by nothing in the durable path; it is kept for
  compatibility and can be retired by a later cleanup task.

## Known limitations/risks

- The durable default database lives at `<project_root>/data/motionforge.db`
  (created only by the explicit bootstrap on first app start).  No
  production DB exists on this machine yet; the first real `uvicorn` start
  will create and upgrade it (with an automatic pre-upgrade backup if a
  DB already exists at an older revision — S01 policy, CR3).
- The `propagate` handler uses `backend="sam2"` exactly as the legacy
  closure did; SAM2 remains an optional dependency (test surface stays
  synthetic/deterministic per S02-T03 scope).

## Recommended PM decision

`PENDING` — awaiting PM review per protocol (no self-approval; no commit; no
roadmap edits; no next-task start).
