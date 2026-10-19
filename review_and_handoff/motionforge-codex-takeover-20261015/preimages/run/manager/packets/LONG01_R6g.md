# LONG01 R6g — continuation sau checkpoint review 14/10 (cùng task/RUN/revision r6)

Bạn là **worker duy nhất** của MF-DEMO-LONG-01. Codex đã review **checkpoint R6f**: CHANGES_REQUESTED —
**9 FAIL + 2 UNKNOWN + 1 PASS engineering** trên master `e3107a52…` (KHÔNG phải submission cuối; UNKNOWN
không được waive). R6g là continuation của cùng revision r6, cùng counter, **không** viết lại từ đầu:
sửa nguyên nhân F02–F09, đóng excerpts F01, chỉ tái tạo phần bị invalidated.

- **Your Invocation ID: `{{INVOCATION_ID}}`**
- **Packet SHA256: `{{PACKET_SHA256}}`**
- **Namespace MỚI của lượt này: `R6/continuations/{{INVOCATION_ID}}/`** cho mọi output/cache/reviews/
  QA/manifest mới. R6f master/comparison + old receipts/terminals/evidence/reviews đã **FROZEN** —
  không overwrite, không "làm khớp hash" lịch sử.

## 0. Đọc trước (bắt buộc; giữ T01–T15 + canonical 12Q)

- U = `C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-r6-checkpoint-review-20261014`:
  `REVIEW_VI.md` (F01–F09), `CORRECTION_MATRIX.md` (12Q canonical: Q01 identity/refs/pose; Q02 role/count/
  visibility/ledger; Q03 contact/events; Q04 ghost/props/background; Q05 semantic gates actual consumers;
  Q06 VACE paired/conformance; Q07 dependencies/cache; Q08 AV/frames/cuts; Q09 Manager held-out QA;
  Q10 manifests/terminal truth; Q11 harness concurrency; Q12 upstream adoption), `FINDING_LOCATIONS.json`,
  `FRESH_PROBES.json`, `PROBE_SUPPLEMENT.json`, `SESSION_OPENING_PROPOSAL.md`.
- N tech packet + pins như trước (giữ nguyên mọi pin; chỉ mở source theo finding đang sửa).
- Quota đã kiểm HEALTHY (Manager probe 14/10 07:19Z, HTTP 200) — nhưng nếu giữa lượt gặp HTTP503 bọc 429
  weekly trở lại: **DỪNG AN TOÀN** — ghi checkpoint + record (blocker exact error text) rồi kết thúc sạch;
  KHÔNG fake progress, KHÔNG đổi model/route.

## 1. RECONCILE R6f (những gì đã khóa)

- R6f dừng vì quota; receipt NEEDS_RECONCILIATION; terminal giữa lượt (40/42 hashes — mismatch
  `scripts/r6_qa.py` + `receipts/R6_COTRACKER_RUNS.jsonl`; remaining_work nói S43/S49/assembly dù master
  đã xuất → **stale, bỏ qua, không tin**). Master/comparison verified decode-clean (46,138,723 B /
  66,667,098 B; audio lag 0ms). Manager đã preserve + append R6F_RECONCILE; registry đã sửa.
- TIẾN BỘ có thật đừng phá: S74 đã về tài liệu (zero-actor explicit), S70 tốt hơn, một số mặt/viền sạch
  hơn, adapter gọi upstream `stitch_magic_im`, VACE có TrimVideoLatent + 3 trials. **Giữ controls
  S25/26/27/39/68/69/71/72 và S74.**

## 2. RESTATE trước mọi mutation (bắt buộc — Manager sẽ đọc)

Viết `R6/continuations/{{INVOCATION_ID}}/R6G_RESTATE.md` TRƯỚC khi sửa/generate, bằng lời của bạn:
(a) pilot [2820,11820)/9000f/30fps/640×360/source audio 94–394s; CAST B/flat2D, write-set
`R6/**` + `D/{input,output,temp}/identity5m_20261008/r6/**` (namespace continuations cho outputs mới);
(b) **định nghĩa canonical 12Q** (đúng U/CORRECTION_MATRIX — không remap);
(c) phân biệt identity / pose / count / contact / event-fid / visibility classes (ZERO_VISIBLE /
FULLY_OCCLUDED / UNKNOWN); (d) consumer gate ở key→propagate→assemble→submit; immutable records;
(e) danh sách F01–F09 + next command đầu tiên của bạn.
Không restate đúng được → DỪNG, ghi record CONTINUE_REQUIRED + blocker (không tự đoán).

## 3. F02–F09 — microfixes fail-closed (đọc U để có số dòng chính xác; preimage đã pin)

- **F02 gate=true**: `r6_assemble.py` phải **import + call `gate_assemble`** trước khi encode (hiện chỉ
  đếm blend). `r6_gate.py`: `review.inputs`/`expected`/`reviewer`/frame-evidence là **bắt buộc** —
  `{}` rỗng phải REJECT (probe ảnh trắng + record trống hiện được ACCEPTED = lỗi). Final blend phải có
  semantic review trên đúng output hashes; gate key không thay review final. Test: encoder-spy — review
  thiếu/sai/stale/UNKNOWN ⇒ encoder KHÔNG được gọi; valid control qua; negative qua actual key/propagate/
  assemble/submit.
- **F03 event đúng fid**: bỏ grid `1,11,21,…` trong `r6_propagate.py`; bỏ dung sai ±5 trong `r6_gate.py`.
  Event keys = boundary nguồn đúng frame (S61 f103/f105/f107; S21 f42/f44/f46; keys cuối shot như dữ
  liệu event). Test off-grid: renderer tiêu thụ ĐÚNG fid + đúng hash; các range ghép không thiếu/lặp frame.
- **F04 CoTracker thật**: sửa reader đọc `event_map.shots[sid]` (không `[sid]`), dùng `f`/`event`/`contacts`
  (không f0/f1/kind); windows phải KHÁC rỗng (S34/S61/S73); queries semantic hand/prop theo landmark
  từng clip (không grid 8×8 frame0); tọa độ riêng source/output; S73 bổ sung contact annotation vào
  event map từ nguồn; reject length mismatch (bỏ `min()` âm thầm); lưu tracks+visibility+queries+raw
  windows + evidence ảnh before/contact/hold/release.
- **F05 freshness thật**: bỏ kiểm max-mtime. Fresh = namespace theo content+invocation; **verify TẤT CẢ
  frame kỳ vọng** tồn tại mới + đúng mapping + child outcomes + full decode; wrapper phải chặn inner
  failure dù outer rc0 (probe tail-fill 9-cũ+1-mới hiện được nhận `fresh:true` = lỗi). Test: partial/
  stale/missing frame/inner-failure block; unchanged-completed reuse chỉ khi chứng minh provenance.
- **F06 cache khóa bytes**: cache identity gồm exact consumed source bytes/span+frame, model, graph/
  settings, refs/views/masks/keys/reviews (hiện thiếu source+model — probe same-path same-size đổi
  source+model vẫn được `(True,'ok')` = lỗi); actual skip consumer kiểm hiện trạng settings của chính
  nó, không chỉ deps tự ghi; propagation không tái dùng `video/tmp/out_*` cùng shot root mù quáng.
- **F07 matrix/QA đúng chuẩn**: `r6_matrix.py` giữ **canonical Q01–Q12** (không remap Q01/Q08/Q12),
  không PASS hardcoded, enum chỉ PASS/FAIL/UNKNOWN; xuất `R6_MATRIX_EVIDENCE.json` + `R6_MANIFEST.json`
  (recursive hashes, hash SAU record cuối, không cycle). `r6_qa.py`: đọc event map đúng level; làm
  **2s-scan + dense event** như docstring; vision hỏi đúng identity/role/action/contact/style (không chỉ
  "cùng cảnh/đen/rác"); sheet timeout/503 ⇒ ghi UNKNOWN thật.
- **F08 records**: terminal mới CHỈ ở `R6/evidence/terminal/{{INVOCATION_ID}}.json` (đúng tên + dedupe
  + RECORD-LAST + hash tươi; đã dùng đúng ở R6d — giữ kỷ luật). Checkpoint mới trong namespace nói đúng
  current bytes/remaining. P1/UNKNOWN còn mở nằm trong `remaining_work`.
- **F09 reproduce command**: sửa `-ss 300` trước input master trong `r6_assemble.py` (probe: seek tới
  cuối = 0 decoded). Command tái tạo phải start frame0; comparison mới: source94s | R5frame0 | R6g
  frame0, cùng frame/timeline; kiểm 9000f cả 3 nguồn.

## 4. F01 — pixels: hard excerpts trước, rồi mới 54 shots

Sửa NGUYÊN NHÂN (mask/pose/binding/z-order) rồi chỉ regenerate downstream bị ảnh hưởng; phần valid tái
dùng read-only theo exact hashes (không render lại mù):

- **S33 t≈77.7–80.5s**: nguồn = người NẰM nhỏ trên giường; KHÔNG thêm đầu lớn dựng đứng; đầu nguồn phải
  được reskin tại chỗ (mask người nằm), không giữ đầu nguồn.
- **S61 t≈244.2–246.5s**: hai mặt nguồn cạnh xe phải được reskin (không còn mặt nguồn), KHÔNG thêm
  portrait lớn phía sau; giữ 2 người đi + xe.
- **S73 t≈294.0–295.3s**: giữ sổ xanh + động tác pick/hold/release của người bên phải; không còn
  silhouette mặt nguồn sau actor; người khuất còn lộ phải giữ.
- S22 t≈4.2–5.2s / S31 t≈41.17s / S41 t≈113.4s: giảm ghost + đúng hướng đầu (không chồng mặt).
  S62 entry: reskin đầy đủ (hết mặt nguồn). S63 t≈261.2s / S64 t≈262.3s: đúng role/occlusion.
  S57 t≈220.1s: xe phải flat2D đồng nhất (hiện còn ảnh chụp).
- Sau excerpts: verify controls S25/26/27/39/68/69/71/72 + S74 không regression; rồi đủ 54 shots →
  master mới trong namespace (9000f/640×360/30fps/300s + audio [94,394)s) + comparison
  source|R5|R6g → QA (head/event/tail + 2s scan + dense contact/occlusion/zoom/key/seam; phần chưa
  xem ghi UNKNOWN).

## 5. Giữ đúng upstream/pins (đọc N khi cần; không mở vòng nghiên cứu)

FLUX klein4B distilled 4steps/Euler/CFG1; SAM2 pin 2b90b9f (canonical 640×360, pad368 một lần/inverse,
output r6, không ghi R4 tracks/masks, không positional fallback); CropAndStitch 8584b08d (upstream crop+
stitch thật, geometry roundtrip/outside-region invariant); Rerender dfaf9d88/EbSynth 02ec8c4/GMFlow
af2d869 (stage2 only; inner-failure guard theo F03/F05/F06); VACE 1.3B local: bảo toàn trial S73 base/
perturb + S62; verify graph đúng (KSampler→TrimVideoLatent.samples, output3→trim_amount, Trim→VAEDecode;
không cắt 4 decoded frames; không rerun chỉ vì UNKNOWN khi proof kiểm được từ bytes); CoTracker 82e02e8
theo F04; ProPainter e870e793 chỉ khi cần clean plate (không thì NOT_NEEDED có lý do); MoCha fallback
CHỈ sau causal failure trên valid routes (workflow pin P3/vendor_review/.../wanvideo_2_1_14B_MoCha_replace_subject_KJ_02.json,
wrapper 088128b2; kiểm deps/VRAM trong scope). ASR/cuts/transcript frozen; VBench chỉ triage. Licenses
giữ (CoTracker/Rerender/ProPainter noncommercial). GPU1 tuần tự; đo allocated/reserved trong process
thật + sampled NVML + RAM tách biệt (CoTracker 18–21GB là số đo shared memory — ghi rõ cách đo, không
gọi physical peak; VACE client 0 ≠ server peak).

## 6. Vận hành

- Write-set: `R6/**` (bounded patch cho scripts/ledger/storyboard hiện hữu, preimage; namespace
  `R6/continuations/{{INVOCATION_ID}}/**` cho outputs/cache/reviews/QA/manifest mới) +
  `D/{input,output,temp}/identity5m_20261008/r6/**`. Old R6f media/terminals/receipts/evidence/reviews:
  READ-ONLY. MAIN/INTEGRATION/prod/tests/DB/source/style/CAST/W7/C1/C2/R3/R4/R5/U/N/O/P/STACK/P3
  protected. PYTHONDONTWRITEBYTECODE=1.
- CADENCE: sau MỖI batch (microfix test / excerpt / propagate / assemble) refresh record (đúng tên,
  dedupe, hash tươi). ~55 turn: refresh + checkpoint. bg process KHÔNG sống qua turn-end — mọi batch
  chạy tới receipt TRONG turn.
- Heartbeat 20′; 8′ không progress → audit. Transient 502/503/504: backoff 5′, reconcile, retry same
  route/owner. 429/quota/auth: DỪNG + record blocker (exact error), không retry mù.
- No PM budget/cap; technical boundary → checkpoint + CONTINUE_REQUIRED (next command cụ thể) + resume
  cùng SID. Hai lượt cùng cách không tiến bộ ⇒ method delta theo evidence (không seed sweep).
  QUALITY_ACCEPTED=0; không tự APPROVED/CLOSED.

## 7. Terminal record (đúng chuẩn r6)

`R6/evidence/terminal/{{INVOCATION_ID}}.json` — schema như R6f (run_id/task_id/revision "r6"/owner_sid/
invocation_id/packet_sha256/status/reason/remaining_work/artifacts/matrix). `TASK_SUBMITTED` **CHỈ KHI**
12 rows PASS thật + đủ 5 kind + remaining rỗng; còn FAIL/UNKNOWN/P1 → `CONTINUE_REQUIRED` với next
command cụ thể (hoặc `NEEDS_RECONCILIATION` nếu lỗi binding) — không ép PASS, không residue-hóa.
Manager sẽ held-out QA độc lập + verify + đóng gói Codex.

Bắt đầu ngay: §0 đọc → §2 restate → F02–F09 microfixes (mỗi fix + test) → F01 excerpts → 54 shots →
namespace master/comparison/QA → record.
