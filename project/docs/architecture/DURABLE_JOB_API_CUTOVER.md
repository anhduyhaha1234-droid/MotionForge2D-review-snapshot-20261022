# Durable Job API Cutover (S02-T05)

**Status:** Implemented for S02-T05 review
**Contract:** `docs/architecture/DURABLE_JOB_CONTRACT.md` V1.1 (approved)
**Persistence:** `app/persistence/jobs.py` (S02-T02, approved)
**Worker:** `app/workflow/durable_worker.py` (S02-T03, approved)
**Reconciler:** `app/workflow/job_reconciler.py` (S02-T04, approved)
**Scope:** API cutover of every backend job exposed by the current API to
durable submit/poll/cancel; explicit app lifecycle; restart-safe recovery
acceptance tests.  No schema/migration/dependency changes; no frontend
response-field changes; no dual-write; `channels.json` untouched.

## 1. Cutover map — closures → durable job types

The audit of every `create_job` call site (TASK start prompt) found exactly
**four** API job submissions, all in `app/api/routes/projects.py`:

| Legacy endpoint | Legacy closure (RAM + thread) | Durable job type | Registered handler | Input manifest |
|---|---|---|---|---|
| `POST /api/projects/{id}/ingest` | `IngestService.ingest(...)` | `ingest` | `job_handlers._ingest_handler` | `{project_id, schema_version, managed_root, project_root}` |
| `POST /api/projects/{id}/objects/{oid}/propagate` | `SegmentationService.propagate_masks(...)` + motion + crops | `propagate` | `job_handlers._propagate_handler` | `{project_id, object_id, scene_id, frame_count, ...}` |
| `POST /api/projects/{id}/preview` | `PreviewRenderService.render_preview(...)` | `preview` | `job_handlers._preview_handler` | `{project_id, object_id, scene_id, ...}` |
| `POST /api/projects/{id}/render` | `FinalRenderService.render_final(...)` | `render` | `job_handlers._render_handler_entry` | `{project_id, object_id, scene_id, format, ...}` |

Every mapping is faithful and restart-safe: the manifest carries the
**resolved project root** and the durable id of the owner (project/object),
so a restarted process reconstructs the exact workflow context from durable
inputs — no closure, no RAM state, no dual-write.  The `propagate` handler
rehydrates the same segmentation/motion/crop pipeline the legacy closure
ran; the `preview`/`render` handlers rehydrate the same render services.

### Legacy-callable compatibility shim

`JobService.create_job(job_type, callable)` (the legacy signature used by
the API tests and the old `TestJobStatus`/`TestJobCancellation` suites) is
kept as a **compatibility shim**: the callable is converted into a
registered synthetic handler (`SYNTH:<type>`) and the job is **still a
durable row** executed by the S02-T03 worker.  RAM never holds the
authority; a synthetic job survives a restart as a `queued` row that fails
closed with `UNKNOWN_HANDLER` in a fresh process (its closure cannot be
reconstructed — the correct behaviour for a non-reconstructable shim).
New API callers always use `create_job(job_type, input_manifest=...)`.

## 2. API-compatible durable service — `app/workflow/job_service.py`

`JobService` keeps the legacy method surface (`create_job` / `get_job` /
`cancel_job`) but is backed by the durable repository:

- `create_job(...)` → `JobRepository.create_job` with a versioned
  `input_manifest`, one `run` step, `actor="api"`; the workspace row is
  created on demand (`default` workspace for the legacy project workflow);
  the owned database is upgraded to head on first use through the explicit
  bootstrap path (never at import time).
- `get_job(id)` → durable read; `None` for unknown (route → 404).
- `cancel_job(id)` → guarded `queued|running → cancelling` with
  `reason_code=CANCEL_REQUESTED`; a second cancel while `cancelling` is an
  idempotent 200-style no-op (contract §6.3); terminal/unknown → False
  (route → 400/404).
- `_job_info` maps the durable `JobRecord` to the legacy `JobInfo`
  response shape.  `JobState` gained `pending` (additive; contract §11.2);
  internal `fenced` is never exposed (the reconciler resolves it before any
  poll observes it, contract §4.5-6).  `error` carries the envelope
  message string; `result_path` is populated from the manifest's legacy
  result path when the Job completed.

## 3. Registered handlers — `app/workflow/job_handlers.py`

All four job types are registered on the worker with
`register_api_handlers(worker)`; each handler receives the versioned
`WorkerContext` (immutable input manifest, checkpoint, fenced callbacks)
and rehydrates the same services the legacy closures used.  `preview` and
`render` declare final outputs (`renders/scene_{scene_id}_preview.mp4` /
`_final.mp4`); the worker's fail-closed declared-output validation (sha256
+ size, contract §9.3/AC6) is the completion gate — a missing/staging
output can never be marked complete.

## 4. Application lifecycle — `app/lifecycle.py` + `app/main.py` + `app/api/app.py`

AC1 wiring, all explicit:

1. **Startup (FastAPI lifespan):** `Lifecycle.initialize()` runs the
   approved bootstrap path (Alembic upgrade on the explicit database
   target, guarded by `assert_schema_revision_supported` — a newer database
   is refused, never touched); then `Lifecycle.start()` runs **one bounded
   reconciliation pass before the worker starts polling** (S02-T04), then
   starts the worker poll loop.
2. **Shutdown:** `Lifecycle.stop()` stops and joins the worker poll loop.
   The reconciler runs in the caller's thread (bounded pass) — there is no
   separate reconciler thread to join.
3. **No import-time side effects:** importing `app.main` / `app.api.app` /
   `app.workflow.job_service` starts no threads, opens no sessions, creates
   no files (verified by the pristine-subprocess probes in the S02-T03/T04
   `test_no_cutover_imports` tests, which still pass — `durable_worker` no
   longer pulls in the API service through `app.workflow.__init__`).

Tests inject a patched database path on `deps._lifecycle_db` so the
lifespan never touches the production database; the shared conftest builds
a durable `JobService` over a temp database + temp managed root.

## 5. Response compatibility (AC3)

- `GET /api/jobs/{id}` keeps `job_id`, `status` (renamed `state`),
  `progress`, `message`, `result_path`, `error`, `job_type` — unchanged
  meanings.  Additive durable fields may appear; none changes legacy field
  meaning.  `fenced` is hidden.
- `POST /api/jobs/{id}/cancel` keeps 200 `{"status":"cancel_requested"}` /
  400 terminal / 404 unknown, plus the idempotent 200 while `cancelling`.
- No frontend response fields were changed; no frontend code was touched.

## 6. HTTP requests are submission-only (AC6)

Submit endpoints validate inputs, write the durable Job row, and return the
`JobInfo` — they never execute the pipeline.  `test_http_submit_is_fast_and_submission_only`
asserts the ingest submit returns while the Job is still durably `queued`
and completes in well under the request budget.

## 7. Acceptance coverage — `tests/test_durable_job_api.py`

| AC | Test |
|---|---|
| AC1 explicit lifecycle, no import side effects | `test_import_starts_no_threads_or_db`, `test_service_lifecycle_start_stop_joins_worker` |
| AC2 durable submit + registered handlers | `test_api_submit_creates_durable_row_with_manifest`, `test_legacy_callable_is_durable_synthetic` |
| AC3 response semantics, fenced hidden | `test_get_job_preserves_legacy_fields_and_hides_fenced`, `test_cancel_semantics_200_400_404` |
| AC4/AC5 restart-safe recovery | `test_forced_close_reconciles_and_completes_without_duplicates` (fresh engine + reconciler + worker; exactly one attempt row) |
| AC7 double-submit / forced close / stale worker / cancel during retry / no false-ready | `test_cancel_during_retry_backoff_wins`, `test_no_false_ready_artifact`; forced-close test above |
| AC6 submission-only HTTP | `test_http_submit_is_fast_and_submission_only` |

Double-submit idempotency is enforced at the repository level
(`(workspace_id, idempotency_key)` partial unique index, S02-T02) — the API
submits carry stable keys (`ingest:{project_id}`,
`propagate:{project}:{object}`, `preview:...`, `render:...`), so a repeated
submit returns the existing active Job row and creates exactly one effect
set (contract §15-3).

## 8. Ownership boundaries

- No schema/migration/dependency changes; no frontend changes; no edits to
  ROADMAP/PRD/MP or prior evidence.
- Legacy `app/workflow/job_service.py` was **replaced** by the durable
  service (same module path — the legacy RAM authority is retired, AC6);
  `deps.get_job_service()` returns the durable service.
- `channels.json` and user data untouched.
