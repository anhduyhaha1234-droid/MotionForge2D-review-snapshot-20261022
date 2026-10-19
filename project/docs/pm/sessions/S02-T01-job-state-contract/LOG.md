# S02-T01 - Execution Log

Append-only.

## 2026-08-03 — Session start (baseline)

### Required reading (complete, in order)

1. [x] `docs/pm/SESSION_PROTOCOL.md`
2. [x] `docs/architecture/PERSISTENCE_DOMAIN_CONTRACT.md`
3. [x] `docs/MASTER_PLAN_V1.md` (job framework + worker sections: §5.6 Global Job Center, §6.5 Processing hierarchy, §7.2 Durable processing, WS-02 exit gates, Scenario G)
4. [x] `docs/PRODUCT_REQUIREMENTS_V2.md` (durable job requirements: §2.1, FR-01, FR-09, NFR Reliability, §14 Error/recovery, domain table)
5. [x] `app/schemas/__init__.py` (JobStatus/JobState enums, JobInfo)
6. [x] `app/workflow/job_service.py` (in-memory JobService)
7. [x] `app/persistence/models.py` (S01 ORM — no Job/JobStep tables yet)
8. [x] `app/persistence/artifacts.py` (ManagedRoot atomic write/trash/restore)
9. [x] `app/api/routes/jobs.py` (GET /api/jobs/{id}, POST /api/jobs/{id}/cancel)
10. [x] `tests/test_api.py` job tests (TestJobStatus, TestJobCancel)
11. [x] `tests/test_clip_cancel_persist.py` (TestJobCancellation, TestRestartPersistence)

### Pre-existing user changes (protected — verified before any write)

`git status --short` (baseline):

```
 M channels.json
 M docs/pm/ROADMAP.md
?? docs/pm/sessions/S02-T01-job-state-contract/
```

- `channels.json` — user modified (224 added lines of test channels). SHA-256: `dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555`. Must remain byte-for-byte identical; will re-hash at gate.
- `docs/pm/ROADMAP.md` — user flipped S02-T01 status PLANNED → READY (1 line). SHA-256: `88e38a4eb14db124cc2afbc4f792f7ec265faa3c2d2a05e1e7268ce8d3dd9e43`. Read-only for this session.
- `docs/pm/sessions/S02-T01-job-state-contract/` — untracked session scaffold (LOG/REPORT/PM_REVIEW/START_PROMPT/TASK) provided by PM.

### Baseline commands + results

```
$ sha256sum channels.json docs/pm/ROADMAP.md
dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555 *channels.json
88e38a4eb14db124cc2afbc4f792f7ec265faa3c2d2a05e1e7268ce8d3dd9e43 *docs/pm/ROADMAP.md

$ git diff --stat
 channels.json      | 224 +++++++++++++++++++++++++++++++++++++++++++++++++++++
 docs/pm/ROADMAP.md |   2 +-
 2 files changed, 225 insertions(+), 1 deletion(-)

$ git log --oneline -3
9865d02 feat: complete S01 transactional legacy import
6fbed17 feat: add read-only legacy import preview
3decbd1 feat: add safe managed artifact storage
```

### Plan (session steps)

1. Draft `docs/architecture/DURABLE_JOB_CONTRACT.md` per TASK.md allowed scope.
2. Resolve all ambiguities explicitly: full state transition table, lease fencing, retry/cancel races, idempotency, artifact staging/publication, API compatibility with the legacy in-memory service.
3. Run mandatory validation (rg contract scan, `git diff --check`, quality-baseline.ps1).
4. Prove `channels.json` and `docs/pm/ROADMAP.md` untouched byte-for-byte; confirm no stray files.
5. Fill `REPORT.md` (status SUBMITTED) and append evidence to this log; stop for PM review.

### Constraints (from TASK.md / START_PROMPT)

- Allowed write scope: `docs/architecture/DURABLE_JOB_CONTRACT.md` + this session dir only.
- Forbidden: runtime source, migrations, dependencies, DB files, user data, PRD/MP/roadmap, ORM/worker/API implementation.
- No ORM models, migrations, repositories, workers, APIs, runtime cutover.

## 2026-08-03 — Validation and submission

### Contract delivered

- `docs/architecture/DURABLE_JOB_CONTRACT.md` (new, 36,478 bytes, 14 sections).
  All required ambiguities resolved explicitly: full Job (15-row) and JobStep
  (11-row) transition tables; terminal-state invariants; lease model with
  fence tokens + reconciler resolution; retry classification with backoff;
  cancel semantics + retry/cancel race matrix; idempotency key uniqueness and
  replay-safe window closure; artifact staging → validate → atomic rename →
  ready-row publication in one transaction; error envelope; observability;
  legacy in-memory service compatibility table; S02-T02..T05 ownership +
  mandatory 7/7 gates.

### Validation results (real command output)

```
$ rg -n "^## |JobStep|transition|lease|heartbeat|fenc|retry|cancel|idempoten|checkpoint|artifact|7/7" docs/architecture/DURABLE_JOB_CONTRACT.md
197 matches; all section headers present.

$ git diff --check -- docs/architecture/DURABLE_JOB_CONTRACT.md docs/pm/sessions/S02-T01-job-state-contract
exit 0

$ powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
run id      : 20260803-185238
Gate 1 - Environment/Preflight         PASS  exit=0
Gate 2 - Python tests                  PASS  exit=0   22.98s  (277 passed, 8 skipped, 7 deselected, 12 warnings in 21.48s)
Gate 3 - Python lint                   PASS  exit=0   0.08s   (All checks passed!)
Gate 4 - Python typing                 PASS  exit=0   0.71s   (Success: no issues found in 48 source files)
Gate 5 - Frontend typecheck            PASS  exit=0   2.44s
Gate 6 - Frontend lint                 PASS  exit=0   4.86s
Gate 7 - Frontend build                PASS  exit=0   5.57s
OVERALL: PASS (exit code 0)

$ sha256sum channels.json docs/pm/ROADMAP.md
dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555 *channels.json
88e38a4eb14db124cc2afbc4f792f7ec265faa3c2d2a05e1e7268ce8d3dd9e43 *docs/pm/ROADMAP.md
(identical to session-start baseline — user files preserved byte-for-byte)

$ git status --short
 M channels.json
 M docs/pm/ROADMAP.md
?? docs/architecture/DURABLE_JOB_CONTRACT.md
?? docs/pm/sessions/S02-T01-job-state-contract/
(only the two allowed write targets added; no stray files)
```

### Scope compliance

- Wrote only: `docs/architecture/DURABLE_JOB_CONTRACT.md` +
  `docs/pm/sessions/S02-T01-job-state-contract/LOG.md` + `REPORT.md`.
- Did NOT touch: runtime source, migrations, dependencies, DB files, user
  data, PRD/MP/roadmap, PM-owned session files (TASK/START_PROMPT/PM_REVIEW).
- No ORM models, migrations, repositories, workers, APIs or runtime cutover.

### Status

REPORT.md filled → status SUBMITTED. Stopping for PM review. No commit, no
self-approval, no next-task start.

## 2026-08-03 — CORRECTION (PM review round 1)

PM decision CHANGES_REQUESTED (18:57 +07:00), three blocking findings.
Fixed all three in `docs/architecture/DURABLE_JOB_CONTRACT.md` → **V1.1**.

### Fix 1 — terminal Jobs immutable; successor-Job retry model
- Deleted the two `failed → queued` and `cancelled → queued` transition rows
  from §4.3; `terminal → (any)` row now explicitly states retry/restart is a
  NEW Job linked via `predecessor_job_id`.
- Added `predecessor_job_id` to §3 Job attributes.
- Added §6.4 "Retry/restart of a terminal Job (successor model)" (5 rules:
  fresh id, same key/generation, chain `A → B → C`, cycle rejection,
  predecessor untouched).
- Rewrote §8.1 uniqueness: `(workspace_id, idempotency_key)` unique among
  terminal Jobs too; one active or completed Job per (workspace, key,
  generation); terminal failed/cancelled predecessors chain to exactly one
  successor each; fresh logical runs bump `input_generation`.
- Added §8.5 "Successor-chain uniqueness and accounting" (guarded INSERT,
  acyclicity, per-Job max_attempts bound, audit trail by job_id).
- §4.5 invariant 4 updated: retry is always a new successor Job, never a
  mutation of the terminal row.

### Fix 2 — JobStep states and transitions exactly consistent
- Added `cancelled` to the §4.2 JobStep state set (terminal; drain completed;
  Job `cancelled` requires every non-completed/skipped step `cancelled`).
- §4.4 table now uses only states from the set; the derivation paragraph
  clarifies Job terminal decisions are computed from the step set (incl.
  `running` step → `ready` when the Job is fenced).

### Fix 3 — final outputs vs intermediate checkpoint artifacts
- §4.5 invariants 2/3 scoped to "final output": failed/cancelled Jobs expose
  NO final output; checkpoint/intermediate artifacts of durably completed
  steps may remain `ready` and are retained for successors.
- §9.2 added the purpose → visibility-class table (`checkpoint`,
  `intermediate`, `preview` never exposed as Job result; `render`/`final`/
  `result` = final output).
- Added §9.5 "Intermediate checkpoint artifacts on cancel/fail" (retention,
  visibility via Job detail/steps view only, successor re-link/skip replay,
  failure reconciliation, no double-ownership / Trash from live-owner set).
- §9.3 completion gate now requires final-output artifact rows ready+linked.
- §11.2 result semantics: `outputs` contains only final-output purposes;
  empty on cancelled/failed; legacy `result_path` shim unchanged.

### Audit + acceptance invariants
- Added §14 "Transition-endpoint invariant audit (compact)": all 25 endpoints
  cross-checked against terminal invariants, visibility classes and
  idempotency; audit conclusions state the v1.1 fixes.
- §15 acceptance invariants extended to 11 (added: terminal-immutability/
  successor test; cancelled/failed expose no final output while checkpoints
  remain reusable; JobStep state-set/transition consistency).
- §11.2 retry semantics rewritten for the successor model
  (`409 IDEMPOTENCY_KEY_IN_USE` for active key; `200` + existing id for
  completed predecessor; fresh `input_generation` for new logical runs).

### Validation (real output, round 1 resubmission)

```
$ rg -n "^## |JobStep|transition|lease|heartbeat|fenc|retry|cancel|idempoten|checkpoint|artifact|7/7" docs/architecture/DURABLE_JOB_CONTRACT.md
285 keyword matches; 15 sections (1..15) present.

$ git diff --check -- docs/architecture/DURABLE_JOB_CONTRACT.md docs/pm/sessions/S02-T01-job-state-contract
exit 0

$ powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
run id      : 20260803-190352
Gate 1 - Environment/Preflight         PASS  exit=0
Gate 2 - Python tests                  PASS  exit=0   23.19s  (277 passed, 8 skipped, 7 deselected, 12 warnings in 21.59s)
Gate 3 - Python lint                   PASS  exit=0   0.08s   (All checks passed!)
Gate 4 - Python typing                 PASS  exit=0   0.68s   (Success: no issues found in 48 source files)
Gate 5 - Frontend typecheck            PASS  exit=0   2.61s
Gate 6 - Frontend lint                 PASS  exit=0   5.33s
Gate 7 - Frontend build                PASS  exit=0   5.59s
OVERALL: PASS (exit code 0)

$ sha256sum channels.json docs/pm/ROADMAP.md
dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555 *channels.json
88e38a4eb14db124cc2afbc4f792f7ec265faa3c2d2a05e1e7268ce8d3dd9e43 *docs/pm/ROADMAP.md
(unchanged — user files preserved byte-for-byte)

$ sha256sum TASK.md START_PROMPT.md PM_REVIEW.md  (session dir)
47689e07... 25ff029a... c956d9d5... (untouched, PM-owned)

$ git status --short
 M channels.json
 M docs/pm/ROADMAP.md
?? docs/architecture/DURABLE_JOB_CONTRACT.md
?? docs/pm/sessions/S02-T01-job-state-contract/
```

Consistency audits run: no `terminal → queued` semantics remain (grep clean);
JobStep transition endpoints ⊆ JobStep state set; all cross-references
(§6.4/§8.5/§9.2/§9.5/§11.2) resolve.

### Status

REPORT.md updated (evidence + corrections), status stays SUBMITTED for
re-review. No commit, no self-approval.
