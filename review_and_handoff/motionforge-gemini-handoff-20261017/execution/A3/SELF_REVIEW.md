# Tự đánh giá kỹ thuật A3 (Self-Review) — GEMINI-A3-EVENT-TIMING-TRACKING

## 1. Phân tích lỗi gốc & Các cải tiến đã hoàn tất
1. **Event Keys Mapping & Inclusion**:
   - Trước sửa: `r6_ledger.py` chỉ lấy grid keys từ R5 storyboard cũ, bỏ rơi các event fids nằm ngoài bội số 10. `r6_gate.py` và `r6_propagate.py` chỉ tìm kiếm trường `"frame"` trong khi `source_actor_ledger.jsonl` sử dụng trường `"f"`.
   - Sau sửa: Đồng bộ hóa nhận diện cả `"f"` (0-based) và `"frame"` (1-based), contacts `from + 1`, và actor entry `from`. Đưa toàn bộ event fids vào storyboard keys để keygen và propagate đồng bộ tuyệt đối, loại trừ hoàn toàn nguy cơ rớt key hoặc gate block.
2. **Hard Cut Decomposition trong `plan_runs`**:
   - `plan_runs` trong `r6_propagate.py` đã được nâng cấp để tách các đoạn chạy độc lập tại ranh giới hard cuts, ngăn ngừa triệt để việc nội suy hình ảnh băng qua hard cuts.
3. **Child Outcomes Fail-Closed**:
   - Đã kiểm chứng: run con `rc != 0`, thiếu frame hoặc partial frames làm `run_shot` dừng ngay lập tức (`SystemExit`), không ghi đè hoặc phát hành `blend_manifest.json` hỏng.
4. **CoTracker Tensor Contract & Side-by-Side Strip**:
   - Thêm `validate_cotracker_tensors` xác thực `(T, N, 2)` và `(T, N)` bool, từ chối tensor chứa NaN, Inf, hoặc vượt quá kích thước canvas.
   - Sửa lỗi hiển thị dải so sánh side-by-side (`c.paste(_I.fromarray(b)...) if False else None` -> kích hoạt dán thật frame sinh ra).
5. **CropAndStitch Landmark Roundtrip**:
   - Đã kiểm chứng: ngoài vùng mask nguyên vẹn 100% (`outside_max == 0.0`); bound check phát hiện và chặn rò rỉ hình học ngoài margin 24.

## 2. Tiêu chí nghiệm thu E1–E7
- **E1**: Map chính xác event fids từ cả 2 định dạng, không sót sự kiện nào.
- **E2**: Decompose runs tách dứt khoát tại hard cut.
- **E3**: Run con lỗi hoặc thiếu frame -> fail-closed ngay lập tức.
- **E4**: CoTracker reader xác thực shape, tính hữu hạn, giới hạn canvas.
- **E5**: Side-by-side strip dán đủ cả 2 ảnh nguồn và kết quả.
- **E6**: Landmark roundtrip sạch, bound check phát hiện rò rỉ.
- **E7**: Toàn bộ 71/71 tests PASS (17 C01 + 13 C02A + 10 C02B1 + 14 C02B2 + 10 C02B3 + 7 A3). Probe v4 replay PASS.

## 3. Trạng thái
- Trạng thái Task A3: `SELF_VERIFIED`.
