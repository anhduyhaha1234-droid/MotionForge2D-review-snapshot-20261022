# Báo cáo nghiệm thu Cổng G1 — Engineering Batch Candidate 04 (Correction G1-R1)

- **Cổng đánh giá**: **Cổng G1 (Gói A — Engineering Batch)**
- **Candidate ID**: `g1-candidate-04`
- **Đường dẫn Candidate**: `C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-gemini-handoff-20261017/execution/submissions/g1-candidate-04`
- **Implementation Owner**: Gemini (`ag/gemini-3.8-flash-high`) qua 9router local (`http://127.0.0.1:20128/v1`)
- **Reviewer độc lập**: Codex PM/Reviewer
- **Thời điểm nộp**: 2026-10-19T12:18:09.475025+00:00
- **Trạng thái**: **`SELF_VERIFIED_PENDING_CODEX_G1 — không phải nghiệm thu cuối.`**

---

## 1. Báo cáo khắc phục các lỗi thực tế từ Review 03 (Candidate 03 -> 04)

Codex trong review candidate 03 đã xác minh **8/20 hàng** (M01, M02, M03, M04, M05, M07, M10, M15). Đợt sửa Candidate 04 tập trung xử lý dứt điểm **12 hàng còn lại**:

1. **R04 — M08, M09 (Propagation Render, Failure Boundary & Global Upstream Naming)**:
   - **Sửa NameError Image**: Bổ sung `from PIL import Image` ở đầu file `r6_propagate.py`. Kiểm tra `ruff check --no-cache --select F821` báo sạch 100% (0 lỗi).
   - **Đồng bộ quy ước đặt tên upstream**: Upstream pinned `VideoSequence` (SHA `ed40afd1`) tạo tên frame theo index toàn cục dạng 4 chữ số toàn cục cho từng frame trong khoảng beg..end-1. Với `beg=11, end=21`, upstream tạo `0011.jpg..0020.jpg`. `r6_propagate.py` kiểm tra chính xác các file này và copy nguyên vẹn sang thư mục `merged`, hỗ trợ trơn tru các run có `beg > 1`.
   - **Bao bọc toàn diện failure boundary**: Toàn bộ quy trình `run_shot()` được đặt trong khối `try...except (Exception, SystemExit) as exc`. Mọi lỗi từ preflight, staging (kể cả `SystemExit` do thiếu key), child execution (`rc != 0`), số lượng frame lệch, frame sai tên (`9001.jpg`), frame thừa (`0000.jpg`), hoặc ảnh corrupt decode đều lập tức xóa bỏ stale `blend_manifest.json`, ghi failure receipt có `rc=1` vào `R6_PROPAGATE_RUNS.jsonl` và thoát nonzero (`sys.exit(1)`).
2. **R06 — M12, M13, M14 (Evidence Rigor & ffprobe Video Decode)**:
   - **Xác thực video bằng ffprobe**: `validate_evidence_video` trong `r6_evidence_contract.py` gọi trực tiếp `ffprobe` để kiểm tra container và stream: video giả mạo (`ftyp + xxxx`) bị ffprobe từ chối ngay lập tức; video hợp lệ được kiểm tra stream video và số frame.
   - **Xác thực mã nguồn test**: Q05 trong `r6_matrix.py` kiểm tra file test parse được cú pháp Python qua `ast.parse` (loại bỏ non-Python garbage), kiểm tra receipt có `all_passed: True`, `tests_run > 0`, `exit_code: 0`, và khớp hash file test.
   - **Xác thực supporting proof**: `gate_batch_conformance` trong `r6_gate.py` bắt buộc `record["proof"]` phải là dict có cấu trúc chi tiết kiểm chứng, từ chối việc chỉ sao chép lại nhãn PASS.
3. **R07 — M14, M16 (Submission Adapter & Hash Recompute)**:
   - **Chặn same-size tamper**: `r6_submission_adapter.py` tính toán lại mã SHA-256 cho toàn bộ artifacts trong manifest đối chiếu với đĩa thực tế; nếu file bị sửa đổi nội dung dù giữ nguyên kích thước (như `ABCD -> WXYZ`), adapter lập tức báo lỗi, trả về `False` và không xuất bản `TASK_SUBMITTED`.
   - **Đấu nối artifacts vào final mode**: Adapter tự động phân loại và truyền danh sách artifacts đầy đủ vào `gate_batch_conformance`, giúp `gate_submit` nhận diện đủ 5 kind (`master`, `comparison`, `matrix`, `checkpoint`, `receipts`).
   - **Thứ tự đóng băng không vòng lặp**: `stage_and_publish_matrix` tính hash của matrix tạm, cập nhật vào manifest trước khi ghi manifest và kiểm tra gate, xuất bản nguyên tử và tạo marker `.submission_freeze.json`.
4. **R03 / R05 — M06, M11 (Strict Integer Contract & Cuts Caller)**:
   - `r6_event_contract.py` áp dụng hàm `check_strict_int` từ chối dứt khoát float (`43.9`), bool (`True`), string (`"43"`), float pair (`42.8/43.2`).
   - CoTracker CLI giữ nguyên `frame: 43` thành `fid: 43`, từ chối out-of-range `f=700`, trả về `None` khi không có visible pairs (không sinh NaN trong JSON).
   - Kiểm tra contact bounds (`from >= 0`, `to >= from`). `run_shot` truyền tường minh `cuts` vào `plan_runs` để chia tách run tại hard cuts.
5. **R08 — M17, M18 (Controller Mutex Race Barrier)**:
   - Đối chiếu mã băm 3 tool sản xuất (`invocation_runtime.py`, `dispatch_long.py`, `terminal_contract.py`) khớp 100% với proof 34/34.
   - Gắn kết 51/51 harness test results và 34/34 race results; thực thi test mô phỏng 2-process OS rendezvous barrier trong sandbox chứng minh 1 winner.
6. **R09 — M19, M20 (Candidate Identity, State Truth & Watchdog)**:
   - Lưu trữ bản sao đầy đủ của 18 file candidate (`source_snapshot/`) và 12 file support dependencies (`dependencies_snapshot/`) vào candidate 04 để phục vụ tái lập độc lập.
   - `auto_nudge_watchdog.py`: phát hiện `WAITING_CODEX_REVIEW` và bỏ qua model nudge để bảo toàn quota; phân loại lỗi mạng tạm thời (chờ 5 phút theo rules §7) vs lỗi quota/auth (dừng và báo blocker).
   - `telegram_heartbeat.py`: phân định trạng thái `WAITING_CODEX_REVIEW`, đo liveness thực mà không lấy self-touch `STATE.json` làm tiến độ.
   - Reconcile `STATE.json` trung thực: `status: WAITING_CODEX_REVIEW`, ghi rõ 8 verified / 12 closed in candidate 04, danh sách `changed_files` đầy đủ.

---

## 2. Bằng chứng kiểm thử thực tế (Ground Truth)

- **Toàn bộ bộ kiểm thử**: **89/89 tests PASS** trong 12.061s:
  - `test_codex_c01_review_binding.py`: 17/17 PASS
  - `test_codex_c02a_dependency_verification.py`: 13/13 PASS
  - `test_codex_c02b1_staged_source.py`: 10/10 PASS
  - `test_codex_c02b2_per_actor_reuse.py`: 14/14 PASS
  - `test_gemini_c02b3_asset_reuse.py`: 10/10 PASS
  - `test_gemini_a3_event_tracking.py`: 7/7 PASS
  - `test_gemini_a4_evidence_conformance.py`: 5/5 PASS
  - `test_g1_r1_correction.py`: 13/13 PASS (M01–M20)
- **Kiểm chứng Producer Replay Probe**:
  - `probe_c02b2_v4.py`: 1 call lần đầu, 0 call lần chạy lại (`verified-reuse`).
- **Kiểm tra tĩnh Ruff F821**:
  - `ruff check --no-cache --select F821 r6/scripts`: **All checks passed!** (0 errors).
- **Tuân thủ Allowlist & Bảo vệ Repository**:
  - INTEGRATION repo: `porcelain: 0` (clean hoàn toàn).
  - MAIN repo: bảo toàn nguyên vẹn dirty baseline cũ (HEAD `a40e368f7c47c232cf2eeed9fb185c5972cb98ba`), 0 commit, 0 push, 0 unapproved mutation.

---

## 3. Danh mục hồ sơ bàn giao trong gói G1 Candidate 04

- **Báo cáo này**: `REPORT_VI.md`
- **Kết quả 20 hàng ma trận**: `CORRECTION_MATRIX_RESULTS.json`
- **Danh mục file & mã băm candidate 04**: `MANIFEST.json`
- **Bản vá diff tổng hợp G1-R1**: `DIFF.patch`
- **Chi tiết kết quả kiểm thử 89 tests**: `TEST_RESULTS.json`
- **Biên bản tự review**: `SELF_REVIEW.md`
- **Bản đồ đối chiếu Q/T**: `Q_T_MATRIX.md`
- **Tài liệu tiếp tục**: `RESUME.md`
- **Trạng thái tiến trình & lease**: `LIVE_JOBS.json`
- **Checkpoint G1-Candidate-04**: `CHECKPOINT.json`
- **Bảng đối chiếu 27 protected files**: `CONTEXT_RECONCILIATION.json`
- **Bản sao nguồn candidate**: `source_snapshot/`
- **Bản sao dependencies hỗ trợ**: `dependencies_snapshot/`

---

**`SELF_VERIFIED_PENDING_CODEX_G1 — không phải nghiệm thu cuối.`**

Đường dẫn để chuyển lại hội thoại Codex đánh giá độc lập:
`C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-gemini-handoff-20261017/execution/submissions/g1-candidate-04/REPORT_VI.md`
và
`C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-gemini-handoff-20261017/execution/submissions/g1-candidate-04/MANIFEST.json`
