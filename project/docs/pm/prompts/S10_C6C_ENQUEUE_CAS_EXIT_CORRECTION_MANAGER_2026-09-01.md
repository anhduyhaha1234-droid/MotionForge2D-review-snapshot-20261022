Bắt buộc đọc TOÀN BỘ file
`C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi
preflight, dispatch, review nội bộ hoặc production write. Ghi `RULES_LOADED`
với absolute path, logical line count và SHA-256. Canonical hiện tại là 180
dòng, SHA-256
`987386c59f72145bdeb203473a2e3949d46d309cca68fdc95b612925c8f5aa25`.
Nếu không đọc được toàn bộ hoặc SHA khác, dừng `BLOCKED_RULES_DRIFT`; không dựa
vào lịch sử chat/tóm tắt cũ.

# S10-C6C — Enqueue coherence + completion-CAS exit correction

Bạn là Hermes Manager dài hạn của MotionForge2D. Hãy thực thi correction và
exit gate, không chỉ trả kế hoạch. Manager không được tự sửa production code.

## 1. Authority và verdict

Codex independent verdict:

`S10-C6B = CHANGES_REQUESTED / NOT_APPROVED`

Vòng được cấp quyền là `S10-C6C`, chỉ sửa hai finding lifecycle của exact
S10-T01C owner rồi chạy exit gate. Không mở sprint/task sản phẩm mới, không mở
S11/S12/S13, không tự ghi APPROVED/CLOSED.

Required reading sau rules:

1. `C:\Users\Admin\MotionForge2D\AGENTS.md`
2. `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
3. `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
4. `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
5. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C6B_PM_REVIEW_2026-09-01.md`
6. `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S10_C6B_CANCEL_LIFECYCLE_CONTINUATION_MANAGER_2026-08-31.md`
7. Toàn bộ current TASK/LOG/REPORT của S10-T01C và
   `docs/pm/sessions/S10-SESSION_REGISTRY.md` trong integration worktree.

## 2. Workspace, owner, model và guards

- Production worktree duy nhất:
  `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`
- Branch `codex/s08-integration`; expected HEAD
  `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`. Discover và ghi actual state;
  HEAD mismatch => dừng cho Codex quyết định.
- MAIN `C:\Users\Admin\MotionForge2D` chỉ được đọc, ngoại trừ không có PM write
  nào được cấp cho Hermes trong packet này.
- Giữ nguyên dirty write-set/attribution. Cấm commit, push, merge, reset,
  checkout, restore, clean, stash, delete hoặc overwrite evidence cũ.
- Resume đúng exact S10-T01C session:
  `20260828_003035_859fe5`. Không tạo owner/session mới.
- User override mới nhất cho worker correction này: direct exact model
  `BAI/glm-5.3-flash`, reasoning `max`, fallback OFF, TTFB 900. Không dùng
  `comboBAI`, `BAI/deepseek-v4-flash-vision-exp`, `ocg/deepseek-v4-flash`,
  Meta/Muse/OpenRouter hoặc alias gần giống.
- Preflight phải probe exact selector/effective route và lưu raw evidence tại
  `output/s10/c6c/manager/prep/model/**`. Invocation dự kiến:
  `hermes --resume 20260828_003035_859fe5 --provider custom -m BAI/glm-5.3-flash --yolo`.
  Nếu CLI thực tế không chấp nhận `--provider custom`, chỉ được dùng cú pháp đã
  probe chứng minh effective model chính xác `BAI/glm-5.3-flash`; không silent
  fallback. Sai route => `BLOCKED_MODEL_ROUTE`.
- `MOTIONFORGE_DATABASE_URL` phải UNSET. Mọi DB, basetemp, runtime, output và
  ports của correction/gate phải fresh, isolated, ngắn vừa đủ cho Windows
  long-path tests và không chạm user data/retained evidence.

## 3. Serialized DAG

Thực thi liên tục:

`PREP -> S10-T01C-C10 -> J6D -> RETAINED-EVIDENCE-CHECK -> EXIT`

Chỉ một writer. Iteration/context limit không phải blocker: sau khi process
thoát, audit landed bytes/log rồi resume CÙNG exact session/model/scope cho tới
khi `TASK_SUBMITTED` hoặc có blocker mới ngoài scope.

Heartbeat mỗi 20 phút. Nếu worker im lặng 8 phút, audit PID/process tree,
command line, CPU, log mtime/size và file mtimes trước khi kết luận. Network/
connection retryable failure: chờ tối thiểu 5 phút rồi resume cùng exact
session/model; không tạo session khác và không đổi model.

## 4. PREP — Manager read-only

Tạo evidence mới dưới `output/s10/c6c/manager/prep/**`:

1. rules/instructions hash, timestamp/timezone, cwd, branch, HEAD, status,
   `git diff --check`, DB env và protected baseline;
2. process/listener inventory; chỉ dọn PID chứng minh thuộc packet này;
3. hash baseline cho toàn bộ S10-T01C files, frontend/T04B/T04C harness, current
   build và hai final vertical bundles;
4. xác nhận no active S10 writer và registry terminal C6B;
5. chạy lại hai Codex reproductions bằng real route + real JobService + isolated
   SQLite:
   - Submit create-job failure -> identical replay đang trả 200 reused nhưng
     zero durable job;
   - Retry create-job failure -> attempt 2 pending nhưng zero durable job.

Không sửa code trong PREP. Reproduction phải lưu exact HTTP body và DB rows.

## 5. S10-T01C-C10 — resume exact owner

### 5.1 Exclusive allowed write scope

- `app/api/routes/s10_full_apply.py`
- `app/workflow/s10_full_apply_jobs.py`
- bounded `app/workflow/job_service.py` chỉ nếu cần reuse/add same-session atomic
  lifecycle primitive; không refactor unrelated worker infrastructure
- `tests/test_s10_full_apply_api.py`
- `tests/test_s10_full_apply_workflow.py`
- append-only current S10-T01C `TASK.md`, `LOG.md`, `REPORT.md`
- append-only `docs/pm/sessions/S10-SESSION_REGISTRY.md`
- new evidence only: `output/s10/c6c/t01c-c10/**`

Forbidden: migrations/models/schemas, S09 authority, T02/T03/T04 production,
frontend/e2e/harness/fixtures/build, ROADMAP/handoff/reviews/prompts ở MAIN,
J1-v4, user data và evidence C6B trở về trước.

### 5.2 F1 — coherent Submit and Retry enqueue lifecycle

1. Không active Full Apply run/attempt nào được tồn tại vô hạn mà không có
   durable job tương ứng.
2. Submit first-create:
   - authority/pins vẫn server-derived, immutable và fail-closed;
   - run+job phải atomic trong một transaction/session, hoặc mọi post-commit
     enqueue failure phải CAS-compensate run thành trạng thái coherent,
     non-claimable trước khi route kết thúc;
   - không nuốt lock, authority, manifest hoặc create-job failure.
3. Submit replay/dedupe:
   - tuyệt đối không trả 200 `reused=true` chỉ vì run row tồn tại;
   - trước success phải chứng minh exact durable job tồn tại, ownership/
     idempotency key đúng và immutable manifest/authority khớp;
   - nếu gặp historical pending run thiếu job, atomically repair exact job hoặc
     fail/compensate rõ ràng; không tạo duplicate job/run.
4. Retry:
   - authority revalidation nên xảy ra trước mutation khi có thể;
   - mọi failure sau commit, gồm authority/pin mismatch và `create_job`, phải
     compensate successor attempt thành durable coherent non-active state hoặc
     rollback atomically;
   - predecessor cancelled giữ nguyên; zero publication/checkpoint mutation;
   - success chỉ khi đúng một canonical successor job tồn tại.
5. Duplicate/idempotency exception chỉ được coi là success sau read-back chứng
   minh exact matching job; không swallow broad exception.
6. Giữ nguyên minimal-submit C8, approval-v2 authority, T03 recompute,
   cancel/resume semantics đã xanh và public response shape trừ khi bắt buộc để
   trả truth. Không migration/schema redesign.

### 5.3 F2 — verify completion CAS in pre-existing-publication branch

1. Nhánh `has_completed` phải kiểm tra conditional/CAS completion trong cùng
   transaction như nhánh publication bình thường; không chỉ execute rồi commit.
2. Cancel landing sau pre-check nhưng trước CAS phải thắng:
   - run không bị đổi `cancelled -> completed`;
   - handler không return success;
   - không ghi checkpoint `completed:true`;
   - durable job drains cancelling/cancelled;
   - không tạo/claim completed publication mới.
3. No-cancel legacy/resume control vẫn hoàn tất truthfully và chỉ ghi completed
   checkpoint sau verified CAS.
4. Ưu tiên dùng một helper/CAS result contract chung để hai nhánh không drift;
   không thêm caller-controlled production test hook.

### 5.4 Tests bắt buộc

Dùng real route + real JobService + cùng isolated SQLite; test-only barriers/
monkeypatch được phép nhưng không mock away transaction/lifecycle:

- forced Submit `create_job` failure -> HTTP failure và zero active orphan;
- identical Submit replay sau failure -> không 200 reused với zero job; nếu
  repair thì exactly one matching job và immutable manifest khớp;
- forced Retry `create_job` failure -> predecessor unchanged, successor không
  active orphan, zero successor job/publication/checkpoint;
- forced post-commit Retry authority/revalidation failure có cùng compensation;
- Retry success/replay -> exactly one canonical successor/job;
- deterministic completed-publication resume race: false pre-check, cancel
  commits before completion CAS -> cancelled run/job, no completed checkpoint,
  no new publication;
- same branch no-cancel control -> verified completed run/checkpoint;
- retained queued/running/mid-chunk/final-chunk cancel tests, resume creation
  failure test và C8 authority/minimal-submit tests vẫn xanh.

Không skip/xfail/ignore, không nới assertion, không đổi fixture thành synthetic
success. Chạy focused suite hai lần trên fresh distinct roots. Append full truth
vào T01C LOG/REPORT; terminal worker chỉ `TASK_SUBMITTED`.

## 6. J6D — Manager independent gate

Chỉ bắt đầu khi exact worker đã thoát và tree ổn định. Manager đọc diff/code,
không tin riêng REPORT:

1. chạy hai reproduction PREP và xác nhận đều bị sửa;
2. new failure/race tests + retained lifecycle/C8 focused suite x2 fresh roots;
3. full `tests/test_s10*.py` x2 trên roots có độ dài phù hợp để cả hai long-path
   fixtures thực sự kiểm tra >260 và không chạm Win32 unprefixed limit;
4. Ruff `--select F` exact và mypy exact ba production files;
5. Alembic exactly one head; OpenAPI materialize zero duplicate operation IDs,
   dùng một counter chuẩn và ghi rõ method set;
6. J1-v4 13/13 + EOL guard; `git diff --check`; write-set attribution; broad
   exception/no-active-orphan source sweep;
7. Manager-owned real API+worker probes cho Submit failure/replay, Retry failure,
   CAS-cancel race và happy path;
8. current build validator 7/7. Frontend/harness/build bytes phải hash-equal
   baseline; nếu worker chạm bất kỳ forbidden frontend/harness byte nào, dừng
   `BLOCKED_SCOPE_VIOLATION`.

J6D fail thuộc finding => resume cùng exact T01C session. Không mở T04B/T04C
worker.

## 7. Retained evidence and focused live check

Nếu frontend/harness/build/authority contract hashes không đổi:

- retain raw 20/20 UI evidence tại
  `output/s10/c6b/t04b-c3/run20-final/**`;
- retain đúng hai final passing verticals tại
  `output/s10/c6b/t04c-c5/run2-c6b-green/run1/**` và
  `output/s10/c6b/t04c-c5/run2-c6b-green/run2/**` cùng hai distinct runtime
  roots/lifecycle files;
- không dùng `run1-c6b-green` làm final green evidence vì đó là earlier failed
  attempt;
- không rebuild hoặc rerun hai full verticals vô ích.

Manager phải chạy focused current-build live lifecycle check cho Submit,
Cancel, Retry và Resume ở desktop + mobile (8 cases, zero skip) hoặc một bộ
tương đương chứng minh cùng product paths. Nếu public contract/happy-path bytes
đổi hoặc focused live check fail, dừng với exact finding; không tự mở T04B/T04C
scope.

## 8. EXIT

Nếu và chỉ nếu mọi gate xanh, tạo
`output/s10/c6c/manager/exit/EXIT_VERDICT.md`, append registry và trả terminal:

`S10-C6C = SPRINT_SUBMITTED / TASK_MANAGER_VERIFIED / PENDING_CODEX_REREVIEW`

EXIT index phải gồm commands, exit codes, test counts/durations/roots, model
effective-route ledger, branch/HEAD/status, hashes, reproduction before/after,
correct final UI/vertical paths, process/port cleanup và mọi correction turn.

Không ghi APPROVED/CLOSED, không commit/push/merge, không mở S11/S12/S13. Sau
terminal, dừng mọi writer và yêu cầu người dùng gọi Codex review một lần.

Chỉ dừng sớm `BLOCKED_* / PENDING_CODEX_DECISION` khi có defect mới ngoài
allowlist, cần schema/migration/authority redesign, exact owner không thể resume
sau retry policy, exact direct GLM route không khả dụng, J1 drift hoặc môi
trường ngoài packet không thể xử lý an toàn. Báo exact file:line, reproduction,
owner và scope cần mở; không chỉ nói “bị block”.
