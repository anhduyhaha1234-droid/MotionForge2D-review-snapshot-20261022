# GEMINI-C02B3-ASSET-VERIFIED-REUSE (Task A2)

## 1. Mục tiêu (Outcome)
Đảm bảo asset producer (`r6_keygen_asset.py`) thực hiện kiểm tra `skip_allowed` trước khi tiến hành các thao tác nặng (staging, upload, ComfyUI post); áp dụng hợp đồng provenance hoàn chỉnh (`r6_key_deps_v4_asset`) đồng bộ giữa asset producer và `r6_cache.py`; tái sử dụng verified key khi đầu vào không đổi; kiểm soát chặt chẽ các trường hợp `zero_shot_asset_restyle` và `asset_black_passthrough` (dựa trên thực tế pixel `std < 6.0`); từ chối tự nâng cấp bản ghi legacy v3 thành complete skip; và đảm bảo không phá vỡ hồi quy 54 bài test của A1/C01/C02A/C02B1.

## 2. Dependencies
- A1 (`CODEX-C02B2-PER-ACTOR-VERIFIED-REUSE`): `SELF_VERIFIED` (54/54 tests pass).
- C01, C02A, C02B1: `APPROVED`.
- CPU only, boundaries ngoại vi (ComfyUI / Upload / Staging) được cô lập bằng test fixtures; không can thiệp GPU / ComfyUI server.

## 3. Phạm vi ghi độc quyền (Exclusive Write Allowlist)
- `R6/scripts/r6_keygen_asset.py`
- `R6/scripts/r6_cache.py`
- `R6/scripts/r6_key_recipe.py`
- `R6/tests/test_gemini_c02b3_asset_reuse.py` (file test mới)
- `WORK/A2/**` và `WORK/STATE.json`, `WORK/CHECKPOINT.json`

## 4. Protected Paths
- Toàn bộ các file còn lại trong `R6/scripts`: `r6_common.py`, `r6_adapter.py`, `r6_graph.py`, `r6_keygen.py`, `r6_gate.py`, `r6_assemble.py`, `r6_propagate.py`, `r6_cotracker.py`, `r6_matrix.py`, `r6_qa.py`, `r6_sam2.py`, `r6_vace.py`, `r6_validate_masks.py`, `r6_write_reviews.py`, `r6g_blend_review.py`, các file `write_terminal_record_*.py`.
- 4 file test hiện tại: `test_codex_c01_review_binding.py`, `test_codex_c02a_dependency_verification.py`, `test_codex_c02b1_staged_source.py`, `test_codex_c02b2_per_actor_reuse.py`.
- Toàn bộ repo MAIN và INTEGRATION, DB, models, assets, media.

## 5. Baseline Hashes & Preimages (trước khi patch)
- `r6_keygen_asset.py`: `c38b6a5c65905f6cc4d094d501785c5b7312da5ae4b617ef1cd716f5d0347b91` (5,934 bytes, 122 lines)
  - Preimage: `WORK/preimages/c02b3_takeover/r6_keygen_asset.py`
- `r6_cache.py`: `8d4b0c7ad5336e7e6c2a68a12f2a622fbccf900575afd2c1249f31863ae4243d` (24,050 bytes, 445 lines)
  - Preimage: `WORK/preimages/c02b3_takeover/r6_cache.py`
- `r6_key_recipe.py`: `e18fc9d20de1cbf2a3a8f7da2e68fc99c59260701bfbd3dca75106a7cbe8e2bd` (6,361 bytes, 138 lines)
  - Preimage: `WORK/preimages/c02b3_takeover/r6_key_recipe.py`

## 6. Ma trận tiêu chí nghiệm thu (Finite Acceptance Matrix)
- **T1 — Replay không tốn tài nguyên**: `r6_keygen_asset.run_key` lần đầu tạo ảnh và deps hoàn chỉnh -> gắn review PASS -> lần gọi thứ hai kích hoạt `skip_allowed` và trả về ngay, không lặp lại staging, graph generation hay Comfy post.
- **T2 — Invalidation độc lập**: Bất kỳ thay đổi nào về source, model, grey ref, graph workflow, seed_off, prompt, hay review (thiếu review, review FAIL, sai artifact hash) đều làm `skip_allowed` từ chối (False) và buộc tạo lại. Khôi phục lại trạng thái cũ thì skip_allowed thành công trở lại.
- **T3 — Black passthrough & Real pixels**: Khi frame phẳng/đen (`std < 6.0`), producer ghi nhận mode `asset_black_passthrough`, lưu key và deps hoàn chỉnh (không có graph). Khi chạy lại có review PASS thì skip_allowed thành công. Nếu frame không phải đen (`std >= 6.0`) mà dám tuyên bố mode black_passthrough thì bị từ chối; không lấy placeholder làm output tốt.
- **T4 — Legacy v3 Denial**: Bản ghi legacy v3 của asset vẫn pass kiểm tra file cũ nhưng bị từ chối dứt khoát tại `skip_allowed` với lý do thiếu complete provenance; không tự động nâng cấp hoặc auto-PASS.
- **T5 — Failure Controls**: Lỗi sinh ảnh (Comfy post failure, không có output, blank edit) không được phép phát hành file `.deps.json`.
- **T6 — Hồi quy toàn diện**: Giữ nguyên 54/54 tests cũ PASS (17 C01 + 13 C02A + 10 C02B1 + 14 C02B2). Toàn bộ test suite mới + cũ đều PASS 100%.
