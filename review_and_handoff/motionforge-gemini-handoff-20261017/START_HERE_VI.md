# Giao việc cho Gemini qua 9router

Dùng agent client có quyền đọc file và chạy terminal trên máy này, cấu hình:

- Base URL: `http://127.0.0.1:20128/v1`
- Model: `ag/gemini-3.8-flash-high`
- API key: key 9router đang dùng; không dán key vào chat.

Copy đoạn sau vào chat của agent:

```text
Tiếp quản MotionForge2D theo prompt đầy đủ ở:
C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-gemini-handoff-20261017/PROMPT_GEMINI_MOTIONFORGE_VI.md

Đọc toàn bộ file đó và toàn bộ canonical rules được dẫn ở đầu file. Tôi giao bạn thực hiện toàn bộ Phase 1 theo dependency và các cổng trong prompt: tự lập task, coding, testing, self-review và sửa lỗi. Codex trong hội thoại gốc là người kiểm duyệt độc lập.

Bắt đầu bằng preflight ownership/current bytes rồi tiếp tục C02B2 từ CHECKPOINT_015; không làm lại từ đầu. Dùng ag/gemini-3.8-flash-high qua 9router, một writer, không fallback. Lịch tự động vẫn tắt. Tự hoàn thành engineering batch và nộp G1 cho Codex; chỉ sau verdict hợp lệ mới mở media, pilot và product theo G2/G3. Không dừng ở việc lập kế hoạch hoặc hỏi lại quyền đã có.

Khi cần Codex review, freeze candidate và gửi tôi đường dẫn REPORT_VI.md cùng MANIFEST.json để chuyển lại hội thoại Codex. Không tự nhận đã được duyệt.
```

Prompt đã giao đủ roadmap, initial allowlist, acceptance tests, kỹ thuật media, kỹ năng, checkpoint/quota và mẫu báo cáo. Đã cập nhật canonical rules mục0.12 để agent không bị kẹt ở model/owner hoặc quy trình microtask cũ.

Tại lúc chuẩn bị: chưa dispatch Gemini, chưa transfer owner, chưa chạy thêm code/render. C02B2 còn dở; ba gói kỹ thuật cũ approved, toàn sản phẩm chưa approved. Automation vẫn PAUSED. Đọc `HANDOFF_PREFLIGHT.json` để xem snapshot; agent phải kiểm lại process/queue/lease trước khi ghi.

Nếu client không đọc được local file, đính kèm hoặc dán toàn bộ `PROMPT_GEMINI_MOTIONFORGE_VI.md`. Một chat text không có shell/filesystem không thể tự thực thi dự án chỉ nhờ 9router.

Khi agent nộp một cổng, gửi lại Codex:

```text
Review độc lập MotionForge2D candidate của Gemini tại: <đường dẫn REPORT_VI.md và MANIFEST.json>.
Kiểm actual bytes, scope, tests và media tương ứng; không chỉ đọc summary. Trả verdict và prompt correction hoặc mở gate kế tiếp theo rules0.12.
```

Không cần bật lại lịch theo dõi. Review sẽ được thực hiện khi người dùng chuyển submission về hội thoại Codex này.
