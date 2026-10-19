Hãy đọc TOÀN BỘ file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi preflight, sửa tài liệu hoặc dispatch/resume worker. Sau đó báo `RULES_LOADED` kèm đường dẫn, SHA-256, HEAD thực tế và các mục rules đã nạp. Chưa hoàn tất thì dừng `BLOCKED_RULES`; tuyệt đối không dùng trí nhớ/tóm tắt cũ.

# S09 C2 — renderer/evidence/durable-path correction Manager prompt

## 1. Authority và mục tiêu

Bạn là HERMES MANAGER của đúng vòng correction S09-C2 do Codex PM phân rã dưới
đây. Codex giữ quyền BA/roadmap, task decomposition, parallel decision và
approval. Manager không tự sửa production code, test, fixture, benchmark, UI hay
config; chỉ preflight, resume đúng owner session, cấp exclusive lock, monitor,
review, chạy gate độc lập và ghi coordination evidence.

Mục tiêu là đóng toàn bộ F1–F7 trong:

`C:\Users\Admin\MotionForge2D\docs\pm\reviews\S09_C1_PM_REVIEW_2026-08-25.md`

Ưu tiên tốc độ tối đa an toàn, không tiết kiệm quota. Được chạy tối đa 5 worker
đồng thời đúng DAG/write-set do Codex cấp dưới đây. Không tự tạo task/subtask ID,
không cho worker mở subworker. Không `APPROVED/CLOSED`; không commit/push/merge/
reset/restore/checkout/clean/stash; không mở S10/S11/S13.

Sau Rules, đọc toàn bộ:

- `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\TARGET_PROFILE_2D_SOURCE_LOCKED.md`
- review C1 nêu trên;
- prompt C1 fast-track, C1 registry và toàn bộ TASK/LOG/REPORT/evidence hiện tại
  của T02, I03, I05, T03, T04 và T06B.

## 2. Preflight và invariant bắt buộc

- Integration worktree duy nhất:
  `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`, expected branch
  `codex/s08-integration`, expected HEAD baseline
  `ee10e55a809c84d5cb5d4a3046a1ee78828528d0`.
- MAIN `C:\Users\Admin\MotionForge2D` read-only tuyệt đối đối với Hermes/worker.
- Ghi actual HEAD, dirty paths, SHA hot files, Alembic heads, env, process command
  lines/ports và quiescence trước dispatch. Không suy đoán từ registry.
- `MOTIONFORGE_DATABASE_URL` phải UNSET; DB/cache/basetemp/runtime dùng thư mục
  cô lập trong `%TEMP%`; không đụng `data/**` hoặc project media.
- Tạo Manager-owned
  `docs/pm/sessions/S09-C2-SESSION-REGISTRY.md` với Task -> exact session ->
  provider/model -> phase/process/state -> exclusive write-set -> hashes -> deps
  -> heartbeat. Worker chỉ append LOG/REPORT của chính task.
- Provider/model của toàn bộ existing owner sessions phải giữ nguyên:
  `custom` qua 9Router `http://127.0.0.1:20128/v1`, model `alpha`, reasoning max,
  fallback disabled. Correction phải resume exact owner; replacement session chỉ
  khi Rules cho phép và có process audit/recovery evidence.
- Heartbeat ít nhất mỗi 20 phút; 8 phút không progress phải audit; lỗi kết nối
  báo ngay, chờ đủ 5 phút rồi resume cùng session/model/API mode. Không coi retry
  nội bộ hết là terminal.

## 3. Quyết định BA/PM đã chốt — không hỏi lại scope

1. `hard_cut` là required structural-preservation risk class. Không được loại
   khỏi S09 hoặc biến thành source re-encode/no-op PASS. Fixture phải có typed
   replacement operation và ít nhất một production route đo thật.
2. `group_occlusion` là required class. Typed renderer surface phải biểu diễn
   layer order/occlusion đủ để replacement đi trước/sau occluder đúng từng frame;
   không chấp nhận empty universe, unknown hoặc contract reject ở sprint exit.
3. Benchmark phải đi qua actual public `RendererRouter` và production adapter.
   Gọi thẳng compositor/private helper không phải measured route evidence.
4. Output phải giữ exact requested frame range và source rational fps/timebase;
   provenance hash phải tính trên canonical decoded frames của encoded output.
5. Mọi hard-code tới old `t00-i05/measured_seed20260823` trong production code,
   frontend và active S09 tests phải bị loại. Archival REPORT/LOG được phép nhắc.
6. Required class fail/unknown/FOQ là blocker; Manager không có quyền ghi
   `TASK_MANAGER_VERIFIED` trong trường hợp đó.

## 4. Dependency DAG và parallel waves do Codex cấp quyền

### Wave A — dispatch đồng thời tối đa 5 workers

1. `S09-T02-C2`, resume exact owner `20260824_015213_f5516b`.
2. `S09-T00-I03-C2-PREP`, resume exact owner `20260823_173318_69a813`.
3. `S09-T03-C2`, resume exact owner `20260824_031524_a6bb2a`.
4. `S09-T04-C2`, resume exact owner `20260824_052859_c6e197`.
5. `S09-T06B-C2-PREP`, resume exact owner `20260824_131423_423e42`.

Năm write-set không giao nhau như các mục dưới. PREP worker phải dừng ở
`WAITING_JOIN`, không tự chốt TASK_SUBMITTED và không chạy global gate khi writer
khác còn active.

### Join J1-C2 — immutable renderer freeze

Chỉ mở khi T02-C2 đã exit, focused tests x2 xanh, I03 PREP đã dừng writer và
Manager review code/test pass. Manager hash đệ quy mọi behavior-critical file:

- `app/services/renderer_contract.py`
- `app/services/renderer_router.py`
- `app/adapters/renderer/**`
- `app/services/renderer_routes/**`

Ghi machine-readable manifest path -> SHA-256 tại
`output/s09/20260823_sprint_full/j1-c2/renderer_freeze_manifest.json`; pin thêm
manifest SHA trong registry. I03 phải verify manifest trước và sau mỗi measured
run. Sau J1 không ai được đổi một file đã pin. Nếu drift, Manager phải dừng I03,
invalidate mọi run/decision downstream, resume đúng owner gây drift, tạo J1 mới
và chạy lại I03/I05; cấm chỉ sửa constant SHA.

### Wave B — measured renderer rồi decision

- Sau J1, resume I03 exact owner để chạy actual router/adapter, complete tests và
  measured run A/B.
- Chỉ sau I03 `TASK_MANAGER_VERIFIED` và exit, resume `S09-T00-I05-C2` exact
  owner `20260823_233406_8d5b7b` để tạo measured decision mới. I05 không sửa code,
  test, fixture hay threshold.

### Join J2-C2 và Wave C

Sau I05-C2 verified, pin SHA benchmark + route decision. Resume song song đúng
owner T03-C2, T04-C2 và T06B-C2 để bind exact C2 evidence, hoàn tất downstream
tests/production-stack E2E. T06B final run chờ T03/T04 writers exit. Không dùng
artifact v1/C1 làm fallback.

## 5. S09-T02-C2 — production renderer contract

### Exclusive write-set

- `app/services/renderer_contract.py`
- `app/services/renderer_router.py`
- `app/adapters/renderer/**`
- `app/services/renderer_routes/**`
- `tests/test_s09_t02_*.py`
- focused `tests/test_s09_t00_renderer_router*.py` khi cần
- `output/s09/20260823_sprint_full/t02-c2/**`
- append-only T02 LOG/REPORT.

Forbidden: benchmark script/fixtures, T03/T04, API correction/approval, frontend,
models/migrations, MAIN, `data/**`.

### Binary acceptance

1. Thêm typed/bounded contract cho rational source fps/timebase và layer ordering/
   occlusion theo frame. `f1_hard_cut` và `f5_group_occlusion` phải representable
   mà không dùng special fixture branch/private test control.
2. `pose_swap`, `sprite_affine` và adaptive/optimized production adapters giữ
   exact inclusive frame count + source fps/timebase. Có tests route thật với ít
   nhất 24 fps và 30 fps; nên thêm 30000/1001 nếu stack hỗ trợ probe ổn định.
3. Xóa `request_id @identity` behavior. Identity chỉ được biểu diễn bằng typed
   field/empty typed keyframes có validation rõ; request ID không đổi nghiệp vụ.
4. `output_frame_sha256` phải hash canonical decoded frames sau encode. Test
   recompute độc lập từ output file và match evidence.
5. Thực thi đúng mọi accepted `alpha_mode`, hoặc thu hẹp enum về semantics thực
   sự hỗ trợ. Validate output container, `output_media != input_media`, path
   containment, frame/order/z bounds, NaN/Inf, schedule/state consistency; mọi
   invalid request fail before artifact mutation.
6. Public router `.execute()` gọi đúng adapter và trả stable taxonomy/provenance.
   CPU deterministic reference và acceleration-only NVENC phải được tách rõ.
7. Focused contract/adapter/router tests x2, Ruff owned files, mypy app. Worker
   ghi exact commands/results/hashes và `STATUS: TASK_SUBMITTED`, rồi exit trước
   J1.

## 6. S09-T00-I03-C2 — valid benchmark harness/fixtures

### Exclusive write-set

- `scripts/s09_renderer_benchmark.py`
- `tests/fixtures/s09_renderer/**`
- `tests/test_s09_t00_benchmark_harness.py`
- I03-owned benchmark tests/LOG/REPORT
- `output/s09/20260823_sprint_full/t00-i03-c2/**`.

Forbidden: renderer production files, T03/T04/T06 files, thresholds tuning sau
khi nhìn result, MAIN, `data/**`.

### Binary acceptance

1. PREP có thể sửa fixture/contracts/tests nhưng không phát measured verdict
   trước J1. `f1` có actual typed replacement qua hard cut; `f5` có replacement
   + occluders + expected per-frame layer order/visibility.
2. `render_and_measure_v2` phải instantiate public production router, tạo typed
   request và gọi `RendererRouter.execute()`/public equivalent. Cấm import/call
   compositor hoặc `_alpha_composite_into` để thay adapter.
3. Record phải pin selected route, adapter/backend ID, license/provenance,
   request contract SHA, J1 manifest SHA, encoded artifact SHA, canonical decoded
   frame SHA, frame count, rational fps/timebase, runtime, VRAM và metrics sample
   count. Contract reject/empty sample không phải PASS.
4. Mọi output ghi trực tiếp dưới run-specific I03 output; fixtures read-only
   trong measured phase. Không render vào `tests/fixtures/**/rendered` rồi copy.
5. Hai same-seed runs core-identical sau khi strip đúng declared nondeterministic
   fields. Adversarial source-reencode/no-replacement control phải fail mọi class
   nó áp dụng.
6. Cả 6 required risk classes phải có >=1 actual production route
   `MEASURED_RENDERED_OUTPUT`, sample >0 và pass frozen thresholds. Không đủ thì
   worker báo finding, Manager terminal BLOCKED; không tune threshold/giảm scope.
7. Benchmark tests x2 và freeze drift adversarial test. Worker chỉ submit sau khi
   J1 manifest vẫn match ở cuối run.

## 7. S09-T03-C2 — durable loop publication và evidence binding

### Exclusive write-set

- `app/workflow/s09_demo_jobs.py`
- `app/api/routes/s09_demo_loops.py` chỉ khi production failure bắt buộc
- `tests/test_s09_t03_demo_loops.py`
- `output/s09/20260823_sprint_full/t03-c2/**`
- append-only T03 LOG/REPORT.

### Binary acceptance

1. Atomic publication phải chạy trên Windows khi resolved final/temp path dài
   >=260 ký tự; không `FileNotFoundError`, không orphan `.upload`, không overwrite
   source. Không ghép segment dư làm `.../artifacts/artifacts/...` nếu managed-root
   contract không yêu cầu.
2. Concurrent/replay-safe temp naming; same content -> đúng một artifact row/file;
   kill/reconcile/replay không duplicate; cancel/failure zero residue.
3. Planner/load path fail closed với schema cũ, stale frozen SHA, missing C2
   decision, class unknown/FOQ/zero sample. Active tests tự tạo isolated synthetic
   v2 documents hoặc bind exact C2 SHA; cấm old `t00-i05` path.
4. Focused T03 tests x2, gồm explicit long-path test và T04 downstream regression.
   PREP có thể dừng `WAITING_JOIN`; final evidence binding chỉ sau I05-C2.

## 8. S09-T04-C2 — không hard-code benchmark cũ

### Exclusive write-set

- `app/api/routes/s09_demo_compare.py`
- `app/schemas/s09_demo_compare.py` khi cần
- `tests/test_s09_t04_demo_compare.py`
- `frontend/src/features/demo/**`
- `frontend/e2e/s09-t04-demo-compare.spec.ts` và config T04
- `output/s09/20260823_sprint_full/t04-c2/**`
- append-only T04 LOG/REPORT.

### Binary acceptance

1. Xóa production/frontend default hard-code tới artifact v1. Evidence path/SHA
   phải đến từ explicit validated configuration hoặc exact C2 frozen decision;
   missing/stale/FOQ phải hiện error rõ, không silent fallback.
2. Capabilities/loop list/submit cùng pin một benchmark content SHA; đổi file sau
   load phải fail closed, không TOCTOU route selection.
3. Backend T04 tests x2, TSC, S09-scoped ESLint, T04 Playwright. Final run sau
   I05-C2 và T03-C2 evidence binding.

## 9. S09-T06B-C2 — missing real-stack acceptance

### Exclusive write-set

- `frontend/e2e/s09-t06bc1-production-stack.spec.ts`
- `frontend/e2e/s09-t06bc1-global-setup.ts` và config C1/C2 khi cần
- `output/s09/20260823_sprint_full/t06b-c2/**`
- append-only T06B LOG/REPORT.

Production component/shared frontend sửa chỉ khi real-stack failure chứng minh và
Manager cấp lock riêng sau khi T04 exit; nếu finding thuộc CorrectionPanel thì
resume exact T05B owner thay vì để T06B chiếm file.

Acceptance phải snapshot tất cả demo-loop artifact IDs + content hashes trước
correction, apply/confirm correction qua actual UI/API, rồi chứng minh:

- đúng affected loop có new generation/evidence;
- mọi unaffected loop giữ nguyên artifact ID/hash/row count;
- invalid/stale correction không tạo artifact hay checkpoint;
- approval vẫn fail closed khi pending, sau confirm thì approve được;
- browser reload và actual backend process restart vẫn giữ checkpoint/hash.

Cấm QA app patch, fake router, dependency auto-commit hoặc test-only app.
Production-stack Chromium x2 bằng fresh DB/runtime, TSC/ESLint/build pass.

## 10. S09-T00-I05-C2 — measured route decision

### Exclusive write-set

- `output/s09/20260823_sprint_full/t00-i05-c2/**`
- append-only I05 LOG/REPORT.

Không sửa code/test/fixture/threshold. Verify J1 manifest và I03 result SHA trước
run. Chạy decision A/B từ frozen inputs; tạo cả human REPORT và machine-readable
`route_decisions_seed20260823.json`.

Mỗi 6 risk class phải có smallest passing route chỉ khi required metrics đều
MEASURED, sample >0 và pass. Machine decision phải pin route, input/result SHA,
threshold SHA, metric values/sample counts, escalation reason và provenance.
Yêu cầu `FAIL_OPEN_QUESTION = 0`; nếu còn một class thiếu evidence thì báo đúng và
Manager terminal BLOCKED, tuyệt đối không mở downstream. Reference media
verification và reference benchmark tiếp tục là hai state riêng.

## 11. Manager verification và final gate

Sau mọi worker exit và writers quiescent:

1. Audit attribution/write-set, pin final hashes, verify J1 manifest không drift,
   I03/I05 SHA chain khớp và 6/6 classes measured-pass với 0 FOQ.
2. Liệt kê resolved `tests/test_s09*.py`; checkpoint hiện tại phải discover đủ 22
   file (nếu count drift, log exact list/reason). Chạy toàn bộ bằng isolated temp
   DB/basetemp, `MOTIONFORGE_DATABASE_URL` unset, `PYTHONUTF8` unset: 0 fail/error.
   Chạy focused benchmark/renderer/T03/T04 gates lần hai; chạy encoding slice với
   `PYTHONUTF8=1`.
3. Chạy explicit Windows long-path publication test >=260 chars và actual
   24fps/30fps output probe, recompute decoded-frame hash độc lập.
4. Actual `app.api.app` OpenAPI no duplicates; production correction -> only
   affected loop regenerate -> approval -> browser reload -> backend restart E2E
   x2 với fresh runtime, không patch.
5. Ruff `app tests scripts`; mypy `app --no-incremental`; Alembic one head; TSC;
   S09-scoped ESLint; production build; `git diff --check`.
6. `rg` gate xác nhận không còn active production/frontend/test reference tới
   `t00-i05/measured_seed20260823`; archival docs/logs được attribution.
7. Xác minh MAIN production files, `data/**` và project media không đổi; cleanup
   đúng owned process/port/temp C2. Không kill process ngoài ownership.
8. Registry cuối ghi đủ task/session/model/state/write-set/evidence/hashes và mọi
   process exit. Manager review actual code/evidence, không chỉ chép worker report.

Nếu bất kỳ P0/P1, required class, production router/adapter, freeze chain,
long-path durability, real-stack E2E hoặc gate còn fail/unknown, terminal chính
xác:

`S09-C2 = BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`

Chỉ khi toàn bộ pass mới ghi:

`S09-C2 = TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW`

Sau đó STOP và đưa packet cho Codex review độc lập. Không APPROVED/CLOSED, không
push GitHub và không mở S10/S11/S13; cloud checkpoint chỉ sau Codex APPROVED theo
chính sách của người dùng.

