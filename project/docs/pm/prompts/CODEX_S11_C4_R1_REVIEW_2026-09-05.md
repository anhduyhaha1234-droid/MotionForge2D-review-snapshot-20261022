# CODEX INDEPENDENT REVIEW — S11-C4-R1 (route-gated, HEAD e98ccd9)

Bạn là Codex Project PM/BA/Independent Code Reviewer dài hạn của MotionForge2D. Đây là session Codex mới; không kế thừa kết luận bằng trí nhớ, không coi prompt này là bằng chứng. Filesystem/repository/runtime/raw evidence là nguồn sự thật.

## 0. Authority load (bắt buộc trước mọi verdict)
Đọc TOÀN BỘ:
1. `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`
2. `C:\Users\Admin\MotionForge2D\AGENTS.md`
3. `C:\Users\Admin\MotionForge2D\frontend\AGENTS.md`
4. `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
5. `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
6. `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
7. `C:\Users\Admin\MotionForge2D\docs\pm\reviews\S11_C4_PM_REREVIEW_2026-09-05.md`
8. `C:\Users\Admin\MotionForge2D\docs\pm\prompts\S11_C4_R1_BOOTSTRAP_ATOMICITY_ROUTE_BLOCKED_2026-09-05.md`
9. `C:\Users\Admin\MotionForge2D-evidence\s11-c4\20260905-093200-R1-routegate\manager\C4_R1_EXIT_VERDICT.md`
10. Toàn bộ `raw/**`, `manager/**`, `lanes/**` dưới run-root R1 `C:\Users\Admin\MotionForge2D-evidence\s11-c4\20260905-093200-R1-routegate`; đồng thời kiểm tra evidence C4 cũ `20260905-034450` (read-only).
11. `docs/pm/sessions/S11-T03G/LOG.md`, `REPORT.md`.
12. Actual diff `5449d13..8c42a32` (R1 write-set) và `8f5af06..e98ccd9` (canonical merge), current source/tests, branch `codex/s11-integration`.
Báo `AUTHORITY_LOADED` kèm path/hash/line count rules, reviewed HEAD, evidence root.

## 1. Submission cần review (tự xác minh lại, không tin lời Manager)
- Canonical worktree: `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`, branch `codex/s11-integration`.
- Claimed HEAD: `e98ccd93066db4a2bd5a925306c7ed75bc5bfe09` (merge no-ff `b5306a3` của R1 `8c42a32` + docs `e98ccd9`), porcelain 0, local==remote.
- R1 commit: `8c42a32` (parent `5449d13`), 5 files trong allowlist C4-R1.
- Recovery owner: `20260905_043139_01a91f` (exact resume, không session 2).
- INT01 owner: `20260903_112116_35051c` (FF-only BLOCKED_MERGE divergent → no-ff authorized, zero conflict).
- Run-root R1: `C:\Users\Admin\MotionForge2D-evidence\s11-c4\20260905-093200-R1-routegate`.
- Route divergence PHẢI tự đối chiếu: prompt C4-R1 cũ pin `cmc/muse-spark-1.3-contributor` (absent 142 IDs, probe 403) = BLOCKED_MODEL_ROUTE theo chữ; user lệnh mới nhất override dùng `cmc/meta/muse-spark-1.3-contributor` (PRESENT + PROBE_OK) cho toàn bộ worker. Quyết định divergence này có chấp nhận được hay vẫn là breach.
- Manager claim `S11-C4-R1 = TASK_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REREVIEW` — đây KHÔNG phải approval.

## 2. Nội dung phải review độc lập
1. Cơ chế: ghost/rollback trong `app/workflow/qc_checks_handler.py` — còn ghost 11 entries? conflict còn partial registry? clean-process proof có durable thật (file mới `tests/test_s11_t03g_qc_check_c4r1.py` 173 dòng, subprocess isolation, không import fixture T03G)?
2. Authority matrix +3 legs: detached HEAD, multi-cycle, clean-process.
3. Evidence closure-grade: T03G 148, T05A 14, T12 dedicated x2 (roots riêng) + T06 full 12, ruff/mypy/diff-check, Alembic fresh head `f9a0b1c2d3e4`, OpenAPI 200 (274 paths/340 ops/9 QC), S10 broad 270 + S10-API 71, T01 serial 64, quiescence, local==remote.
4. Git safety: không reset-hard/clean/stash/rebase/force; merge no-ff đúng owner; write-set đúng 5 files allowlist.
5. S11 có đủ điều kiện đóng hay chưa; S12/S13 có được mở không.

## 3. Output bắt buộc
- Binary verdict: `S11-C4-R1 = APPROVED` hoặc `CHANGES_REQUESTED / NOT_APPROVED`; `S11 = ...`; S12/S13 blocked hay không.
- Liệt kê findings P1/P2 với file+line+repro cụ thể nếu CHANGES_REQUESTED.
- Luôn viết và dán NGUYÊN VĂN prompt Hermes tiếp theo ngay trong câu trả lời (không chỉ kế hoạch).
- Không sửa production/test/migration/UI/config để làm xanh. Review read-only.
