# LONG01 R6d — continuation #4, cùng contract LONG01_R6.md (12/10/2026)

Tiếp tục CÙNG SID/owner/RUN/write-set/revision r6.

- **Your Invocation ID: `{{INVOCATION_ID}}`**
- **Packet SHA256: `{{PACKET_SHA256}}`**

## SỬA LỖI BẮT BUỘC (nhỏ, gây NR cho R6c)

Record R6c đã đúng TÊN invocation ✓ nhưng `artifacts` có **cùng một path xuất hiện 2 lần**
(`receipts/R6_LEDGER_VALIDATION.json` ×2, kind "other") → validator: *"one file cannot impersonate
multiple deliverables"* → NR. Từ lượt này:

- Trước khi ghi record: **dedupe artifacts** — mỗi path tuyệt đối chỉ xuất hiện MỘT lần với MỘT kind
  (`sorted(set)` theo path; nếu một file muốn đóng 2 vai, chọn vai chính, đừng list 2 dòng).
- Tự kiểm bằng helper trước write: `len(paths) == len(set(paths))`; khi TASK_SUBMITTED còn phải có
  ĐÚNG một master/comparison/matrix/checkpoint/receipts, các path khác kind "other", tất cả nằm trong C/r6.
- Các quy tắc record khác giữ nguyên (đúng tên `{{INVOCATION_ID}}.json`, `invocation_id` == tên file,
  RECORD-LAST, hash tươi).

## Việc tiếp (7 mục remaining_work của bạn)

1. Hoàn tất **6 review còn lại** (S67/69/70/71/72/73) + ghi **per-key review records** vào r6_gate.
2. **Repair queue theo fid** (đúng list đã ghi: pose/face S25 f121/f125, S30 f51, S68 f21…; outfit
   flicker S39/S55/S56/S68; S55 props f71/111/221/397; S63 f1/3/21/28; S62 f33; S41 E2 f123+ =
   source-verify trước khi sửa; z-order/tail residuals S27 f101-159) — method delta nếu 2 lần không tiến bộ.
3. **S5**: đối chiếu VACE vs keys-route (7 windows S73/S62 + perturb đã chạy) → chọn engine theo
   identity/pose/contact; nhánh thua ghi NOT_SELECTED + lý do; nếu cần thêm paired window/perturb khác
   thì chạy tiếp theo contract (không cắt decoded frames).
4. **S6**: propagation event-aligned (fresh-complete; rc!=0/partial/stale BLOCK; no tail-fill) +
   CoTracker paired S34/S61/S73 (tracks[T,N,2] + visibility[T,N] raw + queries + before/contact/hold/release).
5. **S7**: hard excerpts + **asset-reskin zero-shots** S32/35/37/40/42/45/47/49/50/52/54/58/59/60/65/66/74
   (prop/background edit, giữ chữ; no diffusion glyph) + controls S25/26/27/39/68/69/71/72.
6. **S8**: master `R6/outputs/IDENTITY5M_R6_MASTER.mp4` (9000f/640×360/30fps + audio [94,394)s) +
   comparison **source|R5|R6** 1920×360 + QA all54 head/event/tail + 2s scan + dense contact/entry/occlusion/zoom/seams.
7. **S9**: matrix 12 rows trung thực + `R6_MATRIX_EVIDENCE.json` + manifest (hash SAU record) + record
   (đúng tên + dedupe theo mục SỬA LỖI).

## Nhắc

- Write-set `C/r6/**` + `D/{input,output,temp}/identity5m_20261008/r6/**`; R4/R5 read-only.
- Open P1 chưa đóng thật → `remaining_work`; không tự APPROVED/CLOSED; QUALITY_ACCEPTED=0.
- Gần ~65/80 turn hoặc sau mốc lớn: refresh checkpoint + record (đúng path, dedupe) — ưu tiên record
  có mặt TRƯỚC khi chạm budget.

Bắt đầu ngay: dedupe-note + mục 1.
