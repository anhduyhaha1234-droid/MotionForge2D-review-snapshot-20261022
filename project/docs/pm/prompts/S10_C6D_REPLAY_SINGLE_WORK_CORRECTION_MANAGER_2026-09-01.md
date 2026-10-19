Bắt buộc đọc TOÀN BỘ file
`C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi
preflight, dispatch, review nội bộ hoặc production write. Ghi `RULES_LOADED`
với absolute path, logical line count và SHA-256. Canonical hiện tại là 180
dòng, SHA-256
`987386c59f72145bdeb203473a2e3949d46d309cca68fdc95b612925c8f5aa25`.
Nếu không đọc được toàn bộ hoặc SHA khác, dừng `BLOCKED_RULES_DRIFT`; không dựa
vào lịch sử chat/tóm tắt cũ.

# S10-C6D — Replay coherence, immutable job identity, single canonical work

Bạn là Hermes Manager dài hạn của MotionForge2D. Hãy thực thi bounded
correction và exit gate, không chỉ trả kế hoạch. Manager không được tự sửa
production code.

## 1. Authority và verdict

Codex independent verdict:

`S10-C6C = CHANGES_REQUESTED / NOT_APPROVED`

Vòng được cấp quyền là `S10-C6D`, chỉ sửa hai finding replay/single-work của
exact S10-T01C owner rồi chạy exit gate. Completion-CAS C10 đã được Codex chấp
nhận và phải frozen. Không mở sprint/task sản phẩm mới, không mở S11/S12/S13,
không tự ghi APPROVED/CLOSED.

Required reading sau rules:

1. `C:\Users\Admin\MotionForge2D\AGENTS.md`
2. `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
3. `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
4. `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
5. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C6C_PM_REVIEW_2026-09-01.md`
6. `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S10_C6C_ENQUEUE_CAS_EXIT_CORRECTION_MANAGER_2026-09-01.md`
7. Toàn bộ current TASK/LOG/REPORT của S10-T01C và
   `docs/pm/sessions/S10-SESSION_REGISTRY.md` trong integration worktree.

## 2. Workspace, owner, model và guards

- Production worktree duy nhất:
  `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`
- Branch `codex/s08-integration`; expected HEAD
  `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`. Discover và ghi actual state;
  HEAD mismatch => dừng cho Codex quyết định.
- MAIN `C:\Users\Admin\MotionForge2D` read-only; packet này không cấp PM write
  cho Hermes.
- Giữ nguyên dirty write-set/attribution. Cấm commit, push, merge, reset,
  checkout, restore, clean, stash, delete hoặc overwrite evidence cũ.
- Resume đúng exact S10-T01C session:
  `20260828_003035_859fe5`. Không tạo owner/session mới.
- Model override cuối cùng do user vừa chỉ định cho C6D: direct exact
  `BAI/deepseek-v4-flash-vision-exp`, provider `custom`, reasoning `max`,
  fallback OFF, TTFB 900. Override này thay `BAI/glm-5.3-flash` của C6C và
  draft OCG route cho chính correction tiếp theo. Cấm `comboBAI`, GLM,
  `ocg/deepseek-v4-flash`, Meta/Muse hoặc alias gần giống.
- Preflight phải probe selector/effective route và lưu raw evidence mới tại
  `output/s10/c6d/manager/prep/model/**`. Invocation dự kiến:
  `hermes --resume 20260828_003035_859fe5 --provider custom -m BAI/deepseek-v4-flash-vision-exp --yolo`.
  Nếu route/effective model không khớp exact, dừng `BLOCKED_MODEL_ROUTE`; không
  silent fallback.
- `MOTIONFORGE_DATABASE_URL` phải UNSET. Mọi DB, basetemp, runtime, output,
  cache và port phải fresh, isolated, ngắn vừa đủ cho Windows path tests và
  không chạm user data/retained evidence.

## 3. Serialized DAG và liveness

Thực thi liên tục:

`PREP -> S10-T01C-C11 -> J6E -> RETAINED-EVIDENCE-CHECK -> EXIT`

Chỉ một writer. Iteration/context limit không phải blocker: sau khi process
thoát, audit landed bytes/log rồi resume CÙNG exact session/model/scope cho tới
khi `TASK_SUBMITTED` hoặc có blocker mới ngoài scope.

Heartbeat mỗi 20 phút. Nếu worker im lặng 8 phút, audit PID/process tree,
command line, CPU, log mtime/size và file mtimes trước khi kết luận. Lỗi
network/connection retryable: báo `RUNNING_RETRY_WAIT`, chờ đủ 5 phút rồi resume
cùng exact session/model; không tạo session khác và không đổi model.

## 4. PREP — Manager read-only, evidence append-only

Tạo evidence mới dưới `output/s10/c6d/manager/prep/**`. Tuyệt đối không sửa,
xóa hoặc chạy script ghi vào `output/s10/c6c/**`.

1. rules/instructions hash, timestamp/timezone, cwd, branch, HEAD, status,
   diff-check, DB env, process/listener inventory và protected hashes;
2. hash baseline cho toàn bộ allowed production/test files, completion-CAS
   files, frontend/harness/current build và retained UI/vertical bundles;
3. xác nhận no active S10 writer và C6C registry terminal;
4. tạo reproduction mới ở hai thư mục tách biệt, immutable:
   - `before/failed-run-queued-job-retry/**`: forced initial enqueue failure ->
     replay repair -> immediate Retry; lưu HTTP bodies và mọi run/job row;
   - `before/tampered-manifest-replay/**`: normal Submit -> mutate only isolated
     job manifest -> identical replay; lưu expected/actual manifest, response và
     durable counts.

Không overwrite `before/**` sau khi worker sửa. Post-fix phải ghi mới vào
`after/**`; không dùng chung filename/path. Reproduction phải dùng real route,
real `JobService`, cùng một fresh isolated SQLite DB cho mỗi sequence.

## 5. S10-T01C-C11 — resume exact owner

### 5.1 Exclusive allowed write scope

- `app/api/routes/s10_full_apply.py`
- bounded `app/services/s10_full_apply.py` chỉ nếu cần sửa chính transition/
  retry lineage; không refactor planner/authority khác
- bounded `app/workflow/job_service.py` chỉ nếu cần một same-session atomic
  primitive cho run+job; không refactor durable worker infrastructure
- `tests/test_s10_full_apply_api.py`
- `tests/test_s10_full_apply_workflow.py` chỉ để retain/add exact race control
  nếu API test không thể chứng minh worker claim; không nới C10 CAS tests
- append-only current S10-T01C `TASK.md`, `LOG.md`, `REPORT.md`
- append-only `docs/pm/sessions/S10-SESSION_REGISTRY.md`
- new evidence only: `output/s10/c6d/t01c-c11/**`

Frozen/forbidden: `app/workflow/s10_full_apply_jobs.py` completion-CAS, all
migrations/models/schemas, S09 authority, T02/T03/T04 production,
frontend/e2e/harness/fixtures/build, MAIN roadmap/handoff/reviews/prompts,
J1-v4, user data và mọi evidence C6C trở về trước. Nếu thật sự cần sửa frozen
file, dừng `BLOCKED_SCOPE_EXPANSION` với exact reason; không tự nới scope.

### 5.2 F1 — coherent repaired replay và exactly one canonical work

1. Sau forced first-submit enqueue failure, run có thể ở `failed` với zero job;
   route phải trả failure trung thực.
2. Identical replay chỉ được success khi read-back chứng minh một cặp coherent:
   - đúng run identity/lineage;
   - run ở trạng thái phù hợp với durable job active/terminal;
   - đúng một canonical job, đúng key/type/workspace/project owner;
   - immutable manifest/authority exact-match.
3. Tuyệt đối không tồn tại hoặc trả success cho `run=failed` + `job=queued|running`.
   Nếu repair tạo job cho same run, transition run phải atomic/coherent với job;
   nếu một nửa thất bại phải compensate/fence nửa còn lại trước response.
4. Trong lúc repaired job queued/running, Retry trên predecessor phải fail
   closed (ưu tiên 409 conflict) hoặc deterministically reuse cùng canonical
   work; không tạo attempt/job thứ hai.
5. Replay-vs-Retry và worker-claim-vs-Retry concurrency phải cho at most one
   active canonical job across the lineage. Predecessor/successor truth,
   publication và checkpoint không được mâu thuẫn.
6. Duplicate/idempotency exception không được swallow thành success nếu
   read-back không chứng minh toàn bộ identity + manifest + lifecycle state.

### 5.3 F2 — immutable durable-job identity before replay success

Trước bất kỳ 200/202/reused success nào, canonical-compare đầy đủ:

- job type `S10_FULL_APPLY` hiện hành;
- deterministic idempotency key của exact run;
- workspace, project owner type/id và run identity;
- complete immutable expected manifest re-derived từ persisted run + frozen v2
  approval/canonical authority, bao gồm render authority, source pins,
  replacement assets, timebase, plan/checkpoint identities và managed-root
  identity theo contract hiện hành.

Missing/malformed/tampered/cross-owner/wrong-type/wrong-run manifest phải fail
closed bằng taxonomy rõ (409/422 phù hợp), không trả reused success và không tạo
duplicate run/job. Không tin client body làm authority; không weaken worker
INPUT_CHANGED fence.

### 5.4 Tests bắt buộc — RED trước, exact assertions

Dùng real route + real `JobService` + isolated SQLite; test-only barriers được
phép nhưng không mock away transaction/lifecycle:

1. first enqueue fail -> HTTP failure, run failed/non-active, zero job;
2. identical replay repair -> immediate DB/API run active-coherent + exactly
   one queued/running canonical job, never failed+queued;
3. immediate Retry while repaired job queued -> conflict/reuse, total active
   jobs across lineage exactly one, no attempt-2 active row;
4. same case after worker claim/running -> still no second work;
5. deterministic concurrent identical replays -> one run/job;
6. deterministic replay-vs-Retry and worker-claim-vs-Retry barriers -> at most
   one active canonical work, zero duplicate publication/checkpoint;
7. mutate stored `input_manifest_json` -> identical replay is not 200/202/
   reused success and creates no side effect;
8. wrong run identity, job type/key, workspace/project owner each fail closed;
9. valid unchanged Submit replay remains idempotent and returns truthful state;
10. retained C10 compensation and completion-CAS race/control tests stay exact.

Không skip/xfail/ignore, không nới assertion, không chấp nhận union của mọi job
state như test C10 cũ. Chạy focused suite hai lần trên fresh roots. Append full
truth vào LOG/REPORT; worker terminal chỉ `TASK_SUBMITTED`.

## 6. J6E — Manager independent gate

Chỉ bắt đầu khi exact worker đã thoát và tree ổn định. Manager đọc diff/code,
không tin riêng REPORT:

1. chạy nguyên `before` reproductions từ bản copy/read-only hoặc script mới và
   ghi kết quả post-fix chỉ vào `after/**`;
2. inspect DB after every step; prove no failed+active-job and no two active jobs
   in one lineage;
3. new replay/retry/manifest/race tests + retained lifecycle/C8/C10 suite x2;
4. full `tests/test_s10*.py` x2 trên roots có độ dài phù hợp; ghi rõ nếu fixture
   root đúng 260 và rerun exact test, không che lỗi product;
5. Ruff `--select F` exact và mypy exact touched production files;
6. Alembic one head; OpenAPI zero duplicate operation IDs; J1-v4 13/13 + EOL;
   diff-check; write-set attribution; broad-exception and lifecycle sweep;
7. Manager-owned real API+worker probes cho valid replay, repaired replay,
   immediate retry conflict, replay/retry race, worker claim race và tampered
   manifest;
8. current build validator 7/7. Frontend/harness/build/completion-CAS bytes phải
   hash-equal baseline; drift => `BLOCKED_SCOPE_VIOLATION`.

J6E fail thuộc finding => resume cùng exact T01C session/model. Không mở
T04B/T04C worker.

## 7. Retained evidence và focused live check

Nếu public contract/frontend/harness/build hashes không đổi:

- retain `output/s10/c6b/t04b-c3/run20-final/**` (20/20);
- retain đúng hai final verticals
  `output/s10/c6b/t04c-c5/run2-c6b-green/run1/**` và `/run2/**`;
- retain C6C focused live 8/8 nếu hash/contract match;
- không rebuild/rerun full verticals vô ích.

Manager chỉ cần focused current-build live lifecycle check cho repaired replay
và blocked Retry ở desktop + mobile nếu UI có thể biểu diễn sequence; nếu path
không có UI trigger, một real API+worker probe cùng current build và retained
8/8 là đủ, nhưng phải ghi lý do. Public contract/happy-path drift hoặc live fail
=> exact finding, không tự mở frontend scope.

## 8. EXIT

Nếu và chỉ nếu mọi gate xanh, tạo
`output/s10/c6d/manager/exit/EXIT_VERDICT.md`, append registry và trả terminal:

`S10-C6D = SPRINT_SUBMITTED / TASK_MANAGER_VERIFIED / PENDING_CODEX_REREVIEW`

EXIT index phải gồm commands, exit codes, counts/durations/roots, direct
BAI DeepSeek vision-exp effective-route ledger, branch/HEAD/status/hashes, immutable
before/after evidence paths, exact run/job lineage tables, retained UI/vertical
paths, process/port cleanup và mọi continuation turn.

Không ghi APPROVED/CLOSED, không commit/push/merge, không mở S11/S12/S13. Sau
terminal, dừng mọi writer và yêu cầu user gọi Codex review một lần.

Chỉ dừng sớm `BLOCKED_* / PENDING_CODEX_DECISION` khi cần schema/migration/
authority redesign, exact owner không thể resume sau retry policy, exact direct
BAI DeepSeek vision-exp route không khả dụng, J1 drift hoặc defect ngoài allowlist. Báo exact
file:line, reproduction, owner và scope cần mở; không chỉ nói "bị block".
