# Hướng dẫn tiếp tục công việc (Resume & Handoff Guide) — Candidate 02

- **Thời điểm đóng gói**: 2026-10-18T15:05:18.414701+00:00
- **Vị trí hiện tại**: Đã hoàn tất đợt sửa G1-R1 (đóng trọn vẹn findings R01–R09 theo 20 hàng acceptance M01–M20), đóng gói hồ sơ Cổng G1 candidate-02 tại `WORK/submissions/g1-candidate-02/`.
- **Trạng thái thực thi**: `G1_CANDIDATE_02_PACKAGED_PENDING_CODEX_REVIEW`.
- **Session ID thực tế**: `20261017_115944_b2a338`.
- **Mô hình**: `ag/gemini-3.8-flash-high` qua `http://127.0.0.1:20128/v1` (fallback OFF).
- **Đã chứng minh**:
  - 89/89 tests PASS toàn diện trên môi trường Python 3.11 thực tế.
  - 20/20 hàng matrix M01–M20 đạt tiêu chí acceptance.
  - CoTracker CLI `--help` exit 0; validator từ chối tensor lỗi, T/N=0, vis ngoài [0,1]; no-NaN JSON.
  - Propagation CLI fail-closed khi child rc!=0; stale manifest bị xóa ngay khi fail.
  - Event transitions bao phủ đủ các mốc actor/contact boundary; plan_runs cắt đứt tại hard cut.
  - Manifest lọc relative path chuẩn xác (72.500+ items), namespace NS cô lập.
- **Chưa chứng minh / Chờ duyệt**:
  - Chưa cấp duyệt media/pilot (chờ Codex APPROVED Cổng G1 mở quyền Gói B Media).
- **Các bước tiếp theo ngay sau khi Codex duyệt Cổng G1**:
  1. Kích hoạt toàn diện Gói B: Hoàn tất các excerpts còn lại.
  2. Ráp nối Pilot 300s (9.000 frames) ghép âm thanh gốc chuẩn bị nghiệm thu Cổng G2.
