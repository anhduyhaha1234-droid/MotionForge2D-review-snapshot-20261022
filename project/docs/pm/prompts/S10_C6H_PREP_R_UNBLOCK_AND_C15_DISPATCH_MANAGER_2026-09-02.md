Bắt buộc đọc TOÀN BỘ file
`C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md` trước mọi
preflight, registry edit, dispatch, resume hoặc source/test write. Báo
`RULES_LOADED` kèm absolute path, logical line count, SHA-256, actual
worktree/branch/HEAD/dirty state và các mục chính đã nạp. Canonical tại lúc
Codex phát hành prompt này là 246 dòng, SHA-256
`9328C8C0672EA0040D278B2A00C81C1DBD24B4C72FF87C68FDA3A357A44B61BC`.
Hash khác hoặc không đọc đủ => `BLOCKED_RULES / RULES_DRIFT`; không dispatch.

# S10-C6H — unblock PREP-R, dispatch C15, then execute to terminal

Đây là continuation bắt buộc cho **chính Manager session**
`20260902_100134_89bbc9`. Không tạo Manager session mới. Thực thi ngay, không
chỉ trả kế hoạch/ETA và không dừng sau dispatch.

Đọc toàn bộ prompt binding gốc:
`C:\Users\Admin\MotionForge2D\docs\pm\prompts\S10_C6H_TEST_AUTHORITY_REBASELINE_AND_FINAL_CLOSURE_MANAGER_2026-09-02.md`
và review mới:
`C:\Users\Admin\MotionForge2D\docs\pm\reviews\S10_C6H_PREP_R_STALL_PM_REVIEW_2026-09-02.md`.
Mọi requirement/gate của prompt binding gốc vẫn hiệu lực; prompt này chỉ giải
blocker PREP-R và siết execution.

## Codex verdict và phạm vi

`S10-C6H = AUTHORIZED_TO_DISPATCH / PREP_R_STALLED / NOT_APPROVED`

- Không có bằng chứng write mới: test SHA vẫn
  `DAD70AE304D123227F9646B501461ED7FD8E6337DADB024269075A8CE63A4591`;
  route SHA vẫn
  `6ADCC48AD3525CC91C6B5890CE98875B85BB8DA66DEE2FB86B57C6992A17B53F`.
- C15 chưa được dispatch. Heartbeat read-only không phải worker và không được
  tính là tiến độ.
- Cấm mở S11/S12/S13; cấm commit/push/merge/deploy; cấm reset/clean/stash/
  restore/checkout hoặc copy-over/redirection vào test/route.
- Không resume C14 `20260902_013803_4d5ce5` hoặc
  `20260902_102609_ee5195`.

## PREP-R resolution — dùng làm ledger, không sửa test ở Manager

Chốt retained authority đúng **57** như sau:

1. Giữ 48 unique non-C6G tests đã được Manager truy ra trực tiếp trong
   authoritative pre-destruction read pages. Persist đầy đủ 48 tên và từng
   message/page source; không chỉ ghi count.
2. Thêm đúng chín patch/contract-proven retained tests:
   - `test_minimal_submit_omits_legacy_authority_succeeds`
   - `test_client_legacy_authority_tamper_fails_closed_zero_run_job`
   - `test_v1_checkpoint_reapproval_required_zero_mutation`
   - `test_tampered_v2_checkpoint_blocked`
   - `test_cross_project_v2_blocked`
   - `test_stale_checkpoint_hash_blocked`
   - `test_unsupported_route_never_coerced`
   - `test_cancel_idempotent_repeat_route`
   - `test_c6e_lifecycle_terminal_active_contradiction_fails_closed`
3. Loại khỏi retained target test obsolete
   `test_c6e_replay_vs_retry_barrier_at_most_one_active`: patch chronology cho
   thấy add tại `145447`, remove/replace tại `145471`, absent trong toàn bộ read
   pages, và superseded bởi
   `test_c6e_replay_vs_retry_barrier_fail_closed` trong late reads `146000`,
   `146518`, `146695`.
4. Với duplicate `test_submit_distinct_on_changed_checkpoint`, giữ semantic
   contract/definition đầu tiên hiện tại; ghi definition thứ hai là stale
   reconstruction duplicate vì pre-C14 read chỉ có một.

Phép tính bắt buộc: `48 + 9 = 57 retained`; `57 + 5 C6G = 62 unique collected`.
Không được suy diễn rằng file hiện tại là byte-exact authority.

## Action sequence — không thêm vòng PM

1. Recheck process/session/writer inventory và hai SHA trên. Nếu SHA drift hoặc
   có writer khác, stop `BLOCKED_CONCURRENT_WRITER_OR_DRIFT`.
2. Ngay trong continuation này, persist ít nhất:
   - `output/s10/c6h/manager/prep/AUTHORITY_SOURCE_LEDGER.md`
   - `output/s10/c6h/manager/prep/AUTHORITY_SOURCE_LEDGER.json`
   - `output/s10/c6h/manager/prep/RETAINED_57_MATRIX.md`
   - `output/s10/c6h/manager/prep/RETAINED_57_MATRIX.json`
   - immutable/hash/write-set/session guard evidence required by binding prompt.
3. Matrix phải có 57/57 rows cụ thể với source, setup, action, expected outcome
   và durable-state invariant. Năm C6G rows là additive, không lẫn vào 57.
4. Manager chạy R-GATE read-only. Nếu ledger/matrix không persist và self-check
   được ngay continuation này, dừng terminal
   `BLOCKED_REBASELINE_SPEC / NOT_APPROVED`; cấm trả ETA mới.
5. Khi R-GATE pass, probe exact worker selector `comboBAI`, provider `custom`,
   reasoning `max`, fallback **OFF**, TTFB 900. Mismatch =>
   `BLOCKED_MODEL_ROUTE`.
6. Tạo đúng một fresh compact worker session cho Task ID `S10-T01C-C15`; ghi
   returned session ID vào registry trước write đầu tiên. Không reuse lineage cũ.
7. Worker C15 là writer duy nhất. C15-A chỉ dùng bounded `apply_patch` để:
   - bỏ stale duplicate và obsolete test theo disposition trên;
   - phục hồi/align helper definitions, gồm unresolved `_C10BoomService`;
   - bảo toàn 57 retained contracts và thêm đúng 5 C6G, đạt 62 unique nodes;
   - không rewrite/copy-over toàn file và không sửa route trong authority phase.
8. Manager độc lập chạy structural audit, collection và authority gate. Chỉ khi
   C15-A đạt R-GATE mới unlock route cho C15-B.
9. C15-B thực thi toàn bộ C6G mechanism, locked 14-row matrix và exit gates theo
   binding prompt. Dùng một normal C15-A -> C15-B continuation và tối đa một
   combined correction continuation; không tạo chuỗi worker mới.
10. Manager tiếp tục đến một terminal thật:
    - success:
      `S10-C6H = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`; hoặc
    - blocked terminal có evidence chính xác.
    Không tự ghi `APPROVED/CLOSED` và không dừng ở “worker dispatched”.

Heartbeat/watchdog chỉ được read-only, không debug gateway/cron trong critical
path và không được dùng thay bằng chứng worker. Báo tiến độ theo artifact/hash/
command exit/session ID, không báo phần trăm hoặc ETA không gắn evidence.
