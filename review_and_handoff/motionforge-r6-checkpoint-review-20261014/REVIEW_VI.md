# MotionForge2D — review checkpoint R6f, 14/10/2026

**Đã chạy từ prompt công nghệ ngày 12/10: có, 6 invocation R6 → R6f. Chưa nộp hoàn tất và chưa được duyệt. Kết luận độc lập trên checkpoint: CHANGES_REQUESTED.**

## Trạng thái xác minh

- Task `MF-DEMO-LONG-01`, RUN `20261005T1643Z-wan-long`; Manager `20261012_002032_daa36c`, worker `20261007_234033_cc0b6d`.
- R6f chạy 01:17:26–03:17:07 ngày **13/10, giờ Việt Nam/Thái Lan (UTC+7)**. Receipt ghi `NEEDS_RECONCILIATION`, exit 0 không có nghĩa đã xong. Terminal giữa lượt ghi `CONTINUE_REQUIRED`, cả 12Q vẫn `UNKNOWN`.
- Nguyên nhân dừng cuối: HTTP 503 bọc lỗi **429 weekly usage limit** của provider. Log đưa hai mốc reset 13/10 09:16:04Z và 07:09:48Z. Các mốc đã qua tại review này nhưng **chưa có phép thử xác nhận quota/route đã phục hồi**. Codex không gọi inference để thử và không tự resume.
- Manager chưa xử lý xong callback R6f: DB read-only thấy assistant cuối vẫn báo “R6f đang chạy”; user callback sau đó báo đã kết thúc. Registry vẫn ghi `R6_RUNNING` nên đã cũ. Heartbeat là tiến trình còn sống, **không phải bằng chứng worker đang làm việc**.
- Snapshot 14/10 10:49 UTC+7: queue Comfy rỗng, không thấy task worker/renderer; 6 lease R6 đều `RELEASED`. Comfy server và Hermes desktop vẫn mở; không can thiệp chúng.
- Context DB: Manager 402 active/319 compacted, worker 586 active/4882 compacted; đây là **message counts**, không phải tokens hoặc số lần compaction.
- MAIN `master@a40e368f7c47c232cf2eeed9fb185c5972cb98ba` còn dirty; INTEGRATION `codex/mf-end-integration-0928@a52fca897906fd61a088016dd802718fdf06d217` sạch. 1.346 path được chọn từ protected set và PM authority không có SHA drift so với baseline R5 review đã ghi; không suy rộng thành kiểm mọi file của toàn máy.

## Bytes đã có và phần kiểm độc lập

| Artifact | SHA-256 | Kết quả |
|---|---|---|
| R6 master, 46.138.723 bytes | `e3107a52c9f10bc36faf7d5aa3aa2e4c4186edae3cd916c52dff9b24eed9e48e` | 640×360, 30fps, 9.000 frame metadata, video/audio 300s; full decode rc0 |
| R6 comparison, 66.667.098 bytes | `f11f43becf58fa5d9ada18af4ab9dcaac494e47ed8b4d8b41fb87bbe33b140a8` | 1920×360, 30fps, 9.000 frame metadata, 300s; decode rc0 |

Audio PCM đầu/giữa/cuối: lag tốt nhất **0ms**, correlation 0,99913 / 0,99962 / 0,99938. Không tuyên bố đã nghe hoặc xem liên tục 5 phút.

Reviewer tự decode frame chính xác, xem **54 midpoint + 23 khung bổ sung**, mỗi hàng source | R5 | R6. Xem `VISUAL_INDEX.json` và `visual/contact_01.jpg` đến `contact_09.jpg`. Timestamp trong ảnh là thời gian pilot; cộng 94s để ra thời gian nguồn. Probe chỉ chạy CPU/file fixture ở output reviewer, không chạy Hermes/GPU hay sửa production.

Tiến bộ có thật: S74 đã trở về tài liệu, không còn hai người như R5; S70 ít sai bố cục hơn ở mẫu; một số mặt/viền sạch hơn. Script adapter hiện có gọi upstream `stitch_magic_im`; VACE script/receipts đã có `TrimVideoLatent` và ba trial. Đây chưa phải chứng minh toàn pilot đạt; không chạy lại inference và chưa đóng độc lập toàn Q06/Q11.

## Findings cần correction

Paths dưới đây tương đối với `R6 = RUN/tasks/MF-DEMO-LONG-01/corrections/identity5m_20261008/r6`. Bản source tại thời điểm review được lưu trong `snapshot/`, số dòng và hash trong `FINDING_LOCATIONS.json` / `AUDIT.json`. Media findings gắn exact master SHA ở trên.

### R6-F01 — P1: final pixels vẫn sai người, pose và hành động

- **S33, t=77,700 / 78,700 / 79,700 / 80,500s**: nguồn có người nằm nhỏ trên giường; R6 giữ đầu nguồn và thêm đầu lớn dựng đứng. `contact_02`, `contact_07`.
- **S61, t=244,200 / 246,200 / 246,467s**: hai mặt nguồn cạnh xe vẫn còn, thêm portrait lớn phía sau. `contact_05`, `contact_07`.
- **S73, t=294,000 / 295,267s**: nguồn có sổ xanh được người bên phải cầm; R6 mất sổ/động tác cầm và còn silhouette mặt nguồn sau actor. `contact_09`.
- **S22 t=4,200–5,200s, S31 t=41,167s, S41 t=113,400s**: sai hướng đầu, chồng mặt/ghost. S63 t=261,200s và S64 t=262,333s cần kiểm lại role/occlusion. S62 t=253,467s vẫn có mặt nguồn ở entry. S57 t=220,133s xe vẫn ảnh chụp, chưa đồng nhất flat2D.

Expected: cùng số người/vai/vị trí/pose/contact như nguồn, CAST B ổn định; thay diện mạo cả người/props/background. Không chấp nhận “identity mạnh hơn” nếu thêm đầu/người hoặc mất sổ. Owner worker cũ. Test: source/ref/key/final đồng frame, dense trước–contact–hold–release và entry/occlusion; sửa nguyên nhân mask/pose/binding rồi chỉ tái tạo downstream bị ảnh hưởng, giữ controls S74 và các shot đã tốt.

### R6-F02 — P1: semantic gate chưa chặn actual assembly và thiếu trường bắt buộc

`scripts/r6_assemble.py:19` chỉ kiểm số blend rồi encode; không import/call `gate_assemble`. Trong `scripts/r6_gate.py:56–70`, vòng kiểm chỉ duyệt keys có trong `review.inputs`: `{}` được nhận, reviewer/expected/evidence không được xác thực bắt buộc. Fresh probe ảnh trắng + record trống nhưng PASS trả **ACCEPTED**, trong khi control nonempty deps sai bị chặn. Đây là lỗi ràng buộc dữ liệu, không phải đòi hash tự hiểu ảnh.

Expected: input keys/expected/reviewer/frame evidence bắt buộc, đủ exact dependencies; từng actual consumer phải gọi gate trước work. Final blend phải có semantic review trên đúng output hashes; gate key không thay review final. Test negative qua actual key/propagate/assemble/submit, encoder spy phải không được gọi khi review thiếu/sai/stale/UNKNOWN; valid control được qua. Owner worker.

### R6-F03 — P1: event keys vẫn bị bỏ bởi grid

`scripts/r6_propagate.py:60` chỉ stage `1,11,21,…`; key ngoài grid không được dùng ở chính thời điểm đó. `scripts/r6_gate.py:105` lại cho phép lệch ±5 frame. S61 storyboard có f103/f105/f107; S21 có f42/f44/f46; nhiều key event khác bị loại. Danh sách đầy đủ ở `FRESH_PROBES.json`; key cuối shot cũng có trong danh sách nên không gọi tất cả là contact events.

Expected: event làm boundary/key đúng frame; không snap/fallback về key trước. Test off-grid entry/contact bắt buộc renderer tiêu thụ đúng fid và đúng hash, các range ghép không thiếu/lặp frame. Owner worker.

### R6-F04 — P1: CoTracker chưa chứng minh contact

`scripts/r6_cotracker.py:68` đọc `event_map[sid]`, trong khi schema thật là `event_map.shots[sid]`; bên trong dùng `f/event` và `contacts`, không phải `f0/f1/kind`. Cả ba receipt S34/S61/S73 có `windows: []`. Queries dòng 72 chỉ là grid 8×8 tại frame0, không có semantic hand/prop mapping. S73 còn thiếu contact annotation trong event map. Raw tracks/visibility và T source/output bằng nhau là tiến bộ, nhưng drift trung bình ~1px không đóng contact.

Expected: sửa reader và ledger sự kiện đúng nguồn; lưu tọa độ hand/prop riêng từng clip, visibility, before/contact/hold/release; reject mismatch length thay `min()` âm thầm. Test S61 có event104 phải sinh window đúng; S34/S73 có contact thật và chứng cứ ảnh. Owner worker.

### R6-F05 — P1: partial refresh của output cũ được nhận là render mới hoàn chỉnh

`scripts/r6_gate.py:122` và `scripts/r6_propagate.py:88` chỉ kiểm mtime mới nhất. Probe 9 frame cũ +1 frame vừa viết được nhận `fresh:true`. Fresh test thứ hai chạy **function run_shot thật**, runner giả lập inner failure/outer rc0, chín frame cũ, một frame mới: wrapper thêm tail rồi trả `fresh_complete:true`, mặc dù không tạo blend.mp4 mới. Xem `PROBE_SUPPLEMENT.json`; lần probe đầu mtime chạm resolution nên đã bị chặn, được giữ nguyên để minh bạch.

Expected: namespace output/cache theo content và invocation; chứng minh tất cả frame yêu cầu mới/đúng mapping, child outcomes và full decode, không dựa maxmtime/count/outerrc. Test partial/stale/missing frame/inner failure phải block, completed unchanged reuse phải chứng minh provenance. Owner worker.

### R6-F06 — P1: dependency verifier không khóa source/model bytes

`scripts/r6_cache.py:21` chỉ lưu source path/span/frame; `verify_deps` dòng46 chỉ hash casts/masks/graph, không source/model. Probe đổi source và model cùng path/cùng size vẫn `(True,'ok')`; đổi ref control bị chặn. Actual propagation còn tái dùng `video/tmp/out_*` ở cùng shot root.

Expected: exact consumed source/frame span, model, graph/settings, refs/views/masks/keys/reviews phải nằm trong cache identity; actual skip consumer kiểm hiện trạng settings, không chỉ deps tự ghi. Test same-path same-size trên từng dependency và unchanged valid reuse, downstream invalidation cụ thể. Owner worker.

### R6-F07 — P1: script matrix thay ý nghĩa 12Q; QA chưa đủ

`scripts/r6_matrix.py:14–25` tự đổi Q01 thành source-lock, Q08 thành engine decision, Q12 thành master+comparison; trái matrix authority (Q01 identity, Q08 AV, Q12 adoption). Các PASS hardcoded và enum `PARTIAL`/`SEE RECEIPT` không phải closure. Script chưa xuất `R6_MATRIX_EVIDENCE.json` hay `R6_MANIFEST.json` tại snapshot, nên không cáo buộc đã nộp 12PASS.

`scripts/r6_qa.py` cũng đọc event map sai level, chỉ lấy đầu/giữa/cuối; không thực hiện 2s-scan/dense event như docstring. Worker vision cuối chủ yếu hỏi “cùng cảnh/đen/rác”, không hỏi source/ref/role/contact; sheet4 timeout, sheet6 503; chưa thấy Manager held-out QA sau freeze.

Expected: giữ nguyên Q01–Q12 trong `CORRECTION_MATRIX.md` của reviewer; source-linked evidence cho từng dòng; UNKNOWN chặn submit. Manager độc lập chọn và xem source/ref/final frames, không chuyển tiếp verdict của worker. Owner worker (matrix/QA artifacts), Manager (held-out QA).

### R6-F08 — P1: terminal/checkpoint còn stale; cần reconciliation mới

R6f terminal có **40/42 artifact hashes khớp**, hai mismatch là `scripts/r6_qa.py` và `receipts/R6_COTRACKER_RUNS.jsonl`. `remaining_work` vẫn nhắc S43/S49/assembly dù master đã xuất; chưa có final matrix/manifest. Receipt fail-closed là đúng, không sửa terminal đóng để ép thông qua.

R6B reconciliation/registry ghi worker refresh nhầm terminal invocation R6 đầu tiên. Phải preserve và phân loại incident theo **đúng writer lineage**; không tự gom incident Manager vào worker, cũng không reset incident count. Lần unsafe scope violation thứ hai trong cùng lineage phải áp dụng §4 trước resume. Không kết luận context hỏng chỉ từ số messages.

Expected: Manager append R6F reconciliation mới, cập nhật current registry có guard; invocation tiếp theo tạo record riêng, đúng ID/packet/owner/revision. Checkpoint và manifest mới, terminal last, không cycle/self-hash; recursive hash match. Quota hết phải báo blocker chính xác; timestamp reset qua không tự là route khỏe. Owner Manager điều phối; worker tạo deliverable/record của invocation mới.

### R6-F09 — P2: command tái tạo comparison vẫn seek tới cuối master

`scripts/r6_assemble.py:69` có `-ss 300` ngay trước input master dài 300s. Fresh read-only probe trả rc0 nhưng **0 decoded bytes** từ input đó. Comparison hiện có đủ 9.000 frame và decode sạch; finding là command reproduce sai, không khẳng định artifact hiện tại hỏng.

Expected: input master bắt đầu frame0, bản comparison mới đồng source94s/R5frame0/R6frame0; giữ exact command thực đã tạo bytes và kiểm cả frame count/timestamp. Owner worker.

## Verdict và bước tiếp theo

Đây là review độc lập **checkpoint đang dở**, không giả lập một Manager EXIT submission chưa tồn tại. Matrix bảo toàn định nghĩa: **9 FAIL +2 UNKNOWN +1 PASS engineering**; Q08 PASS chỉ ở phép kiểm AV đã nêu. QUALITY_ACCEPTED=0, codex_accepted=0, S12/S13 NOT_APPROVED/NOT_CLOSED. Full22/tool/UI/backend/integration vẫn blocked.

Prompt đầy đủ ở `NEXT_HERMES_MANAGER_PROMPT.md`, proposal tương ứng ở `SESSION_OPENING_PROPOSAL.md`. User tự giao cho Manager hiện hành. Cùng task/RUN/R6/owner nếu context/incident audit đạt; giữ candidate hiện tại và old receipts/terminals frozen, kết quả sửa ghi namespace mới trong R6. Không chạy lại toàn bộ từ đầu; sửa nguyên nhân và chỉ invalidation đúng dependencies. Codex không launch/message/resume Hermes, đổi registry hay sửa implementation.

Codex chỉ patch trạng thái current execution trong ba PM docs canonical (rules/handoff/roadmap), giữ preimages. `FINAL_GUARD.json` xác nhận source/media/snapshot input ổn định, protected drift ngoài ba PM docs bằng0; không claim toàn bộ filesystem đã được audit. Các probe tái hiện lỗi là kiểm thử âm tính, không phải test xanh của implementation.
