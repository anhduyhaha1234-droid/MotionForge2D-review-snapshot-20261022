# S02-T03 - Implementation Report

**Status:** SUBMITTED (round 2 — PM CHANGES_REQUESTED AC3 heartbeat rework)
**Hermes session:** 20260803_201105_d65c9d (continuation 20260803_2105 / 2120)
**Started:** 2026-08-03 20:11 +07:00
**Submitted:** 2026-08-03 21:25 +07:00

## Outcome delivered

A deterministic durable worker (`app/workflow/durable_worker.py`) around the
approved S02-T02 `JobRepository`: explicit start/stop/run-once lifecycle with
**no import-time thread**, injectable clock/sleeper/rng, a handler registry
keyed by job type, atomic priority/time-ordered queue claims, implicit
heartbeats on every fenced write, bounded deterministic retry/backoff with
stable error envelopes, cooperative cancel drain, and fail-closed output
validation.  No API routes, no reconciler, no migrations, no dependency
changes, no edits to the legacy `JobService`; `channels.json` preserved
byte-for-byte.

## Acceptance criteria evidence

| AC | Status | Evidence |
|---|---|---|
| AC1 Explicit start/stop/run-once lifecycle; atomic queue claim ordered by priority/time; no background work on import | PASS | `test_import_starts_no_thread_or_job_work` (thread-count invariant), `test_run_once_processes_one_job_and_no_background_thread`, `test_run_once_claims_by_priority_then_age` (priority desc, created_at asc), `test_start_stop_lifecycle`, `test_run_forever_stops_on_flag`, `test_claim_is_atomic_across_two_workers` (exactly one claimant) |
| AC2 Registered handlers receive versioned input/checkpoint context and fenced progress/checkpoint/cancel callbacks; unknown handler fails safely | PASS | `test_registered_handler_receives_versioned_context` (manifest, schema_version, token), `test_unknown_handler_fails_safely` (UNKNOWN_HANDLER permanent), `test_fenced_callbacks_reject_after_fence` (callback-level FencedWorkerError on progress/checkpoint after intruder re-claim) |
| AC3 Heartbeat keeps a live claim; lost/stale token aborts execution and cannot publish state or outputs | PASS | `test_heartbeat_keeps_lease_alive` (fake clock +90s, checkpoint renews lease), `test_heartbeat_thread_keeps_silent_handler_leased` (real beat thread renews a silent handler's lease past TTL), `test_heartbeat_thread_failure_aborts_without_publication` (channel failure ⇒ s2 never starts, no output), `test_heartbeat_never_overwrites_newer_lease`, `test_heartbeat_thread_never_leaks_across_terminal_paths` (success/exception/cancel/fencing), `test_fenced_worker_cannot_publish_state_or_outputs`, `test_release_on_fenced_abort_is_silent` |
| AC4 Transient failures use bounded deterministic backoff and attempts; permanent/exhausted failures persist stable envelopes | PASS | `test_transient_failure_retries_with_bounded_backoff` (attempts [1,2,3]; sleeper 1s/4s ±20%), `test_permanent_failure_fails_with_stable_envelope` (INPUT_MISSING permanent), `test_retries_exhausted_fails_with_envelope` (RETRIES_EXHAUSTED + details.max_attempts + 2 attempt rows), `test_backoff_is_bounded_and_deterministic` (cap 16s; seed-deterministic) |
| AC5 Cancel wins before next effect/step, drains to terminal cancelled, exposes no final output; completed-vs-cancel race serialized | PASS | `test_cancel_drains_to_cancelled_before_next_step` (s2 never runs), `test_cancelled_job_exposes_no_final_output` (zero artifact rows), `test_cancel_during_retry_backoff_wins` (one attempt, cancelled), `test_completed_vs_cancel_race_serialized` (flag first ⇒ completion write rejected, cancelled) |
| AC6 Step/job completion requires declared outputs ready/validated; staging/missing output never marked complete | PASS | `test_completion_requires_declared_outputs` (present+sha256/size ⇒ completed; deleted ⇒ failed VALIDATION_FAILED/OUTPUT_MISSING), `test_validation_failure_fails_closed` (validator raises ⇒ VALIDATION_FAILED permanent), `test_staging_output_never_marked_complete` (staging-only ⇒ failed), `test_output_purposes_constant` ({render, final, result}) |
| AC7 No API cutover/reconciler/schema/dependency changes; targeted and 7/7 PASS | PASS | `test_no_cutover_imports` (app.api / job_service never imported by worker module); targeted 28/28; combined 75/75; baseline 7/7 (see Tests) |

## PM round-1 corrections implemented

1. **Fenced worker aborts silently at the run_once boundary (contract
   §5.3-3)** — `run_once` catches `FencedWorkerError` around `_execute_job`,
   logs a structured warning, rolls back its own transaction, and returns its
   documented result (1); it does **not** raise.  Callback-level rejection is
   retained (`ctx.progress`/`write_checkpoint` still raise
   `FencedWorkerError` from the repository's `_require_fence_token`).
   Tests assert `run_once() == 1`, the intruder's lease row and the Job's
   `running` state remain intact, and `progress == 0.0` (nothing published).
2. **`_write_file` invocation fixed** — helper signature is
   `(root, rel, data)`; the test now calls
   `_write_file(managed_root, "jobs/x/out.txt", b"hello")`.
3. **Missing `session: Session` fixture** added to
   `test_staging_output_never_marked_complete` (and to
   `test_completion_requires_declared_outputs`), so `session.commit()`
   commits the fixture session instead of pytest's fixture definition object.
4. **Output validation reads a consistent committed view** —
   `_validate_outputs` opens a fresh committed session for the declared-
   output disk checks (never the worker's in-flight transaction).
5. **Handler execution holds no SQLite write transaction** — every
   repository write in the claim/step/drain paths commits immediately
   (bounded write windows); the fencing tests' external writers prove no
   lock is held while a handler runs.
6. **Background threads always stop/join** — `stop()` joins the loop thread
   with a bounded timeout; lifecycle tests assert `running is False` after
   stop on success, exception, cancel and fencing paths.
7. **Baseline round-1 failure fixed** — `test_no_cutover_imports` asserted
   `app.api not in sys.modules` in-process, which is a false positive in the
   full suite (other test modules import the API first).  It now probes a
   pristine subprocess: the worker module imports clean, pulling in neither
   `app.api` nor the legacy `job_service`.

## PM round-2 corrections implemented (AC3 — periodic per-claim heartbeat)

1. **Real heartbeat thread, independent of handler behavior.**  `run_once`
   starts a dedicated daemon thread per claim (`_start_heartbeat` →
   `_heartbeat_loop`) that renews the lease every `heartbeat_interval`
   seconds **in its own short-lived Session/transaction**, using the current
   fence token — no progress/checkpoint callback required.
2. **Renews before TTL for silent long-running handlers.**  Test
   `test_heartbeat_thread_keeps_silent_handler_leased` runs a handler that
   makes zero fenced calls for ~0.6s against a 3s TTL and asserts the lease
   is still live at completion (real thread, real sleep — not a
   callback-triggered renewal).
3. **Deterministic stop/join on every terminal path.**  `_stop_heartbeat`
   signals and joins (bounded `heartbeat_join_timeout`) inside the
   `finally` around `_execute_job`; `test_heartbeat_thread_never_leaks_
   across_terminal_paths` covers success, handler exception, cancel drain
   and fencing, asserting `_heartbeat_thread_alive() is False` after each
   and zero stray `hb-*` threads at the end.
4. **Thread-safe failure propagation.**  A beat that observes a lost/stale
   lease records `FencedWorkerError`/`LeaseConflictError` on `_hb_error`
   (under `_hb_lock`); `run_once` checks the channel after the handler
   returns and raises it, so the execution path aborts **before any
   subsequent state/output write** (test asserts step s2 never starts and
   no terminal write is published).
5. **No shared Session / no write transaction during handler compute.**
   The heartbeat thread opens a fresh session per beat and commits each
   beat; the execution thread's own writes remain bounded windows.
6. **Never releases/overwrites a newer worker's lease.**  Each beat verifies
   `lease.worker_id == self.worker_id` and `lease.fence_token == token`
   before renewing; `test_heartbeat_never_overwrites_newer_lease` asserts
   the intruder's lease row and fresh token are untouched after the beat
   observes the re-claim.
7. **Injectable scheduling.**  `WorkerConfig.heartbeat_interval` and
   `heartbeat_join_timeout` are configurable (tests use 0.05s beats /
   5s joins); the loop itself is tested directly.

## Files changed

- `app/workflow/durable_worker.py` (new; DurableWorker + WorkerConfig +
  WorkerContext + registry + envelope helpers)
- `tests/test_durable_worker.py` (new; 28 tests covering AC1-AC7)
- `docs/architecture/DURABLE_WORKER.md` (new; implementation doc)
- `docs/pm/sessions/S02-T03-durable-worker/LOG.md`, `REPORT.md` (this report)

Untouched: API routes, frontend, legacy `app/workflow/job_service.py`,
migrations/schema, dependency files, `app/persistence/*`, user data and
`channels.json` (byte-for-byte), ROADMAP/PRD/MP, PM-owned `TASK.md` /
`START_PROMPT.md` / `PM_REVIEW.md`.

## Tests and validation

| Command | Result | Notes |
|---|---|---|
| `python -m pytest -q tests/test_durable_worker.py --cache-clear` | PASS | 32 passed in ~8.7s |
| `python -m pytest -q tests/test_durable_job_persistence.py tests/test_durable_worker.py --cache-clear` | PASS | 79 passed in ~18s (47 repository + 32 worker) |
| `python -m ruff check app tests` | PASS | All checks passed |
| `python -m mypy app` | PASS | Success: no issues found in 50 source files |
| `git diff --check` | PASS | exit 0 (LF→CRLF advisory only) |
| `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1` | PASS | run id `20260803-212318` — OVERALL PASS exit 0 (7/7 gates: env, python tests, ruff, mypy, tsc, eslint, build) |
| `sha256sum channels.json` | UNCHANGED | `dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555` — identical at session start and end (byte-for-byte preserved) |

## Manual UX/media verification

Not applicable — worker engine task, no UI or media.

## Deviations from task

None.  Two stable failure codes may surface for missing declared outputs
(`VALIDATION_FAILED` from the per-step validation gate, `OUTPUT_MISSING` from
the Job-level completion gate); both are contract codes and both fail closed
(no completion).  Tests assert membership in the allowed pair.

## Out-of-scope findings

- `fenced` rows and lease-expiry resolution remain for S02-T04 (reconciler);
  a fenced worker aborts silently and the Job stays `running` under the new
  owner's lease until the reconciler resolves it.
- Legacy `JobService` still holds a `JobStatus` enum + RAM-only jobs; S02-T05
  cutover decides retirement (same note as S02-T01/T02).

## Known limitations/risks

- Worker concurrency is bounded by the repository's lease CAS; two workers
  polling the same queue can never claim the same Job (race-tested).
- Heartbeat thread joins with a bounded timeout (`heartbeat_join_timeout`).
  Under extreme scheduling stalls the join could time out; the daemon thread
  is then stopped by its own stop event on its next beat and the channel
  error (if any) is still honored before the commit decision.  A handler
  that runs longer than the lease TTL without yielding is protected by the
  beat thread; if the beat thread itself is starved, the reconciler fences
  the claim (contract §5.3) — the intended bounded-timeout behavior.

## Recommended PM decision

`PENDING` — awaiting PM review per protocol (no self-approval; no commit; no
roadmap edits; no next-task start).
