# S02-T01 - Implementation Report

**Status:** SUBMITTED
**Hermes session:** 20260803_184630_1b5696
**Started:** 2026-08-03 18:46 +07:00
**Submitted:** 2026-08-03 18:55 +07:00
**Resubmitted (PM CHANGES_REQUESTED round 1):** 2026-08-03 19:06 +07:00

## PM review corrections (CHANGES_REQUESTED round 1)

| # | Correction | Resolution |
|---|---|---|
| 1 | `failed`/`cancelled` declared terminal and immutable yet the transition table permits return to `queued`; adopt one coherent model — prefer immutable terminal Jobs with retry creating a new linked Job reusing the logical idempotency generation under a documented uniqueness rule | Adopted exactly that model (contract → V1.1). Deleted the `failed → queued` and `cancelled → queued` rows; `terminal → (any)` now forbids all transitions. Added `predecessor_job_id` (§3), §6.4 successor model (fresh id, same key/generation, chain + cycle rejection, predecessor never rewritten), §8.1 uniqueness rewritten ("one active or completed Job per (workspace, key, generation)"; terminal failed/cancelled predecessors each chain to exactly one successor; fresh logical runs bump `input_generation`), §8.5 successor-chain accounting (guarded INSERT, per-Job max_attempts bound), §4.5 invariant 4 updated |
| 2 | JobStep transitions target `cancelled` but the JobStep state list omits it | Added `cancelled` to the §4.2 JobStep state set (terminal; Job `cancelled` requires every non-completed/skipped step `cancelled`); §4.4 transition table now uses only states in the set; derivation paragraph clarifies fenced `running` step → `ready` |
| 3 | Cancel semantics preserve earlier completed-step artifacts, but the terminal cancel invariant forbids any ready artifacts | Introduced purpose-based visibility classes (§9.2 table: `checkpoint`/`intermediate` never exposed as Job result; `render`/`final`/`result` = final output). §4.5 invariants 2/3 scoped to final outputs: cancelled/failed Jobs expose NO final output while checkpoint/intermediate artifacts of durably completed steps remain `ready` (§9.5 retention, successor re-link/skip replay, no double-ownership). §9.3 completion gate requires final-output rows ready; §11.2 `outputs` contains only final-output purposes, empty on cancelled/failed |
| — | Add a compact invariant audit covering every transition endpoint | Added §14 "Transition-endpoint invariant audit (compact)" — all 25 Job/JobStep endpoints cross-checked against §4.5 invariants, §9.2/§9.5 visibility and §8.1/§8.5 idempotency, with 4 audit conclusions; §15 acceptance invariants extended to 11 (terminal immutability/successor; no final output on cancel/fail + checkpoint reuse; JobStep set/transition consistency) |

## Outcome delivered

`docs/architecture/DURABLE_JOB_CONTRACT.md` — the durable Job/JobStep
state-machine contract for Epic E01 / Sprint S02. Contract only: no ORM
models, migrations, repositories, workers, APIs or runtime cutover. The
in-memory `JobService` and JSON filesystem remain runtime authority until
S02-T02..T05 land and are explicitly committed.

The contract resolves every ambiguity the start prompt called out:

- **Full transition tables** — Job (15 rows) and JobStep (11 rows), plus
  terminal-state invariants; no transition out of terminal states; invalid
  transitions reject with `409 INVALID_STATE_TRANSITION`.
- **Lease fencing** — lease row (`worker_id, acquired_at, expires_at,
  heartbeat_at, lease_version, fence_token`), atomic claim, defaults
  (TTL 60s / heartbeat 15s / timeout 90s), fence-token enforcement point
  (not timestamps), reconciler resolution `running|cancelling → fenced →
  queued|failed`; `fenced` never visible via API.
- **Retry/cancel races** — retry classification (transient/permanent/cancel
  with stable error codes, exponential backoff `1s/4s/16s` + jitter,
  `max_attempts` per Job default 3), cancel semantics (durable flag,
  cooperative drain, cancel-during-queued vs running), and an explicit race
  matrix (cancel vs retry, cancel vs terminal write, fenced-worker
  completion, manual retry vs stale drain, double cancel).
- **Idempotency** — `(workspace_id, idempotency_key)` uniqueness with
  terminal-completed reuse, active `409`, generation bump for re-runs;
  attempt accounting; deterministic ids on retry; replay-safe window closure
  (same-transaction effect+state for DB effects, staging-only for
  subprocess effects, `run_id` dedupe for finish events).
- **Artifact publication** — staging under managed root → validate
  (sha256/size/probe) → atomic rename to final path → artifact row
  `ready` + owner link + step `completed` in ONE transaction; Job
  `completed` only after every output `ready` and validated (no `.partial`
  as complete).
- **Transaction boundaries / error envelope / observability** — state vs
  effect vs checkpoint transactions; versioned error envelope
  (`error_code, class, message, step_code, attempt, worker_id, retryable,
  retry_after_s, details`); append-only attempt history + `job_event` log.
- **Legacy compatibility** — §11 table mapping the current in-memory
  service contract (states, create/cancel semantics, response shape,
  `result_path`/`error` fields) to the durable replacement; additive-only
  response changes; state enum extended, never reordered; explicit
  no-migration of RAM jobs, no dual-write.
- **S02-T02..T05 ownership** — per-task implementation ownership table and
  the mandatory 7/7 quality gates (Environment/preflight, pytest
  `-m "not gpu and not sam2 and not integration"`, ruff, mypy, frontend
  tsc, frontend lint, frontend build; `OVERALL: PASS` exit 0), matching the
  S00/S01 gate runs; sequencing (T02 blocked until this contract APPROVED).

The user-modified root `channels.json` was preserved byte-for-byte
(SHA-256 unchanged before/after), as was the user's ROADMAP edit.

## Acceptance criteria evidence

| AC | Status | Evidence |
|---|---|---|
| AC1 Job and JobStep identity, ownership, dependency, resource class, priority, progress and timestamps are explicit | PASS | §3 tables: Job attributes (`id`, `workspace_id`, `job_type` from MASTER_PLAN_V1 §7.2 list, `owner_type/owner_id` per S01 artifact_owner pattern, `parent_job_id`, `resource_class`, `priority` 0..100 default 50, `idempotency_key`, `input_manifest_json`, UTC timestamps, `revision`); JobStep attributes (`step_code`, `position`, `step_type`, `depends_on` DAG, `attempt`, `checkpoint_json`, timestamps, `revision`); invariants incl. fail-closed schema-versioned payloads; progress/ETA rule in §7.3 |
| AC2 Allowed states/transitions and terminal-state invariants are complete, including cooperative cancellation and retry classification | PASS | §4.1/4.2 state tables (Job: `pending/queued/running/cancelling/cancelled/completed/failed` + internal `fenced`; Step: `pending/ready/running/cancelling/cancelled/completed/failed/skipped` — `cancelled` added in v1.1, set matches transition table); §4.3 full Job transition table (13 rows; no terminal→active rows in v1.1); §4.4 full JobStep transition table; §4.5 six terminal invariants (completed ⇒ final outputs ready+validated; failed/cancelled ⇒ no final output; checkpoint retention §9.5; immutable terminal rows + successor rule; revision on every change; fenced never API-visible); §6.1 retry classification with stable codes + backoff; §6.2 cooperative cancel semantics; §6.4 successor retry model; §14 endpoint audit |
| AC3 Lease ownership/expiry/heartbeat, stale-worker fencing and restart reconciliation decisions are explicit | PASS | §5.1 lease model incl. `fence_token` per acquisition and `lease_version`; §5.2 atomic claim + defaults (TTL 60s, heartbeat 15s, timeout 90s, gpu TTL cap); §5.3 five fencing rules (token = enforcement point; reconciler scan; fenced worker aborts silently; atomic acquisition; graceful release); §5.4 crash-mid-write replay-safe window; §4.3 reconciler rows `running→fenced→queued|failed` and `fenced→failed` codes `WORKER_FENCED/RETRIES_EXHAUSTED/INPUT_CHANGED` |
| AC4 Idempotency, attempt accounting, checkpoints and artifact staging/publication rules prevent duplicate effects and false-ready outputs | PASS | §8.1 key composition + uniqueness (v1.1: one active or completed Job per (workspace, key, generation); successor reuse); §8.2 attempt columns + `max_attempts` enforced at claim + append-only attempt history; §8.3 deterministic ids / upsert on retry / external-call idempotency; §8.4 replay-safe window closure (same-transaction rule, staging reuse by hash, `run_id` dedupe); §8.5 successor-chain uniqueness + guarded INSERT; §7.2 checkpoint contract (schema-versioned, atomic with effects, fail-closed); §9.1 staging never exposed; §9.2 four-step publication transaction + purpose visibility classes; §9.3 Job-level completion gate (final-output rows ready); §9.4 cleanup TTL + Trash semantics; §9.5 checkpoint retention/reuse on cancel/fail |
| AC5 Transaction boundaries, error envelope, observability and API/domain compatibility with the legacy in-memory service are explicit | PASS | §7.1 three transaction types + state+effect coupling rule; §10.1 error envelope JSON schema + redaction; §10.2 `job_event` append-only log + structured logs + derived metrics; §11.1 legacy contract table (from `app/workflow/job_service.py` + `app/api/routes/jobs.py` + tests); §11.2 durable replacement contract (response shape preserved, additive fields, enum extended not reordered, cancel route semantics 200/400/404, successor retry semantics with `409 IDEMPOTENCY_KEY_IN_USE`/`200` completed reuse, `outputs` final-output-only + empty on cancel/fail, shim during migration window); §11.3 domain compatibility (Workspace aggregate, no dual-write, no legacy-job migration) |
| AC6 S02-T02..T05 implementation ownership and mandatory 7/7 gates are clear | PASS | §12 ownership table (T02 models/migration/idempotency/events; T03 worker/retry/cancel/publication; T04 reconciliation/fencing/checkpoint resume; T05 API cutover + integration tests), each mapped to contract sections; mandatory 7/7 gates enumerated with exact commands and PASS requirement (this session: `20260803-185238`, OVERALL PASS exit 0); sequencing + sprint exit criteria (kill-worker recovery, cancel-during-backoff, double-submit, fenced publication refusal) |

## Files changed

- `docs/architecture/DURABLE_JOB_CONTRACT.md` (new; contract doc V1.1, 15 sections)
- `docs/pm/sessions/S02-T01-job-state-contract/LOG.md` (baseline + final + CORRECTION entries)
- `docs/pm/sessions/S02-T01-job-state-contract/REPORT.md` (this file)

No runtime source, migration, dependency, database, PRD/MP/roadmap or user
data touched. `docs/pm/sessions/S02-T01-job-state-contract/PM_REVIEW.md`,
`START_PROMPT.md`, `TASK.md` left untouched (PM-owned; hashes verified).

## Architecture/schema/API impact

- **Architecture:** additive contract document only. Defines semantics the
  S02 implementation tasks must satisfy; no code, no schema, no dependency.
- **Schema:** none in this task. The contract fixes semantics for the
  S02-T02 schema (Job, JobStep, lease, attempt-history, job_event tables);
  exact DDL is explicitly deferred (§13).
- **API:** none. §11 defines the compatibility target for the S02-T05
  cutover; the legacy in-memory service remains the runtime authority and
  no dual-write is introduced.

## Tests and validation

| Command | Result | Notes |
|---|---|---|
| `rg -n "^## \|JobStep\|transition\|lease\|heartbeat\|fenc\|retry\|cancel\|idempoten\|checkpoint\|artifact\|7/7" docs/architecture/DURABLE_JOB_CONTRACT.md` | PASS | 197 keyword matches; all required section headers present |
| `git diff --check -- docs/architecture/DURABLE_JOB_CONTRACT.md docs/pm/sessions/S02-T01-job-state-contract` | PASS | exit 0 |
| `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1` | PASS | round 0 run `20260803-185238` — 7/7 gates PASS, exit 0; **round 1 run `20260803-190352`** — Gate 1 Environment/Preflight PASS; Gate 2 Python tests PASS — `277 passed, 8 skipped, 7 deselected, 12 warnings in 21.59s`; Gate 3 ruff PASS (`All checks passed!`); Gate 4 mypy PASS (`Success: no issues found in 48 source files`); Gate 5 frontend typecheck PASS; Gate 6 frontend lint PASS; Gate 7 frontend build PASS; OVERALL PASS exit 0 |
| `sha256sum channels.json docs/pm/ROADMAP.md` | UNCHANGED | `dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555` / `88e38a4eb14db124cc2afbc4f792f7ec265faa3c2d2a05e1e7268ce8d3dd9e43` — identical to session-start baseline AND round-1 check (byte-for-byte preservation across both submissions) |
| `sha256sum TASK.md START_PROMPT.md PM_REVIEW.md` (session dir) | UNCHANGED | `47689e0768f2...`, `25ff029a3bab...`, `c956d9d5831c...` — PM-owned files untouched |
| Consistency audit: terminal→active semantics | CLEAN | grep for `failed → queued`, `cancelled → queued`, terminal re-entry: no matches (only the audit table's "removed in v1.1" annotation) |
| Consistency audit: JobStep transition targets ⊆ JobStep state set | CLEAN | §4.4 targets `ready/skipped/running/completed/failed/cancelling/cancelled` — all present in the 8-state §4.2 set; `pending` never targeted (correct) |
| `git status --short` delta | CLEAN | Exactly: user's 2 modified files (unchanged content) + the 2 allowed write targets; no stray files |
| `git diff --check` (final re-run) | PASS | exit 0 (LF→CRLF advisory only on Windows) |

## Manual UX/media verification

Not applicable — contract-only task, no UI or media.

## Migration and rollback

None. No schema change, no migration, no data movement. Removing the
contract file fully reverts this task.

## Deviations from task

None.

## Out-of-scope findings

- `app/schemas/__init__.py` `JobStatus` (pending/running/completed/failed)
  is a second, older job enum alongside `JobState`; it is unused by
  `job_service.py` and the jobs routes. Not changed (outside write scope);
  S02-T05 should decide whether to retire it.
- The legacy `JobService.cancel_job` mutates state (`CANCELLING`) in the
  API call thread and only then sets the event; the durable contract §6.2
  requires the flag write to be durable and state-guarded. This is a
  documented compatibility gap the cutover must close (noted in §11.2).

## Known limitations/risks

- Contract-only: correctness depends on S02-T02..T05 faithful
  implementation; the §14 acceptance invariants are the binding tests.
- `fenced`-never-visible requires the reconciler to run before API polls in
  the failure window; bounded by lease TTL (≤60s default) — acceptable per
  §5.2, but the S02-T04 reconciler cadence must be shorter than the TTL.
- Deferred DDL/tuning decisions are listed in §13 and do not block T02.

## Recommended PM decision

`PENDING` — awaiting PM review per protocol (no self-approval; no commit;
no next-task start).
