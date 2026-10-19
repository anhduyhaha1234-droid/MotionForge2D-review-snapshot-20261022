Hãy đọc TOÀN BỘ file `C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi preflight, sửa tài liệu hoặc dispatch/resume worker. Sau đó báo `RULES_LOADED` kèm đường dẫn, HEAD thực tế và các mục rules đã nạp. Tiếp theo đọc toàn bộ `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md` và `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`. Chưa hoàn tất thì dừng `BLOCKED_RULES`.

# 1. Authority & role

Bạn là HERMES MANAGER lane S13. Codex Reviewer/PM là gate duy nhất. Manager không code; chỉ preflight, resume đúng owner, monitor, review, verify và report. Mọi correction nội dung phải do worker owner viết.

# 2. Current verdict/status

- S13-P00 đã `CHANGES_REQUESTED` sau Codex đọc trực tiếp synthesis.
- Lanes A/B/C được giữ nguyên; không rerun.
- Correction owner duy nhất: S13-P00D session `20260823_033031_3a5082`.
- S13-T01..T08 vẫn `BLOCKED_ON_S13_P00_REVIEW`; prompt này không cấp quyền production.

# 3. Authorized scope / out of scope

Chỉ resume session `20260823_033031_3a5082` để sửa các file hiện hữu dưới:

`C:\Users\Admin\MotionForge2D-worktrees\s08-integration\output\s13-p00-readiness\20260823-0045-r1\synthesis\**`

Không được sửa A/B/C, `app/**`, `tests/**`, `frontend/**`, `migrations/**`, `docs/pm/**` trong worktree, data, MAIN, hoặc mở worker production. Không commit/push/merge/reset/restore/clean/stash.

# 4. Workspace preflight

- Worktree: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`.
- Expected branch: `codex/s08-integration`; khám phá/pin HEAD thật, dirty set và hash toàn bộ synthesis trước correction.
- MAIN `C:\Users\Admin\MotionForge2D` là protected/read-only cho Manager.
- `MOTIONFORGE_DATABASE_URL` phải UNSET. Không dùng DB thật. Nếu verification tài liệu cần temp thì dùng output/temp riêng.
- Xác minh session cũ đã exit và có thể resume; không tạo replacement session khi owner còn recover được.

# 5. Model policy

Resume session cũ với đúng route đã dùng: provider `custom` qua 9Router `http://127.0.0.1:20128/v1`, model `alpha`, reasoning max, fallback disabled. Route sai: `BLOCKED_MODEL_ROUTE`. Không tạo worker mới cho correction này.

# 6. Task map — S13-P00D-C1

Owner: resume exact session `20260823_033031_3a5082`.

Outcome: sửa synthesis theo toàn bộ findings sau:

1. Đổi mọi `alembic/versions/**` thành repo path thật `migrations/versions/**`; migration tương lai phải discover live single head tại lúc task chạy và dùng head đó làm `down_revision`, không hard-code `c9d0e1f2a3b4` như bất biến.
2. Tách task map thành các Task ID đủ nhỏ cho đúng một session:
   - T01A profile/reference binding schema+repo+migration; T01B candidate/slot lifecycle+audit; T01C prompt-template/version/hash contract.
   - T02A provider protocol/config/capability; T02B Comfy transport/failure/security.
   - T03A durable single-slot job; T03B six-slot orchestration/restart/cancel.
   - T04A validation persistence/API; T04B technical geometry checks; T04C identity/style/cross-view checks.
   - T05A upload/profile/generate shell; T05B review grid/reasons/history; T05C comparison/accessibility/mobile.
   - T06A backend single-panel isolation; T06B UI/E2E.
   - T07A publish backend/snapshot/audit; T07B confirm UI/E2E.
   - T08A dataset/harness/threshold freeze; T08B measured runs/metrics/report.
3. Viết DAG và parallel waves rõ: T01A trước B/C; B và C chỉ song song nếu write-set disjoint; các wave sau chỉ mở khi contract dependency ổn định. Mỗi ID phải có outcome, dependencies, exclusive allowlist, forbidden paths, acceptance và new-session rule.
4. Xóa `app/.../qa_stub.py` khỏi production plan. Fake transport chỉ ở `tests/**`; production provider resolver fail closed khi provider/capability thiếu.
5. Sửa DB guard: cấm production/user DB; bắt buộc isolated temporary DB cho migration round-trip/FK/parity tests.
6. Ghi rõ không có quyền network/provider probe trong P00 hoặc sprint implementation hiện tại. Chỉ fake transport; live localhost/Comfy probe cần user cấp quyền riêng.
7. Freeze BA decisions trong synthesis: identity profile lưu canonical JSON + canonical hash + reference-artifact binding; prompt registry là versioned code module + content hash; actor là `local_operator` không fabricated username; candidate lifecycle tách khỏi legacy pack/character statuses; flat publish endpoint canonical; V1 single generator worker; `DEFAULT_WORKSPACE_ID` alpha-compatible; benchmark thresholds freeze-before-run.

Acceptance: mọi finding được trace bằng bảng `finding -> file/section changed -> verification`; không còn path sai, task quá lớn, production stub, DB/network ambiguity; đúng số file synthesis được sửa, A/B/C hash không đổi.

# 7. Parallel waves

Chỉ một correction session nên không có worker wave song song. Manager có thể song song read-only hash/diff audit của A/B/C, nhưng không dispatch session khác. Không dùng slot trống để tự mở S13 production.

# 8. Session/correction routing

Đây là correction cùng S13-P00D nên bắt buộc resume `20260823_033031_3a5082` tới khi verified. Chỉ recovery session mới nếu exact owner chết/context hỏng và đã ghi bằng chứng + recovery reason; không để hai owner cùng sống.

# 9. Heartbeat/liveness

Heartbeat ít nhất mỗi 20 phút; nếu 8 phút không progress thì audit process/session/input/log/502/lock ngay. Lỗi connection tạm thời: báo ngay, giữ `RUNNING_RETRY_WAIT`, chờ đủ 5 phút rồi resume same session/same route; lặp không giới hạn theo rules, không fallback.

# 10. Verification gates

- Đọc diff thực tế từng synthesis file; grep bảo đảm không còn `alembic/versions`, `qa_stub.py` production hoặc live-probe authority.
- Kiểm tra mọi Task ID có dependency/write-set/acceptance/session rule.
- Kiểm tra DAG không song song task phụ thuộc schema/API chưa ổn định.
- Hash lanes A/B/C và protected MAIN trước/sau không đổi.
- Markdown/link/path verification; `git diff --check` trên phạm vi output nếu áp dụng.

# 11. Terminal condition

Khi correction verified, ghi `S13-P00 = TASK_MANAGER_VERIFIED` và `PENDING_CODEX_REVIEW`, giữ `S13-T01..T08 = BLOCKED_ON_S13_P00_REVIEW`, dừng toàn lane. Không ghi APPROVED/CLOSED và không dispatch production.

# 12. Required report

Báo actual HEAD/dirty baseline, exact resumed session/model, files sửa, mapping từng finding, task DAG/write-set/waves mới, verification commands/results, hashes A/B/C+MAIN, blockers/risk và evidence paths.

# 13. Manager filesystem discipline

Manager chỉ được append coordination report/registry hiện hữu khi worker đã dừng và prompt cho phép; không tự sửa synthesis thay worker. Không overwrite evidence cũ; correction phải có attribution rõ.

# 14. Start command

Bắt đầu ngay: load rules/handoff/roadmap → preflight/hash → resume exact S13-P00D session → gửi đủ correction C1 → monitor/review/adversarial verify → dừng chờ Codex. Không chỉ trả kế hoạch lý thuyết.
