# S10-C6B — Cancel lifecycle correction and automatic S10 exit continuation

Bạn là Hermes Manager dài hạn của MotionForge2D. Thực thi công việc, không chỉ
trả kế hoạch.

## 0. Bắt buộc trước mọi hành động

Đọc TOÀN BỘ, không đọc lướt và không chỉ đọc đoạn đầu:

1. `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`
2. `C:\Users\Admin\MotionForge2D\AGENTS.md`
3. `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
4. `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
5. `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
6. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C6A_CANCEL_LIFECYCLE_PM_DECISION_2026-08-31.md`
7. TOÀN BỘ packet hiện tại của S09-T06A, S10-T01C, S10-T03, S10-T04B,
   S10-T04C và `docs/pm/sessions/S10-SESSION_REGISTRY.md` trong integration
   worktree.

Ghi evidence `RULES_LOADED` gồm logical line count và SHA-256. Nếu rules không
đọc được toàn bộ hoặc SHA khác canonical
`987386c59f72145bdeb203473a2e3949d46d309cca68fdc95b612925c8f5aa25`, dừng
`BLOCKED_RULES_DRIFT`; không tự suy diễn.

## 1. Verdict và authority của vòng này

Codex verdict:

`S10-C6A = CONTINUATION_AUTHORIZED / NOT_APPROVED`

Vòng này là `S10-C6B`. Không mở sprint mới. Không approve/close S10 cho tới
EXIT và Codex re-review.

Lỗi hiện tại là production lifecycle defect thuộc T01C:

- cancel route giữ request write transaction rồi mở read session + second
  writer; SQLite báo `database is locked`;
- `except Exception: pass` nuốt lỗi, route vẫn trả cancelled;
- durable job tiếp tục chạy và worker unconditional update ghi đè
  `cancelled -> completed`, có thể publish sau Cancel;
- resume route có multi-session/silent-success risk tương tự.

Codex đã cấp quyền bounded cho correction này. Không dừng lại để hỏi lại đúng
scope đã được ghi rõ dưới đây.

## 2. Workspace, ownership và model bắt buộc

- MAIN `C:\Users\Admin\MotionForge2D` là read-only đối với production code.
  Chỉ Codex PM sở hữu docs PM ở MAIN.
- Mọi worker làm việc tại
  `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`, branch
  `codex/s08-integration`, giữ nguyên dirty tree và attribution hiện có.
- Không reset, checkout, stash, clean, commit, push hoặc merge.
- Không tạo owner/session mới cho task đã có. Resume đúng exact owner:
  - T01C: `20260828_003035_859fe5`
  - T04B: `20260828_020206_b1f8af`
  - T04C: `20260828_023122_76b87e`
- MỌI worker/resume bắt buộc model selector/effective route chính xác
  `ocg/deepseek-v4-flash`, reasoning `max`, fallback OFF, TTFB 900. Đây là user
  override mới nhất; route thử nghiệm `BAI/deepseeekv4flash` đã bị rút lại vì
  không ổn định và tuyệt đối không được dùng trong C6B.
- Preflight phải probe chính xác `ocg/deepseek-v4-flash`, ghi raw command,
  response và effective-route evidence. Không dùng alias gần giống, không tự
  sửa spelling/case, không dùng BAI/OpenRouter/CMC/Meta hoặc auto-fallback. Sai
  hoặc unavailable route là `BLOCKED_MODEL_ROUTE`.
- Iteration limit không phải scope blocker: resume CÙNG exact session, giữ
  context/evidence/write-set và tiếp tục phần còn lại. Không tạo session mới.

## 3. Preflight Manager — không production write

Tạo evidence dưới `output/s10/c6b/manager/prep/**`:

1. date/timezone, cwd, branch, HEAD, `git status --short`, DB env UNSET;
2. process/listener inventory và ownership; chỉ dọn PID do packet này sở hữu;
3. hash/write-set baseline cho T01C backend, T04B frontend, T04C harness và
   J1-v4 freeze;
4. đọc current registry/TASK/LOG/REPORT và xác nhận không worker S10 nào còn
   active trước khi dispatch;
5. re-run deterministic SQLite reproduction
   `output/s10/c6a/t04b-c3/live-defect-cancel-route/repro.sqlite.py`;
6. ghi retained evidence inventory: J6A approval v2, T01C-C8 minimal submit,
   T03-C5 alignment/J6B 216 passed, T04B executable probe/build/live findings.

Không xóa/recreate evidence C6A. C6B chỉ append/add isolated evidence.

## 4. Serialized DAG bắt buộc

Thực thi liên tục theo thứ tự:

`PREP -> S10-T01C-C9-LIFECYCLE -> J6C -> S10-T04B-C3 -> J6-UI -> J6-BUILD -> S10-T04C-C5 -> EXIT`

Không parallel các node trên. Khi một node pass, tự chuyển node kế tiếp. Chỉ
dừng chờ Codex nếu xuất hiện blocker MỚI đúng terminal conditions ở §10.

## 5. S10-T01C-C9-LIFECYCLE — resume exact owner

Resume session `20260828_003035_859fe5`; không tạo worker mới.

### 5.1 Exclusive bounded write scope

- `app/api/routes/s10_full_apply.py`
- `app/workflow/s10_full_apply_jobs.py`
- bounded `app/workflow/job_service.py` CHỈ khi chứng minh cần same-session /
  atomic lifecycle API; ưu tiên reuse repository/session hiện có
- `tests/test_s10_full_apply_api.py`
- `tests/test_s10_full_apply_workflow.py`
- append-only
  `docs/pm/sessions/S10-T01C-full-apply-api/{TASK,LOG,REPORT}.md`
- new evidence only: `output/s10/c6b/t01c-c9/**`

Nếu tên thư mục packet T01C thực tế khác, dùng đúng thư mục registry đang trỏ
tới; không tạo packet song song.

### 5.2 Required production semantics

1. Cancel run và durable job phải là một lifecycle transition coherent,
   fail-closed. HTTP success không được để job claimable/running mà thiếu durable
   cancellation signal.
2. Không chỉ “commit trước rồi hy vọng cancel job thành công”. Chọn một thiết kế
   có atomicity hoặc rollback/compensation rõ ràng; chứng minh false-success là
   bất khả.
3. Không swallow lock/transition/enqueue failure. Trả HTTP status/detail phù
   hợp, rollback/compensate trạng thái và ghi test cho failure path.
4. Cancel idempotent. Race với job terminal phải trả truth, không giả success.
5. Worker kiểm tra cancel tại ít nhất: trước mỗi chunk, sau final chunk/trước
   stitch, trước publication và trước completion.
6. Completion phải dùng conditional/CAS transition, không unconditional UPDATE
   ghi đè `cancelled`. Sau khi cancel thắng race, zero completed publication.
7. Audit retry và resume trong cùng bounded lifecycle round:
   - không second-writer deadlock;
   - không dùng request session sau commit theo cách tạo stale/implicit txn mơ
     hồ;
   - không nuốt lỗi create-successor/create-job;
   - route chỉ trả success khi durable job state tương ứng đã tồn tại;
   - canonical v2 authority/fingerprint/pins vẫn được revalidate, không copy,
     scan, guess hoặc regenerate.
8. Giữ nguyên minimal submit C8, approval v2, T03 semantics, schemas/migrations.

### 5.3 Required tests — real route + real JobService + same SQLite

Không mock away transaction race. Tạo deterministic barriers/hooks chỉ trong
test code nếu cần:

- cancel queued before claim;
- cancel concurrent with claim/running;
- cancel mid-chunk;
- cancel after final chunk but before stitch/publication;
- after worker drains: run remains cancelled, job has cancelling/cancelled
  history, zero completed publication, no completed checkpoint;
- injected SQLite lock/transition failure is surfaced, not swallowed, and state
  is coherent;
- repeated cancel is idempotent;
- cancel/worker terminal race returns honest status;
- retry after cancelled creates one canonical successor; predecessor remains
  cancelled;
- resume with missing/terminal job creates/reactivates exact durable successor,
  has no lock, and injected creation failure cannot return `resumed: true`.

Run focused tests twice with distinct fresh basetemp roots. Also rerun retained
T01C C8 authority/minimal-submit tests; expected test fallout in owned T01C
files is part of this authorization, not a new scope blocker.

Append TASK/LOG/REPORT truthfully and end worker node `TASK_SUBMITTED`; worker
không tự nhận MANAGER_VERIFIED/APPROVED/CLOSED.

## 6. J6C — Manager independent gate

Manager đọc code/diff và chạy độc lập, không chỉ tin worker report:

1. exact lifecycle focused suite x2 fresh roots;
2. retained T01C-C8 targeted suite x2;
3. full `tests/test_s10*.py` fresh root;
4. exact Ruff and exact mypy over all S10 production/test files;
5. OpenAPI materialization with required minimal submit unchanged, zero duplicate
   operation IDs;
6. Alembic exactly one existing head; no migration/schema drift;
7. J1-v4 byte/EOL freeze;
8. `git diff --check`, source sweep for broad exception swallow in the three
   lifecycle routes, write-set attribution and no forbidden drift;
9. a Manager-owned API+real worker race probe proving cancel cannot become
   completed or publish.

Evidence: `output/s10/c6b/manager/j6c/**`. J6C fail => route correction về cùng
exact T01C session; không tạo owner mới và không mở T04B sớm.

## 7. Resume S10-T04B-C3 and close live UI acceptance

Sau J6C xanh, resume exact owner `20260828_020206_b1f8af` với existing C3
context. Không restart task và không bỏ evidence đã làm.

- Giữ executable fixture, minimal-submit UI, probe và current build truth.
- Chạy scenarios 5 Cancel và 6 Retry trước để xác nhận backend lifecycle fix.
- Sau đó chạy toàn bộ 20/20 cases = 10 scenarios × desktop Chromium + mobile
  Chromium 390x844, zero skip, trên services/build cô lập.
- Cancel phải click thật, quan sát durable status/job/progress; Retry đổi sang
  successor run thật; Resume tạo/tiếp tục durable job thật; reload giữ backend
  truth; không synthetic completion hoặc empty-state pass.
- Frontend defect trong original T04B write scope được sửa bởi cùng owner. Mọi
  backend defect mới ngoài correction đã cấp quyền => §10.
- Append existing T04B TASK/LOG/REPORT, evidence
  `output/s10/c6b/t04b-c3/**`, terminal `TASK_SUBMITTED`.

J6-UI Manager verify 20 listed/20 passed/0 skipped, desktop+mobile, DB/job/run
truth, origin env-driven, TSC, exact full Apply ESLint zero warning, no
assertion weakening.

## 8. J6-BUILD

- Hash production frontend source against build C6A
  `cLDP_DE3A0wuASQWew1vM`.
- Nếu production frontend bytes không đổi: ghi hash-equality proof và giữ build
  hiện tại; không tiêu chi phí build vô ích.
- Nếu production frontend bytes đổi: tạo fresh production build, ghi BUILD_ID,
  validator 7/7, TSC, exact ESLint, origin scan và artifact hash. T04C bắt buộc
  dùng chính BUILD_ID mới.

## 9. Resume S10-T04C-C5 and EXIT

Resume exact owner `20260828_023122_76b87e`; không tạo session mới.

Chạy hai vertical runs fresh, distinct, trên current validated BUILD_ID:

- executable approval v2 và server-derived minimal submit qua product paths;
- real media/asset authority, immutable hashes/pins, zero client/DB authority
  fabrication;
- cancel/retry/resume lifecycle fix được dùng thực, không direct DB patch;
- restart/recovery, affected-only durable correction, exact attempts/calls,
  unchanged segment reuse;
- completed publications decodable và DB-bound SHA/size/path/timebase truth;
- structural compare empty client hint, measured server evidence, negative
  tamper/failure rules;
- distinct run IDs, DB roots, ports/process identities; owned cleanup only.

Sau đó Manager EXIT độc lập:

- full S10 suite x2 fresh distinct roots;
- Ruff/mypy exact zero;
- Alembic one head, OpenAPI zero dup, J1-v4 13/13 + EOL;
- frontend TSC, exact full Apply ESLint zero warning, build validator 7/7;
- 20/20 live UI evidence + two vertical bundles on current build;
- DB/file/media/authority/lifecycle/restart/recompute truth;
- process/port cleanup, diff-check, write-set and model ledger.

Nếu tất cả xanh, terminal duy nhất:

`S10-C6B = SPRINT_SUBMITTED / TASK_MANAGER_VERIFIED / PENDING_CODEX_REREVIEW`

Không tự ghi APPROVED/CLOSED. Không mở S11/S13 production. Cập nhật registry và
các packet worktree append-only; trả full evidence index cho Codex review.

## 10. Khi nào được dừng

Không dừng chỉ vì worker hết iteration, test chạy lâu, có expected owned-test
fallout hoặc cần resume cùng exact session. Manager phải tiếp tục DAG đã được
cấp quyền.

Chỉ dừng `BLOCKED_* / PENDING_CODEX_DECISION` khi có một trong các điều kiện:

- production defect MỚI nằm ngoài mọi write scope đã cấp quyền;
- cần schema/migration/S09 authority redesign hoặc mở owner khác;
- exact `ocg/deepseek-v4-flash` route không khả dụng và không thể resume đúng
  model;
- canonical J1 drift;
- môi trường ngoài task không thể khắc phục an toàn;
- đã đạt final `SPRINT_SUBMITTED` và cần Codex re-review.

Khi dừng, phải nêu exact file:line, reproduction, owner attribution, scope cần
mở và prompt/decision request; không chỉ ghi “bị block”.
