# Tự đánh giá kỹ thuật A2 (Self-Review) — GEMINI-C02B3-ASSET-VERIFIED-REUSE

## 1. Khảo sát & Khắc phục Baseline
- **Baseline trước sửa**:
  - `r6_keygen_asset.py` hoàn toàn không gọi `skip_allowed` khi bắt đầu `run_key`.
  - Không có hợp đồng provenance cho trường hợp `asset_black_passthrough` (bỏ qua sinh .deps.json).
  - Metadata cấu hình ghi vào deps là `{"mode": "zero_shot_asset_restyle", "steps": 4}` lệch schema so với `settings_now` của `r6_cache.py`.
  - `r6_key_recipe.py` từ chối `zero_explicit == True` vì chỉ hỗ trợ per-actor klein.
- **Khắc phục triệt để**:
  - Bổ sung `current_asset_recipe` trong `r6_key_recipe.py` phản ánh đúng prompt, template parameters (steps, cfg, sampler, model, clip, vae), seed và code hash.
  - Thiết lập hợp đồng complete provenance `r6_key_deps_v4_asset` trong `r6_cache.py` cho cả 2 mode: `zero_shot_asset_restyle` và `asset_black_passthrough`.
  - Đấu nối `CA.skip_allowed` trực tiếp ở đầu `run_key` trong `r6_keygen_asset.py`.
  - Kiểm soát nghiêm ngặt pixel thực tế: `std < 6.0` mới cho phép black passthrough; nếu `std >= 6.0` mà khai black passthrough sẽ bị `verify_complete_asset_deps` từ chối.
  - Bản ghi legacy v3 bị từ chối dứt khoát tại `skip_allowed` với lý do `"legacy v3 lacks complete provenance"`.

## 2. Tiêu chí nghiệm thu T1–T6
- **T1**: Replay khi đầu vào không đổi tiêu tốn 0 cuộc gọi staging / post / upload, giữ nguyên byte key và deps. Thiếu review hoặc review sai (FAIL, sai SHA) chặn skip và buộc sinh lại.
- **T2**: Same-path same-size mutation trên từng file (source, model, staged source, stage receipt, graph, grey ref) và mutation tham số (seed offset, storyboard) đều làm invalidation tức thì; restore thành công.
- **T3**: Black passthrough không sinh graph, 0 post call, replay an toàn; từ chối nếu source không thực sự phẳng.
- **T4**: Legacy v3 của asset pass `verify_deps` kiểm tra file cũ nhưng bị từ chối quyền skip complete trong `skip_allowed`.
- **T5**: Lỗi post hoặc blank edit dừng tiến trình ngay, không publish file `.deps.json`.
- **T6**: Hồi quy 64/64 tests PASS (17 C01 + 13 C02A + 10 C02B1 + 14 C02B2 + 10 C02B3). Probe per-actor v4 replay vẫn PASS 100%.

## 3. Allowlist & Bằng chứng bảo vệ
- Sửa đúng allowlist A2: `r6_keygen_asset.py`, `r6_cache.py`, `r6_key_recipe.py`, `test_gemini_c02b3_asset_reuse.py`.
- 0 protected files bị sai lệch hash.
- Trạng thái gói A2: `SELF_VERIFIED`.
