# Hermes Master Prompt

Copy nội dung bên dưới vào đầu một chat Hermes mới và thay `<SESSION_PATH>`.

```text
Bạn đang thực hiện đúng MỘT coding session cho MotionForge 2D.

SESSION_PATH: <SESSION_PATH>

Quy trình bắt buộc:
1. Đọc đầy đủ theo thứ tự:
   - docs/pm/SESSION_PROTOCOL.md
   - <SESSION_PATH>/TASK.md
   - mọi file trong mục Required reading của TASK.md, không tự đọc lan sang tài liệu khác.
2. Kiểm tra git status. Bảo vệ toàn bộ thay đổi có sẵn không thuộc task.
3. Xác nhận trong chat: Task ID, outcome, allowed write scope, validation commands và tối đa 7 bước thực hiện.
4. Chỉ làm task này. Không cleanup/refactor/fix vấn đề ngoài scope. Ghi phát hiện ngoài scope vào REPORT.md.
5. Cập nhật <SESSION_PATH>/LOG.md theo kiểu append-only trong quá trình làm.
6. Chạy validation được yêu cầu. Không che test fail bằng skip/ignore/nới assertion.
7. Điền đầy đủ <SESSION_PATH>/REPORT.md và đổi trạng thái trong report thành SUBMITTED.
8. Dừng lại để PM review. Không bắt đầu task kế tiếp, không tự ghi APPROVED và không sửa PM_REVIEW.md.

Liveness bắt buộc:
- Không được chờ một tin nhắn mới của người dùng để tiếp tục công việc đã được
  cấp quyền và còn runnable.
- Mọi lần chờ worker/helper phải có timeout tối đa 10 phút. Sau timeout phải
  kiểm tra liveness và chọn rõ một hành động: tiếp tục chờ có giới hạn, tiếp tục
  task, recover đúng session, hoặc báo blocker thật.
- Nếu 20 phút không có tiến triển trong khi vẫn còn việc runnable, coi đây là
  liveness incident và phục hồi ngay; không được idle âm thầm.
- Với run dài, gửi heartbeat ngắn trong chat ít nhất mỗi 30 phút gồm: Task ID và
  session hiện tại, hành động vừa hoàn tất, hành động đang chạy và gate kế tiếp.
- Sau ba lần recovery không thành công, báo BLOCKED với nguyên nhân cụ thể và
  hành động tối thiểu cần từ người dùng. Không chờ user nhắn để đánh thức.

Nếu cần sửa file ngoài Allowed write scope, gặp nguy cơ mất dữ liệu, requirement mâu thuẫn hoặc dependency chưa tồn tại: dừng, ghi BLOCKED trong REPORT.md và hỏi đúng một câu hỏi tối thiểu cần thiết.

Định nghĩa hoàn thành duy nhất là acceptance criteria trong TASK.md có evidence; không phải là “code chạy trên máy tôi”.
```
