# GEMINI-A3-EVENT-TIMING-TRACKING (Task A3)

## 1. Mục tiêu (Outcome)
Chuẩn hóa và kiểm soát toàn diện logic event timing, child outcomes của Rerender stage-2 và hợp đồng dữ liệu CoTracker:
1. Đảm bảo event keys không bị bỏ sót ngoài lưới sample; sự kiện contact/entry/exit/occlusion được map frame chính xác (hỗ trợ cả trường `f` và `frame`), không nội suy qua hard cut.
2. Kiểm soát chặt chẽ Rerender stage-2 child failure: bất kỳ run con nào thất bại (`rc != 0`), thiếu frame, partial frames, duplicate frames đều làm parent fail-closed trước khi publish/assemble; không duplicate frame/fill giả để đủ số lượng.
3. CoTracker reader tuân thủ đúng hợp đồng `tracks[T,N,2]` float32, `visibility[T,N]` bool, query points tương ứng; kiểm tra từ chối các trường hợp non-finite, empty, out-of-range; sửa lỗi hiển thị dải so sánh side-by-side (sửa lỗi `if False else None` làm rơi frame kết quả).
4. Kiểm chứng CropAndStitch transform round-trip: ngoài vùng mask không bị rò rỉ, bound check phát hiện rò rỉ hình học.
5. Bảo toàn hồi quy toàn bộ 64 bài test đã kiểm chứng từ A1 (54) và A2 (10).

## 2. Dependencies
- A1 (`CODEX-C02B2-PER-ACTOR-VERIFIED-REUSE`): `SELF_VERIFIED`
- A2 (`GEMINI-C02B3-ASSET-VERIFIED-REUSE`): `SELF_VERIFIED`
- C01, C02A, C02B1: `APPROVED`
- CPU/Fixture boundaries cô lập, không gọi GPU/server live.

## 3. Phạm vi ghi độc quyền (Exclusive Write Allowlist)
- `R6/scripts/r6_cotracker.py`
- `R6/scripts/r6_propagate.py`
- `R6/scripts/r6_ledger.py`
- `R6/scripts/r6_gate.py`
- `R6/tests/test_gemini_a3_event_tracking.py` (test mới)
- `WORK/A3/**` và `WORK/STATE.json`, `WORK/CHECKPOINT.json`

## 4. Protected Paths
- Toàn bộ các file khác trong `R6/scripts` và `R6/tests`.
- Toàn bộ repo MAIN và INTEGRATION, DB, models, assets, media.

## 5. Baseline Hashes & Preimages (trước khi patch)
- `r6_propagate.py`: `bcd22a7676b178a28f1c75baaaae23adec48a89ae5a40cd3765b44f5f824bf01`
- `r6_cotracker.py`: `255e802f4547ac333e77075c8c145b3dc912ba77231248d840c1bc037501cf7c`
- `r6_ledger.py`: `5797fe9f11e1b8178f0d35bff5ca6bc575cb895ebea98831dcd5a65e2b81c131`
- `r6_gate.py`: `8c2e3f9eedd4d8e11832809c2b72293db17df1fb5a4012bd39fa396f93143f94`
- Preimages được lưu tại: `WORK/preimages/a3_takeover/`

## 6. Ma trận kiểm thử (Finite Acceptance Matrix)
- **E1 — Event Keys Mapping & Discovery**: Nhận diện đầy đủ event fids từ cả `"f"` (0-based) và `"frame"` (1-based), contacts `from + 1`, và actor entry `w["from"]`. Đưa đầy đủ vào storyboard keys để không bị thiếu sót khi sinh key và qua cổng `gate_shot_before_propagate`.
- **E2 — Không nội suy qua Hard Cut**: Decompose run trong `plan_runs` cắt đứt tại ranh giới hard cut / event boundary để không nội suy visual qua vết cắt.
- **E3 — Stage-2 Child Outcomes Fail-Closed**: Inject child failure (`rc != 0`), thiếu frame, partial output, duplicate frames -> `run_shot` dừng ngay lập tức (SystemExit/GateBlock), không xuất xưởng blend_manifest.
- **E4 — CoTracker Tensor Contract**: Hàm `validate_cotracker_tensors` xác thực `(T, N, 2)` và `(T, N)`, từ chối tensor chứa NaN, Inf, âm hoặc vượt kích thước canvas (640, 368).
- **E5 — CoTracker Side-by-Side Sửa Lỗi**: Dải so sánh trước/sau `_windows_strip.png` dán cả frame nguồn và frame sinh ra (sửa lỗi code cũ bỏ rơi frame b).
- **E6 — CropAndStitch Landmark Roundtrip**: Landmark roundtrip giữ nguyên ngoài mask; bound check phát hiện rò rỉ pixel ra ngoài dilation mask.
- **E7 — Hồi quy toàn diện**: Chạy toàn bộ 64 bài test cũ + bộ test mới A3 = 100% PASS.
