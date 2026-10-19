# Hướng dẫn tiếp tục công việc (Resume & Handoff Guide) — Candidate 04

- **Thời điểm đóng gói**: 2026-10-19T12:18:09.475025+00:00
- **Vị trí hiện tại**: Đã hoàn tất đợt sửa G1-R1 Candidate 04 (khắc phục dứt điểm NameError Image, frame naming upstream VideoSequence, video ffprobe validation, hash recompute trong submission adapter, strict int event contract, failure boundaries), đóng gói hồ sơ Cổng G1 candidate-04 tại `WORK/submissions/g1-candidate-04/`.
- **Trạng thái thực thi**: `WAITING_CODEX_REVIEW — không chạy ngầm để bảo toàn quota`.
- **Session ID thực tế**: `20261017_115944_b2a338`.
- **Mô hình**: `ag/gemini-3.8-flash-high` qua `http://127.0.0.1:20128/v1` (fallback OFF).
- **Đã chứng minh**:
  - 89/89 tests PASS toàn diện trên môi trường Python 3.11 thực tế (8 verified bởi root + 12 closed trong candidate 04).
  - Ruff F821 clean 100% trên toàn bộ r6/scripts.
  - Video ffprobe validation từ chối video giả (ftyp + xxxx), chấp nhận video hợp lệ.
  - Submission adapter recompute SHA-256 từ chối same-size hash tamper, hỗ trợ final mode với 5 artifact kinds.
  - Watchdog daemon tự động bỏ qua model nudge khi ở trạng thái WAITING_CODEX_REVIEW, phân loại lỗi mạng (chờ 5m) vs quota/auth.
- **Chưa chứng minh / Chờ duyệt**:
  - Nghiệm thu media/pilot thuộc Cổng G2 (chờ Codex APPROVED Cổng G1 mở quyền Gói B Media).
- **Các bước tiếp theo ngay sau khi Codex duyệt Cổng G1**:
  1. Kích hoạt Gói B: Render các hard excerpts (S22, S31, S33, S57, S61, S62, S63, S73, S74).
  2. Dựng bản Pilot 300s (9.000 frames) ghép âm thanh gốc chuẩn bị nghiệm thu Cổng G2.
