# LONG01 R6 — triển khai đúng tài liệu đã kiểm; sửa đồng bộ; hoàn thiện pilot 5 phút (12/10/2026)

Bạn là **worker duy nhất** của MF-DEMO-LONG-01. Packet này THAY mọi chỉ dẫn trước. R5 đã nộp
nhưng Codex **CHANGES_REQUESTED** trên đúng bytes R5 (master `b8b9a404…`): **10 FAIL + 1 UNKNOWN
(Q11 partial) + 1 PASS engineering** — không phải 12 PASS. R6 là **artifact revision mới của cùng
Task/RUN/owner/counters** — không phải task mới. Giữ TOÀN BỘ finding chưa đóng; không thu nhỏ
thành "sửa halo/glyph".

- Run: `C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long`
- D = `…/tasks/MF-DEMO-LONG-01`; C = `D/corrections/identity5m_20261008`; **R6 = C/r6 (write-set của bạn)**
- **Your Invocation ID: `{{INVOCATION_ID}}`**
- **Packet SHA256: `{{PACKET_SHA256}}`**

## 0. Đọc trước (đúng các file này; chỉ mở source theo T-check đang làm)

- N = `C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-tech-conformance-20261012`:
  `TECHNOLOGY_AUDIT_VI.md`, `TECH_CONFORMANCE_MATRIX.md` (T01–T15), `SESSION_OPENING_PROPOSAL.md`.
  N là yêu cầu kỹ thuật hiện hành; `SOURCE_LOCK_FINAL.json` / `PROOF_RESULTS.json` / `PROOF_SUPPLEMENT.json`
  là pins/proofs tham chiếu (docs/clone/CPU proof KHÔNG phải video đạt).
- O = `…/outputs/motionforge-r5-review-20261012`: `REVIEW_VI.md`, `CORRECTION_MATRIX.md` (12 rows),
  `TECH_DECISION_VI.md`, `SESSION_OPENING_PROPOSAL.md`; `FRESH_PROBES_R5.json` + `COMPARE_0x.jpg` /
  `TEMPORAL_S00xx.jpg` khi xử lý finding tương ứng.
- `P3/CAST_B_SPEC.md`, `STACK/STACK_SOURCE_LOCK.json`, `P/NEWTECH_SOURCE_LOCK.json` (pins giữ nguyên).

## 1. RESTATE GATES trước mọi mutation (bắt buộc — context audit hành động)

Viết `C/r6/checkpoint/R6_GATE_RESTATEMENT.md` TRƯỚC khi sửa/generate bất cứ gì:
(a) liệt kê bằng lời của bạn: gate ở key / propagate / assemble / submit + cache contract + record schema;
(b) các bất biến: fallback giữ CAST refs; visible actor thiếu/rỗng mask ⇒ **FAIL, không passthrough**;
zero-actor phải **explicit** (ZERO_VISIBLE ≠ thiếu dữ liệu); source-copy ≠ reskin; file tồn tại/hash
khớp ≠ chất lượng; RECORD-LAST (record refresh là write cuối); mọi output chỉ r6.
Không restate đúng được ⇒ DỪNG, ghi lý do vào record (`CONTINUE_REQUIRED` + blocker) — không tự đoán.

## 2. Findings phải đóng (đọc file gốc để có đủ ngữ cảnh)

**R5-F01** (P1) ledger/binding giữ người nguồn hoặc tạo người không có — `r5_storyboard.py:45` fallback
stale actors khi rỗng; S74 ghi E1/E2 cho cảnh tài liệu; S57 entities=[] dù phần đầu có người;
`r5_keygen.py:29` alias S62 E1/E2=None, S63/67/73 E2=None → `UNBOUND_ABSENT`, caller giữ source.
**R5-F02** (P1) custom compositor thay upstream stitch — `r5_keygen.py:187` `composite_diff_limited`;
`r5_adapter.py:86` có stitch upstream nhưng không được gọi; resize+alpha ở `r5_adapter.py:153`.
**R5-F03** (P1) whole-frame multi-ref phá spatial binding — `r5_graph.py:90` entities[:3];
`r5_common.py:79` left/right theo thứ tự list; 26-shot whole route; corr 0.40 không bắt S33/S64/S70/S74.
**R5-F04** (P1) semantic gate chưa nối — `r5_assemble.py:60` chỉ exists/count; keygen/propagate không
đòi review artifact-bound.
**R5-F05** (P1) cache/deps — `r5_keygen.py:243` skip theo shot/fid trong receipt; `:205` deps theo
basename không hash; 395/608 CAST hash entries null.
**R5-F06** (P1) VACE graph thiếu TrimVideoLatent — `r5_vace.py:89` KSampler→VAEDecode; 81→85 frames;
chỉ S73, không S62, không actual-ref perturb.
**R5-F07** (P1) propagation grid mất event — `r5_propagate.py:60` 1+n*itv; CoTracker S34 81vs220 không
paired; `:85` tail materialize có thể che rc!=0.
**R5-F08** (P1) evidence/closure — manifest con 2148/2149 (R5d terminal stale); Manager R5e step4
chuyển residual khỏi remaining_work (sai); Manager chưa vision-review. (Manager đã preserve/reconcile
trong `manager/evidence/r6/incident_reconcile/`; bạn KHÔNG sửa gì ở đây.)
**R5-F09** (P2) Q11 race proof — ĐÃ do Manager đóng ở R6 bằng suite rendezvous thật (34/34 + 51/51) —
bạn không cần làm Q11, chỉ giữ nguyên contract.
**T-F01** (P1) SAM2 ghi `R4/tracks/SAM2_<shot>.json` (`r5_sam2_excerpt.py:148`) — R6: **mọi** mask/track/
receipt/cache chỉ r6. **T-F02** (P1) canvas/provenance — S61 reused 104×640×368 + 252×640×360; canonical
640×360 + explicit pad4/4→368 MỘT lần + inverse; `f0001` thực là source frame0 — KHÔNG shift 1 frame;
empty mask không chứng minh absent; **không** positional fallback khi thiếu mask (`r5_vace.py:43/52`).
**T-F03** (P1) Rerender chỉ stage2 (`video_blend`) — không claim stage1; event keys đúng thời điểm,
không snap grid; fail-closed với rc!=0/partial/stale; flow cache namespace theo input; wrapper phải
xác nhận fresh complete outputs dù outer rc=0. **T-F04** (P1) CoTracker thiếu raw visibility — lưu
tracks+visibility per-frame, paired windows, queries tay-prop semantic. **T-F05** (=F06 VACE).
**T-F06** (P2) `p1_cuts.py` comment lệch code — chỉ ghi deferred note; KHÔNG rerun ASR/cut; 224/224
candidates giữ.

**Scene-level bắt buộc sửa (review — không được coi MINOR):** S33 thêm người đứng trên giường;
S61 giant B02 sau xe trong khi hai người nguồn vẫn đi; S70 sai người/vị trí; S74 close-up giấy thành
hai CAST portraits; S43–44/53/55 tay-cốc/sổ mất hoặc thay, ghế/thân người đổi hình và màu; S22
3.2–6.97s + S23 7.03–11.07s + S24 đổi góc mặt, ghost viền người cũ, tay/phone/body chồng; S31
36.0–46.33s + S41 107.5–119.27s B03 portrait sai vùng + nhân vật cũ dưới lớp mới + pose ngồi thành
bust; S57/62 còn diện mạo nguồn ở frame nhìn rõ; S73 mất pickup/hold sổ + người khuất một phần;
S42 glyph panel (P2 — giữ open nếu chưa đạt).

**T01–T15 map vào công việc (chi tiết đọc N/TECH_CONFORMANCE_MATRIX.md):** T01 ASR/cuts frozen —
chỉ bổ sung ledger chứng cứ source, không rerun full; T02 SAM2 (S1: canonical canvas, fixture
entry/occlusion/missing/empty, R4 tracks unchanged); T03 FLUX (S3); T04 crop+stitch upstream (S3);
T05 VACE trim+paired (S4); T06 Rerender stage2 + fail-closed (S6); T07 flow-cache namespace (S2/S6);
T08 CoTracker tracks+visibility (S6); T09 ProPainter conditional NOT_NEEDED có lý do (chỉ chạy nếu
cần clean plate, proof thật); T10 MoCha chỉ sau causal failure trên valid keys/VACE, kiểm deps/VRAM
trong scope r6; T11 FFmpeg assemble gates trước encoder (S8/S9); T12 VBench chỉ triage — không cài;
T13/T14 đã do Manager xong (Q11 v3) — bạn giữ contract; T15 resource measurement tách allocated/
reserved/process-tree/sampled (S8). Kết luận từng công nghệ phải ghi SOURCE_READY/ENV_READY/
SMOKE_PASS/SOURCE_UNIT_PASS/PILOT_PASS — docs/clone/unit-test KHÔNG tự là PASS.

## 3. Thứ tự thực thi (dependency; đạt thì tự đi tiếp, không đợi duyệt từng ảnh)

**S0** restate gates (§1) → **S1** source ledger/binding/canvas: ledger theo frame/event phân biệt
ZERO_VISIBLE / FULLY_OCCLUDED / UNKNOWN; S74 = tài liệu không người (zero explicit); S57 đầu có người;
S62 E1/E2 visible phải reskin (không UNBOUND_ABSENT); S31/41 clerk B03 đúng; S63/67/73 giữ người phía
sau lộ một phần; S21 một UNKNOWN không làm mất known identities. Cast: B01→E1, B02→E2 (E8 alias E2),
B03→E3, B04→E4 provisional (đối chiếu nguồn), B05/B06/B07→E5/E6/E7. Mask canonical + SAM2 per-object
đủ mọi visible actor/frame (entry/occlusion prompt correction, reset tại cut); missing/empty khi
visible ⇒ FAIL trước model. → **S2** gates+cache contract: semantic review artifact-bound (reviewer,
hash, input lineage, expected actors/contact, frame evidence) ở key/propagate/assemble/submit;
absent/stale/tampered/UNKNOWN ⇒ block. Cache key = exact consumed source/span/refs/masks/graph/model/
settings/approved keys; same-path same-size mutation invalidate đúng downstream; unchanged accepted
reuse. → **S3** crop+stitch upstream THẬT: dùng CẢ upstream crop VÀ stitch cùng transform (pin
8584b08d, source ở `P/upstream/`); giữ aspect, interior opaque; blend chỉ biên có bounds, bảo vệ
props/actor bên cạnh; synthetic landmark roundtrip + outside-region diff TRƯỚC generate; key sai
pose/count/role ⇒ reject trước propagate. FLUX.2 klein 4B giữ baseline (4 steps/Euler/CFG1);
per-actor edit đúng pose/view nguồn; front/profile cùng ID nối thật mọi nhánh (normal/repair/fallback);
KHÔNG whole-frame multi-ref cho actor thiếu spatial binding; vượt ref limit ⇒ multi-pass z-order +
vùng bảo vệ; không STYLE image có người/cảnh. Test perturb từng CAST ref: actor mục tiêu đổi, người
bên cạnh không. → **S4** VACE đúng native contract: graph official reference-v2v với
`KSampler→TrimVideoLatent.samples`, `WanVaceToVideo.output3→TrimVideoLatent.trim_amount`,
`TrimVideoLatent→VAEDecode`; 4n+1 chunks, overlap seam-check, 30fps exact frame map, pad 640×360→368
crop đúng; control_video/control_masks/reference_image nối thật; mask lossless PNG (hoặc decoded-equivalence
proof); missing input ⇒ fail. Paired **S62 (nhiều vai) + S73 (tay-sổ)** cùng windows/refs với keys-route
đã sửa + actual-ref perturb + peak VRAM/RAM/wall. → **S5** chọn engine theo identity/pose/contact
(không theo tốc độ); nhánh thua ghi NOT_SELECTED + lý do. → **S6** propagation theo event: event keys
đúng thời điểm (không bị grid bỏ/trễ); chia internal range theo event/cut, giữ exact time + source
cuts khi ghép; rc!=0/partial/stale ⇒ block (không tail-fill); CoTracker paired S34 phone / S61
entry-camera / S73 tay-sổ (tracks+visibility raw + before/contact/hold/release + ảnh so trực tiếp).
→ **S7** đóng hard excerpts: S22–24, S31/33/34/41, S57/59/61, S62/63/64/67/70/73/74; giữ controls
S25/26/27/39/68/69/71/72. S40/57/58/59/60 = reskin thật (prop/background asset edit, giữ chữ đã kiểm,
không giao diffusion bịa glyph). → **S8** đủ 54 shots/5 phút: master `R6/outputs/IDENTITY5M_R6_MASTER.mp4`
(640×360/30fps/9000f/300s + audio nguồn [94,394)s) + comparison **source|R5|R6** (1920×360, cùng
frame/timeline) + QA: all54 head/event/tail + scan 2s + dense quanh contact/entry/occlusion/zoom/seams.
→ **S9** matrix 12 rows + R6_MATRIX_EVIDENCE.json + manifest (hash SAU record cuối) + record (§6).

## 4. Negative probes bắt buộc (fresh; dùng bytes R5 fail + controls)

zero actors vs missing ledger; partially visible vs fully occluded; duplicate/full-overlap masks;
empty mask while source visible; same ref-path mutation (same-path same-size); mismatched semantic
hash; source-copy; re-encoded known-bad R5 frames; engine rc!=0 + stale output; event key off-grid;
nested manifest stale terminal; valid unchanged reuse (control). Mỗi probe nêu vị trí/nguồn + kết quả.

## 5. Deliverables (dưới `C/r6/`)

- `outputs/IDENTITY5M_R6_MASTER.mp4` + `outputs/IDENTITY5M_R6_COMPARISON.mp4` (source|R5|R6).
- `source_actor_ledger.jsonl`, `storyboard/`, `cast_atlas.json`, `masks/` (r6-only, canonical contract),
  event map; graphs + commands + model/upstream hashes; resource receipts (allocated/reserved peak
  trong process inference + process-tree RAM + sampled GPU tách riêng).
- `evidence/matrix.json` = `{"rows": {Q01..Q12: PASS|FAIL|UNKNOWN}}` (trung thực; UNKNOWN blocks) +
  `evidence/R6_MATRIX_EVIDENCE.json` (cho từng row: source/function/test/command/owner, expected counts,
  output hashes; Q11 = Manager evidence pack path).
- `checkpoint/R6_CHECKPOINT.md` (append qua các invocation), `receipts/R6_MANIFEST.json`, adoption
  matrix (SOURCE_READY/ENV_READY/SMOKE_PASS/SOURCE_UNIT_PASS/PILOT_PASS + actual consumer/hash/output
  cho CropAndStitch/SAM2/Rerender/CoTracker/VACE; ProPainter/MoCha conditional NOT_NEEDED có lý do).
- **Open P1 nào chưa đóng thật thì để trong `remaining_work`** (không chuyển thành residual để ép PASS).

## 6. Terminal record (schema r6 — RECORD-LAST)

Ghi tại `C/r6/evidence/terminal/{{INVOCATION_ID}}.json` (≤1MB, no duplicate keys):
`schema_version "1.0"`, `run_id "20261005T1643Z-wan-long"`, `task_id "MF-DEMO-LONG-01"`,
**`revision "r6"`**, `owner_sid "20261007_234033_cc0b6d"`, `invocation_id`, `packet_sha256` (tokens
trên), `status` (CONTINUE_REQUIRED | TASK_SUBMITTED | USER_STOP | BLOCKED), `reason`,
`remaining_work` (rỗng CHỈ khi TASK_SUBMITTED), `artifacts` [{kind master/comparison/matrix/
checkpoint/receipts/other, path tuyệt đối trong C/r6, sha256 tươi}], `matrix` đúng 12 khóa.
`TASK_SUBMITTED` chỉ khi 12 rows PASS THẬT + đủ 5 kind + không remaining work. **Record refresh là
write CUỐI CÙNG của invocation** (RECORD-LAST); mọi artifact list phải được hash SAU khi mọi w ghi
dừng. Manifest cũng phải tính hash sau record cuối (bài học R5d). Không tự APPROVED/CLOSED.

## 7. Vận hành

- Write-set: `C/r6/**` + `D/{input,output,temp}/identity5m_20261008/r6/**` — KHÔNG GÌ KHÁC.
  R4/R5 (kể cả R4 tracks/masks → đã vào guard), W7/C1/C2/R3, source/style/CAST board, MAIN,
  INTEGRATION, reviewer packets: read-only tuyệt đối. Mọi mask/track/receipt/cache → r6.
- PYTHONDONTWRITEBYTECODE=1; patch-only cho file tồn tại; file mới trong allowlist.
- WIP1/GPU1; model tuần tự; đo peak thật; không unload/kill dịch vụ khác; không cài framework/weights
  mới (reuse vendor/models read-only); licenses giữ (SAM2 Apache2; CoTracker/Rerender/ProPainter
  noncommercial — eval nội bộ).
- Heartbeat ≥20'; 8' không tiến độ → audit. Transient 502/503/504: backoff 5', reconcile, retry same
  route/owner. Hết context/turns (technical bound) ⇒ checkpoint + `CONTINUE_REQUIRED` + next command
  CỤ THỂ; Manager resume CÙNG SID. Không PM budget/cap. Không seed sweep; 2 lần cùng cách không tiến
  bộ ⇒ method delta từ evidence.
- Dừng sạch: không render child sống ngoài ý muốn; mọi ghi trong write-set.

Bắt đầu: §0 đọc → `R6_GATE_RESTATEMENT.md` → S1…S9. Đích: frozen pilot R6 đủ contract hoặc
`CONTINUE_REQUIRED` với next action thật.
