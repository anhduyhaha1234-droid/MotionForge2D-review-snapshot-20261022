# LONG01 R6c — continuation #3, cùng contract LONG01_R6.md (12/10/2026)

Tiếp tục CÙNG SID/owner/RUN/write-set/revision r6.

- **Your Invocation ID: `{{INVOCATION_ID}}`**
- **Packet SHA256: `{{PACKET_SHA256}}`**

## SỬA LỖI BẮT BUỘC — tên file record (đã gây NEEDS_RECONCILIATION cho R6b)

R6b đã refresh nhầm `evidence/terminal/LONG01-R6-20261012T0810Z-2731.json` (file của invocation #1)
thay vì ghi file MỚI cho chính nó. Từ lượt này:

- Record của invocation NÀY phải nằm ở `C/r6/evidence/terminal/{{INVOCATION_ID}}.json` — đúng từng ký
  tự của Invocation ID ở trên (đây là ID của chính lượt này).
- Trường `invocation_id` trong JSON phải BẰNG tên file đó.
- **KHÔNG refresh/không sửa file record của invocation khác** (giữ nguyên LONG01-R6-…-2731.json).
- Trước khi kết thúc lượt: `ls evidence/terminal/` phải thấy file mang đúng tên invocation này; tự
  kiểm `invocation_id == tên file` và các hash artifact tươi. RECORD-LAST vẫn giữ (record là write cuối).
- Gần ~65/80 turn hoặc sau mốc lớn: refresh record + checkpoint + R6_REMAINING.json.

## Việc tiếp (đúng R6_REMAINING.json của bạn)

1. **S61-tail**: debug `NoneType.get` tại f141 → chạy `r6_keygen.py S0061` cho fids 141..356 (23 key).
2. **S0043**: SAM2 2-chunk (0..538 / 538..1077 re-seed từ centroid mask chunk1) → keys; kiểm totals.
3. **Semantic reviews cho TOÀN BỘ keys**: vision sheets 8-12 key/shot → `r6_gate.write_review`
   (gross errors + spot rim/pose; quality loop đổi theo evidence, tối đa 2 lần cùng cách).
4. **S4 VACE**: rebuild graph đúng `TrimVideoLatent` (KSampler→Trim.samples, WanVaceToVideo.output3→
   trim_amount, Trim→VAEDecode); paired **S62 + S73** cùng windows/refs vs keys-route; actual-ref
   perturb một actor (actor khác/props bảo vệ); peak VRAM/RAM/wall; missing input fail.
5. **S5**: chọn engine theo identity/pose/contact; nhánh thua NOT_SELECTED + lý do.
6. **S6**: propagation event-aligned (fresh-complete; rc!=0/partial/stale BLOCK; no tail-fill) +
   CoTracker paired S34/S61/S73 (tracks[T,N,2]+visibility[T,N] raw + queries + before/contact/hold/release).
7. **S7**: đóng hard excerpts S22-24 S31/33/34/41 S57/59/61 S62/63/64/67/70/73/74 + asset-reskin zero-shots
   S32/35/37/40/42/45/47/49/50/52/54/58/59/60/65/66/74 (giữ chữ; không diffusion glyph) + controls.
8. **S8/S9**: master `R6/outputs/IDENTITY5M_R6_MASTER.mp4` (9000f/640×360/30fps + audio [94,394)s) +
   comparison **source|R5|R6** 1920×360 + QA all54 → matrix 12 rows + `R6_MATRIX_EVIDENCE.json` +
   manifest (hash SAU record) → record đúng tên (mục SỬA LỖI ở trên).

## Nhắc

- Mọi ghi `C/r6/**` + `D/{input,output,temp}/identity5m_20261008/r6/**`; R4/R5 read-only (guard vừa
  xác minh 0 drift — giữ nguyên; kể cả R4 tracks/masks).
- Open P1 chưa đóng thật → `remaining_work` (không thành residual để ép PASS).
- Chạm 80/80 turn → checkpoint + record ĐÚNG TÊN → dừng sạch; Manager resume CÙNG SID.

Bắt đầu ngay từ mục 1.
