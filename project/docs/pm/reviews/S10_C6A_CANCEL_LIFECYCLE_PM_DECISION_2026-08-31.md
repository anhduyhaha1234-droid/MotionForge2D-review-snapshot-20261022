# S10-C6A — Cancel lifecycle blocker — Codex PM decision

Date: 2026-08-31 14:51 +07  
Reviewer: Codex Project PM/BA/Reviewer  
Integration worktree reviewed: `C:/Users/Admin/MotionForge2D-worktrees/s08-integration`  
Branch / HEAD: `codex/s08-integration` / `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`

## Verdict

`S10-C6A = CONTINUATION_AUTHORIZED / NOT_APPROVED`

Hermes and T04B stopped correctly at a real cross-owner production defect. This
is not a hung worker and is not sufficient evidence to approve or close S10.
Codex authorizes a bounded T01C lifecycle correction, followed by automatic
resumption of the existing T04B and T04C owners through the remaining S10 exit
DAG. No S11 or production S13 task is opened by this decision.

## Independent review result

The C6A authority work has made material, retained progress:

- S09 approval v2 and canonical `full_apply_authority` were manager-verified.
- S10 minimal submit is now identity/CAS-only and server-derived; T03 fixtures
  were re-aligned to that real v2 contract.
- The fresh manager backend gate reached `216 passed`.
- T04B produced an executable real fixture and a non-vacuous 20-case desktop +
  mobile live suite. Its probe proved v1 is ineligible, v2 is executable,
  minimal submit returns 202, tampering fails closed, and a real 16/16 run can
  complete.

The live suite then exposed the lifecycle defect below. T04B correctly did not
patch backend files outside its exclusive write scope.

## Findings

### F1 — P0 — cancel endpoint can report success while its durable job remains live

Owner: S10-T01C, exact session `20260828_003035_859fe5`.

`app/api/routes/s10_full_apply.py:481-517` first changes the Full Apply run to
`cancelled` in request session A. Before A is committed, it opens a second read
session B and calls `JobService.cancel_job`, which opens writer session C. On
rollback-journal SQLite this produces A=RESERVED, B=SHARED, C=writer requiring
EXCLUSIVE, hence a deterministic `database is locked` failure. Lines 509-510
swallow every exception, and the route still commits and returns
`cancelled: true`.

Independent reproduction:

`output/s10/c6a/t04b-c3/live-defect-cancel-route/repro.sqlite.py` prints:

- `A: RESERVED lock held`
- `B: SHARED read ok`
- `C: sqlite3.OperationalError ... database is locked — CONFIRMED`

The real live trace shows no durable `cancelling` event: the job proceeds
`queued -> running -> completed`, and the run later changes
`cancelled -> completed` with a completed publication. This violates the route
response, lifecycle contract and user-visible Cancel behavior.

### F2 — P0 — worker completion can overwrite cancellation and publish after a late cancel

`app/workflow/s10_full_apply_jobs.py:622-628` checks cancellation only at the
top of the chunk loop. After the final chunk there is no cancellation check
before stitch/publication (`686-710`) or before completion (`712`).
`_mark_run_status` at `733-739` performs an unconditional UPDATE, so
`completed` can overwrite a concurrent terminal `cancelled` state.

The lifecycle correction must therefore be two-sided: a correct durable API
transition plus worker-side cancellation fences/CAS. Reordering one commit
without preventing false success and late publication is not sufficient.

### F3 — P1 — resume has the same multi-session risk and swallows successor errors

`app/api/routes/s10_full_apply.py:656-767` writes the run in the request
session, then opens another job session and can call `js.create_job` before the
request transaction commits. Lines `745-759` swallow successor-creation
failure after rollback, yet the route can still return `resumed: true`.

Retry commits the request transaction before creating its durable job and does
not have the identical initial lock pattern, but its failure/compensation and
authority revalidation still belong in the same bounded lifecycle audit.

### F4 — P1 — existing tests prove only immediate/service behavior, not the route race

`tests/test_s10_full_apply_api.py:511-528` checks the immediate run status after
Cancel and then retries; it does not run a real worker through the race.
`tests/test_s10_full_apply_workflow.py:461-473` and `597-605` call
`FullApplyService.cancel_run` directly, bypassing the defective route/job
transaction choreography. The current tests can therefore remain green while
the real UI behavior fails.

## Why Hermes keeps stopping

Earlier interruptions included ordinary Hermes iteration limits; the manager
resumed the same exact worker as required. The current stop is different and
intentional: T04B owns frontend acceptance while the defect is in frozen
T01C backend code. `HERMES_AUTOPILOT_RULES.md` requires
`BLOCKED_SCOPE_EXPANSION` and a Codex decision instead of silently crossing
exclusive ownership. The strict live suite is doing its job by finding a real
transaction race that service-only tests missed.

## Authorized correction

Resume only S10-T01C exact owner `20260828_003035_859fe5` under label
`S10-T01C-C9-LIFECYCLE` using the latest user-selected exact worker model
`ocg/deepseek-v4-flash`, reasoning `max`, fallback OFF, TTFB 900. The temporary
`BAI/deepseeekv4flash` override is withdrawn because that route is unstable and
must not be used for C6B.

Allowed production scope:

- `app/api/routes/s10_full_apply.py`
- `app/workflow/s10_full_apply_jobs.py`
- bounded `app/workflow/job_service.py` only if a same-session/atomic API is
  proven necessary
- `tests/test_s10_full_apply_api.py`
- `tests/test_s10_full_apply_workflow.py`
- append-only T01C TASK/LOG/REPORT and isolated `output/s10/c6b/**` evidence

Required semantics:

1. Run cancellation and durable job cancellation must become one coherent,
   fail-closed transition. A successful response may not leave a claimable or
   running job without a durable cancellation signal.
2. Lock/transition/enqueue failures may not be swallowed. HTTP response,
   rollback and compensation semantics must be explicit and tested.
3. Cancellation is idempotent and terminal races are honest.
4. The worker rechecks cancellation before stitch, before publication and
   before completion. Completion uses a conditional transition and may never
   overwrite `cancelled` or create a completed publication after cancellation.
5. Audit and correct retry/resume transaction choreography within the bounded
   T01C lifecycle scope; no route may return success after silently failing to
   create/transition its durable job.

Required race coverage uses the real API route, real JobService and the same
SQLite database:

- cancel while queued, during claim/running, mid-chunk and after final chunk
  but before stitch;
- route success implies durable cancelling/cancelled job state; worker drain
  leaves run cancelled and zero completed publication;
- injected SQLite lock/transition failure is not swallowed and leaves coherent
  state;
- repeated cancel is idempotent;
- retry after cancellation creates a canonical successor while predecessor
  remains cancelled;
- resume does not reproduce the second-writer lock and never hides successor
  creation failure.

## Authorized continuation DAG

`PREP -> S10-T01C-C9-LIFECYCLE -> J6C -> resume S10-T04B-C3 -> J6-UI -> J6-BUILD -> resume S10-T04C-C5 -> EXIT`

- J6C independently reruns targeted lifecycle tests, retained T01C authority
  tests, the full S10 suite, Ruff, exact mypy, OpenAPI, Alembic, J1-v4 and
  `git diff --check`.
- T04B resumes the same owner/session and retains its existing fixture, probe,
  build and live-suite work. It reruns scenarios 5/6 first, then all 20 cases
  with zero skip on desktop/mobile.
- If production frontend bytes change, J6-BUILD creates and validates a fresh
  build; otherwise it records hash equality and avoids a needless rebuild.
- T04C resumes the same owner/session for two fresh, distinct current-build
  vertical runs with DB/file/media/authority/restart/recompute evidence.
- Manager continues automatically through this authorized DAG. It stops for
  Codex only on a genuinely new cross-owner production defect, model-route
  failure, J1 drift, environment blocker, or final sprint review.

## Frozen / not authorized

- No schema or migration change unless a new Codex decision explicitly opens
  it.
- No S09 authority redesign, T03/T04A change, S11 production or S13 production.
- No MAIN production writes, commit, push, merge, stash, reset or cleanup of
  unrelated dirty files.
- No test weakening, skip, mock replacement of the real race, SQLite mode
  change, broad retry loop, swallowed exception or status waiver.

## Next packet

`docs/pm/prompts/S10_C6B_CANCEL_LIFECYCLE_CONTINUATION_MANAGER_2026-08-31.md`
