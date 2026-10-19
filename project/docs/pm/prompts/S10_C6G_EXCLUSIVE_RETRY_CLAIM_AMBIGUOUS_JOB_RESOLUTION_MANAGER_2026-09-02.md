Bắt buộc đọc TOÀN BỘ file
`C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi
preflight, dispatch, resume, review nội bộ hoặc production write. Báo
`RULES_LOADED` kèm absolute path, logical line count, SHA-256, actual
worktree/branch/HEAD/dirty state và các mục chính đã nạp. Canonical tại thời
điểm Codex phát hành prompt này là 193 dòng, SHA-256
`C6AD775A98B9FEEDCDD435932A0B6659B0EF991B0D43F492E47379CC5ED20089`.
Nếu không đọc được toàn bộ hoặc hash khác, dừng `BLOCKED_RULES / RULES_DRIFT`;
không dùng lịch sử chat hay bản tóm tắt cũ để điều hành.

# S10-C6G — Exclusive Retry ownership + ambiguity-safe durable-job resolution

Bạn là Hermes Manager correction của MotionForge2D. Hãy thực thi toàn bộ
bounded correction và sprint-exit gate; không chỉ trả kế hoạch. Codex là PM/BA/
Reviewer duy nhất được APPROVED/CLOSED. Manager không được tự sửa production
code/test/migration/UI/config; mọi implementation thuộc đúng một worker owner.

## 1. Current verdict, authority, required reading

Codex independent verdict:

`S10-C6F = CHANGES_REQUESTED / NOT_APPROVED`

Vòng duy nhất được cấp quyền là `S10-C6G`, correction packet
`S10-T01C-C14`. Không mở S11/S12/S13, không commit/push/merge và không tự ghi
APPROVED/CLOSED.

Sau rules, đọc toàn bộ:

1. `C:\Users\Admin\MotionForge2D\AGENTS.md`
2. `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
3. `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
4. `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
5. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C6F_PM_REVIEW_2026-09-02.md`
6. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C6E_PM_REVIEW_2026-09-01.md`
7. `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S10_C6F_EXACT_JOB_DISCOVERY_RETRY_CAS_RECOVERY_MANAGER_2026-09-01.md`
8. Current T01C TASK/LOG/REPORT, S10 registry, C6F closure matrix/EXIT and raw
   before/after evidence.

## 2. Workspace, owner, model, and hard guards

- Production worktree duy nhất:
  `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`.
- Expected branch `codex/s08-integration`, reviewed HEAD
  `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`; discover actual. HEAD/branch
  mismatch => stop for Codex. Preserve dirty attribution; do not reset, clean,
  stash, restore, checkout or overwrite unrelated bytes.
- MAIN `C:\Users\Admin\MotionForge2D` là read-only đối với Hermes production.
- Logical owner remains S10-T01C. Resume exact healthy recovery session
  **`20260901_230235_b80d4b`** for C14. It has only two compact C13 turns; no
  recovery threshold is met. Do not create a new worker, do not resume old
  `20260828_003035_859fe5` / `20260831_151420_07b6c2`, and never allow two
  writers.
- Before resume, prove exact owner/writer absent and tree stable. Record
  process command lines, ports and hashes. If owner cannot resume, do not
  improvise recovery; stop `BLOCKED_LIVENESS` for Codex.
- Worker route stays exact selector `comboBAI`, provider `custom`, reasoning
  `max`, Hermes external fallback chain OFF, TTFB 900. Internal combo routing is
  allowed; record only effective member evidence actually exposed. Wrong route
  => `BLOCKED_MODEL_ROUTE`, no silent fallback.
- `MOTIONFORGE_DATABASE_URL` must be UNSET. Every test/repro uses a distinct
  short fresh SQLite DB/root/basetemp/output/cache. No user data or retained
  evidence is mutated.

## 3. Task map, ownership, DAG, and fastest safe wave

| Task ID | Outcome | Depends on | Owner | Exclusive production write-set |
|---|---|---|---|---|
| S10-T01C-C14 | One ambiguity-safe durable-job resolver; truthful Retry ownership with no same-state CAS winner; exact tests/evidence addendum | C6F Codex review + stable tree | resume `20260901_230235_b80d4b` | §5 allowlist only |

Serialized writer DAG:

`PREP -> LOCK-C6G-MATRIX -> RESUME-C14-RED -> C14-FIX -> TASK_SUBMITTED ->
PARALLEL-READERS{IDENTITY || RETRY || STATIC} -> MICRO-JOIN -> MATRIX-100% ->
FOCUSED -> FINAL-BROAD -> RETAINED -> EXIT`

Only one production writer exists. For maximum speed, after worker terminal and
stable hashes, Manager may launch exactly three read-only readers concurrently:

- Reader A: identity/ambiguity after-repros and all-row DB assertions.
- Reader B: Retry ownership/CAS after-repros and true race assertions.
- Reader C: source-structure audit + Ruff/mypy/diff-check.

Each reader has isolated DB/temp/output and no source write. Join all three
before focused/full gates. Shared/full gates remain serialized under the global
mutex. No broad suite before micro + matrix closure.

Heartbeat every 20 minutes; after 8 minutes without new progress audit PID,
process tree, command line, CPU, log mtime/size, file hashes and input wait.
Connection errors follow canonical 5-minute same-session/same-model retry. A
worker iteration limit or internal three-retry exhaustion is not terminal.

## 4. Manager-owned immutable PREP — do once, before worker resume

Create new `output/s10/c6g/manager/prep/**`; never rewrite C6F evidence.

1. Record rules/instruction hashes, timestamp/timezone, cwd, branch, HEAD,
   porcelain attribution, DB env, listeners/processes, owner quiescence and
   protected hashes.
2. Hash allowlist plus frozen jobs/models/services/workflow/frontend/build and
   retained C6F evidence.
3. Manager independently reproduce current defects on current bytes, real
   route/JobService/fresh SQLite, and freeze scripts/results before worker:
   - **G1 ambiguous claimants:** normal Submit; mutate original key to
     `tampered-a`; create a second queued Job with the same workspace,
     deterministic generation and manifest but key `tampered-b`; identical
     replay. Current defect expected: HTTP 200 `reused=true`, total rows 2 -> 3
     after canonical repair.
   - **G2 no-op claim:** normal Submit -> Cancel; call the real cancelled Retry
     claim in two distinct sessions without creating a successor. Current
     defect expected: `claim1=true`, `claim2=true`, final predecessor still
     cancelled.
   - **G3 test/source audit:** prove cancelled Retry race test checks final
     response/rows but does not assert exactly one claim/ownership winner.
4. Freeze a SHA-256 manifest of PREP. Worker cannot edit manager evidence.

## 5. S10-T01C-C14 worker contract

### 5.1 Allowed writes

- `app/api/routes/s10_full_apply.py`
- `tests/test_s10_full_apply_api.py`
- append-only current T01C `LOG.md` and `REPORT.md`
- new `output/s10/c6g/t01c-c14/**`

Manager owns `output/s10/c6g/manager/**` and registry/EXIT. Worker must not edit
Manager evidence.

### 5.2 Frozen/forbidden

- `app/persistence/jobs.py`, `app/persistence/models.py`, all migrations/schema
- `app/services/s10_full_apply.py`, `app/workflow/s10_full_apply_jobs.py`,
  `app/workflow/job_service.py`, all planner/renderer/recompute/structural files
- frontend, T04B/T04C harness/build, retained evidence, MAIN, S11/S12/S13,
  channels/data/user media
- test-only production bypass, sleep-as-correctness, swallowed query error,
  cleanup-after-duplicate, weakened counts, prefix-only Job query, same-state
  rowcount as ownership, skip/xfail/monkeypatch replacing the production
  transition being tested

If a migration or frozen file is truly required, stop
`BLOCKED_DEPENDENCY / SCOPE_EXPANSION_REQUIRED` with exact RED evidence; do not
expand scope yourself. Existing unique S10 run natural/idempotency constraints
must be evaluated before claiming a migration is needed.

### 5.3 G1 — one durable-job resolver, fail closed on ambiguity

Replace the split key-only lookup + `_s10_wrong_identity_claimant` one-row
special case with one resolution path that discovers candidates by the union
of independent durable identities, including at minimum:

- canonical run job key;
- deterministic S10 input generation;
- stored manifest `run_id` and relevant project/checkpoint/plan identity;
- workspace/owner identity needed to detect cross-boundary corruption.

The resolver must return a typed/classified result:

- zero relevant candidates -> possible true orphan; only this class may repair;
- exactly one exact canonical candidate -> validate/reuse;
- one wrong candidate -> fail closed 409/422, zero mutation;
- multiple/ambiguous candidates -> fail closed 409/422, zero mutation;
- query/parse/read error -> fail closed; never treat error as absence.

Do not rely on `len(rows) == 1` or return `None` for ambiguity/error. Do not
filter only canonical key prefixes or trusted job types when counting corrupted
identity rows. API success occurs only after full immutable/lifecycle validation.

### 5.4 G2 — truthful Retry ownership

- A failed predecessor may be claimed by a real `failed -> cancelled` CAS.
- An initially cancelled predecessor must not use `cancelled -> cancelled`
  rowcount as an exclusive winner.
- Choose one bounded ownership mechanism for cancelled Retry:
  - a real state/version CAS with clean compensation, or
  - the atomic insertion of the unique successor run/natural key as the
    ownership point, with IntegrityError/domain collision converted to stable
    409 and clean rollback.
- Exactly one caller may pass the ownership point. The loser returns stable 409
  before durable-job creation or after clean rollback; never raw 500.
- Sequential repeat Retry, simultaneous failed Retry, simultaneous cancelled
  Retry and replay-vs-Retry all leave exactly one coherent active lineage work.
- Do not claim exclusivity merely because final unique constraints prevented a
  second row. Tests/evidence must expose winner count at the actual ownership
  point.

### 5.5 Locked anti-omission matrix

Before worker resume, Manager creates `C6G_CLOSURE_MATRIX.md/json` with exact
source, BEFORE evidence, test, AFTER path, expected HTTP/all-row/mutation counts
and status for every row:

| ID | Binary requirement |
|---|---|
| G1-I1 | One wrong-key claimant -> 409/422; one unchanged row |
| G1-I2 | Two same-generation wrong-key claimants -> 409/422; count remains 2, no canonical third row |
| G1-I3 | Combined wrong key + wrong job/workspace/owner identity -> fail closed; all rows unchanged |
| G1-I4 | Resolver query/read/parse error -> fail closed; zero repair/mutation |
| G1-I5 | Wrong manifest run/project identity -> fail closed; zero mutation |
| G1-I6 | True zero-job orphan -> exactly one canonical repair |
| G1-I7 | Valid unchanged replay -> 200 reused; zero side effect |
| G2-R1 | Direct cancelled-claim probe cannot return two exclusive winners |
| G2-R2 | Two simultaneous Retry on failed -> one ownership winner, one successor, one 409 loser |
| G2-R3 | Two simultaneous Retry on cancelled -> no same-state CAS ownership; one insertion/winner, one successor, one 409 loser |
| G2-R4 | Sequential repeat Retry -> stable 409/converge, never 500, no new row |
| G2-R5 | Retained replay-vs-Retry -> one 200, one 409, one active work |
| G3-W1 | Worker-claim-vs-Retry retains two real participants, bounded joins, rendezvous and all-row invariant |
| G4-D1 | Evidence arithmetic addendum states exact matrix total/classes consistently |

No row may be silently merged or omitted. Initial statuses are
`LOCKED_PENDING_FIX`; final success requires **14/14 CLOSED** and matching JSON,
Markdown, REPORT, registry and EXIT arithmetic.

### 5.6 RED-first and one-packet implementation

Worker receives one compact prompt containing all matrix rows; do not split
G1/G2 into separate turns unless connection/iteration forces same-session
continuation.

1. Add tests first. At minimum G1-I2 and G2-R1 must fail on current before bytes
   for the exact expected reason; retained controls stay green. Save raw RED.
2. Implement the two invariant paths only after credible RED.
3. Run exact new/retained tests; append T01C LOG/REPORT with exact **14-row**
   arithmetic and correct the C13 “15/6” typo via append-only addendum.
4. Write `TASK_SUBMITTED`, stop the writer and return control to Manager.

If interrupted, report landed hashes, failed matrix IDs and next command;
Manager resumes this exact owner with a short failed-row packet. Do not paste
the entire C6A-C6F history and do not create another session.

## 6. Manager verification — fail fast, broad only once at final bytes

After worker terminal, review code/test source directly, then launch the three
isolated readers from §3.

### 6.1 MICRO-JOIN

- Re-run Manager G1 ambiguous-claimant repro: expected 409/422, count 2 -> 2,
  zero canonical row.
- Re-run Manager G2 direct claim probe: a cancelled predecessor cannot produce
  `true,true` from the alleged exclusive CAS. If successor insertion is the
  ownership point, assert the same-state CAS is not invoked and exactly one
  insert succeeds.
- Run failed/cancelled Retry true races with barriers at the actual ownership
  operation; assert rendezvous, winner count, responses and every run/job row.
- Run resolver-error/combined-tamper/true-orphan/valid-replay controls.
- Source audit every test named race/barrier/concurrent for participant count,
  contested operation, synchronization, join/timeout and all-row assertion.

Any micro failure => reopen exact matrix row and resume C14 owner. Do not run
focused/full gates.

### 6.2 MATRIX + focused/static

- Close a row only after source review + independent AFTER + exact exit
  assertions. Require 14/14 CLOSED, zero OPEN/PENDING/TO_ADD and identical
  arithmetic across artifacts.
- Exact C14 + retained C6F/C6E/C6D/C10 tests x2 on distinct fresh roots.
- Full T01C API/workflow focused suite x2.
- Ruff functional checks, mypy exact touched production, `git diff --check`.

Reader failures route once as one combined failed-row packet to the same owner;
do not send one correction message per test.

### 6.3 FINAL-BROAD — only after final source hash is frozen

1. Full `tests/test_s10*.py` x2 on distinct fresh short roots, serialized under
   mutex. No skip/xfail/assertion weakening.
2. Alembic exactly one head; materialized OpenAPI path/op/distinct operation ID
   with zero duplicates; J1-v4 13/13 + EOL guard.
3. Protected hashes/write-set/porcelain/DB-env proof; current build validator
   and retained UI/two vertical evidence by hash only when relevant bytes are
   unchanged.
4. Any production/test edit after a gate invalidates that gate. Re-run micro,
   matrix and focused before the one final broad checkpoint; do not run broad
   suites between worker continuation turns.

## 7. Reporting, cleanup, and terminal

Append current owner/model/turn ledger, files, exact test counts/durations,
repros, 14-row matrix, risks and evidence paths to T01C records and registry.
Correct C13's “15 rows / 6 retained” via append-only addendum; preserve history.

Stop writer/watchers/services, remove heartbeat automation, prove exact owner
terminal and task ports free. Keep generic unrelated Hermes desktop processes
untouched. HEAD must remain unchanged; no commit/push/merge.

Success terminal only:

`S10-C6G = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`

Do not write APPROVED/CLOSED and do not open S11/S12/S13. Begin immediately:
rules load -> stable PREP -> immutable two defect repros -> lock 14-row matrix
-> resume exact C13 recovery owner once -> RED -> invariant fix -> parallel
readers -> micro/matrix/focused -> final broad -> retained hashes -> EXIT. Không
chỉ trả kế hoạch.
