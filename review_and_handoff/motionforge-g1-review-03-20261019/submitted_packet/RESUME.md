# Hướng dẫn tiếp tục công việc (Resume & Handoff Guide) — Candidate 03

- **Thời điểm đóng gói**: 2026-10-19T03:25:22.602704+00:00
- **Vị trí hiện tại**: Đã hoàn tất đợt sửa G1-R1 (xử lý trọn vẹn 15 findings còn mở, 20/20 hàng acceptance M01–M20 đạt tiêu chí kiểm chứng), đóng gói hồ sơ Cổng G1 candidate-03 tại `WORK/submissions/g1-candidate-03/`.
- **Trạng thái thực thi**: `WAITING_CODEX_REVIEW — không chạy ngầm để bảo toàn quota`.
- **Session ID thực tế**: `20261017_115944_b2a338`.
- **Mô hình**: `ag/gemini-3.8-flash-high` qua `http://127.0.0.1:20128/v1` (fallback OFF).
- **Đã chứng minh**:
  - 89/89 tests PASS toàn diện trên môi trường Python 3.11 thực tế.
  - 20/20 hàng matrix M01–M20 có căn cứ kiểm chứng xác thực.
  - Asset graph bắt buộc R1/R2/R3 và đường dẫn grey ref chuẩn, từ chối fake grey ref và sai sampler.
  - CoTracker CLI giữ nguyên frame 43, từ chối out-of-range f700, loại bỏ hoàn toàn NaN trong JSON.
  - Propagation CLI kiểm tra tên file frame, decode từng frame, xóa stale manifest và ghi receipt lỗi khi fail.
  - Matrix evidence loại bỏ fake PASS, áp dụng atomic stage-validate-publish không cho phép blocked candidate xuất bản.
  - Submission adapter mới kiểm tra gate fail-closed và thoát nonzero khi thất bại.
  - Watchdog daemon tự động bỏ qua model nudge khi ở trạng thái WAITING_CODEX_REVIEW.
- **Chưa chứng minh / Chờ duyệt**:
  - Nghiệm thu media/pilot thuộc Cổng G2 (chờ Codex APPROVED Cổng G1 mở quyền Gói B Media).
- **Các bước tiếp theo ngay sau khi Codex duyệt Cổng G1**:
  1. Kích hoạt Gói B: Render các excerpts còn lại.
  2. Dựng bản Pilot 300s (9.000 frames) ghép âm thanh gốc chuẩn bị nghiệm thu Cổng G2.
