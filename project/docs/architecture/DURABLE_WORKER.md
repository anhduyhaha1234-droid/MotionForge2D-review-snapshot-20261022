# Durable Worker (S02-T03)

**Status:** Implemented for S02-T03 review
**Contract:** `docs/architecture/DURABLE_JOB_CONTRACT.md` V1.1 (approved)
**Persistence:** `app/persistence/jobs.py` (S02-T02, approved)
**Scope:** Worker loop (claim → execute → heartbeat → publish), retry/backoff
engine, cooperative cancel propagation, staging/publication validation bound
to the durable repository.  No API cutover, no reconciler, no schema change,
no dependency change; the legacy in-memory `JobService` remains the runtime
authority until S02-T05.

## 1. Lifecycle (AC1)

`app/workflow/durable_worker.py` — `DurableWorker(session_factory, config,
clock, sleeper, rng, logger)`:

- **No import-time thread.**  Importing the module or constructing a worker
  starts nothing.  The only thread this class ever spawns is the explicit
  background poll loop created by `start()`; `stop(timeout)` signals and
  joins it.  `run_once()` never touches threading.
- `run_once()` — deterministic single queue scan: claims the highest-priority
  oldest `queued` Job (SQL order `priority DESC, created_at ASC`), executes it
  to a terminal state or a fenced abort, returns the number of claims
  attempted (0 or 1).  Used by tests and by the loop.
- `run_forever()` — polls `run_once()` every `poll_interval` (injectable
  sleeper) until `stop()` is signalled; loop exceptions are logged and
  surfaced on `last_error` (the loop must survive).
- `start()/stop()` — background daemon thread with a stop event; `stop()`
  joins with a bounded timeout.

## 2. Handler registry and versioned context (AC2)

- `register_handler(job_type, handler, declared_outputs=None,
  output_validator=None)` — registry keyed by the Job's `job_type`.  A Job
  whose type has no registered handler fails safely with `UNKNOWN_HANDLER`
  (permanent envelope, never runs nothing).
- Handlers receive a `WorkerContext` carrying the Job's immutable
  `input_manifest`, the step's schema-versioned `checkpoint`, attempt number,
  worker id, fence token, TTL and four **fenced** callbacks:
  - `progress(pct, msg)` / `write_checkpoint(cp)` — each opens its own
    session, writes through `JobRepository` with the current fence token and
    commits immediately (bounded write windows; no SQLite write lock is held
    while a handler runs — verified by the fencing tests' external-writer
    checks).
  - `is_cancelled()` — reads the durable cancel flag (`cancelling` state).
  - `staging_dir()` — per-Job/per-step staging path under the managed root
    (contract §9.1).

## 3. Claim, heartbeat and fencing (AC1/AC3)

- **Claim** (`_claim_next`): atomic `acquire_lease` (S02-T02 CAS) +
  guarded `queued → running` with the current fence token, committed inside
  the claim.  Two workers can never hold the same lease; the loser's
  `run_once` returns 0 (verified by a two-worker race test).
- **Per-claim heartbeat thread** (AC3, independent of handler behavior):
  `run_once` starts a dedicated daemon thread for the claimed Job
  (`_start_heartbeat` → `_heartbeat_loop`) that renews the lease every
  `heartbeat_interval` seconds **in its own short-lived Session**, using the
  current fence token.  The thread never shares a SQLAlchemy Session with
  the execution thread and never holds a write transaction while the handler
  computes.  Before renewing, it verifies the lease still belongs to this
  worker with this token — a beat can never release/overwrite a newer
  worker's lease.  On `LeaseConflictError`/`FencedWorkerError` the thread
  records the failure on a thread-safe channel (`_hb_error` under
  `_hb_lock`), logs a structured warning and stops.
- **Failure propagation**: after the handler completes (in a `finally` that
  always stops/joins the heartbeat thread), `run_once` checks the channel;
  a failed beat raises the recorded error so the execution path aborts
  **before any subsequent state/output write**.  `_stop_heartbeat` joins the
  thread with a bounded timeout (`heartbeat_join_timeout`), so the thread is
  deterministically gone on success, handler exception, cancel, worker stop
  and fencing (verified by leak tests enumerating all terminal paths).
- **Fencing enforcement** (contract §5.3-1/§5.3-3): every worker-owned write
  (progress, checkpoint, step transitions, attempts, error envelopes)
  carries the current fence token; a missing or stale token raises
  `FencedWorkerError` at the repository.  The worker catches it at the
  **run_once boundary**, logs a structured warning, rolls back its own
  transaction and aborts **silently**: it never releases the new owner's
  lease, never publishes outputs, never mutates state.  The intruder's
  lease row and the Job's `running` state stay intact (tested).

## 4. Retry and backoff (AC4)

- Errors are classified by a stable `error_code` (§6.1): transient codes
  (`BUSY_LOCK`, `NETWORK_TIMEOUT`, `PROVIDER_429`, `DISK_FULL`, `GPU_OOM`,
  `TRANSIENT`) retry with bounded exponential backoff
  `base 1s · 4^(attempt-1)` capped at `16s`, jitter ≤20% (injectable rng —
  deterministic for a seed).  All other codes are permanent.
- Every failed attempt is recorded in the append-only `job_attempt` table
  with the attempt envelope; a transient that exhausts the per-Job
  `max_attempts` fails the Job with the stable `RETRIES_EXHAUSTED` envelope
  (`class=permanent, retryable=false`); a permanent failure fails with its
  own envelope.
- The retry loop re-runs the same step (`running → running`) after the
  backoff; cancel wins before the next retry (see §5).

## 5. Cooperative cancellation (AC5)

- Cancel is a durable flag (`cancelling` state, set by the API actor per
  contract §6.2).  The worker checks it:
  1. before starting the next step;
  2. after a handler attempt raises (before scheduling a retry);
  3. after a handler returns, before validation/completion.
- The drain path (`_cancel_drain`) transitions every non-terminal step along
  the §4.4 chain `pending → ready → running → cancelling → cancelled`
  (never starting new effects) and the Job `cancelling → cancelled` with
  `reason_code=CANCEL_DRAINED`.  A step that was mid-flight when the flag
  arrived finishes its current unit (its handler already returned) but no
  final output is published; the Job exposes no final output.
- Completed-vs-cancel race: serialized by the repository's guarded
  transitions — the cancel flag committed before the completion write makes
  the completion write raise `INVALID_STATE_TRANSITION`, which the worker
  observes as a terminal `cancelling` state and drains (tested).

## 6. Fail-closed output validation (AC6)

- `declared_outputs` (per job type) lists final-output artifacts
  (`purpose ∈ {render, final, result}`, §9.2) with `path`, optional
  `sha256` and `size_bytes`.
- After a handler returns, the worker validates every declared output on
  disk **in a fresh committed session** (a consistent committed view, never
  the worker's in-flight transaction): file exists, sha256 matches, size
  matches.  Any mismatch → the step fails with `VALIDATION_FAILED`
  (permanent) and the Job fails.
- The Job-level completion gate re-checks all declared outputs
  (`OUTPUT_MISSING` when any is absent/mismatched) before `running →
  completed`; a staging-only or missing output can never be marked complete
  (contract §9.3, invariant §15-5).  A handler may supply a custom
  `output_validator(ctx, result, staging_dir)`; its exception also fails
  closed with `VALIDATION_FAILED`.

## 7. Ownership boundaries

- No API routes, no reconciler/startup recovery (S02-T04), no migrations,
  no dependency changes, no edits to the legacy `app/workflow/job_service.py`.
- The worker never commits on behalf of the repository outside its own
  explicit transactions; the repository's caller-owns-transaction contract
  (S01 §6) is preserved.
- `channels.json` and user data are untouched.

## 8. Validation evidence (this task)

| Command | Result |
|---|---|
| `python -m pytest -q tests/test_durable_worker.py` | 32 passed |
| `python -m pytest -q tests/test_durable_job_persistence.py tests/test_durable_worker.py` | 79 passed |
| `python -m ruff check app tests` | All checks passed |
| `python -m mypy app` | Success, 50 source files |
| `git diff --check` | PASS |
| `scripts/quality-baseline.ps1` | 7/7 gates PASS (see session LOG) |
| `sha256sum channels.json` | UNCHANGED (byte-for-byte preserved) |

## 9. Out of scope (future tasks)

- Reconciler: lease scan, fencing resolution `fenced → queued|failed`,
  checkpoint resume, startup reconcile (S02-T04).
- API cutover, compatibility shim removal, integration recovery tests
  (S02-T05).
- Real GPU/model/network handlers (synthetic deterministic handlers are the
  test surface).
