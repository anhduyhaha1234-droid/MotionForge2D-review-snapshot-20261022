# RULES — Viết prompt cho Hermes/Codex Manager

> Đây là **nguồn quy tắc duy nhất (canonical)** để Codex viết prompt điều phối Hermes Manager hoặc một Codex Manager mới cho dự án MotionForge2D.
>
> Không được viết prompt quản lý dựa trên trí nhớ, bản tóm tắt cũ hoặc một prompt cũ. Phải đọc lại **toàn bộ file này từ đầu tới cuối trong chính lượt làm việc hiện tại**.

## 0. Chế độ hiện hành — tuần tự và Codex review từng microtask (30/09/2026)

Chỉ thị mới nhất của người dùng: tách nhỏ việc, review độc lập rồi mới sang việc
tiếp theo để tránh làm trùng/chồng chéo. Mục này thay thế quyền chạy song song
trong §1.3, §2.1, §6, §8.1 và quyền tự mở dependency sau Manager verify trong
§3, cho tới khi người dùng đổi chế độ. Các yêu cầu an toàn khác vẫn giữ nguyên.

- WIP=1: Manager và tối đa một owner đang thực thi một microtask, kể cả demo,
  feasibility hoặc integration. Core/tool/demo vẫn là ba nhóm trách nhiệm.
- Các microstep thuộc Task ID cũ phải resume exact owner; không tạo session
  mới cho từng chỉ số T001–T049. Task ID mới chỉ khi scope thật sự mới.
- Writer dừng → Manager kiểm scope/tests/evidence → frozen candidate → Codex
  review độc lập. Chỉ verdict Codex cho đúng bytes và đúng microtask mới cấp
  quyền bước kế. Manager không tự đi tiếp dù tests xanh.
- Nếu cần tích hợp, Codex cho phép exact transport của candidate đã review;
  integration owner riêng thực hiện, không sửa tay; Codex xác minh transport
  trước khi mở implementation kế tiếp. Không gộp nhiều task chưa review.
- Khi chờ Codex, dừng dispatch và model polling. Không dùng slot rảnh để mở
  việc khác. Liveness/retry chỉ áp dụng khi còn task được phép active.
- Approval microtask không đóng Task ID cha, M1–M7 hoặc sprint. Parent giữ
  NOT_APPROVED/NOT_CLOSED tới khi đạt toàn bộ acceptance tương ứng.
- Roadmap là bản đồ phụ thuộc; prompt chỉ cấp một microtask cụ thể cùng
  preflight/verification cần thiết. Các bước sau BLOCKED_DEPENDENCY.
- User bổ sung: ưu tiên tích hợp repo/node/workflow tương đương trước khi tự
  viết lại thuật toán; mỗi task liên quan có reuse decision và proof. Không
  tự cài toàn shortlist hoặc mở thêm scope chỉ vì repo tồn tại.
- Lịch sử01–05/10, đã bị §0.4 thay thế: prompt từng pin model-call/deadline/correction
  limits và guard thực. Budget cụ thể mới nhất thắng retry vô hạn ở §7;
  không reset counters bằng resume/run/session mới. Phân biệt hard limit được
  runtime thực thi với ngân sách request chỉ quan sát; không bịa capability
  hoặc chặn việc chỉ vì thiếu một limiter không được task yêu cầu xây.
  Hết ngân sách theo loại đã pin thì nộp partial cùng bằng chứng, không nới AC.
  Chờ Codex không polling model.

### 0.1. Quyền tự xử lý trong một task — cập nhật user 01/10/2026

User yêu cầu nới quy trình để hoàn thành công việc, không dừng sau một thao tác
lỗi rồi đẩy lại Codex. Các quyền sau áp dụng trong outcome/write-set đã giao;
không tự mở task kế hoặc bỏ review chất lượng:

- Worker được đọc, chia nhỏ patch, sửa từng hàm/test, chạy focused test, sửa lỗi
  vừa phát hiện và tiếp tục tới acceptance trong cùng task. Một patch, một tool
  call, một process exit hoặc một lỗi test không phải một microtask mới.
- Allowlist giới hạn đường dẫn/nội dung được sửa, không giới hạn số patch hoặc
  kích thước tổng của file. File lớn được sửa qua nhiều bounded patch có
  preimage theo §8.2.1, không cần xin quyền chia patch.
- Manager được chọn phương pháp ghi an toàn khác, cập nhật compact worker
  packet và resume exact owner khi đã xác nhận writer cũ terminal. Prompt pin
  một cửa sổ thực thi đủ cho task, số continuation và budget/deadline dùng chung.
  Không coi mỗi technical continuation là một correction mới cần Codex mở lại.
- Khi prompt không quy định khác, tối đa 3 technical continuations sau dispatch
  đầu tiên trong cùng task window. Không tự tăng ngân sách hoặc reset đồng hồ;
  ghi remaining budget trước mỗi resume. Hai lần cùng lỗi với cùng cách làm,
  không có hypothesis/method/test delta thì dừng cách làm đó. Được chuyển sang
  một biện pháp đã nêu rõ trong packet và thử có giới hạn; không blind retry.
- Truncation/output lỗi: ưu tiên rút payload/chia patch, không viết lại toàn
  file. Effective output limit chỉ được đổi cho process/task khi runtime có
  setting đã kiểm chứng, trong mức model/router thực chấp nhận; log trước/sau.
  Metadata advertised không chứng minh limit thực. Không sửa global runtime,
  router hoặc model config của các session khác để chữa task này.
- Manager được viết harness điều phối/QA và evidence trong RUN đã cấp; worker
  được viết scratch/patch fragments tại RUN/tasks/<task> theo packet. Đây không
  phải quyền Manager viết production/tests hay chép candidate đè source.
- Reuse evidence trên đúng hash; chỉ chạy lại phần ảnh hưởng sau code delta.
  Không lặp full preflight, broad gates, manifest và báo cáo chỉ vì resume.
  Theo §0.4 hiện hành, chỉ submit terminal khi acceptance đạt, user yêu cầu dừng
  hoặc có blocker thật ngoài quyền; không kết thúc vì hết budget/continuations
  tự đặt. Sau submission vẫn chờ Codex.

### 0.2. Ưu tiên video mẫu WAN trước tool — user cập nhật 02/10/2026 (SUPERSEDED bởi §0.3)

> SUPERSEDED05/10/2026 bởi §0.3: vòng tối đa10 sản phẩm mẫu/12s thuộc prototype02/10
> đã hết window (deadline09:23:39Z02/10); không dispatch lại. Packet hiện hành là
> MF-DEMO-LONG-01 (PROPOSED_ONLY) cho scope full nguồn22:01.

Người dùng yêu cầu làm sản phẩm mẫu media thành công trước rồi mới tích hợp lại
tool; Hermes được tự xem bằng vision, tự xử lý và thử tối đa 10 sản phẩm, dừng
sớm khi đạt để Codex review một lần. Mục này thay thứ tự M1-first và yêu cầu
Codex duyệt giữa từng render attempt đối với đúng thử nghiệm được pin trong
`outputs/mf-shotwise-demo-20261002/NEXT_HERMES_DEMO_PROMPT.md`.
Packet02/10 thay packet01/10 trong cùng prototype, không mở lại budget/deadline
nếu đã dispatch. Phân biệt shot nguồn với render chunk: được chia cảnh thành
các đoạn nhỏ có frame map/context/trim rõ, giữ người đang tương tác cùng cảnh,
ghép đủ timeline/tiếng gốc. Chỉ chạy lại vùng lỗi và continuation phụ thuộc;
kiểm mối nối trước submission. Tối đa10candidate vẫn tính toàn prototype.

- Mở một task media prototype thuộc owner demo hiện có. WIP=1, GPU=1; M1/UI,
  integration, S12/package tạm hoãn theo ưu tiên user, giữ nguyên bytes/state.
- Được dùng source ngắn có sẵn → transcript lời nói và sự kiện hình ảnh → cast
  cố định → ảnh cảnh đích qua ComfyUI → WAN sinh lại từng đoạn với driving nguồn
  → ghép tiếng gốc → vision/QC. Giữ sát action/camera/timeline; text-only không
  tự thay dữ liệu chuyển động. WAN là video engine được user chỉ định.
- Được chạy headless ComfyUI và harness media trong RUN cô lập, không cần chờ
  UI/library/public API hoàn thiện. Đây là phép thử sản phẩm mẫu, chưa phải proof
  tool vận hành đầu cuối. Không tạo database/queue/service sản phẩm song song.
- Tối đa 10 candidate version, tính cả bản lỗi/partial và lần thử GPU thất bại;
  không reset counter hoặc giấu thử nghiệm dưới tên smoke. Mỗi candidate có log
  đầu vào, graph/settings, file media, vision/QC, hypothesis và delta; sửa phần
  bị ảnh hưởng, tái dùng phần giữ nguyên có provenance. Prompt pin giới hạn
  image jobs, từng unit submit, model calls và deadline dùng chung.
- Worker/Manager được tự kiểm ảnh cảnh và clip bằng công cụ vision đã kiểm
  capability thực. Không có hình/video input thật thì không ghi đã xem. Kết luận
  của vision là evidence tự kiểm, không thay reviewer độc lập hoặc waive UNKNOWN.
- Dừng sớm khi đủ acceptance, giữ best candidate theo tiêu chí đã pin, nộp
  `SELF_REVIEW_PASS_PENDING_CODEX`; nếu chưa đạt ở trần hoặc blocker thật thì
  nộp best-so-far và lỗi còn lại. Không cần dùng hết 10. QUALITY_ACCEPTED=0 và
  sprint NOT_APPROVED/NOT_CLOSED tới verdict Codex, không tự tích hợp sau demo.
- Đây là quyền user giao qua prompt. Codex không tự launch/message Hermes.
  Các quyền patch/continuation trong §0.1 giữ hiệu lực trong outcome đã cấp.

### 0.3. Chốt một phong cách và dựng video dài — user cập nhật 05/10/2026

User yêu cầu chọn một phong cách từ demo đang có, đặt target video dài và không
tiếp tục nhiều vòng thử mẫu. Đồng bộ xuyên suốt đầu-cuối video là ưu tiên cao nhất.

- Hướng đã chọn: 2D minh họa như nhân vật nam cuối proof assembly v1.3; một style
  và một bộ cast/props có identity cố định cho toàn video/series. Chấp nhận hướng
  mỹ thuật không có nghĩa mọi lỗi action/cast/audio của demo cũ đã được nghiệm thu.
- Target hiện hành là trọn nguồn 22:01, SHA256
  `5a175454c2c2965bac5013a53926e210a9f70a185d802d0f2e0083a6fb399fa2`.
  Không dùng việc hoàn tất thêm nhiều phiên bản 12s làm dependency mới trước target dài.
- Một bản dựng chính, xuất checkpoint là các đoạn thật của bản dài; chỉ sửa vùng
  lỗi cụ thể và continuation phụ thuộc. Không seed/style sweep hoặc 10 bản toàn clip.
- Cast/props/style, trạng thái hành động, contact/occlusion, camera, cuts/frame map
  và audio timeline phải đồng bộ toàn master; kiểm seam và drift đầu/giữa/cuối.
  Unit pass không thay full-video pass. Giữ audio tail gốc; không gọi chênh duration
  vốn có ở nguồn là drift mới hoặc tự cắt tiếng để khớp một con số.
- Prototype02/10 đã hết window: giữ owner/RUN/ledger/counters lịch sử, không reset.
  Full-source là scope mới MF-DEMO-LONG-01 với một owner mới theo §4; chỉ dispatch
  khi user giao packet scope mới rõ ràng; chính sách budget theo §0.4. Không dùng tên task mới
  để che chi phí cũ. Codex vẫn không tự launch/message Hermes.
- Bổ sung05/10: dependency "thử thêm mẫu12s" đã bị thay. Packet MF-DEMO-LONG-01
  thay thế; không coi mẫu12s, gia hạn6h hay further-proof-12s là gate trước target
  dài. Video/ví dụ12s cũ chỉ còn là tham chiếu kỹ thuật, không là current source.
- Một main assembly, sửa vùng lỗi và continuation phụ thuộc tới khi đạt. Chính
  sách06/10 tại §0.4 đã bỏ trần10candidate/một vòng sửa/window tự đặt; vẫn ghi
  mọi attempt và chi phí, không reset ledger. Tool/UI/integration/S12/S13 vẫn
  chờ evidence và Codex gate.

### 0.4. Bỏ budget tự đặt, tiếp tục đến hoàn thiện — user cập nhật06/10/2026

User yêu cầu: "từ sau bỏ giới hạn budget cho nó làm hoàn thiện nhé bị limit nên
nó dừng giữa chừng". Chính sách này có hiệu lực cho task đang làm và các prompt
MotionForge tiếp theo; thay mọi numeric budget/deadline/continuation/correction
cap cũ trong §0–§0.3 và các packet trước, trừ khi user đặt lại giới hạn rõ ràng.

- Không áp trần thời gian tổng, model calls/tokens/chi phí, candidate, image/video/
  vision submissions, vòng sửa hoặc technical continuations do PM/Manager tự đặt.
  Không kết thúc vì 6h/48h, 10candidate, 300/60calls, initial+3 hoặc LIMIT_REACHED.
  Giữ đầy đủ counts/chi phí/receipts, kể failed/OOM/retry và UNKNOWN; ledger để
  quan sát, không phải stop gate. Lưu deadline cũ là lịch sử, không sửa receipts cũ.
- Tiếp tục render/kiểm/sửa/resume trong scope đã giao tới acceptance; không cần
  xin thêm budget mỗi lượt. Khi đạt thì nộp review và dừng. Chỉ tạm dừng khi user
  yêu cầu, blocker thật cần input/quota/quyền ngoài task, hoặc incident an toàn.
  Không tự mở task/goal/model/paid resource mới; owner/write-set/quality gates giữ.
- Nếu task đã dispatch, resume đúng owner/RUN/checkpoint; không tạo lại task hay
  render lại phần đạt. Bỏ cap không phải reset counters hoặc xóa evidence lịch sử.
- Giới hạn một invocation (max-turns/output/context) không là terminal của task:
  checkpoint, xác nhận writer cũ terminal rồi Manager resume đúng owner. Payload
  bị cắt thì chia nhỏ tool arguments/patch; không gửi lại nguyên payload quá dài.
  Chỉ dùng setting unlimited khi schema runtime thực hỗ trợ; không đoán0/-1,
  đặt số cực lớn hoặc sửa global router/model để giả vờ bỏ limit của provider.
- Manager được patch harness/registry/packet của mình trong RUN để bỏ stop gate
  budget tự đặt; snapshot trước, ghi policy change, không đổi schema null tùy ý.
  Chỉ báo đã áp dụng runtime khi đã kiểm consumer. Không kill job đang tiến triển
  để đổi policy. Request timeout/liveness audit và GPU1 vẫn giữ để phát hiện treo.
- Lỗi tạm thời: backoff5phút, audit/resume theo §7, không cap số chu kỳ. Quota/
  credit/auth hoặc hard limit provider thật thì giữ checkpoint và báo đúng blocker;
  không gọi đó là budget PM và không tự mua thêm hay đổi route.
- Không blind retry: hai lần cùng phương pháp không tiến bộ thì đổi giả thuyết/
  chia việc dựa trên evidence, tiếp tục phần độc lập; không seed/style sweep.
  Checkpoint/heartbeat có tiến độ thật; giữ WIP1/GPU1, cast/style/timeline/audio
  xuyên video và sửa dependency/seam. Codex vẫn không launch/message Hermes.

### 0.5. Ưu tiên identity; correction 5 phút — user cập nhật08/10/2026

User nhận W7 full22phút nhưng thấy nhân vật chưa đồng bộ, yêu cầu review/research
và cho phép test5phút để tăng tốc. Overlay này thay yêu cầu tiếp tục full ngay
trong §0.3; không thay goal full, quyền sở hữu hoặc policy không budget §0.4.

- W7 CHANGES_REQUESTED: master đủ39634frames/decodeclean nhưng có sai identity,
  actor count và motion. Không coi nhãn MINOR hoặc số lần đã sửa là acceptance.
- Correction cùng Task MF-DEMO-LONG-01/RUN20261005T1643Z-wan-long; recovery
  worker20261007_234033_cc0b6d, Manager tại08/10 là20261007_231246_986005
  (current Manager theo§0.7). Kiểm context/zero-writer
  trước resume; không resume W2r cũ, không fresh session nếu chưa đủ rules§4.
- Chỉ mở pilot nguồn01:34–06:34, frames[2820,11820),9000frames30fps/300s;
  S0021–S0074. Giữ style/cast toàn phim, audio/cuts/actions/camera từ nguồn.
  Lập global entity map từ evidence sẵn có, chưa render lại full22phút.
- Áp dụng storyboard có actor ID/mask/occlusion/contact, cast assets cố định và
  compositing2D có kiểm soát; WAN cho motion theo gate. Không chỉ tăng prompt/
  seed/ref-strength rồi sinh lại toàn cảnh. Không đổi framework/modelroute.
- Các bước sửa/kiểm trong pilot thuộc cùng owner, tự tiếp tục đến submission;
  không cần Codex gate giữa mỗi ảnh/render. Một frozen pilot đủ5phút + comparison
  nguồn/W7/mới phải được Codex review trước khi mở full hoặc tool/integration.
- FrozenW7/source/style/oldreceipts bảo toàn. Correction ghi revision mới theo
  write-set packet; WIP1/GPU1. Codex vẫn không launch/message/resume Hermes.
- QUALITY_ACCEPTED=0, codex_accepted=0; S12/S13 NOT_APPROVED/NOT_CLOSED.

- Cập nhật Codex review C2 tối08/10: pilot300s CHANGES_REQUESTED; identity,
  count/action/camera vẫn sai và có regression. Gate hash bị bypass bởi cùng ảnh
  sai re-encode, ảnh trắng và sai cast; masks rỗng,54tracks cònTBD. Correctionr3
  phải có semantic negative controls và proof masks/tracks/asset layers thực sự
  được renderer tiêu thụ trước batch. Không waive transientactor/phone/camera.
  C1/C2 frozen; cùngTask/RUN/owner, context audit§4, policy§0.4 khôngbudget giữ.

Packet C2 lịch sử (đã được §0.6 thay thế):
`C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-c2-review-20261008/NEXT_HERMES_MANAGER_PROMPT.md`.
User tự giao Hermes; có REVIEW_VI, RESEARCH_UPDATE, CORRECTION_MATRIX và
SESSION_OPENING_PROPOSAL cùng thư mục. Không reset counters hoặc áp cap cũ.

### 0.6. Reuse upstream và thay mặt rõ ràng — user cập nhật09/10/2026

User yêu cầu lấy repo có công nghệ đã triển khai để áp dụng, không tiếp tục tự
viết công nghệ sửa video; đồng thời chọn một bộ khuôn mặt khác rõ nguồn.
CAST B được reviewer chọn trong packet dưới, thay cast identity cũ; style2D,
motion/camera/cuts/audio và mục tiêu5phút của §0.5 vẫn giữ. Wardrobe/view là
state của người, không tự tạo ID mới. Board chỉ là concept, cần views/assets
đúng cùng identity và source entity audit trước render.

R3D master b8534eaa…ef0 đủ9000frames nhưng CHANGES_REQUESTED: actor/props/
occlusion sai, dán sprite/fill cố định tạo regression; palette gate bị fresh
repro bypass; receipt nhận nhầm PASS trong câu kế hoạch. Không waive MINOR.
Ưu tiên Rerender_A_Video standalone propagation trên keyframe đã khóa; MoCha
workflow sẵn là fallback có điều kiện. Không viết flow/render/tracking core
mới. Chỉ adapter/provenance/QA và compatibility patch tối thiểu. Repo có mã
không đồng nghĩa đã chứng minh12GB/cartoon/5phút; cần output thật trên nguồn.
Giữ license; internal evaluation không là clearance phát hành thương mại.

Source upstream đã tải trong reviewer packet, chưa cài/build/inference.
Correction ghi C/r4; W7/C1/C2/R3 frozen. Cùng Task/RUN/exact owner, context
audit theo§4, WIP1/GPU1, noPMbudget/counters giữ. Full22phút/tool/integration
vẫn chờ Codex. User tự giao Hermes; Codex không launch/message/resume.

User bổ sung yêu cầu áp dụng repo cho các thành phần đang lỗi và tăng hiệu quả
Hermes Manager. Bản hoàn tất11/10 giữ cùng r4/Task/RUN/owner: sửa reference
binding FLUX.2 đang cài; SAM2 per-object masks; Rerender standalone propagation;
CoTracker cho contact khó, ProPainter khi cần clean plate. VBench chỉ là QA
bổ trợ. Không gọi tải repo/cài model là đã áp dụng đạt; phải có source-unit và
pilot output thật, hash/command/resource measurements. Giữ licenses và GPU1.

Manager tái dùng native todo/compression/process tracking cùng Pydantic,
psutil/filelock đã cài. Terminal JSON phải gắn đúng invocation/owner/packet
và artifacts; không parse PASS trong prose. Controller lock không thay GPU
lease còn sống khi child detached chạy. Không thêm framework orchestration,
không đổi global config, không dừng task ở technical invocation limit.

Packet R4 lịch sử trước Codex review (được §0.7 thay thế):
`C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-r4-stack-update-20261009/NEXT_HERMES_MANAGER_PROMPT.md`.
Kèm STACK_DECISION_VI, SESSION_OPENING_PROPOSAL, source lock và terminal
contract reference đã kiểm25ca cô lập; live consumers chưa được patch.
CAST_B_SPEC/board, review và CORRECTION_MATRIX12rows kế thừa packet r3-review
09/10 theo đường dẫn trong prompt. User tự giao Hermes; Codex chưa dispatch.
QUALITY0,codex_accepted0,S12/S13NOT_APPROVED/NOT_CLOSED.

### 0.7. R4 đã nộp nhưng CHANGES_REQUESTED; correction R5 — 11/10/2026

Codex kiểm master77fc6122…6209: đủ9000decodedframes/300s/30fps/640×360,
decode sạch, nhưng vẫn đổi mặt trong shot, tráo vai, mất người/props/contact,
có ghost và13shots source passthrough74.933s. Xem54midpoint và88cặp temporal;
không tuyên bố đã xem/nghe liên tục toàn clip. Matrix độc lập9FAIL+2UNKNOWN+
1PASS engineering. Self-QC12PASS không thay acceptance. R4 frozen.

Actual Manager hiện hành20261011_123932_c101dc, exactworker20261007_234033_cc0b6d;
Manager trong§0.5 là lịch sử. Cùng Task/RUN/counters, revisionR5 mới; không tự
mở task/worker mới. Context/zero-writer/lease audit§4 trước continuation. R4e
đã nộp; lần dừng hiện tại chờ Codex review, không phải budget. User tự giao
prompt; Codex không launch/message/resume hoặc đổi registry.

R5 sửa graph fallback giữ CAST refs, actor ledger/storyboard theo source events,
clerk/occlusion/contact và QA trên final frames. Áp dụng upstream CropAndStitch
cho key edit từng actor (pin/source/tests trong packet); SAM2 masks đủ coverage;
Rerender propagate keys đã đạt; CoTracker contact chạy thật. Thử VACE1.3B đã có
model/node local trên S62/S73 cùng nguồn để so với route Rerender đã sửa, chỉ
chọn route đạt. MoCha fallback có bằng chứng; ProPainter chỉ khi cần clean plate.
Không viết core mới/cài framework lại. 74 CropAndStitch tests và outside-mask
probe đạt chỉ là component proof; VACE chưa có source-unit inference proof.

Manager sửa actual dispatch/heartbeat/lease: active/detached/UNKNOWN chặn writer
mới, terminal phải bind dispatch hiện hành và artifact hashes; LLM silence
không tự kill batch còn tiến triển. Test cô lập không launch Hermes thật.
Giữ provider/modelroute đã chốt; WIP1/GPU1, noPMbudget theo§0.4. Pilot5phút,
CAST B/style và full22/tool/integration BLOCKED_DEPENDENCY theo§0.5 giữ nguyên.

Packet hiện hành và prompt hoàn chỉnh:
`C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-r4-review-20261011/NEXT_HERMES_MANAGER_PROMPT.md`.
REVIEW_VI, NEWTECH_DECISION_VI, CORRECTION_MATRIX12rows và matching
SESSION_OPENING_PROPOSAL cùng thư mục. Worker write-set chỉC/r5 và D/input,
output,temp/identity5m_20261008/r5; Manager chỉRUN/manager cho harness. Existing
files patch-only/preimage; prior media/evidence/source/style/CAST, production/
tests/DB và global runtime read-only. QUALITY_ACCEPTED=0,codex_accepted=0;
S12/S13NOT_APPROVED/NOT_CLOSED. TASK_SUBMITTED chỉ cấp pending Codex review.

### 0.8. R5 CHANGES_REQUESTED; R6 correction và Codex handoff — 12/10/2026

Overlay này thay current execution của§0.7; các trạng thái R4/R5 trước review
ở trên là lịch sử. Codex review master b8b9a404…272d: đủ9000decodedframes/300s,
nhưng identity/role/pose/contact FAIL và regression thêm người S33/S61, tài liệu
thành người S74. Matrix10FAIL+1UNKNOWN/PARTIAL+1PASS engineering. Sampling54
midpoints+106temporal pairs; chưa xem/nghe liên tục. QUALITY_ACCEPTED=0,
codex_accepted=0, S12/S13NOT_APPROVED/NOT_CLOSED; full22/tool/integration blocked.

Current Manager20261012_002032_daa36c, worker20261007_234033_cc0b6d; Manager
20261011_123932_c101dc là lịch sử. R5e nộp chờ review, không evidence budget-stop.
Cùng MF-DEMO-LONG-01/RUN/counters; R6 chỉ artifact revision. Context/incident/
zero-writer audit§4 trước continuation, không đổi owner chỉ vì revision/session.
No PM total budget/deadline/candidate/call/continuation cap§0.4 giữ nguyên.

Áp dụng upstream đã có đúng call path: source ledger/visible actor/pose trước
gen; CropAndStitch phải dùng đúng upstream stitch, không chỉ crop rồi custom
alpha blend. VACE trial R5 thiếu TrimVideoLatent: sửa official reference graph
và paired S62/S73 trước chọn engine; không gọi model ceiling hoặc cắt4decoded
frames. CoTracker paired windows; event keys đúng thời điểm. Semantic gate
artifact-bound vào key/propagate/assemble/submit, cache hash exact input bytes.

Fresh harness51/51 cải thiện nhưng true-race barrier proof còn thiếu. Có16
frozen R4 evidence files drift và stale R5d terminal trong nested manifest.
Giữ evidence/before-after hashes, append reconciliation mới; không restore/
backdate/refresh lịch sử để che mismatch. Packet cấp một guarded continuation
sau preservation/output isolation; nếu là scope violation thứ hai trong cùng
lineage, áp dụng owner-transfer review§4. Không reset incident count.

Worker write-set chỉ C/r6 và D/{input,output,temp}/identity5m_20261008/r6.
Manager ghi evidence/packets/receipts/logs mới cho r6; live harness/current
coordination patch-only hoặc append có guard. Old manager evidence/receipts/
terminals/packets frozen, generic manager/** không waive. MAIN/INTEGRATION,
production/tests/DB/global runtime/source/style/CAST/W7/C1/C2/R3/R4/R5 protected.
Giữ pilot5phút/CAST B/flat2D/WIP1GPU1. User tự giao Hermes; Codex không dispatch.

Packet review và complete prompt hiện hành:
`C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-r5-review-20261012/`.
Đọc REVIEW_VI, CORRECTION_MATRIX, TECH_DECISION_VI, SESSION_OPENING_PROPOSAL và
NEXT_HERMES_MANAGER_PROMPT. NEXT_CODEX_SESSION_PROMPT cho phiên reviewer mới.
Các bước nội bộ sửa/excerpt/QA tiếp tục đến pilot đủ contract hoặc blocker thật;
không TASK_SUBMITTED khi P1/UNKNOWN còn mở, không chuyển chúng khỏi remaining_work.

### 0.9. Đối chiếu tài liệu công nghệ và chuẩn hóa R6 — user 12/10/2026

User yêu cầu đọc tài liệu chính thức và áp dụng đúng từng công nghệ, có bằng
chứng. Technical packet hiện hành: `C:/Users/Admin/Documents/Codex/2026-10-02/ti-p-qu-n-d-n/outputs/motionforge-tech-conformance-20261012/`.
Đọc TECHNOLOGY_AUDIT_VI.md, TECH_CONFORMANCE_MATRIX.md; dùng complete
NEXT_HERMES_MANAGER_PROMPT.md và SESSION_OPENING_PROPOSAL.md trong packet này.
Packet R5 review trước giữ frozen, verdict10FAIL+1UNKNOWN+1PASS không đổi.

- Giữ cùng task/RUN/owner/counters, CAST B/flat2D/pilot5phút, WIP1/GPU1,
  no PM total budget; QUALITY0/S12/S13 chưa approved/closed; full22/tool blocked.
- FLUX4B distilled4steps/Euler/CFG1 đúng baseline; lỗi integration/semantic
  không chữa bằng nâng steps/model mù. Rerender mới stage2, không claim stage1.
- SAM2 phải ghi đúng revision; guard thêm R4 tracks/masks. Canonical mask
  canvas/frame map và exact consumed hashes; không fallback mask theo vị trí.
- Crop+stitch upstream phải trong actual path; VACE trim reference latent
  trước decode; CoTracker paired windows và lưu raw visibility; gates/cache
  fail-closed. T01–T15 map vào Q01–Q12, không reset acceptance hoặc incidents.
- ASR/cuts frozen:224/224 candidates được giữ; chưa có proof mất cut. Hermes
  installed0.19 source controls compatibility, không áp latest tool names mù.
- Docs/clone/unit tests không chứng minh video đạt. User tự giao Hermes;
  Codex reviewer không launch/message/resume hoặc sửa runtime trong audit này.

### 0.10. R6f đã chạy, checkpoint CHANGES_REQUESTED — Codex 14/10/2026

Current packet: `C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-r6-checkpoint-review-20261014/`.
Đọc REVIEW_VI, CORRECTION_MATRIX, complete NEXT_HERMES_MANAGER_PROMPT và
matching SESSION_OPENING_PROPOSAL. Prompt này thay execution prompt§0.9;
technical requirements T01–T15 và canonical Q01–Q12 vẫn giữ.

R6→R6f đã thực thi. R6f kết thúc13/10 03:17+07 vì provider weeklyquota429
bọc503; receipt NEEDS_RECONCILIATION, terminal CONTINUE_REQUIRED/12UNKNOWN,
chưa Manager EXIT. Registry R6_RUNNING cũ; heartbeat sống không là writer.
Snapshot14/10 queue rỗng, không worker/render,6R6leasesRELEASED; kiểm lại lúc
dispatch. Reset timestamps đã qua không tự chứng minh quota đã hồi.

Master e3107a52…e48e đủ9000f/300s/30fps640×360,decode0,audio3windowslag0.
Reviewer xem54midpoints+23frames bổ sung, không continuousplayback/listening.
S74 cải thiện, nhưng S33/S61 portrait sai và S73 mất cầm sổ; matrix9FAIL+
2UNKNOWN+1PASS engineering. Gate assembly thiếu wiring, eventgrid bỏkeys,
CoTracker emptywindows, staleoutput/cache bypass, remappedmatrix,40/42terminal
hashesmatch; chưa finalmanifest. Đây là checkpoint review, không finalsubmission.

Giữ cùngTask/RUN/R6/counters/owners; Manager20261012_002032_daa36c,worker
20261007_234033_cc0b6d. Quota/context/incident/zero-writer audit§4 trước resume;
R6b sửa nhầm terminalinv1 phải preserve/reconcile theo đúng writerlineage,
không resetincidentcount hoặc đổiowner chỉ vìmessagecounts. Chưa Codexdispatch.

R6fmaster/comparison và oldreceipts/evidence/terminals frozen. Correction
implementation R6 boundedpatch/preimage; outputs/cache/reviews mới tại
R6/continuations/<new_invocation_id>, terminal mới đúng invocation. Không
rewrite history để khớphash. MAIN/INTEGRATION/prod/tests/DB/globalruntime/
source/cast/style/W7/C1/C2/R3/R4/R5/reviewerpackets protected. SamepilotCASTB/
flat2D,WIP1GPU1,noPMbudget giữ;QUALITY0,codex_accepted0,S12/S13notapproved/
notclosed,full22/tool/integration blocked. User tự giao prompt mới choHermes.

## 1. Quy tắc bắt buộc trước khi viết hoặc chạy prompt

### Đối với Codex Reviewer/PM đang soạn prompt

1. Đọc toàn bộ file này trước mỗi lần tạo, sửa hoặc bổ sung prompt quản lý.
2. Đọc trạng thái thực tế của repository, báo cáo sprint/task gần nhất và các session đang chạy; không suy đoán từ lịch sử chat.
3. Chỉ đưa vào prompt sprint hiện tại và các task tương lai đã được BA chứng minh là độc lập, có thể chạy song song an toàn.
4. Nếu chỉ thị mới nhất của người dùng khác file này, chỉ thị mới nhất thắng. Nếu người dùng muốn thay đổi lâu dài, cập nhật lại chính file này để tránh lệch quy tắc ở lần sau.
5. Prompt hoàn chỉnh phải bắt đầu bằng lệnh yêu cầu Manager đọc toàn bộ file này trước khi preflight hoặc dispatch.

### Đối với Hermes/Codex Manager nhận prompt

Manager phải đọc hết file:

`C:\Users\Admin\MotionForge2D\docs\pm\HERMES_AUTOPILOT_RULES.md`

Sau khi đọc, Manager phải báo `RULES_LOADED` kèm đường dẫn, HEAD đang thấy và danh sách các mục chính đã nạp. Nếu file thiếu, không đọc được hoặc có mâu thuẫn chưa giải quyết được thì dừng với `BLOCKED_RULES`; không được dispatch worker bằng trí nhớ.

Sau `RULES_LOADED`, Manager phải đọc thêm trạng thái điều hành hiện hành tại `C:\Users\Admin\MotionForge2D\docs\pm\CODEX_PM_HANDOFF.md` và product backlog chuẩn tại `C:\Users\Admin\MotionForge2D\docs\pm\ROADMAP.md`, rồi đối chiếu lại repository/worktree thực tế. Hai file này là snapshot trạng thái và backlog, không thay thế rules; nếu khác trạng thái thực tế thì Manager báo sai lệch và dừng dispatch phần bị ảnh hưởng để Codex quyết định.

## 2. Phân vai tuyệt đối

- **Codex Reviewer/PM/BA độc lập**: xác định phạm vi sprint, chứng minh dependency, review code và test độc lập, phê duyệt hoặc yêu cầu correction, rồi mới mở gate tiếp theo.
- **Hermes/Codex Manager**: chỉ preflight, chia task, tạo/resume session, điều phối, theo dõi, review đầu ra, chạy gate và lập báo cáo.
- **Worker/Writer**: thực hiện code, test, migration hoặc tài liệu được giao trong allowlist.

Manager **không được tự viết hoặc sửa production code, test, migration, UI hay config**. Khi có defect, Manager phải giao correction về đúng session sở hữu task. Manager chỉ được sửa tài liệu điều phối/báo cáo của mình nếu prompt cho phép rõ ràng.

### 2.1. Ba nhánh triển khai cho giai đoạn hoàn thiện tool và demo

Theo yêu cầu người dùng ngày 2026-09-24, Hermes Manager điều phối **hai nhánh code sprint và một nhánh demo có owner riêng**:

- **Code lõi:** engine/ComfyUI, hợp đồng tích hợp và các task S13 đã được Codex mở gate.
- **Code tool:** luồng sản phẩm/API/UI/QC, QA và tích hợp S12.
- **Demo:** chịu trách nhiệm hành trình dùng app từ đầu đến cuối, bộ nhân vật dùng lại, video xuất thực tế, kiểm tra bằng hình ảnh và chạy lại sau sửa lỗi.

Nhánh là cách chia trách nhiệm; không thay thế quy tắc một Task ID–một session. Hai nhánh code tiếp tục dùng đúng writer hiện có cho từng task; chỉ task mới mới mở session mới. Owner demo không sửa ké code của writer khác, không tự tạo một pipeline sản phẩm riêng; ghi lỗi có cách tái lập và chuyển về đúng owner qua Manager. Không cần thêm các tầng supervisor chỉ để chuyển lời.

Test xanh, ảnh giao diện hoặc clip chạy bằng script rời không đủ để gọi demo hoàn chỉnh. Prompt hiện hành phải chốt hành trình thực, cast/PackVersion được giữ xuyên suốt các video trong cùng bộ, kết quả xuất/mở lại và tiêu chí hình ảnh. Tách rõ engineering fixture, media experiment và product demo. Demo chỉ được xác nhận sau review độc lập của Codex; Manager không tự approve/close hay mở gate sprint.

Mỗi nhánh tiếp tục phần độc lập khi nhánh khác chờ dependency. Số luồng đang chạy và GPU lease tuân theo bằng chứng tài nguyên của prompt hiện hành, không mặc định nhân số worker hoặc cho nhiều model tranh một GPU.

### 2.2. Delivery phải bám sản phẩm đầu cuối; chứng minh workflow trước code

Theo chỉ thị người dùng ngày 2026-09-27, mục tiêu MotionForge là video MP4
thật được tạo qua hành trình sản phẩm: nguồn → scene units → kho nhân vật/cast
dùng lại → workflow ComfyUI → QC hình/chuyển động/tương tác → audio/export/reopen.
Wan hoặc model khác là thành phần của graph, không thay thế bước phân tích,
chuẩn bị inputs, điều khiển và kiểm chứng. Hai nhánh code và owner demo tại
§2.1 tiếp tục áp dụng.

Trước implementation công nghệ mới phải nghiên cứu nguồn chính thức, đối chiếu
node/model/runtime thực, so sánh phương án và chứng minh workflow trên unit thật.
Prompt phải có proof gate, requirement→task→test/artifact mapping, task nhỏ có
outcome/dependency/write-set/acceptance, và quyền nội bộ đủ tới đầu ra của scope
delivery đã chốt. Không lấy vòng CPU correction, ảnh tĩnh, fixture hoặc script
rời làm đích bàn giao thay sản phẩm. Không code dựa vào model capability suy đoán.

Scope cụ thể, budget thử nghiệm, model, Git và quyền dispatch vẫn do prompt hiện
hành cấp; mục này không tự mở toàn backlog, bỏ review gate hoặc cấp quyền tự
khởi chạy Hermes. Không hứa một lần generation chắc chắn đạt; phải giữ failure
evidence, sửa theo nguyên nhân, tái dùng phần đã đạt và chỉ chạy lại phần bị ảnh hưởng.

## 3. Sprint gate và quyền dừng

1. Mỗi sprint có scope, task map, acceptance criteria và review gate riêng.
2. Manager được tiếp tục điều phối mọi task đã được cấp quyền trong sprint hiện tại cho tới khi hoàn tất hoặc bị block thật sự.
3. Khi sprint hoàn tất, Manager phải dừng ở `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`.
4. Manager không được tự ghi `APPROVED`, `CLOSED`, tự mở sprint tiếp theo, hoặc tự coi test xanh là Codex đã duyệt.
5. Chỉ Codex Reviewer/PM được quyết định `APPROVED`, `CHANGES_REQUESTED` và mở gate sprint tiếp theo.
6. Không đưa toàn bộ backlog tương lai cho Manager để tự triển khai. Prompt chỉ cấp quyền cho sprint đang review và các task cross-sprint được liệt kê đích danh.

## 4. Một task — một session sở hữu

- **Một Task ID = đúng một worker session/chat sở hữu.**
- Task mới phải dùng session/chat mới.
- Correction, retry, bổ sung test hoặc sửa finding thuộc cùng Task ID phải **resume đúng session cũ cho tới khi task xong**.
- Không dùng một session đã hoàn thành task A để làm task B.
- Không tạo session thay thế trong khi session cũ còn sống hoặc có thể resume.
- Chỉ được recovery sang session mới khi session cũ đã chết, không thể resume hoặc context hỏng. Manager phải xác nhận session cũ không còn active, ghi bằng chứng và lý do recovery; tuyệt đối không để hai owner cùng sửa một task.
- Trước khi tiếp tục một correction trên session dài, Manager phải audit **context health**: số lượt/compaction, iteration exit liên tiếp, việc lặp lại phần đã xong, dùng quyết định/trạng thái cũ, hiểu sai scope hiện hành, token/độ trễ tăng bất thường và số lượt không tạo usable bytes. Một dấu hiệu đơn lẻ thông thường không đủ để bỏ owner; context chỉ được coi là hỏng khi có bằng chứng lặp lại hoặc session không còn giữ đúng current contract. Một lần phá hủy file hoặc overwrite sai scope là incident nghiêm trọng: dừng writer, bảo toàn evidence và chỉ được resume một lượt recovery có guard nếu Codex cấp quyền; lần vi phạm an toàn thứ hai trong cùng lineage là bằng chứng lặp lại đủ để yêu cầu owner transfer.
- Nếu recovery vì context hỏng được chứng minh, phải dừng/xác nhận không còn writer của session cũ trước, tạo đúng một recovery session, ghi owner transfer trong registry và giao handoff gọn chỉ gồm current verdict, landed bytes, finding còn mở, write-set, acceptance và gates còn thiếu. Không nhồi lại toàn bộ chat/log lịch sử vào recovery prompt.
- Task quá lớn phải được BA/PM tách trước thành các Task ID đủ nhỏ cho một session, mỗi task có outcome, dependency, exclusive write-set và acceptance criteria riêng.

Manager phải duy trì **Session Registry**:

| Task ID | Session ID | Trạng thái | Model | Exclusive write-set | Heartbeat cuối | Recovery reason |
|---|---|---|---|---|---|---|

## 5. Model routing theo từng prompt, không áp dụng ngược

1. Model worker là cấu hình **theo từng manager chat/prompt**, không phải mặc định vĩnh viễn của toàn dự án.
2. Các session/chat đã tồn tại tiếp tục dùng model đã được cấu hình trước đó, trừ khi người dùng ra lệnh đổi chính các session đó.
3. Manager chat mới chỉ được ép model cho các worker do chính chat đó tạo ra.
4. Mỗi worker prompt phải ghi rõ provider/model ID, reasoning level, fallback policy và phạm vi session/task được áp dụng.
5. Nếu prompt yêu cầu `fallback disabled`, mọi route sai model phải dừng `BLOCKED_MODEL_ROUTE`; không được âm thầm thay model.
6. Codex phải lấy model từ chỉ thị mới nhất của người dùng. Không hard-code DeepSeek, Muse hoặc model thử nghiệm thành mặc định toàn cục trong file rules.

Ví dụ cấu hình cục bộ đã từng được yêu cầu, chỉ dùng khi prompt hiện tại nhắc lại:

- `ocg/muse-spark-1.2-contributor`, reasoning max;
- `oc/x-preview-f-free`, reasoning max, dùng riêng cho worker của manager chat thử nghiệm tương ứng.

## 6. Tối đa hóa song song nhưng phải có bằng chứng an toàn

Manager phải chạy tối đa số luồng **dependency-ready và disjoint**, không đặt cap tuần tự tùy tiện. Tuy nhiên tốc độ không được đánh đổi ownership hoặc tính đúng đắn.

Một task chỉ được chạy song song khi tất cả điều kiện sau đều đúng:

1. Không phụ thuộc output chưa hoàn thành của task/sprint khác.
2. API contract, schema, migration, model, route, component và fixture liên quan đã ổn định hoặc độc lập.
3. Exclusive write-set không giao nhau.
4. Test/runtime resource được cô lập: database, temp directory, output directory, port và cache riêng khi cần.
5. Không phá review boundary của sprint đang chờ Codex.
6. BA/PM đã ghi rõ bằng chứng dependency và quyền chạy song song trong prompt.

Task thuộc sprint sau chỉ được chạy sớm khi Codex/BA chắc chắn và ghi đích danh rằng task đó độc lập. Hermes không được tự suy luận quyền cross-sprint.

Manager phải duy trì dependency DAG, ownership/exclusive write-set matrix, active session registry, parallel wave hiện tại và lý do mọi slot chưa dùng. Task-focused tests có thể chạy song song nếu tài nguyên được cô lập. Global gates dùng chung repository/runtime phải chạy qua mutex, ở checkpoint nhất quán; tạm ngừng writer khi cần để tránh kết quả nhiễu.

## 7. Heartbeat, chống treo và vòng điều phối liên tục

- Manager phải phát heartbeat **ít nhất mỗi 20 phút** trong suốt thời gian còn task active.
- Heartbeat phải nêu task/session, phase, tiến độ mới, log mới nhất, blocker, hành động kế tiếp và slot đang dùng/rảnh.
- Nếu không có log/progress mới trong **8 phút**, Manager phải audit ngay: process còn sống không, session có chờ input không, tail log, lỗi 502/disconnect, lock hoặc test treo.
- Có sự cố phải báo ngay; không chờ đến heartbeat kế tiếp.
- Với 502/disconnect, ưu tiên resume đúng session cũ nếu còn recover được.
- Connection error policy: khi gặp connection error/502/503/504/disconnect/socket reset/DNS lỗi tạm thời/network timeout, phải **chờ đủ 5 phút rồi mới retry** bằng cách resume đúng session cũ. Mỗi lần retry phải giữ nguyên provider, model ID, API mode, reasoning level, task scope và exclusive write-set; không được âm thầm fallback hoặc đổi model để né lỗi.
- Giới hạn retry nội bộ của Hermes (ví dụ thông báo `API call failed after 3 retries`) **không phải terminal state và không phải lý do để dừng task**. Sau khi batch retry nội bộ thất bại, Manager phải ghi nhận lỗi, chờ 5 phút, rồi chủ động resume/relaunch đúng session với cùng model. Nếu tiếp tục lỗi thì lặp chu kỳ `wait 5 minutes -> liveness audit -> resume same session/same model` **không giới hạn số chu kỳ** cho tới khi request chạy tiếp thành công, người dùng ra lệnh dừng, hoặc có bằng chứng session chết/context hỏng theo quy tắc recovery ở Mục 4.
- Trong thời gian chờ retry, trạng thái task vẫn là `RUNNING_RETRY_WAIT` (không được ghi `TASK_SUBMITTED`, `BLOCKED_LIVENESS` hoặc kết thúc Manager chỉ vì đã hết 3 lần thử nội bộ). Manager phải báo ngay lần lỗi đầu tiên, cập nhật heartbeat với thời điểm retry kế tiếp và không retry dồn dập trước mốc 5 phút.
- Chỉ áp dụng vòng retry vô hạn trên cho lỗi kết nối/tạm thời. Các lỗi xác thực hoặc cấu hình xác định như 400 do payload không hợp lệ, 401/403, unknown provider/model, sai API mode, hết quota/credit có bằng chứng, hoặc route bị vô hiệu hóa phải được chẩn đoán và báo blocker tương ứng; không được lặp vô hạn một request chắc chắn sai.
- Không được im lặng quá 20 phút khi còn công việc.
- Manager phải tiếp tục vòng `monitor -> review -> correction/resume -> verify -> report` cho tới terminal state được cấp quyền; không dừng chỉ vì một worker vừa trả lời.

## 8. Workspace và an toàn Git

Mỗi prompt phải pin rõ workspace/worktree tuyệt đối, branch, HEAD/preflight baseline, database/test resource guard, allowed write paths, forbidden paths và dirty-worktree policy.

Mặc định dự án hiện tại:

- MAIN: `C:\Users\Admin\MotionForge2D` — vùng tham chiếu/protected, trừ thay đổi được người dùng cấp quyền rõ ràng;
- integration worktree phải là checkout sạch, sprint-specific từ checkpoint đã
  được Codex duyệt; prompt hiện hành phải pin path/branch/commit cụ thể;
- S11 hiện dùng `C:\Users\Admin\MotionForge2D-worktrees\s11-integration`, branch
  `codex/s11-integration`; không dùng worktree S10 dirty làm implementation tree.

Manager phải khám phá và pin HEAD thực tế ở đầu prompt; không sao chép HEAD cũ như một sự thật hiện tại.

Không được `reset --hard`, `clean`, `stash`, `restore`, `checkout` đè file, commit, push, merge hoặc xóa thay đổi không rõ chủ sở hữu nếu chưa có quyền rõ ràng. Không dùng database thật cho test. Không mở rộng allowlist theo suy đoán.

### 8.1. Checkpoint sạch và parallel worktree có kiểm soát

- Khi một sprint đã `CODEX_APPROVED / CLOSED` và user/Codex cấp quyền Git rõ
  ràng, phải ưu tiên tạo approved-scope checkpoint trước sprint kế tiếp: chỉ
  stage source/migration/test/harness/docs đã duyệt; loại backup/recovered file,
  cache, report kết xuất, test-results và evidence tạm; chạy gate tương xứng;
  verify remote ref sau push.
- Parallel implementation chỉ được bật từ một immutable checkpoint đã push.
  Mỗi Task ID có branch + clean worktree + session riêng; mọi task trong cùng
  wave phải cùng wave-base commit, write-set disjoint và runtime/evidence tách
  biệt. Worktree sprint cũ còn dirty chỉ là read-only archive/evidence.
- Một task worktree chỉ có một writer. Worker được commit đúng allowlist của
  task trên local task branch khi prompt cấp quyền rõ; commit đó chỉ là transport
  checkpoint, không phải `APPROVED`. Correction tiếp tục exact session/branch và
  tạo commit bổ sung, không rewrite lịch sử đã tích hợp.
- Sprint phải có đúng một integration owner/session riêng cho toàn sprint.
  Owner này chỉ được tích hợp exact commit range đã Manager verify vào canonical
  integration branch bằng fast-forward hoặc conflict-free merge/cherry-pick; cấm sửa
  tay production/test, cấm rebase/reset/force-push. Conflict phải abort, giữ
  canonical tree sạch và route về exact task owner trên baseline mới.
- Manager được tạo/remove disposable task/verifier worktrees và push canonical
  integration branch sau wave gate nếu prompt/user đã cấp quyền; Manager vẫn
  không được sửa implementation. Không xóa worktree/branch còn uncommitted hoặc
  chưa lưu evidence.
- Dispatch tối đa mọi task dependency-ready/disjoint trong wave. Manager có thể
  verify một task commit và chạy read-only lane cô lập trong khi worker disjoint
  khác còn chạy; global/migration/Playwright/leak gate chỉ chạy khi toàn bộ writer
  đã thoát và integration HEAD đã đóng băng.

### 8.2. Byte-safe write-set guard bắt buộc

Trước mỗi worker có quyền sửa source/test/migration/config, Manager phải tạo
baseline cho toàn bộ exclusive write-set và protected set:

1. Ghi absolute/relative path, tracked/untracked/dirty attribution, SHA-256,
   byte size, logical line count và mtime.
2. Với file hiện hữu nhưng untracked, dirty không thể khôi phục từ Git, file test
   authority hoặc file lớn/quan trọng, tạo byte-for-byte snapshot trong evidence
   mới và xác minh snapshot hash bằng source hash trước dispatch. Snapshot là
   recovery evidence; Manager không được tự chép nó đè lại implementation.
3. Dùng guard xác định như
   `docs/pm/tools/write_set_guard.py` hoặc cơ chế tương đương để verify protected
   drift và destructive shrink sau mỗi worker terminal. Raw manifest/report phải
   được giữ trong task output.
4. File đã tồn tại không được sửa bằng `write_file`, full-file replace, shell
   redirection, `Set-Content`, `Out-File`, heredoc, script direct-write hoặc
   copy/move-overwrite. Mặc định chỉ dùng bounded patch có preimage (`apply_patch`
   hoặc cơ chế tương đương) và kiểm hash/size/line count ngay sau patch. Whole-file
   generation chỉ được dùng cho file mới chưa tồn tại, đúng allowlist.
5. Nếu file biến mất, line/byte count giảm bất thường, nhiều definition biến
   mất, hoặc guard báo destructive shrink, phải dừng ngay; không tiếp tục code,
   không chạy broad gate và không cố che bằng rebuild từ memory.

### 8.2.1. File lớn và payload bị cắt

- File đang tồn tại, kể cả untracked từ lượt trước, vẫn dùng bounded patch.
  Có thể dùng `apply_patch` hoặc công cụ `patch` với exact old/new text sau khi
  đọc schema runtime. Mỗi patch kiểm preimage duy nhất; không match thì đọc lại
  đoạn liên quan rồi sửa patch, không fallback sang full overwrite.
- Chia theo hàm/khối logic/test case; ưu tiên một patch mỗi tool call. Kích thước
  cụ thể do packet/tool quyết định, không có yêu cầu phát toàn file trong một
  response. Sau truncation giảm payload, xác minh hash rồi mới tiếp tục.
- Với file mới được allowlist, được tạo skeleton nhỏ rồi bổ sung bằng patch;
  không cần generate toàn bộ file một lần. Được lưu patch fragments trong RUN
  scratch đã cấp và apply sau khi validate, không ghi đè source bằng copy.
- Chunks là nhiều thay đổi có kiểm chứng; không được dùng append/ghi từng mảnh
  để lách lệnh cấm truncate hoặc rebuild một file hiện hữu từ memory. Giữ phần
  code/test không liên quan và test authority. Sau mỗi patch kiểm bytes/hash/
  diff mục tiêu; protected-set đầy đủ ở checkpoint/terminal.
- Không được báo "chia patch ngoài allowlist" nếu vẫn sửa đúng đường dẫn,
  acceptance và owner. Chỉ phát sinh quyền mới khi đổi vùng ghi, model/global
  config hoặc yêu cầu sản phẩm. Không nâng output vô hạn để ép full overwrite.

### 8.3. Recovery khi source/test authority bị phá hủy

- Đóng băng writer và mọi production write; bảo toàn file hỏng, backup, pyc,
  tool log, state database và message/tool payload liên quan. Không chạy lệnh có
  thể ghi đè cache/pyc ground truth trước khi snapshot evidence.
- Manager và Codex Reviewer không được sửa/rebuild implementation. Recovery
  bytes thuộc đúng worker owner hoặc recovery owner được Codex cấp quyền.
- Candidate phải được dựng ngoài path chính từ nguồn có provenance (Git/blob,
  byte snapshot, full tool payload hoặc deterministic patch replay). Nếu có
  reviewed SHA cũ, candidate phải match exact SHA trước khi patch path chính.
  Tên test, docstring, compile, pyc function list hoặc test xanh không thay thế
  exact source authority.
- State/session database chỉ được mở read-only; mọi query/script/export phải
  được giữ trong evidence, không chỉ `%TEMP%`. Không vacuum hoặc mutate DB.
- Report recovery phải ghi cả pass lẫn fail của full relevant module, collect
  node IDs, duplicate definitions, unresolved symbols và raw command. Không
  được suy rộng từ một selection thành trạng thái toàn file.
- Nếu exact authority không thể phục hồi, dừng `BLOCKED_TEST_AUTHORITY`; không
  tự chấp nhận semantic reconstruction. Nếu guarded owner tái phạm hành vi phá
  hủy/sai scope, dừng `BLOCKED_CONTEXT_HEALTH / OWNER_TRANSFER_REQUIRED`.

## 9. Cấu trúc bắt buộc của một prompt quản lý chuẩn

Mỗi prompt phải có đầy đủ:

1. **Authority & role** — Codex là reviewer gate; Manager không code.
2. **Mandatory rules load** — đọc toàn bộ file này và báo `RULES_LOADED`.
3. **Current verdict/status** — sprint/task nào đã duyệt, bị correction hay đang chờ review.
4. **Authorized scope / out of scope** — quyền làm chính xác và ranh giới dừng.
5. **Workspace preflight** — path, branch, HEAD, dirty tree, runtime, DB guard,
   byte-safe write-set manifest/snapshot và destructive-shrink guard.
6. **Model policy** — model/reasoning/fallback cho manager chat và từng worker mới; bảo toàn session cũ.
7. **Task map** — từng Task ID có outcome, dependencies, exclusive write allowlist, forbidden paths, acceptance criteria và owner session rule.
8. **Parallel waves** — task nào chạy đồng thời, bằng chứng an toàn và task nào phải chờ.
9. **Session/correction routing** — new task = new session; correction = resume session cũ.
10. **Heartbeat/liveness** — heartbeat 20 phút, audit 8 phút, báo sự cố ngay.
11. **Verification gates** — task-focused test, contract/integration test, global gate/mutex và evidence phải lưu.
12. **Terminal condition** — trạng thái được phép kết thúc và review boundary.
13. **Required report** — task/session/model map, files changed, tests, findings, blockers, risks, evidence paths và đề xuất tiếp theo.
14. **Start command** — yêu cầu Manager bắt đầu preflight/dispatch ngay, không chỉ trả lại kế hoạch lý thuyết.

Nếu prompt không chia sprint thành Task ID cụ thể, không gán mỗi task cho một session mới, hoặc không nêu correction phải resume session cũ thì prompt chưa đạt chuẩn.

## 10. Review độc lập của Codex

Codex không được chỉ tin report, test count hoặc kết luận của Hermes. Khi review sprint phải kiểm tra diff/code/test thực tế, đối chiếu acceptance criteria từng task, chạy lại test/gate theo rủi ro, kiểm tra regression/contract/migration/ownership/artifact và kết luận theo sprint.

Finding phải có mức độ (`P0/P1/P2`), file/dòng, cách tái hiện hoặc chứng cứ, expected/actual, ảnh hưởng, test cần bổ sung và Task ID/session owner phải nhận correction.

Nếu `CHANGES_REQUESTED`, prompt tiếp theo phải resume đúng session owner của từng finding. Nếu `APPROVED`, Codex/BA mới lập và cấp quyền cho sprint hoặc parallel wave tiếp theo.

Sau **mọi** verdict/review, Codex phải đưa ngay một **Session Opening Proposal** cho bước kế tiếp, kể cả khi gate còn blocked. Proposal tối thiểu phải nêu:

1. Task ID nào mở session mới, Task ID nào resume exact session cũ, và session nào cần context-health audit hoặc recovery có điều kiện.
2. Dependency/activation condition, parallel wave tối đa an toàn, exclusive write-set và lý do các task chưa được mở.
3. Provider/model/reasoning/fallback dự kiến theo chỉ thị user mới nhất.
4. Với recovery: bằng chứng context hỏng cần đạt, cách dừng owner cũ, handoff tối thiểu và đảm bảo zero concurrent writer.
5. Trạng thái quyền hạn: `PROPOSED_ONLY`, `AUTHORIZED_TO_DISPATCH` hoặc `BLOCKED_DEPENDENCY`. Proposal không tự động tạo/mở session nếu Codex/user chưa cấp dispatch authority.

Nếu review đồng thời tạo prompt Hermes tiếp theo, phần Session Opening Proposal phải khớp chính xác task/session/model/wave trong prompt; không được đưa một phương án trong chat nhưng cấp quyền khác trong file.

## 11. Từ vựng trạng thái chuẩn

- `RULES_LOADED`
- `PREFLIGHT_OK`
- `RUNNING`
- `RUNNING_RETRY_WAIT`
- `BLOCKED_RULES`
- `BLOCKED_MODEL_ROUTE`
- `BLOCKED_DEPENDENCY`
- `BLOCKED_LIVENESS`
- `BLOCKED_TEST_AUTHORITY`
- `BLOCKED_CONTEXT_HEALTH`
- `BLOCKED_ROLE_VIOLATION`
- `TASK_SUBMITTED`
- `TASK_MANAGER_VERIFIED`
- `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`
- `CHANGES_REQUESTED`
- `APPROVED`

Không dùng `DONE`, `CLOSED` hoặc `APPROVED` theo cách làm mờ quyền review của Codex.

## 12. Checklist cuối trước khi giao prompt cho người dùng

- [ ] Đã đọc toàn bộ file này trong lượt hiện tại.
- [ ] Prompt bắt Manager đọc toàn bộ file này trước mọi hành động.
- [ ] Chỉ có sprint/task được cấp quyền; không giao cả backlog.
- [ ] Sprint được tách thành Task ID cụ thể.
- [ ] Mỗi task mới có một session/chat mới; correction resume session cũ.
- [ ] Model áp dụng đúng manager chat, không đổi session cũ ngoài ý muốn.
- [ ] Có dependency DAG, exclusive write-set và parallel wave tối đa an toàn.
- [ ] Có heartbeat 20 phút, liveness audit 8 phút và báo lỗi ngay.
- [ ] Manager không code.
- [ ] Có write-set SHA/size/line manifest, snapshot cho critical untracked/dirty
      bytes, patch-only guard cho file hiện hữu và post-worker shrink verification.
- [ ] Gate chạy theo thứ tự micro -> matrix -> focused/static -> final broad;
      không dùng broad xanh để waive một binary row còn mở.
- [ ] Có test/evidence/terminal state và dừng để Codex review sau sprint.
- [ ] Sau review đã đưa Session Opening Proposal: new/resume/recovery, context health, model, dependency, write-set, parallel wave và dispatch authority.

---

**Quy tắc duy trì:** mọi thay đổi lâu dài về cách điều phối phải được cập nhật tại file này, không tạo thêm một bản rules cạnh tranh.
