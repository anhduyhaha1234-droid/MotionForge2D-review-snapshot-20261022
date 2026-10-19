# S02-T04 - Implementation Report

**Status:** SUBMITTED
**Hermes session:** 20260803_212922_f59eef
**Started:** 2026-08-03 21:29 +07:00
**Submitted:** 2026-08-03 22:40 +07:00

## Outcome delivered

A deterministic, bounded restart reconciler (`app/workflow/job_reconciler.py`)
around the approved S02-T02 `JobRepository` and the S02-T03 worker:
explicit run-once/startup reconcile with **no import-time behavior**, a
bounded batch scan of expired active leases (oldest first, `batch_size`
cap), **atomic fencing before any decision** (lease token invalidated and
`running|cancelling -> fenced` in one transaction), and fresh-session
resolution of every fenced Job to `queued` / `failed` / `cancelled`
(attempt-budget exhaustion → `RETRIES_EXHAUSTED`; immutable-manifest
fingerprint violation → `INPUT_CHANGED`; cancelling/durable-cancel →
terminal `cancelled`).  Resume is versioned-checkpoint-safe: incompatible
or missing checkpoints fail closed on the worker, requeued steps roll back
to `ready`, and duplicate effects are impossible by construction (fenced
token rejection + atomic lease CAS + deterministic attempt rows numbered
from the durable per-step counter).  No API routes, no schema/migration, no
dependency changes, no edits to the legacy `JobService`; `channels.json`
preserved byte-for-byte.

## Acceptance criteria evidence

| AC | Status | Evidence |
|---|---|---|
| AC1 Explicit run-once/startup reconciler scans only expired active leases using bounded batches; no import-time execution | PASS | `test_import_starts_no_thread_or_work` (thread-count invariant), `test_reconcile_once_empty_queue_reports_zero`, `test_reconcile_once_scans_only_expired_active_leases` (live lease untouched; only expired scanned), `test_reconcile_once_bounded_batch` (5 jobs × batch_size=2 → 2/2/1 passes), `test_grace_window_prevents_premature_fencing` (90s grace), `test_start_stop_lifecycle` |
| AC2 Reconciliation atomically invalidates old fence token and records `running\|cancelling -> fenced -> queued\|failed` events | PASS | `test_fence_invalidates_token_and_records_events` — fence event `actor=reconciler`, `reason_code=LEASE_EXPIRED`, details carry worker id + `old_fence_token_present=True`; lease token replaced by `fenced:*` sentinel; requeue event `reason_code=FENCED_REQUEUE`; single transaction (fence + invalidate commit together) |
| AC3 Retryable Jobs with attempts remaining and valid versioned checkpoint requeue/resume; incompatible/missing-required checkpoint fails closed | PASS | `test_requeue_resumes_from_committed_checkpoint` (fresh worker receives `{"schema_version":1,"chunk_index":7}`; completes; exactly one attempt row), `test_requeue_bumps_attempts_atomically` (Job + step counters bumped in same tx), `test_requeued_step_rolls_back_running_to_ready` (`FENCED_ROLLBACK` event), `test_incompatible_checkpoint_fails_closed_on_resume` (schema_version 99 → SCHEMA_MISMATCH/RETRIES_EXHAUSTED permanent), `test_missing_required_checkpoint_fails_closed` (no checkpoint → fail closed) |
| AC4 Cancelling Jobs reconcile to cancelled without running new effects; exhausted/permanent/input-changed Jobs fail with stable envelope | PASS | `test_cancelling_job_reconciles_to_cancelled_without_effects` (terminal cancelled, `CANCEL_DRAINED`, zero artifacts), `test_exhausted_attempts_fail_with_stable_envelope` (`RETRIES_EXHAUSTED` permanent/retryable=false), `test_permanent_failure_reconciled_to_failed` (attempt budget spent → `RETRIES_EXHAUSTED`), `test_input_changed_fails_closed` (manifest mutated after creation → `INPUT_CHANGED` permanent) |
| AC5 Old worker token is rejected after reconciliation and cannot mutate or publish; new worker continues from committed checkpoint without duplicates | PASS | `test_stale_worker_token_rejected_after_reconciliation` (sentinel token; old token raises `FENCED_WORKER` on progress + transition after fresh re-claim), `test_stale_worker_cannot_release_new_lease` (release with old token → `FENCED_WORKER`), `test_new_worker_continues_from_committed_checkpoint_no_duplicates` (exactly one attempt row, zero artifacts) |
| AC6 Forced-close/reopen integration tests prove state/events/attempts and artifact visibility across fresh engine/session instances | PASS | `test_forced_close_reopen_reconciles_and_resumes` (engine1 killed mid-checkpoint → fresh engine2 reconciler fences+requeues → fresh worker resumes from committed checkpoint; stale token rejected in new process; event chain created→running→fenced→queued→running→completed; exactly one attempt row; zero artifacts), `test_forced_close_reopen_fenced_cancelling_job_cancels` (cancelling mid-drain → terminal cancelled on reopen), `test_reconcile_after_reopen_leaves_terminal_rows_untouched` |
| AC7 No API cutover/schema/deps; targeted tests and 7/7 PASS | PASS | `test_no_cutover_imports` (pristine-subprocess probe: reconciler imports neither `app.api` nor legacy `job_service`); targeted 24/24; combined 103/103; baseline 7/7 (see Tests) |

## Files changed

- `app/workflow/job_reconciler.py` (new; JobReconciler + ReconcileConfig +
  ReconcileReport + manifest_fingerprint)
- `app/persistence/jobs.py` (repository additions: `invalidate_lease` with
  sentinel token, `bump_job_attempt`, `bump_step_attempt`,
  `latest_attempt_number`, `fenced -> cancelled` transition endpoint,
  `manifest_fingerprint` recorded on `created` events of
  `create_job`/`create_successor`)
- `app/persistence/__init__.py` (no new exports — the additions are
  JobRepository methods, accessed via instances; init unchanged apart from
  the pre-existing format)
- `app/workflow/durable_worker.py` (per-claim attempt rows numbered from the
  durable per-step attempt counter so requeued claims never duplicate
  attempt rows)
- `app/workflow/__init__.py` (exports JobReconciler + helpers)
- `tests/test_job_reconciliation.py` (new; 24 tests covering AC1-AC7)
- `tests/test_durable_worker.py` (2-char assertion-margin widening for a
  pre-existing wall-clock flake, see LOG)
- `docs/architecture/JOB_RECONCILIATION.md` (new; implementation doc)
- `docs/pm/sessions/S02-T04-restart-reconciliation/LOG.md`, `REPORT.md`

Untouched: API routes, frontend, legacy `app/workflow/job_service.py`,
migrations/schema, dependency files, user data and `channels.json`
(byte-for-byte), ROADMAP/PRD/MP, PM-owned `TASK.md`/`START_PROMPT.md`/
`PM_REVIEW.md`.

## Architecture/schema/API impact

None.  The transition table gained one endpoint (`fenced -> cancelled`)
inside the existing closed set — required by contract §4.3 so the
reconciler can resolve a cancelling Job to terminal cancelled; no schema
change (the transition table is in-repo logic, not DDL).  The `fenced`
state remains internal; the resolver folds it into `queued`/`failed`/
`cancelled` before any API could observe it (contract §4.5-6).

## Tests and validation

| Command | Result | Notes |
|---|---|---|
| `python -m pytest -q tests/test_job_reconciliation.py --cache-clear` | PASS | 24 passed in ~10.7s |
| `python -m pytest -q tests/test_durable_job_persistence.py tests/test_durable_worker.py tests/test_job_reconciliation.py --cache-clear` | PASS | 103 passed in ~28s (47 + 32 + 24) |
| `python -m ruff check app tests` | PASS | All checks passed |
| `python -m mypy app` | PASS | Success: no issues found in 51 source files |
| `git diff --check` | PASS | exit 0 (LF→CRLF advisory only) |
| `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1` | PASS | run id `20260803-223206` — OVERALL PASS exit 0 (7/7 gates: env, python tests 381 passed/8 skipped/7 deselected, ruff, mypy, tsc, eslint, build) |
| `sha256sum channels.json` | UNCHANGED | `dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555` — identical at session start and end (byte-for-byte preserved) |

## Manual UX/media verification

Not applicable — reconciler engine task, no UI or media.

## Migration and rollback

None — no schema or migration change.

## Deviations from task

None.  Notes:
- `invalidate_lease` uses a unique non-empty sentinel token (`fenced:<uuid>`)
  instead of clearing the token because the schema CHECK
  `ck_job_lease_token_nonempty` forbids empty tokens (schema is frozen for
  this task).  The sentinel has the identical fencing effect: the old token
  can never be presented again.
- The `INPUT_CHANGED` baseline is recorded on the `created` event (manifests
  are immutable by contract §3) rather than at lease acquisition (no schema
  column exists for it).
- One pre-existing wall-clock flake in `tests/test_durable_worker.py`
  (`test_heartbeat_thread_keeps_silent_handler_leased`, 2s assertion margin
  vs 3s TTL renewal under full-suite load) was fixed by widening the margin
  to 2.5s — it fails on unmodified code too and is unrelated to this task.

## Out-of-scope findings

- `fenced` rows are now resolved by the reconciler; the worker's fenced-abort
  path and the reconciler's requeue path are complementary and tested
  together (AC5).
- Legacy `JobService` still holds a `JobStatus` enum + RAM-only jobs; S02-T05
  cutover decides retirement (same note as S02-T01/T02/T03).

## Known limitations/risks

- The reconciler's `INPUT_CHANGED` check relies on the manifest being
  immutable (contract §3); an illegal mutation is caught and fails closed.
- Reconcile batch size (50) bounds a single pass; jobs beyond the batch are
  picked up on the next pass (bounded, never skipped).
- The `fenced -> cancelled` resolution requires the fence event to record
  `reason_code=CANCEL_REQUESTED`; Jobs fenced before this reconciler existed
  (no such event) resolve via the standard attempt-budget path.

## Recommended PM decision

`PENDING` — awaiting PM review per protocol (no self-approval; no commit; no
roadmap edits; no next-task start).
