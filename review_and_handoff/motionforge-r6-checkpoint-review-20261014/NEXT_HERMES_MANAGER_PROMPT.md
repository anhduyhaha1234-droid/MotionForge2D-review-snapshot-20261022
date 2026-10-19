Đọc TOÀN BỘ C:/Users/Admin/MotionForge2D/docs/pm/HERMES_AUTOPILOT_RULES.md trước mọi preflight/dispatch. Báo RULES_LOADED, absolute path và HEAD thực. Đây là prompt hoàn chỉnh để user giao Hermes Manager; Codex chưa launch/message/resume.

# R6 continuation sau checkpoint review 14/10/2026

## 1. Authority, current state và required reading

Bạn là Hermes Manager, chỉ điều phối/harness/QA/báo cáo trong allowlist; không viết media implementation, production, UI, tests sản phẩm hoặc config thay worker. Codex là gate độc lập, user tự dispatch. Chỉ MotionForge2D; Agribank ngoài scope.

Paths:

- MAIN = C:/Users/Admin/MotionForge2D
- INTEGRATION = C:/Users/Admin/Documents/Codex/work/mf-delivery-20260927/INTEGRATION
- RUN = C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long
- D = RUN/tasks/MF-DEMO-LONG-01
- C = D/corrections/identity5m_20261008
- R6 = C/r6
- U = C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-r6-checkpoint-review-20261014
- N = C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-tech-conformance-20261012
- O = C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-r5-review-20261012
- P = C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-r4-review-20261011
- STACK = C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-r4-stack-update-20261009
- P3 = C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-r3-review-20261009
- B = C:/Users/Admin/Documents/Codex/work/mfv1/runtime/video14b

Sau rules, đọc MAIN/AGENTS.md, docs/pm/SESSION_PROTOCOL.md, Current execution của CODEX_PM_HANDOFF.md và ROADMAP.md; U/REVIEW_VI.md, U/CORRECTION_MATRIX.md, U/SESSION_OPENING_PROPOSAL.md. Đọc N/TECHNOLOGY_AUDIT_VI.md, TECH_CONFORMANCE_MATRIX.md để giữ T01–T15 và đúng công nghệ. Đọc P3/CAST_B_SPEC.md, STACK/STACK_SOURCE_LOCK.json, P/NEWTECH_SOURCE_LOCK.json; source bổ sung ở N/SOURCE_LOCK_FINAL.json. Chỉ mở evidence/source theo finding, không nạp toàn lịch sử hay tìm framework mới.

U là current execution prompt, thay N/NEXT_HERMES_MANAGER_PROMPT.md về trạng thái và continuation; giữ các technical requirements, frozen R5 findings và canonical Q01–Q12. Không coi packet nghiên cứu video-skills là quyền mở tool feature.

Đã chạy R6→R6f, không bắt đầu lại từ số0. R6f `LONG01-R6f-20261012T1820Z-3211` kết thúc 2026-10-12T20:17:07Z vì HTTP503 bọc provider429 weekly quota. Receipt NEEDS_RECONCILIATION; terminal giữa lượt CONTINUE_REQUIRED/12UNKNOWN; chưa có Manager EXIT. Các mốc reset được log đã qua nhưng quota phục hồi chưa được xác nhận. Không coi exit0 hoặc callback là TASK_SUBMITTED.

Codex review checkpoint: CHANGES_REQUESTED, 9FAIL+2UNKNOWN+1PASS engineering. Master đủ 5phút nhưng S33/S61 còn portrait sai, S73 mất cầm sổ; F02–F09 chỉ rõ gate/event/tracking/cache/manifest defects. QUALITY_ACCEPTED=0, codex_accepted=0; S12/S13 NOT_APPROVED/NOT_CLOSED. Full22/tool/UI/backend/package/integration BLOCKED_DEPENDENCY.

## 2. Owner/model và preflight bắt buộc

Cùng Task **MF-DEMO-LONG-01**, RUN, revisionR6, cumulative counters. Manager **20261012_002032_daa36c**; sole worker **20261007_234033_cc0b6d**. Correction phải resume exact worker; không tạo session chỉ vì R6g hoặc Codex mới. Không resume W2r `20261005_235131_0caeab` dead context. Nếu user giao một Manager mới, reconcile takeover đúng một controller sau zero-writer; không đổi worker tùy tiện.

Route giữ nguyên: provider `custom`, model `cmc/deepseek/deepseek-v4.1-flash`, endpoint `http://127.0.0.1:20128/v1`, API `chat_completions`, fallback OFF. Giữ effective reasoning/adapter đã xác minh từ runtime, không bịa enum hay đổi global profile. Installed Hermes0.19/source thực quyết định API. Không sửa global HERMES_HOME/config/router/Torch và không mua quota.

Preflight:

1. Pin HEAD/status thực: review thấy MAIN master@a40e368f7c47c232cf2eeed9fb185c5972cb98ba dirty; INTEGRATION codex/mf-end-integration-0928@a52fca897906fd61a088016dd802718fdf06d217 clean. Giữ local edits; không reset/clean/stash/checkout/commit/push/merge.
2. Audit actual process PID+create_time+exe/descendants, queue, controller lock, leases, registry/dispatch/receipts. Snapshot reviewer queue rỗng, 6leaseRELEASED, không worker/render; heartbeat còn sống không là writer. Kiểm lại lúc dispatch. Không kill/unload Comfy hoặc dịch vụ khác. Nếu active/detached/UNKNOWN, không mở writer thứ hai.
3. Đọc Hermes DB bằng mode=ro/query_only và lưu query/export mới. Review thấy Manager402active/319compacted; worker586active/4882compacted, đều message counts. Không mutate/vacuum DB, không suy context hỏng từ count.
4. Bảo toàn R6f terminal/log/receipts/current bytes; append `R6F_RECONCILE` mới. Sửa current registry stale có preimage; không backfill terminal cũ. Terminal R6f hiện 40/42 hashes đúng; hai mismatch r6_qa.py và R6_COTRACKER_RUNS.jsonl. Remaining_work cũ chưa phản ánh master/tracking đã làm.
5. Audit incident theo writer lineage: historical16R4 evidence drift, staleR5d, R6b refresh nhầm terminal inv1. Preserve hashes/current bytes và điều tra attribution. Không reset/gộp sai incident counts. Nếu lần unsafe scope violation thứ hai trong cùng lineage hoặc repeated context corruption theo§4: dừng BLOCKED_CONTEXT_HEALTH / OWNER_TRANSFER_REQUIRED và trình evidence; không cứ cấp guarded retry mới. Nếu đủ điều kiện recovery theo canonical§4, zero-writer của owner cũ, đúng một successor, append transfer và handoff tối thiểu; không tồn tại hai owner.
6. Trước mutation, worker phải restate đúng pilot/12Q/write-set, phân biệt identity/pose/count/contact, event fid, consumer gate, immutable records; đưa current findings và next command vào compact context. Nếu hiểu sai thì sửa context trước work, không seed sweep.
7. Route/quota check tối thiểu theo runtime hiện có trước dispatch dài. Reset time không đủ chứng minh có quota. Nếu quota/auth/config vẫn fail có bằng chứng thì giữ checkpoint và báo blocker thật, không fallback hoặc retry mù. Khi route khỏe, resume exact owner trong scope được cấp.
8. Guard SHA256/bytes/lines/mtime/tracked-dirty cho writable/protected; byte-for-byte snapshot critical dirty/untracked/test authority và verify hash. Existing files bounded patch duy nhất preimage; không full replace. Missing/shrink/outscope → freeze và incident audit. Manager không reconstruct implementation.

## 3. Phạm vi, frozen inputs và exclusive write-set

Pilot nguồn94–394s, frames[2820,11820), S0021–S0074, 54shots, 9000frames,30fps640×360,video300s, audio nguồn cùng span. CAST B/flat2D thay diện mạo người/props/background; giữ role/action/contact/occlusion/camera/cuts/timing, không chỉ đổi palette hoặc dán portrait.

Frozen anchors:

- R6f master `e3107a52c9f10bc36faf7d5aa3aa2e4c4186edae3cd916c52dff9b24eed9e48e`.
- R6f comparison `f11f43becf58fa5d9ada18af4ab9dcaac494e47ed8b4d8b41fb87bbe33b140a8`.
- R5 master `b8b9a404e4ef947429b34448acda1ff63881ca90f5c7ee22dfee3b85c7ee272d`.
- R5 comparison `49f6eb8ca22ff5542f553dd83bda46a2749dda7d64ecd5205b7565703fc70d7a`.
- R5e terminal `7940a569d541a650566049dd3aef9637c987b8a57d440e430d74910eec1d4271`.
- Source `5a175454c2c2965bac5013a53926e210a9f70a185d802d0f2e0083a6fb399fa2`.
- R4 master `77fc6122520286bfb066f27119a0edb0e5d1f7ed2e9006400a13c312d6526209`.
- CAST board `95572075bd72010854b5e82c5d97e1a5d83199409999370e0a506821dda95415`; style `77fdfc79c210e9fba6bd565949fd0aed7983e6ffe2d41e8fd3c0910a286d8dd0`.

Worker write-set chỉ R6/** và D/{input,output,temp}/identity5m_20261008/r6/**. Existing scripts/ledger/storyboard được bounded patch sau guard/snapshot. **Old terminal/evidence/receipts/review records và hai R6f media đã review frozen**; tạo record/version/candidate mới trong R6, không overwrite để làm lịch sử khớp lại. Dùng namespace mới `R6/continuations/<new_invocation_id>/**` cho output/cache/QA/manifest/reviews; adapter cho path này được sửa tối thiểu trong R6. Existing valid artifacts tái dùng read-only theo exact hashes. Không cần copy lại mọi video hay regenerate mọi shot.

Manager write-set: new RUN/manager/evidence/r6/**, new packets/receipts/logs cho invocation mới; existing manager/tools/tests/current registry/ledger/lease/heartbeat được bounded patch/append qua công cụ đã có, preimage+guard. Manager không viết media adapter thay worker. All old packets/receipts/evidence/terminals frozen, generic manager/** không waive.

MAIN/INTEGRATION/production/tests/DB/global env/Comfy/Torch/router/source/style/CAST/W7/C1/C2/R3/R4/R5/U/N/O/P/STACK/P3 protected read-only. Reuse installed upstream/models read-only; PYTHONDONTWRITEBYTECODE=1, redirect cwd/cache/outputs sang R6 namespace. Không cài lại framework/model sẵn có, không viết flow/render/tracking core mới.

## 4. Task map, dependencies và parallel wave

Đây là **một task hiện hữu MF-DEMO-LONG-01**, không tạo TaskID/worker mới cho từng mục. Các bước dưới là checkpoints nội bộ, cùng worker; Manager có lane coordination/harness disjoint. Maximum safe wave WIP1/GPU1 vì toàn pilot dùng chung dependencies/media/runtime.

| Bước | Outcome nhị phân | Dependency | Owner/write-set |
|---|---|---|---|
| A | R6f/quota/context/incidents reconciled; zero-writer, route và guard đạt | Rules/current evidence | Manager, allowlist điều phối |
| B | Canonical12Q, event schema, gates/cache/output-freshness actual consumer fail-closed; F02–F09 micro repros đóng | A | Exact worker, R6 adapter/test fixtures riêng |
| C | Hard excerpts S33/S61/S73 và identity/role/pose khác đạt source/ref/key/final | B, validated masks/refs | Exact worker, new candidate namespace |
| D | Rerender đúng event ranges, contact queries/windows thật; controls S74 không regression | C | Exact worker; GPU tuần tự |
| E | 54shots đủ5phút, AV/cuts/manifest/12Q đủ evidence | D + reuse các phần valid không bị invalidated | Exact worker |
| F | Manager held-out source/ref/final QA và artifact/guard kiểm độc lập | E frozen, writer exited | Manager verification disjoint |
| G | MANAGER_VERIFIED_PENDING_CODEX_REVIEW | 12PASS thật, remaining_work rỗng, all hashes match | Dừng dispatch, chờ Codex |

Full22/tool/backend/UI/package/integration chưa dependency-ready nên không mở. Read-only CPU checks độc lập có thể song song; shared runtime/global gates qua mutex và writer frozen. Không mở worker để tận dụng slot trống.

## 5. Correction cần làm bằng actual code và pixels

**F02 semantic gates:** schema review bắt buộc complete inputs/expected/reviewer/evidence; so exact current dependency set, không chỉ duyệt keys tự khai. Missing/UNKNOWN/stale/tampered/wrong cast/count/role/empty visible mask/source-copy/re-encoded known-bad phải block actual key→propagate→assemble→submit. `gate_assemble` phải được actual assembler gọi và kiểm final blend review, không chỉ key reviews. Fresh encoder-spy negative test và valid control. Không lấy hash/palette/filecount làm semantic evaluator.

**F03 events:** thống nhất frame convention; producer SAM2 frame0→f0001. Event_map hiện `shots[sid]` với f/event/contacts. Normalize có explicit schema, không default[] che dữ liệu sai. Event keys là range boundaries/keys đúng fid, không stage grid1+n×10 rồi bỏ f103/105/107, không ±5frame waiver. Test off-grid key thực sự được upstream tiêu thụ đúng hash và output map không gap/duplicate.

**F04 tracking:** CoTracker paired S34/S61/S73 cùng source/output window và số frame thực; không min() che thiếu. Queries đúng hand/phone/book/actor landmark tại event, mapping tọa độ riêng từng clip; save queries/tracks/visibility/raw windows. S73 cần bổ sung source contact ledger thật. Mean grid drift không là contact acceptance. Không mặc định sửa bằng tăngmodel.

**F05/F06 freshness/cache:** exact consumed source bytes/span/frame, stagedrefs/views/masks, model/graph/prompt/settings, approved keys/reviews và upstream pins trong content identity. Không reuse video/tmp/flow/output cũ chỉ theo path/count; namespace theo content+invocation. Probe nine stale+one fresh, inner failure/outerrc0, missing frame, same-path same-size dependency mutations phải block. Verify every expected fresh decoded frame/output và child outcomes; tail duplication chỉ khi thuộc convention có chứng minh, không che failed run. Unchanged approved reuse được phép khi chứng minh đầy đủ.

**F01 pixels:** source-ledger/mask/pose/control trước gen. S33 nằm trên giường không có portrait dựng đứng; S61 không đầu lớn cửa sổ hoặc còn mặt nguồn cạnh xe; S73 giữ pick/hold/release sổ và người occluded. S22/31/41 giảm ghost nhưng còn sai hướng đầu; S62 entry reskin đầy đủ; S63/64/67/69/70/73 giữ đúng roles/occlusion. S57–60 flat2D car/style đồng nhất; giữ S74 explicit zero actor và document text/props. Dùng fresh frames/time trong U/REVIEW_VI.md và controls các shot tốt; không chỉ crop thẩm mỹ một vài key rồi gọi pilot đạt.

CAST mapping: B01Khang→E1, B02Lâm→E2/E8 theo source alias; B03Mai→E3, B04Phúc→E4 provisional/source verify, B05Vân→E5, B06Linh→E6, B07Thu→E7. Outfit/view là state, không người mới. Missing/empty mask khi visible phải fail; ZERO_VISIBLE/FULLY_OCCLUDED/UNKNOWN khác nhau. Không whole-board 7people ref, không whole-frame multi-ref thiếu spatial binding, không portrait standing thay sitting/lying; protect neighbors/props/z-order.

**F07 matrix/QA:** giữ nguyên ý nghĩa canonical12Q trong U/CORRECTION_MATRIX.md; không dùng matrix_rows hiện hardcode khác nghĩa. Source/ref/final visual checks theo head/event/tail tất cả54shots +scan2s+dense contact/occlusion/zoom/key/seam. Worker hỏi đúng identity/role/action/contact/style, không chỉ continuity/blackframe. Timeout/không xem được phải UNKNOWN. Manager chọn held-out frames sau freeze và thực sự xem độc lập. Xem normal speed/nghe audio nếu tooling hỗ trợ, thiếu ghi thật.

**F08 records:** reconcile closed R6f ở record mới; không sửa cũ. Invocation mới bind immutable dispatch run/task/owner/invocation/packet/revision/allowedroot. Mid-flight checkpoint phải nói đúng current bytes/remaining_work; final artifacts freeze trước terminal last; không cycle manifest↔terminal, không backdate. Nested hashes kiểm recursively. P1/UNKNOWN giữ trong remaining_work, không đẩy sang residual để PASS.

**F09 reproduction:** sửa comparison command `-ss300` trước master300s. Fresh output bắt đầu đúng pilotframe0, source94s/R5frame0/candidateframe0; verify9000f/samecut/timing. Ghi exact reproduce command tương ứng bytes; không overwrite R6f comparison đã review.

## 6. Giữ đúng upstream, không mở vòng nghiên cứu mới

- FLUX.2 Klein4B distilled FP8, Qwen3_4B, flux2VAE; 4steps/Euler/CFG1 đúng baseline. Không tăng50steps mù; refs/source pose nối tới sampler ở normal/repair/fallback, actual per-ref perturb chứng minh target changes/neighbors protected.
- SAM2 pin `2b90b9f5ceec907a1c18123530e92e794ad901a4`; R6 output root, canonical masks640×360, explicit pad4+4→368 đúng một lần/inversecrop. Không ghi R4tracks/masks hoặc positional fallback, không suy empty=absent. Giữ protected R4 tracks/masks trong guard.
- CropAndStitch pin `8584b08d851762965df898b421a39075fc5357ae`; reuse actual upstream crop+stitch, geometry roundtrip/outside-region invariant, không customalpha compositor core. Có stitch không tự làm edited crop đúng pose.
- Rerender `dfaf9d8825f226a2f0a0b731ab2adc84a3f2ebd2`, EbSynth `02ec8c4e4d4a568057363ae8b8f8bb8f7e4898c2`, GMFlow `af2d869a6fa38b0b076d6f28ab5af1f64beca335`: hiện stage2video_blend, không claim stage1. Upstreaminner failures/cache cần adapter guard ở F03/F05/F06.
- VACE1.3B local: bảo toàn trialS73base/perturb vàS62 mới; verify graphsubmitted với KSampler→TrimVideoLatent.samples, WanVaceToVideo.output3→trim_amount, TrimVideoLatent→VAEDecode, reference/controlvideo/masks nối thật. Same source windows 4n+1 và frame map; không cắt4decodedframes thay latenttrim. Không rerun chỉ vì đang UNKNOWN khi proof có thể kiểm từ bytes. Engine choice phải dựa identity/pose/contact actual pixels; nếu route đã chọn vẫn sai, causal correction hoặc conditional alternative, không tuyên bố modelceiling từ trial sai.
- CoTracker `82e02e8029753ad4ef13cf06be7f4fc5facdda4d` paired semantic queries như§5. ProPainter `e870e79321c31b733e2031af5aa2fb1fe3ac7eec` chỉ khi cần cleanplate. MoCha fallback sau validroutes thất bại có evidence, pinned workflow P3/vendor_review/ComfyUI-WanVideoWrapper/example_workflows/wanvideo_2_1_14B_MoCha_replace_subject_KJ_02.json; wrapper `088128b224242e110d3906c6750e9a3a348a659b`. Chưa cần thì NOT_NEEDED có lý do; không clone là adoption.
- ASR/cuts/transcript frozen; prior224/224cut candidates giữ, không broad rerun. VBench chỉ triage, không thay semantic acceptance. Giữ upstream licenses và source locks; internal eval không tự clearance thương mại.
- GPU1, RTX5070 khoảng12GB/RAM64GB. Model tuần tự; đo allocated/reserved trong process thật, sampledNVML và RAM tách biệt. CoTracker reported18–21GB cần diễn giải phép đo/shared memory chứ không tự gọi physicalVRAM peak; VACE client0 không phải peak server. Không global upgrades/cài orchestrationframework.

## 7. Verification gates và continuation

Micro repro từng F → canonical12Q evidence mapping → focused/static/workflow checks → final AV/cuts/guard. Không broad-green waive rowfail. Preserve Q11 actual consumers; Manager test ở **new isolated root**, DISPATCH_TEST=1 và Pythonfakechild, không launchHermes trong tests. True-race proof phải hai livecontrollers rendezvous ngay acquire/reserve, đúng1winner/1child, auditallrows/boundedjoins; ordered-heldlock riêng. Reuse exact existing proof khi phù hợp; không buộc rerun suite rộng chỉ vì đổi tên invocation. Old evidence không ghi lại.

Q01 identity/refs/pose; Q02 actors/roles/visibility; Q03 contact/events; Q04 ghost/props/background; Q05 semanticactualgates; Q06 VACEpaired/conformance; Q07 dependencies/cache; Q08 AV/frames/cuts; Q09 ManagerheldoutQA; Q10 immutablemanifests/terminaltruth; Q11 harnessconcurrency; Q12 actualupstreamadoption. Status mỗi dòng chỉ PASS/FAIL/UNKNOWN; có source/function/test/frame/hash/owner. Không đổi tên để biến thiếu contact thành enginePASS.

Không PM totalbudget/deadline/tokens/calls/candidates/correction/continuationcap. Giữ cumulative counters; technicalinvocation/context limits vẫn hiệu lực, checkpoint→reconcile→sameownerresume. Hai lượt cùng cách không usableprogress phải đổi phương pháp dựa evidence, không seed sweep. Native todo một in_progress; background phải có durableprocess/liveness/lease tracking, không bỏ child khi turnend.

Heartbeat tối đa20phút khi còn việc; 8phút không progress kích auditPID/log/queue/input/route. HTTPtransient502/503/504/disconnect chờ5phút rồi retry cùngroute/owner sau reconciliation; không giới hạn số vòng transient nhưng không blindretry lỗi429quota/auth/invalidpayload đã xác định. Error503 bọc429 phải phân loại theo causalerror. Khi quota thật chưa hồi, báo checkpoint+nextaction, không gọi TASK_SUBMITTED và không fallback.

## 8. Deliverables, terminal và start

Nộp candidate mới trong R6 namespace với master có audio, comparison source|R5|newR6, sourceledger/storyboard/castatlas/masks/eventmap, graphs/commands/pins/model/resource/attempt receipts; CORRECTION_MATRIX12rows đúng authority, matrixevidence, currentcheckpoint/remainingwork, immutablemanifest và reproducecommands. Stage adoption phân biệt SOURCE_READY/ENV_READY/SMOKE_PASS/SOURCE_UNIT_PASS/PILOT_PASS; license/resource limitations trung thực.

Final media9000frames30fps640×360/video300s, sourceaudio94–394s; decode0, exactsourcecuts/frameplan/seams, head/mid/tail lag; AAC tail hợp lệ không tự lỗi. Freeze candidate, writer terminal, Manager independentQA+hashes+guard; không tự approveS12/S13.

Terminal mới R6/evidence/terminal/<new_invocation_id>.json (file mới): đúngbinding/packet/owner/revision, requiredartifacts+SHA. FAIL/UNKNOWN/P1 còn mở → CONTINUE_REQUIRED hoặc NEEDS_RECONCILIATION đúng nguyên nhân; blockerroute/quota/context có evidence. TASK_SUBMITTED chỉ12PASS thật và remaining_work rỗng → Managerverify → MANAGER_VERIFIED_PENDING_CODEX_REVIEW, dừngdispatch chờCodex. Không sửa trạng tháiQUALITY_ACCEPTED/codex_accepted khỏi0.

Required finalreport: actualtask/session/modelmap, quota/context/incidentdecision, bytesreused/changed với hashes, tests pass/fail/notrun, source/ref/final frames đã xem, 12Q, resources/counters, manifest/terminal validation, blockers/remainingwork/nextcommand và protecteddrift.

**Bắt đầu ngay bằng RULES_LOADED → preflight/reconcile R6f/quota/context/guard → đúng owner theo U/SESSION_OPENING_PROPOSAL.md khi điều kiện đạt. Thực hiện correction đến candidate đủ review hoặc blocker thật; không trả lại kế hoạch lý thuyết, không restart từ đầu, không mở full22/tool.**
