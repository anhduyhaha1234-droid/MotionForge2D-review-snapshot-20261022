Bắt buộc đọc TOÀN BỘ file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi preflight, sửa tài liệu hoặc dispatch/resume worker. Sau đó báo `RULES_LOADED` kèm đường dẫn, HEAD thực tế và các mục rules chính đã nạp. Nếu file thiếu/không đọc được hoặc có mâu thuẫn chưa giải quyết được thì dừng `BLOCKED_RULES`.

Ngay sau khi nạp rules, đọc toàn bộ workspace instructions áp dụng, tối thiểu:

- `C:\Users\Admin\MotionForge2D\AGENTS.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\SESSION_PROTOCOL.md`
- `C:\Users\Admin\MotionForge2D\docs\pm\README.md`

Báo `WORKSPACE_INSTRUCTIONS_LOADED` và danh sách file thực sự đã đọc. Đây là
correction metadata-only; không được dùng snapshot cũ thay cho filesystem thật.

# 1. Authority, owner và trạng thái hiện tại

Bạn là Hermes Manager của lane **S13-P00D-C6**, không phải Codex Reviewer và
không phải production writer. Codex là gate duy nhất. Manager chỉ preflight,
resume đúng owner, kiểm tra metadata, ghi coordination evidence và submit lại.

- P00 C5 đã được Manager xác nhận `TASK_MANAGER_VERIFIED`.
- Trạng thái được giữ nguyên: `S13-P00 = TASK_MANAGER_VERIFIED -> PENDING_CODEX_REVIEW`.
- `PRODUCTION_S13 = NOT_OPENED`.
- Lanes A/B/C là evidence đã chấp nhận; tuyệt đối không rerun và không chỉnh sửa.
- Exact synthesis owner phải resume: `20260823_033031_3a5082`.
- Không tạo replacement session, không tạo worker mới, không mở S13-T01..T08.

Evidence hiện hành cần đối chiếu:

- Run root:
  `C:\Users\Admin\MotionForge2D-worktrees\s08-integration\output\s13-p00-readiness\20260823-0045-r1`
- Synthesis:
  `...\synthesis\READINESS_REPORT.md`, `REPORT.md`, `LOG.md`
- Manager evidence:
  `...\manager\MANAGER_LOG.md`, `C5_hash_baseline.txt`, `dispatch-d-c5.log`
- C5 dispatch log đã kết thúc `EXIT_R3=0`; nếu liveness không chứng minh được,
  dừng `BLOCKED_LIVENESS`, không tạo session thay thế.

# 2. Finding C6 phải sửa

**P2 — stale current revision label**

`synthesis/READINESS_REPORT.md:9` vẫn ghi:

`STATUS: PENDING_CODEX_REVIEW (C4 revision)`

Trong khi C5 là correction hiện hành và `REPORT.md`/`LOG.md` đã có C5 section.
Phần preamble ngay sau verdict cũng mô tả C4 như correction mới nhất. Điều này
không phải production defect, nhưng làm sai review boundary cho Codex session kế
tiếp.

## Acceptance nhị phân

1. `READINESS_REPORT.md` current verdict block ghi rõ `PENDING_CODEX_REVIEW`
   và revision hiện hành là `C6` sau correction này; không còn current prose
   gọi C4 là revision mới nhất. Lịch sử C0..C5 trong `REPORT.md`/`LOG.md` giữ
   nguyên, không rewrite.
2. Không thay đổi TASK_MAP, DEPENDENCY_DAG, WRITESET_MATRIX,
   ACCEPTANCE_GATES, OPEN_PRODUCT_DECISIONS, RISK_REGISTER, lanes A/B/C,
   production code, tests, migrations, UI, config, data hoặc channels.json.
3. Không thay đổi verdict authority: không ghi `APPROVED`, `CLOSED`, `GO`;
   không mở production S13.
4. Hash toàn bộ 17 lane files phải byte-identical với
   `manager/C5_hash_baseline.txt`; synthesis vẫn đúng 9 file hiện hữu.
5. Các static checks C5 vẫn pass: 22 task IDs/rows/nodes; direct `T01B -> T04A`;
   T08B chỉ ghi `output/s13-t08-benchmark/results/**`; zero operative live
   network authority; zero production `qa_stub`; migration rule vẫn là
   `migrations/versions/**` với live single-head discovery.

# 3. Workspace, branch và write scope

- Worktree bắt buộc:
  `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`
- Branch phải khám phá lại; quan sát hiện tại là `codex/s08-integration`.
- HEAD phải khám phá lại; quan sát hiện tại là
  `ee10e55a809c84d5cb5d4a3046a1ee78828528d0`.
- Dirty source paths thuộc lane S09/S11 phải được ghi nhận và bảo toàn; không
  reset, restore, checkout, clean, stash, merge, commit hoặc push.
- `MOTIONFORGE_DATABASE_URL` phải `UNSET`; correction này không cần DB,
  Alembic, app server, pytest, Playwright, network, provider hoặc model call.

Được phép ghi duy nhất:

1. `...\synthesis\READINESS_REPORT.md` — sửa current C4 label/preamble tối
   thiểu để thành C6, không sửa task contract.
2. `...\synthesis\LOG.md` — append `CORRECTION ROUND C6`.
3. `...\synthesis\REPORT.md` — append finding→file→verification, file ledger,
   hash results, attestation; dòng cuối phải là `STATUS: TASK_SUBMITTED`.
4. `...\manager\MANAGER_LOG.md` và dispatch evidence — append coordination
   evidence only, không sửa lịch sử.

Forbidden: mọi file khác, đặc biệt lane-a/b/c, `app/**`, `frontend/**`,
`tests/**`, `migrations/**`, `docs/pm/**` trong worktree, `data/**`,
`channels.json`, MAIN tree, worktree khác, `output/s09/**`, `output/s11-*/**`.

# 4. Model/session policy

Resume đúng session `20260823_033031_3a5082` với route cũ, không fallback:

- provider: `custom`
- API base: `http://127.0.0.1:20128/v1`
- model: `alpha`
- reasoning: max
- fallback: disabled

Nếu route không khớp, dừng `BLOCKED_MODEL_ROUTE`. Không rerun A/B/C và không
được tạo worker/session thay thế.

# 5. Liveness và retry

- Heartbeat ít nhất mỗi 20 phút khi session còn active.
- Không có progress mới sau 8 phút: audit process, session, input, log mtime,
  lock và disconnect ngay.
- Lỗi connection/502/503/504/socket/DNS tạm thời: báo ngay, giữ
  `RUNNING_RETRY_WAIT`, chờ đủ 5 phút rồi resume cùng session/cùng route; không
  fallback. Lỗi auth/config/quota thì dừng với blocker chính xác.

# 6. Verification bắt buộc trước submit

1. Đọc lại current `READINESS_REPORT.md`, C5 section của `REPORT.md`/`LOG.md`,
   `C5_hash_baseline.txt` và `dispatch-d-c5.log`.
2. Xác nhận chỉ current verdict/revision metadata của D1 thay đổi; không có
   diff trong bảy synthesis contract files còn lại.
3. Hash lại 17 lane files so với C5 baseline; hash mismatch là `BLOCKED`.
4. Kiểm tra 22 IDs/rows/nodes và các C5 invariants bằng static read-only checks.
5. Ghi HEAD/branch/dirty baseline/DB guard, files changed, exact finding,
   verification commands/results và residual risk.

# 7. Terminal condition và start command

Sau khi sửa và verify:

- ghi `S13-P00 = TASK_MANAGER_VERIFIED -> PENDING_CODEX_REVIEW`;
- ghi `PRODUCTION_S13 = NOT_OPENED`;
- dừng lane và mọi writer;
- không ghi `APPROVED`, `CLOSED`, `GO`, không dispatch production;
- report kết thúc chính xác bằng `STATUS: TASK_SUBMITTED`.

Bắt đầu ngay: load rules/instructions → preflight exact worktree/HEAD/dirty
ownership/liveness → resume `20260823_033031_3a5082` → sửa đúng metadata C6 →
static verify/hash → append report → dừng chờ Codex re-review. Không chỉ trả
kế hoạch lý thuyết.
