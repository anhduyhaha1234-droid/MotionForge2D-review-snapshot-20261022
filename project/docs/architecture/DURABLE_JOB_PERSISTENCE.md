# Durable Job Persistence (S02-T02)

**Status:** Implemented for S02-T02 review
**Contract:** `docs/architecture/DURABLE_JOB_CONTRACT.md` V1.1 (approved)
**Scope:** Job/JobStep ORM models + Alembic migration + lifecycle repository.
No worker, no reconciler, no API cutover, no dual-write — the legacy in-memory
`JobService` remains the runtime authority until S02-T05.

## 1. Schema (Alembic `23b308b1fd0b` — "durable job schema")

Forward-only migration from S01 (`a1b2c3d4e5f6`). Adds five tables:

| Table | Purpose | Key constraints |
|---|---|---|
| `job` | Durable unit of user-visible work | PK id; FK workspace RESTRICT; UNIQUE `predecessor_job_id`; CHECK state/revision/priority/progress; partial unique index (below) |
| `job_step` | Ordered resumable unit (checkpoint boundary) | FK job RESTRICT; UNIQUE `(job_id, step_code)`, `(job_id, position)`; CHECK state/step_type |
| `job_attempt` | Append-only attempt history (§8.2) | FK job/step RESTRICT; UNIQUE `(job_id, step_id, attempt)` and `(job_id, step_code, attempt)` |
| `job_event` | Append-only transition log (§10.2) | FK job/step RESTRICT; CHECK actor; index `(job_id, created_at)` |
| `job_lease` | Exclusive worker claim (§5) | PK `job_id` FK RESTRICT; CHECK lease_version/ttl/expiry ordering |

**Idempotency uniqueness (PM-corrected):** a SQLite **partial unique index**

```sql
CREATE UNIQUE INDEX uq_job_idempotency_key
  ON job (workspace_id, idempotency_key, input_generation)
  WHERE idempotency_key IS NOT NULL AND state NOT IN ('failed','cancelled');
```

- Enforces **one active or completed Job per `(workspace_id, idempotency_key,
  input_generation)`** (contract §8.1/§8.5).
- Terminal `failed`/`cancelled` predecessors are **excluded from the index**,
  so they retain their full immutable audit identity (key + generation +
  manifest + timestamps + error envelope + revision) while a successor
  reusing the same key and generation can be inserted.
- Non-idempotent Jobs (NULL key) never collide.

**Downgrade** raises `RuntimeError` ("not reversible") — recovery is backup
restore, never a lossy downgrade (PERSISTENCE_DOMAIN_CONTRACT §7).

## 2. ORM models

`app/persistence/models.py` gains `Job`, `JobStep`, `JobAttempt`, `JobEvent`,
`JobLease` (plus `Workspace.jobs`). All follow the S01 conventions: VARCHAR(36)
opaque ids, UTC timestamps, integer `revision` starting 1, string enums with
CHECK constraints. The models exactly mirror the migration (verified by
`test_orm_matches_migrated_schema`).

## 3. Repository — `app/persistence/jobs.py`

`JobRepository(session)` — pure persistence; the **caller owns the
transaction** (domain contract §6). No commits inside the repository.

### Creation (AC3)

- `create_job(...)` inserts the Job, its validated step plan and a `created`
  JobEvent in **one transaction**. Step validation (duplicate codes/positions,
  unknown dependencies, cycles, self-dependency) happens before any insert, so
  a bad plan writes nothing.
- Duplicate key handling per §8.1:
  - existing **completed** Job with same `(workspace, key, generation)` ⇒
    returns the existing Job (no duplicate);
  - existing **active** Job ⇒ `IdempotencyKeyInUse` (`409`);
  - fresh logical run ⇒ caller bumps `input_generation` (independent key).
- `create_successor(...)` — retry of a **terminal failed/cancelled** Job:
  - fresh `id`, same `job_type`/owner/workspace, same `idempotency_key` **and**
    same `input_generation`, `predecessor_job_id` = predecessor id;
  - **never mutates the predecessor row** (PM regression: every field and
    revision asserted unchanged after successor creation);
  - at most one successor per predecessor (unique `predecessor_job_id` + a
    pre-check that turns the raw IntegrityError into `IdempotencyKeyInUse`;
    concurrent successors race the unique constraint and exactly one wins —
    verified by `test_concurrent_successor_creation_yields_exactly_one`);
  - a **completed** predecessor is never retried — the completed Job is
    returned (reuse semantics);
  - a non-terminal predecessor raises `InvalidStateTransition`.

### Guarded transitions (AC4)

- `transition_job` / `transition_step` validate, in order:
  1. endpoint exists in the transition table (`JOB_TRANSITIONS` /
     `JOB_STEP_TRANSITIONS` — closed sets from contract §4.3/§4.4);
  2. current state is not terminal (rows are immutable, §4.5-4);
  3. `expected_revision` matches the row's revision (optimistic concurrency);
  4. actor is a known actor;
  5. **worker** transitions require the current fence token (contract §5.3-1:
     the token is the enforcement point). Scheduler/reconciler/system
     authority transitions (e.g. `running → fenced`, `fenced → queued`) do
     not carry a worker token.
- Every accepted transition: `revision += 1`, `started_at` on first
  `running`, `finished_at` on terminal, error envelope on `failed`, and a
  `JobEvent` (actor, worker_id, fence_token, revision) **in the same
  transaction**.
- Errors carry stable codes: `INVALID_STATE_TRANSITION`,
  `IDEMPOTENCY_KEY_IN_USE`, `FENCED_WORKER`.

### Leases (AC5, PM-corrected — atomic CAS)

- `acquire_lease`: **guarded compare-and-swap**, not SELECT-then-merge:
  1. atomic `INSERT ... ON CONFLICT DO NOTHING` on `job_lease` — the single
     guarded write that decides the race; exactly one session inserts
     `lease_version=1`, the rest fall through;
  2. a live unexpired lease held by ANY worker (self or another) is rejected
     with `LeaseConflictError` (`LEASE_CONFLICT`); only absent or
     expired/released leases may be acquired (§5.3-2);
  3. reacquisition of an expired/released lease is an atomic guarded UPDATE
     matching the exact current `lease_version` and requiring `expires_at <=
     now` (SQL-side comparison); it monotonically bumps `lease_version` **and
     the Job's `revision`** and issues a fresh random `fence_token` (§5.1).
- Real two-session race test (`test_two_session_lease_race_exactly_one_claimant`)
  uses a threading barrier so both sessions claim concurrently — exactly one
  wins, the other receives `LeaseConflictError`, one lease row remains.
- `heartbeat_lease`: extends `expires_at` by TTL (default 60s), updates
  `ttl_seconds`; token mismatch ⇒ `FencedWorkerError`.
- `release_lease`: graceful release — `expires_at = now` (safe re-claim from
  checkpoint, §5.3-5); the CHECK is `expires_at >= acquired_at` so a released
  lease remains valid.
- `_require_fence_token`: any worker write without a token or with a stale
  token is rejected (`FENCED_WORKER`).

### Worker-owned writes are always fenced (PM-corrected)

Every repository write a worker can invoke while the Job is
`running`/`cancelling` calls `_require_fence_token` **unconditionally** —
missing AND stale tokens both raise `FENCED_WORKER` (contract §5.3-1):

- `transition_job` / `transition_step` (worker actor)
- `update_progress(job_id, progress, fence_token=...)`
- `update_step_progress(step_id, progress, fence_token=...)`
- `write_checkpoint(step_id, checkpoint, fence_token=...)`
- `record_attempt(..., fence_token=...)` (attempt completion/error)
- `set_job_error(job_id, error, fence_token=...)`

Explicit tests `test_missing_token_rejected_on_worker_writes` and
`test_stale_token_rejected_on_worker_writes` cover all five write paths with
missing and stale tokens, and assert nothing was persisted.

### Attempts, progress, checkpoints, errors

- `record_attempt`: append-only row; duplicate `(job, step, attempt)` rejected
  by unique constraint.
- `update_progress` / `update_step_progress`: bounded 0..100 (§7.3).
- `write_checkpoint`: requires `schema_version` (fail-closed §7.2); fenced
  against the lease when the Job is running/cancelling.
- `set_job_error`: persists the final error envelope (§10.1).

### Delete

- `delete_job` only for active rows; terminal rows refuse
  (`JobAlreadyTerminalError` — immutability, not a data-loss path).

## 4. Migration safety (AC2)

- Fresh upgrade empty → head: PASS (twice on independent DBs).
- Upgrade from S01 revision preserves existing rows: PASS.
- Downgrade refuses: PASS.
- Database reopen preserves jobs, steps, attempts, events, leases: PASS.
- The S01 revision alone has **no** Job tables (`test_s01_revision_has_no_job_tables`
  upgrades exactly to `a1b2c3d4e5f6` and asserts absence); the S02 head adds
  the five durable tables.

## 5. Validation evidence (this task)

| Command | Result |
|---|---|
| `python -m pytest -q tests/test_durable_job_persistence.py` | 47 passed |
| `python -m pytest -q tests/test_persistence_bootstrap.py tests/test_durable_job_persistence.py` | 66 passed |
| `python -m ruff check app tests` | All checks passed |
| `python -m mypy app` | Success, 49 source files |
| `git diff --check` | PASS |
| `scripts/quality-baseline.ps1` | 7/7 gates PASS (see session LOG) |
| `sha256sum channels.json` | UNCHANGED (byte-for-byte preserved) |

## 6. Out of scope (future tasks)

- Worker loop, claim → execute → heartbeat → publish (S02-T03).
- Retry/backoff engine and cooperative cancel flag propagation (S02-T03).
- Reconciler: lease scan, fencing resolution `fenced → queued|failed`,
  checkpoint resume (S02-T04).
- API cutover, compatibility shim, integration recovery tests (S02-T05).
