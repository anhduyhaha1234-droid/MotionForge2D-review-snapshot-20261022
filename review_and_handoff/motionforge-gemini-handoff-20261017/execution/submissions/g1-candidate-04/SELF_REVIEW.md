# Tự đánh giá Cổng G1 (Self-Review) — Candidate 04 (Correction G1-R1)

## 1. Khắc phục triệt để các phát hiện còn mở từ Review 03
- **G1-R04 [P1] (Propagation & Render Failure Boundary)**:
  - Khắc phục lỗi `NameError: name 'Image' is not defined`: import `Image` từ `PIL` ở đầu file `r6_propagate.py`. Kiểm tra Ruff F821 đạt 0 lỗi.
  - Sửa quy ước tên frame theo đúng chuẩn của upstream pinned `VideoSequence`: sử dụng frame index toàn cục dạng 4 chữ số toàn cục cho từng frame trong khoảng beg..end-1. Với `beg=11, end=21`, upstream tạo `0011.jpg..0020.jpg` và `r6_propagate.py` nhận diện chính xác, copy thẳng sang `merged`.
  - Bao bọc toàn bộ `run_shot()` trong khối `try...except (Exception, SystemExit) as exc`: bất kỳ lỗi nào từ preflight, staging, child run, tên sai, thừa frame, hay ảnh hỏng đều lập tức xóa stale `blend_manifest.json`, ghi failure receipt có `rc=1` vào `R6_PROPAGATE_RUNS.jsonl` và thoát nonzero (`sys.exit(1)`).
- **G1-R06 [P1] (Fake Media & Evidence Rigor)**:
  - Thay thế hoàn toàn heuristic kiểm tra ftyp/size bằng `ffprobe -v error -count_frames -show_streams -show_format -of json` qua `r6_evidence_contract.validate_evidence_video`: file video giả (`ftyp + xxxx`) lập tức bị từ chối với lỗi ffprobe container; file video hợp lệ được kiểm tra stream video và số frame.
  - Sửa `r6_matrix.py`: Q05 yêu cầu file test parse được cú pháp Python qua `ast.parse` và receipt gắn mã hash, exit_code 0, node_ids; Q08 yêu cầu video pass ffprobe; Q07 yêu cầu toàn bộ deps yêu cầu được xác thực; loại bỏ hoàn toàn các trường hợp PASS giả mạo.
- **G1-R07 [P1] (Submission Adapter & Hash Recompute)**:
  - Sửa `r6_submission_adapter.py`: kiểm tra recompute SHA-256 cho toàn bộ artifacts trong manifest; từ chối và chặn xuất bản ngay khi có same-size hash tamper (`ABCD -> WXYZ`).
  - Trong mode `final`, adapter phân loại và truyền danh sách artifacts đầy đủ vào `gate_batch_conformance`, giúp `gate_submit` nhận diện đủ 5 kind (`master`, `comparison`, `matrix`, `checkpoint`, `receipts`).
  - Sửa `stage_and_publish_matrix`: cập nhật hash của `R6_MATRIX_EVIDENCE.json.tmp` vào manifest trước khi ghi manifest và kiểm tra gate; xuất bản đồng thời và ghi commit marker `.submission_freeze.json`.
- **G1-R03 / R05 [P2] (Strict Time Contract & Cuts)**:
  - Sửa `r6_event_contract.py`: áp dụng hàm `check_strict_int` từ chối triệt để float (`43.9`), bool (`True`), string (`"43"`), float pair (`42.8/43.2`).
  - CoTracker CLI giữ nguyên `frame: 43` thành `fid: 43`, từ chối out-of-range `f=700`, trả về `None` khi không có visible pairs (không sinh NaN trong JSON).
  - Kiểm tra contact bounds (`from >= 0`, `to >= from`). `run_shot` truyền tường minh `cuts` vào `plan_runs` để chia tách run tại hard cuts.
- **G1-R08 [P2] (Controller Provenance)**:
  - Đối chiếu mã băm 3 tool sản xuất (`invocation_runtime.py`, `dispatch_long.py`, `terminal_contract.py`) khớp 100% với proof 34/34.
  - Gắn kết 51/51 harness test results và 34/34 race results; thực thi test mô phỏng 2-process OS rendezvous barrier trong sandbox chứng minh 1 winner.
- **G1-R09 [P2] (State Truth & Watchdog)**:
  - Sửa `auto_nudge_watchdog.py`: phát hiện `WAITING_CODEX_REVIEW` và bỏ qua model nudge để bảo toàn quota; phân loại lỗi mạng tạm thời (chờ 5 phút theo rules §7) vs lỗi quota/auth (dừng và báo blocker).
  - Sửa `telegram_heartbeat.py`: phân định trạng thái `WAITING_CODEX_REVIEW`, đo liveness thực mà không lấy self-touch `STATE.json` làm tiến độ.
  - Reconcile `STATE.json` trung thực: `status: WAITING_CODEX_REVIEW`, ghi rõ 8 verified / 12 closed in candidate 04, danh sách `changed_files` đầy đủ.

## 2. Kết quả kiểm thử Ground Truth
- **Toàn bộ 89/89 tests PASS** (100% OK trong 12.061s).
- Producer replay probe: **PASS 100%** (1 initial call, 0 replay call, verified-reuse).
- Ruff check F821 trên toàn bộ `r6/scripts`: **All checks passed!** (0 errors).
- Zero git mutation / zero push / zero dirty tree trên INTEGRATION.
