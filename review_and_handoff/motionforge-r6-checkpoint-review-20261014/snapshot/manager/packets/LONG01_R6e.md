# LONG01 R6e — continuation #5, cùng contract LONG01_R6.md (12/10/2026)

Tiếp tục CÙNG SID/owner/RUN/write-set/revision r6. (Record R6d đã ĐÚNG tên + dedupe ✓ — giữ nguyên kỷ luật này.)

- **Your Invocation ID: `{{INVOCATION_ID}}`**
- **Packet SHA256: `{{PACKET_SHA256}}`**

## Việc tiếp (đúng remaining_work của R6d — 6 mục)

1. **Repair round-2 (3 fids)**: S62 f33 (method delta #2: tighter crop / E6-only edit), S69 f101 (blob
   gần đầu), S72 f71 (cổ biến dạng) → regen keys.
2. **Đóng BLOCKED SHOTS trước propagate**: S21 f61/f96 (giant-head residual — chẩn actor/region trên
   f61), S27 f101-159 tail (white residue + scale), + các shot còn lại trong danh sách record.
3. **S7 zero-shots asset pass**: S32/35/37/40/42/45/47/49/50/52/54/58/59/60/65/66/74 (prop/background
   edit giữ chữ, no diffusion glyph) + **hard-excerpt QA** S22-24 S31/33/34/41 S57/59/61 S62/63/64/67/70/73/74
   + controls S25/26/27/39/68/69/71/72.
4. **S8**: chạy `r6_assemble.py` (đã built+compiled; crop 640:360:0:4 inverse) khi **54/54 blends ready**
   → `R6/outputs/IDENTITY5M_R6_MASTER.mp4` (9000f/640×360/30fps + audio [94,394)s) + comparison
   **source|R5|R6** 1920×360 + QA all54 head/event/tail + 2s scan + dense contact/entry/occlusion/zoom/seams.
5. **S6-tail**: CoTracker paired S34/S61/S73 (tracks[T,N,2]+visibility[T,N] raw + queries +
   before/contact/hold/release) so với outputs đã propagate.
6. **S9**: matrix 12 rows trung thực + `R6_MATRIX_EVIDENCE.json` + `R6_MANIFEST.json` (hash SAU record
   cuối) → record (đúng tên + dedupe như R6d).

## Nhắc

- Propagation: gates đã cài (semantic review artifact-bound); chỉ propagate keys đã qua gate; fail-closed
  (rc!=0/partial/stale ⇒ BLOCK; không tail-fill). Open P1 chưa đóng thật → `remaining_work`.
- Write-set `C/r6/**` + `D/{input,output,temp}/identity5m_20261008/r6/**`; R4/R5 read-only.
- Gần ~65/80 turn hoặc sau mốc lớn: refresh checkpoint + record (đúng tên, dedupe) — record có mặt
  TRƯỚC khi chạm budget. Chạm budget → dừng sạch, Manager resume CÙNG SID.
- QUALITY_ACCEPTED=0; không tự APPROVED/CLOSED.

Bắt đầu ngay từ mục 1.
