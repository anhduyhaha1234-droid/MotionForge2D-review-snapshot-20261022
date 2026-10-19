# Báo cáo Sprint S01 — Nền tảng persistence

**Trạng thái:** HOÀN THÀNH / APPROVED
**Ngày nghiệm thu:** 03/08/2026
**Quality baseline:** `20260803-184034` — 7/7 PASS

## Kết quả chính

Sprint S01 hoàn thành 5/5 task, tạo nền móng lưu trữ bền vững cho MotionForge 2D:

1. Thống nhất domain contract SQLAlchemy và chính sách migration.
2. Khởi tạo SQLite engine/session cùng Alembic migration có version.
3. Quản lý artifact bằng đường dẫn an toàn, atomic write và Trash có kiểm soát.
4. Đọc/kiểm kê dữ liệu JSON cũ ở chế độ preview, không sửa nguồn.
5. Import dữ liệu cũ theo transaction: backup trước, rollback toàn bộ khi lỗi,
   chống import trùng và giữ nguyên legacy ID.

## Bằng chứng nghiệm thu

- 18 test riêng cho transactional import: PASS.
- 117 test persistence của toàn S01: PASS.
- Ruff và mypy: PASS.
- Baseline bắt buộc gồm 7 cổng Python/frontend: 7/7 PASS.
- Đã phát hiện và sửa race condition giữa bước xác minh nguồn và transaction;
  dữ liệu ghi DB hiện chỉ đọc từ backup đã xác minh.
- Không cutover runtime, không dual-write, không thay đổi dữ liệu người dùng
  trong `channels.json`.

## Có thể review gì ngay

Đây là demo kỹ thuật của nền persistence: chạy preview/import trên fixture,
kiểm tra backup manifest, dữ liệu SQLite sau khi mở lại, idempotency và rollback.
Demo giao diện người dùng chưa thuộc S01; UI shell được lên kế hoạch ở S04, còn
luồng import/analyze hoàn chỉnh ở S05.

## Bước tiếp theo

Sprint S02 gồm 5 task về durable processing: state machine cho Job/JobStep,
lưu lifecycle và idempotency key, worker ngoài HTTP request, phục hồi sau restart,
và API/integration tests cho recovery contract.
