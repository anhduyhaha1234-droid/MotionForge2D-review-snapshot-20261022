# Tự đánh giá Cổng G1 (Self-Review) — Engineering Batch Candidate 01

## 1. Tóm tắt kết quả kỹ thuật
- Toàn bộ 4 task của Gói A (`A1`, `A2`, `A3`, `A4`) đã hoàn tất và tự kiểm tra đạt chuẩn (`SELF_VERIFIED`).
- Tổng cộng **76/76 unit & regression tests PASS** (không lỗi, không skip, thời gian chạy ~9.1s).
- Root probe v4 replay kiểm chứng độc lập producer: lần đầu gọi 1 lần, lần chạy lại gọi 0 lần (`verified-reuse`).
- 0 protected files bị lệch mã băm (toàn bộ 27 protected files từ preflight được bảo toàn 100%).

## 2. Các thành phần đã giải quyết triệt để
- **A1**: Per-actor complete provenance `r6_key_deps_v4_per_actor`, same-path same-size invalidation 10 thành phần đầu vào, kiểm soát no-visible-actor và actor bị che hoàn toàn (fewer graphs).
- **A2**: Asset producer provenance `r6_key_deps_v4_asset`, đấu nối `skip_allowed` vào `r6_keygen_asset.py`, phân biệt pixel thực tế `std < 6.0` cho black passthrough, từ chối quyền skip của legacy v3.
- **A3**: Đồng bộ hóa nhận diện event keys từ cả `f` và `frame`, không để sót event fids; tách run không nội suy qua hard cut; stage-2 child failure fail-closed; CoTracker tensor contract validation và sửa lỗi hiển thị frame b.
- **A4**: Dynamic namespace `R6_INVOCATION_DIR`; tích hợp `gate_batch_conformance` vào gate; assembler fail-closed trước encoder; mô phỏng 2-controller barrier mutex.

## 3. Tính trung thực & Giới hạn (Honesty & Limitations)
- Hồ sơ nộp G1 chỉ xin nghiệm thu phần kỹ thuật mã nguồn (Engineering Batch), **tuyệt đối không xin nghiệm thu media/chất lượng video**.
- Các tiêu chí video (Q01, Q02, Q03, Q04, Q06, Q08, Q09, Q12) được giữ nguyên FAIL/UNKNOWN cho tới khi Codex cấp quyền render GPU ở Gói B.
