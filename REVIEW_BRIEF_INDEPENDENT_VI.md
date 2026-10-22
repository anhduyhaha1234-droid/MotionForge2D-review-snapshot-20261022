# Đề bài gửi reviewer độc lập — MotionForge2D

**Gửi toàn bộ file này cho reviewer.** Mục tiêu là xác định khách quan MotionForge2D đang giải đúng bài toán nào, code và sản phẩm thực sự làm được gì, vì sao chưa ra video đạt yêu cầu, kiến trúc hiện tại có đáng tiếp tục hay nên thay một phần, và lộ trình ngắn nhất có bằng chứng để hoàn thiện. Đây là **đề bài đánh giá**, không phải yêu cầu reviewer xác nhận các báo cáo cũ hay tiếp tục sửa theo cách cũ.

## Tin nhắn có thể gửi nguyên văn

> Bạn là reviewer độc lập về sản phẩm, kiến trúc phần mềm, hệ thống video AI local và UX. Hãy đánh giá MotionForge2D từ mục tiêu người dùng và bằng chứng thực tế trước khi đánh giá giải pháp đang có. Đừng xem PRD, rules, report cũ, số test xanh, nhãn `APPROVED` hay độ lớn codebase là sự thật hiển nhiên; đó là **đầu vào cần kiểm chứng**. Đừng mặc định phải giữ cấu trúc, thuật toán, model hoặc workflow hiện tại chỉ vì đã đầu tư nhiều công sức.
>
> Tôi cần kết luận có thể hành động: **(1)** sản phẩm nên giải bài toán gì và phạm vi Phase 1 khả thi là gì; **(2)** phần nào thực sự chạy qua hành trình người dùng và chất lượng media; **(3)** nút thắt gốc nằm ở dữ liệu, hợp đồng, wiring, thuật toán, model, runtime, UX hay tiêu chí sản phẩm; **(4)** nên giữ, sửa, tái dùng giải pháp có sẵn hay thay công nghệ nào; **(5)** thứ tự công việc và điều kiện nghiệm thu để có demo 60 giây, pilot 300 giây rồi sản phẩm dùng được cho nhiều video.
>
> Chỉ làm **review read-only** trong lượt này: không sửa source, không chạy GPU/render tốn tài nguyên, không tạo agent/writer, không đổi gate hoặc trạng thái nghiệm thu. Được chạy kiểm tra CPU/read-only trong checkout tách biệt và được nghiên cứu repo/tài liệu công khai. Nếu thiếu input thiết yếu, ghi `UNKNOWN/BLOCKED_BY_EVIDENCE` cùng danh sách file và phép kiểm cần thiết; không đoán là PASS hoặc FAIL. Có thể đề xuất thí nghiệm GPU nhỏ để tôi quyết định sau.

## 1. Bộ đầu vào và cách tránh nhầm phiên bản

| Nguồn | Vai trò | Lưu ý |
|---|---|---|
| [Repo private mới, `main`](https://github.com/anhduyhaha1234-droid/MotionForge2D-review-snapshot-20261022) | Snapshot bàn giao, rules, history bundle, packet G1/G2, report 22/10 | Pin commit tại lúc review; `project/` chỉ là tập source chọn lọc. |
| [Nhánh full-code 02/10](https://github.com/anhduyhaha1234-droid/MotionForge2D-review-snapshot-20261022/tree/review/20261002-full-code) | Toàn bộ app tích hợp để review code/architecture; commit `f3917d1525b9c10dfb0d2483a791bf16315762a2` | Không suy rằng G1 candidate 16 đã được tích hợp vào branch này. |
| [PRD V4](https://github.com/anhduyhaha1234-droid/MotionForge2D-review-snapshot-20261022/blob/review/20261002-full-code/docs/PRODUCT_REQUIREMENTS_V2.md) và [BA brief](https://github.com/anhduyhaha1234-droid/MotionForge2D-review-snapshot-20261022/blob/review/20261002-full-code/docs/external-review/PROJECT_BRIEF_VI.md) | Mục tiêu lịch sử để thẩm định tính hợp lý và traceability | Tên file PRD có `V2` nhưng header ghi Product Requirements V4; ghi nhận điểm này, kiểm version thật. |
| [Rules canonical](project/docs/pm/HERMES_AUTOPILOT_RULES.md) | Hiểu ranh giới approval, evidence và lineage lịch sử | Review xem quy tắc nào bảo vệ chất lượng, quy tắc nào tạo chi phí/khó dùng. Không dùng rules làm bằng chứng sản phẩm tốt. |
| [G1 candidate 16](updates/20261022/g1/c16/) và [verdict độc lập](updates/20261022/g1/root_review.md) | Frozen engineering evidence contract | Manifest SHA-256 `4df7de9ccc81dff7a82a9b9d70d90a48eae2bb17cd9ff455748b041f20a0ba82`; chỉ G1 engineering được duyệt, không phải media. |
| [G2 readiness/recovery](updates/20261022/g2/) | Trạng thái đầu vào/runtime trước media | Preflight 19 PASS, 25 FAIL, 7 UNKNOWN; media chưa chạy. Kiểm lại nguồn của từng claim. |
| [Review R6 cũ](review_and_handoff/motionforge-r6-checkpoint-review-20261014/REVIEW_VI.md) | Ví dụ output 300 giây đã render nhưng sai hình/hoạt động | Không gộp R6 cũ với G1 C16/G2 mới. Muốn kết luận chất lượng phải xem video/frame nguồn–đích; nếu chưa có media, ghi thiếu bằng chứng. |
| [Report 22/10](REVIEW_CODE_20261022_VI.md) và [test audit](updates/20261022/TEST_AUDIT_VI.md) | Danh sách claim/đường dẫn để **phản biện** | Hãy ghi nhận giả thuyết độc lập trước khi dựa vào kết luận report này. |

Trước mọi verdict, lập **bảng phiên bản** cho từng claim: repo/branch/commit hoặc manifest SHA, file nguồn, dữ liệu media, ngày, thử nghiệm và reviewer. Không cộng test/approval của các cây khác nhau. Kiểm thực tế của repo mới, kể cả quyền truy cập và trạng thái asset; ZIP giải nén thiếu `.git` từng tạo test fail giả nên các test dùng Git phải chạy trong Git checkout.

## 2. Xác định lại mục tiêu sản phẩm từ góc nhìn người dùng

Hãy trả lời trước khi bàn code:

1. Người dùng chính là ai, đầu vào thực tế là loại video nào, output thế nào mới tạo giá trị? Trải nghiệm tối thiểu từ import tới MP4 là gì? Mức can thiệp thủ công/phút video chấp nhận được là bao nhiêu?
2. Cần giữ chính xác yếu tố nào của nguồn: mạch chuyện, số vai, thứ tự sự kiện, chuyển động, contact tay–vật, occlusion, camera, thời lượng, audio? Yếu tố nào được phép sai khác ở cấp pixel/frame? Đề xuất **định nghĩa fidelity đo được** thay cho “giống” mơ hồ.
3. PRD lịch sử đặt nhiều mục tiêu đồng thời: all-object reskin, Character Library/Generator, batch, 4K, local-first, quản lý channel/project, audio gốc. Mục nào thiết yếu để có video đáng dùng; mục nào có thể hoãn mà không mất giá trị? Nêu hậu quả của việc hạ scope.
4. Người dùng đã ưu tiên sinh video **local** để tiết kiệm khi làm số lượng lớn; agent Hermes/Gemini/DeepSeek có thể chạy cloud cho phân tích/điều phối. Kiểm chính xác media/audio/metadata nào ra ngoài máy và đề xuất ranh giới dữ liệu phù hợp.
5. Pilot 60 giây, 300 giây và mục tiêu nhiều video có cùng CAST là ba cổng khác nhau. Cổng nào chứng minh điều gì? Nếu 60 giây đẹp mà 300 giây đứt identity thì chưa đạt phần nào?
6. Với nguồn 640×360, “xuất 4K” là upscale hay native generation? UI và tài liệu phải nói thật thế nào? 4K có nên là gate sớm hay sau fidelity/continuity?

**Đầu ra bắt buộc:** một trang *product contract* với persona, job-to-be-done, phạm vi Phase 1, ngoài phạm vi, ưu tiên P0/P1/P2 và tiêu chí nghiệm thu quan sát được. Chỉ rõ yêu cầu nào thiếu rõ ràng, mâu thuẫn hoặc không khả thi trên phần cứng/ngân sách mục tiêu. Nếu phải hỏi tôi, chỉ hỏi những quyết định thật sự đổi thiết kế/acceptance và đưa lựa chọn kèm tác động.

## 3. Kiểm kê độc lập cái gì đã có và cái gì thật sự chạy

Với từng năng lực dưới đây, lập bảng `requirement → entry point UI/API → actual call path → producer/consumer → test/receipt → artifact media → verdict`. Dùng các trạng thái **PRODUCT_PROVEN**, **MEDIA_PROVEN**, **INTEGRATION_PROVEN**, **FIXTURE_ONLY**, **CODE_PRESENT**, **BLOCKED**, **ABSENT**, **UNKNOWN**. Một năng lực có module nhưng không có caller production là `CODE_PRESENT`, không phải “xong”.

| Năng lực cần xem | Câu hỏi chứng minh chính |
|---|---|
| Import, probe và source pin | Người dùng nhập video qua UI/API được không? SHA/timebase/audio/scene persist và reopen sau restart? |
| Scene/shot/event analysis | Boundary, camera, action, contact, occlusion và audio map có đo từ source bytes? Event off-grid có được giữ đúng timestamp? |
| Object Role/CAST/Character Pack | ID xuyên cảnh/video, version asset bất biến, multi-view/pose, relink/split/merge và reuse có hoạt động trên dữ liệu thật? |
| Reference/anchor và storyboard | Ảnh neo tạo/duyệt/khóa ở đâu? 54-shot pilot có input đầy đủ? Prompt/control/graph ràng buộc per-shot, không tái dùng sai? |
| Engine local | FFmpeg, SAM2/CoTracker/segmentation, ComfyUI, model weights/node/endpoint/VRAM có load và chạy được trên máy mục tiêu? |
| Render/composite/cache | Source → mask/track/actor/prop/background → frames → stitch; cache khóa đúng source/model/graph/CAST/review; sửa một shot invalidate đúng downstream? |
| QC và review | Output observation lấy từ frame thật hay fixture? Identity/action/contact/occlusion/flicker/timing/audio có comparator trong production path và fail-closed? |
| Export/S12 | MP4 cuối có codec, duration, audio, 30 fps/PTS đúng; reopen từ app; lỗi `av_policy` lịch sử đã giải quyết chưa? |
| Frontend UX | Người mới thực hiện toàn flow mà không SQL seed/script/manual path? Before/After, review by exception, progress/cancel/retry/restart có rõ? |
| Batch/ops/install | Hai video dùng cùng CAST, không lẫn artifact; clean Windows setup, model download/config, quota/disk/OOM/recovery có tái lập được? |

**Đầu ra bắt buộc:** capability matrix với trạng thái, confidence, bằng chứng exact commit/path/line/hash/command, tác động người dùng và phép thử còn thiếu. Không đưa “% hoàn thành” nếu chưa có mẫu số chức năng, trọng số và evidence được thống nhất.

## 4. Review kiến trúc và chất lượng code theo luồng thực

Vẽ sơ đồ **AS-IS** và call graph của ít nhất hai đường chạy: (a) người dùng import→demo→export; (b) một shot khó có hai người, tiếp xúc với đạo cụ và che khuất. Chỉ ra nguồn sự thật cho Project, VideoItem, Scene, ObjectRole, CAST version, storyboard, job attempt, lease, artifact hash và QC verdict. Đánh giá:

- Ranh giới UI/Next.js ↔ FastAPI ↔ DB/job/worker ↔ artifact store ↔ ComfyUI/FFmpeg; nơi nào đang gọi vòng, bỏ qua gate hoặc có hai source of truth.
- Tính đúng của schema/timebase/frame interval, API/error contract, migrations, idempotency, ownership/lease, cancel/retry/restart, concurrent writer, partial output, cache invalidation và an toàn filesystem.
- Production wiring thật so với test gọi trực tiếp module; test có negative case qua actual adapter/gate không; mock/fixture có che lỗi semantic hay môi trường không.
- Mức tách engine/model khỏi domain; khả năng thay một node/model/graph mà không viết lại toàn app; dependency pin, Windows/CUDA/VRAM và clean-host reproducibility.
- Quyền riêng tư của local media, secrets, local API/auth boundary, log chứa path/dữ liệu, dữ liệu gửi tới agent cloud và lưu trữ/cleanup.
- Maintainability: module phình to, code trùng, contract vô định, exception bị nuốt, timestamp/mtime làm identity, test rườm rà nhưng không bảo vệ đường chạy quan trọng.

Với mỗi finding P0/P1/P2, ghi `symptom → failing actual call path → root cause đã chứng minh hoặc hypothesis → vì sao test/self-review cũ bỏ sót → user impact → cách tái lập → điều kiện đóng`. Tách lỗi **data/asset, contract, wiring, thuật toán, model, orchestration, UX và evidence overclaim**. Không quy toàn bộ vấn đề cho Gemini, ComfyUI hay model khi input/binding chưa đúng.

## 5. Đánh giá video và pipeline sinh hình một cách có thể lặp lại

Nếu có video nguồn, reference và output thật, chọn mẫu độc lập gồm cảnh dễ, khó, biên cut, entry/exit, two-actor, contact/hold/release, occlusion, giấy/chữ và camera motion. Không chỉ chọn screenshot đẹp. Với từng shot so đồng bộ **source | target reference | generated frames/video**, nghe audio ở đầu/giữa/cuối và xem cả vùng chuyển cảnh. Ghi frame/timestamp, role/prop ID, expected/actual, lỗi và severity. Các phép đo như 9.000 frame, decode rc0, A/V correlation, mask IoU, drift, flicker là bổ trợ; **không thay review nội dung/hành động**.

Đánh giá riêng:

1. Cách cắt scene/shot và tạo identity/role ledger: thế nào để một vật/người giữ ID qua cut, khi thay diện mạo vẫn đúng vai và người sở hữu đạo cụ?
2. Reference pipeline: ảnh đầu cảnh, nhiều góc CAST, last-frame chaining, keyframe/event anchors và storyboard. Last-frame chaining xử lý thế nào khi cut đổi góc, nhân vật ra/vào khung, drift tích lũy hoặc đạo cụ đổi tay?
3. Motion conditioning: video-to-video, pose/depth/flow/track, mask/segmentation, compositing và generative model; từng cách giữ action/contact/camera đến mức nào trên cùng fixture?
4. Routing độ khó: tín hiệu nào dự đoán cảnh dễ/khó trước render, confidence/uncertainty nào đủ tin cậy; đường xử lý riêng cho giấy/đạo cụ, single actor, multi-actor/contact và camera phức tạp.
5. QC theo rủi ro: tự động chặn artifact sai rõ rệt và chọn frame để người xem; loại lỗi nào còn bắt buộc người duyệt? Thời gian xem/sửa mỗi phút output là bao nhiêu?

Nếu không có raw media, ghi rõ **không thể verdict chất lượng**; chỉ ra asset/manifest/hash nào cần cung cấp. Không suy chất lượng từ R6 review hoặc report của agent mà không tự nhìn mẫu. Không chạy lại 300 giây chỉ để có file mới trước khi biết vài shot đại diện đã giải được nút thắt.

## 6. Đánh giá UX/UI từ nhiệm vụ của người mới

Thử hoặc walkthrough bằng browser thật theo kịch bản: tạo project → import → xem scene/role → chọn hoặc tạo CAST → duyệt anchor/demo → xem và sửa một lỗi → render lại đúng phạm vi → xuất và mở file. Ghi số quyết định/nhấp chuột, nơi mất context, trạng thái chờ lâu, lỗi thiếu asset/model/VRAM, thông báo khó hiểu, cách so before/after, khả năng undo/retry và accessibility bàn phím. Phân biệt màn hình có trong code với flow có thể hoàn thành. Đề xuất IA và màn hình tối thiểu theo nguyên tắc **automation trước, review ngoại lệ**, nhưng kiểm thực tế với người dùng; không đánh giá chỉ bằng ảnh mockup hoặc gu thẩm mỹ.

**Đầu ra bắt buộc:** journey map hiện tại với điểm đứt, wireflow đề xuất và danh sách UX change theo tác động; mỗi change gắn một user task/metric, không chỉ “UI đẹp hơn”.

## 7. Tìm phương án có sẵn trước khi tự build hoặc tiếp tục vá

Cho từng nhóm nút thắt trọng yếu, kiểm xem package, workflow, node hoặc repo **đã nằm trong dự án** có giải được chưa; sau đó mới so với upstream/repo hiện hành. Dùng nguồn chính thức hoặc GitHub source tại ngày review, ghi URL, license, commit/version, Windows/Python/Torch/CUDA/RTX 5070 12 GB, input/output contract, độ bảo trì, công sức tích hợp và giới hạn. Không dùng stars, README demo hoặc claim marketing làm proof phù hợp. Ít nhất so ba đường:

| Hướng | Cần phân tích |
|---|---|
| Sửa tối thiểu/giữ engine | Nếu lỗi chỉ ở dữ liệu, schema, binding, gate hoặc UI, patch ở đâu, mất bao lâu và regression nào? |
| Tái dùng/thay một module | Thành phần open-source/upstream nào thay tracker, segmentation, reference, video generation, compositor hoặc QC mà giữ contract? |
| Thiết kế lại một đoạn pipeline | Nếu kiến trúc hiện tại không thể đáp ứng semantic fidelity/throughput, ranh giới thay, migration, dữ liệu cần chuyển và rollback là gì? |

Mỗi finding chốt `PATCH`, `REUSE_INSTALLED`, `ADOPT_UPSTREAM`, `REPLACE` hoặc `DEFER_WITH_REASON`. Đề xuất benchmark cùng source shot/CAST/acceptance với baseline, ghi hash output, thời gian GPU, VRAM, công sửa tay và chất lượng. Phân biệt **đề xuất**, **đã cài**, **đã wired**, **đã test**, **đã đạt media**. Không tự cài hàng loạt hoặc đổi stack trong lượt review này.

## 8. Kết luận và kế hoạch reviewer phải trả lại

Yêu cầu một báo cáo tiếng Việt với các phần sau, ưu tiên bảng và link bằng chứng:

1. **Executive verdict 1 trang:** mục tiêu có hợp lý không, hiện tại dùng được đến đâu, có video nào được nghiệm thu chưa; top 5 blocker; mức chắc chắn và phạm vi chưa kiểm.
2. **Product contract đề xuất:** mục tiêu Phase 1, trường hợp sử dụng, tradeoff fidelity–chi phí–thời gian–manual work, chỗ nào PRD cần đổi hoặc hỏi chủ dự án.
3. **Version/evidence map:** từng repo/commit/candidate/manifest/media output; sự khác nhau giữa `main`, nhánh full-code, G1 C16, G2 và R6 lịch sử.
4. **Capability matrix:** mỗi tính năng là PRODUCT_PROVEN/MEDIA_PROVEN/INTEGRATION_PROVEN/FIXTURE_ONLY/CODE_PRESENT/BLOCKED/ABSENT/UNKNOWN; bằng chứng và test còn thiếu.
5. **AS-IS architecture + TO-BE options:** call/data flow, source of truth, bottleneck, dependency và ít nhất hai phương án có tradeoff. Nêu rõ giữ/thay phần nào và vì sao.
6. **Findings có thể sửa:** ID, P0/P1/P2, confidence, exact path/line/commit, expected/actual, repro, root cause hoặc hypothesis, vì sao test bỏ sót, tác động và acceptance.
7. **Media/UX review:** sample frame/clip và kết quả đo nếu có dữ liệu; nếu thiếu, danh sách chính xác cần cấp. Không dùng một screenshot để nghiệm thu toàn video.
8. **Bảng phương án nguồn mở:** nguồn/version/license/compatibility, PATCH–REUSE–ADOPT–REPLACE–DEFER, test cùng fixture và rủi ro chuyển đổi.
9. **Roadmap theo cổng có bằng chứng:** bước nhỏ nhất tạo clip 10–30 giây đúng action/contact; demo 60 giây; pilot 300 giây; tích hợp UI end-to-end; batch/cài sạch. Cho dependency, chủ sở hữu đề xuất, ước lượng theo range/giả định, thời gian GPU và điều kiện dừng/pivot. Ưu tiên sửa nút thắt làm video sai trước phần phụ.
10. **Danh sách câu hỏi cho tôi:** chỉ các quyết định người dùng phải chốt; mỗi câu kèm 2–3 lựa chọn, hệ quả và default đề xuất. Phần reviewer có thể tự xác minh thì hãy tự làm.

**Chuẩn bằng chứng:** mọi kết luận quan trọng có nguồn cụ thể (commit/path/line hoặc media hash/frame/timestamp), lệnh và kết quả tái lập, hoặc ghi rõ `INFERENCE/UNKNOWN`. Severity dựa vào ảnh hưởng tới output/người dùng; không chấm điểm tùy cảm tính. Khi hai nguồn mâu thuẫn, nêu cả hai và cách phân xử. Không báo “xong”, “70%”, “production-ready” nếu chưa có mẫu số và cổng nghiệm thu rõ. Đưa quyết định cuối cùng theo ba lớp riêng: **engineering**, **media quality**, **product usability**.

Đây là **review độc lập, không cấp quyền triển khai**. Sau báo cáo, hãy đề xuất session/task tiếp theo ở trạng thái `PROPOSED_ONLY` hoặc `BLOCKED_DEPENDENCY`, nêu dependency, write-set và phép kiểm. Tôi sẽ quyết định việc coding/render sau khi đọc kết quả.
