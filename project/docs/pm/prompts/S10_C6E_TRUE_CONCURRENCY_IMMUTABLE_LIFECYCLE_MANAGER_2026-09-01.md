Bắt buộc đọc TOÀN BỘ file
`C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi
preflight, dispatch, review nội bộ hoặc production write. Ghi `RULES_LOADED`
với absolute path, logical line count, SHA-256, HEAD đang thấy và các mục chính
đã nạp. Canonical hiện tại là 193 dòng, SHA-256
`c6ad775a98b9feedcdd435932a0b6659b0ef991b0d43f492e47379cc5ed20089`.
Nếu không đọc được toàn bộ hoặc SHA khác, dừng `BLOCKED_RULES_DRIFT`; không dựa
vào lịch sử chat hoặc bản tóm tắt cũ.

# S10-C6E — True concurrency, exact immutable manifest, lifecycle truth

Bạn là Hermes Manager dài hạn của MotionForge2D. Hãy thực thi bounded
correction và exit gate, không chỉ trả kế hoạch. Manager không được tự sửa
production code/test/migration/UI/config; mọi correction phải resume đúng
worker session sở hữu.

## 1. Authority, verdict, required reading

Codex independent verdict:

`S10-C6D = CHANGES_REQUESTED / NOT_APPROVED`

Vòng duy nhất được cấp quyền là `S10-C6E`, sửa ba blocker của exact S10-T01C:
true concurrent replay tạo hai jobs, thiếu lifecycle validation, và manifest
comparison không đầy đủ. Không mở sprint/task sản phẩm mới, S11/S12/S13, không
tự ghi APPROVED/CLOSED.

Sau rules, đọc toàn bộ:

1. `C:\Users\Admin\MotionForge2D\AGENTS.md`
2. `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
3. `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
4. `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
5. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C6D_PM_REVIEW_2026-09-01.md`
6. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C6C_PM_REVIEW_2026-09-01.md`
7. `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S10_C6D_REPLAY_SINGLE_WORK_CORRECTION_MANAGER_2026-09-01.md`
8. Toàn bộ current TASK/LOG/REPORT của S10-T01C và
   `docs/pm/sessions/S10-SESSION_REGISTRY.md` trong integration worktree.

## 2. Workspace, owner, model, guards

- Production worktree duy nhất:
  `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`.
- Branch `codex/s08-integration`; expected preflight HEAD
  `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`. Ghi actual HEAD/status; mismatch
  thì dừng cho Codex quyết định.
- MAIN `C:\Users\Admin\MotionForge2D` read-only đối với Hermes.
- Giữ nguyên dirty attribution. Cấm commit/push/merge/reset/checkout/restore/
  clean/stash hoặc xóa/overwrite evidence cũ.
- Correction phải resume exact S10-T01C session
  `20260828_003035_859fe5`; không tạo owner/session mới.
- Trước resume, audit context health của exact owner theo rules mới: số turn và
  compaction/iteration exits, lặp việc, stale contract, token/độ trễ và usable
  bytes. Nếu healthy, resume exact owner. Nếu có bằng chứng context hỏng lặp
  lại, dừng writer cũ và báo `BLOCKED_CONTEXT_RECOVERY_PROPOSAL` cho Codex với
  proposed recovery session/handoff gọn; prompt này không tự cấp quyền tạo
  replacement owner và tuyệt đối không để hai writer cùng sống.
- Worker model exact `BAI/deepseek-v4-flash-vision-exp`, provider `custom`,
  reasoning `max`, fallback OFF, TTFB 900. Cấm comboBAI, GLM, OCG, Meta/Muse,
  alias gần giống hoặc silent fallback.
- Probe selector/effective route trước dispatch, lưu raw evidence tại
  `output/s10/c6e/manager/prep/model/**`. Invocation dự kiến:
  `hermes --resume 20260828_003035_859fe5 --provider custom -m BAI/deepseek-v4-flash-vision-exp --yolo`.
  Sai effective route => `BLOCKED_MODEL_ROUTE`.
- `MOTIONFORGE_DATABASE_URL` phải UNSET. Test DB/temp/output/cache/ports phải
  fresh, isolated, ngắn cho Windows path tests và không chạm user data.

## 3. Task map, DAG, ownership, parallelism

Task duy nhất:

| Task ID | Outcome | Depends on | Owner | Exclusive write-set |
|---|---|---|---|---|
| S10-T01C-C12 | Một canonical durable job dưới true concurrency; exact immutable manifest; explicit run/job lifecycle matrix | C6D review | resume `20260828_003035_859fe5` | allowlist §5 |

Serialized production DAG:

`PREP -> S10-T01C-C12 -> J6F -> RETAINED-EVIDENCE-CHECK -> EXIT`

Chỉ một production writer. Không có production task độc lập nào được phép chạy
song song. Sau khi writer terminal và tree quiescent, các focused test/static
readers có thể chạy song song với DB/basetemp/output riêng; full/global gates
phải qua một mutex trên checkpoint bytes nhất quán.

Iteration/context limit không phải blocker. Sau mỗi process exit, audit landed
bytes/log rồi resume cùng exact owner/model/scope đến `TASK_SUBMITTED` hoặc
blocker ngoài scope.

Heartbeat mỗi 20 phút. Im lặng 8 phút phải audit PID/process tree, command line,
CPU, log mtime/size, file mtimes và trạng thái chờ input. Connection/502/503/
504/disconnect là `RUNNING_RETRY_WAIT`: báo ngay, chờ đủ 5 phút, liveness audit,
rồi resume cùng session/model/scope; không đổi model hoặc tạo owner khác.

## 4. PREP — Manager read-only, evidence immutable

Tạo mới `output/s10/c6e/manager/prep/**`; không sửa/xóa
`output/s10/c6c/**` hoặc `output/s10/c6d/**`.

1. Lưu rules/instructions hashes, timestamp/timezone, cwd, branch, HEAD,
   porcelain attribution, diff-check, DB env, listener/process inventory và
   protected hashes.
2. Hash baseline toàn allowlist, completion-CAS, planner/rendering,
   frontend/harness/current build, retained UI/vertical bundles.
3. Xác nhận no writer và registry C6D terminal.
4. Reproduce trên production bytes trước C12 bằng real route, real JobService,
   fresh isolated SQLite; mỗi case có riêng `before/**`, không overwrite:
   - `before/true-concurrent-repair/**`: forced first enqueue failure, rồi hai
     TestClient/thread thật rendezvous bằng `threading.Barrier` ngay trước hai
     real `create_job`; lưu barrier count, both HTTP bodies, all run/job rows.
     Expected defect hiện tại: two 200 reused responses, one pending run, two
     different queued jobs cùng idempotency key.
   - `before/project-root-manifest-tamper/**`: normal Submit, mutate only stored
     `project_root`, identical replay. Expected defect: 200 reused.
   - `before/terminal-run-active-job/**`: normal Submit, mutate only run to
     cancelled while job stays queued, identical replay. Expected defect: 200
     reused cancelled + queued.
5. Nếu một baseline không tái hiện, không giả lập PASS; ghi raw state và audit
   drift trước dispatch.

Post-fix chỉ ghi `after/**`, tuyệt đối không dùng chung path/file với before.

## 5. S10-T01C-C12 — resume exact owner

### 5.1 Allowed write-set

- `app/api/routes/s10_full_apply.py`
- bounded `app/services/s10_full_apply.py` chỉ nếu cần transition/lineage truth
- bounded `app/workflow/job_service.py` hoặc `app/persistence/jobs.py` chỉ nếu
  cần expose/handle stable idempotency-domain exception; không refactor job
  subsystem
- `tests/test_s10_full_apply_api.py`
- bounded `tests/test_s10_full_apply_workflow.py` nếu cần worker-claim barrier
- append-only T01C `LOG.md`, `REPORT.md`, integration S10 registry
- new `output/s10/c6e/**`

Preferred bounded design: mọi S10 durable creation phải truyền cùng một
deterministic non-NULL `input_generation`/generation identity derived
server-side from canonical run/work identity, để existing database unique
backstop thực sự serialize concurrent inserts; catch stable job-domain
idempotency conflict, re-read and validate winner, không compensate shared run
trên convergence. Nếu worker chứng minh cần sửa `app/persistence/models.py` hoặc
migration/index toàn cục, dừng `BLOCKED_SCOPE_EXPANSION` cho Codex; prompt này
không cấp quyền migration/global schema rewrite.

### 5.2 Forbidden/frozen

- `app/workflow/s10_full_apply_jobs.py` completion-CAS frozen byte-for-byte
- planner, renderers, S09 authority, migration/schema/model files
- frontend, T04B/T04C specs/harness, build and retained bundles
- MAIN production files, S11/S12/S13, user data, Git history
- test-only bypass, sleep-as-synchronization, swallowed exceptions, duplicate
  cleanup after the fact, weakened assertions, fake publication/checkpoint,
  monkeypatch that replaces the production transition being tested

### 5.3 Binary implementation requirements

#### F1 — true concurrency and one canonical work

1. Two simultaneous identical repair replays converge to exactly one durable
   job row and one run; no transient/final second claimable job.
2. Both requests return truthful convergent outcomes. Stable idempotency
   conflict is not treated as generic enqueue failure and must not compensate
   the shared winning run back to failed.
3. One deterministic generation identity is used consistently by Submit,
   repair/replay, Retry and Resume job creation paths where the same S10 job
   identity can race.
4. Replay-vs-Retry and worker-claim-vs-Retry cannot leave two active canonical
   jobs or two active attempts across the lineage.
5. Do not rely on read-before-write as the only guard; prove a database-backed
   collision/convergence path.

#### F2 — complete immutable job identity

1. Build the expected durable manifest using exactly the same server defaults
   applied by `JobService.create_job`, including `schema_version`,
   `managed_root`, `project_root`, complete authority/media pins and exact key
   set.
2. Compare canonical full dictionaries deeply and order-insensitively. Missing,
   extra, malformed or changed immutable fields fail closed before 200/202.
3. Validate job type, idempotency key, deterministic generation, workspace,
   owner type/id and manifest run/project/checkpoint/plan identities.
4. Valid unchanged replay remains idempotent and creates zero side effects.

#### F3 — explicit lifecycle truth

1. Implement and document an explicit allowed run-status/job-state matrix.
2. `failed + queued/running` may be coherently healed only by the exact repair
   case after complete identity validation.
3. `cancelled/completed + queued/running` and other terminal/active
   contradictions fail closed with no mutation and never `reused=true`.
4. Terminal legitimate control pairs and active legitimate pairs retain their
   intended behavior; no publication/checkpoint mutation from replay checks.

### 5.4 Mandatory RED-first deterministic tests

Tests must fail on pre-C12 bytes and pass only after the fix:

1. Actual concurrent repair replay with two threads/clients and
   `threading.Barrier` or Events. Assert both participants reached the barrier;
   sequential A-then-B is forbidden.
2. Repeat the concurrent case on fresh DBs enough times to shake out the
   collision path; each iteration asserts exactly one run, one key, one job,
   one active work and zero publication/checkpoint.
3. Deterministic replay-vs-Retry barrier covering the pre-check/post-check/
   enqueue window; assert at most one active lineage job/attempt.
4. Deterministic worker-claim-vs-Retry barrier using real job state/CAS, not a
   sequential state edit mislabeled as a race.
5. Stable idempotency-collision control: winner is reused; loser does not mark
   the shared run failed.
6. Mutate separately `project_root`, `schema_version`, add an unknown extra
   key, remove one expected key, and alter a nested authority pin; every replay
   fails closed with unchanged counts.
7. Wrong job key/type/workspace/project/owner/generation fail closed; valid
   unchanged replay control succeeds.
8. Lifecycle matrix: cancelled+queued, completed+running fail closed;
   failed+queued exact repair heals; valid active and valid terminal controls.
9. Retain all C6D/C10/C9 lifecycle/compensation/completion-CAS tests unchanged.

No `time.sleep` may be the correctness mechanism. Evidence must show actual
barrier rendezvous and final raw database rows.

## 6. J6F Manager verification

Sau worker `TASK_SUBMITTED`, Manager review diff/code/tests trực tiếp; không chỉ
đọc REPORT. Nếu finding còn, resume same C12 owner.

Required fresh gates:

1. Three independent after-reproductions matching §4, under `after/**`.
2. C12 race/lifecycle/manifest focused suite x2 on distinct fresh roots.
3. Retained T01C C9/C10/C6D suite x2.
4. Full `tests/test_s10*.py` x2 on distinct fresh short roots.
5. Ruff functional errors over all touched production/test files; mypy exact
   touched production; `git diff --check`.
6. Alembic exactly one head; OpenAPI path/op/distinct operation-id counts and
   zero duplicates; J1-v4 13/13 and EOL guard.
7. Source review proving all S10 job-create pathways use deterministic
   non-NULL generation consistently, stable conflict convergence exists, and
   no loser compensation corrupts the winner.
8. Protected SHA/write-set/porcelain attribution and DB-env proof.

Any actual duplicate job, serial test labeled concurrent, 200 reused on a
manifest/lifecycle mismatch, missing barrier proof, test failure/skip, static
error, schema drift or forbidden write is binary fail and routes correction to
the same C12 owner.

## 7. Retained evidence and terminal

Because scope is backend lifecycle only and frontend/build bytes must remain
identical, hash-verify and retain current C6B 20/20 live UI, two C6B verticals,
and C6C 8/8 focused live evidence. Do not rerun expensive UI/vertical unless a
relevant contract/hash changes; if so stop for Codex scope decision.

At success, stop writers/watchers/owned services, remove heartbeat, verify
ports free, append task/session/model/write-set/tests/evidence/risks to T01C
LOG/REPORT and integration registry, and write:

`S10-C6E = SPRINT_SUBMITTED / TASK_MANAGER_VERIFIED / PENDING_CODEX_REREVIEW`

Không ghi APPROVED/CLOSED, không mở S11/S12/S13, không tiếp tục backlog. Bắt đầu
ngay: rules load -> preflight -> immutable before probes -> resume C12 exact
owner bằng exact BAI DeepSeek -> verify J6F -> terminal; không chỉ trả kế hoạch.
