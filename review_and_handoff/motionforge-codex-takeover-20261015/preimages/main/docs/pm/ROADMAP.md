# MotionForge 2D - Epic, Sprint and Task Roadmap

**Planning model:** outcome-based, dependency-gated  
**Execution rule (30/09/2026):** one Task ID = one Hermes chat/session;
WIP=1; independent Codex review after each microtask before the next step.
See canonical HERMES_AUTOPILOT_RULES.md §0; older parallel plans are historical.  
**Estimate unit:** session-sized, not calendar commitment

**Approved target overlay:** [Source-Locked 2D Target Profile](TARGET_PROFILE_2D_SOURCE_LOCKED.md)

Future S05-S12 acceptance contracts must apply this overlay before a task packet
is issued.

## Current execution overlay — 2026-10-14: R6f checkpoint CHANGES_REQUESTED

Current packet/prompt/proposal: `C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-r6-checkpoint-review-20261014/`.
R6→R6f đã chạy; quota429bọc503 làm dừng13/10 03:17+07, chưafinalsubmission.
ReceiptNEEDS_RECONCILIATION, terminalCONTINUE_REQUIRED/12UNKNOWN; registryRUNNING
cũ. Snapshot14/10 no worker/render,queueempty,6leasesRELEASED; quota phải kiểm lại.

Mastere3107a52…e48e đủ9000f300s/AVdecode0/audio3windowslag0; review54midpoints+
23frames thấy S74 cải thiện nhưng S33/S61 portrait sai/S73 mất sổ. Canonical12Q:
9FAIL+2UNKNOWN+1PASSengineering. Correctiongates/eventkeys/tracking/cache/QA/
matrix/terminal trước validhardexcerpts→candidate5phút→ManagerheldoutQA→Codex.

SameMF-DEMO-LONG-01/RUN/R6/owners/counters; Manager20261012_002032_daa36c,worker
20261007_234033_cc0b6d; context/incident/quota/zero-writer audit trước resume.
Newcandidate namespace trongR6,oldmedia/receipts/terminals frozen; patchonly
implementation cópreimages. T01–T15/upstream/CASTB/source-lock/noPMbudget/WIP1GPU1
giữ. User tự giao prompt, Codex khôngdispatch. QUALITY0/S12S13notapprovednotclosed;
full22/tool/backend/UI/integration BLOCKED_DEPENDENCY.

## Historical execution overlay — 2026-10-12: R6 triển khai đúng tài liệu và bằng chứng

Technical audit/prompt/proposal hiện hành: `C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-tech-conformance-20261012/`.
T01–T15 gắn vào12Q: exact model/API/upstream call path, masks/canvas/frame map,
latent trim, paired tracking, event keys và semantic gate/cache. Không thêm
framework/owner/scope. FLUX4B4steps đúng; Rerender stage2 chưa có stage1
constraints. Có source/CPU proofs, chưa có R6 inference hay acceptance mới.

R5 đủ9000frames/300s nhưng Codex CHANGES_REQUESTED: sai actor/pose/contact,
ghost và regression S33/S61/S74. Matrix10FAIL+1UNKNOWN+1PASS engineering;
QUALITY0/codex_accepted0, S12/S13 NOT_APPROVED/NOT_CLOSED. Full22/tool/integration
BLOCKED_DEPENDENCY. Không gọi residual MINOR hoặc self-QC12PASS là acceptance.

R6 cùng TaskMF-DEMO-LONG-01/RUN/counters, Manager20261012_002032_daa36c,
worker20261007_234033_cc0b6d; context/incident audit trước continuation.
R4/R5 frozen. Scope pilot[2820,11820), CAST B/flat2D, WIP1/GPU1, noPMbudget.
Source ledger/visibility/pose đúng→upstream crop+stitch→VACE có TrimVideoLatent
và paired S62/S73 đối chứng keys-route→chọn route đạt→event-aware propagation/
semantic gate/cache→pilot5phút→Manager held-out QA→Codex. Không thêm core mới.

Harness fresh51/51 đạt, true-race proof còn thiếu; bảo toàn16 frozenR4 evidence
drift và stale nested R5manifest. Tests mới output r6, không rewrite lịch sử.
Packet/proposal/review/prompt Hermes và prompt Codex mới:
`C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-r5-review-20261012/`.
User tự giao Hermes; Codex không launch/message/resume, không đổi registry.

## Historical execution overlay — 2026-10-11: R4 FAIL, R5 khóa actor và contact

R4 có pilot9000frames/300s decode sạch nhưng Codex CHANGES_REQUESTED: identity,
role/visibility/contact/ghost và source-passthrough còn lỗi P1. Matrix độc lập
9FAIL+2UNKNOWN+1PASS engineering. SAM2 và Rerender đã inference một phần nhưng
graph fallback bỏ CAST refs, QA/cache và Manager lease/terminal còn bypass.

R5 cùngMF-DEMO-LONG-01/RUN20261005T1643Z-wan-long/counters; Manager hiện hành
20261011_123932_c101dc, exactworker20261007_234033_cc0b6d. R4 frozen. Source-event
storyboard → actor-isolated CropAndStitch/FLUX refs + SAM2 masks → approved keys
→ Rerender và source-unit VACE1.3B đối chứng S62/S73 → route đạt → pilot5phút
→ Manager held-out QA → Codex. CoTracker contact chạy thật; ProPainter/MoCha
conditional. Model/node local hoặc74componenttests không chứng minh video đạt.

Packet hiện hành user tự giao, Codex không launch/message/resume:
`C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-r4-review-20261011/NEXT_HERMES_MANAGER_PROMPT.md`.
Matching proposal/review/research/matrix cùng thư mục; rules§0.7. Giữ CAST B,
flat2D,pilot[2820,11820),WIP1GPU1,noPMbudget; full22/UI/backend/tool/integration
BLOCKED_DEPENDENCY. QUALITY0,codex_accepted0,S12/S13NOT_APPROVED/NOT_CLOSED.

## Historical execution overlay — 2026-10-11 trước R4 submission: áp dụng stack upstream

R3D vẫn FAIL; chưa có C/r4 lúc12:14+07. Cùng MF-DEMO-LONG-01/RUN/owner,
CAST B/style/pilot300s và12rows Q01–Q12. Không mở task mới hoặc reset counters.
User yêu cầu dùng repo có sẵn cho cả pipeline lỗi và hiệu quả Manager:
ref binding FLUX.2 → SAM2 masks/approved keys → Rerender standalone → QA;
CoTracker ở contact khó, ProPainter khi cần clean plate. MoCha fallback có
điều kiện giữ như packet trước. Tải/pin source không là runtime/media pass.

Manager phải dùng structured terminal result và reconcile child/GPU lease;
reference validator đã qua25ca cô lập, live consumers chưa patch. Không thêm
framework; reuse native todo/compression/process và Pydantic/psutil/filelock.
Source-unit proof rồi pilot đủ54shots, Manager verify, Codex review; full22phút/
tool/UI/backend/integration vẫn BLOCKED_DEPENDENCY. NoPMbudget/WIP1GPU1 giữ.

Packet hiện hành (user tự giao, Codex chưa launch/message/resume):
`C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-r4-stack-update-20261009/NEXT_HERMES_MANAGER_PROMPT.md`.
Proposal cùng thư mục; rules§0.6 canonical. QUALITY0,codex_accepted0;
S12/S13NOT_APPROVED/NOT_CLOSED.

## Historical execution overlay — 2026-10-09: R3D FAIL, reuse upstream + CAST B

R3D đủ300s/decodeclean nhưng đồng bộ nhân vật, props/contact/occlusion vẫnFAIL.
Codex fresh repro palettegate và terminalclassifier đều có falsePASS. Không
chữa bằng dán sprite/fill cố định tiếp. User yêu cầu áp dụng repo có sẵn và
một bộ mặt khác rõ nguồn: CAST B concept đã chọn; assets/views cần khóa.

Correction r4 cùngMF-DEMO-LONG-01/RUN/exactworker, contextaudit§4. Upstream
Rerender standalone + approvedkeyframes là route trước, MoCha workflow là
fallback có điều kiện. Source đã tải, chưabuild/install/inference trênmáy.
NoPMbudget/counters/WIP1GPU1 giữ; pilot[2820,11820),9000f/S21–74.
FrozenW7/C1/C2/R3; full22phút/tool/UI/integration BLOCKED_DEPENDENCY.

Packet hiện hành:
`C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-r3-review-20261009/NEXT_HERMES_MANAGER_PROMPT.md`.
User tự giao, Codex chưa launch/message/resume. QUALITY0,codex_accepted0,
S12/S13NOT_APPROVED/NOT_CLOSED; policy§0.6 ghi reuse và thaycast.

## Historical execution overlay — 2026-10-08 tối: C2 pilot CHANGES_REQUESTED

Pilot300s technicalpass nhưng identity/count/action/cameraFAIL và semanticgate
hashbypass được Codex tái hiện. C2 chưa triển khai actualmasks/tracks/layerlock.
Mở correctionr3 trong cùng MF-DEMO-LONG-01/RUN/owner saucontext audit§4:
sourceevents/castlayers→semanticgate+actualcompositorproof→300s→Codex review.
Nguồn[2820,11820),S0021–74;fixedstyle/WIP1GPU1/noPMbudget/counters giữ nguyên.
FrozenW7/C1C2 được giữ; full22phút/tool/UI/integration BLOCKED_DEPENDENCY.

Packet hiện hành: `C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-c2-review-20261008/NEXT_HERMES_MANAGER_PROMPT.md`.
User tự giao; Codex chưa launch/message/resume. REVIEW_REEL45,5s chỉ là evidence,
chưa cór3correctedvideo. QUALITY0,codex_accepted0,S12/S13NOT_APPROVED/NOT_CLOSED.

## Historical execution overlay — 2026-10-08: identity5phút trước full

W7 đã đủ39634frames/22:01 và decodeclean, nhưng Codex CHANGES_REQUESTED vì
đổi mặt xuyên shot, sai vai, mất người và sai động tác. QUALITY_ACCEPTED0;
S12/S13NOT_APPROVED/NOT_CLOSED. Nhãn MINOR của Hermes không đóng actor errors.

User cho phép test5phút để tập trung identity. Chốt source01:34–06:34,
[2820,11820),9000frames30fps640×360;54shotS0021–S0074. Cùng Task/RUN,
Manager20261007_231246_986005 và worker20261007_234033_cc0b6d, sau context/
zero-writer audit. Globalentity+castbible→actortracks/masks/contact→assets2D
khóa+WANmotion/composite→QA5phút→Codex. Full22phút/tool/UI/integration vẫn chờ.
Không reset counters, không PMbudget cap, WIP1/GPU1. FrozenW7 được giữ nguyên.

Packet hiện hành:
`C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-identity-review-20261008/NEXT_HERMES_MANAGER_PROMPT.md`.
User tự giao Hermes; Codex chưa launch/message/resume. Bản comparison5phút đã
tạo trong cùng thư mục chỉ là baseline W7, chưa phải video correction.

## Historical execution overlay — 2026-10-07 tối: khôi phục W2r context failure

W2r đã chạy correction và kết thúc16:10 vì provider context overflow sau repeated
compaction; không phải hoàn thành hay hết PM budget. Có165chunkR2/28610frames
header-valid (~15:54), checkpoint đã ghép867,433s; chưa quality accepted.
S0164 gate/hash lệch, counters/resume stale; heartbeat nhận nhầm conhost và sai
receipt path. Đề xuất Manager mới + một recovery worker sau zero-writer/owner
transfer đúng§4, cùng Task/RUN/source/style/counters, WIP1/GPU1. Không reset pipeline.

Packet hiện hành:
`C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-context-recovery-20261007/NEXT_HERMES_MANAGER_PROMPT.md`.
User tự giao; Codex chưa dispatch hoặc đổi registry. Bảo trì context bằng checkpoint,
invocation gọn + tự continuation cùngSID và nén sớm; không cap tổngbudget. Khóa cast
toàn timeline, QC đúng bytes trước adopt và tiếp tục166–225, sửa phần lỗi đã chứng minh.
QUALITY_ACCEPTED0; S12/S13 NOT_APPROVED/NOT_CLOSED; chưa mở code/integration.

## Historical execution overlay — 2026-10-07 đầu ngày: review66s FAIL; storyboard/cast correction đề xuất

Bổ sung reviewpartial294s cùng round:16shot có evidence sai cảnh, tổngspan87,9s;
còn lỗi motion khi anchor đúng và incident duplicate runner. Packet hiện hành
đã gộp F13–F15/§6.1: scene assets dùng lại, motion gate, atomic ownership và
tiến độ theoQC. Không mởscope/owner mới; user vẫn tự giao, registry USER_STOP.

MF-DEMO-LONG-01 cùng RUN20261005T1643Z-wan-long, Manager20261005_232945_f060a9,
worker20261005_235131_0caeab hiện USER_STOP. Codex chưa dispatch. 54chunks đã
render không đồng nghĩa accepted; checkpoint66s sai cảnh/cast/count/entry ngay
từ anchor, còn cache/QC/assembly/state-gate defects. Full-pose0→1 và continuation
đã có trong savedgraphs, không coi sửa tĩnh cũ là proof đạt.

Phương án để user giao: khóa cast assets toàn phim → storyboard/events có hình
theo block → anchor/inputQC → WAN cho motion nhân vật,2D route cho đồ họa phù hợp
→ sửa66s đầu của master → tiếp tục full22:01/globalQC. WIP1/GPU1, cùng owner;
không vòng chọnstyle/test12s. Policy§0.4 không budget giữ nguyên, cumulativeledger
không reset; fixed6h childkill và watchdog thiếu quality/stopgate cần correction.

Packet hiện hành `C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-storyboard-review-20261007/NEXT_HERMES_PROMPT.md`;
REVIEW_VI.md và SESSION_OPENING_PROPOSAL.md cùng thư mục. Chỉ user giao packet
mới kích hoạt resume sau stop. Tool/code/integration chờ media; QUALITY_ACCEPTED0,
S12/S13 NOT_APPROVED/NOT_CLOSED.

## Historical execution overlay — 2026-10-06: hoàn thiện MF-DEMO-LONG-01, không budget tự đặt

Theo user và canonical§0.4, bỏ trần tổng thời gian/calls/candidates/submissions/
correction/continuations của task đã giao. Giữ ledger, progress/liveness và hard
limits thực của provider; không blind retry hoặc tự mở scope khác. Tiếp tục cùng
RUN20261005T1643Z-wan-long và worker20261005_235131_0caeab sau audit activity,
không tạo lại owner chỉ vì policy đổi. Manager registry20261005_232945_f060a9.
Receipt gần nhất được đọc là output-truncation, timed_out=false; payload/patch
nhỏ và exact-owner continuation là bước sửa, không chỉ xóa số48h trong prompt.
Source22:01, một cast/style2D, frame/cut/action/audio continuity giữ nguyên.
Packet LONG_VIDEO_HERMES_PROMPT.md đã cập nhật06/10; user tự giao, Codex không
launch/message. Runtime caps phải được Manager áp vào harness của mình; chưa
coi là đã đổi chỉ vì file rules được cập nhật. WIP1/GPU1; code/UI/S12/S13 còn chờ.

## Historical execution overlay — 2026-10-05: MF-DEMO-LONG-01 PROPOSED_ONLY (preflight xong, chưa dispatch)

Packet05/10 là PROPOSED_ONLY; lượt này chỉ đọc rules/handoff/roadmap + preflight rồi báo
`RULES_LOADED`/`PREFLIGHT_OK`. Không dispatch worker, không tạo RUN/write-set, không render.
Ngân sách scope dài (§6 packet) chỉ kích hoạt khi user giao thực thi. Scope vẫn là full
nguồn SHA256 `5a175454…` (39,634frames/30fps/640×360), một cast/style 2D xuyên suốt, một
main assembly + tối đa một vòng sửa cục bộ. Đồng bộ identity/hành động/contact/camera/cuts/
frame coverage/audio là bắt buộc; ví dụ12s cũ chỉ là tham chiếu kỹ thuật. Xem rules§0.3 và
packet `.../outputs/motionforge-review-20261005/LONG_VIDEO_HERMES_PROMPT.md`. WIP1/GPU1;
code/UI/integration/S12/S13 chờ; QUALITY_ACCEPTED=0, S12/S13 chưa đóng.

## Historical execution overlay — 2026-10-05 (scope pin chi tiết): một style, dựng trọn nguồn 22:01

User yêu cầu chọn một phong cách và làm clip dài, không thêm vòng chọn mẫu.
Chọn 2D minh họa như nhân vật nam cuối proof v1.3; khóa cast/props/style cho toàn
nguồn SHA256 `5a175454c2c2965bac5013a53926e210a9f70a185d802d0f2e0083a6fb399fa2`.
Nguồn đã được user chỉ và kiểm metadata/hash: 39634 frames, 30fps, 640x360;
giữ tiếng gốc và audio tail. Đồng bộ identity, hành động/contact, camera, cuts,
frame coverage, seam và audio xuyên toàn master là tiêu chí bắt buộc.

Một main assembly; xuất sớm các đoạn sản xuất thật khoảng 60–120s rồi tiếp tục
toàn video. Chỉ sửa vùng lỗi và continuation phụ thuộc, không seed/style sweep.
Xem canonical rules §0.3 và packet hiện hành tại
`C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-review-20261005/`:
LONG_VIDEO_HERMES_PROMPT.md và SESSION_OPENING_LONG_VIDEO.md.

MF-DEMO-LONG-01 là scope full-source mới được đề xuất; user tự giao Hermes.
Prototype02/10 đã hết deadline, giữ nguyên RUN/owner/ledger lịch sử. Ngân sách
scope dài phải được giao tường minh qua packet, không reset chi phí cũ.
WIP1/GPU1, code/UI/integration còn chờ; QUALITY_ACCEPTED=0, S12/S13 chưa đóng.

## Historical execution overlay — 2026-10-02: WAN từng cảnh/đoạn rồi ghép video

User ưu tiên chứng minh video mẫu rồi mới hoàn thiện/tích hợp tool. Mở đúng
MF-DEMO-E2E-R5 / WAN-PROTOTYPE-01 với existing demo owner; WIP1/GPU1, headless
ComfyUI được phép trong RUN cô lập. Transcript hình ảnh + cast cố định + ảnh
cảnh đích + driving nguồn → WAN → MP4 có tiếng → vision tự kiểm/sửa tối đa
10 candidate versions, dừng sớm khi đạt rồi Codex review một lần.

Canonical rules §0.2 và packet
`C:/Users/Admin/Documents/Codex/2026-09-22/tr-ng-th-i-terminal-gi/outputs/mf-shotwise-demo-20261002/NEXT_HERMES_DEMO_PROMPT.md`
thay thứ tự M1-first và gate giữa từng render attempt của plan 30/09 cho scope
này. Render policy deterministic-default của target overlay 19/08 là lịch sử
đối với thử nghiệm WAN được user yêu cầu; các yêu cầu fidelity/timeline/audio
vẫn giữ. M1/UI/integration/package chờ video proof; không xóa hoặc đánh dấu xong.
Demo pass chưa phải product/release pass; QUALITY_ACCEPTED=0 đến Codex verdict.

Revision02/10 phân biệt shot nguồn với chunk render. Được chia nhỏ trong cảnh
theo runtime và giữ frame mapping/context/trim; tái dùng phần đạt, sửa vùng lỗi
và continuation phụ thuộc rồi kiểm mối nối. Không đổi source/cast/cuts hoặc tự
reset trần10candidate/40video submissions/deadline nếu prototype đã dispatch.

## Historical execution overlay — 2026-10-01: M1-01 correction

Goal/milestones giữ nguyên. MF-END-10/M1-01 đang correction, chưa đóng. User đã
mở quyền chia bounded patches và tiếp tục exact owner trong cùng task window;
xem canonical rules §0.1/§8.2.1 và packet
`C:/Users/Admin/Documents/Codex/2026-09-22/tr-ng-th-i-terminal-gi/outputs/mf-writing-unblock-20261001`.
Một tool call/patch/process exit không phải task mới. Không dừng chỉ vì file lớn
khi có thể chia patch trong allowlist. Budget/deadline có giới hạn và Codex review
sau microtask vẫn áp dụng. Các bước công nghệ/demo/integration kế tiếp chưa mở.

## Historical execution overlay — 2026-09-30

Goal/U01–U28 và các task owner được giữ. Thứ tự thực thi hiện hành nằm tại
`C:/Users/Admin/Documents/Codex/2026-09-22/tr-ng-th-i-terminal-gi/outputs/mf-goal-review-skills-20260929/SEQUENTIAL_DELIVERY_PLAN_20260930.md`.
Chỉ MF-END-10/M1-01 được đưa vào prompt Manager mới; phần còn lại là roadmap
chờ Codex gate. Không đóng S12/S13 bằng một demo ngắn hoặc microtask UI.

## Historical delivery overlay — 2026-09-27

User yêu cầu một sản phẩm đầu cuối qua scene units và ComfyUI, nghiên cứu/proof
workflow trước implementation. Current PM scope, dependencies và acceptance:
`C:/Users/Admin/Documents/Codex/2026-09-22/tr-ng-th-i-terminal-gi/outputs/mf-takeover-20260927/EXECUTION_CONTRACT.md`.
Requirements U01–U28 trong PRODUCT_AND_COMFY_PLAN.md; 28 task mới/112 micro-job
trong TASK_BOARD.md và tasks/. Chỉ reference-pack/engine/UI/QC/batch slice được
liệt kê được mở sau PROOF_GATE; không tự mở toàn S13 hoặc ghi S13 đã hoàn tất.
Legacy sprint histories dưới đây được giữ; current status theo REVIEW_AND_HANDOFF.md
và actual repository. S12 NOT_CLOSED; quality NOT_ACCEPTED; toàn bộ release gates
clean Windows/human vẫn phải có bằng chứng, không thay bằng demo acceptance dễ hơn.

## Release map

| Release | Epics | Exit outcome |
|---|---|---|
| R0 Trusted Foundation | E00-E01 | Safe tests, durable domain and jobs |
| R1 Production Shell Alpha | E02-E03 | Manage channels/projects/videos and import/analyze |
| R2 Character & Reskin Alpha | E04-E06 | Reusable characters, object mapping, demo/apply |
| R3 Review & 4K Beta | E07-E08 | Actionable QC, original audio and validated 4K |
| R4 Character Generator | E09 | Guided six-pose 2D pack generation |

Sprint numbers express dependency order. They do not promise fixed duration. A sprint closes only when its exit gate is approved.

---

## EPIC E00 - Baseline and Change Safety

**Outcome:** repository has trustworthy gates and tests cannot mutate user production data.  
**Master Plan:** WS-01, G1.

### Sprint S00 - Isolate and record the baseline

| Task ID | Session outcome | Depends on | Status |
|---|---|---|---|
| S00-T01 | Tests use isolated channel/preset storage and never write root `channels.json` | None | APPROVED |
| S00-T02 | Reproducible baseline script/report for Python, typecheck, lint and build | S00-T01 | APPROVED |
| S00-T03 | Declare/configure runtime dependencies and FFmpeg discovery without machine-specific fallback | S00-T02 | APPROVED |
| S00-T04A1 | Resolve Python mypy baseline outside monolithic projects route | S00-T03 | APPROVED |
| S00-T04A2 | Resolve Python mypy baseline in projects route | S00-T04A1 | APPROVED |
| S00-T04B | Resolve frontend ESLint baseline without behavior changes | S00-T04A2 | APPROVED |

**Sprint exit:** clean checkout can install/run gates; tests leave production-root data unchanged; remaining warnings are explicitly baselined.

**Sprint status:** APPROVED — exit verified by quality-baseline run `20260803-144737` (7/7 gates PASS).

---

## EPIC E01 - Durable Domain, Persistence and Jobs

**Outcome:** one backend authority persists business state and long jobs survive restart.  
**Master Plan:** WS-00, WS-01, G1.

### Sprint S01 - Persistence foundation

| Task ID | Session outcome | Depends on | Status |
|---|---|---|---|
| S01-T01 | Define approved SQLAlchemy domain contracts and migration policy | S00 exit | APPROVED |
| S01-T02 | Bootstrap SQLite engine/session and schema-version migrations | S01-T01 | APPROVED |
| S01-T03 | Implement managed artifact paths, atomic writes and safe Trash contract | S01-T02 | APPROVED |
| S01-T04 | Build read-only legacy JSON inventory/import preview | S01-T02 | APPROVED |
| S01-T05 | Implement transactional legacy import with backup and migration tests | S01-T03,S01-T04 | APPROVED |

**Sprint status:** APPROVED — exit verified by quality-baseline run `20260803-184034` (7/7 gates PASS).

### Sprint S02 - Durable processing

| Task ID | Session outcome | Depends on | Status |
|---|---|---|---|
| S02-T01 | Define Job, JobStep, Artifact and error/retry state machine | S01 exit | APPROVED |
| S02-T02 | Persist job lifecycle and idempotency keys | S02-T01 | APPROVED |
| S02-T03 | Worker executes/retries/cancels jobs outside HTTP request | S02-T02 | APPROVED |
| S02-T04 | Restart reconciliation resumes or safely fails interrupted jobs | S02-T03 | APPROVED |
| S02-T05 | Job API and backend integration tests cover recovery contract | S02-T04 | APPROVED |

**Sprint status:** APPROVED — exit verified by quality-baseline run `20260804-000921` (7/7 gates PASS).

**Epic exit:** migration fixtures pass; jobs and artifacts reconcile after forced close; no durable truth relies only on RAM/frontend storage.

---

## EPIC E02 - Production Management and Product Shell

**Outcome:** users manage source/production channels, multi-video projects and resumable work.  
**Master Plan:** WS-00, WS-02, G2.

### Sprint S03 - Production management API

| Task ID | Session outcome | Depends on | Status |
|---|---|---|---|
| S03-T01 | Channel CRUD with source/production role and validation | E01 | APPROVED |
| S03-T02 | Project CRUD with source and production channel relationships | S03-T01 | APPROVED |
| S03-T03 | Video Item lifecycle, ordering and per-video status | S03-T02 | APPROVED |
| S03-T04 | Project summary/read-model API for dashboard | S03-T03 | APPROVED |

**Sprint status:** APPROVED — exit verified by quality-baseline run `20260804-110540` (7/7 gates PASS).

### Sprint S04 - New UI shell

| Task ID | Session outcome | Depends on | Status |
|---|---|---|---|
| S04-T01 | Establish UI tokens, layout primitives and Vietnamese product navigation | S03-T04 | APPROVED |
| S04-T02 | Home dashboard lists projects, next actions and active jobs | S04-T01 | APPROVED |
| S04-T03 | Channel management UX with empty/loading/error states | S04-T02 | APPROVED |
| S04-T04 | Project Detail manages Video Items, channels and outputs | S04-T02,S03-T04 | APPROVED |
| S04-T05 | Guided Project Shell persists step readiness and resume location | S04-T04 | APPROVED |

**Sprint status:** APPROVED — UI correction and visual QA verified by quality-baseline run `20260804-144203` (7/7 gates PASS).

**Epic exit:** Scenario H passes; a user never needs filesystem navigation to find the next Video Item.

---

## EPIC E03 - Import and Analyze

**Outcome:** an imported Video Item becomes a resumable, timebase-safe analyzed artifact.  
**Master Plan:** WS-03, G2.

### Sprint S05 - Import/analyze vertical slice

| Task ID | Session outcome | Depends on | Status |
|---|---|---|---|
| S05-T01 | Video preflight/probe contract and actionable incompatibility errors | E02 | PLANNED |
| S05-T02 | Managed import copies/registers source safely with checksum | S05-T01 | PLANNED |
| S05-T03 | Canonical timebase/proxy plus StructuralLockManifest with exact frame and audio-stream facts | S05-T02 | PLANNED |
| S05-T04 | Stable shot IDs, scored cut candidates, camera/background classes and risk-frame manifest | S05-T03 | PLANNED |
| S05-T05 | Import/Analyze UI shows estimate, progress, cancel, retry and resume | S05-T04 | PLANNED |
| S05-T06 | Golden import/analyze integration includes the verified 2D reference fixture manifest and restart-recovery evidence | S05-T05 | PLANNED |

**Epic exit:** one Video Item imports, analyzes and resumes from the new Project Shell with stable scene/time contracts.

---

## EPIC E04 - Character Library and Cast Mapping

**Outcome:** reusable, validated and version-pinned characters work across projects/channels.  
**Master Plan:** WS-05A, G2.5.

### Sprint S06 - Character Library

| Task ID | Session outcome | Depends on | Status |
|---|---|---|---|
| S06-T01 | Character, Pack Version, Asset and pose-slot domain/API | E01 | APPROVED |
| S06-T02 | Import existing preset assets into draft packs without mutating originals | S06-T01 | APPROVED |
| S06-T03 | Six required poses plus view/pose/anchor capability, transparency/resolution and completeness validation | S06-T02 | APPROVED |
| S06-T04 | Character Library browse/search/filter/detail UI | S06-T03,S04-T01 | APPROVED |
| S06-T05 | Pack review, publish and immutable version UX | S06-T04 | APPROVED |

**Sprint status:** APPROVED — product gate completed; S06-T05 baseline `20260805-091121` passed 7/7.

### Sprint S07 - Project cast reuse

| Task ID | Session outcome | Depends on | Status |
|---|---|---|---|
| S07-T01 | Project Cast Mapping pins role type, Pack Version and CompatibilityPolicy version | S06 exit,E05 contract | APPROVED |
| S07-T02 | In-context picker shows per-occurrence compatibility evidence and fail-closed blockers | S07-T01 | APPROVED |
| S07-T03 | Cross-project reuse and version-isolation integration tests | S07-T02 | APPROVED |

**Sprint status:** APPROVED — independent Codex re-review 2026-08-22; no blocking follow-up for S09.

**Epic exit:** Scenario I passes; later library edits cannot silently alter prior project mappings.

---

## EPIC E05 - Object Intelligence

**Outcome:** users select video-global Object Roles rather than repeating work scene by scene.  
**Master Plan:** WS-04, G3.

### Sprint S08 - Object discovery and curation

| Task ID | Session outcome | Depends on | Status |
|---|---|---|---|
| S08-T01 | Occurrence/Role and scene-graph schema covers character, prop, background, foreground, graphic and source-only overlay | E03 | APPROVED |
| S08-T02 | Candidate extraction stores prompts/masks, representative thumbnails, camera-relative motion and risk evidence | S08-T01 | APPROVED |
| S08-T03 | Cross-scene grouping combines visual identity with motion/interaction evidence and merge/split/confirm API | S08-T02 | APPROVED |
| S08-T04 | Object Gallery selection and confidence UX | S08-T03 | APPROVED |
| S08-T05 | Object correction actions rerun only affected dependencies | S08-T04 | APPROVED |
| S08-T06 | Golden role/group/contact/occlusion dataset and calibrated metrics report | S08-T05 | APPROVED |

**Sprint status:** APPROVED — original foundation review in `reviews/S08_SPRINT_PM_REVIEW_2026-08-19.md`; required Source-Locked taxonomy/structural-evidence bridges are the dependency baseline used by approved S07 and the S09 realignment below.

**Epic exit:** Scenarios A-B pass through object selection with actionable low-confidence handling.

---

## EPIC E06 - Reskin Demo and Apply

**Outcome:** users prove the look on representative loops before committing full-video compute.  
**Master Plan:** WS-05, G3-G4.

### Sprint S09 - Demo-first reskin

| Task ID | Session outcome | Depends on | Status |
|---|---|---|---|
| S09-T00 | Benchmark SceneGraph/MotionContract/RendererRouter on verified risk loops and license-gate every adapter | S05 exit,E05 contract | APPROVED — J1-v4 direct 13/13, measured 6/6 risk classes retained |
| S09-T01 | Reskin Mapping pins compatibility evidence, pose/contact anchors and renderer route per segment | E04,E05,S09-T00 | APPROVED |
| S09-T02 | Implement tested pose-swap/affine route behind adaptive renderer contract; escalate by measured residual | S09-T01 | APPROVED |
| S09-T03 | Select 3-5 risk-covering demo loops and create proxy jobs | S09-T02 | APPROVED |
| S09-T04 | Demo comparison UI: original/result/split/wipe/blink | S09-T03 | APPROVED |
| S09-T05 | Demo corrections for masks, z-order, contacts, mesh/parts and route override regenerate only affected loop | S09-T04 | APPROVED |
| S09-T06 | Explicit approval pins structural/compatibility/renderer contracts in immutable apply checkpoint | S09-T05 | APPROVED — C7-R2 build/config/owned-restart acceptance independently verified |

**Execution update (2026-08-23):** Codex independently approved the S09-T00 readiness package and verified the old T01 foundation with 48/48 focused tests. A dedicated Manager prompt may now run the full S09 implementation slice: implement/benchmark T00 first, resume the exact old T01 owner, then T02..T06 in dependency order, and stop once at `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`. Do not silently downgrade to legacy transform-only parity.

**Codex review update (2026-08-24 21:18 +07):** full S09 is
`CHANGES_REQUESTED`. The current T02 adapters do not perform replacement-layer
reskinning and the v1 harness does not score renderer output. User đã chọn ưu
tiên tốc độ thay vì tiết kiệm quota: chạy full correction prompt
`prompts/S09_C1_FAST_TRACK_MANAGER_2026-08-24.md` với Wave A tối đa 5 worker có
write-set tách biệt, renderer/API join gates, rồi stop for Codex review. T03/T04
disk state được giữ lại nhưng chưa approved; S10 và S11 production vẫn blocked.

**Codex C1 re-review update (2026-08-25 09:50 +07):** S09 remains
`CHANGES_REQUESTED`. Current all-S09 gate is `8 failed, 318 passed`; C1 has only
4/12 measured route-fixture rows, J1 SHA drifted after its handshake, benchmark
bypasses production router/adapters, T03 durable publish fails at Windows path
length 260, and production E2E omits only-affected-loop proof. Authorized next
packet is `prompts/S09_C2_CORRECTION_MANAGER_2026-08-25.md`: five disjoint owner
lanes in Wave A, immutable full renderer freeze manifest, actual-router I03
measurement, I05 measured decision, then downstream/E2E join. S10/S11 production
remain blocked until Codex independently approves S09-C2.

**Codex C2 independent review update (2026-08-25 22:46 +07):** S09 remains
`CHANGES_REQUESTED`. C2 materially fixed the renderer and reached 6/6 measured
classes, but it did not implement correction-bound regeneration: its final E2E
fails an unmeasured route pin, reuses the old job and asserts every artifact is
unchanged. J1-v3 was pinned after loader drift while I03/I05/downstream remained
on v2, and the harness uses a second three-file freeze authority plus a
noncanonical raw-concat decoded hash. Independent current gate is
`1 failed, 362 passed`; T04 cannot serve a published artifact at a 272-character
Windows path. Authorized next packet is
`prompts/S09_C3_CORRECTION_MANAGER_2026-08-25.md`, which resumes exact owners for
durable affected-only generation, UI scope/evidence, unified J1-v4, rerun
I03/I05 and production E2E. S10, production S11 and production S13 remain
blocked until Codex approves S09-C3.

**Codex C3 independent review update (2026-08-26 09:51 +07):** S09 remains
`CHANGES_REQUESTED`. C3 materially fixed unified freeze/canonical hash,
long-path serving and durable regeneration plumbing; Codex re-hashed J1-v4
13/13 clean and independently got 51/51 focused backend tests, Ruff, TSC and
Alembic one head. However the production QA DB disproves affected-only
acceptance: the formal job requested and rendered all four loops
(`regenerated=true` for d1-d4; d1/d2/d3 merely produced byte-identical files).
The UI returns all `completedLoops`, z-order always edits `placements[0]`, four
other correction kinds have no real render-effect dispatcher, the fingerprint
omits frozen-evidence SHA and T06B never asserts per-loop regenerated state.
Review: `reviews/S09_C3_PM_REVIEW_2026-08-26.md`. Authorized packet:
`prompts/S09_C4_CORRECTION_MANAGER_2026-08-26.md`, resuming the exact
T05A/T03/T04/T05B/T06B owners. S10, production S11 and production S13 remain
blocked until Codex independently approves S09-C4.

**Codex C5 independent review update (2026-08-27):** S09 remains
`CHANGES_REQUESTED`, but the product backend is now materially green: Codex
independently obtained T03 40/40, T04 24/24 with a real >=260-character path,
T06 backend 43/43, plus Ruff/mypy/TSC/scoped ESLint passes. Exit is blocked by
acceptance integrity: J1-v4 direct hash is only 6/13 after CRLF recurrence;
Chromium restart force-kills an unverified port owner and leaks its replacement;
the two runs reuse one hard-coded runtime/DB/output and Run2 lacks complete raw
evidence. Review: `reviews/S09_C5_PM_REVIEW_2026-08-27.md`. Authorized bounded
packet: `prompts/S09_C6_EXIT_HARDENING_MANAGER_2026-08-27.md`; one new
EOL-guard task plus exact T03/T06B owner corrections. No S10/S11/S13 production
work opens before Codex approves C6.

**Codex C6 independent review update (2026-08-27):** S09 remains
`CHANGES_REQUESTED`, although the remaining scope is now only T06B acceptance
lifecycle. Codex directly confirmed J1-v4 13/13, coherent-evidence proof PASS,
T06 backend 43/43, TSC and scoped ESLint; Run1/Run2 also have distinct roots and
DBs. The blocker is a false restart: `primaryLaunched` is null when Phase G calls
`stopLaunched`, while the original backend was launched by an external runner;
the replacement can collide with the old listener and readiness still succeeds
against the old process. Cleanup is not fail-closed and active C4 fallbacks
remain. Review: `reviews/S09_C6_PM_REVIEW_2026-08-27.md`. Authorized bounded
packet: `prompts/S09_C7_OWNED_RESTART_CORRECTION_MANAGER_2026-08-27.md`; resume
only T06B owner `20260824_131423_423e42`. S10 and other production lanes remain
blocked until Codex approves C7.

**Codex C7 independent review update (2026-08-27):** C7 materially closes the
C6 process-lifecycle defect: exact initial/replacement listener ownership,
ordered stop/relaunch, durable checkpoint read and fail-closed cleanup are real;
J1-v4 13/13, T06 backend 43/43, TSC and scoped ESLint remain green. S09 still
cannot close because the current post-run `.next` bakes API port 8888 while the
launcher trusts BUILD_ID existence; Codex's fresh isolated Chromium run failed
before the product flow at `(không có project)`. The launcher also retains
C4/C6 fixture fallbacks and `npx`/`shell:true`. Review:
`reviews/S09_C7_PM_REVIEW_2026-08-27.md`. Authorized same-round continuation:
`prompts/S09_C7_R1_REPRODUCIBLE_BUILD_CONTINUATION_MANAGER_2026-08-27.md`;
resume only the exact T06B owner. No C8 and no other production lane.

**Codex C7-R1 independent review update (2026-08-27):** the two R1 Chromium
runs, lifecycle and direct DB truth are green: one completed render attempt for
d4 only, exact reuse of d1-d3, checkpoint survives exact owned restart. Current
build hashes match 182/182; fixture 21/21; J1 13/13, T06 backend 43/43, TSC and
ESLint pass. S09 still cannot close because R1 changed the normal frontend proxy
fallback from 8888 to test port 8201 outside its write set, while the launcher
still reuses `.next` on BUILD_ID alone and cannot accept safe explicit fresh
roots. Review: `reviews/S09_C7_R1_PM_REVIEW_2026-08-27.md`. Authorized narrow
same-C7 continuation:
`prompts/S09_C7_R2_FINAL_CONFIG_BUILD_INTEGRITY_MANAGER_2026-08-27.md`. Resume
only the exact T06B owner; no backend/product-flow rewrite and no other lane.

**Codex C7-R2 final review update (2026-08-27 21:40 +07):** R2 restored the
normal 8888 frontend fallback, replaced BUILD_ID-only reuse with a seven-check
content/input/build validator and accepted arbitrary safe fresh runtime/output
roots. Codex independently passed J1 13/13, T06 backend 43/43, TSC/ESLint,
direct DB affected-only probes and a third fresh Chromium run with exact owned
restart and cleanup. `S09 = CODEX_APPROVED / CLOSED`. Review:
`reviews/S09_C7_R2_FINAL_PM_REVIEW_2026-08-27.md`. Three documentation/parser
P2 items are carried forward without opening C8.

### Sprint S10 - Full apply

| Task ID | Session outcome | Depends on | Status |
|---|---|---|---|
| S10-T01 | Shot/layer chunked full-video reskin job with overlap, deterministic checkpoint and resume | S09 exit | APPROVED / CLOSED — C6H R3 final review 2026-09-03 |
| S10-T02 | Multi-role mappings process independently while preserving contact/z-order edges | S10-T01 | APPROVED / CLOSED |
| S10-T03 | Partial recompute preserves approved/unaffected segments | S10-T02 | APPROVED / CLOSED |
| S10-T04 | End-to-end Demo→Apply restart plus frame/cut/trajectory/contact regression evidence | S10-T03 | APPROVED / CLOSED |

**Execution authority (2026-08-27):** Codex packet
`prompts/S10_FULL_APPLY_MANAGER_2026-08-27.md` freezes eight owner sessions and
the exact internal DAG. Only T01A/T01B may write in parallel; shared
workflow/API/schema integration is serialized. Hermes must stop once at
`SPRINT_SUBMITTED / PENDING_CODEX_REVIEW`.

**Codex C2 independent review update (2026-08-29 11:35 +07):** S10 remains
`CHANGES_REQUESTED`. T03 still fabricates recompute frames/adapter evidence;
T04A still emits hard-coded/fallback structural truth; nested-Windows full gate
is `2 failed, 164 passed`; T04C retained only invalid R1 evidence and has no
fresh C2 run. C3 is a bounded serialized correction on exact T03→T04A→T01C-
static→T04C owners. Review: `reviews/S10_C2_PM_REVIEW_2026-08-29.md`; prompt:
`prompts/S10_C3_REALITY_EXIT_CORRECTION_MANAGER_2026-08-29.md`. No S11/S13
production opens before Codex approves/closes S10.

**Codex C4 blocker decision (2026-08-30 10:05 +07):** C4 J1-J3 are
Manager-verified but not Codex-approved. J4 is blocked by one independently
confirmed `F841` in T01A-owned `tests/test_s10_full_apply_domain.py:172`.
Codex authorized exact owner `20260827_234001_9d7f39` to remove only that dead
assignment, re-run J4, then continue exact T04C owner for two strict C4 vertical
runs. S10 remains `CONTINUATION_AUTHORIZED / NOT_APPROVED`; S11/S13 production
remains blocked.

**Codex C4 final independent review update (2026-08-30 16:27 +07):** S10
remains `CHANGES_REQUESTED`, now only for a bounded frontend exit correction.
Backend C4 authority/recompute/structural/long-path/restart gates are
independently green, but exact scoped Apply ESLint exits 1 at S10-owned
`frontend/src/app/(app)/apply/page.tsx:90` because state is synchronously set in
an effect. The old lint evidence omitted this route page. Authorized prompt is
`prompts/S10_C5_APPLY_LINT_CURRENT_BUILD_EXIT_MANAGER_2026-08-30.md`: exact
T04B owner fixes URL/state without suppression, then exact T04C owner runs two
fresh vertical acceptances on the corrected current build. Backend is frozen;
S11/S13 production remains blocked pending S10 approval/close.

**Codex C5 independent review update (2026-08-30 18:01 +07):** backend,
authority, recovery, structural evidence, full suite 206/206, Apply lint/TSC,
current build and two distinct C5 vertical runs are independently green. S10
still remains `CHANGES_REQUESTED` because `s10-apply-ui.spec.ts` can pass its
progress/evidence/action cases on an empty page, never clicks
Cancel/Retry/Resume and skips mobile under the recorded config. Authorized C6
is exact-owner, live-product UI acceptance only; backend stays frozen. If no
production source changes, retain the hashed C5 build/runs and avoid needless
rerun cost. Prompt:
`prompts/S10_C6_REAL_APPLY_UI_ACCEPTANCE_MANAGER_2026-08-30.md`.

**Codex C6 blocker decision (2026-08-31 10:01 +07):** Hermes correctly stopped
at `BLOCKED_SCOPE_EXPANSION`, but the blocker is broader than a missing public
SLM hash. Full Apply still plans and writes job authority from client scene/
mapping; C5/C6 evidence fabricated affected region and downgraded an unsupported
route. C5's backend/authority-green conclusion is superseded. Authorized C6A is
serialized exact-owner work: additive immutable S09 approval v2 bridge, S10-T01C
server-derived minimal submit, then resume the existing 20-case T04B suite,
fresh build and two fresh T04C vertical runs without DB/client authority
fabrication. Review: `reviews/S10_C6_BLOCKER_PM_DECISION_2026-08-31.md`; prompt:
`prompts/S10_C6A_SERVER_DERIVED_APPLY_AUTHORITY_MANAGER_2026-08-31.md`. S10
remains `CONTINUATION_AUTHORIZED / NOT_APPROVED`; S11-T02..T06 and production
S13 remain blocked.

**Codex C6A cancel-lifecycle decision (2026-08-31 14:51 +07):** C6A materially
completed approval v2, server-derived minimal submit and T03 alignment; Manager
fresh full S10 gate reached 216 passed, and T04B's executable live fixture then
exposed a real T01C transaction race. Cancel can return success while a
second-writer SQLite lock is swallowed, leaving the durable job live; worker
completion can overwrite `cancelled` and publish. Resume has a related
multi-session/silent-success risk. S10 remains
`CONTINUATION_AUTHORIZED / NOT_APPROVED`. Authorized C6B is serialized exact
owner work: `T01C-C9-LIFECYCLE -> J6C -> T04B-C3 -> J6-UI -> J6-BUILD ->
T04C-C5 -> EXIT`, with automatic same-session continuation through ordinary
iteration limits. Latest user model override for every C6B worker is restored
to exact `ocg/deepseek-v4-flash`, reasoning max, fallback OFF; the temporary
`BAI/deepseeekv4flash` route is withdrawn as unstable. Review:
`reviews/S10_C6A_CANCEL_LIFECYCLE_PM_DECISION_2026-08-31.md`; prompt:
`prompts/S10_C6B_CANCEL_LIFECYCLE_CONTINUATION_MANAGER_2026-08-31.md`.

**Codex C6B independent review update (2026-09-01):** C6B Manager evidence is
green for existing tests, current build, 20/20 live UI and two final vertical
runs, but S10 remains `CHANGES_REQUESTED / NOT_APPROVED`. Codex reproduced two
T01C P1 gaps omitted by the suite: Submit failure plus identical replay can
return 200 `reused=true` for a pending run with zero durable job; Retry enqueue
failure leaves an active pending successor with zero durable job. The
pre-existing-publication resume branch also fails to verify its completion CAS
before writing `completed:true`, allowing contradictory checkpoint truth when
cancel wins the race. Authorized C6C resumes only exact T01C owner
`20260828_003035_859fe5`; frontend/T04B/T04C stay frozen. Direct worker model is
`BAI/glm-5.3-flash`, max, fallback OFF; `comboBAI` is prohibited. Review:
`reviews/S10_C6B_PM_REVIEW_2026-09-01.md`; prompt:
`prompts/S10_C6C_ENQUEUE_CAS_EXIT_CORRECTION_MANAGER_2026-09-01.md`. S11-T02..T06
and production S13 remain blocked.

**Codex C6C independent review update (2026-09-01):** C10 correctly closes the
zero-job orphan compensation and pre-existing-publication completion-CAS
finding, and broad existing gates remain green. S10 nevertheless remains
`CHANGES_REQUESTED / NOT_APPROVED`: replay repair creates a queued job while
the run remains failed, so immediate Retry creates a second active job for the
same lineage; replay also returns 200 reused for a tampered immutable job
manifest because it checks only key existence. Authorized C6D resumes only
exact T01C owner `20260828_003035_859fe5` to make repair coherent, enforce one
canonical work across replay/retry/claim races, and validate complete durable
job identity before success. Completion-CAS/frontend/T04B/T04C stay frozen.
Direct worker route is the user's final exact selector
`BAI/deepseek-v4-flash-vision-exp`, custom/max/fallback OFF after the local GLM
quality/speed review. Review:
`reviews/S10_C6C_PM_REVIEW_2026-09-01.md`; prompt:
`prompts/S10_C6D_REPLAY_SINGLE_WORK_CORRECTION_MANAGER_2026-09-01.md`. S11 and
production S13 remain blocked pending S10 approval/close.

**Codex C6D independent review update (2026-09-01):** ordinary repaired replay
coherence, immediate Retry rejection and gross manifest-tamper rejection are
improved, but S10 remains `CHANGES_REQUESTED / NOT_APPROVED`. Codex's true
two-thread barrier produced two HTTP 200 reused responses and two queued jobs
with the same S10 idempotency key; the shipped “concurrent” test is serial.
Replay also returns 200 for terminal-run/active-job contradiction and for a
stored manifest whose `project_root` alone is tampered, because lifecycle is
not checked and immutable comparison is only a whitelist. Authorized C6E
resumes exact T01C owner `20260828_003035_859fe5`; exact worker model remains
`BAI/deepseek-v4-flash-vision-exp`, custom/max/fallback OFF. Review:
`reviews/S10_C6D_PM_REVIEW_2026-09-01.md`; prompt:
`prompts/S10_C6E_TRUE_CONCURRENCY_IMMUTABLE_LIFECYCLE_MANAGER_2026-09-01.md`.
S11-T02..T06 and production S13 remain blocked; S13-P01 Character Fit
Recommender remains planned.

**Codex C6E independent review update (2026-09-01):** C6E now closes the prior
true-concurrent identical-repair duplicate, full manifest-default comparison
and explicit run/job lifecycle matrix, but S10 remains
`CHANGES_REQUESTED / NOT_APPROVED`. Codex independently changed only a stored
durable job idempotency key; replay returned 200 reused and inserted a second
queued job for the same run/generation because discovery searches only the
expected key. Retry uses a no-op `cancelled -> cancelled` update as an exclusive
claim; a second Retry on the same predecessor returns 500 on the unique run
identity. The claimed worker-claim/Retry barrier test is sequential. Context
health for the heavily resumed T01C owner has crossed the canonical recovery
threshold (617-message effective lineage plus repeated current-contract misses),
so authorized C6F opens exactly one compact recovery session after confirming
zero old writer and recording owner transfer. User-selected worker route is
exact `comboBAI`, custom/max, Hermes fallback chain OFF, with effective member
ledger required. Review: `reviews/S10_C6E_PM_REVIEW_2026-09-01.md`; prompt:
`prompts/S10_C6F_EXACT_JOB_DISCOVERY_RETRY_CAS_RECOVERY_MANAGER_2026-09-01.md`.
S11-T02..T06 and production S13 remain blocked; S13-P01 remains planned.

**Codex C6F independent review update (2026-09-02):** S10 remains
`CHANGES_REQUESTED / NOT_APPROVED`. C6F fixes the single wrong-key claimant and
sequential repeat-Retry 500, but exact durable resolution still treats multiple
same-generation wrong-key claimants as a true orphan: Codex's real-route probe
returned 200 reused and grew Job count 2 -> 3. Retry also still treats the
same-state `cancelled -> cancelled` update as exclusive; two direct claims both
returned true. Authorized C6G resumes exact compact recovery owner
`20260901_230235_b80d4b` to implement one ambiguity-safe resolver and truthful
Retry ownership, then run one final phased exit. Review:
`reviews/S10_C6F_PM_REVIEW_2026-09-02.md`; prompt:
`prompts/S10_C6G_EXCLUSIVE_RETRY_CLAIM_AMBIGUOUS_JOB_RESOLUTION_MANAGER_2026-09-02.md`.
S11-T02..T06 and production S13 remain blocked; S13-P01 remains planned.

**Codex C6G C14 incident decision (2026-09-02):** S10 is
`INCIDENT_RECOVERY_REQUIRED / NOT_SUBMITTED / NOT_APPROVED`. The C14 worker
overwrote the untracked API test from 2,547 lines to 278. The Manager's
reconstruction is not yet authoritative: Codex independently obtained 58
failed/5 passed, 63 collected nodes, a duplicate test definition and missing
helper symbols. Canonical role separation rejects further Manager test edits
and Codex semantic reconstruction. One guarded resume of the actual state.db
C14 owner `20260902_013803_4d5ce5` is authorized: recover an exact candidate
matching pre-C14 SHA `963ED50E...`, apply only verified patches, pass a Manager
recovery gate, then finish the original 14-row C6G contract. Exact recovery
failure stops `BLOCKED_TEST_AUTHORITY`; a second unsafe write stops
`BLOCKED_CONTEXT_HEALTH / OWNER_TRANSFER_REQUIRED`. Decision:
`reviews/S10_C6G_C14_TEST_DESTRUCTION_PM_DECISION_2026-09-02.md`; prompt:
`prompts/S10_C6G_C14_T3_FORENSIC_TEST_AUTHORITY_RECOVERY_MANAGER_2026-09-02.md`.
S11-T02..T06 and production S13 remain blocked.

**Codex C6G authority terminal / C6H decision (2026-09-02):** guarded C14-T3
proved the pre-destruction 57-test SHA is not recoverable from state.db. Codex
also found three identical VSS copies, but they are only a 13-test ancestor
(`5B312719...`); local history search and VSS+DB replay still cannot reach
`963ED50E...`. `S10-C6G = BLOCKED_TEST_AUTHORITY / SUPERSEDED_BY_S10-C6H /
NOT_APPROVED`. C6H authorizes a formal semantic authority rebaseline, never an
exact-restoration claim and never acceptance of DAD70AE3 as-is. New task
`S10-T01C-C15` uses one fresh compact `comboBAI` custom/max/fallback-OFF session,
patch-only guarded writes, exact 57 retained + five C6G = 62-node authority
gate, then the locked 14-row closure. Manager may run isolated read-only lanes
in parallel only after writer exit. Decision:
`reviews/S10_C6G_BLOCKED_AUTHORITY_C6H_REBASELINE_PM_DECISION_2026-09-02.md`;
prompt:
`prompts/S10_C6H_TEST_AUTHORITY_REBASELINE_AND_FINAL_CLOSURE_MANAGER_2026-09-02.md`.
S11-T02..T06 and production S13 remain blocked.

**Codex C6H R2 independent review update (2026-09-03):** S10 remains
`CHANGES_REQUESTED / NOT_APPROVED`. R2 safely fixed the unrelated-malformed-row
global block and stale per-row classifier, with current 70/70 API and 290/290
broad gates. A remaining P1 makes stored-manifest identity depend on exactly
two JSON whitespace encodings: a valid tab-formatted target manifest plus
tampered key/generation is missed, replay returns `200 reused=true`, and Job
count grows 1 -> 2. Authorized R3 must use one representation-independent exact
target-run prefilter, resume safe owner `20260903_012248_d29911`, and run in a
genuinely new compact Manager chat. Review:
`reviews/S10_C6H_R2_PM_REVIEW_2026-09-03.md`; prompt:
`prompts/S10_C6H_R3_FORMAT_INDEPENDENT_MANIFEST_IDENTITY_MANAGER_2026-09-03.md`.
S11-T02..T06 and production S13 remain blocked.

**Codex C6H R3 final review update (2026-09-03 10:40 +07):** R3 closes the
format-dependent manifest identity finding with one escaped exact-run literal
containment plus parsed exact run/project/plan classification. Current Manager
gates are 71/71 API, 96/96 focused twice and 291/291 broad twice; Codex
independently reran 71/71 and added two distinct real-stack probes, both green.
Raw-session audit found zero forbidden critical write. `S10-C6H R3 =
CODEX_APPROVED / CLOSED`; whole `S10 = CODEX_APPROVED / SPRINT_CLOSED`.
Review: `reviews/S10_C6H_R3_FINAL_PM_REVIEW_2026-09-03.md`. S11 production is
opened by `prompts/S11_T02_T06_FULL_SPRINT_MANAGER_2026-09-03.md`; production
S13 remains not opened.

**Epic exit:** Scenarios A-E pass; no full apply begins without explicit Demo approval.

---

## EPIC E07 - Review and Original Audio

**Outcome:** users review only actionable problems while source audio remains synchronized.  
**Master Plan:** WS-06, WS-07, G4.

### Sprint S11 - QC and original audio

| Task ID | Session outcome | Depends on | Status |
|---|---|---|---|
| S11-T01 | Original audio remux/codec fallback consumes S05 stream facts and preserves source synchronization | E03 | APPROVED — Codex direct review 2026-08-23, 64/64 suite |
| S11-T02 | QCItem domain normalizes visual/audio/timecode issues | E06,S11-T01 | READY / FULL_SPRINT_AUTHORIZED |
| S11-T03 | Structural drift, contact, z-order, clipping, identity/flicker and A/V checks create QC items | S11-T02 | AUTHORIZED_AFTER_INTERNAL_DEPENDENCY |
| S11-T04 | Review Queue navigates issue, correction and affected rerun | S11-T03 | AUTHORIZED_AFTER_INTERNAL_DEPENDENCY |
| S11-T05 | Readiness gate blocks only unresolved blockers | S11-T04 | AUTHORIZED_AFTER_INTERNAL_DEPENDENCY |
| S11-T06 | Original-audio and targeted-review acceptance suite | S11-T05 | AUTHORIZED_AFTER_INTERNAL_DEPENDENCY |

**Current gate (2026-09-03 11:07 +07, clean Git checkpoint activated):** S11-T01 is
APPROVED, S11-P02 rev-C6 is `CODEX_APPROVED` as the binding 19-ID/14-wave
packet, and E06/S10 is now closed. Production T02..T06 is
`AUTHORIZED_TO_DISPATCH` through one new full-sprint Manager. Immediate wave is
W1/T02A; each Task ID uses a new worker, correction resumes exact owner.
Approved code is pushed at `4cec376bd7589bfd5bbd8c2260fdd63b751aca73` and
clean canonical S11 branch/worktree is pushed at
`7751598214eedb6b72e3783e39a2a408721abe40` / `codex/s11-integration` /
`C:\Users\Admin\MotionForge2D-worktrees\s11-integration`. W6 runs four real
isolated implementation workers, W9 and W12 run two; all other waves follow the
DAG serially. One Git-only `S11-INT01` owner merges only Manager-verified task
branches and pushes only green wave heads. S13 remains not opened.

**Codex independent review update (2026-09-04):** T02..T06 was submitted clean
and pushed at `4d7ad8196c3f7a21af744906ef4174690159d889`; an independent 20-file
backend risk suite passed 314/314. Verdict remains `CHANGES_REQUESTED /
NOT_APPROVED / S11_NOT_CLOSED` because (1) an audio-only completed QC job can be
selected as full readiness authority and (2) the required restart/resume row is
not yet an executable restart scenario. A P2 diff-check whitespace mismatch also
remains. Bounded `S11-C1` is authorized by
`prompts/S11_C1_FULL_SCOPE_READINESS_RESTART_EXIT_MANAGER_2026-09-04.md`: open a
new compact Manager, resume exact owners, run T03G/T06C/T03A in three disjoint
parallel lanes, then T05A dependency-serial; T04B is conditional only if the
executable restart probe reveals a product defect. Worker model is
`ocgfree/muse-spark-1.3-contributor-free`, max requested, fallback off. S12 and
S13 remain not opened until Codex rereview closes S11.

**S11-C1 Codex rereview update (2026-09-04):** local correction tree is clean at
`c9d5453b429fd96957860cd7ed27eddcf18e2ead`, but remote remains `4d7ad81` and
S11 is still `CHANGES_REQUESTED / NOT_CLOSED`. Fresh real-DB probes show three
open authority rows: missing completion counts default to zero, completion
identity mismatch is accepted, and 51 newer audio jobs can evict a valid full
authority from the limited mixed-job page. The submitted T06C restart node
restarts full QC instead of the targeted correction/RECOMPUTE_OBJECTS workflow.
T05A was also misrouted through the durable T04D session, and the C1 watchdog
was left running. Bounded `S11-C2` is authorized by
`prompts/S11_C2_COMPLETION_AUTHORITY_TARGETED_RESTART_OWNER_EXIT_MANAGER_2026-09-04.md`:
run exact T03G and T06C owners in parallel, then the real T05A owner serially;
T04B remains conditional, INT01 performs the final verified non-force push.
S12/S13 remain unopened.

**S11-C2 Codex rereview update (2026-09-04 17:34 +07):** canonical and remote
are clean/equal at `7474eb7`, T03G passes 98/98, T05A 14/14 and the real
targeted correction/`RECOMPUTE_OBJECTS` restart passes twice. S11 remains
`CHANGES_REQUESTED / NOT_CLOSED`: five completion-authority identity tamper
rows still fail open; T06C does not fully bind affected pre/post artifacts or
fresh QCItem/readiness; and the terminal static gate masked a mypy failure plus
a nonexistent OpenAPI test. T03G follow-on fix `e7e9242` was left unmerged.
Bounded `S11-C3` is authorized by
`prompts/S11_C3_EXACT_IDENTITY_RESTART_PROOF_FAIL_FAST_EXIT_MANAGER_2026-09-04.md`:
new compact Manager, exact T03G/T06C owners in two safe parallel lanes,
conditional T04B/T05A only on executable RED, exact INT01 fail-fast integration
and one final non-force push. S12/S13 remain unopened.
The user-selected worker route for C3 is exact custom 9Router
`cmc/muse-spark-1.3-contributor`, requested reasoning `max`, fallback off.

**S11-C3 Codex rereview update (2026-09-05):** canonical and GitHub are
clean/equal at `28a2207`; independently rerun T03G 143, T05A 14 and T06C T12
twice are green. S11 remains `CHANGES_REQUESTED / NOT_CLOSED`. Clean-process
probes show normal app/real JobService bootstrap registers zero detectors, so
full QC cannot execute. Read authority also catches unavailable registry
authority and guesses revision `1.0.0`, falsely accepting a claimed full
completion with only 2/10 detectors registered. C3 used inherited/`meta` calls
after exact CMC returned 403 despite fallback OFF and submitted only 7/15 final
gates. Bounded `S11-C4` is authorized by
`prompts/S11_C4_PRODUCTION_REGISTRY_FAIL_CLOSED_FINAL_EXIT_MANAGER_2026-09-05.md`:
one fresh compact T03G recovery owner after context-health transfer, exact
INT01 integration, then complete fail-fast closure. S12/S13 remain unopened.

**S11-C4 Codex independent rereview update (2026-09-05):** canonical HEAD is
`8f5af068978265a0dc347db97099f897e1eb5a49`, clean and equal to remote;
independent T03G/T05A/T12 and static checks are green. The sprint is still
`CHANGES_REQUESTED / NOT_APPROVED / NOT_CLOSED` for binding reasons: the exact
`cmc/muse-spark-1.3-contributor` route was unavailable (403 and absent from
`/v1/models`) while recovery used the unauthorized `cmc/meta/...` alias;
`ensure_full_band_registered` retains ghost registrations and leaves partial
state after a conflict; the current test structure does not protect against
removing the production bootstrap hook; and the submitted packet overclaims a
failed guard and incomplete/raw gate evidence, including the T12 run arithmetic.
Next bounded correction/review prompt is
`prompts/S11_C4_R1_BOOTSTRAP_ATOMICITY_ROUTE_BLOCKED_2026-09-05.md`, currently
`BLOCKED_MODEL_ROUTE`; no worker or S12/S13 implementation is authorized.

**S11-C4-R1 Codex independent rereview update (2026-09-05 19:11 +07):**
canonical `e98ccd9` is clean/local==remote and independent T03G 148, T05A 14,
T12 twice, Ruff, two-file binding mypy, Alembic and OpenAPI are green. The newer
user instruction authorizes `cmc/meta/muse-spark-1.3-contributor`, so the old
route blocker is closed prospectively. S11 nevertheless remains
`CHANGES_REQUESTED / NOT_APPROVED / NOT_CLOSED`: arbitrary import/explicit
exceptions bypass rollback, the multi-step registry transaction is not locked,
and a fresh deterministic two-thread repro leaves 9/10 detectors after one
success. The recovery owner also used prohibited heredoc `Path.write_text()` on
tracked source/test files, requiring context-health owner transfer, while the
R1 packet omits mandatory registry/guard/final-state artifacts and overclaims a
three-file mypy green. Proposed R2 is
`prompts/S11_C4_R2_BOOTSTRAP_TRANSACTION_OWNER_TRANSFER_MANAGER_2026-09-05.md`;
it is `PROPOSED_ONLY` until explicit user dispatch authority.

**S11-C4-R2 Codex independent rereview update (2026-09-05 23:43 +07):**
canonical `11dd50a` is clean/local==remote; fresh Codex T03G 151, T05A 14,
T12 twice, static, Alembic and OpenAPI gates are green. The production
RLock/rollback mechanism also passes a stronger true-contention reproduction
and KeyboardInterrupt/SystemExit rollback probes. S11 remains
`CHANGES_REQUESTED / NOT_APPROVED / NOT_CLOSED` because the committed race test
serializes its callers and performs a repair bootstrap before final assertions;
R2 also dispatched two owners onto the same task/worktree, and the competing
session wrote five untracked evidence files after its claimed freeze. The final
packet lacks postimage/guard/command/final-state artifacts and omits its first
129-failure/13-error matrix attempt. Proposed R3 is test/docs plus evidence
closure only, using exact intended owner `20260905_192221_6da09b` and freezing
duplicate `20260905_192249_150b51`:
`prompts/S11_C4_R3_DURABLE_CONTENTION_EVIDENCE_CLOSURE_MANAGER_2026-09-05.md`.

**S11-C4-R3 Codex independent rereview update (2026-09-06):** canonical and
remote are clean/equal at `4f2c787`; production remains frozen and fresh Codex
C4R1 6, T03G 152, T05A 14, T12 twice plus static/Alembic gates are green. S11
still remains `CHANGES_REQUESTED / NOT_APPROVED / NOT_CLOSED`: the committed
race test can label B blocked without proving B reached the production lock,
returns only revision count and never compares the exact expected four-field
snapshot. Two non-writing Codex mutants demonstrate both false-green paths.
The R3 root also lacks `commands.jsonl`, raw route/session files and a real
pre-R3 writable-test baseline. Bounded R4 keeps production frozen, continues
Manager `20260905_162953_5a5cda` and resumes only exact owner
`20260905_192221_6da09b`:
`prompts/S11_C4_R4_DETERMINISTIC_LOCK_EVIDENCE_CLOSURE_MANAGER_2026-09-06.md`.

**S11-C4-R4 Codex independent rereview update (2026-09-06):** canonical and
remote are clean/equal at `1f5936d`; production is unchanged. The R4 durable
test now proves B reached the delegated real-lock boundary and compares the
complete revision map plus immediate exact four-field snapshot. Fresh Codex
C4R1 6, T03G 152, T05A 14, T12 twice and static gates are green; both actual-
test negative controls are rejected correctly. Product/test work is complete,
but S11 remains `CHANGES_REQUESTED / NOT_APPROVED / NOT_CLOSED` on one evidence
P1: R4 ledger rows 5-21 reuse one impossible zero-duration timestamp, raw gate
files lack the missing command envelopes, and a failed pre-resume guard is not
indexed. Bounded R5 is evidence-only in exact Manager
`20260905_162953_5a5cda`; no worker, code change, merge or push:
`prompts/S11_C4_R5_LIVE_LEDGER_EVIDENCE_ONLY_MANAGER_2026-09-06.md`.

**Epic exit:** unchanged source voice/BGM/SFX play in sync; Scenario D works without reviewing the full timeline.

---

## EPIC E08 - Validated 4K Delivery and Packaging

**Outcome:** approved projects render, resume and validate a clearly labeled 4K master.  
**Master Plan:** WS-08, WS-09, G5.

### Sprint S12 - 4K beta candidate

**Current dependency gate (2026-09-06):** `BLOCKED_DEPENDENCY` because `S11 =
NOT_CLOSED` after the independent S11-C4-R4 review. The PLANNED rows below
remain planning-only; no S12 implementation dispatch is authorized until Codex
approves/closes S11 and issues a separate S12 contract.

| Task ID | Session outcome | Depends on | Status |
|---|---|---|---|
| S12-T01 | Export preflight distinguishes native 4K from upscale | E07 | PLANNED |
| S12-T02 | GPU/CPU render profiles and capability detection | S12-T01 | PLANNED |
| S12-T03 | Chunked render, stitch and restart-safe checkpoint | S12-T02 | PLANNED |
| S12-T04 | Output validation covers StructuralLockManifest, resolution, frames/timebase, streams and partial files | S12-T03 | PLANNED |
| S12-T05 | Export UI shows estimate/progress/retry/result and evidence | S12-T04 | PLANNED |
| S12-T06 | Clean-machine packaging and supported hardware matrix | S12-T05 | PLANNED |

**Epic exit:** Scenarios F-G pass and a `.partial` artifact is never shown as completed output.

---

## EPIC E09 - Guided 2D Character Generator

**Outcome:** one simple 2D reference becomes a human-reviewed six-pose library pack without training.  
**Master Plan:** WS-05B, G4.5.

### Sprint S13 - Generator alpha

| Task ID | Session outcome | Depends on | Status |
|---|---|---|---|
| S13-P00 | Readiness package: dependency proof, domain/provider/validation contracts, write-set matrix and task packets | E04 | APPROVED — Codex C6 re-review 2026-08-23; binding 22-task planning baseline |
| S13-P01 | AI-assisted Character Fit Recommender delta: rank existing packs and generation starting profiles against the source/sample character with explainable compatibility evidence | S13-P00,S09 exit | USER_REQUESTED / PLANNED — required BA/PM delta review before any S13 production prompt; no dispatch authority |
| S13-T01 | Character Profile and stable reference-code prompt contract | E04,S13-P00,S13-P01 | BLOCKED_PLANNING_DELTA / NOT_DISPATCH_AUTHORIZED — S13-P01 must be decomposed and approved; then serialize shared schema/API paths behind active-authorized S10 |
| S13-T02 | ComfyUI/provider adapter with capability and failure contracts | S13-T01 | PLANNED |
| S13-T03 | Pose-conditioned six-panel generation job | S13-T02,E01 | PLANNED |
| S13-T04 | Identity/style/pose validation and panel status | S13-T03 | PLANNED |
| S13-T05 | Guided upload→profile→generate→review UI | S13-T04 | PLANNED |
| S13-T06 | Regenerate one panel and preserve approved panels | S13-T05 | PLANNED |
| S13-T07 | Publish complete approved output as immutable Pack Version | S13-T06 | PLANNED |
| S13-T08 | Scenario J quality/performance benchmark report | S13-T07 | PLANNED |

**Execution update (2026-08-29 19:30 +07):** S13-P00 C6 remains Codex
`APPROVED` planning-only; no P0/P1/P2 planning finding remains. Production S13
is still `NOT_OPENED`: authorized S10-C4 correction and early S13 share the
integration tree and authority paths, with later overlap on
`frontend/src/lib/api.ts`. The existing
`prepare-s13-t01` worktree must be re-preflighted against the eventual stable
integration HEAD. A new Codex production prompt is required only after S10 is
APPROVED/CLOSED and shared write-set ownership is reconciled.

**Additive product update (2026-08-29 21:55 +07):** the user requires
`S13-P01` before production S13. This is an additive planning delta and does
not rewrite or silently invalidate the approved 22-task S13-P00 evidence.
Codex BA/PM must decompose and review the recommender write-set, dependency DAG,
privacy/model policy, acceptance gates and benchmark additions, then fold the
approved delta into the future production prompt.

### S13 mandatory identity-quality requirements

These requirements are inherited by every S13 implementation task and may not be
weakened by a provider-specific shortcut:

- Separate immutable `Character Identity` from versioned pose-pack candidates and
  published `Pack Version`; projects pin the exact published version they use.
- Generate and review one slot at a time from the same reference hash, identity-profile
  hash, prompt-template version and reproducibility metadata. Only pose/camera variables
  may change between slots.
- Each slot follows `GENERATING -> REVIEW_REQUIRED | REJECTED | APPROVED -> SUPERSEDED`.
  Regenerating one slot preserves all other approved slots.
- Publish is fail-closed: all six required slots must pass hard integrity/topology checks
  and explicit human approval. Uncertain or near-threshold results are
  `REVIEW_REQUIRED`, never silent `PASS`.
- Validation covers real transparency, SHA-256/size/resolution, silhouette, palette,
  landmark/proportion, limb topology, line weight/style, clothing/accessories,
  cross-view identity, unwanted text/watermark/background and crop completeness.
- Every compositing-ready slot has a consistent canvas, scale, facing direction,
  ground/contact anchor and bounding box; no cropped limbs or unexplained position/scale
  jump is allowed across views.
- Review UI keeps the original reference visible and supports zoom plus
  overlay/blink/wipe comparison, validation reasons, candidate history and single-slot
  regeneration.
- Every candidate records reference/profile hashes, provider/model/adapter version,
  seed, final prompt, generation settings, template version and approval audit data.
- V1 is deliberately limited to simple flat-color 2D stick/doodle characters with clear
  outlines and standard two-arm/two-leg topology. Complex anime, photoreal, 3D,
  gradients and texture-heavy styles remain unsupported until benchmark evidence exists.
- S13-T08 must use a 20-40 character golden set with approved six-slot truth, controlled
  variations and negative identity-drift examples. The primary metric is false-accept
  rate, followed by review/regeneration rate, repeatability, latency and cost per pack.

### S13 AI-assisted Character Fit Recommender requirements

These requirements implement the user request to use the source/sample
character to recommend equivalent characters or generation starting profiles
that are easier to pose and reskin:

- Build a source requirement profile from approved source-role evidence; rank
  eligible immutable Pack Versions and, when no pack is sufficient, compatible
  generation starting profiles/templates. Never recommend drafts or incomplete
  packs as ready-to-use replacements.
- Apply hard compatibility gates before AI similarity: topology/limb count,
  required view and pose coverage, articulation range, anchors/contacts/prop
  needs, scale, proportion and silhouette. A style or embedding score may never
  override a hard geometric blocker.
- AI similarity may assist ranking with appearance/style embeddings plus
  outline, palette, clothing/accessory and proportion signals. The system must
  remain provider-agnostic and local-first; an unavailable AI model falls back
  to deterministic compatibility evidence, not fabricated confidence.
- Return an explainable Top-K list with per-dimension scores, blockers,
  missing pose/view coverage, confidence/calibration and the expected renderer
  or controlled-redraw risk. Do not expose only one opaque global score.
- The recommendation is advisory. The user confirms the character/pack or
  generation profile; AI may not silently change identity, auto-publish a pack,
  bypass Demo/compatibility gates or alter approved slots.
- Pose generation keeps the chosen target identity/reference hash immutable
  across all slots. Source-character similarity guides compatibility and pose
  conditioning only; it must not copy the source character's protected visual
  identity into the target.
- Extend the golden benchmark with Top-K compatible-hit rate, hard-blocker
  leakage (target: zero), explanation correctness, calibration, and measured
  review/regeneration/render-route reduction versus selection without the
  recommender. Benchmark inputs and expected matches are frozen before runs.

**Epic exit:** generator failure cannot block manual library usage; only complete reviewed packs can be published.

---

## Task activation rules

- Chỉ một task ở trạng thái `IN_PROGRESS` trừ khi PM chủ động cho phép parallel work với write scopes không giao nhau.
- Task chỉ chuyển `PLANNED -> READY` khi mọi dependency đã `APPROVED` và PM đã tạo session packet.
- Sprint/epic exit là task review riêng nếu evidence phân tán; không tự suy ra từ việc các PR đã merge.
- Thứ tự E04 và E05 có thể overlap sau khi contract ObjectRole tối thiểu được approve; `S07-T01` vẫn chờ contract đó.
- E09 có thể chạy sau E04 nhưng mặc định đặt sau beta reskin để không làm trễ core value.
- Ngoại lệ đã cấp quyền 2026-08-22: `S13-P00` readiness-only được chạy song song với S09/S11 vì chỉ ghi output riêng. Không task production S13 nào được mở trước Codex review P00 và một prompt cấp quyền mới.
