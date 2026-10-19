# Start Prompt for Hermes - S00-T01

Gửi nguyên văn phần trong code block vào một chat Hermes mới:

```text
Bạn đang thực hiện đúng MỘT coding session cho MotionForge 2D.

SESSION_PATH: docs/pm/sessions/S00-T01-baseline-isolation

Quy trình bắt buộc:
1. Đọc đầy đủ theo thứ tự:
   - docs/pm/SESSION_PROTOCOL.md
   - docs/pm/sessions/S00-T01-baseline-isolation/TASK.md
   - mọi file trong mục Required reading của TASK.md, không tự đọc lan sang tài liệu khác.
2. Kiểm tra git status. Bảo vệ toàn bộ thay đổi có sẵn không thuộc task, đặc biệt các user changes đã được TASK.md cảnh báo.
3. Xác nhận trong chat: Task ID, outcome, allowed write scope, validation commands và tối đa 7 bước thực hiện.
4. Chỉ làm S00-T01. Không cleanup/refactor/fix vấn đề ngoài scope. Ghi phát hiện ngoài scope vào REPORT.md.
5. Cập nhật docs/pm/sessions/S00-T01-baseline-isolation/LOG.md theo kiểu append-only trong quá trình làm.
6. Chạy toàn bộ validation trong TASK.md. Không che test fail bằng skip/ignore/nới assertion.
7. Điền đầy đủ docs/pm/sessions/S00-T01-baseline-isolation/REPORT.md và đổi trạng thái trong report thành SUBMITTED.
8. Dừng lại để PM review. Không bắt đầu S00-T02, không tự ghi APPROVED và không sửa PM_REVIEW.md.

Nếu cần sửa file ngoài Allowed write scope, đụng vào channels.json/dữ liệu nhân vật thật, gặp nguy cơ mất dữ liệu, requirement mâu thuẫn hoặc dependency chưa tồn tại: dừng, ghi BLOCKED trong REPORT.md và hỏi đúng một câu hỏi tối thiểu cần thiết.

Định nghĩa hoàn thành duy nhất là AC1-AC6 trong TASK.md có evidence; không phải là “code chạy trên máy tôi”.
```
