# Tự đánh giá Cổng G1 (Self-Review) — Candidate 02 (Correction G1-R1)

## 1. Đóng trọn vẹn 7 Findings P1 và 2 Findings P2
- **G1-R01 [P1] (Asset Provenance & Sampler Mismatch)**:
  - Bổ sung yêu cầu bắt buộc: `consumed["grey_ref"]` phải có mặt, đúng role, và khớp hash trong `verify_complete_asset_deps` khi ở chế độ `zero_shot_asset_restyle`.
  - Bổ sung kiểm tra nghiêm ngặt `inp("SAMPLER", "sampler_name") == recipe["sampler"]`: từ chối mọi trường hợp graph sampler là `heun` khi recipe là `euler`.
  - Bổ sung kiểm tra references R1_LOAD và R2_LOAD trỏ đúng grey ref.
- **G1-R02 [P1] (CoTracker CLI Argparse Crash)**:
  - Bổ sung `import argparse` vào đầu `r6_cotracker.py`.
  - Subprocess `r6_cotracker.py --help` đã được kiểm chứng trả về `exit 0` kèm usage đầy đủ.
- **G1-R03 [P1] (Tracker Validator Empty / Non-finite Tensors & Window Drift)**:
  - `validate_cotracker_tensors` từ chối dứt khoát `T <= 0`, `N <= 0`, mảng rỗng, tracks NaN/Inf, vis NaN/Inf, và vis ngoài khoảng binary / `[0, 1]` (chặn triệt để visibility = 9.0).
  - Viết lại cách tính window drift bằng hàm an toàn: chỉ tính trên các frame có cả 2 bên hiển thị trong window (`both[window].any()`); khi không có cặp nào, trả về `None`, loại bỏ hoàn toàn `NaN` trong file JSON.
- **G1-R04 [P1] (Propagation CLI Child Fail-Closed)**:
  - Sửa `main()` trong `r6_propagate.py` để thoát với mã lỗi nonzero (`sys.exit(1)`) ngay khi có bất kỳ shot nào gặp sự cố.
  - Sửa `run_shot()` để xóa sạch `blend_manifest.json` cũ khi child run `rc != 0` hoặc partial frames, đồng thời ghi nhận bản ghi thất bại bền vững vào `R6_PROPAGATE_RUNS.jsonl`.
- **G1-R05 [P1] (Canonical Event Transitions)**:
  - Thống nhất hàm `event_fids_for` bao phủ toàn bộ các mốc chuyển trạng thái:
    - Entry, exit, occlusion, reappear của actor (`w["from"] > 1` và `w["to"] < n`).
    - Bắt đầu và kết thúc của contact (`from + 1` và `to`).
    - Sự kiện `f + 1` hoặc `frame`, từ chối mâu thuẫn f vs frame và giá trị ngoài phạm vi `[1, n]`.
  - Đồng bộ hóa logic này vào `r6_ledger.py`, `r6_gate.py`, và `r6_propagate.py`.
- **G1-R06 [P1] (Q-Matrix Evidentiary Rigor & Batch Gate Enforcement)**:
  - Sửa `r6_matrix.py`: mỗi verdict PASS bắt buộc phải parse file evidence thật, kiểm tra `st_size > 0`, kiểm tra JSON hợp lệ và verdict PASS trong nội dung; không còn tình trạng cấp PASS từ file 0-byte hoặc string rỗng.
  - `gate_batch_conformance` từ chối các mode lạ (như `"finla"`) bằng `GateBlock("UNKNOWN_BATCH_MODE")`; ở mode `"final"` bắt buộc phải gọi `gate_submit(record)` kiểm tra toàn bộ artifacts.
  - Nối `gate_batch_conformance` vào caller thực tế (`main()` trong `r6_matrix.py` và `gate_submit()` trong `r6_gate.py`).
- **G1-R07 [P1] (Manifest Relative Filtering & Namespace Isolation)**:
  - Sửa `build_manifest` trong `r6_matrix.py`: dùng relative path đối với `K.R6`, chỉ loại bỏ thư mục `work/` nội bộ của R6, không loại bỏ thư mục cha `Documents/Codex/work` trên Windows.
  - Manifest được ghi vào namespace invocation (`NS / "R6G_MANIFEST.json"`), loại trừ chính file manifest ra khỏi danh sách để tránh stale self-hash.
- **G1-R08 [P2] (Q11 Mutex Race Barrier Sandbox & Proof Binding)**:
  - Đối chiếu mã băm của 3 file production tools (`invocation_runtime.py`, `dispatch_long.py`, `terminal_contract.py`) với historical proof 34/34.
  - Xây dựng bài test độc lập `test_m18_q11_two_process_race_barrier` dùng 2 process hệ điều hành thật sự (`multiprocessing.Process`) cạnh tranh atomic rendezvous, chứng minh đúng 1 winner và 1 loser.
- **G1-R09 [P2] (Context Reconciliation & Honest State Truth)**:
  - Đối chiếu chi tiết 27 protected files: 19 file khớp baseline 100%, 8 file được sửa đổi hợp lệ trong phạm vi A1–A4 & G1-R1.
  - Cập nhật nhất quán toàn bộ các tài liệu trạng thái cho candidate 02.
  - Phân định rõ ràng: code G1-R1 `SELF_VERIFIED_PENDING_CODEX_G1`, các frame media B1 đã kết xuất được ghi nhận là `UNREVIEWED` (chờ nghiệm thu G2).

## 2. Kết quả kiểm thử Ground Truth
- **Toàn bộ 89/89 tests PASS** (gồm 76 tests cũ + 13 tests mới bao phủ 20 hàng matrix M01–M20).
- Root probe v4 replay: **PASS 100%** (initial 1, replay 0, verified-reuse).
- Zero git mutation / zero push / zero dirty tree trên INTEGRATION.
