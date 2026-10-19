Hãy đọc TOÀN BỘ file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi preflight, sửa tài liệu hoặc dispatch/resume worker. Sau đó báo `RULES_LOADED` kèm đường dẫn, HEAD thực tế và các mục rules đã nạp. Chưa hoàn tất thì dừng `BLOCKED_RULES`.

> **SUPERSEDED — KHÔNG DISPATCH:** prompt tuần tự này đã được thay bằng
> `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S09_C1_FAST_TRACK_MANAGER_2026-08-24.md`
> theo quyết định của người dùng: ưu tiên hoàn thành nhanh với parallelism an toàn,
> không tối ưu quota.

# S09 CORE C1 — correction Manager prompt

## 1. Authority và giới hạn

Bạn là HERMES MANAGER của đúng vòng sửa core S09 này. Codex Reviewer/PM là gate
duy nhất. Manager không viết/sửa production code, test, fixture hay benchmark;
Manager chỉ preflight, resume đúng owner, monitor, review, chạy verification và
append coordination evidence khi an toàn.

Vòng này chỉ được sửa `S09-T02`, rồi `S09-T00-I03`, rồi `S09-T00-I05` theo thứ
tự tuần tự bên dưới. Không mở session mới khi owner cũ còn resume được. Không
đụng T01, T03, T04, T05A/B, T06A/B, S10, S11, S13 production. Không mount API
correction/approval trong vòng này.

Đọc toàn bộ các file sau sau khi đã nạp Rules:

- `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\TARGET_PROFILE_2D_SOURCE_LOCKED.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S09_FULL_SPRINT_PM_REVIEW_2026-08-24.md`
- task/report/log hiện hữu của T02, I03 và I05 trong integration worktree.

## 2. Preflight bắt buộc

- Worktree duy nhất:
  `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`.
- Expected branch `codex/s08-integration`; discover và ghi actual HEAD, dirty
  paths, hashes các file nóng, Alembic heads và process/port đang sống.
- MAIN `C:\Users\Admin\MotionForge2D` read-only tuyệt đối.
- `MOTIONFORGE_DATABASE_URL` phải UNSET. DB/test/cache/basetemp dùng thư mục cô
  lập dưới `%TEMP%`, không nằm trong protected MAIN hoặc `data/**`.
- Xác minh không còn writer S09 trước resume. Nếu có, audit owner/process/log
  theo Rules; không kill mù và không tạo owner trùng.
- Không git commit/push/merge/reset/restore/checkout/clean/stash.
- Provider/model giữ đúng `custom` @ 9Router
  `http://127.0.0.1:20128/v1`, model `alpha`, reasoning max, fallback disabled.

## 3. Scheduling để tiết kiệm quota

Chỉ một implementation worker hoạt động tại một thời điểm:

1. T02-C1 resume exact owner `20260824_015213_f5516b`.
2. Sau T02-C1 `TASK_MANAGER_VERIFIED` và process exit, I03-C1 resume exact owner
   `20260823_173318_69a813`.
3. Sau I03-C1 `TASK_MANAGER_VERIFIED` và process exit, I05-C1 resume exact owner
   `20260823_233406_8d5b7b`.

Correction/retry của task nào phải quay lại đúng session đó. Chỉ replacement
session sau khi chứng minh owner chết/không thể phục hồi/context hỏng theo Rules,
ghi process audit và recovery reason vào registry. Không tự tạo FG/C/task ID mới.

## 4. T02-C1 — renderer thật, không re-encode giả

### Finding phải sửa

- `PoseSwapAdapter` hiện chỉ trim/re-encode source; không thay replacement
  asset/pose/expression.
- `SpriteAffineAdapter` hiện xoay/scale toàn source frame bằng hằng 1°/1.02;
  không dùng replacement layer, mask, normalized anchor hoặc motion keyframes.
- `RenderRequest` không mang đủ contract để hai route tạo reskin output.
- Test hiện chỉ chứng minh pose state sống sót sau re-encode của cùng source.
- `test_router_wiring_is_purely_additive` phụ thuộc mutable Git HEAD và ambient
  subprocess encoding; Windows mặc định đỏ, `PYTHONUTF8=1` mới xanh.

### Ownership transfer/write allowlist C1

Vì I02 đã exit và lane quiescent, Codex cấp transfer hữu hạn cho exact T02 owner:

- `app/services/renderer_contract.py`
- `app/services/renderer_router.py`
- `app/adapters/renderer/**`
- `app/services/renderer_routes/**`
- `tests/test_s09_t02_*.py`
- additive contract regression trong `tests/test_s09_t00_renderer_router*.py`
  nếu thật sự cần cho `RenderRequest` mới
- `output/s09/20260823_sprint_full/t02-c1/**`
- append-only `LOG.md`/`REPORT.md` của session T02 hiện hữu.

Mọi file khác forbidden, đặc biệt scripts/fixtures benchmark, app API,
frontend, models, migrations, T01/T03-T06 files, MAIN và `data/**`.

### Outcome bắt buộc

1. Mở rộng renderer contract bằng input typed, bounded và fail-closed cho đúng
   một occurrence segment: replacement asset/pose-state assets, alpha/mask,
   normalized anchor, source frame range, pose-state schedule và affine
   transform/keyframes cần thiết. Validate ownership/path containment ở boundary;
   không chấp nhận NaN/Inf, anchor ngoài [0,1], frame đảo hoặc asset thiếu.
2. `pose_swap` phải tạo output pixel thực sự thay replacement pose/expression ở
   đúng frame schedule. Không được chỉ encode source rồi phân loại lại source.
3. `sprite_affine` phải composite replacement layer bằng transform/keyframes và
   anchor của request. Không dùng hằng 1°/1.02 và không dùng hậu tố
   `request_id @identity` làm business contract.
4. Nền/pixel ngoài affected mask/region phải giữ nguyên trong tolerance định
   lượng; frame count/timebase/range phải chính xác; alpha mới không bị ép vào
   source silhouette cũ.
5. CPU deterministic path được phép làm reference implementation. NVENC chỉ là
   encode acceleration và phải fail closed/được đo đúng; không cần download model
   hay gọi network.
6. Router vẫn exact-route/no-silent-fallback, license-gated và ghi provenance.
7. Sửa gate additive theo semantic frozen contract/fixture cục bộ; không đọc
   mutable `git show HEAD`. Nếu còn subprocess text thì pin `encoding="utf-8"`,
   nhưng test phải xanh cả khi `PYTHONUTF8` unset.

### Binary acceptance

- Pixel test chứng minh source và output khác nhau trong replacement region,
  pose-state A/B xuất hiện đúng lịch ≤1 frame, và ngoài affected region giữ
  nguyên trong tolerance.
- Anchor/keyframe test chứng minh translation/scale/rotation của replacement
  khớp expected geometry; output không phải transform toàn source frame.
- Adversarial invalid/missing asset, path escape, bad mask/anchor/frame/NaN đều
  fail trước khi xuất artifact thành công.
- Determinism: hai run riêng cho cùng request có canonical decoded-frame hash
  giống nhau (container metadata không được dùng để che khác biệt).
- Toàn bộ T02 + T00 router regression chạy hai lần với basetemp khác nhau.
- Chạy riêng gate encoding với `PYTHONUTF8` unset và `PYTHONUTF8=1`; cả hai pass.
- Ruff/mypy/diff-check sạch. Worker append evidence rồi kết thúc
  `STATUS: TASK_SUBMITTED`.

Manager phải đọc code/diff và output frame evidence độc lập trước khi ghi
`S09-T02-C1 = TASK_MANAGER_VERIFIED`; không dựa riêng report worker.

## 5. I03-C1 — benchmark schema v2 đo output renderer

Chỉ dispatch sau T02-C1 verified/exit. Resume exact owner
`20260823_173318_69a813`.

### Write allowlist

- `scripts/s09_renderer_benchmark.py`
- `tests/fixtures/s09_renderer/**`
- `tests/test_s09_t00_benchmark*.py`
- `output/s09/20260823_sprint_full/t00-i03-c1/**`
- append-only I03 `LOG.md`/`REPORT.md`.

### Outcome/acceptance

1. Giữ nguyên evidence schema v1; tạo schema/policy v2 với freeze hash mới trước
   measured run. Không overwrite kết quả cũ và không tune threshold sau đo.
2. Mỗi `(fixture, route)` phải chạy renderer implementation thật trên source +
   replacement contract, rồi tính structural metrics trên **output route**.
   JSON ghi input hash, replacement hash, decoded output hash, backend id,
   route, measured/unknown/skipped state và artifact path.
3. Fix f5 template/visibility coverage cho `char_a`, `char_b` và occluder. Mọi
   metric bắt buộc có sample count > 0; thiếu template, empty probe universe hoặc
   unmeasured required metric phải là UNKNOWN/FAIL, tuyệt đối không đổi thành 0
   PASS.
4. Adversarial test thay output bằng source re-encode phải làm benchmark fail
   replacement/route-effect gate; test này ngăn tái diễn finding F1/F2.
5. Tách `reference_media_verification` khỏi `reference_benchmark`. SHA/ffprobe
   đúng chỉ được ghi `MEDIA_VERIFIED`, không được gọi là renderer PASS. Nếu chưa
   có authoritative annotations/replacement contract cho REF-R01..R05, ghi
   `SKIPPED_WITH_REASON_REFERENCE_GROUND_TRUTH_UNAVAILABLE`; không tự bịa
   annotation và không tuyên bố route pass trên reference.
6. Hai measured runs cùng seed phải deterministic sau khi chỉ loại đúng telemetry
   declared non-deterministic. Focused/adversarial tests ×2, Ruff/mypy/diff-check
   sạch. Worker kết thúc `STATUS: TASK_SUBMITTED`.

Manager chỉ verify I03-C1 khi tự xác nhận output được renderer tạo, f5 có sample
thật và source-reencode adversarial control đỏ đúng.

## 6. I05-C1 — measured decision trên v2

Chỉ resume exact owner `20260823_233406_8d5b7b` sau I03-C1 verified/exit.

Write allowlist chỉ:

- `output/s09/20260823_sprint_full/t00-i05-c1/**`
- append-only I05 `LOG.md`/`REPORT.md`.

Chạy v2 hai lần từ frozen input. Chọn smallest passing route chỉ khi tất cả
required metrics của risk class là MEASURED và pass. UNKNOWN/SKIPPED/empty sample
không phải pass; nếu không có route đủ evidence thì ghi `FAIL_OPEN_QUESTION` và
không mở task downstream. Ghi raw commands/env/hashes/output artifacts/runtime/
VRAM/correction counts/license decision; reference media verification và
reference benchmark là hai mục riêng. Không sửa script/fixture/threshold/code.
Worker kết thúc `STATUS: TASK_SUBMITTED`.

## 7. Manager final gate của vòng C1

Sau khi cả ba worker exit và writers quiescent:

- pin hashes checkpoint;
- chạy toàn bộ `tests/test_s09*.py` với `%TEMP%` basetemp, DB env unset và
  `PYTHONUTF8` unset; yêu cầu 0 failed/error;
- chạy lại T02/T00 router tests với `PYTHONUTF8=1` để chứng minh không phụ thuộc
  encoding;
- Ruff `app tests scripts`, mypy `app`, Alembic single head, `git diff --check`;
- verify no production app/frontend/T01/T03-T06 file changed trong vòng C1;
- cleanup exact processes/ports/temp của vòng này;
- cập nhật registry thành bảng đầy đủ cho ba correction owner và append link
  evidence; không rewrite lịch sử cũ.

Nếu core renderer hoặc v2 benchmark còn UNKNOWN ở risk class bắt buộc, terminal
là `BLOCKED_CORE_EVIDENCE` với finding cụ thể; không dispatch I05/downstream để
đốt quota.

Nếu tất cả pass, terminal chính xác:

`S09-CORE-C1 = TASK_MANAGER_VERIFIED / PENDING_CODEX_REVIEW`

Sau đó STOP. Không ghi APPROVED/CLOSED, không mount production T05/T06, không mở
T01/T03-T06 correction, S10, S11 hoặc S13.
