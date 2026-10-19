# Tự đánh giá Cổng G1 (Self-Review) — Candidate 03 (Correction G1-R1)

## 1. Đóng trọn vẹn 15 findings còn mở (20/20 Matrix Rows M01–M20)
- **G1-R01 [P1] (Asset Provenance & Graph Wiring)**:
  - Bắt buộc `consumed["grey_ref"]` phải có mặt, đúng role và khớp hash trong `verify_complete_asset_deps`.
  - `_verify_asset_graph` yêu cầu bắt buộc các node `R1_LOAD`, `R2_LOAD`, `R3_LOAD` phải tồn tại trong graph (từ chối thiếu R1) và trỏ đúng canonical path `identity5m_20261008/r6/_grey_64.png` (từ chối `wrong_invocation/fake_grey.png`).
  - `KEY_LOAD` bắt buộc phải trỏ đúng `identity5m_20261008/r6/work/<staged_source.name>`.
- **G1-R02 [P1] (CoTracker CLI Argparse Crash)**: Đã đóng từ candidate 02 (subprocess `--help` exit 0).
- **G1-R03 / R05 [P1/P2] (CoTracker Events, Transitions & Timing)**:
  - Xây dựng `r6_event_contract.py`: thống nhất duy nhất một parser thời gian cho cả 0-based `f` và 1-based `frame`.
  - CoTracker CLI giữ nguyên `frame: 43` thành `fid: 43` (không bị mặc định thành 2).
  - Out-of-range events (`f: 700` trong clip 50 frames) bị từ chối dứt khoát với ValueError.
  - Window drift tính trên `both[window].any()`: trả về `None` khi không có visible pairs, loại bỏ hoàn toàn `NaN` trong JSON.
  - Contact bounds: từ chối contact có `from < 0` hoặc `to > n`.
  - Cut caller: `run_shot` truyền tường minh `cuts=cuts` vào `plan_runs` để phân tách run tại hard cuts.
- **G1-R04 [P1] (Propagation Child Errors & Manifest Invalidation)**:
  - Kiểm tra số lượng frame chính xác, tên file chuẩn `0001.jpg..expect.jpg` cho `i in 1..expect`, từ chối tên sai (`9001.jpg`) hoặc frame thừa (`0000.jpg`).
  - Kiểm tra PIL decode cho từng frame trong run con và toàn bộ merge frames.
  - Xử lý lỗi toàn diện: khi có bất kỳ sự cố nào (child rc!=0, partial, tên sai, thừa, corrupt decode), `blend_manifest.json` bị xóa ngay lập tức, ghi receipt thất bại có `rc: 1` vào `R6_PROPAGATE_RUNS.jsonl`, và `main()` thoát với mã lỗi nonzero (`sys.exit(1)`).
- **G1-R06 / R07 [P1] (Matrix Rigor, Batch Gate Enforcement & Atomic Publication)**:
  - Xây dựng `r6_evidence_contract.py`: Q01 yêu cầu ảnh decode được, Q05 yêu cầu receipt với `all_passed: True` (không fallback PASS mù), Q07 yêu cầu v4 deps vượt qua `CA.verify_complete_deps`, Q08 yêu cầu video MP4 decode được.
  - `gate_batch_conformance` từ chối mode lạ (`GateBlock`), yêu cầu supporting proof cho Q05/Q07 trong mode engineering, và yêu cầu đầy đủ artifacts trong mode final.
  - Atomic stage-validate-publish protocol: nếu gate thất bại, file `.tmp` bị hủy và `GateBlock` được ném ra, candidate bị chặn tuyệt đối không thể xuất bản manifest/matrix.
  - Xây dựng `r6_submission_adapter.py`: kiểm tra toàn bộ gate và artifacts, thoát nonzero (exit 1) khi có lỗi và không bao giờ ghi `TASK_SUBMITTED` trái phép.
  - `build_manifest` lọc relative path chuẩn xác, loại trừ internal `work/`, bảo toàn file dưới ancestor `Codex/work`, và ghi vào invocation namespace.
- **G1-R08 [P2] (Controller Mutex Race Barrier)**:
  - Đối chiếu mã băm 3 tool sản xuất (`invocation_runtime.py`, `dispatch_long.py`, `terminal_contract.py`) khớp 100% với proof 34/34.
  - Khảo sát kết quả 34/34 race cases và 51/51 harness test cases; thực thi test mô phỏng 2-process OS barrier chứng minh 1 winner / 1 loser.
- **G1-R09 [P2] (Candidate Identity, State Truth & Watchdog)**:
  - Snapshot toàn bộ 12 support dependencies vào candidate 03 để phục vụ tái lập độc lập.
  - `auto_nudge_watchdog.py` được cấu hình bỏ qua model nudge khi ở trạng thái `WAITING_CODEX_REVIEW` để bảo toàn quota.
  - `telegram_heartbeat.py` phân định rõ trạng thái `WAITING_CODEX_REVIEW` và không lấy self-touch `STATE.json` làm tiến độ code.
  - Reconcile `STATE.json` trung thực: `changed_files` đầy đủ, không overclaim.

## 2. Kết quả kiểm thử Ground Truth
- **Toàn bộ 89/89 tests PASS** (100% OK trong 9.816s).
- Producer replay probe: **PASS 100%** (1 initial call, 0 replay call, verified-reuse).
- Zero git mutation / zero push / zero dirty tree trên INTEGRATION.
