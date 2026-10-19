# Tự đánh giá kỹ thuật A1 (Self-Review) — CODEX-C02B2-PER-ACTOR-VERIFIED-REUSE

## 1. Phạm vi ghi độc quyền (Allowlist Compliance)
- Chỉ sửa đúng file kiểm thử theo nhiệm vụ: `R6/tests/test_codex_c02b2_per_actor_reuse.py`.
- Các file sản xuất `r6_cache.py`, `r6_keygen.py`, `r6_key_recipe.py` giữ đúng SHA-256 từ Checkpoint 015 đã được đối chiếu khớp hoàn toàn:
  - `r6_cache.py`: `8d4b0c7ad5336e7e6c2a68a12f2a622fbccf900575afd2c1249f31863ae4243d`
  - `r6_keygen.py`: `4082b9d59afbab5416ed6c4784e713612d16553b98a307ccc428a0e7975bd282`
  - `r6_key_recipe.py`: `e18fc9d20de1cbf2a3a8f7da2e68fc99c59260701bfbd3dca75106a7cbe8e2bd`
- 27 file được bảo vệ (`protected`) trong `C02B2_PREFLIGHT.json` có 0 drift.
- Không sửa Git commit/push, không can thiệp database, không GPU/ComfyUI/HTTP inference.

## 2. Tiêu chí nghiệm thu P1–P6
- **P1 (Replay & Review Binding)**:
  - Single-actor: 1 lần tạo ban đầu (stage=1, crop=1, upload=4, post=1) -> gắn review PASS -> chạy lại unchanged replay tiêu tốn 0 cuộc gọi phụ, giữ nguyên byte key và deps.
  - Multi-actor: 2 actor tạo tương ứng (crop=2, post=2, upload=8) -> unchanged replay tiêu tốn 0 cuộc gọi phụ.
  - Thiếu review hoặc review sai (status FAIL, sai SHA artifact) -> `skip_allowed` từ chối (False), bắt buộc sinh lại.
- **P2 (Effective Settings Mutations)**:
  - Độc lập kiểm tra thay đổi: `R6_CTX_FACTOR`, `R6_SEED_OFF`, `R6_ONLY_ENTITY`, ledger class, storyboard, template steps/cfg, code hash.
  - Mọi thay đổi đều làm `skip_allowed` trả về False; khôi phục giá trị ban đầu thì `skip_allowed` trả về True.
- **P3 (Same-Path Same-Size Mutations & Edge Cases)**:
  - Thay đổi đúng 1 byte giữ nguyên kích thước trên từng file: source, model, auth cast front/profile, staged cast front/profile, staged source, stage receipt, mask, crop, edit, graph. Tất cả đều làm invalidation tức thì; restore đều trả về valid.
  - Non-first graph của multi-actor cũng bị kiểm tra và invalidation độc lập.
  - No-visible-actor (`keep_source_no_visible_actor`): tạo key passthrough, 0 crop/post/upload, replay an toàn.
  - Fully-covered actor: actor phía sau bị che kín hoàn toàn bởi actor phía trước chỉ sinh 1 crop/graph cho actor trước, actor sau được ghi nhận `fully_covered` mà không tạo graph giả.
- **P4 (Malformed, Truncated, Depth & Legacy Denial)**:
  - Sai self-digest `deps_sha` bị chặn.
  - Truncated collection (cắt bớt actor hoặc mask) kèm tính lại `deps_sha` vẫn bị chặn vì không khớp với expected selection/recipe.
  - Sai kiểu dữ liệu (bool thay int/float), non-finite (NaN/Inf), duplicate keys, depth > 256 đều bị từ chối an toàn (controlled False/GateBlock).
  - Legacy v3: kiểm tra positive file validation trả về (True, "ok"), nhưng `skip_allowed` từ chối dứt khoát với lý do `"legacy v3 lacks complete per-actor provenance"`.
- **P5 (Failure Controls & Standalone Gate Import)**:
  - Lỗi GPU/post, blank edit (std < 0.01), bound check thất bại đều làm producer dừng ngay lập tức mà không ghi file `.deps.json`.
  - Gate import độc lập: kiểm tra `r6_gate` import thành công mà không kéo theo `torch` hay `r6_adapter`.
- **P6 (Regression & Replay Probe)**:
  - Full suite 54/54 tests PASS (17 C01 + 13 C02A + 10 C02B1 + 14 C02B2).
  - Root replay probe `probe_c02b2_v4.py` chạy độc lập PASS (initial=1, replay=0).

## 3. Findings và trạng thái
- Không có finding kỹ thuật nào còn mở trong phạm vi A1.
- Trạng thái gói A1: `SELF_VERIFIED`.
