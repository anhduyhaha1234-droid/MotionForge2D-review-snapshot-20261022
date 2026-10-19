# Chọn công nghệ theo nhu cầu MotionForge2D

## Quyết định

Học ngay quy trình storyboard theo sự kiện, kiểm từ video đã xuất, dữ liệu cue có nguồn gốc và kiểm bố cục/chữ. Đưa các nguyên tắc này vào skill và hợp đồng bên cạnh; việc thực thi trên pilot vẫn theo packet R6 hiện hành. Chưa thêm renderer hoặc thay route xử lý nhân vật vào runtime.

Sau gate pilot, tính năng mở rộng đầu tiên nên là **caption và motion graphics có timeline riêng, gắn với asset đã duyệt**. Sau đó mới đến Launch Video và cắt footage theo transcript. Đây là thứ tự đề xuất sản phẩm, chưa phải wave được dispatch.

Không nguồn nào trong nhóm đã kiểm chứng khả năng tự sửa global CAST, spatial binding, occlusion hoặc hand–prop contact cho nguồn MotionForge. Những vấn đề đó vẫn thuộc ledger/mask/crop–stitch/VACE/propagation và 12Q đã khóa.

## 15 nguồn đã đối chiếu

Mỗi dòng là lựa chọn theo evidence tài liệu/source, chưa có local render benchmark. Commit đầy đủ và hash nằm trong SOURCE_LOCK.json.

| Nguồn | Phần nên học/tái dùng | Áp dụng vào MotionForge | Giới hạn cần giữ |
|---|---|---|---|
| [product-launch-motion](https://github.com/AbubakrChan/product-launch-motion) | Cue từ word timestamps của VO thật; manifest; QA lấy từ bản MP4 giao; đo mix | Launch composer, CuePlan, QA artifact-bound | MIT phần tác giả viết; NOTICE loại trừ phim/ảnh khách hàng. Không lấy look/ảnh demo, không ép đổi CAST B hoặc normalize audio pilot |
| [motion-graphics-skills](https://github.com/charlie947/motion-graphics-skills) | Brief/brand, chart, product proof, HTML seek theo thời gian | Template có tham số, số liệu được xác nhận, card/CTA | Tree ở pin có 15 SKILL.md, README cũng 15; phần About từng ghi 13. Số lượng không phải quality proof; không nhập mọi template vào tool |
| [claude-motion-design](https://github.com/howseen-ai/claude-motion-design) | Render theo frame, chờ font/assets; sheet source/output và seam | Adapter capture và QA có frame index | Có cấu hình và path riêng của tác giả. `remake_qa.py` hardcode 24fps, 1557 frames, seam positions và màu; không chạy nguyên xi cho pilot 30fps |
| [hyperframes-student-kit](https://github.com/nateherkai/hyperframes-student-kit) | Tách plan EDL khỏi apply; retime transcript; validate beats | Chế độ biên tập footage có preview cuts và undo | README ở pin: 15 skill logical, mirror hai folder; 406 **draft** cards. Cắt silence làm đổi timeline, cấm dùng cho pilot giữ nguồn. Dịch vụ transcribe ngoài là tùy chọn, không tự upload |
| [motion-graphics](https://github.com/Barty-Bart/motion-graphics) | B-roll bám lời, mask preview và correction bằng positive/negative points | Overlay editor; UX xem mask từ SAM2 hiện có | Object separation dùng SAM2 qua Transformers, không phải model identity mới. Không cài thêm Torch/SAM2 cạnh runtime. SRT/VTT word times được chính skill ghi là ước lượng |
| [animate](https://github.com/cth9191/animate) | Story/look/storyboard trước animation; style kit; kiểm text/safe area; bố cục riêng từng tỉ lệ | Explainer templates và storyboard preview sau gate | 7 style dựng procedural canvas, không phải chuyển arbitrary footage thành 7 style giữ motion. Không hỏi lại style pilot; không áp beat grid lên cuts nguồn |
| [claude-motion](https://github.com/whaleyxbt/claude-motion) | Sheet theo beat, zoom vào đoạn chuyển, vòng sửa từ render cuối; sound cues | QA panel và sound design cho launch | Sheet không chứng minh đã playback/nghe. Không nâng pilot lên 60fps hoặc chèn ambient motion chỉ vì toolkit có mặc định đó |
| [claude-remotion-skill](https://github.com/haidrrrry/claude-remotion-skill) | Choreography, timing theo fps, inspect output | Tham khảo mỹ thuật khi dùng Remotion | Hướng dẫn craft, không bảo đảm chữa mọi blur/stiff motion. Các luật spring/stagger hoặc luôn phải có chuyển động không phù hợp mọi cảnh nguồn |
| [Motion](https://github.com/motiondivision/motion) | React gestures/layout/panel transitions | UI feedback tại cast, QC, progress sau khi mở tool | MIT; UI library không thay WAN hay video encoder. 120fps là khả năng/mục tiêu tùy thiết bị, không phải cam kết đo trên máy này |
| [motion-dev-animations-skill](https://github.com/199-biotechnologies/motion-dev-animations-skill) | Reduced-motion, keyboard, transform/opacity và cách chọn pattern | Hướng dẫn animation UI có ích cho Next/React hiện có | Đây là kho tìm được khớp tên từ link `199...`; liên kết người dùng đưa ban đầu không đầy đủ. Không coi mọi `filter` luôn rẻ hoặc mọi gesture đã đạt 120fps |
| [HyperFrames](https://github.com/heygen-com/hyperframes) | HTML/media + seekable timeline; CLI/check/render; engine adapter | Ứng viên ưu tiên để proof lớp caption/motion graphics độc lập | Apache-2.0 ở repo; Node>=22, Chrome headless và FFmpeg. Đã đọc execute.ts: ensureRenderBrowser thực sự được gọi. Chưa cài/benchmark Windows; GSAP/templates/assets có điều kiện riêng |
| [Remotion](https://github.com/remotion-dev/remotion) | Composition React, timing theo frame và player | Phương án thay thế nếu chỉnh sửa/preview React trong app là nhu cầu chính | Runtime có license riêng, không phải MIT toàn bộ. Quy mô tổ chức/cách dùng cần đối chiếu trước product integration; không cài cả hai renderer để rồi chọn sau |
| [Remotion skills](https://github.com/remotion-dev/skills) | API/markup/captions/render docs từ tác giả engine | Dùng làm authority API khi renderer Remotion được chọn | Pin đã tải ghi skill version4.0.535; phải khớp package thực. Không thấy LICENSE gốc riêng trong tree đã lấy; không tự gán MIT. Hướng dẫn preview mặc định không thay yêu cầu MP4 thật của MotionForge |
| [GSAP skills](https://github.com/greensock/gsap-skills) | Timeline labels/nesting, cleanup và framework integration | Kỹ thuật authoring animation nếu route có GSAP | Skills MIT; runtime GSAP có điều khoản khác. Quyền cho app có visual animation builder cần kiểm theo use case trước phát hành |
| [LottieFiles motion-design-skill](https://github.com/LottieFiles/motion-design-skill) | Timing, easing, staging, reduced-motion và personality | Token chuyển động dùng chung cho UI/template | MIT; là hướng dẫn thiết kế, không phải engine xuất phim/Lottie tự động. Không áp tuyệt đối “luôn ba lớp chuyển động” lên QC hoặc cảnh giữ motion nguồn |

## Những chỗ phải sửa cách hiểu từ bài giới thiệu

1. **HyperFrames không bỏ trình duyệt khỏi kiến trúc.** Nó chạy Chrome headless và FFmpeg; người dùng không phải điều khiển trình duyệt thủ công. Bằng chứng: README và `packages/cli/src/commands/render/execute.ts:92,183` ở pin đã lưu. [Nguồn chính thức](https://github.com/heygen-com/hyperframes).
2. **Skill không đồng nghĩa tính năng đã tích hợp.** Đọc file hướng dẫn, có scripts, cài package, chạy fixture, chạy clip thật và đạt pilot là các mức khác nhau. Cả 15 nguồn ở đây mới ở mức kiểm tài liệu/source cho tác vụ này.
3. **Beat sync và source lock là hai chính sách khác nhau.** Cắt nhạc hay dead air hợp lý trong launch/talking-head nhưng làm sai hợp đồng giữ cuts/audio/action hiện tại.
4. **Không bảo đảm bằng khẩu hiệu.** “5 prompts”, “chữa dứt điểm”, “120fps”, “cinematic” không phải acceptance test của MotionForge. Cần đo hoặc nhìn output đúng bytes.
5. **Giấy phép phải tách ba lớp:** skill/source, engine, assets/fonts/music/models. [Remotion license](https://github.com/remotion-dev/remotion/blob/84e4d06d82a5b0388050a5bba7c49b0868c01018/LICENSE.md) và [pricing hiện hành](https://www.remotion.dev/docs/license/pricing) phân biệt điều kiện Free/Company. [Webflow Product Terms §9](https://webflow.com/legal/product-terms) giới hạn một số công cụ tạo animation qua visual builder cạnh tranh. Vì MotionForge dự định có editor, chưa có đủ căn cứ ghi GSAP “commercial cleared”; cần kiểm trường hợp sản phẩm cụ thể. Điều này không cản việc học nguyên tắc hoặc viết hợp đồng hôm nay.

## Chọn một renderer cho proof sau gate

**Ưu tiên khảo sát HyperFrames** cho lớp composition từ HTML: khớp nhiều skill được gửi, có check/CLI, code Apache-2.0. Tách authoring runtime khỏi engine; nếu dùng GSAP thì rà điều khoản nêu trên, không suy license engine bao phủ GSAP. Cần đo cold/warm render, RAM và output thật trên Windows trước chốt.

**Remotion là phương án thay thế** khi cần React composition và chỉnh tham số/preview gắn chặt frontend. React19 hiện có giúp giảm khác biệt authoring nhưng không tự chứng minh tương thích package/render runtime. Giữ version đồng bộ và xác định điều kiện license của tổ chức. Không chọn chỉ vì repo phổ biến.

**Không chọn raw Playwright renderer tự viết làm production mặc định.** Học capture/readiness/seam QA từ howseen/animate nhưng tận dụng engine có sẵn để giảm việc tự bảo trì media timing/cancel/resume. Nơi tích hợp cần adapter nhỏ và provenance; không viết lại motion/flow core.

## Phần đã áp dụng trong bộ này

- CuePlan dùng frame nguyên và fps hữu tỉ; phân biệt cue lời thoại đo thật với ước lượng.
- Source-locked plan chỉ cho marker phục vụ QA; đổi nhạc, cắt, retime, camera/overlay bị chặn trong hợp đồng mẫu.
- Feature spec buộc freeze input/output và lấy QA từ file render cuối; không nhận preview thay MP4.
- Tái dùng Job/JobStep/JobAttempt, QC fingerprint và timeline authority đang có trong INTEGRATION.
- Skill có lựa chọn theo mode, đọc tham chiếu đúng việc; không kế thừa path riêng, lệnh cài global hoặc luật mở nhiều agents từ upstream.

Các thay đổi này đang nằm trong gói outputs, chưa thay code/tool/packet Hermes đang chạy. Đây là giới hạn theo bản bàn giao, không phải một verdict mới hay lời khẳng định đã triển khai công nghệ vào pilot.
