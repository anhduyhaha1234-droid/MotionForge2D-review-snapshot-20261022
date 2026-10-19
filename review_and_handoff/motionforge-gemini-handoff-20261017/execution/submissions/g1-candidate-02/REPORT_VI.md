# Báo cáo nghiệm thu Cổng G1 — Engineering Batch Candidate 02 (Correction G1-R1)

- **Cổng đánh giá**: **Cổng G1 (Gói A — Engineering Batch)**
- **Candidate ID**: `g1-candidate-02`
- **Đường dẫn Candidate**: `C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-gemini-handoff-20261017/execution/submissions/g1-candidate-02`
- **Implementation Owner**: Gemini (`ag/gemini-3.8-flash-high`) qua 9router local (`http://127.0.0.1:20128/v1`)
- **Reviewer độc lập**: Codex PM/Reviewer
- **Thời điểm nộp**: 2026-10-18T15:05:18.414701+00:00
- **Trạng thái**: **`SELF_VERIFIED_PENDING_CODEX_G1 — không phải nghiệm thu cuối.`**

---

## 1. Tóm tắt khắc phục toàn bộ 7 Findings P1 và 2 Findings P2

Theo yêu cầu trong `REVIEW_VI.md` và `CORRECTION_MATRIX.md` của Codex, đợt sửa `G1-R1` đã xử lý triệt để:
1. **G1-R01 [P1] — Asset Provenance & Sampler Mismatch (M01–M04)**:
   - Sửa `r6_cache.py`: bắt buộc `consumed["grey_ref"]` phải có mặt, đúng role và khớp hash trong `verify_complete_asset_deps` cho chế độ restyle.
   - Sửa `_verify_asset_graph`: bắt buộc kiểm tra `inp("SAMPLER", "sampler_name") == recipe["sampler"]`, từ chối ngay khi graph là `heun` trong khi recipe là `euler`.
   - Kiểm tra các reference images R1_LOAD và R2_LOAD trỏ đúng grey reference.
2. **G1-R02 [P1] — CoTracker CLI Argparse Crash (M05)**:
   - Bổ sung `import argparse` vào `r6_cotracker.py`. Lệnh CLI `python -B r6_cotracker.py --help` đã được kiểm chứng trả về `exit 0` kèm usage đầy đủ.
3. **G1-R03 [P1] — Tracker Validator Empty / Non-finite Tensors & Window Drift (M06–M07)**:
   - `validate_cotracker_tensors` từ chối dứt khoát `T <= 0`, `N <= 0`, mảng rỗng, tracks NaN/Inf, vis NaN/Inf, và vis ngoài khoảng binary / `[0, 1]`.
   - Sửa cách tính drift theo từng window: chỉ tính trên các frame có cả 2 bên hiển thị trong window; khi không có cặp nào, trả về `None`, loại bỏ hoàn toàn `NaN` trong file JSON.
4. **G1-R04 [P1] — Propagation CLI Child Fail-Closed (M08–M09)**:
   - Sửa `main()` trong `r6_propagate.py` để thoát nonzero (`sys.exit(1)`) khi có bất kỳ shot nào bị lỗi.
   - Sửa `run_shot()` xóa sạch `blend_manifest.json` cũ khi child run `rc != 0` hoặc partial frames, đồng thời ghi nhận failure receipt vào `R6_PROPAGATE_RUNS.jsonl`.
5. **G1-R05 [P1] — Canonical Event Transitions (M10–M11)**:
   - Thống nhất hàm `event_fids_for` trích xuất đầy đủ mọi mốc chuyển trạng thái: actor entry/exit/occlusion/reappear, contact start/end, event `f+1` hoặc `frame`.
   - Đồng bộ hóa logic này vào cả 3 file: `r6_ledger.py`, `r6_gate.py`, và `r6_propagate.py`.
   - `plan_runs` phân tách dứt khoát các run tại hard cut.
6. **G1-R06 [P1] — Q-Matrix Evidentiary Rigor & Batch Gate Enforcement (M12–M14)**:
   - Sửa `r6_matrix.py`: mỗi verdict PASS bắt buộc phải parse file evidence thật, kiểm tra `st_size > 0`, kiểm tra JSON hợp lệ và verdict PASS trong nội dung; file 0-byte trả về `UNKNOWN`.
   - `gate_batch_conformance` từ chối các mode lạ bằng `GateBlock("UNKNOWN_BATCH_MODE")`; ở mode `"final"` bắt buộc phải gọi `gate_submit(record)` kiểm tra toàn bộ artifacts.
   - Nối `gate_batch_conformance` vào caller thực tế (`main()` trong `r6_matrix.py` và `gate_submit()` trong `r6_gate.py`).
7. **G1-R07 [P1] — Manifest Relative Filtering & Namespace Isolation (M15–M16)**:
   - Sửa `build_manifest` trong `r6_matrix.py`: lọc theo relative path đối với `K.R6`, chỉ loại bỏ thư mục `work/` nội bộ, không loại bỏ thư mục cha `Documents/Codex/work`.
   - Manifest được ghi vào namespace invocation `NS / "R6G_MANIFEST.json"`, loại trừ chính file manifest ra khỏi danh sách để tránh stale self-hash.
8. **G1-R08 [P2] — Q11 Mutex Race Barrier Sandbox & Proof Binding (M17–M18)**:
   - Đối chiếu mã băm của 3 file production tools (`invocation_runtime.py`, `dispatch_long.py`, `terminal_contract.py`) khớp 100% với historical proof 34/34.
   - Xây dựng bài test độc lập `test_m18_q11_two_process_race_barrier` dùng 2 process hệ điều hành thật sự (`multiprocessing.Process`) cạnh tranh atomic rendezvous, chứng minh đúng 1 winner và 1 loser.
9. **G1-R09 [P2] — Context Reconciliation & Honest State Truth (M19–M20)**:
   - Đối chiếu chi tiết 27 protected files: 19 file khớp baseline 100%, 8 file được sửa đổi hợp lệ trong phạm vi A1–A4 & G1-R1.
   - Cập nhật nhất quán toàn bộ các tài liệu trạng thái cho candidate 02.
   - Phân định rõ ràng: code G1-R1 `SELF_VERIFIED_PENDING_CODEX_G1`, các frame media B1 đã kết xuất được ghi nhận là `UNREVIEWED` (chờ nghiệm thu G2).

---

## 2. Bằng chứng kiểm thử thực tế (Ground Truth)

- **Toàn bộ bộ kiểm thử**: **89/89 tests PASS** trong 11.173s:
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
- **Tuân thủ Allowlist & Bảo vệ Repository**:
  - INTEGRATION repo: `porcelain: 0` (clean hoàn toàn).
  - MAIN repo: bảo toàn nguyên vẹn dirty baseline cũ (HEAD `a40e368`), 0 unapproved modifications.

---

## 3. Danh mục hồ sơ bàn giao trong gói G1 Candidate 02

- **Báo cáo này**: `REPORT_VI.md`
- **Kết quả 20 hàng ma trận**: `CORRECTION_MATRIX_RESULTS.json`
- **Danh mục file & mã băm candidate 02**: `MANIFEST.json`
- **Bản vá diff tổng hợp G1-R1**: `DIFF.patch`
- **Chi tiết kết quả kiểm thử 89 tests**: `TEST_RESULTS.json`
- **Biên bản tự review**: `SELF_REVIEW.md`
- **Bản đồ đối chiếu Q/T**: `Q_T_MATRIX.md`
- **Tài liệu tiếp tục**: `RESUME.md`
- **Trạng thái tiến trình & lease**: `LIVE_JOBS.json`
- **Checkpoint G1-Candidate-02**: `CHECKPOINT.json`
- **Bảng đối chiếu 27 protected files**: `CONTEXT_RECONCILIATION.json`

---

**`SELF_VERIFIED_PENDING_CODEX_G1 — không phải nghiệm thu cuối.`**

Đường dẫn để chuyển lại hội thoại Codex đánh giá độc lập:
`C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-gemini-handoff-20261017/execution/submissions/g1-candidate-02/REPORT_VI.md`
và
`C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-gemini-handoff-20261017/execution/submissions/g1-candidate-02/MANIFEST.json`
