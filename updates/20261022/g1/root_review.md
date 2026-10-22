# Review độc lập MotionForge2D — G1 candidate 16

**Verdict: `G1_APPROVED` cho đúng frozen candidate 16**, manifest SHA-256 `4df7de9ccc81dff7a82a9b9d70d90a48eae2bb17cd9ff455748b041f20a0ba82`. Phạm vi duyệt là engineering evidence contract Q05/Q07 và các suite G1; cho phép chuẩn bị Gói B Media theo §0.12 sau transport được kiểm chứng. Đây không phải nghiệm thu media, video, sản phẩm hay G2.

## Bằng chứng

- Candidate: `C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-04-20261020/submissions/g1-candidate-16`. Manifest khai 74 file, inventory trước/sau của guard lần hai đều đúng 74/74, không có file thừa hoặc `.pyc`. `SOURCE_CHANGES.json` khai đúng sáu file thay đổi với pre/post SHA-256. C11 là base; C15 giữ nguyên như incident, không dùng để duyệt.
- Guard chính thức: `C:/Users/Admin/Documents/Codex/g1c16-r2/VERIFICATION.json`, SHA-256 `ccc43a4808f10772128c490c2aa227d3708714fceaf9f275160e61acb35799a7`, `VERIFY_PASS` trên bản sao, 8 suite, 92/92 test pass, 0 fail/skip, 116 subtest pass. `GUARD_PROCESS_RECEIPT.json` lưu exact command/cwd/env, UTC start/end, stdout/stderr và **exit code 0**; trước đó r1 cũng PASS.
- `SUBTEST_EVENTS.json` là lượt bổ sung độc lập trên bản sao guard: 40 unittest từ ba suite có subtest, 116/116 sự kiện `addSubTest` PASS, ghi parent/subtest identity; không sửa candidate. Đây là evidence phụ cho khoảng trống summary trong guard JSON.
- `C:/Users/Admin/Documents/Codex/g1c16-independent-challenge/run-01/CHALLENGE_RESULTS.json` đi qua actual adapter→gate trên bản sao manifest-exact. Positive dùng pytest receipt thực và 54 v4 dependency record được `r6_cache` kiểm: `TASK_SUBMITTED`. Mười hai negative (artifact thiếu/hash sai/tamper cùng size, invocation/verifier cũ hoặc bịa, node ID thiếu, receipt PASS giả cho test fail, thiếu 1/54 dependency, đổi bytes đã tiêu thụ) đều exit 1 và không có terminal. Inventory frozen trước/sau challenge 74/74; challenge process exit 0.
- `C:/Users/Admin/Documents/Codex/g1c15-report-reconciler/c16-final/RECONCILIATION.json` ghi 0 FAIL; hai UNKNOWN của guard JSON (process exit và subtest node events) đã được hai receipt bổ sung ở trên giải quyết. Guard và challenge chỉ dùng CPU/fixture; không có GPU/render.

## Đánh giá thay đổi

Lỗi C11 là Q05/Q07 nhận số liệu do caller tự khai. C16 thực thi file test Q05 bằng pytest, lấy JUnit node IDs/exit và ràng buộc receipt với invocation, bytes test; gate chạy lại test để không tin PASS tự ghi. Q07 đòi dependency v4 cho từng shot trong plan và xác minh hash/identity qua validator hiện có. Matrix và adapter dùng cùng contract; test RED cũ chứng minh đường bypass trước patch, test mới/challenge chứng minh sau patch fail closed. Không thêm dependency hay thay video engine. Nested Q05 runner được chặn để tránh vòng gọi đệ quy.

## Ranh giới tiếp theo

Source video 22:01 đã pin tại `C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long/tasks/MF-DEMO-LONG-01/source/source_full.mp4` hiện **không tồn tại**. Pin lịch sử: 36,971,916 bytes, SHA-256 `5a175454c2c2965bac5013a53926e210a9f70a185d802d0f2e0083a6fb399fa2`. Không dùng fixture 11-byte để thay. Gói B có thể làm preflight/transport CPU, nhưng inference, render và G2 exact 300s cần khôi phục đúng source hoặc user cấp nguồn mới để làm lại source pin. MAIN, live owner_work và C15 không bị sửa trong review này.

Hai agent GPT-6 Sol Max trả lỗi usage limit trước câu trả lời cuối, nhưng artifact đã lưu và root chạy lại các công cụ trên C16. Usage API báo cửa sổ 5 giờ dùng 6%, tuần dùng 21% và `credits.hasCredits=false`; tín hiệu này không xác định chắc nguyên nhân block riêng của subagent hay chứng minh credits đã phục hồi. Không mở agent mới/fallback để né block.
