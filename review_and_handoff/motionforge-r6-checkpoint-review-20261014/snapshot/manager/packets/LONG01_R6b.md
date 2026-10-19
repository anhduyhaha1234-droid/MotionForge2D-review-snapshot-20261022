# LONG01 R6b — continuation #2, cùng contract LONG01_R6.md (12/10/2026)

Tiếp tục CÙNG SID/owner/RUN/write-set/revision r6. `LONG01_R6.md` vẫn là hợp đồng hiện hành
(§1 restate đã có trong `R6_GATE_RESTATEMENT.md` — giữ hiệu lực; §6 record schema; §7 vận hành).

- **Your Invocation ID: `{{INVOCATION_ID}}`**
- **Packet SHA256: `{{PACKET_SHA256}}`**

## Việc tiếp — đúng 6 mục remaining_work + next command trong checkpoint của bạn

1. **Seeds cho ~27 people-shots còn lại**: vision batch 4 f1-frames/grid (như đã làm với S57/S61/S62),
   đối chiếu nguồn cho từng shot; extend `r6_sam2.SEEDS`; chạy SAM2 r6 cho các shot thiếu:
   S0021 S0025 S0026 S0027 S0028 S0029 S0030 S0033 S0036 S0038 S... (danh sách đầy đủ trong checkpoint).
2. **Key production đủ shot** (`r6_keygen.py <SHOT>` từng shot) + **vision semantic review records**
   (`r6_gate.write_review`) sau mỗi batch — quality loop: rim-bleed + pose-turn nhẹ đã thấy ở S23 f1
   (đổi theo evidence nếu 2 lần không tiến bộ; không seed sweep; reject key sai pose/count/role).
3. **S4 VACE**: rebuild graph có `TrimVideoLatent` (`KSampler→Trim.samples`, `WanVaceToVideo.output3→
   trim_amount`, `Trim→VAEDecode`); paired **S62 + S73** cùng windows/refs vs keys-route đã sửa;
   actual-ref perturb một actor (actor khác/props bảo vệ); đo peak VRAM/RAM/wall; missing input fail.
4. **S6**: propagation event-aligned qua upstream stage2 (fresh-complete check; rc!=0/partial/stale ⇒
   BLOCK; KHÔNG tail-fill) + CoTracker paired S34/S61/S73 (lưu tracks[Т,N,2]+visibility[T,N] raw,
   queries tay-prop, before/contact/hold/release + ảnh so).
5. **S7**: đóng hard excerpts S22-24 S31/33/34/41 S57/59/61 S62/63/64/67/70/73/74; asset reskin
   S40/57/58/59/60 (prop/background edit giữ chữ; KHÔNG diffusion glyph).
6. **S8/S9**: assemble `R6/outputs/IDENTITY5M_R6_MASTER.mp4` (9000f/640×360/30fps/300s + audio
   [94,394)s) + comparison **source|R5|R6** (1920×360 cùng timeline) + QA all54 head/event/tail +2s
   scan + dense contact/entry/occlusion/zoom/seams → matrix 12 rows (trung thực; UNKNOWN blocks) +
   `R6_MATRIX_EVIDENCE.json` + manifest (hash SAU record) + record.

## Nhắc

- RECORD-LAST: refresh record là write cuối; manifest hash sau record cuối. Open P1 nào chưa đóng
  thật → `remaining_work` (không thành residual để ép PASS).
- Mọi ghi `C/r6/**` + `D/{input,output,temp}/identity5m_20261008/r6/**`; R4/R5/MASKS/TRACKS read-only
  (guard đang theo dõi — invocation trước 0 drift, giữ vậy).
- Chạm ranh giới kỹ thuật (~80 turn) → checkpoint + record → dừng sạch; Manager resume CÙNG SID.

Bắt đầu ngay từ mục 1.
