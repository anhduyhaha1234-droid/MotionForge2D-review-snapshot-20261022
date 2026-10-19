# Coding Sessions

Mỗi thư mục con tương ứng đúng một Task ID và một chat Hermes.

Tên chuẩn: `<Task-ID>-<short-slug>`, ví dụ `S00-T01-baseline-isolation`.

Mỗi thư mục phải có:

- `START_PROMPT.md`: câu lệnh hoàn chỉnh để mở chat Hermes.
- `TASK.md`: contract do PM sở hữu; Hermes chỉ đọc.
- `REPORT.md`: Hermes điền khi triển khai.
- `LOG.md`: Hermes append trong suốt session.
- `PM_REVIEW.md`: chỉ PM cập nhật.

Không tái sử dụng một session folder cho task khác.
