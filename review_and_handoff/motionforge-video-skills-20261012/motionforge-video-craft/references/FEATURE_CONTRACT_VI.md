# Hợp đồng tính năng — MotionForge video craft

Trạng thái: **DESIGN_READY / IMPLEMENTATION_BLOCKED_DEPENDENCY**. Đây là đặc tả sản phẩm để dùng khi mở gate tool, không phải lệnh giao Hermes, sprint mới hoặc quyền ghi production. Không sửa acceptance của MF-DEMO-LONG-01.

## 1. Hành trình người dùng

Sau khi pilot đạt và phần tool được mở, người dùng chọn loại sản phẩm:

| Loại | Đầu vào | Kết quả | Quy tắc thời gian |
|---|---|---|---|
| Giữ chuyển động nguồn | Video + cast đã khóa | Video thay diện mạo đúng timeline + QA | Nguồn là authority; không cắt silence, đổi tốc độ, đổi camera/cuts/audio |
| Video ra mắt sản phẩm | Logo/screenshots/brand + thông tin đã xác nhận + VO tùy chọn | Bản dựng có storyboard, caption, CTA và MP4 | Cue theo VO thật nếu có; nhạc là lớp phụ |
| Biên tập người nói | Video + transcript theo từ | Preview EDL, footage đã cắt và transcript đã map lại | Mọi đoạn bỏ hiện trên preview; bảo toàn ánh xạ về nguồn |
| Video giải thích | Nội dung + assets/style được chọn | Storyboard và các cảnh procedural | Storyboard đã chốt quyết định beats; layout riêng theo tỉ lệ |

Không đưa lựa chọn mode mới vào pilot đang sửa. “Giữ chuyển động nguồn” là lựa chọn hiện hành đã chốt; không hỏi lại CAST B/flat2D.

## 2. Vị trí nối vào code đang có

Đối chiếu read-only tại INTEGRATION `a52fca897906fd61a088016dd802718fdf06d217`. Source tồn tại không đồng nghĩa feature đã chạy/được duyệt. Mọi điểm dưới là vị trí thiết kế cần xác nhận lại khi dispatch.

| Thành phần hiện hữu | Bằng chứng đã đọc | Cách tái dùng khi mở gate |
|---|---|---|
| `app/workflow/durable_worker.py` + `job_handlers.py` | `register_handler` và handler nhận manifest; Job authority không nằm trong HTTP closure | Thêm handler composition theo contract được duyệt, dùng cùng lifecycle/cancel/checkpoint; không tạo queue riêng |
| `app/services/source_locked_timeline.py` | `TIMELINE_VERSION`, parse time base, partition/coverage/identity reason codes | Giữ authority hiện hữu; cue sidecar tham chiếu hash, không sửa frozen block để thêm beats |
| `app/workflow/qc_checks_handler.py` | `RUN_QC_CHECKS`, policy/evidence fingerprints, server-owned scopes, zero-item completion | Bổ sung checker trong scope được duyệt, không để client gửi tên detector tùy ý; content change làm review hết hiệu lực |
| `app/workflow/s12_export_jobs.py` | Durable submission, source/audio resolution, managed output; publisher có lifecycle riêng | Adapter trả candidate manifest. Preview hoặc renderer exit0 chưa được publish/completed; vẫn qua export/QA authority |
| `frontend/src/features/shot-review/*` | ShotList, QcMarkerList, BeforeAfterSync, panel/API có sẵn | Thêm cue/event markers và mở đúng evidence; không dựng màn review thứ hai |
| `frontend/src/features/reference-library/*`, `project-cast/*` | View board, mapping và library picker tồn tại | Brand assets thuộc library riêng; actor ID/cast mapping giữ authority riêng, không trộn logo/template với cast identity |
| `frontend/package.json` | Next16.2.12, React19.2.4, Konva/Zustand; chưa khai báo Motion/Remotion/GSAP/HyperFrames | Chỉ thêm dependency cho route đã proof và được chọn, không cài toàn bộ danh sách |

Giới hạn đọc code: đã kiểm các điểm contract và hàm liên quan, chưa chạy frontend/backend hoặc quality suite. `BeforeAfterSync` dùng HTMLVideo currentTime và ngưỡng lệch 0.15s; không coi player này là công cụ xác minh chính xác từng frame. Frame QA phải lấy decoded frames/time map của artifact.

## 3. Dữ liệu chung cần có

Không đưa toàn bộ các đối tượng dưới vào một migration lớn. Chốt interface trước, proof sidecar trong managed output, rồi tách task theo dependency.

- **Asset manifest:** asset ID, SHA256, type, kích thước/duration, nơi lưu, provenance/rights, font/model/runtime pin nếu liên quan. Không tải mạng động khi render; input là assets đã resolve.
- **Brand profile:** palette, font file, logo, safe margins, tỷ lệ export và motion tokens. Không chứa actor identity thay cho ProjectCastMapping.
- **Storyboard:** scene ID, khoảng frame, mục đích, assets, câu VO, cue IDs, transition, expected visual state và approval ràng buộc content hash. Sửa một scene làm invalid approval/dependencies liên quan.
- **CuePlan:** version, mode, source hash, fps numerator/denominator, source span, output frame count, audio/frame-map policy; cue ID, half-open frame range, clock, action, evidence reference. Khác namespace với source actor/event ledger.
- **Word timing:** mỗi word có stable ID, text, start/end sample/time, audio hash, method/version, trạng thái `measured` hoặc `estimated`. Câu thay hoặc audio đổi phải invalidate cue. Không chia đều SRT rồi ghi “word-locked”.
- **EDL:** source keep/delete spans, lý do/confidence, output-to-source map; transcript remapped chỉ sinh từ cùng EDL hash. Cut mistakes cần kiểm ngữ nghĩa, không chỉ xóa phần lặp ký tự.
- **Render receipt:** renderer/version/config, browser/font/asset hashes, width/height/fps/frame count, outputs, exit/cancel/checkpoint, thời gian/RAM đo thật. Cache key dựa bytes/config/policy, không dựa path/size.
- **QA record:** artifact hash, source/reference hashes, frame/time samples thực đã xem, checker/reviewer identity, PASS/FAIL/UNKNOWN từng mục, limitations. Structural validation không tạo semantic PASS.

## 4. Tính năng đầu tiên: Cue & QA sidecar

**Mục đích:** nối storyboard, word/event cue và evidence vào timeline mà không làm đổi video nền. Trong mode giữ nguồn, sidecar ban đầu chỉ là marker QA. Caption/motion layers là derivative export ở mode authoring được mở riêng sau gate.

Đầu vào: media asset/hash, time base chuẩn, storyboard revision, word/event references và chính sách mode. Đầu ra: CuePlan immutable + marker list + báo lỗi theo cue ID. Không render hoặc thay source khi tạo plan.

Hợp đồng tối thiểu được minh họa bằng `assets/cue-plan.example.json` trong skill. Bộ kiểm Python đi kèm là **reference validator cho sidecar**, không nhập vào app hoặc thay source_locked_timeline. Nó kiểm hình dạng/quan hệ số học/chính sách mode, không đọc video, xác minh hash file hay đánh giá nội dung.

Acceptance trước khi tích hợp:

1. Frame nguyên, khoảng `[start,end)`, fps hữu tỉ dương; boundary cuối không bị lệch/mất/nhân đôi. Test thêm 30000/1001 ở adapter quy đổi, không chỉ 30fps.
2. Source-locked: output frame count bằng source span; frame map identity; audio original_locked; chỉ marker. Các cut/retime/graphic/camera bị reject rõ lý do.
3. Word cue chỉ mang nhãn đồng bộ đo thật khi timestamps gắn đúng audio hash. Sai nguồn, timing unknown, cue ngoài range hoặc ID trùng phải reject. Sai thứ tự ngẫu nhiên có policy rõ, không âm thầm sort sửa ý nghĩa.
4. Source/audio/template đổi cùng path/cùng size thì hash invalidates plan/review/cache downstream; unchanged control được reuse.
5. UI mở marker tới đúng decoded frame/evidence và hiển thị trạng thái chưa kiểm. Thiếu data không vẽ một timeline “đã đạt”.
6. Reopen app vẫn có plan/marker/version. Không chỉ giữ trong localStorage/Zustand. API, persistence và worker tuân lifecycle hiện hữu.

## 5. Tính năng tiếp: Caption & Motion Layers

Đầu vào: approved base media, CuePlan, template asset có version, text/data chính xác, font local và export profile. Đầu ra: preview và MP4 derivative có receipt; giữ original riêng.

Một renderer adapter được chọn sau proof. API nội bộ đề xuất: `validate(manifest)`, `render_still(frame)`, `render_range(start,end,checkpoint)`, `cancel(run)`; kết quả trả candidate + evidence, không tự publish. Tên này là contract dự kiến, không phải hàm đang tồn tại.

Chỉ bắt đầu bằng 3 mẫu có mục đích rõ: lower-third, caption theo từ và comparison/stat card. Không nhập 406 card. Template chỉ dùng props/data đã validate; URL/user text không trở thành code được thực thi tùy ý. Giữ render assets local và managed-root isolation.

Proof phải có MP4 thật với chữ tiếng Việt, tên dài, xuống dòng, dấu tiếng Việt, font thiếu, 16:9 và 9:16, first/last frame và transition seam. Seek cùng frame từ hai thứ tự khác nhau phải ra cùng decoded pixels trong cùng pinned runtime; không hứa byte-identical MP4 trên mọi máy. Check layout/contrast có sample count >0, font ready và media ready; 0/0 không phải PASS.

QA xác minh cue time ở file cuối trong ngưỡng được chốt theo fps, không chỉ JS timeline. Kiểm audio mux/decode, missing image/font/audio, cancel, stale checkpoint và cache mutation. Graphic không che khu vực actor/contact được bảo vệ khi dùng footage; tắt layer khôi phục base media. Video test kỹ thuật không được đặt nhãn pilot acceptance.

## 6. Launch Video

Ghép thành hành trình: nhập assets/brief → script dựa claims thật → storyboard preview → VO/timings nếu cần → preview các beats → render → QA → export/reopen. Không buộc đủ một số lượng concept/style cố định khi user đã chọn.

Mỗi số liệu/giá/testimonial/screenshot có provenance. Thiếu asset thì nêu phần thiếu, không chế UI đang hoạt động hoặc đánh dấu tính năng chưa build là có thật. VO có thể là recording người dùng; không tự mua API/clone giọng. Nhạc/sound mastering là profile riêng, không đổi audio pilot nguồn.

Acceptance: claim đúng assets, chữ đọc được trên điện thoại, cue gắn VO thật, first/last frames hợp lệ, không white-frame sau grade, nghe/đo file cuối và ghi giới hạn kiểm, license manifest, bản ngang/dọc được relayout. Không chốt “Apple quality” bằng số test.

## 7. Transcript Edit và Explainer

**Transcript Edit:** plan EDL trước, hiển thị đoạn xóa và lý do, cho undo; review mistakes/retakes riêng silence. Cần word timing tin cậy và full audio duration, không infer đuôi video từ từ cuối. Fixture có khoảng im lặng, tiếng Việt, hai người nói chồng, âm nhạc không lời và đoạn pause có ý nghĩa. Hai-track A/V map cùng EDL. Không kích hoạt trên source-locked job.

**Explainer:** chọn một style kit, chốt story/frames theo user intent đã có; giữ style assets/version, tách score và VO. Test text overflow/safe area/morph/camera trên output, không chỉ contact sheet preview. Đây là procedural authoring, không là fallback engine reskin CAST.

## 8. UI motion

Dùng Motion hoặc CSS tùy độ phức tạp, chưa thêm dependency hiện tại. Ưu tiên chuyển panel QC, feedback chọn cast và progress state; không animate video canvas đang làm bằng chứng. Không biến phần trăm ước đoán thành progress thật. Keyboard/focus giữ đúng, reduced-motion loại spatial motion không cần thiết. Đo trên mục tiêu thực; không ghi bảo đảm 120fps.

## 9. Thứ tự mở sau này

| Bước đề xuất | Điều kiện mở | Bàn giao để review |
|---|---|---|
| Cue sidecar proof | Pilot được Codex chấp nhận và user mở tool gate | Contract + adapter proof + negative cases, không thay media |
| Một renderer proof | Contract sidecar rõ; phiên bản/license/use case được xác định | MP4 thật + seek/AV/layout/resource proof trên Windows |
| Durable job + UI integration | Candidate proof đã review; exact transport/owner/write-set mới | API→queue→preview→render→QA→reopen thực; cancellation/resume |
| Launch templates | Integration đạt | Một sản phẩm launch dùng assets thật và review file cuối |
| Transcript Edit/Explainer | Scope riêng được mở | EDL hoặc storyboard + sản phẩm riêng, không ghép vào correction CAST |

Task IDs, session owners, exclusive write-set, branch và model route chỉ được cấp trong packet tương lai theo rules canonical sau preflight. Không mở wave ở đây; không thay packet R6 hiện hành. Giữ WIP/GPU policy và counters theo canonical rules lúc thực thi.
