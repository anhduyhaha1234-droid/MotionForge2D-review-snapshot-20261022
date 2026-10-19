# MotionForge2D — Codex PM Session Handoff

Đọc file này đầu tiên khi tiếp quản bằng một Codex chat/session mới. Đây là
checklist phục hồi ngữ cảnh; TASK hiện hành, filesystem và process thực tế vẫn
là nguồn sự thật. Không dựa riêng vào lịch sử chat hoặc lời tóm tắt của Hermes.

Trước file này, bắt buộc đọc toàn bộ
`C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`. Rules là
canonical cho orchestration; file handoff này chỉ giữ trạng thái điều hành và
không được dùng để ghi đè rules.

### Current execution — 2026-10-14: R6f checkpoint cần correction, chưa nộp final

Packet hiện hành: `C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-r6-checkpoint-review-20261014/`.
Đọc REVIEW_VI, CORRECTION_MATRIX, NEXT_HERMES_MANAGER_PROMPT và matching
SESSION_OPENING_PROPOSAL. Thay execution prompt12/10; technical T01–T15 và12Q giữ.

- Đã chạy6invocations R6→R6f. R6f dừng13/10 03:17+07 bởi weeklyquota429 bọc503;
  receiptNEEDS_RECONCILIATION, terminalCONTINUE_REQUIRED/12UNKNOWN, chưaManagerEXIT.
  RegistryR6_RUNNING stale; heartbeat sống không đồng nghĩa worker làm việc.
  Snapshot14/10 queueempty/no worker-render/6leasesRELEASED; quota recovery chưa thử.
- Mastere3107a52…e48e:9000f300s30fps640×360/decode0/audiohead-mid-taillag0.
  Codex xem54midpoints+23frames; không continuousplayback/listening. S74 tốt hơn;
  S33/S61 portrait sai, S73 mất sổ; canonicalmatrix9FAIL+2UNKNOWN+1PASSengineering.
- Actualconsumer gateassembly chưa gọi; eventkeys bỏoffgrid; CoTracker reader sai
  schema/windowsrỗng; partialstaleoutput+source/modelcache mutationbypass. Script
  matrix đổi nghĩa12Q. Terminal40/42hashesmatch, chưafinalmanifest/matrixevidence.
- Manager20261012_002032_daa36c,worker20261007_234033_cc0b6d không đổi. Message
  countsManager402active/319compacted,worker586/4882. Context/incident§4/zero-writer
  audit và quotahealth trước continuation. R6b sửa nhầm terminalinv1 cần reconcile
  theođúnglineage; khôngresetincidents/tựđổiowner. User tự giao prompt;Codex chưa dispatch.
- CùngMF-DEMO-LONG-01/RUN/R6/counters,CASTB/pilot5phút,WIP1GPU1,noPMtotalbudget.
  GiữR6fmedia/oldrecords frozen, implementationboundedpatch và candidate/cache/
  evidence mớiR6/continuations/<new_invocation_id>. Source/style/cast/priorrevisions/
  MAIN/INTEGRATION/prod/tests/DB/runtime protected. QUALITY0/codex_accepted0,
  S12/S13NOT_APPROVED/NOT_CLOSED;full22/tool/integrationBLOCKED_DEPENDENCY.

### Historical execution — 2026-10-12: R5 FAIL, R6 technology-conformance prompt

Technical audit mới đã xong: `C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-tech-conformance-20261012/`.
Đọc TECHNOLOGY_AUDIT_VI.md và TECH_CONFORMANCE_MATRIX.md; prompt Hermes và
session proposal hiện hành trong thư mục mới này, thay prompt kỹ thuật cũ.
Source snapshots/pins và fresh static/CPU proofs đi kèm; chưa chạy R6.
Giữ toàn bộ R5 verdict/evidence bên dưới. Findings bổ sung: SAM2 write-root
R4 và mixed canvas trong reused S61 masks; Rerender stage2-only; VACE thiếu
latent trim; CoTracker thiếu raw visibility. FLUX4steps đúng; cuts224/224 giữ.
Source/API đúng không tự là quality pass; current owners và12Q không đổi.

- R5 master b8b9a404e4ef947429b34448acda1ff63881ca90f5c7ee22dfee3b85c7ee272d:
  fresh 9000 decoded frames, video300s/30fps/640×360, full AV decode0,
  audio đầu/giữa/cuối lag0ms. Codex xem54midpoint+106cặp temporal19shot;
  chưa xem/nghe liên tục. Một số mặt tốt hơn, nhưng identity/role/pose/contact
  vẫn FAIL; S33 thêm người trên giường, S61 giant portrait, S74 giấy thành2người.
- Matrix độc lập10FAIL+1UNKNOWN/PARTIAL+1PASS engineering. QUALITY0,
  codex_accepted0; S12/S13 NOT_APPROVED/NOT_CLOSED; full22/tool/integration blocked.
- New tech đã chạy một phần: upstream crop nhưng custom compositor thay stitch;
  VACE1.3B S73 thiếu TrimVideoLatent nên81→85frames, chưa có valid A/B để chọn
  engine; CoTracker S34 source81/output220 không paired. Cache/semantic gate còn
  bypass. Không kết luận VACE model ceiling hoặc mask lệch1frame từ comment.
- Current Manager20261012_002032_daa36c; worker20261007_234033_cc0b6d. Manager
  20261011_123932_c101dc lịch sử. R5e nộp chờ review, snapshot queue rỗng/không
  render; Manager báo monitor dừng/5leases RELEASED. Không phải budget-stop.
- Context snapshot: Manager319active/0compacted, worker566active/3540compacted
  là message counts. Context-health/incident audit§4 trước continuation. Giữ
  owner nếu audit đạt; recovery chỉ khi đủ evidence, zero concurrent writer.
- Fresh harness51/51 PASS; true two-controller barrier proof còn thiếu. Terminal
 18/18 direct artifact hashes khớp nhưng nested manifest2148/2149: R5d terminal
  đổi.16 frozenR4 evidence files drift sau review trước. Bảo toàn và append
  reconciliation; regression mới chỉ ghi evidence/r6, không sửa lịch sử.
- R6 cùng TaskMF-DEMO-LONG-01/RUN20261005T1643Z-wan-long/counters; CAST B/flat2D,
  pilot[2820,11820), WIP1/GPU1, no PM total budget/candidate/deadline cap. Sửa
  source ledger/pose/masks→upstream crop+stitch/official VACE trim→paired excerpts
  →route đạt→semantic gate/cache→54shots/5phút. R4/R5 frozen; không mở full22.
- Packet R5 review đóng băng (prompt mới xem thư mục technical audit ở trên):
  `C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-r5-review-20261012/`
  Đọc REVIEW_VI, CORRECTION_MATRIX, TECH_DECISION_VI, SESSION_OPENING_PROPOSAL.
  NEXT_HERMES_MANAGER_PROMPT.md hoàn chỉnh để user giao; NEXT_CODEX_SESSION_PROMPT.md
  cho Codex session mới. User tự dispatch; Codex chưa launch/message/resume.
  MAINa40e368f dirty/INTEGRATIONa52fca89 clean giữ; reviewer chỉ3PMdocs cópreimages
  và isolated outputs. FINAL_GUARD.json ghi drift kiểm cuối, tách drift có trước.

### Historical execution — 2026-10-11: R4 CHANGES_REQUESTED, R5 prompt sẵn để user giao

- R4 master77fc6122520286bfb066f27119a0edb0e5d1f7ed2e9006400a13c312d6526209:
  đúng9000frames/300s/30fps/640×360, fullAVdecode0, audio đầu/giữa/cuối lag0ms.
  Visual54midpoint+88cặp temporal xác nhận đổi mặt S23, tráo vai S31/41/62,
  ghost S57/59/61, mất sổ S22/73 và người khuất một phần. Không claim đã xem/
  nghe liên tục. 13shots source passthrough74.933s chưa đạt reskin.
- Matrix9FAIL+2UNKNOWN/PARTIAL+1PASS engineering; QUALITY0/codex_accepted0,
  S12/S13NOT_APPROVED/NOT_CLOSED. Full22/tool/integration BLOCKED_DEPENDENCY.
- SAM2 inference8shots và Rerender/EbSynth/GMFlow batch có thật; CoTracker
  chưa có source-unit proof, ProPainter conditional/source-only. Fallback
  FLUX mất CAST refs, mask/semantic gate/cache còn bypass. Manager actual
  consumers còn lỗi active lease/UNKNOWN child/stale terminal/stall-kill.
- Manager actual20261011_123932_c101dc, exactworker20261007_234033_cc0b6d.
  R4e đã nộp, hiện dừng chờ review. Snapshot queue rỗng; lastheartbeat23:07:12+07
  chưa xác nhận monitor live lúc23:21. Worker313active/2888compacted, Manager
  196active/199compacted là message counts, cần context/zero-writer audit.
- R5 cùngTaskMF-DEMO-LONG-01/RUN20261005T1643Z-wan-long/owner/counters,
  chỉartifactrevision mới. Giữ pilot[2820,11820),S21–74,CAST B/flat2D/WIP1GPU1,
  noPMbudget. R4 frozen; user tự giao, Codex không dispatch hoặc đổi registry.
- Bổ sung upstream CropAndStitch per-actor edit: pin8584b08d…357ae,74tests và
  pixel invariance probe đạt, chưa là identity/video pass. VACE1.3B/14B files+
  WanVaceToVideo node đã có local; R5 bắt source-unit đối chứng S62/S73, chưa
  có inference proof. CoTracker phải chạy contact thật; MoCha fallback sau
  bằng chứng. Không cài lại framework hoặc tự viết core.
- Packet hiện hành:
  `C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-r4-review-20261011/NEXT_HERMES_MANAGER_PROMPT.md`.
  Đọc REVIEW_VI, NEWTECH_DECISION_VI, CORRECTION_MATRIX, SESSION_OPENING_PROPOSAL;
  chỉ mở fresh probes/temporal evidence tương ứng. Prompt đủ owner/route/
  write-set/guard/continuation, rules§0.7. MAINa40e368f dirty và INTEGRATION
  a52fca89 clean giữ; reviewer chỉ cập nhật3PMdocs có preimages và isolated outputs.
  Hash lại38,174file PRE của worker:0drift trong phạm vi manifest.

### Historical execution — 2026-10-11 trước R4 submission: source reuse + Manager reliability

- Snapshot12:14+07: chưa có C/r4, queue Comfy rỗng; 209 protected files/media
  đúng hash. Worker348active/1810compacted, Manager315active/231compacted;
  last worker CONTINUE_REQUIRED và registry stale như09/10. Heartbeat còn
  sống không chứng minh worker render đang chạy. Cần actual-controller,
  context-health và zero-writer/child audit trước resume; không reset counters.
- R3D vẫn CHANGES_REQUESTED; chưa có media mới để đổi verdict. CAST B/style/
  pilot[2820,11820),S21–74/noPMbudget/WIP1GPU1 giữ nguyên.
- User yêu cầu repo có sẵn cho cả thành phần lỗi và Manager. Phát hiện cụ thể:
  w2_anchor2 chỉ cấp2cast, S63/67/70/73 bỏ businessman và prompt cấm thêm người.
  Giữ FLUX.2, sửa ref binding; SAM2 masks, Rerender propagation, CoTracker
  contact khó, ProPainter khi cần plate. VBench chỉ advisory. Không viết core mới.
- Đã tải/pin thêm1076sourcefiles SAM2/CoTracker/ProPainter; chưa cài weights/
  chạy inference. Terminal contract Pydantic reference đạt25/25ca cô lập;
  live dispatch/heartbeat chưa patch. Prompt bắt Manager sửa consumer/lease
  và worker tạo source-unit proof rồi pilot, không dừng ở research/install.
- Packet hiện hành, thay prompt09/10 nhưng cùng r4/Task/RUN/exactowner:
  `C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-r4-stack-update-20261009/NEXT_HERMES_MANAGER_PROMPT.md`.
  STACK_DECISION_VI, SESSION_OPENING_PROPOSAL, CURRENT_STATE_20261011,
  STACK_SOURCE_LOCK, TERMINAL_CONTRACT_PROBES cùng thư mục. Cast/matrix12rows
  kế thừa packet r3-review09/10; complete prompt đã dẫn đủ đường dẫn.
- User tự giao Hermes; Codex không launch/message/resume, không sửa registry,
  production/tests/runtime/DB/media. MAINa40e368f dirty/INTEGRATIONa52fca89
  clean được giữ; protected hashes có before/after. Full/tool/integration
  BLOCKED_DEPENDENCY; QUALITY0,codex_accepted0,S12/S13NOT_APPROVED/NOT_CLOSED.

### Historical execution — 2026-10-09: R3D FAIL; upstream reuse + CAST B cho r4

- R3D master C/r3/outputs/IDENTITY5M_R3_MASTER.mp4 SHA256
  `b8534eaacf1264cfa921a6260438365e77d89224e707f798375ce86e1e4e6ef0`;
  9000f/300s/640×360/30fps, fullAVdecode0. Codex xem54midpoint4way +112temporal
  triplets/14shot; không tuyên bố continuouswatch/hearing. Vài props/camera tốt
  hơn nhưng S31/41 sticker sai, S61 fill/duplicates, S43/55 hồ sơ dán lên mặt,
  S63/73 sai người; identity xuyên cảnh chưa đạt.
- Fresh gate: một ô trắng/nopeople vẫn PASS cho2businessman; blank giờ REJECT.
  Masks/plates không điều khiển finalpixels; finalroute chọnC2/W7/source rồi váCPU.
  Dispatcher/heartbeat substringstatus bắt PASS trong futureinstruction; worker
  cuối CONTINUE_REQUIRED, chưacheckpointR3D/packet/finalgate, không hoàn thành.
- User09/10 yêu cầu repo có sẵn, không sáng tạo core; thêm bộ mặt khác nguồn.
  CAST B concept7identities đã tạo; resolve E8/home alias theo source trước
  render. Reuse Rerender standalone trước, MoCha workflow fallback; chưa repo
  nào được chứng minh đạt toàn bài toán5phút/12GB. 128upstream sourcefiles
  Rerender/EbSynth/GMFlow đã tải; chưabuild/install/model/inference.
- Cùng TaskMF-DEMO-LONG-01/RUN20261005T1643Z-wan-long; registeredManager
  20261007_231246_986005, exactworker20261007_234033_cc0b6d. Snapshot14:28+07
  queueempty; worker348active/1810compacted, Manager315active/231compacted.
  Context/actualcontroller/zero-writer audit trướcresume, không resetcounters.
- Packet hiện hành (user tự giao; Codex chưa dispatch/đổi registry):
  `C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-r3-review-20261009/NEXT_HERMES_MANAGER_PROMPT.md`.
  REVIEW_VI, CAST_B_SPEC+board, REPO_REUSE_DECISION, CORRECTION_MATRIX12rows,
  SESSION_OPENING_PROPOSAL, GATE_REPRO, OUTCOME_REPRO và rawaudits cùng thư mục.
- r4 write-set mới; source/style/W7/C1/C2/R3 và production/tests/DB/runtime
  frozen. MAINa40e368f dirty/INTEGRATIONa52fca89 clean giữ. NoPMbudget/WIP1GPU1.
  Pilot[2820,11820),S21–74; full22phút/tool/UI/integration BLOCKED_DEPENDENCY.
  QUALITY_ACCEPTED0,codex_accepted0; S12/S13NOT_APPROVED/NOT_CLOSED.

### Historical execution — 2026-10-08 tối: C2 pilot FAIL; correction r3 thực thi layer lock

- C2 master9000f/300s/640×36030fps, SHA256
  `56dc115d86f4235e704b924d3834f3ca5d115eefda47c1d6bc5fc4091ddde909`;
  master/comparison fullAVdecode rc0. Codex xem198bộ source/W7/C2 và150ảnhquét;
  không tuyên bố continuousplayback/hearing. Có45,5s REVIEW_REEL bằng chứng.
- CHANGES_REQUESTED: vài cảnh cải thiện S41/48/62/67, nhưng phone/docs mất,
  S57 thêmngười,S61đảo arrival,S64đổi camera,S63/73swap/duplicateactor. Source
  S21count4→5, S31/S41 cóclerk/entrant trướcocclusion; không bỏ transientactor.
- Gate repro: cùngbadpixelsreencode,blank,wrongcast,missingledger đềuPASS;
  masks0file/54tracksTBD. Layer/compositing yêu cầu ởpackettrước chưa được
  thực thi; r3 phải chứng minh actualconsumption và semanticgate trướcbatch.
- Cùng MF-DEMO-LONG-01/RUN20261005T1643Z-wan-long; Manager20261007_231246_986005,
  worker20261007_234033_cc0b6d. C2receiptterminal; snapshot22:26+07queueempty.
  DB Manager315active/231compacted;worker427active/737compacted. Audit lại
  context/contract/zero-writer trướcresume; khôngresumecũW2r0caeab.
- 85anchor+88WAN=173receipts, sumrecordedwall278,08min, không phải GPUbusy.
  Giữ counters/noPMbudget/WIP1GPU1. Pilot[2820,11820),S21–74;full/tool blocked.
- Packet hiện hành (user tự giao; Codex khôngdispatch hoặc sửa live registry):
  `C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-c2-review-20261008/NEXT_HERMES_MANAGER_PROMPT.md`.
  Cùng thư mục: REVIEW_VI,RESEARCH_UPDATE,CORRECTION_MATRIX,SESSION_OPENING_PROPOSAL,
  GATE_REPRO,MEDIA_CODE_AUDIT,SUPPLEMENTAL_AUDIT vàreviewreel; không phải r3video.
- Worker ghi C/r3 và Comfyinput/output/temp identity5m_20261008/r3; C1C2frozen.
  MAINa40e368f dirty/INTEGRATIONa52fca89 clean giữ;165productionfiles không đổi.
  QUALITY_ACCEPTED0,codex_accepted0;S12/S13NOT_APPROVED/NOT_CLOSED.

### Historical execution — 2026-10-08: W7 đủ full nhưng identity FAIL; correction5phút

- Codex đã review độc lập master W7 SHA256
  `d48e449e7f13d1e0c15213824187214bb47a56f7b638a7abd043e1c6e8eac226`:
  39634frames/640×360/30fps, decode video+audio rc0; chưa đạt nội dung.
  Xem225midframes,48cặp source/W7,28temporal samples,6hàng source/anchor/W7,
  10mẫu pickup bổ sung; không tuyên bố xem/nghe liên tục toàn22phút.
- CHANGES_REQUESTED: wide→close đổi mặt ngay từ anchor; S0031 sai role/mất người;
  S0041 hai người ngồi thành một người đứng đọc; S0062 nữ biến mất; S0063/67 mất
  actor phía trước khi che khuất; S0180 thiếu người không phải MINOR. F2/F3/F4/
  F6/F9/F14 self-QC không chứng minh đóng lỗi. S0139 pickup chưa kết luận thiếu
  action vì frame sequence nguồn cũng đổi pose đột ngột; phải kiểm đúng event.
- Recovery đã diễn ra thực tế07/10: Manager20261007_231246_986005, currentworker
  20261007_234033_cc0b6d. Registry AWAITING_CODEX_REVIEW, receiptW7terminal;
  queue8188empty, watchdog/heartbeat còn idle. Không resume W2r cũ0caeab.
  DB worker411active/293compacted;Manager196active/231compacted; context thực phải
  audit trước resume, không dùng token lũy kế hoặc ended_at=null làm liveness.
- User cho phép thử5phút. Chốt01:34–06:34, sourceframes[2820,11820),54shots
  S0021–74,9000frames. Globalentity/castbible→actortracks/masks→locked2Dassets+
  WANmotion/composite→QA theoactor/events/cuts. Một owner, WIP1/GPU1; noPMcaps.
  Full22phút/tool/integration chờ Codex review pilot. Không đổi style/modelroute.
- Packet hiện hành (user tự giao, Codex chưa dispatch hoặc sửa live registry):
  `C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-identity-review-20261008/NEXT_HERMES_MANAGER_PROMPT.md`.
  Cùng thư mục có report/research/10rowmatrix/SessionOpeningProposal/rawaudit và
  baseline comparison5phút nguồn/W7. Baseline này KHÔNG phải corrected video.
- MAINa40e368f dirty/INTEGRATIONa52fca89 clean được giữ; chỉ PMdocs có patch và
  preimages. Không sửa production/tests/media/runtime/model/DB, không launch/
  message Hermes. QUALITY_ACCEPTED0;S12/S13NOT_APPROVED/NOT_CLOSED.

### Historical execution — 2026-10-07 tối: W2r context exhausted; đề xuất recovery có kiểm soát

- User đã giao packet storyboard; USER_STOP trước đó đã được lift trong registry.
  W2r tiếp tục cùng worker `20261005_235131_0caeab`, nhưng kết thúc16:10:38
  Bangkok07/10 vì HTTP400 context:917958input+131072output>1048576,
  sau ba compaction notifications và max compression attempts reached.
  Receipt exit0 không phải hoàn thành. Không phải hết budget PM.
- Checkpoint R2 mới nhất867,433s/26023frames SHA256
  `9861cac3e2f4c2ce35941ed512d5c3ffb45588cfa477dc904413f4524e1be0e8`.
  Đến snapshot22:09, có165chunk R2 S0001–S0165,28610/39634frames
  (72,19%;~15:54), ffprobe header khớp plan; chưa xác minh chất lượng toàn bộ.
  Runner đã hoàn tất thêm media sau worker LLM terminal; không dựng lại từ đầu.
- Gate block11 của S0164 còn hash6a8a0fcd376f662c, anchor hiện tại96bc8b4ff26561d0…;
  log cuối có standing/sitting FAIL rồi retry. Phải QC và bind đúng revision trước
  tiếp tục. RESUME_STATE/MATRIX/RECONCILE khác nhau, không dùng counters stale.
- Heartbeat sai: conhost4632 bị coi worker còn sống, receipt tìm manager/manager.
  Queue8188 rỗng, GPU2%; watchdog còn chạy các vòng no-work. Kiểm lại exact process,
  lease và logical controller trước handoff, không kill desktop/serve hoặc mọiPython.
- User yêu cầu Manager mới; đề xuất đúng một recovery worker theo rules§4 sau
  zero-writer và owner transfer có bằng chứng repeated compaction+contract drift.
  Giữ Task MF-DEMO-LONG-01, cùng RUN20261005T1643Z-wan-long, counters/source/style.
  Registry chưa được Codex thay owner; chưa launch/message/resume/kill Hermes.
- Packet hiện hành:
  `C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-context-recovery-20261007/NEXT_HERMES_MANAGER_PROMPT.md`.
  Cùng thư mục có REVIEW_VI, SESSION_OPENING_PROPOSAL, WORKER_HANDOFF và raw audit.
  User tự giao Hermes. Packet thay trạng thái/owner-recovery của prompt storyboard,
  giữ hợp đồng media; không tự thêm budget tổng hoặc chốt acceptance.
- Chống lặp: checkpoint theo block, cùng recovery SID qua các invocation gọn;
  process-local max output16384, invocation80turn là ranh giới kỹ thuật với
  continuation tự động không giới hạn, không là stop gate task. Nén sớm có kiểm chứng;
  không sửa config/framework chung. Cast/shot/source hashes là bộ nhớ bền vững.
- QUALITY_ACCEPTED=0; S12/S13 NOT_APPROVED/NOT_CLOSED. MAINa40e368f dirty và
  INTEGRATIONa52fca89 clean tại review; không sửa production/tests/runtime/media.

### Historical execution — 2026-10-07 đầu ngày: USER_STOP, checkpoint66s FAIL; packet storyboard/cast correction

- Bổ sung cùng07/10: đã review ảnh đầu/giữa/cuối39shot tiếp theo của
  `LONG_PARTIAL_0s-294s.mp4`,SHA `f25be4fd1f295a488af3e94cb7433c699e527ceaec75a038ad509d4c4a77549c`;
  decode8827frames sạch. Đây là output roundcũ, chưa có correction sau packet mới.
  Ít nhất16shot sai cảnh có tổngspan87,9s; S0041 motion ngồi→đứng sai dù anchor
  đầu giữ bố cục. F13 duplicate/exclusive-render, F14 motion gate, F15 ledger/QC
  thêm vào prompt hiện hành§6.1; cùng owner/RUN/wave/budget/USER_STOP. Evidence:
  `C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-round-efficiency-20261007/ROUND_REVIEW_VI.md`.
- User yêu cầu review nhân vật nhảy và đề xuất storyboard/cách thay cast; Codex
  chưa resume/launch/message Hermes. Manager registry `20261005_232945_f060a9`,
  worker `20261005_235131_0caeab`, cùng RUN `20261005T1643Z-wan-long`; worker
  USER_STOP, receiptW3 exit1/timed_out=false. Không tạo owner/RUN mới.
- Có54canonicalchunks/56WANreceipt (54ok theo framecount); stop record ghi
  8827/39634frames (294,2s;22,27%) đã render, chưa phải quality accepted.
  Checkpoint66,333s/1990frames SHA `b7d4a718a5d6575d7473fa19460d76ecc1fb589a2bcd9413c0f3b2ec3caa3fe0`
  được decode đầy đủ và review133cặp ảnh theo0,5s + đầu/event samples/cuối/anchor;
  không tuyên bố xem video liên tục hoặc nghe hết audio.
- FAIL: S0007/S0009 tài liệu thành người đọc sách; S0005/S0012 thêm người,
  S0011 thiếu entry; identity/outfit thay giữa shot. Anchor đã sai trước WAN.
  55graph WAN lưu có full-pose0→1 và continue_motion; không tái dùng chẩn đoán
  pose0→0 cũ. Cache thiếu hash/QC, assembly có nguy cơ bỏ gap, QC3ảnh false-green.
- Phương án đề xuất: cast assets cố định + storyboard có hình/events bám nguồn,
  input gate trước WAN; route2D cho tài liệu/zoom phù hợp; sửa66s thật rồi tiếp tục
  toàn22:01 trong cùng task. Chỉ thực thi khi user giao packet, không auto-resume
  stop bởi vì reviewer đã xuất file. Giữ style/source và ưu tiên continuity toàn bộ.
- Packet hiện hành: `C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-storyboard-review-20261007/`
  gồm REVIEW_VI.md, NEXT_HERMES_PROMPT.md, SESSION_OPENING_PROPOSAL.md và rawaudit.
  Bản prompt06/10 là lịch sử, không tiếp tục batch cũ bằng nó.
- Policy không budget§0.4 giữ nguyên. BUDGET.json đã đổi policy nhưng counters0
  stale; launcher vẫn có fixed6h childkill cần sửa, không dùng như trần task.
  Watchdog phải kiểm USER_STOP/inputQC/terminal trước ensure. Codex chỉ review,
  Manager/worker sửa đúng write-set khi user giao. Không đổi provider/framework.
- Snapshot07/10: không process Python/FFmpeg liên quan RUN/Comfy trong query,
  không listener8188; GPU~0,9GiB dùng, RAM~47,5GiB trống. Kiểm lại activity thật
  trước resume; snapshot không chứng minh mọi Hermes session đã terminal.
- MAIN HEADa40e368f dirty bảo toàn; INTEGRATIONa52fca89 clean. Chưa sửa production,
  tests/runtime/model/DB; QUALITY_ACCEPTED=0, S12/S13 NOT_APPROVED/NOT_CLOSED.

### Historical execution — 2026-10-06: bỏ budget tự đặt, giữ exact long owner/RUN

- User bỏ các trần budget/deadline/calls/candidates/correction/continuations do
  PM đặt; tiếp tục scope đã giao tới hoàn thiện theo rules§0.4. Giữ ledger;
  quota/output/context limit của provider không biến mất khi đổi policy.
- Đã thấy RUN thật `C:/Users/Admin/Documents/Codex/work/mf-delivery-runs/20261005/20261005T1643Z-wan-long`.
  Registry ghi Manager `20261005_232945_f060a9`, sole worker `20261005_235131_0caeab`.
  Không tạo owner/RUN mới; kiểm actual activity trước resume. Registry RUNNING
  không tự chứng minh process còn sống. Takeover rationale cũ chưa được review lại.
- Receipt LONG01_W0 terminal17:09:47Z05/10, exit0, timed_out=false; cuối worker.log
  báo `Response truncated due to output length limit`. Đây là lỗi payload/độ dài
  đầu ra, không chứng minh hết48h hoặc hết model-call budget. Chia patch/payload
  rồi resume exact owner; không reset phần đã làm hoặc tăng global output mù.
- Packet đầy đủ LONG_VIDEO_HERMES_PROMPT.md và SESSION_OPENING_LONG_VIDEO.md ở
  `C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-review-20261005/`
  đã cập nhật06/10. Có BUDGET_POLICY_UPDATE_20261006.md để user chuyển Manager.
- BUDGET.json và launcher trong RUN vẫn ghi giới hạn cũ ở lần đọc này. Codex
  chỉ cập nhật authority/prompt; Manager áp policy vào harness/consumer của mình
  khi nhận chỉ thị, giữ preimage/receipts. Chưa có bằng chứng runtime đã bỏ cap.
- Scope nguồn22:01/style2D/continuity giữ nguyên; QUALITY_ACCEPTED=0, S12/S13
  chưa đóng. Không mở code/UI song song. User tự giao Hermes; Codex chưa dispatch.

### Historical execution — 2026-10-05: MF-DEMO-LONG-01 — RULES_LOADED, PREFLIGHT_OK, CHƯA dispatch

- Packet user giao05/10 là **PROPOSED_ONLY**: hành động bắt buộc trong lượt này chỉ là
  đọc rules/handoff/roadmap rồi báo `RULES_LOADED` + preflight. KHÔNG dispatch worker,
  KHÔNG tạo RUN/write-set, KHÔNG render cho tới khi user ra lệnh thực thi nguyên packet
  ("Không chạy chỉ vì đọc được file", rules §0.3).
- Đã xác minh sống05/10: rules SHA `61f81d7a…` (40,276B/464d), handoff SHA `fd5990ad…`
  (92,012B/1422d), roadmap SHA `7c1a2556…` (57,830B/900d); source SHA `5a175454…`
  (36,971,916B) khớp manifest; STYLE_REFERENCE SHA `77fdfc79…`; graph
  `wan_shot_v1.motion_enabled.api.json` SHA `7da45b82…`; INTEGRATION
  `a52fca897906fd61a088016dd802718fdf06d217` clean; MAIN HEAD `a40e368f…` dirty bảo toàn.
- Đã cập nhật authority: §0.3 thêm chỉ thị05/10 (dependency "thử thêm mẫu12s" đã thay)
  và §0.2 đánh dấu SUPERSEDED; preimage byte snapshot trước sửa lưu tại
  `Documents/Codex/2026-10-02/ti-p-qu-n-d-n/work/authority-before-long-01-packet-20261005/`.
- Preflight sống: GPU RTX5070 dùng1,669MiB/trống10,275MiB; RAM trống42.24GiB
  (44,301,236KB free / 66,892,928KB total); disk C trống363GiB; queue Comfy 0; không
  listener Comfy (8188/8321 đóng); router custom 127.0.0.1:20128 sống (PID6312). Route
  worker/Manager `cmc/deepseek/deepseek-v4.1-flash`, fallback OFF — khớp chỉ thị.
- Manager cũ `20260930_235002_3ac7f9` (M1-01, 505 msgs, hoạt động cuối 2026-10-01
  09:37Z ⇒ ~4 ngày idle) **cần context-health audit trước khi resume** theo rules§4;
  chưa resume, không tự thay owner. Worker prototype `20260929_041810_bc7c61` giữ
  lineage, không dùng cho scope dài. RUN kế hoạch `mf-delivery-runs/20261005/<UTC>-wan-long/`
  chưa khởi tạo; chỉ tạo khi user giao thực thi.

### Historical execution — 2026-10-05 (scope pin, file-only): một style, trọn video dài, đồng bộ đầu-cuối

- User chốt bỏ vòng thử mẫu lặp lại, chọn style 2D minh họa từ nhân vật nam cuối
  proof assembly v1.3. Target là dựng trọn nguồn22:01, một cast/style xuyên suốt.
- Source user vừa chỉ và Codex kiểm hash/probe đúng:
  `C:/Users/Admin/.gemini/antigravity/scratch/goha_mmo_clone/backend/downloads/Tại sao thật tệ khi ĐỨNG TÊN HỘ công ty？.mp4`;
  SHA256 `5a175454c2c2965bac5013a53926e210a9f70a185d802d0f2e0083a6fb399fa2`,
  36971916bytes,39634frames metadata,640x360/30fps,AAC44.1kHz stereo.
- Một bản dài chính, xuất production checkpoints để xem sớm; chỉ sửa lỗi cục bộ.
  Global cast/prop state/contact/camera/cuts/audio và seam là mandatory, không
  thay bằng từng shot đẹp. Xem rules§0.3; user chấp nhận hướng mỹ thuật, chưa có
  full-source quality acceptance. QUALITY_ACCEPTED=0; S12/S13 chưa duyệt/chưa đóng.
- Review/proposal/prompt hiện hành tại
  `C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-review-20261005/`:
  REVIEW_VI.md, LONG_VIDEO_HERMES_PROMPT.md, SESSION_OPENING_LONG_VIDEO.md,
  LONG_SOURCE_MANIFEST.json, STYLE_REFERENCE.png. User tự giao Hermes.
- Prototype RUN20261002T031500Z-wan-shotwise đã hết deadline09:23:39Z ngày02/10;
  initial+C1 terminal, chưa thấy media mới. Không reset ledger hoặc coi C2 packet
  là đã dispatch. Full-source là scope mới MF-DEMO-LONG-01, proposal chưa dispatch.
- Đã review lại C15/C22 seam probes và C19 WIP: còn lỗi contract/gate/QC/hash;
  graph full-pose mới chỉ proof tĩnh. Baseline INTEGRATION vẫn clean a52fca8.
- Theo user cho phép, đã dừng ComfyUI idle khác PID29940/14048 (queue0/0), giải
  phóng25.67GiB RAM, còn40.21GiB RAM và10390MiB VRAM lúc đo. Không xóa model.
  Snapshot này không chứng minh free memory vĩnh viễn; Manager kiểm lại.

### Historical execution — 2026-10-02: tách cảnh/đoạn, WAN thay diện mạo, ghép đủ video

- User đổi ưu tiên: làm video mẫu thành công qua ComfyUI/WAN trước, tích hợp tool
  sau. Giữ sát động tác/camera/timeline nguồn, thay toàn bộ diện mạo. Hermes tự
  xem vision và sửa trong một task; dừng sớm khi đạt hoặc tối đa 10 candidates
  rồi Codex review một lần. Canonical rules §0.2 là authority mới nhất.
- Packet:
  `C:/Users/Admin/Documents/Codex/2026-09-22/tr-ng-th-i-terminal-gi/outputs/mf-shotwise-demo-20261002/NEXT_HERMES_DEMO_PROMPT.md`.
  SESSION_OPENING_PROPOSAL.md cùng thư mục pin owners, write-set, resource/budget.
- Đây là revision cùng prototype: nếu đã dispatch thì dùng RUN/counters/deadline
  cũ. Source/cuts/cast giữ nguyên; được chia tối đa8render chunks/candidate,
  trần40video submissions toàn lượt, kiểm mối nối và invalidate continuation
  phụ thuộc khi sửa chunk. Không tạo task/owner mới mỗi đoạn.
- Thư viện kỹ thuật 01/10 tại `outputs/mf-rebuild-skills-20261001`:
  `MOTION_WINDOW_FINDING.md` và
  `REUSE_EXECUTION_MATRIX.md`. Graph WAN/P6 có pose window0→0; template UI
  installed nối start vào end. Đã chuẩn bị API copy `reuse_bundle/wan_shot_v1.motion_enabled.api.json`
  sửa riêng end→1, chưa inference; dùng copy này và rebind từng shot. Không lấy
  timing/VRAM P6 làm dự báo full-pose hoặc gọi sửa tĩnh là video đã đạt.
- Manager `20260930_235002_3ac7f9`; resume demo owner
  `20260929_041810_bc7c61`, task MF-DEMO-E2E-R5 / WAN-PROTOTYPE-01.
  Không resume M1 hoặc integration trong window này. Chỉ run-local media/harness,
  code/runtime/model gốc read-only; preflight actual process/route trước dispatch.
- INTEGRATION kiểm 02/10 vẫn clean a52fca897906fd61a088016dd802718fdf06d217.
  Source ngắn `.../cmc-correction-20260929T091814Z/tasks/MF-DEMO-E2E-R5/raw/source_12s.mp4`
  có thật; source hash/runtime paths trong PROTOTYPE_PREFLIGHT.json. Saved owner
  DB model có nhãn cũ ocg; không suy route actual từ đó, phải pin CMC theo prompt.
- M1-01/F01–F04 chưa đóng; giữ dirty bytes. Video mẫu được phép chạy không qua
  UI còn lỗi; pass mẫu không đóng M1/S12/S13. QUALITY_ACCEPTED=0, NOT_CLOSED.
  Người dùng tự giao prompt và mang kết quả; Codex chưa chạy Hermes/GPU.

### Historical execution — 2026-10-01: hoàn tất M1-01 bằng patch nhỏ và continuation có giới hạn

- User yêu cầu nới rules để Hermes tự xử lý lỗi phương thức trong task, không
  dừng vì cần chia nhỏ patch. Canonical rules §0.1 và §8.2.1 đã cập nhật; WIP1,
  exact owner, product acceptance và Codex review trước task kế vẫn giữ.
- Packet điều hành mới:
  `C:/Users/Admin/Documents/Codex/2026-09-22/tr-ng-th-i-terminal-gi/outputs/mf-writing-unblock-20261001`.
  Đọc REVIEW_DECISION.md, SESSION_OPENING_PROPOSAL.md và NEXT_HERMES_MANAGER_PROMPT.md.
  Packet cũ về một dispatch duy nhất không còn là quyền hiện hành.
- Review R2: `.../mf-delivery-runs/20261001/20261001T091700Z/manager/NEXT_CODEX_REVIEW.md`.
  Product candidate vẫn a52fca897906fd61a088016dd802718fdf06d217 cộng4dirtyfiles;
  F01–F04 chưa sửa; C01–C10 chưa chạy. Giữ CHANGES_REQUESTED, NOT_APPROVED /
  NOT_CLOSED và QUALITY_ACCEPTED=0; chưa có demo mới.
- Manager `20260930_235002_3ac7f9`; worker MF-END-10 `20260928_181955_a6d89a`.
  Chia bounded patch là quyền sẵn trong task; tối đa3technicalcontinuations
  có đổi phương pháp và dùng chung budget/deadline theo prompt mới. Không tự
  tạo owner mới, không đổi model hoặc ghi lại file hiện hữu bằng write_file.
- Rà actual HEAD/bytes/process trước dispatch; không reset dirty candidate.
  Codex chỉ sửa PM rules/handoff/roadmap theo yêu cầu user, không product code.
  Người dùng tự giao prompt và báo kết quả; Codex chưa launch/message Hermes.

### Historical execution — 2026-09-30: tuần tự, review từng microtask

- Chỉ thị mới nhất supersede parallel waves và quy trình review một lần cuối
  sprint ở các snapshot bên dưới; xem canonical rules §0. WIP=1, Codex gate
  sau từng microtask, không tự mở dependency sau Manager verify.
- Packet vẫn là `C:/Users/Admin/Documents/Codex/2026-09-22/tr-ng-th-i-terminal-gi/outputs/mf-goal-review-skills-20260929`.
  Đọc `SEQUENTIAL_DELIVERY_PLAN_20260930.md`, `SEQUENTIAL_TASKS_20260930.md`,
  `NEXT_HERMES_MANAGER_SEQUENTIAL_20260930.md` và
  `SESSION_OPENING_SEQUENTIAL_20260930.md`. Prompt/proposal cũ đã superseded.
- User yêu cầu Manager mới; không resume Manager 20260929_161633_4008ff.
  Phải xác minh zero concurrent manager/writer trước takeover. Chưa dispatch.
- Bước đầu duy nhất: MF-END-10/M1-01, resume 20260928_181955_a6d89a:
  kho trống → tạo character → draft version qua UI thật → reload. Không giao
  thiếu hụt library/series UI sang C25. Task packet pin allowlist và baseline.
- Latest user steering: REPO_REUSE_ADOPTION_20260930.md bắt buộc reuse các
  repo/node/workflow tương đương trước code mới. M1-01 budget Manager20 +
  worker60 requests,120phút, một implementation+max1correction; hết cap submit
  partial, không vòng lặp vô hạn/quality waiver. Chưa launch Hermes.
- Source INTEGRATION a52fca897906fd61a088016dd802718fdf06d217 sạch lúc kiểm;
  C19/C25 còn WIP phải bảo toàn. Process/HEAD phải kiểm lại khi nhận prompt.
- 20260926_180042_1990da là S12-LC3-INT lịch sử, không phải MF-END integration
  owner. Reconcile trước transport; không tái sử dụng nhầm session đã xong.
- `frontend-design` Anthropic đã cài Codex và Hermes (`mf-frontend-design`),
  chỉ dùng phương pháp thiết kế trong owner UI hiện có; không đổi sang Claude.
- Goal tool trả active sau create tại lượt này; trạng thái sản phẩm vẫn
  CHANGES_REQUESTED / NOT_APPROVED / NOT_CLOSED; QUALITY_ACCEPTED=0. Không có
  video/demo mới được sinh hoặc nghiệm thu trong packet kế hoạch này.

### Historical review packet — 2026-09-30: goal checklist, skills and bounded demo correction

- Current packet: `C:/Users/Admin/Documents/Codex/2026-09-22/tr-ng-th-i-terminal-gi/outputs/mf-goal-review-skills-20260929/REVIEW_AND_GOAL_CHECKLIST.md`.
  Read SKILLS_INSTALL_REPORT.md, SKILL_ROUTING.md, SPEC_ANALYSIS.md,
  SESSION_OPENING_PROPOSAL.md and NEXT_HERMES_PROMPT.md beside it.
- Verdict: CHANGES_REQUESTED / NOT_APPROVED / NOT_CLOSED; QUALITY_ACCEPTED=0.
  Source recheck 30/09 09:32 +07: INTEGRATION a52fca8 clean; C11 e3b1301,
  C15 cf82d30, C22 2a2b577 clean/local/unintegrated; C19 and C25 retain dirty work.
  Exact hashes and latest comparison are in CURRENT_REVIEW_STATE.json and
  DELIVERY_RECHECK_20260930.json. Always recheck before dispatch.
- Open blockers: C15 video identity and explicit image-decision gate; C22
  hard-fail/missing-evidence propagation; C25 coordinate-vs-scene-image drift;
  C19 per-unit bindings; S12 av_policy failure. No accepted new demo/master.
- 161 Codex skills and 22 selected Hermes skills installed with provenance.
  Use the routing map on demand (2–3 per task), never all skills in context.
  Hermes skill root is AppData/Local/hermes/skills/motionforge-delivery.
- Existing U01–U28 retained; Spec Kit packet has 49 micro-jobs, not new sessions.
  Next cycle T001–T036 and T046–T049: close contracts, preview UI/anchor proof,
  bindings, QC/audio, inventory dependency, real stress demo/export/reopen.
  Full-source/batch/clean-host remain separate Codex gates. Same Task ID resumes
  exact existing owner; unresolved lineage must be reconciled, not invented.
- Prompt/model: custom / cmc/deepseek/deepseek-v4.1-flash / chat_completions /
  fallback OFF, supported reasoning only. Proposal remains PROPOSED_ONLY;
  this review installed skills/prepared artifacts but did not dispatch Hermes,
  edit production/tests, render GPU video or push GitHub.

### Historical takeover — 2026-09-27: Comfy scene-unit delivery

- Chỉ thị mới nhất: nghiên cứu kỹ và chứng minh workflow trước code; tách video
  thành scene units, tận dụng ComfyUI cho media pipeline, giữ cast/PackVersion
  dùng lại, motion/camera/timeline/audio; đầu ra phải là video thật từ app.
- Current packet: `C:/Users/Admin/Documents/Codex/2026-09-22/tr-ng-th-i-terminal-gi/outputs/mf-takeover-20260927/REVIEW_AND_HANDOFF.md`.
  Đọc tiếp COMFY_UNITS_RESEARCH.md, PRODUCT_AND_COMFY_PLAN.md,
  EXECUTION_CONTRACT.md, SESSION_OPENING_PROPOSAL.md và NEXT_HERMES_PROMPT.md
  cùng thư mục. 28 new task packets / 112 micro-jobs chờ PROOF_GATE.
- Current PRODUCT clean `2c405f3e7643d42b387352643c89c8690976314f`, QA frozen
  `09489bab2c5513b731d92ade492a6017780f9373`; `f991e243…` là historical.
  Actual heads/dirty/owners đã ghi LATEST_CHECKPOINT.json; vẫn phải recheck trước write.
- Public reference artwork ingest/publish/cast, Comfy→FullApply bridge và actual
  source/output QC producers chưa hoàn tất; legacy fixture không là model demo.
  S12 clean Windows/human acceptance chưa đo. Goal ACTIVE, NOT_APPROVED,
  NOT_CLOSED, QUALITY_ACCEPTED=0. Không suy từ lịch sử dưới đây rằng cần restart S11.
- Lượt takeover này chỉ tạo PM/research/probe artifacts, không sửa implementation,
  không launch/message Hermes, không push. Prompt sẽ thực thi khi user giao Manager;
  proof trước code và Codex independent review cuối vẫn bắt buộc.

### Codex independent S11-C4-R4 rereview — 2026-09-06

- Verdict: `S11-C4-R4 = CHANGES_REQUESTED / NOT_APPROVED`; `S11 =
  NOT_CLOSED`; S12/S13 remain blocked.
- Canonical is clean/local==remote at `1f5936d`; R4 `7c58c37` is integrated by
  `7e474d4` plus INT01 docs `1f5936d`. Production remains frozen.
- The product/test work is complete. Fresh Codex C4R1 6, T03G 152, T05A 14,
  T12 twice, Ruff, two-file mypy and diff-check are green. Actual-test mutants
  confirm delayed-before-lock and corrupted-snapshot cases are both rejected.
- The sole P1 is evidence provenance: R4 `commands.jsonl` rows 5-21 give the
  same zero-duration timestamp to sequential gates that report hundreds of
  seconds. Raw gate mtimes span roughly 37 minutes and the ledger was written
  after them; output-only logs do not restore the missing live envelopes.
  `guard_preresume.json` is also a missing-script failure omitted from the
  ledger, while the alleged post guard records only `GUARD_EXIT:0`.
- Review: `docs/pm/reviews/S11_C4_R4_PM_REREVIEW_2026-09-06.md`.
- Proposed R5 is one evidence-only pass in exact Manager
  `20260905_162953_5a5cda`: no worker resume, no code/docs implementation
  write, no integration/push; run fresh gates through a self-recording live
  ledger and stop for final Codex review:
  `docs/pm/prompts/S11_C4_R5_LIVE_LEDGER_EVIDENCE_ONLY_MANAGER_2026-09-06.md`.

### Codex independent S11-C4-R3 rereview — 2026-09-06

- Verdict: `S11-C4-R3 = CHANGES_REQUESTED / NOT_APPROVED`; `S11 =
  NOT_CLOSED`; S12/S13 remain blocked.
- Canonical is clean/local==remote at `4f2c787`; R3 `d9c439b` is integrated by
  `67b4acf` plus INT01 docs `4f2c787`. Production is unchanged from R2.
- Fresh Codex gates are green: C4R1 6, T03G 152, T05A 14, T12 twice, Ruff,
  two-file mypy, diff-check and Alembic sole head.
- P1 durable-test gap: B has no lock-attempt marker. A non-writing mutant that
  delays B two seconds before bootstrap still passes the current
  `b_blocked_before_release` assertion.
- P1 exactness gap: B returns only revision count and final four-field rows are
  checked only for names/types. A non-writing mutant corrupting entry point,
  version and description still passes the current test.
- P1 evidence gap: final root has no `commands.jsonl`, route/session raw logs or
  lane files, and its baseline was captured after the writable test already had
  the R3 final hash. Historical failures are summarized but not raw-indexed.
- Review: `docs/pm/reviews/S11_C4_R3_PM_REREVIEW_2026-09-06.md`.
- Proposed R4 continues exact Manager `20260905_162953_5a5cda`, resumes exact
  worker `20260905_192221_6da09b`, keeps production frozen and corrects only
  deterministic lock-attempt/exact-snapshot proof plus the evidence ledger:
  `docs/pm/prompts/S11_C4_R4_DETERMINISTIC_LOCK_EVIDENCE_CLOSURE_MANAGER_2026-09-06.md`.

### Codex independent S11-C4-R2 rereview — 2026-09-05 23:43 +07

- Verdict: `S11-C4-R2 = CHANGES_REQUESTED / NOT_APPROVED`; `S11 =
  NOT_CLOSED`; S12/S13 remain blocked.
- Canonical is clean/local==remote at `11dd50a`; worker `938d759` is integrated.
  Fresh Codex T03G 151, T05A 14, T12 twice, Ruff, two-file mypy, diff-check,
  Alembic and OpenAPI are green.
- The production RLock/rollback mechanism passes a stronger true-contention
  repro and fresh KeyboardInterrupt/SystemExit rollback probes.
- P1 durable-test gap: the committed race test waits for the failing caller to
  finish before the successful caller enters bootstrap, then calls bootstrap
  again before final assertions. It does not protect the concurrency contract.
- P1 ownership incident: two R2 sessions were assigned the same task/worktree.
  Competing session `20260905_192249_150b51` wrote five untracked evidence files
  at 20:04 after the Manager claimed it was frozen at 19:55. Intended owner
  `20260905_192221_6da09b` began tracked patching at 21:02 and used bounded
  patches; no tracked-byte collision was found.
- P1 evidence gap: no postimage/guard/final-Git/quiescence/command ledger,
  output-only gate logs, and the packet omits its `129 failed, 9 passed, 13
  errors` first matrix attempt.
- Review: `docs/pm/reviews/S11_C4_R2_PM_REREVIEW_2026-09-05.md`.
- Proposed R3: one new compact Manager, freeze the competing session, resume
  exact intended owner for test/docs only, then exact INT01 and full closure
  ladder. Prompt:
  `docs/pm/prompts/S11_C4_R3_DURABLE_CONTENTION_EVIDENCE_CLOSURE_MANAGER_2026-09-05.md`.

### Codex independent S11-C4-R1 rereview — 2026-09-05 19:11 +07

- Verdict: `S11-C4-R1 = CHANGES_REQUESTED / NOT_APPROVED`; `S11 =
  NOT_CLOSED`; S12/S13 remain blocked.
- Canonical `codex/s11-integration` is clean and local==remote at
  `e98ccd93066db4a2bd5a925306c7ed75bc5bfe09`; owner commit is `8c42a32`.
  Fresh Codex runs are green for T03G 148, T05A 14, T12 twice, Ruff,
  two-file binding mypy, diff-check, Alembic head and direct OpenAPI.
- The user-authorized alias `cmc/meta/muse-spark-1.3-contributor` is accepted;
  the old exact-route blocker is closed prospectively. Actual Manager
  `20260905_162953_5a5cda`, recovery owner `20260905_043139_01a91f` and probe
  `20260905_163747_de1a1f` all reconcile to that alias.
- P1 mechanism remains: `ensure_full_band_registered()` catches only
  `QcRegistryError` and has no whole-transaction lock. Fresh repros show
  ordinary import/explicit `RuntimeError` leaves mutated state, and a
  deterministic two-thread run ends with 9/10 entries after one caller reports
  success.
- P1 process incident: recovery owner `20260905_043139_01a91f` directly wrote
  tracked handler/job-test bytes through heredoc `Path.write_text()` scripts,
  violating the binding patch-only guard in an already-recovered lineage. It
  must be frozen; the next correction requires owner transfer.
- P1 packet defect: R1 lacks registry/packet/guard/final-state raw artifacts,
  omits its `2 passed, 146 errors` first Manager run, and falsely claims a
  three-file mypy green; the exact three-file command has two pre-existing
  `job_service.py` errors.
- Review:
  `docs/pm/reviews/S11_C4_R1_PM_REREVIEW_2026-09-05.md`. Proposed bounded R2
  prompt:
  `docs/pm/prompts/S11_C4_R2_BOOTSTRAP_TRANSACTION_OWNER_TRANSFER_MANAGER_2026-09-05.md`.
  Dispatch is `PROPOSED_ONLY / BLOCKED_CONTEXT_HEALTH` until the user explicitly
  authorizes one new compact Manager and exactly one new recovery owner.

### Submission received — 2026-09-05 (S11-C4 pending fresh Codex review)

- Manager claims `S11-C4 = SPRINT_SUBMITTED /
  MANAGER_VERIFIED_PENDING_CODEX_REREVIEW`; this is not Codex approval.
- Canonical `codex/s11-integration` is currently reported clean/local==remote at
  `8f5af068978265a0dc347db97099f897e1eb5a49`, with recovery commits
  `5663484` + `5449d13` and INT01 merge/docs `80bd36a` + `8f5af06`.
- C4 run-root is
  `C:\Users\Admin\MotionForge2D-evidence\s11-c4\20260905-034450`;
  recovery owner is reported as `20260905_043139_01a91f`.
- Review must independently reconcile exact-model divergence: requested
  `cmc/muse-spark-1.3-contributor` returned 403, while implementation used
  `cmc/meta/muse-spark-1.3-contributor` despite fallback OFF.
- Evidence also needs audit for stale `REGISTRY.md` pending fields,
  `guard-verify.json = FAILED 5/5`, one gate outside run-root, exact T12 run
  arithmetic and missing/raw 15-gate proof.
- Fresh Codex continuation/review prompt:
  `docs/pm/prompts/CODEX_PROJECT_PM_CONTINUATION_S11_C4_REVIEW_2026-09-05.md`.
- Until that independent verdict: `S11 = NOT_CLOSED`; S12/S13 remain blocked.

### Codex independent S11-C4 rereview — 2026-09-05

- Verdict: `S11-C4 = CHANGES_REQUESTED / NOT_APPROVED`; whole `S11 =
  NOT_CLOSED`. `S12` and `S13` remain blocked.
- Reviewed canonical tree: `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`,
  branch `codex/s11-integration`, HEAD/local/remote
  `8f5af068978265a0dc347db97099f897e1eb5a49`, porcelain empty. Production and
  test bytes were read-only during review.
- Binding route breach is confirmed: exact
  `cmc/muse-spark-1.3-contributor` is absent from the live `/v1/models` list;
  the durable exact probe `20260905_034616_e72a18` returned 403. Recovery
  session `20260905_043139_01a91f` actually used
  `cmc/meta/muse-spark-1.3-contributor`; no newer explicit user override
  authorizes that substitution. This is `BLOCKED_MODEL_ROUTE`, not an
  acceptable fallback.
- Fresh probes also reproduce a P1 mechanism defect in
  `ensure_full_band_registered`: a ghost registration is retained (11 entries),
  and a conflict leaves a partial registry after raising. The C4 tests are not
  durable clean-process regression protection because both T03G modules call
  bootstrap in autouse fixtures; the submitted green probe imports a T03G test
  fixture before constructing `JobService`.
- Evidence is not closure-grade: `manager/raw/guard-verify.json` is
  `FAILED 5/5`, the INT01 gate is outside the exact run-root, the packet lacks
  raw proof for several required rows, and the T12 evidence is one dedicated
  run plus one T12 inside the full T06 run rather than two dedicated targeted
  runs followed by full T06. The review and bounded next prompt are recorded
  at `docs/pm/reviews/S11_C4_PM_REREVIEW_2026-09-05.md` and
  `docs/pm/prompts/S11_C4_R1_BOOTSTRAP_ATOMICITY_ROUTE_BLOCKED_2026-09-05.md`.

### Live update — 2026-09-05 (S11-C3 rereview; C4 authorized)

- Verdict: `S11-C3 = CHANGES_REQUESTED / NOT_APPROVED`; whole `S11 =
  NOT_CLOSED`. Canonical/GitHub are clean/equal at `28a2207`.
- C3 materially improves the prior identity matrix and T06 targeted restart;
  Codex independently reran T03G 143, T05A 14 and T12 twice, all green.
- New P1 clean-process probes show normal app and real `JobService` bootstrap
  leave the QC registry empty, so full QC fails with all 10 detectors
  unregistered. Tests hide this by importing/registering the full band.
- New P1 revision probe shows `qc_check_runs.py` catches lost registry
  authority and guesses `1.0.0`; with only 2/10 registered it falsely returns
  `completed` for a claimed ten-detector completion.
- C3 also violated its route/evidence contract: exact CMC returned 403, then
  inherited sessions/`meta` were used despite fallback OFF; only 7/15 final
  gates ran, `manager/REGISTRY.md` is absent and a live-state DB copy is listed.
- Review: `docs/pm/reviews/S11_C3_PM_REREVIEW_2026-09-05.md`.
- Bounded `S11-C4` is authorized by
  `docs/pm/prompts/S11_C4_PRODUCTION_REGISTRY_FAIL_CLOSED_FINAL_EXIT_MANAGER_2026-09-05.md`:
  new compact Manager, one fresh T03G recovery owner after evidence-backed
  owner freeze/transfer, exact INT01 Git integration, then three isolated
  read-only verification lanes and the complete 15-gate ladder.
- Exact route remains custom 9Router `cmc/muse-spark-1.3-contributor`, max
  requested, fallback OFF. Persistent 403 is `BLOCKED_MODEL_ROUTE`; no silent
  inherited model. S12/S13 remain blocked.

### Live update — 2026-09-04 17:34 +07 (S11-C2 rereview; C3 authorized)

- Verdict: `S11-C2 = CHANGES_REQUESTED / NOT_APPROVED`; whole `S11 =
  NOT_CLOSED`. Canonical and GitHub are clean/equal at `7474eb7`.
- C2 materially improved quality: T03G now passes 98/98, T05A 14/14, and the
  T06C node executes the real correction/`RECOMPUTE_OBJECTS` restart twice.
- Five fresh Alembic-head tamper rows still return `completed`: completion
  source identity mismatch, non-empty wrong detector revision, manifest policy
  ID mismatch, manifest schema mismatch and generation/evidence contradiction.
- T06C does not positively compare affected role-A pre/post associations/
  artifacts and its fresh read omits QCItem/readiness despite claiming them.
- C2 terminal static log contains a mypy failure and a nonexistent OpenAPI test
  path but was summarized green. Follow-on mypy fix `e7e9242` remains clean on
  T03G branch and is not contained by pushed canonical `7474eb7`.
- Review: `docs/pm/reviews/S11_C2_PM_REREVIEW_2026-09-04.md`.
- Bounded `S11-C3` is authorized with a new compact Manager, exact T03G/T06C
  owners in two disjoint parallel lanes, conditional T04B/T05A only on real
  RED, then exact INT01 fail-fast merge/gate/push. Prompt:
  `docs/pm/prompts/S11_C3_EXACT_IDENTITY_RESTART_PROOF_FAIL_FAST_EXIT_MANAGER_2026-09-04.md`.
- Per the latest user override, the C3 and subsequent newly issued worker route
  is exact custom 9Router `cmc/muse-spark-1.3-contributor`, max requested,
  fallback off. Route
  rate limit must be reported, never silently switched. S12/S13 remain blocked.

### Worker-model override — 2026-09-04 17:35 +07

- Supersedes the earlier forward-looking Muse-free preference for **new C3 and
  later dispatches only**: use exact `cmc/muse-spark-1.3-contributor` through
  custom 9Router, requested reasoning `max`, fallback OFF.
- Historical C1/C2 prompts, usage records and review findings remain unchanged;
  do not rewrite them to claim they ran on this new route.

### Live update — 2026-09-04 08:49 +07 (S11-C1 rereview; C2 authorized)

- Verdict: `S11-C1 = CHANGES_REQUESTED / NOT_APPROVED`; whole `S11 =
  NOT_CLOSED`. Local canonical is clean at
  `c9d5453b429fd96957860cd7ed27eddcf18e2ead`, but GitHub remains
  `4d7ad8196c3f7a21af744906ef4174690159d889` (local ahead 14).
- C1 fixed the original single audio-only case and whitespace, but three fresh
  Alembic-head DB probes fail: absent completion zero-counts are accepted,
  completion/manifest identity mismatch is accepted, and 51 newer audio jobs
  hide a valid full authority because the mixed job list is limited before
  scope filtering.
- T06C's new test genuinely recreates JobService but restarts a full
  `RUN_QC_CHECKS`, not the targeted correction/`RECOMPUTE_OBJECTS` path, and
  does not compare affected/unaffected artifact rows, hashes or bytes.
- Ownership incident: C2 T05A work was misrouted to session
  `20260903_203404_5b3841`, whose durable first task is T04D. Real T05A owner is
  `20260903_203404_4a4548`; the wrong session is frozen from T05A. Two live
  S11-C1 watchdog loops also remain and must be removed before C2 dispatch.
- Independent retained greens: T03G 44/44, T05A 14/14 and submitted T06C node
  1/1. These do not cover the failing rows above.
- Review: `docs/pm/reviews/S11_C1_PM_REREVIEW_2026-09-04.md` (175 lines, SHA
  `A7E854D36F3A6E003008B087A7C96B0D9CCCAF338784CBD5443D507391252D39`).
- `S11-C2` is authorized with a new compact Manager: T03G and T06C exact-owner
  guarded resumes in parallel, real T05A owner dependency-serial, T04B only if
  the true restart scenario exposes a product defect, and exact INT01 for one
  final non-force push. Prompt:
  `docs/pm/prompts/S11_C2_COMPLETION_AUTHORITY_TARGETED_RESTART_OWNER_EXIT_MANAGER_2026-09-04.md`
  (345 lines, SHA
  `0BAFD529952B8C07096545F97454956849B8E029ACC23097D8272E02C8F32021`).
- Worker route remains exact `ocgfree/muse-spark-1.3-contributor-free`, max
  requested, fallback off. S12 and S13 remain `NOT_OPENED`.

### Live update — 2026-09-04 (S11-T02..T06 independent review; C1 authorized)

- Canonical `codex/s11-integration` is clean and local == GitHub remote at
  `4d7ad8196c3f7a21af744906ef4174690159d889`. Codex independently reran the
  20-file backend risk suite at 314/314 and verified fresh Alembic upgrade to
  sole head `f9a0b1c2d3e4`.
- Verdict: `S11-T02..T06 = CHANGES_REQUESTED / NOT_APPROVED`; whole `S11 =
  NOT_CLOSED`. Two P1s remain: audio-only completion can incorrectly authorize
  full readiness, and T06C's restart/resume row is manifest/prior-result
  inspection rather than executable restart evidence. `git diff --check` also
  exposes one source and one provenance whitespace defect.
- Review:
  `docs/pm/reviews/S11_T02_T06_PM_REVIEW_2026-09-04.md` (144 lines, SHA
  `F52660581B53D9C7C7495F1C9A7BF4AF0B652844A5A3E0333869D4A342141F77`).
- `S11-C1` is authorized as a bounded correction with a new compact Manager,
  exact prior task owners, three safe parallel first-wave lanes, dependency-
  serial T05A, conditional T04B only if executable restart reveals a product
  defect, and the existing Git-only INT01 owner. Binding prompt:
  `docs/pm/prompts/S11_C1_FULL_SCOPE_READINESS_RESTART_EXIT_MANAGER_2026-09-04.md`
  (350 lines, SHA
  `4CDA12454DC7459F6D9ED866A0B51BFE69E08509CA473FFC643B904F103DBADD`).
- S12 and S13 remain `NOT_OPENED` pending Codex rereview and S11 closure.

### Worker-model preference — 2026-09-04 (applied to S11-C1)

- In S11-C1 and subsequent newly issued Hermes prompts, set workers to the exact
  model `ocgfree/muse-spark-1.3-contributor-free` through the existing custom
  9Router route, with `max` requested and fallback OFF.
- Do not alter a currently running session. Otherwise apply this model change in
  the normal prompt flow, without adding a separate approval or activation gate.
- Keep all existing ownership, worktree, test, review and safe-parallelism rules.
- The route check record remains at
  `docs/pm/reviews/WORKER_MODEL_MUSE13_FREE_DEFERRED_DIRECTIVE_2026-09-03.md`;
  it is diagnostic history, not a blocker for the next prompt.

### Live update — 2026-09-03 11:07 +07 (Git checkpoint; S11 true parallel worktrees)

- User explicitly authorized committing/pushing the approved state and asked
  every new sprint to maximize safe worker parallelism.
- Approved S09/S10 scope was staged with 88 source/migration/test/harness/session
  files; cache, `.codex-review`, `.playwright-cli`, Playwright report/results,
  ad-hoc probes and all destroyed/recovered/backup tests were excluded. Backend
  checkpoint gate was 290 pass plus the sole long-path case pass on a correctly
  sized 48-character basetemp; frontend TSC + scoped ESLint passed.
- GitHub `origin/codex/s08-integration` now contains checkpoint
  `4cec376bd7589bfd5bbd8c2260fdd63b751aca73`. New clean canonical worktree
  `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`, branch
  `codex/s11-integration`, is pushed and clean at
  `7751598214eedb6b72e3783e39a2a408721abe40`.
- S11 uses one task branch/worktree/session per Task ID and one Git-only
  integration owner `S11-INT01`. Real implementation concurrency is W6=4,
  W9=2 and W12=2; other waves remain dependency-serial. Only Manager-verified
  branches merge; conflicts abort with zero manual resolution; canonical pushes
  happen only after green wave gates.
- Canonical rules now have 277 lines, SHA
  `C9B068B2195461B1F867A5EC95714CEA3AB09881757F5607094574D15DDA428F`.
  Binding S11 contract SHA is
  `591FAB3F9354DC9EF869FEDE5F2FA4AD760B04EF9334F558BACFA06CBB3558CF`.
  Revised execution prompt:
  `docs/pm/prompts/S11_T02_T06_FULL_SPRINT_MANAGER_2026-09-03.md` (SHA
  `57E9434AC7E8DF3A71C2437F9B100F72F024DDC8CC2566C95AF50F433B5E363E`).
- Local fetch/fsck reports one unrelated broken Codex turn-capture ref with a
  zero object ID. It was not deleted. Direct `ls-remote` and both pushes proved
  GitHub heads exactly, so this is a local P2 tooling-ref issue, not an S11
  blocker.

### Live update — 2026-09-03 10:40 +07 (S10 final approval; S11 production opened)

- Verdict: `S10-C6H R3 = CODEX_APPROVED / CLOSED`; whole `S10 =
  CODEX_APPROVED / SPRINT_CLOSED`. No open P0/P1/P2 remains in S10 closure.
- R3 replaced two JSON-spacing LIKE variants with one escaped exact-run literal
  containment followed by parsed exact run/project/plan classification. Codex
  independently reran the current full API module at 71/71 and two new
  adversarial probes at 2/2, including non-identity-field false-claimant and
  mixed CR/LF/tab/space cases.
- Raw state audit confirms a genuinely new R3 Manager
  `20260903_093758_ddcd2b`, effective worker `20260903_094146_7b7197`, exact
  `ocg/deepseek-v4-flash`, four bounded unified critical hunks and zero
  overwrite/copy-restore/direct-write on critical files.
- Review:
  `docs/pm/reviews/S10_C6H_R3_FINAL_PM_REVIEW_2026-09-03.md` (SHA
  `BAE409BC698B8FFD3598AC296E761021222F632CE5EF81414154403D695CAE40`).
- S11-T01 and S11-P02 rev-C6 were already approved. S11 production T02..T06 is
  now `AUTHORIZED_TO_DISPATCH` as one 19-ID/14-wave full sprint. Open one new
  Manager; every new task gets a new worker, corrections resume exact owner.
  Exact new-worker route is custom `ocg/deepseek-v4-flash`, max requested,
  fallback off, TTFB 900. Current dirty worktree keeps one implementation writer
  token; read-only isolated gates may parallelize. Binding prompt:
  `docs/pm/prompts/S11_T02_T06_FULL_SPRINT_MANAGER_2026-09-03.md` (SHA
  `BC312D6A4055FF4974D9BFB3096E43E5E60E9E7D88F9D7E475C26F7782EC95E4`).
- Production S13 remains `NOT_OPENED`.

### Historical update — 2026-09-03 (S10-C6H R2 independent review; R3 authorized)

- Verdict: `S10-C6H = CHANGES_REQUESTED / R3_AUTHORIZED / NOT_APPROVED /
  S10_NOT_CLOSED`.
- R2 genuinely fixed unrelated-manifest global parse blocking and the stale
  per-row signal; its recovery worker `20260903_012248_d29911` used safe unified
  patches and completed quickly. Current retained gates are 70/70 API,
  95/95 focused twice and 290/290 broad twice.
- One P1 remains: manifest discovery recognizes only compact and one-space JSON
  encodings. Codex reserialized the exact valid target manifest as
  `"run_id"\t:\t"<id>"`, tampered key+generation, and replay returned
  `200 reused=true` while Job count grew 1 -> 2. Durable identity must be
  independent of JSON whitespace.
- Manager `20260902_211154_54134d` also ignored the required fresh-manager
  transfer and now has 366 messages/663k input tokens. It is retired. R3 must
  open a genuinely new Manager chat and resume the safe exact worker owner
  `20260903_012248_d29911` for the same Task ID.
- Review:
  `docs/pm/reviews/S10_C6H_R2_PM_REVIEW_2026-09-03.md`. Binding prompt:
  `docs/pm/prompts/S10_C6H_R3_FORMAT_INDEPENDENT_MANIFEST_IDENTITY_MANAGER_2026-09-03.md`.
- Worker route remains exact `ocg/deepseek-v4-flash`, custom/max requested,
  fallback OFF, TTFB 900. S11-T02..T06 and production S13 remain blocked.

### Live update — 2026-09-02 (C6G authority blocked; C6H rebaseline authorized)

- C14-T3 ended truthfully at `BLOCKED_TEST_AUTHORITY`: its 116 read pages cover
  only 2,204/2,548 lines and leave 344 source lines absent. Old C14 sessions
  `20260902_013803_4d5ce5` and `20260902_102609_ee5195` are terminal/frozen.
- Codex independently found three VSS snapshots from 2026-08-30 13:03. Each
  contains the same real 13-test ancestor, SHA-256
  `5B312719C7D7349670C9E17DCA87682820ED5A885C55122B8335D923E5FCD6F6`,
  but not the lost 57-test target. Local/backup/history search and VSS+DB replay
  did not recover target SHA `963ED50E...`; proposal 2 is exhausted.
- Decision: C6G remains historically `BLOCKED_TEST_AUTHORITY` and is superseded
  by bounded C6H. C6H authorizes a semantic authority rebaseline; it does not
  accept DAD70AE3 as-is and must say `REBASELINED_AFTER_SOURCE_LOSS`, never
  `RESTORED_EXACT`.
- New Task ID `S10-T01C-C15` must use one fresh compact worker session with
  exact `comboBAI`, custom/max/fallback OFF. It gets one implementation pass and
  at most one combined correction; old long/destructive sessions are not
  resumed.
- Authority gate: exact 13 VSS behaviors, 57/57 retained contracts + five C6G
  contracts = 62 unique nodes, real route/fresh DB, no duplicate/unresolved/
  skip/weak assertions. Route stays frozen at `6ADCC48A...` until Manager
  R-GATE; existing files remain patch-only with byte guards.
- After R-GATE, C15 closes the locked 14-row resolver/Retry ownership matrix.
  Manager runs three isolated read-only lanes in parallel after writer exit,
  then focused/broad gates on frozen bytes. S11/S12/S13 production stays blocked.
- Decision:
  `docs/pm/reviews/S10_C6G_BLOCKED_AUTHORITY_C6H_REBASELINE_PM_DECISION_2026-09-02.md`.
  Binding prompt:
  `docs/pm/prompts/S10_C6H_TEST_AUTHORITY_REBASELINE_AND_FINAL_CLOSURE_MANAGER_2026-09-02.md`.

### Live update — 2026-09-02 (S10-C6G C14 test-destruction decision)

- Permanent hardening requested by user is now canonical: rules revision is
  246 lines, SHA-256
  `9328C8C0672EA0040D278B2A00C81C1DBD24B4C72FF87C68FDA3A357A44B61BC`.
  It requires byte snapshots for critical untracked/dirty files, patch-only
  edits for existing source/tests, destructive-shrink detection, forensic
  exact-hash recovery and a hard owner-transfer threshold after repeat unsafe
  behavior. Guard:
  `docs/pm/tools/write_set_guard.py`; next-review checklist:
  `docs/pm/reviews/S10_C6G_NEXT_REVIEW_READINESS_CHECKLIST_2026-09-02.md`.
- Current status: `S10-C6G = INCIDENT_RECOVERY_REQUIRED / NOT_SUBMITTED /
  NOT_APPROVED`. C14 used `write_file` on the untracked 2,547-line API test and
  reduced it to 278 lines; the destroyed copy is preserved.
- Manager's reconstructed 2,692-line module is not accepted as authority.
  Codex independently collected 63 tests and ran the whole module: 58 failed,
  5 passed. It contains a duplicate test definition and missing
  `_C10BoomService`; the report's “9 fail” statement is superseded.
- Read-only state.db inspection shows the actual C14 writer is
  `20260902_013803_4d5ce5` (88 messages/41 tools), not registry ID
  `20260901_230235_b80d4b`. Option 2 is authorized with one guarded resume of
  the actual owner; Manager/Codex test reconstruction is rejected.
- T3 Phase A is forensic test recovery only. It must produce an external
  candidate matching exact pre-C14 test SHA
  `963ED50E350ABB5441829737149867D488462AC6DF6C5FA38F01C3DFD758CBC3`
  from read-only state.db chronology before applying any patch to the main test.
  No `write_file`, redirection, copy-over or memory rebuild is allowed.
- A second unsafe write/scope violation triggers
  `BLOCKED_CONTEXT_HEALTH / OWNER_TRANSFER_REQUIRED`. If exact bytes are not
  recoverable, stop `BLOCKED_TEST_AUTHORITY`; do not fabricate a semantic
  replacement. Only after Manager R-GATE may the same owner finish C6G.
- Decision:
  `docs/pm/reviews/S10_C6G_C14_TEST_DESTRUCTION_PM_DECISION_2026-09-02.md`.
  Binding prompt:
  `docs/pm/prompts/S10_C6G_C14_T3_FORENSIC_TEST_AUTHORITY_RECOVERY_MANAGER_2026-09-02.md`.
- Worker route remains `comboBAI`, custom/max/fallback OFF. S11/S12/S13
  production remains blocked.

### Live update — 2026-09-02 (Codex S10-C6F independent review)

- Verdict: `S10-C6F = CHANGES_REQUESTED / NOT_APPROVED`.
- C6F materially closes the single wrong-key claimant and sequential repeat-
  Retry 500 cases; Codex independently reran the current risk selection 13/13,
  and Ruff/mypy passed for reviewed bytes.
- P1 durable discovery remains non-invariant: `_s10_wrong_identity_claimant`
  returns a claimant only for exactly one row. Codex created two wrong-key jobs
  with the same workspace/generation/manifest; replay returned 200 reused and
  inserted a third canonical job (count 2 -> 3), instead of failing ambiguity.
- P1 Retry ownership remains false: `_s10_retry_claim_predecessor` still uses
  `cancelled -> cancelled`. Direct independent calls in two sessions returned
  `true, true` while status stayed cancelled. The later unique successor
  constraint masks the duplicate claim but does not make the CAS exclusive.
- P2 evidence arithmetic: C13 LOG/REPORT/registry say 15 rows/6 retained while
  the binding prompt and actual matrix contain 14 rows/5 retained.
- Only bounded `S10-C6G` is authorized. Resume exact compact recovery owner
  `20260901_230235_b80d4b`; do not create another worker and do not resume the
  superseded old lineage. Route remains exact `comboBAI`, custom/max, Hermes
  fallback OFF, TTFB 900.
- Review: `docs/pm/reviews/S10_C6F_PM_REVIEW_2026-09-02.md`. Prompt:
  `docs/pm/prompts/S10_C6G_EXCLUSIVE_RETRY_CLAIM_AMBIGUOUS_JOB_RESOLUTION_MANAGER_2026-09-02.md`.
- S11-T02..T06 and production S13 remain blocked; S13-P01 Character Fit
  Recommender remains planned.

### Live update — 2026-09-01 (Codex S10-C6E independent review)

- Verdict: `S10-C6E = CHANGES_REQUESTED / NOT_APPROVED`.
- C6E đã đóng các blocker C6D về true concurrent identical repair (một run/
  một job, generation non-NULL), full manifest `project_root/schema_version`
  và terminal-run/active-job lifecycle contradiction. Codex focused hiện tại
  8/8 + Ruff/mypy/diff-check đều xanh cho case đã viết.
- P1 còn lại: `_s10_find_durable_job` lookup bằng expected key nên một job bị
  đổi chỉ `idempotency_key` trở thành invisible; identical replay trả 200
  reused và tạo job queued thứ hai cùng run/generation. Test “wrong identity”
  không hề mutate key/job type/owner type như docstring tuyên bố.
- P1 Retry: CAS cho phép `cancelled -> cancelled` và vẫn coi rowcount=1 là
  exclusive winner. Retry lần hai cùng cancelled predecessor hiện trả 500 do
  unique S10 run conflict thay vì stable 409/convergence.
- P2 evidence: `test_c6e_worker_claim_vs_retry_barrier` vẫn tuần tự — claim/
  commit xong mới gọi Retry, không có thread/barrier/Event.
- Context-health audit cho logical owner T01C xác nhận recovery threshold:
  effective lineage `20260831_151420_07b6c2` có 617 messages/14 user turns/
  304 tool entries trong request dump 1,200,867 bytes, kèm repeated contract
  misses. Old writer đã dừng, ports free; C6F được phép mở đúng một compact
  recovery session và ghi owner transfer, không resume old lineage sau transfer.
- Latest user model override: exact `comboBAI`, provider custom, reasoning max,
  Hermes fallback chain OFF, TTFB 900. Combo hiện chứa BAI DeepSeek vision-exp
  và OCG DeepSeek v4 flash; phải ghi effective-member ledger.
- Review: `docs/pm/reviews/S10_C6E_PM_REVIEW_2026-09-01.md`. Prompt:
  `docs/pm/prompts/S10_C6F_EXACT_JOB_DISCOVERY_RETRY_CAS_RECOVERY_MANAGER_2026-09-01.md`.
- S11-T02..T06 và production S13 tiếp tục blocked; S13-P01 Character Fit
  Recommender vẫn planned.

### Live update — 2026-09-01 (Codex S10-C6D independent review)

- Verdict: `S10-C6D = CHANGES_REQUESTED / NOT_APPROVED`.
- Codex dùng real route/JobService/SQLite và barrier thật: hai simultaneous
  repaired replays đều trả 200 reused nhưng tạo hai job `queued` khác ID cùng
  idempotency key. Test C6D mang tên concurrent thực tế gọi A rồi B tuần tự.
- Validator không thực hiện lifecycle check như docstring: run `cancelled` +
  job `queued` vẫn replay 200 reused. Manifest compare cũng bỏ qua
  `project_root`/`schema_version`/extra keys; tamper chỉ `project_root` vẫn 200.
- Existing C6D sequential tests 8/8, Ruff/mypy/Alembic/OpenAPI xanh; phần sửa
  ordinary repair/retry và gross manifest tamper được chấp nhận nhưng chưa đủ
  sprint exit.
- BAI DeepSeek C6D: khoảng 50 phút/2 turns, 59 requests, router estimate
  0.688993; GLM C6C: khoảng 5h10/5 turns, 126 requests, 5.765848. DeepSeek nhanh
  và rẻ hơn rõ, nhưng concurrency reasoning chưa đáng tin nếu thiếu barrier.
- Chỉ authorize bounded `S10-C6E` cho exact T01C owner
  `20260828_003035_859fe5`, model exact
  `BAI/deepseek-v4-flash-vision-exp`, custom/max/fallback OFF. Completion-CAS,
  planner/rendering, frontend/T04B/T04C/build/evidence frozen.
- Review: `docs/pm/reviews/S10_C6D_PM_REVIEW_2026-09-01.md`. Prompt:
  `docs/pm/prompts/S10_C6E_TRUE_CONCURRENCY_IMMUTABLE_LIFECYCLE_MANAGER_2026-09-01.md`.
- S11-T02..T06 và production S13 vẫn blocked; S13-P01 Character Fit
  Recommender vẫn planned.

### Live update — 2026-09-01 (Codex S10-C6C independent review)

- Verdict: `S10-C6C = CHANGES_REQUESTED / NOT_APPROVED`. C10 đã sửa đúng
  zero-job orphan compensation và completion-CAS race, nhưng replay repair vẫn
  để run `failed` trong khi tạo job `queued`; immediate Retry tạo attempt/job
  thứ hai cho cùng lineage.
- Durable-job replay chỉ kiểm tra key tồn tại. Codex thay manifest bằng
  `{"tampered":true}` rồi identical replay vẫn nhận 200 `reused=true`; immutable
  authority/owner/job identity chưa được chứng minh trước success.
- Existing C10 tests 6/6 x2 và full suite gần như xanh nhưng không cover hai
  invariants này. Independent full: 230 passed + một fixture root đúng 260 ký
  tự; isolated longer-root rerun pass. Ruff/mypy/Alembic/OpenAPI green.
- C6C GLM cần năm turn, khoảng 5h10 wall-clock worker, có static fallout và test quá
  permissive. Local comparison không hoàn toàn đồng điều kiện nhưng direct
  DeepSeek C6 rộng hơn đã hoàn tất khoảng 1h17 và router estimate thấp hơn.
  User final override cho C6D là exact `BAI/deepseek-v4-flash-vision-exp`,
  custom/max/fallback OFF; model ID đã được xác nhận có trong 9Router `/v1/models`.
- Chỉ authorize bounded `S10-C6D` cho exact T01C owner
  `20260828_003035_859fe5`; completion-CAS/frontend/T04B/T04C frozen. C6D phải
  chứng minh coherent repaired replay, immutable manifest/owner và at most one
  active work across replay/retry/worker races.
- Review: `docs/pm/reviews/S10_C6C_PM_REVIEW_2026-09-01.md`. Prompt:
  `docs/pm/prompts/S10_C6D_REPLAY_SINGLE_WORK_CORRECTION_MANAGER_2026-09-01.md`.
- S11-T02..T06 và production S13 tiếp tục blocked đến khi S10 được Codex
  APPROVED/CLOSED; S13-P01 Character Fit Recommender vẫn giữ nguyên.

### Live update — 2026-09-01 (Codex S10-C6B independent review)

- Verdict: `S10-C6B = CHANGES_REQUESTED / NOT_APPROVED`. Manager C6B đã hoàn
  tất phần lớn lifecycle/UI/vertical và full suite hiện không có regression
  rộng, nhưng Codex tái hiện hai P1 acceptance-critical trong T01C.
- Submit enqueue failure để lại pending run không job; identical replay trả 200
  `reused=true` dù durable job count vẫn bằng 0. Retry enqueue failure cũng để
  lại attempt 2 pending không job. Đây là active orphan/false-success.
- Nhánh worker resume với pre-existing completed publication execute completion
  CAS nhưng không kiểm rowcount/live status, sau đó unconditionally ghi
  `completed:true`; cancel có thể thắng CAS nhưng durable checkpoint vẫn nói
  completed.
- Chỉ authorize bounded `S10-C6C` cho exact T01C owner
  `20260828_003035_859fe5`. T04B/T04C/frontend/harness frozen; retain 20/20 và
  đúng hai final verticals dưới `run2-c6b-green/run1` + `/run2` nếu hashes không
  đổi.
- Model decision: worker correction dùng direct exact
  `BAI/glm-5.3-flash`, reasoning max, fallback OFF; cấm `comboBAI`. C6B alias
  thực tế route 984 request vào GLM và chỉ 3 vào DeepSeek vision, nên không phải
  controlled comparison. GLM được chọn cho complex coding, nhưng findings này
  chứng minh independent Codex review vẫn bắt buộc.
- Review:
  `docs/pm/reviews/S10_C6B_PM_REVIEW_2026-09-01.md`. Prompt:
  `docs/pm/prompts/S10_C6C_ENQUEUE_CAS_EXIT_CORRECTION_MANAGER_2026-09-01.md`.
- S11-T02..T06 và production S13 vẫn blocked đến khi S10 được Codex
  APPROVED/CLOSED. S13-P01 Character Fit Recommender vẫn nằm trong kế hoạch.

### Live update — 2026-08-31 14:51 +07 (Codex S10-C6A cancel lifecycle decision)

- Verdict: `S10-C6A = CONTINUATION_AUTHORIZED / NOT_APPROVED`. Hermes không bị
  treo: exact T04B frontend owner dừng đúng `BLOCKED_SCOPE_EXPANSION` sau khi
  20-case live UI suite phát hiện backend T01C cancel-route race.
- Independent root cause: request session giữ SQLite write transaction, route
  mở read session rồi gọi second writer; `database is locked` bị
  `except Exception: pass` nuốt. Route vẫn trả cancelled, durable job tiếp tục
  và worker unconditional update ghi đè run `cancelled -> completed`, có thể
  tạo completed publication. Resume route có multi-session/silent-success risk
  cùng họ và phải được audit trong một bounded lifecycle round.
- Authorized C6B exact-owner DAG:
  `T01C-C9-LIFECYCLE -> J6C -> resume T04B-C3 -> J6-UI -> J6-BUILD -> resume
  T04C-C5 -> EXIT`. Manager phải tự tiếp tục qua iteration limits bằng cùng
  exact sessions; chỉ quay lại Codex khi có blocker cross-owner mới hoặc final
  sprint review.
- User model override mới nhất: mọi C6B worker/resume quay lại dùng chính xác
  `ocg/deepseek-v4-flash`, reasoning max, fallback OFF, TTFB 900; probe exact
  route, không tự sửa alias/spelling/case và không fallback. Override tạm
  `BAI/deepseeekv4flash` đã bị rút vì không ổn định.
- Review:
  `docs/pm/reviews/S10_C6A_CANCEL_LIFECYCLE_PM_DECISION_2026-08-31.md`. Prompt:
  `docs/pm/prompts/S10_C6B_CANCEL_LIFECYCLE_CONTINUATION_MANAGER_2026-08-31.md`.
- S10 vẫn chưa APPROVED/CLOSED; S11-T02..T06 và production S13 vẫn blocked.

### Live update — 2026-08-31 10:01 +07 (Codex S10-C6 blocker decision)

- Verdict: `S10-C6 = CONTINUATION_AUTHORIZED / NOT_APPROVED`. Hermes dừng đúng
  tại `BLOCKED_SCOPE_EXPANSION`; Codex bác expose hash đơn thuần, nới equality
  hoặc waiver.
- Root cause P0 sâu hơn UI: `FullApplyService.submit` vẫn plan bằng
  scene/mapping client gửi và route tiếp tục ghi các body đó vào job
  `render_authority`. C5 E2E và C6 probe từng đổi `mesh_warp -> sprite_affine`
  và tự gắn affected region, nên phần backend/authority-green của review C5 bị
  supersede.
- Approval v1 không đủ authority: nó không pin SLM canonical hash/manifest,
  exact selected route, source, mapping/config/geometry. Fresh C6 DB còn chứa
  sáu route alternatives cho hai segments; checkpoint hash, timebase fingerprint
  và SLM hash là ba giá trị khác nhau.
- Authorized serialized C6A: exact S09-T06A owner tạo immutable approval v2;
  exact S10-T01C owner chuyển Full Apply sang server-derived minimal submit;
  rồi resume exact T04B 20-case live UI, fresh build và exact T04C hai vertical
  runs không DB/client authority fabrication.
- Exact owner/model: T06A `20260824_120141_312e9e`, T01C
  `20260828_003035_859fe5`, T04B `20260828_020206_b1f8af`, T04C
  `20260828_023122_76b87e`; mọi resume dùng `ocg/deepseek-v4-flash`, reasoning
  max, fallback OFF, TTFB 900.
- Review: `docs/pm/reviews/S10_C6_BLOCKER_PM_DECISION_2026-08-31.md`. Prompt:
  `docs/pm/prompts/S10_C6A_SERVER_DERIVED_APPLY_AUTHORITY_MANAGER_2026-08-31.md`.
- S11-T02..T06 và production S13 vẫn blocked; S13-P01 Character Fit
  Recommender planning delta vẫn giữ nguyên.

### Live update — 2026-08-30 18:01 +07 (Codex S10-C5 independent review)

- Verdict: `S10-C5 = CHANGES_REQUESTED / NOT_APPROVED`. C5 đã sửa đúng Apply
  lint, exact frontend lint/TSC/build validator xanh, current BUILD_ID
  `rbYCsFU8q82gvOvcRhJSA`, backend full suite 206/206 và hai fresh vertical run
  C5 có DB/artifact/media/recovery/structural truth độc lập xanh.
- P1 blocker còn lại là acceptance integrity trong
  `frontend/e2e/s10-apply-ui.spec.ts`: test progress/evidence/actions có thể pass
  ở empty state; test cancel/retry/resume không click hành động; disabled Apply
  không assert disabled; mobile bị skip trong current config. T04C API vertical
  runs không thay thế user-facing `/apply` browser acceptance.
- Bounded C6: resume exact T04B owner `20260828_020206_b1f8af`, model exact
  `ocg/deepseek-v4-flash`, reasoning max, fallback OFF, để viết live-product UI
  acceptance trên fresh isolated product services. Backend frozen; chỉ nếu test
  phát hiện T04B frontend defect mới sửa trong original scope. Nếu production
  build input đổi, exact T04C owner `20260828_023122_76b87e` phải chạy lại hai
  fresh current-build vertical runs.
- Review: `docs/pm/reviews/S10_C5_PM_REVIEW_2026-08-30.md`. Prompt:
  `docs/pm/prompts/S10_C6_REAL_APPLY_UI_ACCEPTANCE_MANAGER_2026-08-30.md`.
- S11-T02..T06 và production S13 vẫn blocked. S13-P01 Character Fit
  Recommender vẫn là planning delta bắt buộc trước production S13.

### Live update — 2026-08-30 16:27 +07 (Codex S10-C4 final re-review)

- Verdict: `S10-C4 = CHANGES_REQUESTED / NOT_APPROVED`. C4 đã đóng thực chất
  các finding backend C3: Codex độc lập xác nhận Ruff/mypy/Alembic/OpenAPI/J1,
  effective backend 206/206, durable correction, measured structural gate,
  long-path media và hai DB vertical run có authority/restart/affected-only
  truth.
- Blocker duy nhất là frontend gate trong S10-owned
  `frontend/src/app/(app)/apply/page.tsx:90`: synchronous `setRunId` trong
  effect làm exact Apply ESLint exit 1 (`react-hooks/set-state-in-effect`).
  T04B evidence cũ chỉ lint `src/features/apply/**`, bỏ sót chính route page.
  Cùng command còn bốn warning trong hai S10 E2E files.
- Bounded C5 DAG: resume exact T04B owner `20260828_020206_b1f8af` để sửa
  URL/state và own warning; J5 build/lint; resume exact T04C owner
  `20260828_023122_76b87e` để dọn own warnings và chạy hai fresh vertical runs
  trên corrected current BUILD_ID; backend frozen.
- Review: `docs/pm/reviews/S10_C4_FINAL_PM_REVIEW_2026-08-30.md`. Prompt:
  `docs/pm/prompts/S10_C5_APPLY_LINT_CURRENT_BUILD_EXIT_MANAGER_2026-08-30.md`.
- Worker model vẫn bắt buộc exact `ocg/deepseek-v4-flash`, reasoning max,
  fallback OFF. S11-T02..T06 và production S13 vẫn blocked.

### Live update — 2026-08-30 10:05 +07 (Codex S10-C4 blocker decision)

- Hermes dừng đúng tại `S10-C4 = BLOCKED_SCOPE_EXPANSION / PENDING_CODEX_DECISION`.
  Independent Ruff rerun trên exact 9 production + 8 S10 test files xác nhận
  đúng một lỗi `F841`: dead assignment
  `tests/test_s10_full_apply_domain.py:172`.
- File thuộc exclusive write-set S10-T01A; exact owner là
  `20260827_234001_9d7f39`. Codex không waiver Ruff và đã cấp quyền tối thiểu
  resume owner này để xóa đúng một dòng, re-run J4, rồi chỉ khi J4 xanh mới
  resume T04C owner `20260828_023122_76b87e` cho hai strict C4 vertical runs.
- Decision review:
  `docs/pm/reviews/S10_C4_BLOCKER_PM_DECISION_2026-08-30.md`. Prompt tiếp theo:
  `docs/pm/prompts/S10_C4A_T01A_STATIC_UNBLOCK_AND_EXIT_MANAGER_2026-08-30.md`.
- Worker route giữ đúng user override: exact `ocg/deepseek-v4-flash`, reasoning
  max, fallback OFF; raw alias/OpenRouter/CMC/Meta bị cấm. `S10` vẫn chưa
  APPROVED/CLOSED; production S11/S12/S13 vẫn không mở.

### Live update — 2026-08-29 21:55 +07 (S13 Character Fit Recommender requirement)

- User yêu cầu khi tạo pose/reskin phải dựa trên nhân vật mẫu để AI đề xuất các
  nhân vật/Pack Version hoặc generation starting profile tương đương, nhằm giảm
  biến dạng và số lần regenerate.
- Roadmap đã thêm `S13-P01` là planning delta bắt buộc trước production S13.
  Tính năng phải hard-gate topology/pose-view coverage/anchors/proportion trước,
  sau đó mới dùng embedding/style similarity để xếp hạng Top-K có giải thích.
  AI chỉ tư vấn; user xác nhận và không được bypass compatibility/Demo/publish.
- `S13-P00 C6` vẫn là approved 22-task baseline và không bị sửa hồi tố. Codex
  BA/PM phải review/decompose P01 rồi mới đưa delta vào prompt production tương
  lai. `S13-T01` hiện `BLOCKED_PLANNING_DELTA / NOT_DISPATCH_AUTHORIZED`; S10-C4
  vẫn là lane đang được cấp quyền.

### Live update — 2026-08-29 19:30 +07 (Codex S10-C3 independent review)

- `S10-C3 = CHANGES_REQUESTED`; S10 chưa `APPROVED/CLOSED`. Review:
  `docs/pm/reviews/S10_C3_PM_REVIEW_2026-08-29.md`.
- P0 authority/fence: FullApply production route tự tạo 100-frame NumPy source
  và hash-colored assets; `job_reconciler._input_changed` trả unchanged cho
  mọi S10 job. Đây là production write ngoài T04C scope và phá immutable-input
  restart contract.
- P0 semantics: T03 đã gọi T02 executor nhưng vẫn dựng fallback checkpoint/
  zero-hash/gen-1/frame100 authority và chỉ perturb affected region theo hash
  correction ID; không bind/apply durable correction thật. T04A vẫn mirror
  cuts, dùng fixed-low metric arrays và missing evidence=`0/False`.
- Independent gates: J1-v4 13/13 retained; full S10 `169 passed, 1 failed`
  trên fresh nested Windows root (269-char sidecar), exact nine-file mypy
  `15 errors/3 files`, Ruff F* `6 errors`, alembic/OpenAPI/diff-check green.
- T04C run1/run2 có artifact plumbing tiến bộ thật: mỗi DB 24 verified chunks,
  2 publications, recompute 4/4, 30 DB-bound MP4 đều SHA/size/ffprobe green.
  Nhưng cả hai dùng cùng synthetic source SHA, fixed mapping, zero persisted
  structural rows, direct SQLite manifest patch và direct lease requeue nên
  không phải vertical acceptance hợp lệ.
- Registry claim “ALL 9 GATES GREEN” tự mâu thuẫn với mypy failure; S10 sprint
  report không được append sau C3 và vẫn là R0/R1 snapshot cũ.
- C4 serialized exact-owner DAG:
  `T01C-authority/fence -> T03-real-correction -> T04A-real-measurement ->
  T01C-static -> T04C-strict -> EXIT`. Prompt:
  `docs/pm/prompts/S10_C4_AUTHORITY_SEMANTICS_EXIT_CORRECTION_MANAGER_2026-08-29.md`.
- Latest user model override for every C4 worker, including resumed exact owner
  sessions: Hermes selector `deepseek-v4-flash`, effective
  `ocg/deepseek-v4-flash`, reasoning `max`, fallback OFF. This supersedes the
  prior C3 `custom/meta` route; wrong/unavailable route is
  `BLOCKED_MODEL_ROUTE`, never auto-fallback.
- S11-P02 rev-C6 và S13-P00 C6 vẫn approved planning-only. Production S11
  remains blocked on E06/S10; production S13 remains `NOT_OPENED`.

### Live update — 2026-08-29 11:35 +07 (Codex S10-C2 independent review)

- `S10-C2 = CHANGES_REQUESTED`; S10 chưa `APPROVED/CLOSED`. Review độc lập:
  `docs/pm/reviews/S10_C2_PM_REVIEW_2026-08-29.md`.
- Hai P0 production blockers: T03 recompute tại
  `app/services/s10_recompute.py:637-688` vẫn dựng frame màu/hash và tự gán
  correction kind thành adapter; T04A route tại
  `app/api/routes/s10_full_apply.py:1086-1239` vẫn dùng source-cut synthetic,
  fixed-low metrics và missing-evidence=`0/False`/fallback annotations.
- Full fresh nested-Windows S10 gate độc lập: `2 failed, 164 passed`; đúng hai
  test T03 pass trên short root, xác nhận path-budget defect tại atomic
  `*.evidence.json.staging`, không phải logic green cho root được yêu cầu.
  Nine-file S10 mypy còn `76 errors in 5 files`.
- T04C-C1 không có worker result C2. Hai retained roots là byte-copy của R1,
  BUILD_ID cũ, `.bin` không ffprobe-decodable, artifact SHA/size NULL, không
  publication/recompute; harness còn terminal/missing-route/caller-metric
  fallbacks. Chúng không phải acceptance evidence hợp lệ.
- Gates vẫn pass: J1-v4 direct 13/13 (12 LF + 1 CRLF), Ruff functional F*,
  Alembic one head `a10b11c12d3e`, OpenAPI materialization, TSC, Apply ESLint,
  current build validator 7/7 BUILD_ID `UoAHhbO6043uUWKNz2JTZ` và
  `git diff --check`.
- C3 correction serialize exact owners:
  `T03 20260828_011920_b79bd6 -> T04A 20260828_014304_25d94a -> T01C-static
  20260828_003035_859fe5 -> T04C 20260828_023122_76b87e`. Route giữ
  `custom/meta/max/no-fallback`; T01A/T01B/T02/T04B frozen. Prompt:
  `docs/pm/prompts/S10_C3_REALITY_EXIT_CORRECTION_MANAGER_2026-08-29.md`.
- `S11-P02 rev-C6 = CODEX_APPROVED` cho planning/readiness packet 19 IDs/14
  waves; production S11 vẫn blocked trên E06/S10. `S13-P00 C6` vẫn approved
  planning-only; production S13 vẫn `NOT_OPENED` vì shared paths còn dirty/
  active trong S10.

### Live update — 2026-08-29 04:00 +07 (S10-C2 submitted for Codex re-review)

- Integration authority remains
  `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`, branch
  `codex/s08-integration`, reviewed base HEAD `d3f6f796558aa9c7247da7d51e7d34e65b56cdf7`;
  S10 is still an uncommitted dirty write-set. A new reviewer must rediscover
  actual branch/HEAD/status/processes before using this snapshot.
- S10 Manager registry stops at `2026-08-29 03:58 +07` with
  `S10-C2 = PENDING_CODEX_REREVIEW`; this is not `APPROVED/CLOSED`.
- J1-J5 are manager-claimed green after exact-owner corrections. They still
  require independent Codex source/test/evidence review.
- T04C-C1 did not produce a successful C2 worker result: both resume wrappers
  exited 1 with no usable worker output. Manager retained `TASK_SUBMITTED` and
  copied/migrated the old R1 Run1/Run2 evidence into
  `output/s10/c2/t04c-c1/**`.
- T04C's retained report explicitly says the old runs completed all 12 chunks
  before the manual stop, tolerated an absent recompute route, produced twelve
  `chunk_*.bin` files per run, and used BUILD_ID
  `g3s0EKHByfzsFsRNZpWRI`; the current C2 build manifest is
  `UoAHhbO6043uUWKNz2JTZ`. These facts conflict with C2's strict mid-run
  restart, real recompute, decodable-media and same-current-build acceptance.
  They are review leads, not a pre-recorded Codex verdict.
- Immediate review packet for the next long-lived Codex PM session:
  `docs/pm/prompts/CODEX_PROJECT_PM_CONTINUATION_S10_C2_REVIEW_2026-08-29.md`.
  That session must independently review S10-C2 first and always issue the
  bounded Hermes prompt corresponding to its verdict.
- S09 remains Codex-approved/closed. S11-T01 is approved, but S11-T02..T06 and
  production S13 remain unopened pending S10/E06 exit and a fresh dependency/
  write-set review. S13-P00 planning only is approved.

### Live update — 2026-08-27 21:40 +07 (Codex S09-C7-R2 final review)

- `S09-C7-R2 = CODEX_APPROVED / CLOSED`; toàn Sprint `S09 = CODEX_APPROVED /
  CLOSED`. Không còn P0/P1.
- Codex độc lập xác nhận build validator 7/7 trên BUILD_ID
  `dm7D7QTAc52eVVVHqU09Y`, 185 file/hash, manifest SHA `c606d99b...`; J1-v4
  direct 13/13; exact T06 backend 43/43; TSC, scoped ESLint và diff-check xanh.
- Direct SQLite trên cả hai R2 DB chứng minh đúng một renderer attempt, chỉ d4
  regenerated và d1-d3 exact reuse. Codex còn chạy một Chromium acceptance mới
  trên explicit fresh temp roots: 1 passed (41.4s), owned restart
  `28784 -> 18924`, checkpoint read sau restart, all owned processes exited và
  ports 3115/8201/8212 released; unrelated 3014/8099 preserved.
- Ba P2 không chặn được carry forward: `REPORT-C7.md` chưa append R2, per-run
  `env.json` chưa ghi BUILD_ID/manifest SHA, parser chưa reject positional
  garbage. Không mở C8 chỉ để sửa documentation/harness polish.
- Review:
  `docs/pm/reviews/S09_C7_R2_FINAL_PM_REVIEW_2026-08-27.md`.
- S10 Full Apply là production lane kế tiếp và đã được Codex chia thành tám
  owner packets. Prompt:
  `docs/pm/prompts/S10_FULL_APPLY_MANAGER_2026-08-27.md`.
- GitHub backup sau S09: code/test/session evidence đã push commit `d3f6f79` lên
  `origin/codex/s08-integration`; Codex/Hermes settings, roadmap, prompts và
  reviews đã push commit `3e61640` lên `origin/master`. Remote default `main`
  vẫn ở `ee10e55`; chưa fast-forward trực tiếp vì thao tác nhánh mặc định cần
  user phê duyệt rõ hoặc PR.
- S11-T02..T06 vẫn blocked trên E06 cho tới S10 exit; production S13 vẫn không
  mở song song vì overlap `models.py`, migrations, `app/api/app.py` và
  integration state với S10.

### Live update — 2026-08-27 (Codex S09-C7-R1 independent review)

- `S09-C7-R1 = CHANGES_REQUESTED`; corrected terminal is
  `S09-C7-R2 = BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`. This remains
  inside C7, not C8. S09 is not APPROVED/CLOSED; S10, production S11 and
  production S13 remain blocked.
- Product evidence is now materially green: both Chromium runs passed with
  real owned restart; direct DB probes show one attempt rendering d4 only and
  exact reuse of d1-d3; build chunks currently match 182/182; fixture is 21/21;
  independent J1 is 13/13, T06 backend 43/43, TSC and ESLint pass.
- P1 product/config blocker: R1 changed shared `frontend/next.config.ts` outside
  its write set and made test port 8201 the no-env application fallback. Normal
  product authorities still use 8888. Restore env-driven rewrite with 8888
  fallback; C7 build continues to inject 8201 explicitly.
- P1 harness blocker: `run-c7.js` still reuses a build when BUILD_ID alone
  matches and still hard-codes/deletes only run1/run2 roots. This contradicts
  the terminal claim and prevents safe fresh-root independent reproduction.
- P2: direct current `git diff --check` finds an extra blank EOF in the S09
  registry despite the report's exit-0 claim.
- Review: `docs/pm/reviews/S09_C7_R1_PM_REVIEW_2026-08-27.md`.
- Only authorized next packet:
  `docs/pm/prompts/S09_C7_R2_FINAL_CONFIG_BUILD_INTEGRITY_MANAGER_2026-08-27.md`.
  Resume Manager `20260827_020702_b17b35` and exact T06B owner
  `20260824_131423_423e42`, model `meta`, reasoning max. No backend/product-flow
  rewrite and no other sprint production.

### Live update — 2026-08-27 (Codex S09-C7 independent review)

- `S09-C7 = CHANGES_REQUESTED`; corrected terminal is
  `S09-C7-R1 = BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`. This is a bounded
  continuation inside C7, not C8. S09 is not APPROVED/CLOSED; S10, production
  S11 and production S13 remain blocked.
- Retained green: owned initial/replacement backend lifecycle is now real;
  Run1/Run2 lifecycle and product evidence are coherent; independent J1-v4 is
  13/13, T06 backend is 43/43, TSC and scoped ESLint pass. Independent failure
  cleanup also released exact PIDs and ports 3115/8201/8212.
- P1 blocker: current `.next` was rebuilt at 18:59 after the passing C7 runs,
  contains `http://localhost:8888` in 26 files and contains zero required 8201
  URL. `run-c7.js` trusts only BUILD_ID existence, so Codex's fresh Chromium
  run reached the wrong backend and failed at `(không có project)`.
- P1 launcher gap: active C4/C6 fixture fallback remains, and Next/Playwright
  still run through `npx` plus `shell:true`; REPORT-C7 does not reconcile those
  facts or the post-run build.
- Review: `docs/pm/reviews/S09_C7_PM_REVIEW_2026-08-27.md`.
- Only authorized next packet:
  `docs/pm/prompts/S09_C7_R1_REPRODUCIBLE_BUILD_CONTINUATION_MANAGER_2026-08-27.md`.
  Resume Manager `20260827_020702_b17b35` and exact T06B owner
  `20260824_131423_423e42`, model `meta`, reasoning max. No backend/product
  rewrite and no other sprint production.

### Live update — 2026-08-27 (Codex S09-C6 independent review)

- `S09-C6 = CHANGES_REQUESTED`; corrected terminal is
  `BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`. S09 is not APPROVED/CLOSED;
  S10, production S11 and production S13 remain blocked.
- Retained green under Codex rerun: J1-v4 direct 13/13 with 12 LF + composite
  CRLF guard; coherent frozen-evidence test PASS; T06 backend 43/43; TSC and
  scoped ESLint PASS; Run1/Run2 use distinct runtime roots and DBs.
- P0 acceptance blocker: the spec calls `stopLaunched(primaryLaunched)` while
  `primaryLaunched` is still null. The original backend belongs to external
  `run-prod.js`; the attempted replacement may collide with port 8201 while the
  health probe still reaches the original process. The claimed checkpoint
  restart is therefore not proven.
- P1: runner cleanup can resolve without process exit, manual taskkill appears
  in the worker report, Next uses an unowned shell wrapper, and global setup /
  config retain C4 runtime/seeder fallbacks.
- Review: `docs/pm/reviews/S09_C6_PM_REVIEW_2026-08-27.md`.
- Only authorized next packet:
  `docs/pm/prompts/S09_C7_OWNED_RESTART_CORRECTION_MANAGER_2026-08-27.md`.
  Resume only T06B owner `20260824_131423_423e42` with exact model `meta`,
  reasoning max. No backend/product rewrite and no other sprint production.

### Live update — 2026-08-27 (Codex S09-C5 independent review)

- `S09-C5 = CHANGES_REQUESTED`; corrected terminal là
  `BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`. S09 chưa APPROVED/CLOSED; S10,
  production S11 và production S13 vẫn blocked.
- Backend correction is materially green under independent rerun: T03 40/40,
  T04 24/24 including >=260-char path, T06 backend 43/43, Ruff/mypy/TSC/scoped
  ESLint pass.
- P1 blockers: J1-v4 direct bytes are 6/13 because seven files reverted to
  CRLF and no `.gitattributes` protects the manifest; Chromium restart kills an
  unverified listener on 8201 and leaks the replacement handle; Run1/Run2 reuse
  one hard-coded runtime/DB/output and Run2 lacks complete raw evidence.
- P2: “different verified evidence” flips only a declared SHA and accepts any
  404/409/422; J3 evidence directory omits several claimed logs.
- Review: `docs/pm/reviews/S09_C5_PM_REVIEW_2026-08-27.md`.
- Only authorized next packet:
  `docs/pm/prompts/S09_C6_EXIT_HARDENING_MANAGER_2026-08-27.md`. C6 runs one new
  EOL-guard task plus exact T03/T06B corrections; no other sprint opens.

### Live update — 2026-08-27 (Codex S09-C4 independent review)

- `S09-C4 = CHANGES_REQUESTED`; corrected terminal là
  `BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`. S09 chưa APPROVED/CLOSED; S10,
  production S11 và production S13 vẫn blocked.
- Retained green: J1-v4 SHA `ae92247b...` re-hash 13/13, T06 backend 43 passed,
  frontend TSC và scoped ESLint pass.
- Independent blockers: T04 long-path run `22 passed, 1 failed`; zero-mutation
  collision test permits committed junk lineage; frozen identity includes
  filesystem path; Chromium production E2E is not reproducible from normal
  Windows Node/PowerShell launcher; Ruff has six errors and mypy one error.
- Manager evidence/state was not reconciled and old task-owned QA processes
  remained. Manager/worker scope boundaries must be restored.
- Review: `docs/pm/reviews/S09_C4_PM_REVIEW_2026-08-27.md`.
- Only authorized next packet:
  `docs/pm/prompts/S09_C5_FINAL_CORRECTION_MANAGER_2026-08-27.md` revision C5-R2;
  resume exact T03/T04/T06B owners in one disjoint PREP wave with Hermes
  model/combo `meta`, reasoning max, then enforce full quiescence and serialized
  integration/correction/production gates. No other sprint production work is
  opened.

### Live update — 2026-08-26 09:51 +07 (Codex S09-C3 independent review)

- `S09-C3 = CHANGES_REQUESTED`; corrected terminal là
  `BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`. Không APPROVED/CLOSED/push;
  S10, production S11 và production S13 vẫn blocked.
- C3 giữ được các cải thiện thật: J1-v4 manifest SHA `ae92247b...` re-hash 13/13
  zero drift; I03 run-A `12de1345...`, run-B `dab37e41...`, I05 decision
  `d289929d...`; long-path/content/freeze chain hiện không phải blocker.
- Independent focused T03/T04/T05A-C3 suite `51 passed`; Ruff reviewed
  write-set, frontend TSC, Alembic one head `b3c4d5e6f7a9` và diff-check xanh.
- P0 runtime repro từ chính production QA DB: regeneration job
  `d2bad83e-9a89-4387-ad51-97ad7436dcba` requested/affected cả d1-d4 và ghi
  `regenerated=true` cho cả bốn; render_ms d1=764, d2=375, d3=687, d4=625.
  Artifact d1-d3 giống base chỉ vì byte-identical rerender, không phải reuse.
- Root causes: `CorrectionPanel` trả toàn bộ completed loops; T06B chỉ so
  artifact identity. T03 z-order luôn sửa `placements[0]`, bỏ qua affected layer;
  four non-z kinds không có real effect dispatcher; fingerprint thiếu frozen
  evidence SHA; worker workspace guard self-compares và không có tác dụng.
- Review record:
  `docs/pm/reviews/S09_C3_PM_REVIEW_2026-08-26.md`.
- Next authorized packet:
  `docs/pm/prompts/S09_C4_CORRECTION_MANAGER_2026-08-26.md`. Resume exact
  T05A/T03/T04/T05B/T06B owners theo Wave A; không rerun I03/I05 nếu J1-v4
  không drift. Không mở sprint khác.

### Live update — 2026-08-25 22:46 +07 (Codex S09-C2 independent review)

- `S09-C2 = CHANGES_REQUESTED`; corrected terminal là
  `BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`. Không APPROVED/CLOSED/push;
  S10, production S11 và production S13 chưa được mở.
- P0 product gap: production correction confirm không tạo durable targeted
  regeneration. C2 E2E cố ý làm route pin fail rồi replay job cũ và assert mọi
  loop, kể cả affected loop, không đổi; đó là zero regeneration, trái binary
  acceptance “affected generation mới / unaffected exact reuse”.
- P0 evidence gap: Manager pin J1-v3 `b8928aec...` sau drift nhưng I03/I05 và
  production downstream vẫn pin v2 `aa405015...`; harness còn một freeze
  authority riêng chỉ ba file/token C1.
- Independent full 23-file S09 suite trên isolated worktree basetemp:
  `1 failed, 362 passed`. Failure thật là T04 content GET trả 404 trên absolute
  MP4 path dài 272 ký tự dù file đã publish; writer long-path safe nhưng reader/
  FileResponse chưa safe.
- Benchmark `decoded_output_hash` là raw frame concat, không phải canonical
  frame-count+shape+bytes hash. UI cũng không gửi `affected_loop_ids` và
  ApprovalPanel không match route-override evidence.
- Static gates vẫn tốt: Ruff, mypy 125 files, Alembic one head, TSC, scoped
  ESLint, production build và materialized OpenAPI no-duplicate đều pass.
- Review record:
  `docs/pm/reviews/S09_C2_PM_REVIEW_2026-08-25.md`.
- Next authorized packet:
  `docs/pm/prompts/S09_C3_CORRECTION_MANAGER_2026-08-25.md`. C3 resume exact
  T05A/T03/T04/T05B/I03 owners theo Wave A, unified J1-v4, I05 decision rồi
  T06B production E2E. Không tự mở sprint khác.

### Live update — 2026-08-25 09:50 +07 (Codex S09-C1 re-review)

- `S09-C1 = CHANGES_REQUESTED`; corrected terminal tại review boundary là
  `BLOCKED_WITH_FINDINGS / PENDING_CODEX_REVIEW`. Không APPROVED/CLOSED/push;
  S10 và production S11 vẫn blocked, production S13 chưa được mở bởi lane này.
- Independent current gate trên toàn bộ 22 `tests/test_s09*.py`:
  `8 failed, 318 passed`. Bốn lỗi do J1 frozen SHA drift
  (`46c6a4...` expected, `62c7d7...` actual); bốn lỗi T03/T04 do durable publish
  chạm Windows path length 260 và job fail tại `.mp4.upload`.
- C1 decision v2 chỉ có 4/12 route-fixture rows measured; hard-cut và
  group-occlusion không có route measured. C1 prompt bắt buộc trường hợp này
  phải BLOCKED, không cho Manager ghi TASK_MANAGER_VERIFIED.
- Benchmark hiện gọi thẳng compositor/private helper thay vì production
  `RendererRouter`/adapter; frontend/T03/T04 vẫn dùng artifact v1 `t00-i05`.
  Renderer còn fixed 30fps, request-ID identity control và pre-encode output
  hash; production E2E thiếu proof only-affected-loop regenerate.
- Review record:
  `docs/pm/reviews/S09_C1_PM_REVIEW_2026-08-25.md`.
- Next authorized packet:
  `docs/pm/prompts/S09_C2_CORRECTION_MANAGER_2026-08-25.md`. Wave A resume năm
  exact owners T02/I03/T03/T04/T06B song song; J1 immutable renderer manifest;
  I03 actual-router measurement; I05 decision; rồi downstream/E2E join và stop
  for Codex review. Không tự mở sprint khác.

### Live update — 2026-08-24 21:18 +07 (Codex S09 full-sprint review)

- `S09 = CHANGES_REQUESTED`; S09 is not approved/closed and S10/S11 production
  remains blocked.
- P0 core finding: T02 `pose_swap` only re-encodes the source and
  `sprite_affine` transforms the whole source frame with fixed constants; the
  benchmark scores source fixtures rather than renderer outputs. F5 group
  occlusion uses an empty probe universe yet is reported PASS, and reference
  `VERIFIED` means SHA/ffprobe only.
- Independent default-Windows S09 suite: `247 passed, 1 failed`; the T02
  additive gate depends on ambient subprocess encoding and mutable Git HEAD.
- Deferred post-core findings: production OpenAPI has no T05/T06 paths, T06A
  submit does not commit, correction schema accepts invalid route/anchor/frame
  payloads, and T01 route evidence mixes NULL-manifest rows into a pinned view.
- Review record:
  `docs/pm/reviews/S09_FULL_SPRINT_PM_REVIEW_2026-08-24.md`.
- Next prompt is the user-authorized fast-track full correction:
  `docs/pm/prompts/S09_C1_FAST_TRACK_MANAGER_2026-08-24.md`. Prompt tuần tự
  `S09_CORE_C1_CORRECTION_MANAGER_2026-08-24.md` đã superseded theo quyết định
  ưu tiên tốc độ của user. Fast-track chạy tối đa 5 owner có write-set tách biệt,
  dùng renderer-contract và production-API join gates. Wave A resume exact
  owners T02, I03, T01, T05A và T06A; Wave B chạy I05 và production-stack T06B,
  rồi stop for Codex re-review. Không mở S10/S11/S13.

### Live update — 2026-08-24 00:20 +07 (Codex S11-P02 rev-C5 re-review)

- `S11-P02 rev-C5 = CHANGES_REQUESTED`; exact synthesis owner phải resume:
  `20260823_145947_057312`, route custom/alpha/max/no-fallback.
- C5 đã sửa đúng bốn wave/Task references và thêm lane-proposal authority
  fence, nhưng active T03D acceptance vẫn đếm 8 overlay reason codes qua
  T03E audio/timecode. Binding partition phải là T03B=2 + T03C=3 + T03D=3;
  T03E là hai check riêng.
- Metadata hiện hành còn stale/sai ngày và C5 chưa tách explicit worker
  write-set khỏi Manager coordination append. Review record:
  `docs/pm/reviews/S11_P02_PM_REVIEW_2026-08-23.md`.
- Next prompt:
  `docs/pm/prompts/S11_P02_C6_CORRECTION_2026-08-24.md`. Đây là docs-only
  correction; `S11-T02..T06 = BLOCKED_DEPENDENCY_ON_E06/S09`, không production
  dispatch.

### Live update — 2026-08-23 23:20 +07 (Codex re-review of actual C6)

- `S13-P00 = CODEX_APPROVED`: C6 changed exactly the three authorized files;
  23/26 baseline files remained byte-identical, the stale C4 label is gone,
  the report ends `TASK_SUBMITTED`, and all 22 task/write-set/acceptance/DAG
  contracts remain intact. Review record:
  `docs/pm/reviews/S13_P00_PM_REVIEW_2026-08-23.md`.
- Approval is for the P00 planning baseline only. `PRODUCTION_S13 = NOT_OPENED /
  BLOCKED_RESOURCE_ON_S09_ACTIVE_INTEGRATION_LANE`.
- At 23:20 +07, integration HEAD was
  `ee10e55a809c84d5cb5d4a3046a1ee78828528d0`; S09 I02/I03 artifacts had recent
  writes through 23:18 and the worktree carried active S09 renderer/harness
  changes. Future S09 tasks overlap S13 on `models.py`, migrations and
  `app/api/app.py`. The `prepare-s13-t01` worktree remains stale at
  `a43b20da742996bafcb2f9d1ac57b10d3f1a5204`.
- Next prompt is wait/preflight-only:
  `docs/pm/prompts/S13_POST_P00_STABLE_LANE_WAIT_MANAGER_2026-08-23.md`. It may
  not dispatch a worker. Codex must issue a later full-sprint prompt after S09
  writers exit and a current stable lane is verified.

### Live update — 2026-08-23 22:25 +07 (Codex re-review of actual C5)

- Actual integration HEAD is `ee10e55a809c84d5cb5d4a3046a1ee78828528d0` on
  `codex/s08-integration`; dirty source paths are attributed to S09/S11.
- S13-P00 C5 was independently checked: 22 task IDs/rows/nodes, lane hashes
  unchanged, and no P0/P1 structural finding remains.
- One P2 metadata finding remains: synthesis `READINESS_REPORT.md` still labels
  the current package `C4 revision`. Resume the exact synthesis owner
  `20260823_033031_3a5082` with the C6 metadata-only prompt; do not rerun lanes.
- Terminal state remains `S13-P00 = TASK_MANAGER_VERIFIED -> PENDING_CODEX_REVIEW`;
  `PRODUCTION_S13 = NOT_OPENED`; no S13 production dispatch.
- Next prompt: `docs/pm/prompts/S13_P00_C6_METADATA_CORRECTION_2026-08-23.md`.

## Trạng thái điều hành hiện hành — 2026-08-23 12:05 +07

### Live update — 2026-08-23 12:05 +07 (Codex direct review)

- Baseline tích hợp vẫn là `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`,
  branch `codex/s08-integration`, HEAD
  `a43b20da742996bafcb2f9d1ac57b10d3f1a5204`; dirty count quan sát là 266.
  Manager phải khám phá lại, không pin snapshot này thành sự thật vĩnh viễn.
- **S11-T01 APPROVED** sau Codex đọc trực tiếp engine/handler/tests và chạy lại
  full five-file suite: `64 passed` trong 240.58s, basetemp ngoài protected MAIN,
  `MOTIONFORGE_DATABASE_URL` unset. T01B/T01C/T01D không cần correction thêm.
  S11-T02..T06 vẫn `BLOCKED_DEPENDENCY` vì cần E06/S09 exit; chỉ readiness
  docs-only được phép chạy song song trước gate đó.
- **S09-T00 readiness package APPROVED làm input triển khai.** Codex cũng đọc
  trực tiếp sản phẩm T01 contract cũ và chạy lại 48/48 test. Giữ sản phẩm cũ
  làm nền, nhưng S09-T01 chưa hoàn tất contract Source-Locked hiện hành và phải
  resume đúng session `20260822_232748_b4b2ad` sau T00 implementation. Một
  Manager S09 mới được cấp quyền chạy trọn sprint T00 implementation → T06,
  theo task map/write-set trong prompt Codex 2026-08-23, rồi dừng một lần ở
  sprint gate.
- **S13-P00 CHANGES_REQUESTED**: synthesis dùng sai migration path
  `alembic/versions/**`, task packets quá lớn cho một session, còn đề xuất
  production `qa_stub.py`, và chưa khóa rõ isolated-test DB/network authority.
  Chỉ resume synthesis owner `20260823_033031_3a5082`; không rerun A/B/C và
  chưa mở production S13-T01..T08 cho tới Codex re-review correction.
- Các prompt manager chuẩn hiện hành được lưu dưới `docs/pm/prompts/` với ngày
  2026-08-23. Chỉ prompt đích danh được phép ghi đè trạng thái stale bên dưới;
  rules canonical vẫn là `HERMES_AUTOPILOT_RULES.md`.

### Live update — 2026-08-23 00:01 +07

- S09-T01 theo contract cũ đã thực sự chạy từ 23:27, process owner hiện ghi
  `proc_f24cb4aef494`; `output/s09/s09-t01/dispatch.log` còn tăng lúc 23:59.
  Worker đang ở pha phân tích/thiết kế và tại snapshot chưa thấy S09 production
  file mới. Phải gửi scope correction vào đúng Manager S09 hiện tại để yêu cầu
  worker dừng an toàn, giữ nguyên owner lineage và chuyển T01 về
  `BLOCKED_DEPENDENCY` trước khi chạy S09-T00.
- S11 correction round R6 đang chạy song song đúng owner: T01B session
  `20260821_160614_40b90e` xử lý F1+F3 và T01C session
  `20260821_214021_cbc36d` xử lý F2; T01D chờ Wave 2 cho F4. Không tạo session
  S11 thay thế và không gửi task mới vào các owner này.
- S13-P00 chưa chạy. Có thể mở Manager riêng sau khi S09-T01 cũ đã dừng an
  toàn. Manager mới phải audit tài nguyên và tăng số audit worker disjoint theo
  slot thực tế; không làm nghẽn heartbeat/liveness của S11/S09.

- Workspace tích hợp: `C:\Users\Admin\MotionForge2D-worktrees\s08-integration`,
  branch `codex/s08-integration`, HEAD quan sát gần nhất
  `a43b20da742996bafcb2f9d1ac57b10d3f1a5204`. Mọi Manager vẫn phải preflight
  lại HEAD/dirty tree/process thay vì coi snapshot này là khóa cố định.
- S07 Project Cast Reuse: **APPROVED** sau Codex review độc lập; focused/full,
  Playwright và vertical reuse gates đã xanh, không còn finding chặn S09.
- S08 Object Intelligence cùng bridge Source-Locked đã qua gate mở S07/S09.
  Review nền được lưu tại `docs/pm/reviews/S08_SPRINT_PM_REVIEW_2026-08-19.md`.
- S11-T01: **CHANGES_REQUESTED**. Correction phải resume đúng owner sessions
  T01B `20260821_160614_40b90e`, T01C `20260821_214021_cbc36d`, T01D
  `20260822_003041_b18319`; S11-T02..T06 vẫn `BLOCKED_DEPENDENCY` trên E06 và
  T01 Codex approval.
- S09: contract worktree tạo lúc 22:46 +07 đang lệch roadmap MAIN vì bỏ qua
  `S09-T00` và adaptive renderer/source-lock overlay. Tại snapshot 23:26 +07
  chưa thấy S09 output hay production file mới, registry còn ghi session T01
  “đang tạo”. Không cho T01 code tiếp theo contract cũ; phải realign và chạy
  S09-T00 trước, sau đó dừng ở Codex gate trước khi chốt T01..T06.
- Lane song song bổ sung được phép ngay: **S13-P00 readiness-only**, tối đa ba
  worker audit read-only song song rồi một worker synthesis; chỉ được ghi
  `output/s13-p00-readiness/<run-id>/**`. Không được viết production code,
  migration, test hay mở S13-T01 cho tới Codex review P00.
- Product backlog/target overlay chuẩn nằm ở MAIN `docs/pm/ROADMAP.md`. Bản
  roadmap cũ trong worktree không được dùng để hạ scope chuẩn.

## Vai trò cố định

- Codex là PM/reviewer: audit, quyết định gate và soạn prompt cho Hermes manager.
- Hermes Manager chỉ preflight, dispatch, monitor, review và report; Manager
  không tự sửa production code/test/migration/UI/config. Worker session riêng
  mới là implementation writer.
- Codex không tự chạy Hermes khi người dùng đã có Hermes quản lý; chỉ khởi chạy
  nếu người dùng cho phép rõ ràng.
- Hermes chỉ được kết thúc task ở `TASK_SUBMITTED`/`TASK_MANAGER_VERIFIED` và
  sprint ở `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`. Chỉ
  Codex được ghi `APPROVED`.

## Khôi phục trạng thái trước mọi hành động

1. Đọc `docs/pm/SESSION_PROTOCOL.md`, `docs/pm/README.md`, roadmap, TASK/LOG/
   REPORT/PM_REVIEW của task liên quan và automation state.
2. Kiểm tra tất cả worktree, branch, `git status --short`, process Hermes/watcher,
   session ID và log đang tăng hay đã ổn định.
3. Nếu Hermes writer còn chạy: Codex hoàn toàn read-only; không sửa tài liệu,
   không chạy quality gate và không review giữa chừng.
4. Không tự suy ra “task mới nhất”; xác định Task ID, worktree và exact session
   từ filesystem/evidence.

## Task và Hermes session lifecycle

- Một Task ID = một session folder = một Hermes chat/session.
- Task ID mới phải dùng Hermes session mới.
- Cùng Task ID bị `CHANGES_REQUESTED` phải resume đúng stored session ID; không
  mở fresh session. S05-C04 từng vi phạm điều này ở R2/R3 — không lặp lại.
- Session đã APPROVED/CLOSED không được nhận Task ID mới.
- Không mở task kế tiếp cho đến khi task cũ: writer thoát, REPORT SUBMITTED,
  Codex review APPROVED và trạng thái CLOSED.
- Automation state có thể cũ do launcher thủ công; phải reconcile trước khi dùng.
  Không dùng “most recent session” ngầm định.

## Parallel work

- Chạy tối đa các task dependency-ready đã được Codex/BA cấp quyền và có
  exclusive write-set cùng runtime resources không giao nhau. Watcher/read-only
  reviewer không được tính là production writer.
- Mỗi Task ID vẫn có exact owner session riêng. Cùng worktree chỉ được chạy
  song song khi prompt chứng minh disjoint cả file/API/schema/migration/fixture,
  database/temp/output/port/cache; global gate phải qua mutex ở checkpoint ổn
  định. Nếu không chứng minh được thì serialize hoặc dùng worktree riêng.
- Không dùng parallel để né Codex sprint gate hoặc dependency chưa APPROVED.

## An toàn tuyệt đối

- Không commit/push/deploy/merge/reset/checkout/restore/clean/stash/delete nếu
  chưa có quyền rõ ràng.
- Bảo vệ `channels.json`, mọi `data/`, database, fixture, user data, backup,
  evidence cũ và dirty changes. Không overwrite QA run/screenshot cũ.
- Mọi test/runtime phải dùng root/database/evidence directory mới và cô lập.
- Không sửa PRD, Master Plan, roadmap hoặc task contract từ Hermes; PM sở hữu.
- Không skip/ignore/nới assertion để làm xanh gate.

## Cấu trúc prompt giao Hermes manager

Mỗi prompt phải nêu: Task ID + exact worktree + new/resume exact session; hard
worktree guard; required reading; outcome; findings/AC nhị phân; allowed write
scope; forbidden scope; protected-data baseline; validation tách riêng; evidence
cần append; stop conditions; và `SUBMITTED only`.

Nếu là correction, prompt phải giữ nguyên lịch sử LOG/REPORT, append correction
round, sửa toàn bộ finding hữu hạn và resume exact session. Nếu phát sinh nhu
cầu ngoài scope, Hermes dừng `BLOCKED` để PM quyết định.

## Review gate của Codex

Chỉ review sau khi writer thoát và tree ổn định. Thứ tự: scope → acceptance →
architecture/domain → data/migration → tests/evidence → UX → regression.
Đọc code/diff trực tiếp; không tin riêng REPORT. Chạy lại gate độc lập theo rủi
ro, kiểm tra protected hash, new run ID, screenshot và isolation. Ghi PM_REVIEW
với decision, timestamp, reviewed tree, session ID và Quality Run ID.

Script `.ps1`/`.sh` không phải module Python nên không chạy trực tiếp bằng
pytest. Kiểm tra phù hợp là PowerShell Parser, `bash -n`, functional smoke và
regression Python liên quan.

## Chế độ thực thi sprint do người dùng yêu cầu

- Codex chuẩn bị/duyệt sprint contract, dependency graph, task packets, worktree
  và protected-data baseline trước khi giao việc.
- Một Hermes manager điều phối TOÀN BỘ sprint. Mỗi Task ID con vẫn phải dùng một
  Hermes coding session riêng; manager không biến cả sprint thành một session
  writer duy nhất và không tái sử dụng session đã đóng cho Task ID khác.
- Manager được tự review từng task sau khi writer thoát: audit diff/scope, chạy
  targeted + regression gates, yêu cầu correction bằng cách resume đúng session
  của Task ID đó, rồi mới mở dependency kế tiếp.
- Việc manager tự review chỉ là internal gate, không phải Codex `APPROVED`.
  Trong lúc sprint chạy, task hoàn tất giữ trạng thái
  `MANAGER_VERIFIED_PENDING_SPRINT_REVIEW`/`SUBMITTED`; Hermes không ghi PM
  approval.
- Manager chạy đến hết sprint, tạo sprint-exit report, fresh 7/7 baseline,
  integration/Playwright/visual evidence theo scope, protected-data comparison
  và danh sách mọi correction/session ID. Sau đó dừng toàn bộ writer ở
  `SUBMITTED` và gọi người dùng/Codex review MỘT LẦN ở sprint exit.
- Codex không theo dõi/poll khi sprint đang chạy. Chỉ review khi người dùng báo
  Hermes đã xong; Codex có thể APPROVED toàn sprint hoặc trả một correction
  packet hữu hạn cho manager xử lý trong cùng sprint.
- Parallel trong sprint chỉ dành cho task độc lập: dependency đã mở, worktree +
  session + write scope riêng, không chia sẻ mutable QA/database/output. Manager
  phải serialize mọi integration hoặc scope giao nhau.
- Không bắt đầu sprint mới trước khi sprint hiện tại được Codex APPROVED/CLOSED.

## Snapshot lịch sử 2026-08-05 — đã bị trạng thái 2026-08-22 ở trên thay thế

- S05-C04 và Sprint S05: APPROVED/CLOSED.
- Reviewed Hermes submission: `20260805_210521_ead0fd`.
- Fresh quality baseline: `20260805-214242`, 7/7 PASS.
- Codex independent targeted suite: 41/41 PASS.
- Protected MAIN `channels.json` SHA-256:
  `DD7AAE26096902EFF74986B36554957D87EB8E60C5E8FF8048064C31655EB555`.
- S06-T01..T04 đã APPROVED. S06-T05 packet đã tồn tại với trạng thái
  APPROVED trong worktree `s06-t01-review`; baseline `20260805-091121` 7/7
  PASS, focused Playwright 8/8. Sprint S06 hoàn tất về product gate. MAIN và
  một số packet/worktree còn snapshot cũ/bản sao incident; phải reconcile bằng
  thao tác không phá hủy trước integration, nhưng không chạy lại S06-T05.
- Các sprint đã hoàn tất về product gate: S00, S01, S02, S03, S04, S05, S06.
- Sprint sản phẩm tiếp theo theo dependency core là S08. S07 vẫn chờ E05/
  ObjectRole contract từ S08; không chạy S07 trước contract này.

Trạng thái trên chỉ là snapshot. Session mới luôn phải kiểm tra lại filesystem
và process trước khi tiếp tục.
