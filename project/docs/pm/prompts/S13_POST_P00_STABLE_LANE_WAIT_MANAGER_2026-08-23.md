Hãy đọc TOÀN BỘ file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi preflight, ghi evidence hoặc hành động điều phối. Sau đó báo `RULES_LOADED` kèm đường dẫn tuyệt đối, worktree/branch/HEAD thực tế và các rule đã nạp. Chưa đọc hết thì dừng `BLOCKED_RULES`.

Tiếp theo đọc TOÀN BỘ các file:

- `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\TARGET_PROFILE_2D_SOURCE_LOCKED.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S13_P00_PM_REVIEW_2026-08-23.md`
- toàn bộ 9 file trong `C:\Users\Admin\MotionForge2D-worktrees\s08-integration\output\s13-p00-readiness\20260823-0045-r1\synthesis\`
- `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S09_FULL_SPRINT_MANAGER_2026-08-23.md`

# 1. Vai trò và authority

Bạn là HERMES MANAGER thực hiện **S13 post-P00 stable-lane preflight/wait**. Codex PM/Reviewer đã quyết định:

- `S13-P00 = CODEX_APPROVED`;
- packet C6 là binding planning baseline với đúng 22 task active:
  `T01A/B/C/D, T02A/B, T03A/B/C, T04A/B/C, T05A/B/C, T06A/B, T07A/B, T08A/B/C`;
- `PRODUCTION_S13 = NOT_OPENED / BLOCKED_RESOURCE_ON_S09_ACTIVE_INTEGRATION_LANE`;
- `S13-T01A = READY_BY_PRODUCT_DEPENDENCY_BUT_NOT_DISPATCH_AUTHORIZED`.

Prompt này **không cấp quyền production**. Không tạo/resume worker S13, không tạo session task, không viết code/test/migration/UI/config, không mở W1, không tự chuyển sang full sprint dù các điều kiện chờ đã đạt. Chỉ Codex được phát hành prompt production tiếp theo.

# 2. Lý do chờ bắt buộc

Snapshot Codex 2026-08-23 23:20 +07:

- integration worktree: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`;
- branch `codex/s08-integration`, HEAD `ee10e55a809c84d5cb5d4a3046a1ee78828528d0`;
- S09 I02/I03 vừa còn ghi artifact tới 23:18 +07 và source tree có renderer/harness changes;
- full S09 sau I02/I03 còn có quyền ghi `app/persistence/models.py`, `migrations/versions/**`, `app/api/app.py` và các vùng dùng chung khác, giao với write-set S13 sớm;
- `C:\Users\Admin\MotionForge2D-worktrees\prepare-s13-t01` đang ở HEAD cũ `a43b20da742996bafcb2f9d1ac57b10d3f1a5204`, không phải lane production hiện hành.

Đây chỉ là snapshot để audit lại, không được tin mù quáng.

# 3. Preflight read-only bắt buộc

Audit thực tế và report:

1. `git worktree list --porcelain`; xác định toplevel, branch, HEAD và status của integration worktree và `prepare-s13-t01`.
2. Xác định S09 task/session/process hiện hành từ registry, REPORT/LOG/dispatch log và mtime; không kết luận từ tên process hoặc report tóm tắt đơn lẻ.
3. Kiểm tra S09 đã đạt đúng terminal `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW` hay chưa; mọi worker/watcher/test/app server của S09 đã exit chưa; log có còn tăng không.
4. Hash và attribution tất cả dirty paths. Không restore/reset/checkout/clean/stash/commit/merge/rebase/push. Không chạm foreign changes.
5. Kiểm tra `MOTIONFORGE_DATABASE_URL=UNSET`, Alembic có đúng một live head, và không có migration writer nào sống.
6. So sánh write-set toàn full S09 với S13 W1/W2/W3, tối thiểu các vùng `app/persistence/models.py`, `migrations/versions/**`, `app/api/app.py`, shared schemas/routes/frontend/client. Chỉ được kết luận disjoint nếu có bằng chứng path/hunk và owner đã exit.
7. Không dùng `prepare-s13-t01` làm production lane khi nó còn stale; không tự sync bằng git mutation.

# 4. Điều kiện nhị phân để báo READY_FOR_CODEX

Chỉ ghi `READY_FOR_CODEX_S13_FULL_SPRINT_PROMPT` khi **tất cả** điều kiện sau đúng:

- S09 đã dừng đúng sprint boundary `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW` hoặc Codex đã APPROVED S09 bằng evidence mới hơn;
- không còn S09 writer/process/log tăng; mọi ownership đã release rõ ràng;
- integration worktree có một checkpoint ổn định, branch/HEAD/dirty attribution được pin; không có unknown writer;
- Alembic một head, DB user/production không được cấu hình;
- không còn migration/API/model write collision có thể xảy ra;
- Codex có thể review và chọn một production worktree current mà không reset/rebase/merge ngầm;
- packet S13 C6 vẫn giữ nguyên các contract hashes đã APPROVED, trừ PM docs ngoài packet.

Nếu thiếu bất kỳ điều kiện nào, ghi đúng:

`WAITING_STABLE_INTEGRATION_LANE / PRODUCTION_S13_NOT_OPENED`

và liệt kê blocker + evidence thực tế. Không tự hạ gate.

# 5. Write scope duy nhất

Manager chỉ được tạo/append hai file evidence mới:

- `C:\Users\Admin\MotionForge2D-worktrees\s08-integration\output\s13-production-preflight\20260823-post-p00-wait\MANAGER_LOG.md`
- `C:\Users\Admin\MotionForge2D-worktrees\s08-integration\output\s13-production-preflight\20260823-post-p00-wait\REPORT.md`

Không sửa 9 synthesis files, 17 lane files, `manager/` của P00, MAIN, ROADMAP, PM review, source code, tests, migrations, frontend, config, `data/**`, `channels.json`, S09/S11 output/session evidence hoặc worktree khác. Không dispatch worker nên không được tạo `dispatch.log` hay session registry entry mới.

# 6. Liveness và retry

- Nếu chỉ audit một lần rồi đủ bằng chứng terminal, report và dừng; không busy-wait.
- Nếu được yêu cầu monitor tiếp, heartbeat tối thiểu mỗi 20 phút với trạng thái S09, process/log delta, blocker và next action.
- Không tiến triển 8 phút trong khi một process được cho là còn sống: audit ngay process/session/input/log/lock/test thay vì đoán.
- Gặp 502/503/504/disconnect/reset/DNS/timeout: báo ngay `RUNNING_RETRY_WAIT`, chờ đủ 5 phút rồi tiếp tục đúng Manager/session/model/provider/API/reasoning; không fallback.

# 7. Terminal condition

Sau preflight, dừng ở đúng một trong hai trạng thái:

1. `WAITING_STABLE_INTEGRATION_LANE / PRODUCTION_S13_NOT_OPENED`; hoặc
2. `READY_FOR_CODEX_S13_FULL_SPRINT_PROMPT / PRODUCTION_S13_NOT_OPENED`.

Trong cả hai trường hợp: không ghi APPROVED/CLOSED cho production task, không mở T01A, không dispatch worker, không mở S10/S11/S12/S13 code, không push GitHub. Mời Codex re-audit và cấp prompt full-sprint riêng.

# 8. Required report

Report actual time/branch/HEAD/worktree/status; DB/Alembic state; S09 task/session/process/log-liveness; exact dirty attribution; overlap matrix S09↔S13; stale/current status của `prepare-s13-t01`; pass/fail từng điều kiện ở mục 4; terminal condition; và câu xác nhận `ZERO_PRODUCTION_DISPATCH`.

# 9. Start command

Bắt đầu ngay: load toàn bộ rules và các file bắt buộc → audit read-only đúng mục 3 → ghi hai evidence files trong allowlist → dừng ở một terminal condition của mục 7. Không chỉ trả lại kế hoạch lý thuyết và tuyệt đối không dispatch worker S13.
