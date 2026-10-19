# MotionForge 2D - PM Execution System

Thư mục này biến PRD và Master Plan thành các phiên triển khai nhỏ, có thể kiểm soát và review độc lập.

## Source of truth

Thứ tự ưu tiên khi có xung đột:

1. `sessions/<session-id>/TASK.md` của phiên hiện tại.
2. Quyết định PM trong `sessions/<session-id>/PM_REVIEW.md`.
3. `ROADMAP.md` và `SESSION_PROTOCOL.md`.
4. `../MASTER_PLAN_V1.md`.
5. `../PRODUCT_REQUIREMENTS_V2.md`.
6. Code hiện tại và tài liệu legacy chỉ dùng làm evidence, không tự động trở thành requirement.

## Nguyên tắc vận hành

- Một session chat = một Task ID.
- Không gộp hai task vì “tiện sửa cùng lúc”.
- Hermes chỉ đọc các tài liệu được liệt kê trong `Required reading` của task.
- Hermes chỉ sửa phạm vi trong `Allowed write scope`.
- Mọi phát hiện ngoài phạm vi được ghi vào `REPORT.md`, không tự ý xử lý.
- Mỗi session phải tạo `REPORT.md` và cập nhật `LOG.md` trước khi kết thúc.
- Session sau chỉ bắt đầu khi PM đánh dấu session trước là `APPROVED` hoặc tạo task sửa lỗi riêng.
- Không dùng `REPORT.md` để thay đổi requirement. Chỉ PM được sửa `TASK.md`, roadmap hoặc quyết định scope.

## Cấu trúc

```text
docs/pm/
├── README.md
├── ROADMAP.md
├── SESSION_PROTOCOL.md
├── REVIEW_CHECKLIST.md
├── prompts/
│   └── HERMES_MASTER_PROMPT.md
├── templates/
│   ├── TASK_TEMPLATE.md
│   ├── REPORT_TEMPLATE.md
│   ├── LOG_TEMPLATE.md
│   └── PM_REVIEW_TEMPLATE.md
└── sessions/
    ├── README.md
    └── S00-T01-baseline-isolation/
        ├── START_PROMPT.md
        ├── TASK.md
        ├── REPORT.md
        ├── LOG.md
        └── PM_REVIEW.md
```

## Trạng thái task

`PLANNED -> READY -> IN_PROGRESS -> SUBMITTED -> APPROVED`

Nhánh ngoại lệ:

- `SUBMITTED -> CHANGES_REQUESTED -> IN_PROGRESS`
- `IN_PROGRESS -> BLOCKED`
- `PLANNED -> CANCELLED`

Hermes không được tự đánh dấu `APPROVED`.

## Cách mở một session mới

1. PM chọn task `READY` tiếp theo trong `ROADMAP.md`.
2. Copy bốn template vào `sessions/<Task-ID>-<slug>/`.
3. PM hoàn thiện `TASK.md`, đặc biệt là read/write scope và acceptance criteria.
4. PM tạo `START_PROMPT.md` đã điền đúng session path từ master prompt.
5. Người dùng mở chat Hermes mới và gửi nguyên văn `START_PROMPT.md`.
6. Hermes thực hiện, ghi report/log và dừng.
7. PM review bằng `REVIEW_CHECKLIST.md`, ghi `PM_REVIEW.md`.

Không yêu cầu Hermes đọc toàn bộ `docs/`. Đây là chủ ý để tránh nhiễu từ tài liệu milestone/legacy cũ.
