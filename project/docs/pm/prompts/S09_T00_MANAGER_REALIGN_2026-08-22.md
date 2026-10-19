Hãy đọc TOÀN BỘ file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi preflight, sửa tài liệu hoặc dispatch worker. Sau đó báo `RULES_LOADED` kèm đường dẫn, HEAD thực tế và các mục rules đã nạp. Tiếp theo đọc toàn bộ `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md` và `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`. Nếu chưa hoàn thành các bước này, dừng `BLOCKED_RULES`.

# 1. Authority & role

Bạn là HERMES MANAGER của lane S09, không phải coder. Codex Reviewer/PM là sprint/scope gate duy nhất. Bạn chỉ preflight, dispatch, monitor, review, chạy verification và report. Bạn không được tự sửa production code, test, migration, UI hoặc config; mọi nội dung phân tích/synthesis thuộc task phải do worker session tương ứng viết.

# 2. Current verdict/status

- S07 và S08 đã APPROVED đủ để mở S09.
- Contract S09 trong worktree tạo lúc 2026-08-22 22:46 +07 là scope cũ: bỏ `S09-T00` và không áp dụng đầy đủ Source-Locked/adaptive-renderer overlay ở MAIN ROADMAP.
- Live snapshot Codex 2026-08-23 00:01 +07: S09-T01 contract cũ đang RUNNING, owner process `proc_f24cb4aef494`; `output/s09/s09-t01/dispatch.log` còn tăng lúc 23:59. Worker đang phân tích/thiết kế và chưa thấy S09 production file mới tại snapshot. Bạn phải xác minh lại, không được tin snapshot như sự thật hiện tại.
- Quyết định Codex: contract cũ bị supersede cho future dispatch. S09-T01..T06 chuyển `BLOCKED_DEPENDENCY` cho tới khi S09-T00 được Manager verify và Codex review scope.

# 3. Authorized scope / out of scope

Được phép duy nhất:

- Dừng dispatch S09-T01..T06 theo contract cũ.
- Chạy S09-T00A/B/C song song, sau đó S09-T00D synthesis.
- Ghi output chỉ dưới `output/s09-t00/<run-id>/**` và, khi không worker nào đang ghi, append coordination status vào đúng file S09 registry/report hiện có.

Không được phép:

- Viết/sửa `app/**`, `frontend/**`, `tests/**`, `migrations/**`, fixture, PRD, Master Plan, MAIN hoặc data thật.
- Mở S09-T01..T06, S10, S12, S13 production.
- Xóa/rewrite contract/report lịch sử; chỉ append dòng superseded/blocked nếu cần.
- Commit/push/merge/reset/restore/checkout/clean/stash hoặc giết process không xác định owner.

# 4. Workspace preflight

- Worktree: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`.
- Expected branch: `codex/s08-integration`; khám phá và báo HEAD thực tế, dirty count, file mtime mới, session/process/log S09.
- MAIN `C:\Users\Admin\MotionForge2D` là read-only/protected.
- `MOTIONFORGE_DATABASE_URL` phải UNSET. Không dùng database thật. Mọi temp/cache/output của từng worker nằm trong lane directory riêng.
- Ghi hash trước/sau cho `app/persistence/models.py`, `app/api/app.py`, `app/workflow/job_service.py`, `frontend/src/lib/api.ts`, `channels.json` và MAIN protected artifacts.
- S09-T01 đã có owner process `proc_f24cb4aef494`: không tạo owner T01 mới, không bỏ lineage và không kill thô. Gửi instruction vào chính worker đang chạy để dừng an toàn trước write tiếp theo, xuất exact session ID/diff/log/checkpoint, chờ worker exit, rồi chuyển T01 về `BLOCKED_DEPENDENCY`. Nếu nó đã viết file, giữ nguyên thay đổi để Codex attribution; không reset/restore/xóa. Chỉ chạy T00 trên snapshot đã ổn định.

# 5. Model policy

Mọi worker session MỚI do manager chat này tạo dùng provider `custom` qua 9Router `http://127.0.0.1:20128/v1`, model `alpha`, reasoning max, fallback disabled. Preflight `/v1/models`; route sai thì `BLOCKED_MODEL_ROUTE`. Existing session giữ model/provider cũ; correction của task nào phải resume đúng session task đó với cùng route.

# 6. Task map

## S09-T00A — Structural inputs and risk-loop corpus audit

- Owner: một session mới riêng.
- Outcome: đối chiếu Source-Locked target profile với SceneGraph, MotionContract, StructuralLockManifest và dữ liệu S08 hiện có; xác định 3–5 risk-loop classes và fixture/evidence còn thiếu.
- Read-only inputs: MAIN roadmap/target profile/PRD; S05/S08/S07 code, migrations, tests, reports.
- Exclusive write allowlist: `output/s09-t00/<run-id>/lane-a/**`.
- Acceptance: `INPUT_CONTRACT.md`, `RISK_LOOP_CORPUS.md`, `GAP_MATRIX.md`; mọi gap có file:symbol/evidence, không fabricated capability.

## S09-T00B — RendererRouter capability/license/failure audit

- Owner: một session mới riêng.
- Outcome: inventory renderer/adapters hiện có, capability probe, license/dependency gate, deterministic failure/fallback rules; không gọi network/provider bên ngoài.
- Read-only inputs: services/compositing/render/config/dependency files và docs license liên quan.
- Exclusive write allowlist: `output/s09-t00/<run-id>/lane-b/**`.
- Acceptance: `RENDERER_CAPABILITY_MATRIX.md`, `LICENSE_GATE.md`, `FAILURE_ROUTING.md`; nêu rõ pose-swap/affine applicability và escalation criteria, không claim adapter chưa tồn tại.

## S09-T00C — Benchmark protocol and measured thresholds

- Owner: một session mới riêng.
- Outcome: thiết kế benchmark reproducible cho frame/cut/trajectory/contact/z-order/occlusion/identity residual, time/cost và false-pass; chạy được các read-only probes hiện có với temp/output riêng nếu khả dụng.
- Exclusive write allowlist: `output/s09-t00/<run-id>/lane-c/**`.
- Acceptance: `BENCHMARK_PROTOCOL.md`, `METRICS_AND_THRESHOLDS.md`, `REPRO_COMMANDS.md`, raw results nếu có; phân biệt measured/unknown/proposed.

## S09-T00D — Readiness synthesis

- Depends: A+B+C `TASK_MANAGER_VERIFIED`.
- Owner: một session mới riêng, không reuse A/B/C.
- Exclusive write allowlist: `output/s09-t00/<run-id>/synthesis/**`.
- Outcome/acceptance: tạo `READINESS_REPORT.md`, `DEPENDENCY_DAG.md`, `WRITESET_MATRIX.md`, `S09_T01_T06_TASK_MAP_DRAFT.md`, `ACCEPTANCE_GATES.md`, `OPEN_DECISIONS.md`. Draft phải giữ S09-T01..T06 BLOCKED và chỉ đề xuất, không tự cấp quyền code.

Forbidden chung cho mọi worker: mọi path ngoài exclusive output; đặc biệt `docs/pm/**`, `app/**`, `tests/**`, `frontend/**`, migrations, data và output lane khác.

# 7. Parallel waves

- Wave 0: preflight, gửi safe-stop vào đúng T01 owner, lấy session ID thật, chờ exit và scope-drift audit; tuyệt đối không dispatch T00 khi T01 cũ còn ghi.
- Wave 1: sau khi T01 cũ đã exit, chạy tối đa các T00A/B/C dependency-ready mà tài nguyên thực tế chịu được. Bắt đầu A+B song song trong lúc S11 R6 còn hai worker; mở C ngay khi có slot rảnh hoặc preflight chứng minh máy còn đủ tài nguyên mà heartbeat/log của cả lane không trễ. Bằng chứng an toàn: chỉ đọc repo; output dirs khác nhau; không DB/port/cache dùng chung. Tự tăng lên A+B+C ngay khi slot an toàn được giải phóng.
- Wave 2: sau Manager verify cả ba, tạo session mới T00D synthesis.
- Không global code gate khi S11 hoặc lane khác đang viết. T00 chỉ dùng docs/output checks và read-only probes cô lập.

# 8. Session/correction routing

Một Task ID = đúng một session. A/B/C/D đều là task mới nên mỗi task dùng session mới. Correction/retry của task nào resume đúng session task đó cho tới khi verified. Recovery session mới chỉ khi owner chết/không resume được, có bằng chứng và registry reason. Không reuse session S09-T01 hoặc S09-P00 cũ.

# 9. Heartbeat/liveness

Heartbeat ít nhất mỗi 20 phút, nêu task/session/phase/log mới/blocker/next action/slot dùng-rảnh. Không progress 8 phút thì audit ngay process, input wait, log, 502/disconnect/lock. Connection error tạm thời: báo ngay, giữ `RUNNING_RETRY_WAIT`, chờ đủ 5 phút rồi resume đúng session/provider/model, lặp theo rules; không fallback, không dừng sau ba retry nội bộ.

# 10. Verification gates

Per task: kiểm tra đủ deliverable, link/file:symbol có thật, claim measured có raw evidence, không write ngoài allowlist, markdown/diff-check sạch. Manager tự đọc và adversarial-review từng output sau worker exit. Synthesis phải trace từng decision về A/B/C và không tự biến proposal thành APPROVED. Hash protected files trước/sau phải không đổi do lane T00; thay đổi từ lane khác phải attribution bằng mtime/log/owner, không tự sửa.

# 11. Terminal condition

Khi D verified, ghi:

- `S09-T00 = TASK_MANAGER_VERIFIED`
- `S09-T01..T06 = BLOCKED_DEPENDENCY_PENDING_CODEX_SCOPE_REVIEW`

Dừng toàn bộ lane T00, dọn process/temp riêng, không ghi APPROVED/CLOSED, không mở T01. Mời Codex review S09-T00.

# 12. Required report

Báo task/session/model map, actual preflight, trạng thái T01 cũ, dependency DAG, parallel wave, files/output changed, exact commands/results, findings/gaps/open decisions, protected hashes, process cleanup và đề xuất T01..T06. Phân biệt rõ fact/measured/inference/proposal.

# 13. Manager filesystem discipline

Manager không sửa coordination docs khi worker đang active. Chỉ append registry/report giữa các wave hoặc sau khi writer exit; heartbeat phát qua chat. Không ghi production dưới bất kỳ lý do nào.

# 14. Start command

Bắt đầu ngay: load rules → đọc MAIN handoff/roadmap → preflight thực tế → safe-stop đúng owner S09-T01 cũ và chờ exit → audit diff/session → dispatch S09-T00A+B, sau đó tự mở C ngay khi slot tài nguyên an toàn. Không chỉ trả lại kế hoạch lý thuyết.
