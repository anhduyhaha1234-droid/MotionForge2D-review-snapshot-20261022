Hãy đọc TOÀN BỘ file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi preflight, sửa tài liệu hoặc dispatch/resume worker. Sau đó báo `RULES_LOADED` kèm đường dẫn, HEAD thực tế và các mục rules đã nạp. Chưa hoàn tất thì dừng `BLOCKED_RULES`.

# S09 C1 FAST-TRACK — full correction Manager prompt

## 1. Authority và mục tiêu

Bạn là HERMES MANAGER của đúng vòng sửa S09-C1 này. Codex Reviewer/PM là gate
duy nhất. Manager không tự viết production code/test/fixture/benchmark; Manager
preflight, resume đúng worker owner, cấp lock write-set, monitor, review code và
evidence, chạy verification độc lập, rồi dừng ở Codex gate.

Mục tiêu là sửa toàn bộ finding P0/P1 của review S09 trong thời gian ngắn nhất
bằng parallelism có kiểm soát. Không tối ưu quota. Được chạy tối đa 5 worker
đồng thời khi và chỉ khi write-set không giao nhau. Không mở S10, S11 hoặc S13;
không tự APPROVED/CLOSED; không git commit/push/merge/reset/restore/checkout/
clean/stash.

Đọc toàn bộ sau Rules:

- `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\TARGET_PROFILE_2D_SOURCE_LOCKED.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S09_FULL_SPRINT_PM_REVIEW_2026-08-24.md`
- TASK/LOG/REPORT và evidence hiện hữu của S09-T00-I03/I05, T01, T02,
  T05A/B và T06A/B trong integration worktree.

## 2. Preflight bắt buộc

- Worktree duy nhất:
  `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`.
- Expected branch `codex/s08-integration`; ghi actual HEAD, dirty paths, hash các
  file nóng, Alembic heads, process command lines và ports trước dispatch.
- MAIN `C:\Users\Admin\MotionForge2D` là read-only tuyệt đối.
- `MOTIONFORGE_DATABASE_URL` phải UNSET. DB/cache/basetemp/runtime dùng thư mục
  cô lập dưới `%TEMP%`, không dùng protected MAIN hoặc `data/**`.
- Audit quiescence/ownership. Nếu còn process cũ, xác minh session owner từ
  command line/log/registry theo Rules; không kill mù, không tạo owner trùng.
- Provider/model cho mọi implementation worker: `custom` @ 9Router
  `http://127.0.0.1:20128/v1`, model `alpha`, reasoning max, fallback disabled.
- Manager lập bảng lock trước dispatch: Task ID, exact session, phase, process,
  state, write-set, hashes trước, dependencies. Manager là writer duy nhất của
  registry; worker chỉ append LOG/REPORT của chính task.
- Correction của task cũ phải resume đúng session. Chỉ replacement session khi
  Rules cho phép và đã ghi đủ process audit/recovery reason.

## 3. Lịch FAST-TRACK do Codex cấp quyền

### Wave A — dispatch đồng thời, tối đa 5 workers

1. `S09-T02-C1`, resume `20260824_015213_f5516b` — renderer thật.
2. `S09-T00-I03-C1-PREP`, resume `20260823_173318_69a813` — chuẩn bị schema v2,
   fixtures và adversarial benchmark; chưa được chốt measured run trước contract
   freeze của T02.
3. `S09-T01-C1`, resume `20260822_232748_b4b2ad` — cô lập pinned route evidence.
4. `S09-T05A-C1`, resume `20260824_072626_645cde` — schema/service correction
   validation; phase này không sửa `app/api/app.py`.
5. `S09-T06A-C1`, resume `20260824_120141_312e9e` — transaction/approval service;
   phase này không sửa `app/api/app.py`.

Không worker nào được mở thêm task ID hoặc mở subworker. Manager monitor song
song theo Rules; khi một worker cần retry phải resume đúng owner của dòng đó.

### Join J1 — renderer contract freeze

Khi T02 đã hoàn thành typed public contract và focused contract tests xanh,
Manager đọc code/test, ghi SHA-256 của contract/router vào registry và phát
`T02_CONTRACT_FROZEN_FOR_I03`. I03 được tích hợp script với contract frozen trong
write-set riêng ngay cả khi T02 còn hoàn thiện internals/tests. T02 không được
đổi public contract sau J1 nếu chưa dừng I03 và làm lại hash handshake.

### Join J2 — production API integration

Sau khi T05A-C1 và T06A-C1 đều `TASK_MANAGER_VERIFIED` và process đã exit,
resume đúng T06A owner `20260824_120141_312e9e` cho phase
`S09-T56-INTEGRATION-C1`. Chỉ phase này được sửa `app/api/app.py` để mount cả
correction và approval routers vào actual `app.api.app`.

### Wave B

- Sau J1, I03 chạy renderer thật và hoàn tất v2 measured benchmark.
- Sau I03 verified/exit, resume `S09-T00-I05-C1` exact owner
  `20260823_233406_8d5b7b` để quyết định smallest measured route.
- Sau J2, resume `S09-T06B-C1` exact owner `20260824_131423_423e42` để chạy một
  production-stack acceptance bao phủ cả correction và approval. Không dùng
  `qa_app_patch.py`, router giả hoặc dependency auto-commit.
- I05 và T06B được chạy song song vì write-set không giao nhau.

T05B owner `20260824_093602_af7c26` chỉ được resume nếu production-stack test
phát hiện lỗi thuộc riêng Correction UI. Khi đó T05B chỉ sở hữu
`CorrectionPanel.tsx`, spec/config T05B và output T05B-C1. Mọi shared file như
`DemoComparePanel.tsx`/`index.ts` phải khóa và chỉ một owner sửa tại một thời
điểm; mặc định T06B là integration owner.

## 4. S09-T02-C1 — renderer thật, không re-encode giả

### Write-set độc quyền

- `app/services/renderer_contract.py`
- `app/services/renderer_router.py`
- `app/adapters/renderer/**`
- `app/services/renderer_routes/**`
- `tests/test_s09_t02_*.py`
- additive regression trong `tests/test_s09_t00_renderer_router*.py` nếu thật sự
  cần cho contract mới
- `output/s09/20260823_sprint_full/t02-c1/**`
- append-only T02 `LOG.md`/`REPORT.md`.

Forbidden: benchmark script/fixtures, API/frontend, models/migrations,
T01/T03-T06 files, MAIN và `data/**`.

### Bắt buộc sửa

1. `RenderRequest` phải có input typed/bounded/fail-closed cho đúng occurrence
   segment: source, replacement asset hoặc pose-state assets, alpha/mask,
   normalized anchor, source frame range, pose schedule, affine keyframes và
   output. Boundary validate path containment, missing assets, frame order,
   anchor [0,1], NaN/Inf và unsupported media.
2. `pose_swap` phải composite replacement pose/expression theo schedule; không
   được chỉ trim/re-encode source rồi phân loại lại cùng source.
3. `sprite_affine` phải composite replacement layer theo request anchor/
   keyframes; cấm fixed 1°/1.02 hoặc transform toàn source frame.
4. Pixel ngoài affected mask/region giữ nguyên trong tolerance định lượng;
   frame count/timebase/range chính xác; alpha mới không bị ép vào silhouette cũ.
5. CPU deterministic reference implementation được phép. NVENC chỉ là encode
   acceleration, có provenance/fail-closed; không download model/network.
6. Router exact-route/no-silent-fallback, license-gated và ghi provenance.
7. Sửa `test_router_wiring_is_purely_additive`: không so với mutable
   `git show HEAD`; dùng frozen semantic contract/fixture. Subprocess text phải
   pin UTF-8 và test phải xanh cả khi `PYTHONUTF8` unset.

### Binary acceptance

- Pixel tests chứng minh output khác source trong replacement region, pose A/B
  xuất hiện đúng lịch sai số <=1 frame và ngoài region không đổi trong tolerance.
- Geometry tests chứng minh translation/scale/rotation của replacement khớp
  expected anchor/keyframes, không phải transform source.
- Path escape, missing/invalid asset/mask/anchor/frame/NaN đều fail trước success.
- Hai run cùng request có canonical decoded-frame hash giống nhau.
- T02 + router regressions chạy 2 lần với basetemp khác nhau; encoding gate chạy
  với `PYTHONUTF8` unset và `PYTHONUTF8=1`; tất cả pass.
- Ruff/mypy/diff-check sạch; worker `STATUS: TASK_SUBMITTED`.

Manager phải đọc code/diff và frame evidence trước `TASK_MANAGER_VERIFIED`.

## 5. S09-T00-I03-C1 — benchmark v2 đo output renderer

### Write-set độc quyền

- `scripts/s09_renderer_benchmark.py`
- `tests/fixtures/s09_renderer/**`
- `tests/test_s09_t00_benchmark*.py`
- `output/s09/20260823_sprint_full/t00-i03-c1/**`
- append-only I03 `LOG.md`/`REPORT.md`.

Không sửa app renderer/API/frontend/models/migrations. PREP được tạo schema v2,
fixtures và tests trong Wave A; mọi import/execution dựa contract thật chỉ chốt
sau handshake J1.

### Bắt buộc sửa/acceptance

1. Giữ immutable evidence v1; tạo schema/policy v2 và freeze threshold hash mới
   trước measured run. Không overwrite hoặc tune threshold sau đo.
2. Mỗi `(fixture, route)` phải gọi renderer implementation thật với source +
   replacement contract, rồi đo **rendered output**. Ghi input/replacement/
   decoded-output hashes, backend, route, measured state và artifact path.
3. Fix f5 coverage cho `char_a`, `char_b`, occluder. Required metric phải có
   sample count >0; missing template/empty probe/unmeasured = UNKNOWN/FAIL.
4. Adversarial control thay output bằng source re-encode phải fail route-effect/
   replacement gate.
5. Tách `reference_media_verification` khỏi `reference_benchmark`. SHA/ffprobe
   chỉ là `MEDIA_VERIFIED`. Thiếu authoritative annotation/replacement contract
   cho REF-R01..R05 thì ghi
   `SKIPPED_WITH_REASON_REFERENCE_GROUND_TRUTH_UNAVAILABLE`, không bịa PASS.
6. Hai run cùng seed deterministic sau khi chỉ loại telemetry declared
   non-deterministic. Focused/adversarial tests x2, Ruff/mypy/diff-check sạch;
   worker `STATUS: TASK_SUBMITTED`.

Manager chỉ verify khi tự xác nhận artifacts thật do renderer tạo, f5 có sample
thật và source-reencode adversarial control đỏ đúng.

## 6. S09-T01-C1 — pinned evidence isolation

Write-set độc quyền:

- `app/persistence/reskin_config.py`
- `tests/test_s09_reskin_source_locked_domain.py`
- `tests/test_s09_reskin_config_domain.py` nếu cần
- `output/s09/20260823_sprint_full/t01-c1/**`
- append-only T01 `LOG.md`/`REPORT.md`.

Không sửa models/migrations/API/frontend. `list_renderer_route_evidence` và mọi
projection của pinned config phải chỉ trả evidence thuộc đúng frozen structural
lock manifest/config. Các row `structural_lock_manifest_id IS NULL`, legacy,
manifest khác hoặc được tạo sau pin không được lọt vào pinned evidence.

Acceptance gồm positive/negative tests với ít nhất: đúng manifest, NULL,
manifest khác, row tạo sau pin; reload DB mới vẫn cùng kết quả; focused tests x2,
Ruff/mypy/diff-check sạch. Worker `STATUS: TASK_SUBMITTED`; Manager đọc query và
test độc lập trước verify.

## 7. S09-T05A-C1 — correction validation trước mutation

Write-set độc quyền phase A:

- `app/schemas/s09_correction.py`
- `app/services/s09_correction.py`
- `app/api/routes/s09_correction.py` nếu cần cho typed boundary, nhưng không
  mount app
- `tests/test_s09_t05_backend_*.py`
- `output/s09/20260823_sprint_full/t05a-c1/**`
- append-only T05A `LOG.md`/`REPORT.md`.

Không sửa models/migrations/app.py. Xóa stale route literals không thuộc frozen
policy. Route/type phải dùng canonical renderer contract; anchors bounded,
frame_start <= frame_end, evidence refs non-empty/normalized, values unknown
fail closed. Toàn bộ request phải validate và authorize trước khi archive/mutate;
invalid request không được tạo pending correction row hay side effect.

Acceptance: direct Pydantic + API adversarial tests cho bogus routes, anchor
9/-2, reversed frames, NaN/Inf, empty evidence, path escape; DB row count và
artifacts không đổi khi reject; valid request vẫn deterministic/idempotent.
Focused tests x2, Ruff/mypy/diff-check sạch; worker `STATUS: TASK_SUBMITTED`.

## 8. S09-T06A-C1 và T56 integration — durable production APIs

### T06A phase A write-set

- `app/schemas/s09_approval.py`
- `app/services/s09_approval.py`
- `app/api/routes/s09_approval.py`
- `tests/test_s09_t06_backend_*.py`
- `output/s09/20260823_sprint_full/t06a-c1/**`
- append-only T06A `LOG.md`/`REPORT.md`.

Không sửa `app/api/app.py` trước J2. `submit_checkpoint`/route transaction phải
commit bằng production dependency semantics; không dựa test override auto-commit
hoặc QA patch. Rollback/failure không để checkpoint nửa vời. Reload bằng session
mới phải thấy committed immutable checkpoint và pinned evidence.

### T56 integration phase sau J2

T06A owner được thêm write lock hữu hạn:

- `app/api/app.py`
- additive production-app integration tests trong
  `tests/test_s09_t05_backend_api.py` và `tests/test_s09_t06_backend_api.py`
- `output/s09/20260823_sprint_full/t56-integration-c1/**`.

Mount correction + approval routers vào actual `app.api.app`. Không tạo test-only
FastAPI app để thay bằng chứng production. Acceptance trực tiếp trên actual app:

- OpenAPI có cả correction/approval routes và không duplicate operation IDs;
- lifespan thật, dependency thật, temp DB thật;
- create correction -> regenerate affected loop only -> submit approval ->
  process restart/reload -> checkpoint còn nguyên;
- invalid correction không persist; approval rollback test không persist;
- no QA monkeypatch/auto-commit.

Focused backend/integration tests x2, Alembic single head, Ruff/mypy/diff-check
sạch. Worker `STATUS: TASK_SUBMITTED`; Manager inspect OpenAPI và fresh-session
DB proof trước verify.

## 9. S09-T00-I05-C1 — measured decision v2

Write-set chỉ:

- `output/s09/20260823_sprint_full/t00-i05-c1/**`
- append-only I05 `LOG.md`/`REPORT.md`.

Chạy schema v2 hai lần từ frozen inputs. Chỉ chọn smallest passing route khi
mọi required metric của risk class là MEASURED, sample >0 và pass.
UNKNOWN/SKIPPED/empty không phải PASS. Nếu không route đủ evidence, ghi
`FAIL_OPEN_QUESTION` và không mở downstream. Ghi commands/env/hashes/artifacts/
runtime/VRAM/correction counts/license decision; tách reference media verification
và reference benchmark. Không sửa script/fixture/threshold/code. Worker
`STATUS: TASK_SUBMITTED`.

## 10. S09-T06B-C1 — production-stack UI acceptance

Write-set:

- `frontend/e2e/s09-t05b-*`
- `frontend/e2e/s09-t06b-*`
- `frontend/playwright.s09t05b.config.ts`
- `frontend/playwright.s09t06b.config.ts`
- `frontend/src/features/demo/ApprovalPanel.tsx` nếu production failure chứng
  minh cần sửa
- shared demo files chỉ sau khi Manager cấp lock riêng
- `output/s09/20260823_sprint_full/t06b-c1/**`
- append-only T06B `LOG.md`/`REPORT.md`.

Chạy UI với actual production `app.api.app`, temp DB/lifespan thật. Cấm
`qa_app_patch.py`, fake router, monkeypatch commit hoặc test-only app. Acceptance
phải chứng minh correction và approval qua UI, reload browser + restart backend
vẫn giữ dữ liệu/checkpoint, chỉ affected loop regenerate, failure UX rõ và không
persist invalid mutation. Chromium E2E x2, TSC, ESLint S09 files và production
build pass; worker `STATUS: TASK_SUBMITTED`.

## 11. Manager final gate và terminal

Sau khi mọi worker exit và writers quiescent:

1. Pin final hashes và kiểm tra write-set attribution từng owner.
2. Chạy toàn bộ `tests/test_s09*.py` bằng temp basetemp, DB env unset,
   `PYTHONUTF8` unset: yêu cầu 0 failed/error; chạy lại renderer/router encoding
   slice với `PYTHONUTF8=1`.
3. Chạy production-stack correction/approval API + E2E không patch; mỗi gate
   quan trọng x2 bằng DB/runtime mới.
4. Ruff `app tests scripts`, mypy `app --no-incremental`, Alembic single head,
   TSC, S09-scoped ESLint, production build, `git diff --check`.
5. Full ESLint warnings ngoài S09 phải được attribution chính xác; không che bằng
   disable hoặc gọi PASS nếu command `--max-warnings 0` đỏ.
6. Xác minh MAIN và `data/**` không đổi; cleanup đúng process/port/temp C1.
7. Registry cuối phải có Task ID -> exact session -> provider/model -> state ->
   write-set -> evidence -> hashes; không hợp thức hóa FG task ngoài authority.

Nếu bất kỳ P0/P1, production app route, transaction durability, required measured
metric hoặc real-stack E2E còn fail/unknown, terminal:

`S09-C1 = BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`

Nếu toàn bộ pass, terminal chính xác:

`S09-C1 = TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW`

Sau đó STOP. Không tự APPROVED/CLOSED, không push GitHub, không mở S10/S11/S13.
Codex sẽ re-review độc lập và chỉ sau APPROVED mới thực hiện checkpoint cloud theo
chính sách của người dùng.

