# Durable Job State-Machine Contract V1.1

**Status:** Approved for S02 implementation
**Changes in v1.1:** successor-Job retry model (terminal rows immutable);
JobStep `cancelled` state added and transition table aligned; final-output vs
checkpoint-artifact visibility split; transition-endpoint invariant audit
(§14); invariants 7–9 added (§15).
**Scope:** Job/JobStep identity, lifecycle state machine, leases and fencing,
retry/cancel semantics, idempotency, checkpoints, artifact staging/publication,
transaction boundaries, error envelope, observability, API/domain compatibility
with the legacy in-memory service, and S02-T02..T05 ownership split.
**Epic:** E01 — Durable Domain, Persistence and Jobs
**Sprint:** S02 — Durable processing
**Supersedes:** nothing (S01-PERSISTENCE_DOMAIN_CONTRACT.md §9 explicitly
deferred Jobs/JobSteps/retries/leases/cancellation/restart reconciliation to
this contract).

This document is a **contract only**. It adds no engine, ORM models,
migrations, repositories, workers, APIs or runtime cutover. The in-memory
`JobService` (`app/workflow/job_service.py`) and the JSON filesystem remain the
runtime authority until S02-T02..T05 land and are explicitly committed.

---

## 1. Purpose and design intent

MotionForge needs long-running background work (analysis, tracking, reskin
preview/apply, render, QC) that must survive process restart, run concurrently
without corrupting output, and never present partial output as complete
(PRODUCT_REQUIREMENTS_V2 §14; MASTER_PLAN_V1 §5.6, §7.2, Scenario G).

Design intent, in priority order:

1. **Durability before speed.** Job/JobStep state and all business effects are
   persisted transactionally; a crash at any point leaves the job resumable or
   safely failed, never falsely completed.
2. **One writer per job.** The lease grants exclusive execution; every state
   change is an atomic guarded update.
3. **Idempotent effects.** No matter how many times a step runs, visible
   effects (entities, artifacts, downstream triggers) occur at most once.
4. **Cancellation is cooperative and observable.** Cancel is a request with a
   bounded wait; the job reaches a terminal state on its own or is force-fenced
   by the reconciler after the lease expires.
5. **No partial output masquerades as ready.** Outputs are staged and
   validated; an artifact becomes `ready` only after atomic publication, and a
   Job reaches `completed` only after every output is published and validated.

---

## 2. Terminology

| Term | Meaning |
|---|---|
| Job | Durable unit of user-visible work (e.g. `RENDER_VARIANT`, `APPLY_RESKIN`). |
| JobStep | Ordered, resumable unit inside a Job. Checkpoint boundary. |
| Step code | Stable logical name of a step (e.g. `probe`, `chunk_0_100`); never a display string. |
| Resource class | Declared capacity requirement (`cpu_light`, `cpu_heavy`, `gpu`, `io`). |
| Lease | Exclusive claim by one worker over a Job for a bounded time window. |
| Fencing | Mechanism preventing a stale worker from mutating state after its lease expires. |
| Attempt | One execution of a JobStep, numbered 1..N within the Job. |
| Idempotency key | Deterministic key derived from Job type + input identity (+ generation). |
| Checkpoint | Persisted, versioned step payload that fully describes what remains. |
| Staging | Pre-publication artifact state; not visible as a completed output. |
| Publication | Atomic transition of an artifact from staging to `ready` (or a Job output set to visible). |

---

## 3. Job identity, ownership and static attributes

| Attribute | Contract |
|---|---|
| `id` | Opaque public ID, `VARCHAR(36)` (UUIDv7-compatible; UUID4 acceptable initially). Never a legacy id. |
| `workspace_id` | Required FK to `workspace` (RESTRICT on delete). Jobs are scoped to exactly one workspace. |
| `job_type` | Stable code from the approved job-class list (MASTER_PLAN_V1 §7.2): `ANALYZE_MEDIA`, `DISCOVER_OBJECTS`, `TRACK_OCCURRENCES`, `GROUP_OBJECTS`, `GENERATE_RESKIN_PREVIEW`, `APPLY_RESKIN`, `GENERATE_CHARACTER_CONTACT_SHEET`, `GENERATE_CHARACTER_PANEL`, `VALIDATE_CHARACTER_PACK`, `ATTACH_ORIGINAL_AUDIO`, `RUN_QC`, `RENDER_VARIANT`, `VALIDATE_OUTPUT`, `CLEANUP`. New job types require an approved contract change. |
| `owner_type`, `owner_id` | Polymorphic owner (`project`, `video_item`, `character`, ...) matching the S01 `artifact_owner` pattern; owner must exist and be in the same workspace. |
| `parent_job_id` | Nullable self-reference for sub-job composition (e.g. a render batch's children). Child jobs inherit the parent's workspace. |
| `predecessor_job_id` | Nullable reference to the terminal Job this Job replaces (retry/restart successor). One successor per predecessor; cycle rejected. See §6.4 and §8.5. |
| `resource_class` | `cpu_light`, `cpu_heavy`, `gpu`, `io`. Used by the scheduler for capacity; `gpu` jobs are serialized per GPU. |
| `priority` | Integer, default 50, range [0..100], higher = sooner. Priority affects scheduling order only; it never changes correctness semantics. |
| `idempotency_key` | `job_type + ":" + canonical input identity + ":" + input generation`. Nullable — set when the caller demands exactly-once semantics (FR-02 import, FR-09 retry, render variant). See §8. |
| `input_manifest_json` | Versioned, schema-tagged input identity (source artifact ids, variant config, model/asset versions). Read-only after creation. |
| `created_at`, `updated_at`, `started_at`, `finished_at` | UTC timestamps. `started_at` set on first RUNNING claim; `finished_at` set exactly once when a terminal state is written. |
| `revision` | Integer, starts 1, increments on every business update (S01 optimistic concurrency). |

### JobStep static attributes

| Attribute | Contract |
|---|---|
| `id` | Opaque public ID, `VARCHAR(36)`. |
| `job_id` | Required FK to `job` (RESTRICT). |
| `step_code` | Stable logical code; unique within a Job (ordering key). |
| `position` | Non-negative integer; the Job's execution order. |
| `step_type` | `sync` (executes inside the worker's transaction) or `async` (spawns a long sub-process; completion re-enters via a finish event). |
| `depends_on` | Nullable list of step codes that must be `completed` first (Job-level DAG; cyclic dependencies rejected at creation). |
| `resource_class`, `priority` | Inherited from the Job unless overridden. |
| `attempt` | Current attempt number, starts 0, incremented on each (re)start, max per Job. |
| `checkpoint_json` | Versioned resume payload written by the step (`{"schema_version": N, ...}`); never a second source of truth for domain state. |
| `started_at`, `finished_at` | UTC timestamps per attempt window. |
| `revision` | Optimistic concurrency counter. |

Invariants:

- Job and JobStep IDs are generated by the persistence layer, never client-supplied.
- `depends_on` may only reference steps of the same Job.
- A JobStep cannot be deleted while its Job is not terminal.
- Public API never accepts a Job's `revision` from the client; it is internal.
- `input_manifest_json` and `checkpoint_json` are schema-versioned; a reader that does not know the version fails closed (refuses to resume rather than guessing).

---

## 4. State machine

### 4.1 Job states

| State | Meaning |
|---|---|
| `pending` | Created, not yet eligible (dependency not satisfied). |
| `queued` | Eligible, waiting for a worker slot. |
| `running` | A worker holds a valid lease and is executing. |
| `cancelling` | Cooperative cancellation requested while running/queued; worker is draining, must not start new effects. |
| `cancelled` | Terminal. Cooperative stop completed; effects idempotently rolled back or marked cancelled. |
| `completed` | Terminal. Every step `completed`; every output artifact published and validated. |
| `failed` | Terminal. Non-retryable failure or retries exhausted. |
| `fenced` | Terminal-safe intermediate: lease expired with no heartbeat while `running`; the reconciler must re-queue or fail the Job. `fenced` is not user-visible in the API; it is folded into `queued` (retry) or `failed` (exhausted) by the reconciler before the API observes it. |

`pending`/`queued`/`running`/`cancelling` are **active**; `cancelled`/`completed`/
`failed` are **terminal**; `fenced` is **transient-recovery**.

### 4.2 JobStep states

| State | Meaning |
|---|---|
| `pending` | Not started. |
| `ready` | Dependencies satisfied; eligible for execution. |
| `running` | A worker holds the Job's lease and is executing this step. |
| `cancelling` | Cancel requested; the step is draining and will not start new effects. |
| `completed` | Terminal; effects published. |
| `failed` | Terminal; this attempt failed (retry may create a new attempt). |
| `cancelled` | Terminal; the step drained on a cancel and started no new effects. The Job's `cancelled` state requires every non-`completed`/`skipped` step to be `cancelled`. |
| `skipped` | Terminal; step not executed (e.g. optional step pruned by a checkpoint). |

### 4.3 Full Job transition table

| From | To | Guard | Actor | Effect/notes |
|---|---|---|---|---|
| `pending` | `queued` | All `depends_on` Jobs terminal-`completed` (or none) | scheduler | Initial enqueue. |
| `queued` | `running` | Lease acquired; `revision` match | worker | Sets `started_at` on first claim; increments step attempt. |
| `queued` | `cancelling` | none | API/user | Cancel request accepted while queued. |
| `queued` | `cancelled` | — | worker | Worker drains and confirms cancel (no effects started). |
| `running` | `cancelling` | none | API/user | Cooperative cancel request. |
| `running` | `completed` | All steps `completed`; all declared outputs published & validated | worker | Sets `finished_at`; increments `revision`. |
| `running` | `failed` | Non-retryable error OR attempts exhausted; cancel not pending | worker/reconciler | Error envelope persisted; `finished_at`. |
| `running` | `fenced` | Lease expiry/heartbeat timeout | reconciler | Lease row invalidated; worker must not act further. |
| `running` | `cancelled` | Cancel confirmed by worker while draining | worker | All started effects idempotently reverted/marked; **final outputs never published**; checkpoint artifacts of completed steps retained (§9.5). |
| `cancelling` | `cancelled` | Worker observed cancel flag and drained | worker | Terminal. |
| `cancelling` | `running` | Cancel rejected by worker within grace (optional) | worker | Rare; documented escape hatch for non-cooperative steps. |
| `cancelling` | `failed` | Non-retryable error during drain | worker | Terminal with error envelope. |
| `cancelling` | `fenced` | Lease expiry during drain | reconciler | Same fencing as running. |
| `fenced` | `queued` | Attempts remain AND inputs unchanged (idempotency key intact) | reconciler | Requeue; step attempt count incremented at next claim. |
| `fenced` | `failed` | Attempts exhausted OR idempotency key invalidated | reconciler | Terminal; error envelope `FENCED/EXHAUSTED`. |
| terminal | (any) | — | nobody | **No transitions out of terminal states. Rows are immutable once terminal.** Retry/restart of a terminal Job is a NEW Job (successor) linked via `predecessor_job_id`; see §6.4 and §8.5. |

Invalid transitions are rejected with `409 Conflict` and a stable error code
(`INVALID_STATE_TRANSITION`). No transition bypasses the lease check while the
Job is `running`/`cancelling`.

### 4.4 Full JobStep transition table

| From | To | Guard | Actor |
|---|---|---|---|
| `pending` | `ready` | All `depends_on` steps `completed`/`skipped` | scheduler |
| `pending` | `skipped` | Checkpoint prunes this optional step | worker |
| `ready` | `running` | Job lease held | worker |
| `running` | `completed` | Effect published + checkpoint written | worker |
| `running` | `failed` | Error raised; attempt result recorded | worker |
| `ready`/`running` | `cancelling` | Job cancel observed | worker |
| `cancelling` | `cancelled` | Drained; no new effects | worker |
| `cancelling` | `failed` | Error during drain | worker |
| `running`/`cancelling` | `ready` | Lease lost (fenced); attempt rolled back | reconciler |
| `failed` | `ready` | Retry permitted; attempts remain | worker (on re-claim) |

A JobStep has **no** direct transition to Job terminal states; the Job terminal
decision is always computed from the step set: all `completed`/`skipped` →
Job `completed`; any unrecoverable `failed` (retries exhausted) → Job `failed`;
drain complete with all remaining steps `cancelled`/`skipped` and no new
effects → Job `cancelled`. A step that was `running` when the Job was fenced
returns to `ready` (attempt rolled back) — the Job itself transitions
`running → fenced → queued|failed` independently.

### 4.5 Terminal-state invariants

1. `completed` ⇒ every step is `completed` or `skipped`, every declared **final
   output** artifact is `ready` with matching sha256/size, and the Job's
   `finished_at` is set. A Job whose outputs failed validation **cannot** be
   `completed` (FR-09: "Completed chỉ sau validation").
2. `failed` ⇒ an error envelope exists with stable code + message + failing
   step, and no **final output** was published as `ready` by this Job's failed
   attempt (partial/staging artifacts stay `staging` or move to `trash`).
   Durable intermediate checkpoint artifacts from completed steps may remain
   `ready` (see §9.5); they are never exposed as Job final output.
3. `cancelled` ⇒ the Job exposes **no final output**; no artifact linked to
   this Job with an output purpose (`render`, `final`, `result`) is `ready`.
   Durable intermediate checkpoint artifacts (purpose `checkpoint`,
   `intermediate`) from steps that completed before the cancel may remain
   `ready` and are retained for a future successor Job (see §9.5). All
   partial/staging outputs are reverted or trashed; none may ever appear
   complete.
4. Terminal rows are immutable: no field changes, no re-run, no delete except
   a future explicit retention/cleanup workflow. A retry/restart of a terminal
   Job is **always a new Job** (successor) linked through `predecessor_job_id`
   (§6.4, §8.5) — never a mutation of the terminal row.
5. `revision` increments on **every** state change; a guarded update uses
   `WHERE id = ? AND revision = ?` and retries the read only when the state
   machine allows it.
6. `fenced` is never visible through the API: the reconciler resolves it to
   `queued` or `failed` before any poll sees it.

---

## 5. Leases, heartbeat and fencing

### 5.1 Lease model

- A lease is a row in the lease store keyed by `job_id`:
  `worker_id, acquired_at, expires_at, heartbeat_at, lease_version, fence_token`.
- `worker_id` is a unique per-process/per-pod identifier (hostname + boot id +
  random suffix), generated once at worker start.
- `fence_token` is a fresh random value written on **every** lease acquisition
  (re-claim included). Workers must present the current token with every
  guarded write; a mismatch ⇒ the write is rejected (fenced).
- `lease_version` is a monotonic counter incremented on each acquisition;
  workers use it for optimistic concurrency on the lease row itself.

### 5.2 Acquisition and renewal

- Worker claims `queued` jobs atomically:
  `UPDATE job SET state='running' WHERE id=? AND state='queued'` (or
  `fenced`→`queued` transition first), then inserts/replaces the lease row
  with `expires_at = now + lease_ttl`.
- Defaults (configurable per resource class): `lease_ttl = 60s`, heartbeat
  interval `= 15s`, heartbeat timeout `= 90s` (3 missed beats). `gpu` jobs
  may extend TTL; never above a hard cap so a dead worker is fenced in
  bounded time.
- Heartbeat updates `heartbeat_at` and extends `expires_at` to
  `now + lease_ttl`; the heartbeat row update carries the worker's
  `fence_token` and fails if the token no longer matches.

### 5.3 Stale-worker fencing rules

1. The **fence token check is the enforcement point**, not the timestamp.
   Any state write from a worker whose token does not match the current lease
   row is rejected with `FENCED_WORKER` and the write is dropped. Timestamps
   only decide *when* the reconciler reclaims.
2. The reconciler (S02-T04) periodically scans leases:
   - `expires_at < now` and no valid heartbeat ⇒ it atomically invalidates the
     lease (bumps `lease_version`, clears `fence_token`) and transitions the
     Job `running|cancelling` → `fenced`, then resolves:
     - attempts remain + idempotency key intact ⇒ `fenced → queued`
       (requeue; step attempt count incremented at next claim);
     - otherwise ⇒ `fenced → failed` with error envelope
       `WORKER_FENCED`, `RETRIES_EXHAUSTED`, or `INPUT_CHANGED`.
3. A fenced worker that later wakes and tries to write receives
   `FENCED_WORKER`; it must abort its attempt silently (log + release
   resources) and **must not** publish artifacts.
4. Lease acquisition is atomic (single guarded UPDATE on the lease row); two
   workers can never hold the same Job lease.
5. Graceful shutdown: worker marks the lease released (`expires_at = now`)
   and the Job back to `queued` **only** if it is safe to re-claim from the
   current checkpoint (always true for steps that wrote checkpoints
   transactionally with their effects).

### 5.4 Worker crash mid-write

Because every effect is transactional (see §7), a crash between "effect
committed" and "state updated" is detected on restart by replay of the
Job's idempotency key: the effect already exists ⇒ the update is applied
without re-executing the effect. A crash before the effect commit ⇒ the
effect is absent ⇒ the step re-runs from its checkpoint. This is the
**replay-safe window**; it is closed by doing effect + state update in the
same transaction whenever the effect is a database write (see §7).

---

## 6. Retry, cancellation and their races

### 6.1 Retry classification

Errors are classified by a stable `error_code` in the envelope:

| Class | Codes (examples) | Behavior |
|---|---|---|
| `transient` | `BUSY_LOCK`, `NETWORK_TIMEOUT`, `PROVIDER_429`, `DISK_FULL` (when space freed by cleanup), `GPU_OOM` (chunk retry) | Automatic retry with bounded backoff, up to `max_attempts` (default 3; per job type). |
| `permanent` | `INPUT_MISSING`, `SCHEMA_MISMATCH`, `VALIDATION_FAILED`, `UNSUPPORTED_CODEC`, `FENCED_WORKER`-with-exhausted-attempts | No automatic retry; Job → `failed`. Manual retry allowed only if the job type declares `retryable=true`. |
| `cancel` | `CANCELLED` | Only via the cancel path; never retried. |

- Backoff: exponential `1s, 4s, 16s` (+ jitter ≤ 20%); the Job stays
  `failed` (attempt exhausted) only after `max_attempts` — intermediate
  failures reset the step to `ready` and increment `attempt`.
- `max_attempts` is per Job (stored at creation; default 3), not per step, so
  a pathological loop cannot burn unlimited work.
- GPU OOM is special: it is `transient` **only** if the job type declares
  chunked execution; otherwise `permanent`.

### 6.2 Cancel semantics

- `POST /api/jobs/{id}/cancel` (legacy route shape, see §11) sets a durable
  cancel flag when the Job is `pending|queued|running|cancelling` and
  transitions to `cancelling`; a `409` otherwise.
- Cancellation is **cooperative**: the worker checks the flag at step
  boundaries and at every checkpoint; a step in flight finishes its current
  unit of work (or is interrupted by its subprocess) and then drains.
- Cancel-during-queued: no effects started ⇒ worker marks `cancelled` without
  executing.
- Cancel-during-running: current step may complete its current unit; the next
  step is not started; already-published effects of *earlier* steps remain
  (they are durable), later effects are not created. The Job reaches
  `cancelled` only when the drain finishes; until then it is `cancelling`.

### 6.3 Retry/cancel race matrix (decided)

| Race | Decision |
|---|---|
| Cancel arrives while a retry is scheduled | Cancel wins. The retry is not started; Job → `cancelling` → `cancelled`. |
| Worker completes the final step at the same instant cancel is set | Completion wins only if the terminal `completed` write happened-before the cancel flag write (serialized by the DB: first writer wins). If `completed` was written first, cancel returns `409`; the Job stays completed. If the flag was written first, the worker's completion write is rejected (`INVALID_STATE_TRANSITION`) and the Job cancels. |
| Cancel arrives during a transient retry backoff | The cancel flag is set; the scheduled re-claim sees it and transitions to `cancelled` without re-running. |
| Retry decision (reconciler) races a manual cancel | Same rule as above: first committed writer wins; the loser receives a conflict and re-reads. |
| Stale worker completes after being fenced | Its writes are rejected by the fence token; artifact publication is refused; reconciler resolves `fenced` → `queued`/`failed` independently. |
| Manual retry of a `failed` Job while a leftover worker is still draining | The retry cannot acquire the lease until the old lease expires (token mismatch); the reconciler fences the stale worker first. The retry re-claims only from a valid checkpoint. |
| Cancel requested twice | Second cancel is a no-op `200`-style idempotent response while `cancelling`; `409` once terminal. |

All race resolutions are implemented with the guarded-write pattern
(`WHERE state = expected`), so they hold under concurrency without global
locks.

### 6.4 Retry/restart of a terminal Job (successor model)

Terminal Jobs are immutable (invariant 4.5-4); retrying or restarting one
**never mutates the terminal row**. Instead:

1. A retry/restart request creates a **new Job** (the successor) with:
   - the same `job_type`, `owner_type/owner_id`, `workspace_id`,
     `resource_class`, `priority` and `input_manifest_json`;
   - `predecessor_job_id` = the terminal Job's id;
   - a fresh `id`; the same logical `idempotency_key` **generation** — see
     §8.5 for the uniqueness rule;
   - `attempt = 0` (fresh attempt accounting) and a fresh step plan.
2. The successor's first step set is computed by checkpoint replay: steps
   already durably `completed` in the predecessor (with valid checkpoint
   artifacts) are re-linked or skipped; only unfinished work re-runs
   (§9.5). The predecessor row is never rewritten.
3. While the successor is active, the predecessor remains immutable and
   queryable; its final output (if any was published before failure) stays
   valid and is not deleted by the retry.
4. A successor may itself be retried, forming a chain
   `A → B → C` via `predecessor_job_id`; cycles are rejected at creation
   (a Job can never be its own ancestor). Only the newest Job in a chain is
   active; the others are terminal.
5. Cancel of a successor does not affect the predecessor's terminal state or
   its retained checkpoint artifacts; those artifacts may be reused by a
   later successor (§9.5).

---

## 7. Transactions, checkpoints and replay safety

### 7.1 Transaction boundaries

- **State change transaction:** every Job/JobStep/lease write is one short
  SQLite transaction; `busy_timeout` bounded (S01 §6); retry only for known
  transient lock errors, never duplicating entities.
- **Effect transaction:** a step's business effects (rows in
  project/video_item/scene/artifact tables) are committed in **one**
  transaction per step (or per chunk, if the step is chunked).
- **State+effect coupling rule (the core durability rule):**
  - If the effect is a database write ⇒ effect and state update happen in
    **the same transaction** (effect commit + step `completed` + checkpoint +
    artifact publication row are one commit). This closes the replay window.
  - If the effect is a long subprocess/GPU run (async step) ⇒ the subprocess
    writes only to **staging paths**; the state update transaction (step
    `completed`, checkpoint, artifact publication) runs only after the
    subprocess exits 0 and the output passes validation. A crash mid-run
    leaves only staging files; they are garbage-collected by the next attempt
    or by `CLEANUP`.
- **Checkpoint transaction:** a checkpoint is persisted in the same
  transaction as the progress/state it belongs to. A checkpoint that is
  newer than the last committed effect is never trusted (replay starts from
  the last committed checkpoint).

### 7.2 Checkpoint contract

- `checkpoint_json` = `{"schema_version": N, ...}`; written by the step at
  safe boundaries (per chunk, per scene, per variant) **and** atomically with
  the corresponding effect commit.
- Resume rule: on re-claim after fence/restart, the worker loads the last
  committed checkpoint and re-runs **only** uncommitted work; committed work
  is skipped by idempotency replay (§8.4).
- A checkpoint must be self-contained enough to resume without the original
  in-memory state (no closures, no thread handles; only ids, paths, offsets,
  counters).
- Checkpoint schema bumps are backward-compatible reads (defaults) or a
  documented `resume_required = false` (start over) decision; a reader that
  cannot parse the version fails closed.

### 7.3 Progress and ETA

- `progress` is `float 0..100`; steps declare their weight (`weight_sum` per
  Job sums to 100). Job progress = Σ(step weight × step progress); ETA is
  derived from progress deltas over wall-clock time, never persisted as a
  truth field.
- Progress updates are persisted with the checkpoint cadence (bounded write
  rate — no per-frame writes for 4K work).

---

## 8. Idempotency and attempt accounting

### 8.1 Idempotency keys

- `idempotency_key = job_type + ":" + canonical_input_identity + ":" + input_generation`.
  Canonical input identity is a stable serialization of the input manifest
  (artifact ids, variant config, model/asset versions); `input_generation`
  distinguishes explicit re-runs of the same inputs (e.g. "rerun user
  changed nothing but demanded re-render").
- `(workspace_id, idempotency_key)` is **unique among terminal Jobs too**:
  the key identifies the logical work. Creating a Job with an existing key:
  - if the existing Job is terminal-`completed` ⇒ returns the existing Job
    (no duplicate);
  - if active ⇒ `409 IDEMPOTENCY_KEY_IN_USE`;
  - if the existing Job is terminal-`failed`/`cancelled`, the caller may
    create a **successor Job** that reuses the same key **and the same
    generation**, linked via `predecessor_job_id` (§6.4). The uniqueness
    rule is: **one active or completed Job per (workspace, key,
    generation)**; any number of terminal `failed`/`cancelled`
    predecessors may share the key, each with exactly one successor in the
    chain (§8.5). A caller demanding a *fresh* logical run (new inputs, or
    "re-render even though nothing changed") bumps `input_generation`,
    which yields a different key.
- The key is set at creation and immutable for the Job's life. The
  predecessor's key and the successor's key are equal when the successor
  reuses the generation; the successor is still a distinct row with a
  distinct `id`.

### 8.2 Attempt accounting

- `attempt` (Job-level) and per-step attempt counters are durable columns.
- Every re-claim (requeue after fence, retry after failure) increments the
  step's attempt counter in the same transaction that acquires the lease.
- `max_attempts` enforced at claim time: if `attempt >= max_attempts` and the
  step is not `completed`, the Job goes `fenced|failed → failed` with
  `RETRIES_EXHAUSTED`.
- Attempt history (attempt number, started_at, finished_at, result/error,
  worker_id, fence_token) is persisted for observability; it is append-only.

### 8.3 Duplicate-effect prevention

- Any step that creates entities or artifacts derives deterministic ids from
  (job_id, step_code, chunk_index) or reuses the idempotency key namespace —
  never random UUIDs on retry. Re-running a step with the same inputs
  produces the same ids and updates in place (upsert semantics) instead of
  duplicating rows.
- Side-effectful external calls (provider APIs, uploads) are guarded by the
  idempotency key of the step; a retried step reuses the recorded external
  handle/result when present.

### 8.4 Replay-safe window closure

- DB effects: same-transaction rule (§7.1) — no replay window.
- Filesystem effects: staged writes are keyed by (job_id, step_code, target);
  on retry, existing staged files with matching hash are reused; a partial
  staged file is overwritten. Publication (rename to final) happens once per
  (job_id, step_code, target) and is recorded in the artifact row within the
  effect transaction — a retry that finds the artifact row `ready` skips
  publication.
- Subprocess effects: the finish event carries the subprocess's
  `run_id` (random per attempt); duplicate finish events for the same
  attempt are ignored (unique `(job_id, step_code, run_id)`).

### 8.5 Successor-chain uniqueness and accounting

- A successor Job reuses the predecessor's `idempotency_key` **and**
  generation (§6.4). Uniqueness is enforced as: at most **one** Job with a
  given `(workspace_id, idempotency_key)` may be active (non-terminal) at
  any time; at most **one** Job with that key may be terminal-`completed`
  (the newest completed run wins); any number of terminal-`failed` /
  `cancelled` predecessors may exist, each having **at most one** successor
  (`predecessor_job_id` is unique per predecessor).
- Creation of a successor is guarded: `INSERT ... WHERE` no active Job and
  no newer completed Job exists for the key, and the referenced predecessor
  is terminal. Violations return `409 IDEMPOTENCY_KEY_IN_USE`.
- The chain `A → B → C` is acyclic by construction (each Job records at most
  one predecessor; a Job may not reference a Job that transitively
  references it back).
- The successor starts `attempt = 0`; `max_attempts` applies per Job, so a
  successor that fails again is itself retryable as a new successor —
  total work across a chain is bounded by (chain length × max_attempts) and
  remains user-visible and auditable.
- Attempt history and `job_event` records carry `job_id`, so a chain's full
  audit trail is the union of each Job's records, linked by
  `predecessor_job_id`.

---

## 9. Artifact staging and publication

### 9.1 Staging

- During execution, outputs are written to staging paths under the managed
  root (`staging/<job_id>/<step_code>/...`) using S01-T03 `ManagedRoot`
  atomic writes (same-directory temp, fsync, atomic rename within the
  staging area).
- Staging artifacts are **never** linked as ready outputs, never exposed as
  job results, and never included in "latest output" queries.

### 9.2 Publication

A step output becomes a real artifact only through a **publication
transaction**. Every published artifact carries a `purpose` (in
`artifact_owner.purpose`, S01 §4) that fixes its visibility class:

| Purpose | Visibility class | Exposed as Job final output? |
|---|---|---|
| `checkpoint` | intermediate checkpoint artifact | never |
| `intermediate` | intermediate data (masks, crops, probes) | never |
| `preview` | user-visible preview | only via explicit preview UI, never as the Job result |
| `render`, `final`, `result` | **final output** | yes — exactly what `completed` requires and what cancel/fail forbids |

Publication steps:

1. Validate: file exists at the staging path; sha256 + size match what the
   step declared; media probe (if applicable) passes.
2. Move (atomic rename) staging → final managed path
   `artifacts/<workspace_id>/<kind>/<job_id>/<step_code>/<name>`.
3. Insert/update the `artifact` row (`state=ready`, sha256, size, mime,
   relative_path) **and** the `artifact_owner` link with the correct
   `purpose` **and** the step `completed` state **in one transaction**.
4. Only after that commit may the Job transition `running → completed`.

Failure at any point leaves the artifact row `staging`/absent and the file
either in staging or absent — never a `ready` row pointing at a missing or
partial file (S01 invariant: a row becomes `ready` only after the atomic
filesystem write succeeds; here the write is the rename into the final path).

### 9.3 Job-level completion gate

- `completed` requires **all** declared **final-output** artifact rows `ready`
  and linked (purpose `render`/`final`/`result`, §9.2), and — for
  `RENDER_VARIANT`/`VALIDATE_OUTPUT` — the output
  validation step `completed` (MASTER_PLAN_V1 exit: "no `.partial` file is
  presented as complete"; PRD: "Completed chỉ sau validation").
- A Job whose publication transaction failed (e.g. disk full at rename) goes
  `failed` with `PUBLICATION_FAILED`; partial outputs remain `staging` and
  are cleaned by `CLEANUP` or the retry.

### 9.4 Cleanup

- `CLEANUP` jobs and the reconciler garbage-collect `staging/` older than a
  configurable TTL (default 24h) and orphaned `staging` artifact rows; they
  never touch `ready` artifacts or their owners.
- Trash/restore of published artifacts follows S01-T03 `ManagedRoot`
  semantics (recovery manifest, containment checks).

### 9.5 Intermediate checkpoint artifacts on cancel/fail

- **Retention:** when a Job reaches `cancelled` or `failed`, artifacts with
  purpose `checkpoint` or `intermediate` that were published by steps that
  durably `completed` remain `ready` and owned by the Job. They are safe to
  retain because each is the validated output of a fully committed step and
  is never presented as the Job's final output (invariants 4.5-2/3).
- **Visibility:** the Job API exposes `outputs` only for final-output
  purposes. On `cancelled`/`failed`, `outputs` is empty (or lists only
  outputs that were published before failure — never for `cancelled`);
  checkpoint artifacts are reachable only through the Job detail/steps view
  or by an explicit successor request.
- **Successor reuse:** a successor Job (§6.4) replays the predecessor's
  step plan: a step whose checkpoint artifact is still `ready` and valid
  (sha256 matches the recorded checkpoint) is re-linked — `artifact_owner`
  gains the successor as an additional owner — or marked `skipped`; only
  unfinished steps run. This is the only path that attaches a new Job to
  artifacts published by a predecessor.
- **Reconciliation on failure:** a `failed` Job's partial final-output
  artifacts stay `staging` and are cleaned per §9.4; intermediate artifacts
  of a step that *failed* (not completed) are treated as partial and
  cleaned. Only `completed`-step checkpoint artifacts survive.
- **No double-ownership:** an artifact row may list several owners (the
  predecessor and each successor that re-linked it); Trash eligibility is
  computed from the live-owner set (S01 §4: an artifact may enter Trash only
  when no live owner link remains).

---

## 10. Error envelope and observability

### 10.1 Error envelope (persisted + API)

```json
{
  "error_code": "GPU_OOM",
  "class": "transient",
  "message": "CUDA out of memory at chunk 3/12",
  "step_code": "render_chunk",
  "attempt": 2,
  "worker_id": "host-abc-7f3",
  "recoverable": true,
  "retryable": true,
  "retry_after_s": 4,
  "details": { "chunk_index": 3, "chunks_total": 12 },
  "stack": "optional, redacted"
}
```

- `error_code` is stable and machine-readable; `message` is human-readable;
  `details` is a versioned free-form map. `stack` is redacted (no secrets,
  no absolute local paths) before persistence.
- Every `failed` Job carries exactly one final error envelope; every failed
  step carries its own attempt envelope (append-only attempt history).

### 10.2 Observability

- Append-only attempt history (§8.2) and an append-only `job_event` log:
  state transitions with `(job_id, from, to, actor, worker_id, fence_token,
  revision, timestamp, reason_code)`.
- Structured logs: worker startup/claim/heartbeat/fence; reconciler scans;
  publication transactions; every log line includes `job_id`, `step_code`,
  `worker_id`, `attempt`.
- Metrics (not persisted): queue depth by resource class, lease expiry rate,
  fence rate, retry rate by error class, ETA error. These are derived from
  `job_event`; no separate metric store in Phase 1.

---

## 11. API/domain compatibility with the legacy in-memory service

### 11.1 Legacy service contract (current, from `app/workflow/job_service.py`)

| Aspect | Legacy behavior |
|---|---|
| States | `queued`, `running`, `cancelling`, `cancelled`, `completed`, `failed` (JobState enum). |
| Create | `create_job(job_type, func)` — thread + RAM dict. |
| Progress | `progress 0..100` via callback; `message` string. |
| Cancel | `cancel_job(id)` → True if set flag; else False (404 if missing, 400 if not cancelable). |
| Result | `result_path` set when worker returns a str; `error` set on exception. |
| API | `GET /api/jobs/{id}` → `job_response(info)`; `POST /api/jobs/{id}/cancel` → `{"status":"cancel_requested"}` / 400 / 404. |

### 11.2 Durable replacement contract (S02-T05 cutover target)

- **Response shape preserved:** `GET /api/jobs/{id}` keeps `job_id`, `state`
  (now the durable Job state), `progress`, `message`, `result_path`,
  `error`, `job_type`. New fields are **additive only** (e.g.
  `steps`, `attempts`, `lease`); existing fields never change meaning.
- **State enum compatibility:** durable states = legacy set + `pending` +
  `fenced` (internal). `JobState` enum in `app/schemas/__init__.py` is
  extended, never reordered (enum values are strings; consumers compare
  `.value`).
- **Cancel route:** `POST /api/jobs/{id}/cancel` keeps semantics: 200
  `{"status":"cancel_requested"}` when the flag was durably set, 400 when the
  Job is terminal, 404 when unknown. No new route is required; the route's
  service dependency is swapped to the durable repository.
- **Creation API:** current callers use `create_job(job_type, func)` with an
  in-process callable. The durable cutover introduces `create_job(job_type,
  input_manifest, ...)` returning a Job that a worker picks up by polling the
  durable queue; the legacy callable form is **not** carried forward for new
  callers. A compatibility shim (in-memory job types registered to worker
  implementations) exists only during the S02-T03/T05 migration window and is
  removed after cutover.
- **Retry semantics:** a retry request on a terminal Job creates a
  **successor Job** (new `id`, same `idempotency_key` and generation,
  `predecessor_job_id` set — §6.4, §8.5). The API response carries the new
  Job's `job_id`; the predecessor row is never modified. Creating a
  successor for a key that already has an active Job returns
  `409 IDEMPOTENCY_KEY_IN_USE`; creating one for a `completed` predecessor
  returns the existing Job (`200` with the completed Job's id) — a
  completed logical run is never re-run unless the caller bumps
  `input_generation` (fresh key).
- **Result semantics:** `result_path` is replaced by the published artifact
  set (`outputs: [{artifact_id, relative_path, kind, sha256, size_bytes,
  purpose}]`) once the Job is `completed`. `outputs` contains only
  final-output purposes (`render`, `final`, `result`); on
  `cancelled`/`failed` it is empty, while checkpoint/intermediate artifacts
  remain queryable via the Job detail/steps view (§9.5). The legacy field
  remains populated by the shim for the migration window.
- **Error field:** `error` becomes the envelope (JSON); string consumers
  during migration read `error.message`.

### 11.3 Domain compatibility

- The durable Job references S01 entities (`workspace_id`, `owner_type/owner_id`,
  artifact ids) — no new top-level aggregates are invented; Job/JobStep live
  under the existing `Workspace` aggregate boundary (PERSISTENCE_DOMAIN_CONTRACT §3).
- Existing in-memory jobs created before cutover are **not** migrated
  (RAM-only by definition; they die with the process). The cutover is
  explicit: a startup check logs any leftover legacy state and the durable
  queue starts empty; no dual-write between JSON job state and the DB is
  introduced (S01 §8 forbids dual writes).
- API responses keep their contract during S02 until S02-T05 is approved
  (S01 §8: existing APIs keep their response contract unless a separate
  approved task changes it).

---

## 12. S02-T02..T05 ownership split and gates

| Task | Owns (implementation) | Must satisfy from this contract |
|---|---|---|
| S02-T02 | Job/JobStep ORM models + migration; idempotency key uniqueness; attempt columns; `job_event`/attempt-history tables; lease table | §3 identity/static attrs; §4.1/4.2 states and terminal invariants; §8.1 key uniqueness; §8.2 attempt accounting; §10.2 event log |
| S02-T03 | Worker loop (claim → execute → heartbeat → publish); retry/backoff engine; cooperative cancel flag propagation; staging/publication helpers bound to the durable repository | §4.3/4.4 transitions; §5 lease acquisition/heartbeat; §6.1 retry classification/backoff; §6.2 cancel; §8.3/8.4 duplicate-effect prevention; §9.1/9.2 staging/publication |
| S02-T04 | Restart reconciliation: lease scan, fencing, `fenced → queued/failed`, checkpoint resume, startup reconcile | §5.3 fencing rules; §5.4 replay-safe window; §7.2 checkpoint resume; §8.4 replay closure; §4.5 invariant 6 (fenced never visible) |
| S02-T05 | Job API cutover (swap service dependency), integration tests covering the recovery contract, compatibility shim removal | §11 API/domain compatibility; §9.3 completion gate; full recovery contract tests |

- **Mandatory 7/7 gates:** every S02 task runs the full quality baseline
  (`scripts/quality-baseline.ps1` — Environment/preflight, Python tests
  (`-m "not gpu and not sam2 and not integration"`), ruff, mypy, frontend
  tsc, frontend lint, frontend build) and must finish with `OVERALL: PASS`,
  exit code 0 — the same gate set verified in S00 (`20260803-144737`) and
  S01 (`20260803-184034`). A non-PASS baseline is a failed task regardless of
  feature tests.
- **Sequencing:** T02 must not ship before T01 is APPROVED (this contract is
  its dependency); T03/T04 depend on T02; T05 depends on T03+T04. A task may
  not silently reinterpret a section of this contract; reinterpretation is a
  T01 `CHANGES_REQUESTED` or a new contract task.
- **Legacy protection:** until S02-T05 cutover is explicitly committed, the
  in-memory `JobService` remains the runtime authority; workers/APIs must not
  dual-write.
- **Sprint exit (ROADMAP):** "jobs and artifacts reconcile after forced
  close; no durable truth relies only on RAM/frontend storage" — verified by
  S02-T05 integration tests covering: kill worker mid-job → restart →
  resume/fail-safe; cancel during retry backoff; duplicate-effect absence
  under double-submit; fenced stale worker unable to publish.

---

## 13. Open decisions deferred to implementation (allowed)

1. Exact SQLite DDL for the lease table and attempt-history table (S02-T02
   owns schema; this contract fixes semantics, not DDL).
2. Chunk-size and checkpoint cadence per job type (S02-T03 owns per-type
   tuning; defaults: checkpoint per chunk/scene, heartbeat 15s, TTL 60s).
3. Whether `cancelling → running` (cancel rejection) is exercised per type —
   default is cancel always wins; job types may opt into the escape hatch.
4. Retry backoff jitter distribution (bounded ≤20% of the base delay).
5. Worker process topology (threads vs processes) — contract requires
   durable state + fencing; topology is an implementation detail.

---

## 14. Transition-endpoint invariant audit (compact)

Every transition endpoint in §4.3/§4.4, cross-checked against the terminal
invariants (§4.5), the successor model (§6.4/§8.5), the visibility classes
(§9.2) and the API semantics (§11.2). An endpoint is **closed** iff it
preserves "terminal rows immutable", "no final output without validation",
"one active/completed Job per key" and "checkpoint artifacts survive
cancel/fail":

| Endpoint | §4.5 invariants | §9.2/§9.5 visibility | Idempotency §8.1/§8.5 | Closed |
|---|---|---|---|---|
| `pending → queued` | n/a (active) | n/a | no key change | ✅ |
| `queued → running` | n/a | n/a | attempt++ | ✅ |
| `queued → cancelling` | n/a | n/a | cancel flag durable | ✅ |
| `queued → cancelled` | terminal, immutable | no final output (none started) | key stays; successor possible | ✅ |
| `running → completed` | all steps done; **final outputs** ready+validated | outputs exposed | key consumed (completed) | ✅ |
| `running → failed` | envelope; no final output ready | partial stays staging | key free for successor | ✅ |
| `running → fenced` | transient-recovery | n/a | n/a | ✅ |
| `running → cancelled` | terminal; no final output | checkpoint artifacts retained (§9.5) | key free for successor | ✅ |
| `cancelling → cancelled` | terminal; no final output | checkpoint artifacts retained | key free | ✅ |
| `cancelling → running` | escape hatch only | n/a | n/a | ✅ |
| `cancelling → failed` | envelope; no final output ready | partial cleaned | key free | ✅ |
| `cancelling → fenced` | transient | n/a | n/a | ✅ |
| `fenced → queued` | n/a (recovery) | n/a | attempt++ | ✅ |
| `fenced → failed` | envelope; no final output | partial cleaned | key free | ✅ |
| `terminal → queued` | **removed in v1.1** — terminal rows never transition | — | — | ✅ (absent) |
| `pending → ready` | n/a | n/a | n/a | ✅ |
| `ready → running` | n/a | n/a | attempt++ | ✅ |
| `running → completed` (step) | step terminal | checkpoint/intermediate published | replay-safe | ✅ |
| `running → failed` (step) | step terminal | partial cleaned | attempt recorded | ✅ |
| `ready/running → cancelling` (step) | n/a | n/a | drain | ✅ |
| `cancelling → cancelled` (step) | step terminal | no new effects | Job cancelled iff all remaining steps cancelled | ✅ |
| `cancelling → failed` (step) | step terminal | partial cleaned | Job failed | ✅ |
| `running/cancelling → ready` (step, fenced) | step rollback | staging cleaned | attempt++ at re-claim | ✅ |
| `failed → ready` (step retry) | step not terminal-final | partial cleaned | attempt++ | ✅ |

**Audit conclusions (v1.1 fixes):**

1. No transition leaves a terminal Job state; retry/restart is exclusively
   the successor-Job path (§6.4, §8.5) — the two `terminal → queued` rows
   were deleted.
2. JobStep states and transitions now use the identical set
   (`pending, ready, running, cancelling, cancelled, completed, failed,
   skipped`); `cancelling → cancelled` and `failed → ready` endpoints match
   the state list exactly.
3. "No final output" is scoped to final-output purposes (§9.2 table);
   checkpoint/intermediate artifacts may remain `ready` (§9.5) without
   violating the cancel/fail invariants, because `outputs` never includes
   them.
4. Idempotency: one active or completed Job per `(workspace, key,
   generation)`; terminal failed/cancelled predecessors chain to exactly one
   successor each. API retry creates the successor and never mutates the
   predecessor (§11.2).

---

## 15. Acceptance invariants (must be provable by S02-T05 tests)

1. Two workers can never hold the same Job lease (atomic claim).
2. A fenced worker's state writes and artifact publications are rejected.
3. Double-submit of the same idempotency key creates one Job and one effect
   set.
4. A crash between effect commit and state update is detected and resolved
   without duplicate effects (replay or same-transaction).
5. No Job is ever `completed` with a `staging` output, a missing output, or
   an unvalidated render.
6. Cancel during any active state reaches `cancelled` (or `failed` with a
   cancel-related envelope) within the lease bounds, and never publishes a
   partial output as `ready`.
7. A terminal Job is never mutated: retry/restart yields a successor Job
   with `predecessor_job_id` set, the same idempotency key/generation, and a
   fresh `id`; the predecessor's row and final output (if any) are
   unchanged.
8. A cancelled or failed Job exposes no final output in `outputs`, while
   checkpoint/intermediate artifacts from durably completed steps remain
   `ready` and reusable by the successor (re-link or skip).
9. JobStep state set and JobStep transition endpoints are exactly
   consistent (no transition targets a state outside the set).
10. Every state transition is recorded in `job_event` with actor, worker_id
    and revision.
11. The full seven-gate quality baseline remains PASS for every S02 task.
