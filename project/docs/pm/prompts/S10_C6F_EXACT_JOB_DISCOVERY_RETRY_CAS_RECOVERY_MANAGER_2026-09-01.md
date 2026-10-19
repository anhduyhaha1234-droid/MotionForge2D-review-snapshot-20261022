Bắt buộc đọc TOÀN BỘ file
`C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi
preflight, recovery-session creation, dispatch, review nội bộ hoặc production
write. Ghi `RULES_LOADED` với absolute path, logical line count, SHA-256, HEAD
đang thấy và các mục chính đã nạp. Canonical hiện tại là 193 dòng, SHA-256
`c6ad775a98b9feedcdd435932a0b6659b0ef991b0d43f492e47379cc5ed20089`.
Nếu không đọc được toàn bộ hoặc SHA khác, dừng `BLOCKED_RULES` với reason
`RULES_DRIFT`; không dựa vào lịch sử chat hoặc bản tóm tắt cũ.

# S10-C6F — Closure protocol: exact job identity, truthful Retry, real races

Bạn là Hermes Manager dài hạn của MotionForge2D. Hãy thực thi bounded correction
và exit gate, không chỉ trả kế hoạch. Manager không được tự sửa production
code/test/migration/UI/config; mọi production correction do đúng một worker
recovery session của logical task S10-T01C thực hiện.

## 1. Authority, verdict, required reading

Codex independent verdict:

`S10-C6E = CHANGES_REQUESTED / NOT_APPROVED`

Vòng duy nhất được cấp quyền là `S10-C6F`, correction packet
`S10-T01C-C13`. Không mở S11/S12/S13 hoặc task sản phẩm khác, không tự ghi
APPROVED/CLOSED.

Sau rules, đọc toàn bộ:

1. `C:\Users\Admin\MotionForge2D\AGENTS.md`
2. `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
3. `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
4. `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
5. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C6E_PM_REVIEW_2026-09-01.md`
6. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C6D_PM_REVIEW_2026-09-01.md`
7. `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S10_C6E_TRUE_CONCURRENCY_IMMUTABLE_LIFECYCLE_MANAGER_2026-09-01.md`
8. Toàn bộ current TASK/LOG/REPORT của
   `docs/pm/sessions/S10-T01C-orchestration-api/` và current integration
   `docs/pm/sessions/S10-SESSION_REGISTRY.md`.

## 2. Workspace, recovery authority, model, guards

- Production worktree duy nhất:
  `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`.
- Branch `codex/s08-integration`; expected HEAD
  `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`. Ghi actual HEAD/status; mismatch
  thì dừng cho Codex quyết định.
- MAIN `C:\Users\Admin\MotionForge2D` read-only đối với Hermes.
- Giữ nguyên dirty attribution. Cấm commit/push/merge/reset/checkout/restore/
  clean/stash hoặc xóa/overwrite evidence cũ.
- Logical task owner vẫn là S10-T01C, nhưng Codex đã xác nhận context cũ hỏng:
  original owner `20260828_003035_859fe5`, effective continuation
  `20260831_151420_07b6c2`, latest request dump 1,200,867 bytes / 617 messages /
  14 user turns / 304 tool entries; repeated contract misses và serial test
  mislabeled concurrent. Đây là recovery được Codex cấp quyền theo rules §4.
- Trước recovery, xác nhận không còn process/writer của owner cũ hoặc descendant,
  ports free và tree quiescent. Append registry `OWNER_TRANSFER` với metrics/lý
  do, old owner/effective descendant, timestamp và zero-live-writer proof.
- Sau đó tạo đúng **một new recovery session**, capture session ID mới, gắn nó
  làm owner duy nhất của `S10-T01C-C13`. Không resume owner/descendant cũ sau
  transfer; không để hai writer sống cùng lúc.
- User override mới nhất: worker model exact-case `comboBAI`, provider `custom`,
  reasoning `max`, Hermes fallback chain OFF, TTFB 900. `comboBAI` là combo route
  được phép chọn nội bộ giữa các member; không ép hoặc giả attribution một member.
  Read-only state lúc Codex review gồm `BAI/deepseek-v4-flash-vision-exp` và
  `ocg/deepseek-v4-flash`; Manager phải re-probe current combo membership,
  exact-case selector và lưu effective upstream ledger.
- Invocation worker dự kiến, KHÔNG có `--resume`:
  `hermes -z "<compact C13 prompt>" --provider custom -m comboBAI --yolo --pass-session-id`.
  Probe/dispatch raw evidence ở `output/s10/c6f/manager/prep/model/**`. Sai exact
  selector => `BLOCKED_MODEL_ROUTE`; không capture được owner mới =>
  `BLOCKED_DEPENDENCY` với reason `RECOVERY_OWNER_NOT_CAPTURED`.
- `MOTIONFORGE_DATABASE_URL` phải UNSET. Test DB/temp/output/cache/ports phải
  fresh, isolated, ngắn cho Windows path tests và không chạm user data.

## 3. Task map, DAG, ownership, parallelism

| Task ID | Outcome | Depends on | Owner | Exclusive write-set |
|---|---|---|---|---|
| S10-T01C-C13 | Exact durable-job discovery; truthful/idempotent Retry collision handling; true worker-claim race proof | C6E review + owner transfer | exactly one new recovery session | allowlist §5 |

Serialized production DAG:

`PREP -> LOCK-CLOSURE-MATRIX -> OWNER_TRANSFER -> WORKER-RED -> C13-FIX ->
TASK_SUBMITTED -> J6G{MICRO -> MATRIX-100% -> FOCUSED -> FINAL-BROAD} ->
RETAINED-EVIDENCE-CHECK -> EXIT`

Chỉ một production writer. Không production task nào chạy song song. Sau worker
terminal và tree quiescent, focused/static readers có thể chạy song song với
DB/basetemp/output riêng; full/global gates phải qua một mutex trên checkpoint
bytes nhất quán.

Heartbeat mỗi 20 phút. Im lặng 8 phút audit PID/process tree, command line, CPU,
log mtime/size, file mtimes và trạng thái chờ input. Connection/502/503/504/
disconnect xử lý theo canonical rules; 401/403/config/model error là chẩn đoán
blocker, không retry vô hạn. Không đổi model hoặc tạo owner thứ hai.

## 4. PREP + correction closure protocol (binding)

Tạo mới `output/s10/c6f/manager/prep/**`; không sửa/xóa
`output/s10/c6c/**`, `c6d/**` hoặc `c6e/**`.

### 4.1 Immutable preflight

1. Lưu rules/instructions hashes, timestamp/timezone, cwd, branch, HEAD,
   porcelain attribution, diff-check, DB env, listeners/process inventory,
   protected hashes và old-owner quiescence.
2. Hash toàn allowlist, frozen completion-CAS, model/schema/migrations,
   planner/rendering, frontend/harness/current build và retained UI/verticals.

### 4.2 Manager-owned BEFORE repros — khóa trước dispatch

3. Reproduce trên current production bytes, real route, real JobService, fresh
   SQLite; mỗi case riêng `before/**`:
   - `wrong-idempotency-key/**`: normal Submit; mutate ONLY durable job key;
     identical replay. Expected current defect: 200 reused và tổng **2 Job rows**
     cho cùng run/generation. Query/assert mọi Job row, không filter canonical
     prefix.
   - `repeat-retry-cancelled/**`: normal Submit -> Cancel -> Retry success ->
     Retry lại exact predecessor. Expected current defect: second request 500,
     unique S10 run conflict.
   - `worker-claim-retry-test-audit/**`: prove shipped test executes real worker
     claim and Retry sequentially, has zero second thread/barrier/Event.
4. Nếu baseline không tái hiện, không giả PASS; audit drift trước dispatch.
   Post-fix chỉ ghi `after/**`.

Các script/result/hash trong `output/s10/c6f/manager/prep/before/**` do Manager
sở hữu và trở thành immutable ngay khi dispatch. Worker không được sửa, copy đè
hoặc đổi expected result. Manager ghi SHA-256 manifest của toàn before bundle.

### 4.3 LOCK-CLOSURE-MATRIX — không dispatch nếu chưa khóa

Trước tạo recovery worker, Manager phải viết
`output/s10/c6f/manager/prep/CLOSURE_MATRIX.md` và machine-readable
`CLOSURE_MATRIX.json`. Mỗi row bắt buộc có:

| Field | Nội dung bắt buộc |
|---|---|
| Closure ID | ID ổn định dưới đây |
| Requirement | invariant nhị phân, không phải mô tả chung |
| Current source | exact file:line/function |
| BEFORE evidence | path + actual HTTP + all run/job counts |
| BEFORE class | `RED_DEFECT`, `RETAINED_CONTROL` hoặc `STRUCTURAL_GAP` |
| Worker test | exact test name dự kiến; chưa có phải ghi `TO_ADD` |
| AFTER evidence | path dự kiến; ban đầu `PENDING` |
| Exit assertion | expected HTTP, rows, active work, mutation count |
| Status | `LOCKED_PENDING_FIX`, sau cùng chỉ được `CLOSED` |

Closure IDs tối thiểu, không được bỏ/gộp mơ hồ:

- `F1-K1` wrong idempotency key; `F1-K2` wrong job type; `F1-K3` wrong
  owner type; `F1-K4` wrong owner id; `F1-K5` wrong generation;
  `F1-K6` wrong manifest run ID; `F1-K7` wrong manifest project ID;
  `F1-K8` legitimate zero-job orphan repair; `F1-K9` valid unchanged replay.
- `F2-R1` repeat Retry on cancelled predecessor; `F2-R2` Retry-vs-Retry from
  failed; `F2-R3` Retry-vs-Retry from cancelled; `F2-R4` retained
  Replay-vs-Retry.
- `F3-W1` true worker-claim-vs-Retry race.

Mọi row phải có trước-state thật. Row đã đúng trên current bytes được ghi
`RETAINED_CONTROL`, không được giả là RED. Ba finding Codex F1-K1, F2-R1 và
F3-W1 structural gap phải được reproduce/audit đúng như §4.2. Nếu matrix còn
`TO_ADD` mà không có exact acceptance/expected counts, dừng
`BLOCKED_DEPENDENCY` với reason `CLOSURE_MATRIX_INCOMPLETE`; cấm dispatch worker
bằng prose chung.

### 4.4 Tối ưu vòng correction

- Manager không chạy full S10 suite trong PREP và không chạy lại broad suite sau
  từng worker turn. Chi phí sớm chỉ dành cho BEFORE repro + micro tests.
- Khi một phase fail, resume đúng recovery owner bằng prompt ngắn chỉ gồm failed
  Closure IDs, actual evidence, landed-byte hashes, allowlist và gate kế tiếp;
  không nhồi lại history C6A-C6E.
- Không cho worker tự tuyên bố một row `CLOSED`; chỉ Manager đóng row sau source
  review + independent AFTER reproduction.
- Test name, docstring, worker REPORT và số lượng pass không phải bằng chứng nếu
  source test không thực hiện đúng mutation/rendezvous/count assertion.

## 5. S10-T01C-C13 — recovery worker

### 5.1 Allowed write-set

- `app/api/routes/s10_full_apply.py`
- bounded `app/services/s10_full_apply.py` chỉ nếu cần stable domain handling
  cho duplicate Retry successor; không refactor service/domain khác
- `tests/test_s10_full_apply_api.py`
- append-only T01C TASK/LOG/REPORT + integration registry
- new `output/s10/c6f/t01c-c13/**`; worker không ghi vào
  `output/s10/c6f/manager/**`

### 5.2 Frozen/forbidden

- `app/persistence/jobs.py` (C6E accepted backstop, frozen)
- `app/persistence/models.py`, mọi migration/schema/global index
- `app/workflow/job_service.py`, `app/workflow/s10_full_apply_jobs.py`
- planner, renderers, S09 authority, frontend, T04B/T04C specs/harness, build,
  retained bundles, MAIN production files, S11/S12/S13 và user data
- test-only bypass, sleep-as-correctness, swallowed exception, duplicate cleanup
  after the fact, weakened assertion hoặc monkeypatch thay production transition

Nếu chứng minh cần file ngoài allowlist/migration, dừng `BLOCKED_DEPENDENCY` với
reason `SCOPE_EXPANSION_REQUIRED`, exact repro và lý do; không tự mở scope.

### 5.3 F1 — exact durable-job discovery before repair or reuse

1. Không được dùng expected idempotency-key lookup làm bằng chứng duy nhất rằng
   job không tồn tại. Trước missing-job repair, phải phát hiện mọi durable S10
   job claim cùng run/generation/manifest identity.
2. Wrong key/type/workspace/owner type/owner id/generation hoặc manifest
   run/project/checkpoint/plan identity phải fail closed 409/422 trước success
   hoặc repair; zero mutation và counts unchanged.
3. Một tampered-key job không được trở thành invisible rồi sinh canonical job
   thứ hai. Multiple candidate/ambiguous rows phải fail closed.
4. Legitimate zero-job orphan vẫn repair đúng một canonical job; valid unchanged
   replay vẫn 200 reused và zero side effects.
5. Query/tests phải đếm tất cả Job rows liên quan, không chỉ key bắt đầu bằng
   `s10_full_apply_job:`.

### 5.4 F2 — truthful Retry claim/collision semantics

1. `cancelled -> cancelled` no-op không được coi là exclusive CAS winner.
2. Retry lần hai cùng predecessor phải return stable 409 hoặc converge vào đúng
   existing successor theo semantics được document/test; cấm raw IntegrityError,
   500 hoặc tạo thêm active run/job.
3. Hai simultaneous Retry trên predecessor ban đầu `failed` và trên predecessor
   ban đầu `cancelled` phải qua true barrier, cuối cùng đúng một successor
   run/job active. Loser fail trước mutation hoặc clean rollback/convergence.
4. Existing unique natural/idempotency backstop phải được chuyển thành stable
   domain/API outcome; không swallow và không để session failed transaction.
5. Replay-vs-Retry C6E accepted behavior vẫn phải giữ: một 200 winner, một 409
   loser, một active canonical work.

### 5.5 F3 — real worker-claim-versus-Retry race

1. Thay test serial `test_c6e_worker_claim_vs_retry_barrier` bằng test có hai
   participants thật: worker thread dùng real `JobRepository.transition_job`
   revision/state CAS; Retry chạy đồng thời qua TestClient riêng.
2. Dùng `threading.Barrier`/Events ở deterministic pre-check/CAS window; assert
   cả hai participant rendezvous. Không gọi claim xong rồi mới Retry.
3. Lưu raw outcomes, barrier tokens/count, all run/job rows. Final invariant:
   at most one active lineage job/attempt, run/job lifecycle coherent, không
   publication/checkpoint side effect.
4. Giữ sequential control dưới tên rõ ràng nếu hữu ích, nhưng không dùng nó làm
   race evidence.

### 5.6 Mandatory RED-first tests

Tests mới phải fail trên before bytes và pass sau fix:

1. Wrong idempotency key -> 409/422; total Job count unchanged one.
2. Wrong job type, owner type, manifest run ID, project ID từng case fail closed.
3. Legitimate zero-job repair + valid replay controls.
4. Repeat Retry same cancelled predecessor -> stable 409/converge, never 500.
5. Retry-vs-Retry true barrier on failed and cancelled sources; one successor.
6. Worker-claim-vs-Retry true barrier with real transition CAS.
7. Retain all eight C6E tests and C6D/C10/completion-CAS regressions unchanged.

Không `time.sleep` làm correctness mechanism. Evidence phải có rendezvous và raw
database rows.

### 5.7 Invariant-first implementation, không vá từng symptom

Worker phải chọn và document một thiết kế chung đóng toàn bộ closure rows:

1. Một durable-job resolution path phát hiện canonical claimant, wrong-identity
   claimant, ambiguous/multiple claimant và true zero-job orphan; không thêm
   nhánh đặc biệt chỉ cho `idempotency_key`.
2. Một Retry claim/collision policy tạo outcome ổn định cho first, repeated và
   simultaneous Retry; cấm dựa vào same-state rowcount như ownership token.
3. Mọi API success chỉ xảy ra sau exact identity/lifecycle validation; mọi loser
   rollback/converge sạch trước response.
4. Không “sửa test cho xanh” bằng cách filter chỉ canonical key, bỏ tampered row,
   giảm count assertion hoặc chuyển race thành sequence.

### 5.8 Worker execution phases — bắt buộc đúng thứ tự

**Phase W-RED — test-only trước production code:**

- Thêm/chỉnh tests cho mọi `TO_ADD` row trong locked matrix, chưa sửa production.
- Chạy exact new tests. F1-K1, F2-R1 và race-structure gap phải RED đúng expected
  reason; retained controls phải giữ GREEN. Lưu raw log dưới
  `output/s10/c6f/t01c-c13/worker-red/**`.
- Nếu test mới PASS trước fix vì không chạm defect thật, sửa test/repro cho đúng;
  cấm coi đó là completion.

**Phase C13-FIX:**

- Chỉ sau W-RED credible mới sửa production trong allowlist theo §5.7.
- Chạy lại đúng new tests đến GREEN, ghi `TASK_SUBMITTED`, dừng writer; Manager
  mới được chạy independent MICRO-GATE §6.1 trên tree quiescent.
- Nếu turn bị cắt, báo exact phase/Closure IDs/landed hashes; Manager resume cùng
  recovery owner, không chạy broad gate và không tạo session khác.

## 6. J6G Manager verification — phased, fail-fast, broad gate chạy cuối

Sau `TASK_SUBMITTED`, Manager review diff/code/tests trực tiếp; nếu finding còn,
resume recovery owner mới, không quay lại owner cũ và không tạo owner thứ hai.

### 6.1 MICRO-GATE — rẻ, bắt buộc trước mọi suite rộng

Manager chạy độc lập trên fresh DB/root:

1. AFTER `wrong-idempotency-key`: 409/422, `total Job rows == 1`, unchanged ID/
   key-tampered row, zero new side effect.
2. AFTER repeat Retry: first success + second stable 409/converge, never 500;
   exactly one successor run/job.
3. AFTER true worker-claim-vs-Retry: two live participants, rendezvous true,
   raw outcomes + all DB rows, at most one coherent active lineage work.
4. Retry-vs-Retry barriers from failed và cancelled sources: exactly one
   successor; loser truthful; no unhandled error.
5. Source-structure audit của mọi test mang tên `barrier`, `race`, `concurrent`:
   exact two participant creation, synchronization point, join/timeout,
   rendezvous assertion và all-row final assertion. Test tuần tự là FAIL dù
   pytest xanh.

Micro-gate fail => update exact matrix rows `OPEN`, resume recovery owner bằng
failed-row packet; **không chạy focused/full/static broad gates**.

### 6.2 CLOSURE-MATRIX GATE

Sau micro-green, Manager review source/test trực tiếp và điền AFTER path/actual
cho toàn bộ F1-K1..K9, F2-R1..R4, F3-W1. Chỉ đóng row khi:

`BEFORE classified + worker RED/control credible + implementation reviewed +
independent AFTER exact + exit assertion true`.

Yêu cầu **100% rows CLOSED, 0 PENDING/OPEN/TO_ADD**. Một field/test bị bỏ sót là
binary fail; không bù bằng full-suite pass.

### 6.3 FOCUSED-GATE — chỉ sau matrix 100% closed

1. C13 exact tests x2 trên distinct fresh roots.
2. Retained C6E/C6D/C10/completion-CAS selection x2.
3. Ruff functional errors touched files; mypy exact touched production;
   `git diff --check`.

Nếu focused fail, resume same owner và quay lại đúng failed Closure ID/gate;
không chạy full S10.

### 6.4 FINAL-BROAD-GATE — chỉ một lần trên final checkpoint bytes

Chỉ khi §§6.1-6.3 đều green và writer terminal:

1. Full `tests/test_s10*.py` x2 distinct fresh short roots, global mutex.
2. Alembic exactly one head; OpenAPI path/op/distinct operation-id + zero dup;
   J1-v4 13/13 + EOL guard.
3. Protected SHA/write-set/porcelain/DB-env proof; current build validator và
   retained-evidence hashes nếu relevant bytes unchanged.
4. Effective `comboBAI` member ledger theo từng worker turn; không gán toàn bộ
   combo traffic cho một upstream khi không có evidence.

Sau bất kỳ production edit cuối nào, previous broad result bị invalid và chỉ
rerun final broad gate sau khi micro/matrix/focused đã green lại. Không chạy
broad x2 giữa các continuation turns.

Any 200 reused plus two jobs, second Retry 500, no-op exclusive CAS, serial test
labeled concurrent, missing barrier proof, test fail/skip, forbidden write,
schema/frontend drift là binary fail và phải correction trong cùng recovery
session.

## 7. Retained evidence and terminal

Backend-only scope: hash-retain C6B 20/20 live UI, two final verticals, C6C/C6E
focused evidence và frozen build nếu relevant bytes unchanged. Không rerun UI/
vertical tốn kém nếu hashes vẫn bằng; drift thì dừng cho Codex scope decision.

Khi success: stop writer/watchers/services, remove heartbeat, ports free, append
task/session owner-transfer/model-member ledger/write-set/tests/evidence/risks
vào T01C LOG/REPORT + registry. EXIT report bắt buộc đính kèm final
`CLOSURE_MATRIX.md/json` với 100% rows CLOSED, phase durations và số broad runs
thực tế, rồi ghi:

`S10-C6F = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`

Không ghi APPROVED/CLOSED, không mở S11/S12/S13. Bắt đầu ngay: rules load ->
quiescence/context recovery audit -> immutable before repros -> lock closure
matrix -> create đúng một comboBAI recovery session -> worker RED -> invariant
fix -> micro -> matrix 100% -> focused -> final broad một lần -> retained hashes
-> EXIT; không chỉ trả kế hoạch.
