# Restart Reconciliation (S02-T04)

**Status:** Implemented for S02-T04 review
**Contract:** `docs/architecture/DURABLE_JOB_CONTRACT.md` V1.1 (approved)
**Persistence:** `app/persistence/jobs.py` (S02-T02, approved)
**Worker:** `app/workflow/durable_worker.py` (S02-T03, approved)
**Scope:** Restart reconciliation: lease scan, atomic fencing, `fenced →
queued|failed|cancelled` resolution, attempt accounting, checkpoint-resume
compatibility and duplicate-effect prevention across process restarts.  No
API cutover, no schema change, no dependency change, no edits to the legacy
in-memory `JobService`; `channels.json` untouched.

## 1. Reconciler lifecycle (AC1)

`app/workflow/job_reconciler.py` — `JobReconciler(session_factory, config,
clock, sleeper, logger)`:

- **No import-time behavior.**  Importing the module or constructing a
  reconciler starts no threads, opens no sessions, touches no files.  The
  only thread this class ever spawns is the explicit background poll loop
  created by `start()`; `stop(timeout)` signals and joins it.
  `reconcile_once()` never touches threading.
- `reconcile_once()` — deterministic single bounded pass: scans at most
  `batch_size` (default 50) expired active leases, fences each candidate
  atomically, resolves every fenced Job to a terminal-or-queued state in
  **fresh sessions**, and returns a structured `ReconcileReport`
  (`scanned/fenced/requeued/failed/cancelled/skipped/errors/elapsed`).
  Never raises: per-Job failures are recorded on the report.
- `reconcile_forever()` — polls `reconcile_once()` every `poll_interval`
  (injectable sleeper) until `stop()`; loop exceptions are logged and
  surfaced on `last_error` (the loop must survive).
- `start()/stop()` — explicit daemon poll thread.

## 2. Candidate scan (AC1)

A Job is a candidate iff it is in an active leased state (`running` /
`cancelling`) **and** its lease row `expires_at` is in the past beyond the
fence grace (`fence_grace_seconds`, default 90s — the heartbeat-timeout
window of contract §5.2).  The scan is a read-only SQL join ordered by
oldest expiry, bounded by `batch_size`.  A live heartbeating worker is
never disturbed; a lease that expired within the grace window (a single
missed beat) is not fenced yet.

## 3. Atomic fencing (AC2)

For every candidate the reconciler performs **one atomic unit** in a single
transaction (contract §5.3-2):

1. `invalidate_lease(job_id)` — replaces the lease's `fence_token` with a
   unique non-empty sentinel (`fenced:<uuid>`, required because the schema
   CHECK `ck_job_lease_token_nonempty` forbids an empty token) and marks the
   lease released (`expires_at = now`).  The old token can never be
   presented again: every subsequent write by the stale worker raises
   `FENCED_WORKER` (§5.3-1 — the token is the enforcement point).
2. `transition_job(running|cancelling -> fenced, actor="reconciler")` —
   reason_code `LEASE_EXPIRED` (running) or `CANCEL_REQUESTED` (cancelling),
   with details recording the old worker id, lease version, and the
   manifest fingerprint.

Only after this unit commits does the reconciler decide requeue vs fail vs
cancel — in a **fresh session**, so the decision always observes the
committed state (exactly what a restarted process would see).  `fenced` is
never visible to the API: the resolver folds it into `queued`/`failed`/
`cancelled` before any poll can observe it (contract §4.5-6).

## 4. Resolution rules (AC2/AC3/AC4)

Order of checks in `_resolve_fenced` (each in its own fresh session):

| Condition | Decision | Envelope / reason |
|---|---|---|
| Fence reason `CANCEL_REQUESTED` (was `cancelling`) | `fenced -> cancelled`, actor reconciler | `CANCEL_DRAINED`; **no new effects ever started** (§6.3 cancel wins) |
| `job.attempt >= job.max_attempts` | `fenced -> failed` | `RETRIES_EXHAUSTED`, class permanent, retryable false |
| Manifest fingerprint ≠ creation fingerprint | `fenced -> failed` | `INPUT_CHANGED`, class permanent (§4.3) |
| otherwise | `fenced -> queued` | `FENCED_REQUEUE` |

**Requeue transaction (contract §8.2):** the Job-level `attempt` counter and
every non-terminal step's `attempt` counter are bumped in the **same
transaction** as `fenced -> queued`; a step that was mid-flight
(`running`/`cancelling`) is first rolled back to `ready` with
`reason_code=FENCED_ROLLBACK` (contract §4.4 — its attempt is rolled back,
and a re-claiming worker replays only uncommitted work).  Steps that are
`pending` are left pending; terminal steps (`completed`/`skipped`) are
never touched.

**Input-changed baseline:** `create_job`/`create_successor` record
`manifest_fingerprint` in the `created` event's details.  Manifests are
immutable by contract (§3), so the reconciler compares the current manifest
against that durable baseline and fails closed if the manifest was ever
mutated after creation.  A missing baseline (defensive) is treated as
unchanged so Jobs never spuriously fail.

## 5. Checkpoint-resume compatibility (AC3)

The reconciler never inspects checkpoint payload semantics.  Resume
compatibility is enforced by the worker on re-claim:

- a step whose checkpoint is absent or carries an unsupported
  `schema_version` is **not resumed** — the step re-runs from its beginning
  with a fresh checkpoint (contract §7.2: "a reader that cannot parse the
  version fails closed");
- a Job whose handler rejects the incompatible checkpoint fails with a
  stable envelope (`SCHEMA_MISMATCH`/`RETRIES_EXHAUSTED`, permanent);
- a resumed handler always receives the **committed** checkpoint (the
  last one written atomically with its effect), never a partial one.

## 6. Duplicate-effect prevention (AC3/AC5)

Duplicate effects are impossible by construction:

1. **Fencing is the enforcement point** (§5.3-1): a stale worker's state
   writes, heartbeats, releases and publications are all rejected with
   `FENCED_WORKER` after the sentinel replaces its token.  The stale worker
   aborts silently at its `run_once` boundary and can never publish.
2. **The reconciler never executes handlers** — it only transitions state;
   business effects are exclusively produced by the worker under a valid
   lease.
3. **Atomic re-claim**: the requeued Job is only re-claimed through the
   repository's lease CAS, which bumps `lease_version` and issues a fresh
   token — two workers can never hold the same lease (S02-T02 race test).
4. **Deterministic attempt rows**: per-claim attempt numbers are numbered
   from the durable per-step attempt counter (`latest_attempt_number` +
   per-claim counter), so `(job, step, attempt)` rows are unique across
   claims — replay can never insert a duplicate attempt row or duplicate an
   effect keyed by attempt.
5. **Committed checkpoint resume**: a re-claiming worker replays only
   uncommitted work from the last committed checkpoint; committed work is
   skipped (worker's idempotent step completion).

## 7. Forced-close/reopen proof (AC6)

The integration tests simulate a real restart with **fresh engines and
session factories** over the same database file:

- phase 1: worker-a claims a Job, writes a checkpoint, then is "killed"
  (no graceful release — the lease row is left expired);
- phase 2: a brand-new engine + `JobReconciler` reopen the database,
  fence the Job, and requeue it; the old worker's token is rejected in the
  new process;
- phase 3: a brand-new worker re-claims and resumes from the committed
  checkpoint; asserts: Job `completed`, attempt counters bumped exactly
  once, exactly one attempt row, exactly one `fenced`/`queued`/`completed`
  event chain, and **zero artifact rows** (no duplicate effects).

A second test proves a `cancelling` Job that died mid-drain reconciles to
`cancelled` on reopen — never requeued, never re-run.

## 8. Ownership boundaries

- No API routes, no migrations, no dependency changes, no edits to the
  legacy `app/workflow/job_service.py`; the legacy service remains the
  runtime authority until S02-T05.
- Repository additions are pure persistence methods (no behavior change):
  `invalidate_lease`, `bump_job_attempt`, `bump_step_attempt`,
  `latest_attempt_number`, plus the `manifest_fingerprint` recorded on
  `created` events and the `fenced -> cancelled` transition endpoint
  (contract §4.3 table — required so the reconciler can resolve a
  cancelling Job to terminal cancelled).
- Worker change: per-claim attempt rows are numbered from the durable
  per-step attempt counter (contract §8.2) so requeued claims never
  duplicate attempt rows.
- `channels.json` and user data untouched.

## 9. Validation evidence (this task)

| Command | Result |
|---|---|
| `python -m pytest -q tests/test_job_reconciliation.py --cache-clear` | 24 passed |
| `python -m pytest -q tests/test_durable_job_persistence.py tests/test_durable_worker.py tests/test_job_reconciliation.py --cache-clear` | 103 passed |
| `python -m ruff check app tests` | All checks passed |
| `python -m mypy app` | Success, 51 source files |
| `git diff --check` | PASS |
| `scripts/quality-baseline.ps1` | 7/7 gates PASS (see session LOG) |
| `sha256sum channels.json` | UNCHANGED (byte-for-byte preserved) |

## 10. Out of scope (future tasks)

- API cutover, compatibility shim removal, full recovery-contract
  integration tests (S02-T05).
- Real GPU/model/network handlers (synthetic deterministic handlers are the
  test surface).
