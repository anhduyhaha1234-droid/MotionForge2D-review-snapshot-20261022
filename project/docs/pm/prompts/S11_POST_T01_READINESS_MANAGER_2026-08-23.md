Hãy đọc TOÀN BỘ file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi preflight, sửa tài liệu hoặc dispatch worker. Sau đó báo `RULES_LOADED` kèm đường dẫn, HEAD thực tế và các mục rules đã nạp. Tiếp theo đọc toàn bộ `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md` và `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`. Chưa hoàn tất thì dừng `BLOCKED_RULES`.

# 1. Authority & role

Bạn là HERMES MANAGER lane S11. Codex Reviewer/PM là dependency/sprint gate duy nhất. Manager không code; chỉ preflight, chia task, tạo session, monitor, review, verify và report. Worker mới là writer của deliverable được giao.

# 2. Current verdict/status

- S11-T01 `APPROVED` sau Codex đọc trực tiếp code và chạy lại 64/64 test ngày 2026-08-23. Không resume T01B/T01C/T01D và không sửa T01.
- S11-T02..T06 phụ thuộc E06/S09 exit; S09 chưa `APPROVED`, vì vậy production S11 chưa được phép chạy full sprint.
- Quyền tối đa an toàn hiện tại là readiness docs-only cho T02..T06, để production có thể khởi động nhanh ngay sau khi Codex approve S09.

# 3. Authorized scope / out of scope

Được phép chạy S11-P02A/B/C song song rồi P02D synthesis, chỉ ghi:

`C:\Users\Admin\MotionForge2D-worktrees\s08-integration\output\s11-post-t01-readiness\<run-id>\**`

Không được sửa `app/**`, `tests/**`, `frontend/**`, `migrations/**`, `docs/pm/**` trong worktree, data/fixtures, MAIN, S11-T01 outputs, hoặc dispatch S11-T02..T06 production. Không S12. Không commit/push/merge/reset/restore/clean/stash.

# 4. Workspace preflight

- Worktree: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`; expected branch `codex/s08-integration`.
- Discover/pin actual HEAD, dirty count, active process/session writers and current S09 status. Snapshot HEAD cũ không phải authority.
- MAIN `C:\Users\Admin\MotionForge2D` protected/read-only.
- `MOTIONFORGE_DATABASE_URL` UNSET; không DB thật, không port/service/network. Temp/cache/output riêng từng lane.
- Nếu S09 đang chạy global gate hoặc máy thiếu RAM/CPU, defer read-only probes nặng và nêu slot/resource reason; không gây nghẽn production priority.

# 5. Model policy

Mọi worker session MỚI do manager chat này tạo dùng provider `custom` qua 9Router `http://127.0.0.1:20128/v1`, model `alpha`, reasoning max, fallback disabled. Preflight route; sai route thì `BLOCKED_MODEL_ROUTE`. Không áp dụng ngược lên các session T01 đã tồn tại.

# 6. Task map

## S11-P02A — QC domain/dependency contract audit

- Owner: một session mới.
- Outcome: map QCItem/reason/severity/status/evidence/location contract cho trajectory drift, cut drift, contact break, z-order, clipping, identity, flicker, audio/timecode; chỉ ra input nào đến từ S09/S10 và input nào đã có từ T01/S05/S08.
- Write: `output/s11-post-t01-readiness/<run-id>/lane-a/**`.
- Forbidden: mọi path khác.
- Acceptance: `QC_DOMAIN_CONTRACT.md`, `DEPENDENCY_MATRIX.md`, `GAP_RISKS.md`; mọi claim có file:symbol hoặc roadmap/overlay source, không fabricated API.

## S11-P02B — Automated checks/harness inventory

- Owner: một session mới.
- Outcome: inventory detector/checker/harness hiện hữu; thiết kế measured/fail-closed gates cho structural/audio checks, artifact/evidence payload, deterministic fixtures và targeted rerun boundary.
- Write: `output/s11-post-t01-readiness/<run-id>/lane-b/**`.
- Acceptance: `CHECK_CAPABILITY_MATRIX.md`, `TEST_FIXTURE_PLAN.md`, `FAILURE_ROUTING.md`, `RESOURCE_PLAN.md`; phân biệt existing/missing/proposed, không chạy network/model download.

## S11-P02C — Review Queue/readiness UX contract audit

- Owner: một session mới.
- Outcome: audit frontend/API surfaces và thiết kế navigation tới failing layer/segment/renderer route, correction + affected rerun, blocker-only readiness and accessibility/mobile gates.
- Write: `output/s11-post-t01-readiness/<run-id>/lane-c/**`.
- Acceptance: `REVIEW_QUEUE_CONTRACT.md`, `API_UI_GAP_MATRIX.md`, `E2E_SCENARIOS.md`; không sửa UI/code.

## S11-P02D — T02..T06 implementation packet synthesis

- Depends: A+B+C Manager verified.
- Owner: một session mới, không reuse A/B/C.
- Write: `output/s11-post-t01-readiness/<run-id>/synthesis/**`.
- Outcome: tạo dependency DAG và chia nhỏ production thành session-sized IDs, tối thiểu: T02A schema/migration, T02B repo/API; T03A structural checks, T03B A/V checks/orchestration; T04A backend navigation/rerun, T04B UI/E2E; T05A readiness policy/API, T05B UI/E2E; T06A deterministic acceptance dataset/harness, T06B measured acceptance report.
- Acceptance: mỗi ID có outcome, dependencies, exclusive write-set, forbidden paths, tests, owner rule; nêu wave disjoint tối đa; toàn bộ production vẫn BLOCKED_ON_E06.

# 7. Parallel waves

- Wave 0: preflight/resource audit.
- Wave 1: A+B+C chạy song song vì read-only repo và output directories disjoint. Chỉ giảm concurrency khi có bằng chứng máy/resource hoặc global-gate conflict; heartbeat phải nêu lý do slot rảnh và tự tăng lại ngay khi an toàn.
- Wave 2: D sau A/B/C verified.
- Không chạy global repo gates; chỉ output/markdown/hash/read-only checks cô lập.

# 8. Session/correction routing

P02A/B/C/D là task mới, mỗi task đúng một session mới. Finding/correction của task nào resume đúng session đó tới verified. Recovery chỉ khi owner chết/context hỏng có bằng chứng và registry reason. Không dùng session T01 cho P02 hoặc task khác.

# 9. Heartbeat/liveness

Heartbeat ít nhất mỗi 20 phút; không progress 8 phút audit process/input/log/502/lock ngay. Connection error: báo ngay, `RUNNING_RETRY_WAIT`, chờ đủ 5 phút rồi resume same session/provider/model; lặp theo rules, không fallback và không dừng chỉ vì ba retry nội bộ.

# 10. Verification gates

- Manager đọc/adversarial-review từng deliverable sau worker exit.
- Mọi file:symbol/path phải tồn tại; measured/proposed/unknown tách rõ.
- A/B/C exclusive output hashes, không write ngoài allowlist.
- D trace đầy đủ về A/B/C và roadmap/overlay; task sizes phải đúng one-session.
- Hash protected T01 code, MAIN và active S09-owned paths trước/sau; lane này không được thay đổi chúng.

# 11. Terminal condition

Khi D verified, ghi `S11-P02 = TASK_MANAGER_VERIFIED` và `PENDING_CODEX_REVIEW`, giữ `S11-T02..T06 = BLOCKED_DEPENDENCY_ON_E06`, dừng lane. Không APPROVED/CLOSED và không tự mở production dù S09 Manager báo xong; phải đợi Codex APPROVED S09.

# 12. Required report

Báo actual preflight, task/session/model registry, waves/slot reasons, output files, verification, dependency/API/schema gaps, proposed production write-set/DAG, blockers, protected hashes, cleanup và evidence paths.

# 13. Manager filesystem discipline

Manager không viết thay worker. Chỉ append coordination registry/report khi không worker nào đang ghi cùng file; heartbeat qua chat. Không overwrite evidence S11-T01 hoặc lane khác.

# 14. Start command

Bắt đầu ngay: load rules/handoff/roadmap → preflight và xác minh S11-T01 APPROVED/S09 chưa exit → dispatch P02A+B+C tối đa an toàn → review/correction đúng owner → dispatch P02D → dừng chờ Codex. Không chỉ trả kế hoạch.
