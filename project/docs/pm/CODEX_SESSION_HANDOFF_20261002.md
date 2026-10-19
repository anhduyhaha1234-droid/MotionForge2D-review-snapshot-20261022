# Session: MotionForge2D — bàn giao Codex ngày 02/10/2026

Tài liệu để một phiên Codex mới tiếp quản mà không nạp toàn bộ chat cũ. Đây là bản ghi trạng thái tại lúc bàn giao, không phải bằng chứng rằng runtime/owner vẫn giữ nguyên sau đó. Trước preflight hoặc soạn prompt quản lý, đọc toàn bộ `C:/Users/Admin/MotionForge2D/docs/pm/HERMES_AUTOPILOT_RULES.md`. Chỉ thị mới nhất của người dùng có ưu tiên hơn tài liệu cũ.

## Current state — đang dừng ở đâu

- Đã hoàn tất công bố snapshot code và tài liệu lên GitHub, kiểm remote refs và nội dung. Không cần làm lại việc push chỉ vì đổi phiên Codex.
- Đã viết và công bố prompt Hermes ngày 02/10: **tách cảnh/đoạn → ảnh cảnh bằng ComfyUI → WAN thay diện mạo theo video nguồn → ghép đủ video/audio → vision/QC**. Codex chưa dispatch Hermes và chưa chạy GPU trong đợt này.
- **Phát hiện mới ngay khi bàn giao:** bản prompt local trong outputs đã đổi sau publication: 31863bytes, SHA256 `3e357d7c16d0b13596d7f8e91133fa1ba6b86aba40e5172a08e0b91a2c22d206`, LastWriteTimeUtc `2026-10-02T04:21:11.2795132Z`; có hai đoạn bối cảnh/lời thoại Agribank chen ở dòng30–41. Chưa xác định ai sửa hoặc có phải yêu cầu mới hay không. Không coi nội dung này là transcript thật; không ghi đè/xóa thay đổi. Bản đã công bố còn nguyên tại `C:/Users/Admin/Documents/Codex/work/mf-external-review-20260929/docs/external-review/updates/20261002/prompt-20261002/NEXT_HERMES_DEMO_PROMPT.md` (30899bytes, hash b141e04c... ghi đầy đủ ở Key results); checkout này vẫn clean, HEAD f3917d... tại kiểm cuối. Dùng bản đóng băng này để đối chiếu contract đã bàn giao, không nhầm file outputs hiện tại vẫn khớp receipt cũ.
- Đã tìm và sửa trong **bản sao graph dùng thử** lỗi pose window của WAN. Chưa có inference xác minh bản sửa; chưa có video mới được Codex nghiệm thu.
- Trạng thái sản phẩm: `NOT_APPROVED / NOT_CLOSED`, `QUALITY_ACCEPTED=0`. Terminal khi Manager nộp: `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`. Không chuyển sang approved chỉ vì test, packet hoặc publication pass.
- M1-01/F01–F04 chưa đóng; S12/S13 chưa nghiệm thu. UI/tool/batch tạm để sau mẫu video. Mẫu media thành công cũng không tự động đóng sản phẩm.
- `get_goal` kiểm ở lượt bàn giao trả `goal: null`; đừng đọc ghi chú goal active/blocked lịch sử thành trạng thái hiện tại. Mục tiêu sản phẩm vẫn còn; kiểm công cụ goal của phiên mới trước khi mô tả trạng thái của nó.

**Việc đầu tiên của phiên mới:** đọc rules + tài liệu này + overlay hiện hành trong handoff chuẩn; đối chiếu prompt đã công bố với local drift vừa ghi nhận, kiểm git status/HEAD chỉ ở các checkout cần thiết, rồi xác định người dùng đã giao prompt 02/10 cho Hermes và có packet mới chưa bằng bằng chứng local hoặc đường dẫn người dùng cung cấp. Nếu có packet mới, review nó độc lập. Nếu chưa có, cung cấp bản prompt đã công bố và báo local drift, không tự khởi động Hermes hoặc tạo một vòng nghiên cứu/kế hoạch mới. Không coi việc chuyển phiên là quyền xóa/sửa lại prompt local đã được tác nhân khác thay đổi.

## Task specification — yêu cầu đã chốt

MotionForge2D biến video nguồn thành video với **toàn bộ diện mạo mới**: nhân vật, vật thể và bối cảnh; vẫn giữ sát **động tác, tương tác/tiếp xúc/che khuất, camera, các điểm cắt, timeline và audio gốc**. Không chuyển thành text-to-video chỉ gần giống nội dung.

Người dùng đã chốt: “Vẫn giữ sát động tác, camera và timeline gốc; chỉ thay toàn bộ diện mạo.” Dùng kho nhân vật riêng, một cast nhất quán xuyên cả bộ video; không đề xuất nhân vật khác mỗi video. WAN là model video được yêu cầu; ComfyUI điều phối các bước. Tái sử dụng repo/node/workflow có sẵn đã đối chiếu runtime trước khi viết mới.

Ưu tiên hiện hành: **mẫu video thật thành công trước, sau đó mới đưa pipeline đã chứng minh vào tool vận hành**. Headless harness được phép trong prototype; phải ghi rõ đó chưa phải demo app end-to-end. Đừng lặp lại câu hỏi về mục tiêu/fidelity/cast đã trả lời.

Người dùng tự dispatch và đưa kết quả về: “việc giao cho hermes và báo cho bạn là việc của tôi cơ mà”. Phiên Codex mới làm reviewer/PM độc lập, không tự gửi message, resume hoặc launch Hermes. Đổi phiên Codex không đồng nghĩa đổi owner Hermes.

## Important files — đọc theo thứ tự, có chọn lọc

| Đường dẫn tuyệt đối | Vai trò / khi cần đọc |
|---|---|
| `C:/Users/Admin/MotionForge2D/AGENTS.md` | Hướng dẫn workspace; bắt buộc đọc toàn rules trong lượt viết prompt quản lý. |
| `C:/Users/Admin/MotionForge2D/docs/pm/HERMES_AUTOPILOT_RULES.md` | Đọc toàn bộ. §0.2 là override demo-first hiện hành; không kéo retry vô hạn/gate từng microtask cũ vào prototype. |
| `C:/Users/Admin/MotionForge2D/docs/pm/CODEX_SESSION_HANDOFF_20261002.md` | Bản bàn giao đang đọc. |
| `C:/Users/Admin/MotionForge2D/docs/pm/CODEX_PM_HANDOFF.md` | Đọc phần Current execution 02/10 trước; các phần Historical chỉ khi cần truy vết. |
| `C:/Users/Admin/Documents/Codex/2026-09-22/tr-ng-th-i-terminal-gi/outputs/mf-shotwise-demo-20261002/SESSION_OPENING_PROPOSAL.md` | Chủ sở hữu, scope, write-set, budget hiện hành. |
| `C:/Users/Admin/Documents/Codex/work/mf-external-review-20260929/docs/external-review/updates/20261002/prompt-20261002/NEXT_HERMES_DEMO_PROMPT.md` | Bản đóng băng khớp publication, dùng để đọc contract hiện hành và đối chiếu packet. |
| `C:/Users/Admin/Documents/Codex/2026-09-22/tr-ng-th-i-terminal-gi/outputs/mf-shotwise-demo-20261002/NEXT_HERMES_DEMO_PROMPT.md` | Bản local đã thay đổi sau push; có đoạn Agribank chưa xác nhận. Bảo toàn, không coi khớp receipt cũ. |
| `C:/Users/Admin/Documents/Codex/2026-09-22/tr-ng-th-i-terminal-gi/outputs/mf-shotwise-demo-20261002/PROTOTYPE_PREFLIGHT.json` | Bằng chứng source, model, runtime; metadata tại thời điểm kiểm, không chứng minh process hiện tại. |
| `C:/Users/Admin/Documents/Codex/2026-09-22/tr-ng-th-i-terminal-gi/outputs/mf-rebuild-skills-20261001/MOTION_WINDOW_FINDING.md` | Finding kỹ thuật đã review, giới hạn kết luận và bản graph sửa. |
| `C:/Users/Admin/Documents/Codex/2026-09-22/tr-ng-th-i-terminal-gi/outputs/mf-rebuild-skills-20261001/REUSE_EXECUTION_MATRIX.md` | Công nghệ/node có thể dùng lại; không cần nghiên cứu lại từ đầu. |
| `C:/Users/Admin/Documents/Codex/2026-09-22/tr-ng-th-i-terminal-gi/outputs/mf-github-refresh-20261002/FINAL_DELIVERY_VERIFICATION.json` | Receipt xác minh push; đọc nếu cần kiểm công bố. |
| `C:/Users/Admin/Documents/Codex/2026-09-22/tr-ng-th-i-terminal-gi/outputs/mf-shotwise-demo-20261002/PUBLICATION_RECEIPT.json` | Exact commit/hash prompt đã công bố. |
| `C:/Users/Admin/Documents/Codex/2026-09-22/tr-ng-th-i-terminal-gi/outputs/mf-goal-review-skills-20260929/REVIEW_AND_GOAL_CHECKLIST.md` | Checklist toàn sản phẩm trước chuyển hướng demo-first; dùng sau khi review mẫu, không coi mọi gate là đã pass. |

Không đọc toàn bộ outputs, chat Hermes hay logs để mở phiên. Chỉ mở packet/evidence liên quan finding đang xét. Skills đã cài; chọn ít skill phù hợp, không chạy lại cài đặt hoặc nạp mọi framework.

## System architecture — code, runtime và pipeline

**MAIN / tài liệu chuẩn:** `C:/Users/Admin/MotionForge2D`, master tại lần kiểm `a40e368f7c47c232cf2eeed9fb185c5972cb98ba`, có thay đổi chưa commit. Bảo toàn; không dùng nhầm làm baseline triển khai.

**INTEGRATION:** `C:/Users/Admin/Documents/Codex/work/mf-delivery-20260927/INTEGRATION`, branch `codex/mf-end-integration-0928`, HEAD `a52fca897906fd61a088016dd802718fdf06d217`, clean tại lần kiểm 02/10. Đây là source baseline được pin; không suy clean hiện tại từ bản ghi này.

**WIP chưa hợp nhất:** `C:/Users/Admin/Documents/Codex/work/mf-delivery-20260930/M1-01` có 4 file source; `C:/Users/Admin/Documents/Codex/work/mf-delivery-20260929/C19` có 3; `C:/Users/Admin/Documents/Codex/work/mf-delivery-20260929/C25` có 7. C11/C15/C22 có commit chưa tích hợp. Đã lưu vào snapshot GitHub; không cherry-pick/merge hàng loạt hoặc ghi đè. C19 có helper đặt sai scope và tham chiếu `canonical` chưa định nghĩa; không coi WIP này là fix chạy được.

**Backend thực:** FastAPI ở thư mục `app/`, entry `app/main.py` → `app/api/app.py`; không phải `backend/`. Lần kiểm 02/10 process uvicorn PID36088 chạy từ C25, `127.0.0.1:8041`. `/health`, `/docs`, `/openapi.json` trả 200, OpenAPI 308 path keys (có alias), không đồng nghĩa mọi API đã test. Health trả `{"status":"ok","service":"motionforge-2d"}`. API ví dụ `/api/v2/projects`, `/api/v2/characters`, `/api/jobs/{job_id}`. Config MAIN có port cũ 8002/8888; phải kiểm process/cwd trước khi sửa lỗi API/UI. VS Code đã mở MAIN, khác checkout đang chạy backend.

**ComfyUI runtime:** `C:/Users/Admin/Documents/Codex/work/mfv1/runtime/video14b/ComfyUI`; Python ở `C:/Users/Admin/Documents/Codex/work/mfv1/runtime/video14b/venv/Scripts/python.exe`. GPU đã ghi nhận RTX5070 khoảng12GB. Model baseline: `wan_animate_2_int8_convrot.safetensors` + LightX2V rank64; scene image bằng `flux-2-klein-4b-fp8.safetensors`, distilled4steps/cfg1/Euler. Không tự nâng cấp runtime/model giữa benchmark.

Luồng: source video/audio → transcript + shot/event/timeline → cast cố định → ảnh cảnh có đủ vai đúng vị trí → WAN dùng original clip điều khiển chuyển động cho từng chunk → QC/continuation/seam → ghép đúng timeline/audio → MP4 + so sánh + bằng chứng. Transcript là metadata, không thay video conditioning.

## Workflow — owner, budget và cách tiếp tục

Manager hiện pin `20260930_235002_3ac7f9`; demo worker `20260929_041810_bc7c61`, task `MF-DEMO-E2E-R5 / WAN-PROTOTYPE-01`. Worker M1 `20260928_181955_a6d89a` đang deferred. Manager mới do user giao phải ghi takeover và kiểm không có controller/writer trùng. Session DB label/ended_at không đủ chứng minh activity; không import Hermes chỉ để kiểm metadata.

Route Hermes theo prompt: `cmc/deepseek/deepseek-v4.1-flash`, `chat_completions`, fallback OFF; reasoning theo actual route. Vision phải thử actual image/tool/provider, không suy có vision từ tên model hoặc lời Manager. Route này dành cho Hermes, không phải lệnh đổi model của Codex.

Budget **chung cả prototype, không reset khi đổi prompt/ngày/session**: max10candidate (kể failed/partial/OOM/smoke), max8renderchunks/candidate, max40video submissions,20image,40vision; worker300/Manager60 observed model requests;6h từ dispatch đầu, initial+3technicalcontinuations. WIP1/GPU1. Các phép đo là observed counters; không tuyên bố có enforcement cứng khi chưa chứng minh. Transient retry tối đa2chu kỳ với backoff5phút; lỗi quota/auth/config phải chẩn đoán/dừng. Poll bằng script, tránh dùng LLM để chờ. Chi tiết đầy đủ trong prompt.

Nếu prototype đã chạy: tiếp tục đúng RUN, owner, counters/deadline và lưu evidence cũ. Nếu chưa: RUN dự kiến `C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261002/<UTC>-wan-shotwise`. Worker chỉ ghi RUN/tasks/MF-DEMO-E2E-R5/WAN-PROTOTYPE-01; Manager RUN/manager. Code/runtime/models/globalconfig/DB gốc protected. Không mở task UI tranh GPU.

Hermes tự vision/correct trong budget; không chờ Codex sau từng render. Dừng sớm khi mọi mandatory criterion PASS, không UNKNOWN, nộp `SELF_REVIEW_PASS_PENDING_CODEX`; Codex review cuối độc lập. Nếu sửa chunk A thì mọi continuation dùng output A cũ phải đánh STALE và render lại tới anchor độc lập. Không che lỗi bằng freeze/interpolation/crossfade hoặc đổi choreography/cast.

Lệnh read-only nhỏ khi cần xác nhận baseline (PowerShell):

```powershell
git -C 'C:/Users/Admin/Documents/Codex/work/mf-delivery-20260927/INTEGRATION' status --short
git -C 'C:/Users/Admin/Documents/Codex/work/mf-delivery-20260927/INTEGRATION' rev-parse HEAD
git -C 'C:/Users/Admin/Documents/Codex/work/mf-external-review-20260929' status --short
```

Kết quả lần bàn giao: hai status không in dòng; HEAD INTEGRATION là a52fca897906fd61a088016dd802718fdf06d217. Nếu khác, ghi drift và điều tra; không tự reset. Khi người dùng đưa packet: xác minh actual files/hash, source/cast, graph/model parameters, logs/counters và video cuối + so sánh đồng bộ; không chỉ đọc chữ PASS. Review chất lượng gồm thay đủ vai/vật thể/bối cảnh, giữ identity, contact/occlusion, motion/camera/cuts, continuity, frames/duration/audio và khả năng tái lập. Chỉ sau media proof mới lập microtask tích hợp tool, độc lập review trước task kế theo rules.

## Errors and corrections — finding phải giữ

1. Graph canonical `C:/Users/Admin/Documents/Codex/work/mf-delivery-20260927/INTEGRATION/app/media_workflows/wan_shot_v1.json`, node `672:587` WanAnimate2ToVideo đặt pose start/end đều0. Runtime `ComfyUI/comfy_extras/nodes_wan.py` dùng window này; với6step LCM, đầu schedule có thể còn pose/no-pose blend, các bước sau không dùng direct pose. **Không nói pose hoàn toàn vô tác dụng ở mọi bước hoặc đã chứng minh đây là nguyên nhân duy nhất.**
2. Template UI installed `C:/Users/Admin/Documents/Codex/work/mfv1/runtime/video14b/venv/Lib/site-packages/comfyui_workflow_templates_json/templates/video_wan_animate2.json` nối start sang cả end; export lại không sửa wire sẽ tái tạo lỗi dù widget end hiển thị1.
3. Bản API sửa chỉ end0→1 tại `C:/Users/Admin/Documents/Codex/2026-09-22/tr-ng-th-i-terminal-gi/outputs/mf-rebuild-skills-20261001/reuse_bundle/wan_shot_v1.motion_enabled.api.json`, SHA256 `7da45b824d0c0810a5ff318fcf713914fb211a6405985de9e22435a042e448c7`. 63nodes, còn lại giữ baseline. **Chỉ review tĩnh; chưa inference.** Timing/VRAM P6 cũ135.21s/10763MiB không dự báo full-pose graph mới.
4. WAN reference dùng `reference_image[:1]`; batch nhiều portrait không bảo đảm conditioning nhiều vai. Dùng ảnh cảnh đủ vai qua Klein multi-reference và original driving clip. Prompt cũ BOOK áp dụng sai mọi cảnh/source crops lặp lại không tạo cast mới. Phải rebind từng shot; tránh trộn WAN2.2 Animate và Animate2/LoRA khác generation.
5. Commit snapshot từng báo lỗi auto geometric-repack do internal ref `refs/codex/turn-diffs` hỏng. Commit/push vẫn thành công, remote đã kiểm. Không xóa internal refs; nếu bị lại có thể tắt auto-maintenance riêng command bằng `-c gc.auto=0 -c maintenance.auto=false` rồi kiểm kết quả thực.
6. Không coi packet gate19/19 hay test fixture xanh là quality acceptance. Không mở lại prompt cũ đã superseded, không đổi goal thành chỉ hoàn tất hồ sơ.

## Learnings — tiết kiệm quota, giữ đúng trọng tâm

- Các lượt trước tốn nhiều token vì context dài, cache thấp, lặp điều phối; tránh đọc toàn logs và gọi model để poll. Cần usable artifacts/finding cụ thể trong mỗi correction.
- Skills đã cài và audit ở `C:/Users/Admin/Documents/Codex/2026-09-22/tr-ng-th-i-terminal-gi/outputs/mf-rebuild-skills-20261001/SKILLS_INSTALL_REPORT.md`: 13skills/155files mới,445file cũ không đổi,10SpecKit giữ lại. Superpowers `DISABLED_BY_ADMIN`, không bypass; BMAD/gstack cache không phải runtime đã cài. Không tự cài toàn bộ vào Hermes.
- Dùng chọn lọc handing-off-sessions, motionforge-correction-closure-review, evidence-gap-review, ce-code-review/ce-debug, cost-aware-llm-pipeline theo task; đọc SKILL.md khi áp dụng. Không nhiều supervisor chỉ chuyển lời.
- New Codex session là reviewer mới tiếp quản, không có quyền làm chạy lại toàn prototype hoặc reset limits của Hermes. Không thêm vòng nghiên cứu công nghệ mới nếu actual runtime/hypothesis không thay đổi.

## Key results — kết quả có thể dùng ngay

**GitHub mới nhất:** https://github.com/anhduyhaha1234-droid/MotionForge2D/tree/review/20261002-full-code

**Tài liệu cho dev:** https://github.com/anhduyhaha1234-droid/MotionForge2D/blob/review/20261002-full-code/START_HERE_EXTERNAL_REVIEW.md

**Prompt Hermes đã công bố:** https://github.com/anhduyhaha1234-droid/MotionForge2D/blob/review/20261002-full-code/docs/external-review/updates/20261002/prompt-20261002/NEXT_HERMES_DEMO_PROMPT.md

Exact review commit `f3917d1525b9c10dfb0d2483a791bf16315762a2`; prompt SHA256 `b141e04c81b5f44d3b0de8a99d761a4a7b3bcde10762e59ef1f7edf930d5ed9b` (30899bytes). Local checkout `C:/Users/Admin/Documents/Codex/work/mf-external-review-20260929`, branch `codex/external-review-20260929`, clean lúc kiểm.

Repo là public tại kiểm02/10. Default `main` vẫn cũ `ee10e55a809c84d5cb5d4a3046a1ee78828528d0`; đừng dùng trang main để kết luận upload mới không có. Branch review chứa source baseline a52 ở root; WIP ở `review-snapshots-20261002/`, không phải tất cả đã tích hợp. Đã capture100worktrees/903records/821unique files (~11.85MB); cutoff code `2026-10-02T02:56:02.380416Z`. Đã kiểm852hash,13refs remote,3rawfiles exact; không credentials/env/database/models/runtime/node_modules mới được đưa lên. Không đổi visibility/defaultbranch, không mergePR.

Source benchmark: `C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20260929/cmc-correction-20260929T091814Z/tasks/MF-DEMO-E2E-R5/raw/source_12s.mp4`; SHA256 `fc18e859599f8feeb730ee9018413ced4c183f90a15e20ccc162433c4666c8cc`;12s/360frames/30fps/640x360/audio48kHzstereo. Các cut cũ121/241/343 cần xác nhận convention zero-based half-open; không bỏ short last shot.

Prompt02/10 đã được root kiểm consistency/publication; không tuyên bố có independent full review của revision này hoặc video acceptance. Bản bàn giao Codex hiện tại chỉ lưu local, không có trong commit f3917d đã push trước đó.

## Worklog — các bước đã làm

- Thu thập rules/handoff/checklist và giới hạn quyền; bảo toàn WIP chưa merge.
- Đối chiếu hướng transcript với yêu cầu reskin sát nguồn; giữ WAN + ComfyUI và original video conditioning.
- Audit/reuse runtime/workflows, tìm pose-window và multi-role input defects; chuẩn bị graph copy sửa một field.
- Hoàn thiện prototype prompt cho Hermes tự vision/correct có budget, một owner/GPU; không dispatch.
- Sửa prompt02/10 theo shot/chunk, continuation dependencies và QC ghép toàn clip; giữ counters nếu đã chạy.
- Xác minh backend8041 từ C25 và phân biệt với checkout MAIN mở VS Code.
- Công bố snapshot đầy đủ và prompt lên branch review; kiểm remote độc lập, không nghiệm thu sản phẩm.
- Người dùng yêu cầu đổi sang Codex session mới để giảm quota; lưu bản bàn giao này và cung cấp prompt khởi động gọn.
- Đối chiếu cuối phát hiện local prompt đổi sau push, ghi cả hai hashes và vị trí bản đóng băng; giữ nguyên local edits, chưa kết luận người sửa hoặc ý định.
