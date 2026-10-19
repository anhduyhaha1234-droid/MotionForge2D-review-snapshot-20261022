# Kiểm kê kỹ năng Hermes liên quan MotionForge2D — 15/10/2026

Đã quét **171 SKILL.md** bằng `rg --files`, chọn **40 thư mục**: **21** có nội dung trực tiếp MotionForge/ComfyUI/SAM/WAN/VACE/video proof, và **19** hỗ trợ coding, planning, review, context/quota. Toàn bộ 40 thư mục gồm **551 file, 4.094.180 byte** đã có SHA-256 từng file để root nhập byte-identical vào thư viện dự án.

Chỉ inventory/report được ghi trong thư mục này. Không gọi Hermes, không thay registry/runtime/config, không chạy hook/script trong skills, không cài global, không đọc auth/env/credentials. Đây không phải một product review hay bằng chứng runtime hiện tại.

## Sản phẩm bàn giao

- `HERMES_SKILL_INVENTORY.json`: metadata tất cả171 skills; source directory/relative directory; SHA/size/mtime từng file trong40 thư mục; heading index; coverage; six bundles và dependencies thiếu.
- `SELECTED_SKILL_NAMES.txt`:40 relative directory paths.
- `ACTIVE_DIGEST_VI.md`: quy tắc portable sang Codex, authority override ngày15/10, context/quota/checkpoint, self-review và independent review, video acceptance, những đoạn không được chạy nguyên văn.
- `build_inventory.py`: script read-only có thể tái tạo inventory; chỉ ghi các file trong chính thư mục này.

## Coverage — giữ chính xác nghĩa “nạp”

Đã đọc đầy đủ **21 SKILL.md**, gồm5 skill trực tiếp project/video và16 support. Đã đọc một phần3 file rất dài: `motionforge-2d-project` (1–193), `motionforge-sprint-manager` (1–103), `terminal-engineering-discipline` (đọc đoạn đầu/cuối trong lần output bị truncation). Những phần chưa xem và16 skill còn lại chỉ được quét/hash/index, **không được ghi là đã semantic-load đầy đủ**. Manifest có `read_coverage` từng skill.

References đã đọc đầy đủ: `motionforge-sprint-manager/references/long-scope-manager-dispatch-20261005.md`, `motionforge-sprint-manager/references/delivery-takeover-20260928.md`, `motionforge-2d-project/references/delivery-takeover-scene-unit-proof.md`, `comfyui-video-model-proof/references/manager-pixel-review-of-worker-media.md`, `comfyui-video-model-proof/references/delivered-clip-verification.md`.

Hai file lõi MotionForge đều khoảng100KB, ngoài ra nhiều skill orchestration ~100KB. Vì user yêu cầu tránh quá context, cách phù hợp là **toàn bộ nội dung có sẵn trên đĩa + digest ngắn được kích hoạt + progressive retrieval từng task**. Không nạp cả551 file vào coder. Root có thể sao chép40 thư mục giữ nguyên byte; kiểm tra source/destination hash rồi ghi import receipt. Không overwrite globals có sẵn.

## Phát hiện ảnh hưởng trực tiếp

1. **Authority không portable nguyên văn.** Pin Qwen/DeepSeek/Muse, role Manager-only, Hermes CLI và owner IDs lịch sử không được dùng để chống yêu cầu mới GPT-6 Sol Max/Codex coding. User mới cho phép coding+subagent; vẫn cần bảo toàn product gates, write ownership và frozen evidence.
2. **Skill có hướng dẫn không an toàn nếu coi như quyền.** `terminal-engineering-discipline` tự tuyên bố override system; `requesting-code-review` đưa mẫu stash/reset/add-A/commit và tự spawn fixer; các skill orchestration chứa kill/restart/watchdog/push/merge. Không thực thi chúng khi import; digest chỉ giữ phần phương pháp có ích.
3. **Một số bundle không đầy đủ.** `bom-coding.yaml` thiếu `bom-ui-render-review` và `bom-precommit-review`; `bom-research.yaml` thiếu `bom-github-research-ranking` và `bom-competitor-comparison`; `bom-work.yaml` thiếu `bom-supplier-document-check`. `bom-build-efficient` và `bom-quota` không thiếu skill được tham chiếu, nhưng quota/model/failover procedures cần override. Không gọi bundle đầy đủ chỉ vì file YAML tồn tại.
4. **Skills nhiều lớp lịch sử, không phải live state.** Benchmark GPU, Comfy versions, task statuses, accepted commits, limits, source spans và node/weight lists trong file đều cần timestamp/proof hiện tại. Đặc biệt tài liệu05/10 chứa total budget/deadline đã có khả năng bị rules sau thay thế; không hồi sinh chúng.
5. **Hữu ích nhất ngay:** task có AC cụ thể, state ledger nhỏ, selective file reads, same-writer correction, self-review trước independent review, provenance/cache fail-closed, real public-path tests, semantic pixel/event checks. `comfyui-video-model-proof` phân biệt source/import/weights/inference/quality rõ ràng và tránh nhầm ffprobe thành chất lượng.

## Gợi ý import/dispatch cho root

Tạo package project-local mới gồm `vendor/hermes/<relative_directory>` bằng40 mục manifest, giữ nguyên tên/cấu trúc/reference paths, bên ngoài là digest override và source manifest. Chỉ đánh dấu IMPORTED sau destination hash match toàn bộ551 file. Việc sao chép do root thực hiện; inventory worker chưa import.

Trước coder: root đọc actual governing docs/current review, xác minh zero writer ở scope dự kiến, cấp allowlist và acceptance cho microtask đầu, dùng `spawn_agent(model='gpt-6-sol', reasoning_effort='max', fork_turns='none')` với compact packet. Không chuyển toàn bộ lịch sử này. Coder tự kiểm tra rồi trả frozen candidate; root review độc lập. Context handoff phải bảo toàn bytes và next action; quota exhausted báo tại chat hiện tại, không tự đổi model hoặc tạo agent để lách giới hạn.
