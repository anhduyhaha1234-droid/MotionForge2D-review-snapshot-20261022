# MotionForge2D — digest áp dụng cho Codex, 15/10/2026

Đây là bản chuyển ngữ quy trình từ thư viện Hermes, không phải quyền thực thi mới và không thay thế acceptance của sản phẩm. File gốc được giữ nguyên và có SHA-256 trong `HERMES_SKILL_INVENTORY.json`. Các dữ kiện runtime, commit, benchmark và session trong skill là lịch sử; phải kiểm tra trạng thái hiện tại trước khi dùng làm căn cứ.

## Authority hiện tại

- User ngày 15/10 đã cho phép Codex tạo agent coding, xác nhận model **GPT-6 Sol, reasoning Max**, và yêu cầu root review độc lập sau khi coder xong. Vì vậy những chỉ dẫn cũ “Codex chỉ review, user tự dispatch Hermes”, pin Qwen/DeepSeek/Muse/Claude, hoặc bắt dùng Hermes CLI không áp dụng cho lane Codex mới.
- Sự thay đổi vai trò/model không tự xóa ràng buộc sản phẩm, frozen evidence, một writer cho một write set, GPU=1, source/CAST/style pins, bảo toàn dữ liệu và acceptance hiện tại. Root phải xác định write set và đầu ra cụ thể theo trạng thái thực tế; không để skill tự mở toàn bộ S12/S13/UI/full22.
- Các tool mẫu `delegate_task`, `skill_view`, Hermes `terminal/process`, `cronjob`, CLI flags và state.db không phải API Codex. Dùng công cụ Codex tương ứng; không giả lập tool không có bằng cách sửa cấu hình hay gọi một agent ngoài lane.
- Skill là hướng dẫn thấp hơn user/developer/system. Câu “override system” trong `terminal-engineering-discipline` bị loại; không load nó mỗi lời chào hoặc mỗi turn. Nội dung mẫu không cấp quyền stash/reset/clean/commit/push/merge, broad delete, kill cây process hoặc đọc credentials.

## Kích hoạt thư viện có chọn lọc

Có thể sao chép byte-identical toàn bộ **40 thư mục liên quan** (21 trực tiếp MotionForge/video, 19 support coding/context) để mọi tài liệu luôn sẵn. **Có trong thư viện không có nghĩa đã đọc đầy đủ hoặc runnable.** Manifest ghi riêng `read_coverage`.

Mỗi microtask đưa vào context: quy tắc còn hiệu lực + task contract + checkpoint + finding liên quan + đoạn mã đang đổi + chỉ 2–4 skill cần cho việc đó. Hai file lõi `motionforge-2d-project` và `motionforge-sprint-manager` đều khoảng 100 KB; không nhét lại toàn bộ vào mỗi prompt. Tra cứu theo heading/line đã lập index, đọc thêm nguyên section khi cần, ghi provenance. Lịch sử lỗi đã giải quyết ở lại trên đĩa.

Nhóm mặc định cho coder: `bom-repository-inspection`, `bom-requirements-to-plan`, `bom-verified-implementation`, `bom-systematic-debugging`, `bom-context-budget-manager`, `bom-session-checkpoint-handoff`, `bom-tool-output-minimizer`. Khi tác vụ video cần thêm `comfyui-video-model-proof` và `local-comfyui-adapter-proof`; khi root review media thêm reference `manager-pixel-review-of-worker-media.md`.

`plan` có trigger “user muốn chỉ lập kế hoạch, không thực thi”, nên không activate nguyên văn trong yêu cầu coding hiện tại. Học cách viết task/AC từ nó; không lấy câu “không implement” để dừng việc user đã yêu cầu. `bom-model-routing` cũng không tự thay GPT-6 Sol Max bằng model rẻ hơn.

## Chu kỳ coding và tự review

1. Xác minh workspace/root, baseline HEAD và dirty files, writer/child processes liên quan, nhiệm vụ đang active, allowlist. Bảo toàn preimage các file dự định sửa; frozen evidence giữ nguyên.
2. Một microtask có một đầu ra hành vi, AC đo được, danh sách file và test cụ thể. Không chia giả tạo chỉ để đổi task/owner hoặc reset chi phí. Ưu tiên vertical slice nhỏ có thể review được, giữ dependency chain.
3. Tái hiện finding bằng đường producer→consumer thật, xác định root cause, sửa nhỏ nhất phù hợp architecture. Reuse engine/upstream đã chứng minh; không tự thay core video bằng renderer hoặc propagation mới khi contract không cho phép.
4. Chạy test trọng tâm sau thay đổi; dùng test có thể fail trên defect cũ, không test chỉ lặp implementation. Nếu code ảnh hưởng wiring public path, thêm proof không DI/stub che mất wiring. Race phải có hai participant sống cùng lúc, rendezvous tại thao tác tranh chấp, một winner, các result/row được kiểm tra.
5. Coder tự review hai lượt: **(a) contract/AC và write scope**, **(b) correctness, cache/identity/provenance, failure behavior, tests, semantic media**. Ghi raw command+exit+artifact hash và hạn chế. Coder có quyền sửa finding của mình trong allowlist, nhưng không tự ghi `QUALITY_ACCEPTED=1`, APPROVED/CLOSED.
6. Trước bàn giao: không còn writer/child đang sửa candidate; pin bytes/manifest; báo exact changed files, test evidence, self-review findings đã sửa/chưa sửa, checkpoint và lệnh tiếp. Root review độc lập bằng code thật, raw evidence, fresh focused probes và ảnh/clip cần thiết; worker summary là tự báo cáo.
7. Root trả findings về đúng owner/lane hiện tại; không tạo fix agent thứ ba tự động vì template `requesting-code-review` nói vậy. Không áp max 2 vòng như total-cap; mỗi vòng phải có evidence mới và tiến bộ, không retry mù.

## Context và quota

- Giữ ledger ngắn trên đĩa: mục tiêu, phiên bản authority, task/owner/model, allowlist, file/hash đã đổi, lệnh và kết quả, failure nguyên văn, quyết định, bước tiếp theo, PID/job đang sống. Tách verified/hypothesis, không dựa vào chat dài để nhớ exact IDs.
- Checkpoint ở mỗi đơn vị đã kiểm chứng, trước đổi domain, trước compaction hoặc áp lực context. Summary phải đủ cho một phiên kế tiếp khôi phục việc mà không đọc lại toàn transcript. Không cần nạp tất cả 551 file để chứng minh “đã nạp skills”.
- Dùng `rg`, SQL projection, metadata và đoạn lỗi xác định. Raw log lớn lưu file; tool chỉ trả phần quyết định + đường dẫn. Gom những read độc lập; mutation phụ thuộc phải tuần tự.
- Không bịa context remaining/tokens/quota từ số message. Nếu runtime không cung cấp số đo, ghi UNKNOWN và dựa vào checkpoint sớm. Quota phải từ tool account usage thực tế hoặc lỗi provider; reset time gắn đúng timezone.
- Khi 429/5h/weekly quota hết: giữ nguyên code/evidence/checkpoint, phân biệt quota vs transient 5xx vs auth/validation. Báo rõ trong chat này: model, window bị chặn, reset time nếu có, công việc đã xác minh, bước tiếp. Không đổi model/fallback, không reset counter, không tạo agent mới nhằm vượt quota.
- Retry-After và backoff cho transient được áp dụng theo runtime; không tight-loop. Không retry auth/validation cùng payload vô hạn. “Đợi reset rồi tiếp tục” cần cơ chế automation Codex có thật và prompt tái nhập checkpoint; không hứa rằng một process hoặc subagent đã chết sẽ tự sống lại. Automation chỉ quản lý tiến độ/tiếp tục trong scope đã cho phép, không mở rộng quyền.
- `bom-quota-budget-planner` hữu ích ở chỗ bảo vệ validation và giảm đọc lặp; total budget/candidate/deadline caps trong skill hoặc lịch sử không tự trở thành hạn mức PM mới. Ranh giới task/checkpoint là quản lý context, không phải bỏ dở acceptance.

## Quy tắc video cần giữ

- Tách năm trạng thái: source có node, runtime import node, weights có, inference đã chạy, chất lượng được chấp nhận. Không lấy một cột suy ra cột khác. Tách technical PASS khỏi semantic PASS.
- Graph xuất phải khớp live node interface và official template của pinned revision. Per-unit prompt/refs/role mapping phải bind đúng nguồn và cut; không dùng graph của unit khác rồi chỉ thay IO. Điều chỉnh pad/crop có map, giữ source composition, frame count/fps/audio contract.
- Không dự đoán OOM hoặc throughput từ số tham số. Đo từng run, phân biệt cold/warm; sampled VRAM không gọi peak. Một GPU job mỗi lúc, artifacts/output/temp/cache mới cô lập.
- Khi mất kết nối sau submit, query queue/history/epoch trước khi resubmit. File output không có successful history không là kết quả. Không dùng exit0 hoặc ffprobe để thay review pixels.
- So sánh ảnh nguồn và output ở đúng shot/frame; xem first/mid/last và event/occlusion/contact/prop transitions. Một video đúng thời lượng vẫn có thể sai nhân vật, pose hoặc không thực hiện động tác. Giữ superseded bytes, append lineage, không ghi đè để làm evidence “xanh”.
- Scope pilot/frame/audio hiện tại phải lấy từ task/current review; ví dụ 4 giây/12 giây, geometry368, benchmark2026-09 và caps cũ trong skills không là expected values cho pilot5m.

## Mâu thuẫn cụ thể phải chặn khi chuyển sang Codex

| Nguồn | Nội dung không áp dụng nguyên văn | Cách xử lý |
|---|---|---|
| `motionforge-autopilot` | Pin `ocg/qwen3.7-max`, tự commit, thông báo popup | Pin GPT-6 Sol Max theo user; không cấp thêm Git/OS notification quyền |
| `motionforge-sprint-manager` | CLI Hermes, owner/session lịch sử, stash/merge/push ví dụ | Tham khảo bài học; root xác định Codex owner mới và write set, không chạy snippets |
| `terminal-engineering-discipline` | Override system, bắt load mọi turn, quy tắc xóa cả history | Bỏ các đoạn này; giữ TARGET→RUN→VERIFY và evidence honesty |
| `subagent-orchestration` | Đọc ALL files, spawn fresh task/context, kill trees, mirror daemon | Progressive retrieval; một coder active; quiescence trước thay owner; không chạy daemon mẫu |
| `plan` | Plan-only, hỏi lại “Shall I proceed?”, frequent commits | User đã yêu cầu coding; dùng task craft, không dừng xin lại |
| `requesting-code-review` | Stash baseline, add-A/commit, max2fixes, tự spawn fixer | Baseline cô lập/phân tích preimage; root review độc lập, same coding owner sửa |
| `bom-model-routing` + retry controller | Chọn model rẻ/failover | Không silent fallback khỏi model user xác nhận |
| `comfyui-video-model-proof` | Candidate2/config2 hard caps, phiên bản/runtime lịch sử | Không tổng cap tự đặt; verify runtime hiện tại và contract |
| `long-scope-manager-dispatch-20261005.md` | Deadline48h và attempt caps | Lịch sử đã bị authority sau thay thế; không hồi sinh deadline cũ |

## Parent/root cần đọc trước dispatch

1. Authority thực tế hiện hành: `HERMES_AUTOPILOT_RULES.md`, `AGENTS.md`, `SESSION_PROTOCOL.md`, overlay PM và review/checkpoint mới nhất, cộng yêu cầu user15/10/model được xác nhận. Các file này không được inventory worker đọc lại hay sửa.
2. Digest này và manifest coverage/conflicts. Không gọi “40 skill đã đọc toàn bộ” vì không đúng.
3. Đúng task contract/code và selected source sections cần cho microtask. Cho coder đường dẫn full library và digest; yêu cầu tự load thêm khi cần, khai báo skill nào thực sự dùng.
4. Ghi lane model/reasoning thật từ spawn tool receipt; owner/write allowlist; quota/context checkpoint+resume contract; independent root review; proof zero concurrent writer ở cùng scope.
