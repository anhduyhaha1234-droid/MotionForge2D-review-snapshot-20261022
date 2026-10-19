# Báo cáo hoàn tất A1 — CODEX-C02B2-PER-ACTOR-VERIFIED-REUSE

- **Task ID**: `CODEX-C02B2-PER-ACTOR-VERIFIED-REUSE`
- **Giai đoạn**: Gói A (Engineering batch), Task A1
- **Implementation Owner**: Gemini (`ag/gemini-3.8-flash-high`) qua 9router local (`http://127.0.0.1:20128/v1`)
- **Reviewer độc lập**: Codex PM/Reviewer (giữ quyền nghiệm thu các cổng G1, G2, G3)
- **Thời điểm hoàn tất**: 2026-10-17T05:43:44.350393+00:00
- **Trạng thái**: `SELF_VERIFIED` (chưa phải `ROOT_APPROVED`, sẵn sàng chuyển tiếp sang task A2 theo quy tắc batch A)

---

## 1. Kết quả kiểm chứng thực tế (Ground Truth Evidence)

1. **Bộ kiểm thử toàn diện (Full Test Suite)**:
   - **54/54 tests PASS** trong 4.057s (không có lỗi, không có test bị bỏ qua):
     - `test_codex_c01_review_binding.py`: 17/17 PASS (hồi quy C01)
     - `test_codex_c02a_dependency_verification.py`: 13/13 PASS (hồi quy C02A)
     - `test_codex_c02b1_staged_source.py`: 10/10 PASS (hồi quy C02B1)
     - `test_codex_c02b2_per_actor_reuse.py`: 14/14 PASS (bộ test mới hoàn chỉnh cho A1)
2. **Kiểm chứng Producer Replay thực tế (Root Probe)**:
   - Chạy độc lập `probe_c02b2_v4.py`:
     - Lần chạy đầu (initial generation): 1 call
     - Lần chạy lại giữ nguyên đầu vào (unchanged replay): 0 call
     - Trạng thái skip trước replay: `[true, "verified-reuse"]`
     - Kết quả: `pass: true` (exit code 0)
3. **Tuân thủ Allowlist & Bảo toàn Protected Files**:
   - Chỉ sửa đổi duy nhất file kiểm thử được phép: `R6/tests/test_codex_c02b2_per_actor_reuse.py`.
   - Ba file mã nguồn `r6_cache.py`, `r6_keygen.py`, `r6_key_recipe.py` giữ đúng 100% SHA256 từ Checkpoint 015.
   - Toàn bộ 27 file được bảo vệ từ `C02B2_PREFLIGHT.json` đạt 0 drift (100% khớp hash).

---

## 2. Chi tiết thực hiện ma trận P1–P6

- **P1**: Đã chứng minh cả single-actor và multi-actor khi có review PASS hợp lệ sẽ không sinh lại ảnh/crop/upload/post ở lần gọi thứ hai. Thiếu review hoặc review sai (status FAIL, sai artifact hash) lập tức chặn skip và buộc sinh lại.
- **P2**: Đã kiểm tra độc lập các biến đổi tham số hiệu lực (`R6_CTX_FACTOR` mặc định 1.02, `R6_SEED_OFF`, `R6_ONLY_ENTITY`, ledger class, storyboard, template `steps` và `cfg`, mã nguồn code hash). Mọi thay đổi đều làm vô hiệu hóa cache (invalidation); khi khôi phục tham số cũ thì cache hợp lệ trở lại (restored positive).
- **P3**: Đã kiểm tra thay đổi 1 byte giữ nguyên kích thước trên tất cả các thành phần: source, model, auth cast front/profile, staged cast front/profile, staged source, stage receipt, mask, crop, edit output, và graph (kể cả graph non-first của actor thứ hai). Đã chứng minh trường hợp không có actor (`keep_source_no_visible_actor`) và trường hợp actor bị che hoàn toàn (`fully_covered`, ít graph hơn số mask).
- **P4**: Kiểm tra chặt chẽ các trường hợp dữ liệu hỏng: sai `deps_sha`, cắt bớt actor/mask kèm tính lại `deps_sha`, sai kiểu dữ liệu (bool thay số), số phi hữu hạn (NaN/Inf), duplicate keys, độ sâu lồng nhau > 256. Bản ghi legacy v3 được kiểm tra positive đối với hàm kiểm tra file cũ nhưng bị từ chối dứt khoát tại cổng skip per-actor với thông điệp rõ ràng: `"legacy v3 lacks complete per-actor provenance"`.
- **P5**: Khi gặp lỗi sinh ảnh (mất kết nối ComfyUI, ảnh edit đen/blank, vi phạm bound check), tiến trình `r6_keygen` dừng lập tức và không phát hành file `.deps.json`. Module `r6_gate` import độc lập thành công mà không kéo theo `torch` hay `r6_adapter`.
- **P6**: Hoàn thành toàn bộ ma trận kiểm tra và hồi quy 40 bài test cũ.

---

## 3. Các artifact bàn giao của A1

- Mã nguồn test: `R6/tests/test_codex_c02b2_per_actor_reuse.py` (SHA256 `af7d783ea510bb6323123662122e646da0e2d6c9170dbfb47f8eb0993edd7e24`)
- Diff: `WORK/A1/DIFF.patch`
- Manifest: `WORK/A1/MANIFEST.json`
- Kết quả test chi tiết: `WORK/A1/TEST_RESULTS.json`
- Tự review: `WORK/A1/SELF_REVIEW.md`
- Preimages gốc trước khi sửa: `WORK/preimages/c02b2_takeover/`
