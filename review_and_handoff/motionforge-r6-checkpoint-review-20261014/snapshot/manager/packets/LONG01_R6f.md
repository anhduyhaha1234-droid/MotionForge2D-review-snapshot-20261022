# LONG01 R6f — continuation #6 (chặng cuối), cùng contract LONG01_R6.md (12/10/2026)

Tiếp tục CÙNG SID/owner/RUN/write-set/revision r6.

- **Your Invocation ID: `{{INVOCATION_ID}}`**
- **Packet SHA256: `{{PACKET_SHA256}}`**

## RECONCILE R6e (đọc để không lặp)

R6e: 2h15m, chạm 80/80 budget TRƯỚC khi ghi record (lần thứ 3) + để chuỗi bg (pid 37968)
**chết khi turn đóng** → S43/S61 blend = 0. R6e không backfill. Từ lượt này:

- **CADENCE bắt buộc**: sau MỖI batch hoàn tất (S43/S61 propagate, assemble, QA, matrix) —
  **refresh record NGAY** (script riêng cho invocation này; đúng tên `{{INVOCATION_ID}}.json`;
  `invocation_id` == tên; dedupe paths; hash tươi; RECORD-LAST vẫn giữ cho lần ghi cuối cùng).
  KHÔNG để quá 1 batch mà chưa có record. Turn ~55: refresh + checkpoint dù batch chưa xong.
- **KHÔNG phó mặc bg chain qua turn-end**: batch phải chạy TỚI RECEIPT trong turn (poll tới xong)
  hoặc để lại trạng thái + next command rõ trong record. bg process KHÔNG sống qua turn.

## Việc — chặng cuối

1. **S43**: hoàn tất keys cho fids còn thiếu (tới đủ cửa sổ shot; mask đã đủ 1078/entity) →
   **ghi review MỚI** cho các key vừa regen (review cũ đã stale-hash — gate đang chặn đúng
   `SEMANTIC_REVIEW_TAMPERED: S0043_f0901`) → propagate S43 (fresh-complete gate).
2. **S61**: hoàn tất keys tail (f161+ và phần còn thiếu) → reviews mới → propagate S61.
3. **Enumerate 54/54 blends** (hiện ~52; S0099 là fixture — không vào master): điền đủ trước khi ráp.
4. **Assemble**: `python -B scripts/r6_assemble.py && python -B scripts/r6_qa.py && python -B scripts/r6_matrix.py`
   (đã built+compiled; crop inverse 640:360:0:4; audio [94,394)s) → `R6/outputs/IDENTITY5M_R6_MASTER.mp4`
   (9000f/640×360/30fps/300s) + comparison **source|R5|R6** 1920×360.
5. **QA**: vision sheets `evidence/qa/*.png` (all54 head/event/tail + 2s scan + dense contact/entry/
   occlusion/zoom/seams) — xem thật, ghi verdict trung thực; phần chưa xem ghi rõ.
6. **CoTracker paired** S34/S61/S73 (tracks[T,N,2]+visibility raw + queries + before/contact/hold/release).
7. **S9 + record**: matrix 12 rows trung thực + `R6_MATRIX_EVIDENCE.json` + `R6_MANIFEST.json` (hash SAU
   record cuối) → record `TASK_SUBMITTED` **CHỈ KHI** 12 rows thật PASS + đủ 5 kind + không remaining;
   còn P1 mở → `CONTINUE_REQUIRED` với next command cụ thể (không ép PASS, không residual-hóa).

## Nhắc

- Write-set `C/r6/**` + `D/{input,output,temp}/identity5m_20261008/r6/**`; R4/R5 read-only.
- QUALITY_ACCEPTED=0; không tự APPROVED/CLOSED. Dừng sạch, không child sống ngoài ý muốn.

Bắt đầu ngay: record skeleton (đúng tên) → mục 1.
