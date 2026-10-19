# Báo cáo nghiệm thu Cổng G1 — Engineering Batch Candidate 03 (Correction G1-R1)

- **Cổng đánh giá**: **Cổng G1 (Gói A — Engineering Batch)**
- **Candidate ID**: `g1-candidate-03`
- **Đường dẫn Candidate**: `C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-gemini-handoff-20261017/execution/submissions/g1-candidate-03`
- **Implementation Owner**: Gemini (`ag/gemini-3.8-flash-high`) qua 9router local (`http://127.0.0.1:20128/v1`)
- **Reviewer độc lập**: Codex PM/Reviewer
- **Thời điểm nộp**: 2026-10-19T03:25:22.602704+00:00
- **Trạng thái**: **`SELF_VERIFIED_PENDING_CODEX_G1 — không phải nghiệm thu cuối.`**

---

## 1. Báo cáo xử lý 15 Findings còn mở & 5 Findings đã được xác minh

Codex trong review candidate 02 đã xác minh **5/20 hàng** (M01, M05, M08, M10, M15). Đợt sửa Candidate 03 tập trung xử lý dứt điểm **15 hàng còn lại**:

1. **R01 — M02, M03, M04 (Effective References & Graph Wiring)**:
   - Sửa `r6_cache.py`: `_verify_asset_graph` bắt buộc các node `R1_LOAD`, `R2_LOAD`, `R3_LOAD` phải tồn tại trong graph (từ chối thiếu R1) và phải trỏ chính xác canonical path `identity5m_20261008/r6/_grey_64.png` (từ chối `wrong_invocation/fake_grey.png`).
   - `KEY_LOAD` bắt buộc phải trỏ đúng `identity5m_20261008/r6/work/<staged_source.name>`.
   - Giữ nguyên các test controls: black passthrough hợp lệ, unchanged replay 0 extra calls.
2. **R03 / R05 — M06, M07, M11 (Canonical Event Contract & CoTracker Timing)**:
   - Xây dựng `r6_event_contract.py`: thống nhất duy nhất một parser thời gian cho cả 0-based `f` và 1-based `frame`, kiểm tra mâu thuẫn f vs frame, và bắt buộc bounds `[1, n]`.
   - Sửa `r6_cotracker.py`: sử dụng contract chung, giữ nguyên `frame: 43` thành `fid: 43` (không bị mặc định thành 2); từ chối out-of-range events (`f: 700` trong clip 50f) bằng ValueError.
   - Sửa cách tính drift window: trả về `None` khi không có visible pairs, loại bỏ hoàn toàn `NaN` trong JSON.
   - Sửa `event_fids_for`: từ chối contact có `from < 0` hoặc `to > n` bằng ValueError.
   - Sửa `run_shot`: truyền tường minh `cuts=cuts` vào `plan_runs` để phân tách run tại hard cuts.
3. **R04 — M09 (Propagation Child Output Validation & Invalidation)**:
   - Sửa `run_shot` trong `r6_propagate.py`: kiểm tra số lượng frame chính xác, tên file chuẩn `0001.jpg..expect.jpg` cho `i in 1..expect`, từ chối tên sai (`9001.jpg`) hoặc frame thừa (`0000.jpg`).
   - Kiểm tra PIL decode cho từng frame trong run con và toàn bộ merge frames.
   - Xử lý lỗi toàn diện: khi có bất kỳ sự cố nào (child rc!=0, partial, tên sai, thừa, corrupt decode), `blend_manifest.json` bị xóa ngay lập tức, ghi receipt thất bại có `rc: 1` vào `R6_PROPAGATE_RUNS.jsonl`, và `main()` thoát với mã lỗi nonzero (`sys.exit(1)`).
4. **R06 / R07 — M12, M13, M14, M16 (Matrix Rigor, Batch Gate Enforcement & Atomic Publication)**:
   - Xây dựng `r6_evidence_contract.py`: Q01 yêu cầu ảnh decode được, Q05 yêu cầu receipt với `all_passed: True` (không fallback PASS mù), Q07 yêu cầu v4 deps vượt qua `CA.verify_complete_deps`, Q08 yêu cầu video MP4 decode được.
   - `gate_batch_conformance` từ chối mode lạ (`GateBlock`), yêu cầu supporting proof cho Q05/Q07 trong mode engineering, và yêu cầu đầy đủ artifacts trong mode final.
   - Atomic stage-validate-publish protocol: nếu gate thất bại, file `.tmp` bị hủy và `GateBlock` được ném ra, candidate bị chặn tuyệt đối không thể xuất bản manifest/matrix.
   - Xây dựng `r6_submission_adapter.py`: kiểm tra toàn bộ gate và artifacts, thoát nonzero (exit 1) khi có lỗi và không bao giờ ghi `TASK_SUBMITTED` trái phép.
   - `build_manifest` lọc relative path chuẩn xác, loại trừ internal `work/`, bảo toàn file dưới ancestor `Codex/work`, và ghi vào invocation namespace.
5. **R08 — M17, M18 (Controller Mutex Race Barrier)**:
   - Đối chiếu mã băm 3 tool sản xuất (`invocation_runtime.py`, `dispatch_long.py`, `terminal_contract.py`) khớp 100% với proof 34/34.
   - Khảo sát kết quả 34/34 race cases và 51/51 harness test cases; thực thi test mô phỏng 2-process OS barrier chứng minh 1 winner / 1 loser.
6. **R09 — M19, M20 (Candidate Identity, State Truth & Watchdog)**:
   - Snapshot toàn bộ 12 support dependencies vào candidate 03 để phục vụ tái lập độc lập.
   - `auto_nudge_watchdog.py` được cấu hình bỏ qua model nudge khi ở trạng thái `WAITING_CODEX_REVIEW` để bảo toàn quota.
   - `telegram_heartbeat.py` phân định rõ trạng thái `WAITING_CODEX_REVIEW` và không lấy self-touch `STATE.json` làm tiến độ code.
   - Reconcile `STATE.json` trung thực: `changed_files` đầy đủ, không overclaim.

---

## 2. Bằng chứng kiểm thử thực tế (Ground Truth)

- **Toàn bộ bộ kiểm thử**: **89/89 tests PASS** trong 9.816s:
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
  - MAIN repo: bảo toàn nguyên vẹn dirty baseline cũ (HEAD `a40e368`), 0 commit, 0 push, 0 unapproved mutation.

---

## 3. Danh mục hồ sơ bàn giao trong gói G1 Candidate 03

- **Báo cáo này**: `REPORT_VI.md`
- **Kết quả 20 hàng ma trận**: `CORRECTION_MATRIX_RESULTS.json`
- **Danh mục file & mã băm candidate 03**: `MANIFEST.json`
- **Bản vá diff tổng hợp G1-R1**: `DIFF.patch`
- **Chi tiết kết quả kiểm thử 89 tests**: `TEST_RESULTS.json`
- **Biên bản tự review**: `SELF_REVIEW.md`
- **Bản đồ đối chiếu Q/T**: `Q_T_MATRIX.md`
- **Tài liệu tiếp tục**: `RESUME.md`
- **Trạng thái tiến trình & lease**: `LIVE_JOBS.json`
- **Checkpoint G1-Candidate-03**: `CHECKPOINT.json`
- **Bảng đối chiếu 27 protected files**: `CONTEXT_RECONCILIATION.json`
- **Thư mục snapshots hỗ trợ**: `dependencies_snapshot/`

---

**`SELF_VERIFIED_PENDING_CODEX_G1 — không phải nghiệm thu cuối.`**

Đường dẫn để chuyển lại hội thoại Codex đánh giá độc lập:
`C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-gemini-handoff-20261017/execution/submissions/g1-candidate-03/REPORT_VI.md`
và
`C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-gemini-handoff-20261017/execution/submissions/g1-candidate-03/MANIFEST.json`
