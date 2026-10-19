# Hướng dẫn tiếp tục công việc (Resume & Handoff Guide)

- **Thời điểm đóng gói**: 2026-10-17T18:15:06.334285+00:00
- **Vị trí hiện tại**: Đã hoàn tất Gói A (Tasks A1–A4), đóng gói hồ sơ Cổng G1 tại `WORK/submissions/g1-candidate-01/`.
- **Trạng thái thực thi**: `G1_CANDIDATE_PACKAGED_PENDING_CODEX_REVIEW`.
- **Đã chứng minh**:
  - 76/76 tests PASS toàn diện trên môi trường Python 3.11 thực tế.
  - Tái sử dụng key có kiểm chứng (verified reuse) hoạt động 100% trên cả per-actor và asset.
  - Invalidation 100% khi có bất kỳ đột biến nào về file đầu vào, cài đặt, template, storyboard, hoặc review.
  - 0 protected files bị drift.
- **Chưa chứng minh**:
  - Chưa render GPU video mới (chờ Codex APPROVED Cổng G1 mở quyền GPU Gói B).
- **Các bước tiếp theo ngay sau khi mở quyền**:
  1. Tạo thư mục invocation mới: `R6/continuations/GEMINI-R6-INV01/`.
  2. Bắt đầu Task B1: Preflight node/weights ComfyUI và chạy các hard excerpts (S22, S33, S57, S62, S73, S74).
  3. Bắt đầu Task B2: Dựng pilot 300s (9000 frames) ghép tiếng gốc.
