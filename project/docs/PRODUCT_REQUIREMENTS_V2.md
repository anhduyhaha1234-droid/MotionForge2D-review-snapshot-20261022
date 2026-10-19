# MotionForge 2D - Product Requirements V4

**Trạng thái:** Approved product baseline  
**Ngày cập nhật:** 2026-08-03  
**Trọng tâm Phase 1:** Quản lý sản xuất nhiều video/kênh, kho nhân vật dùng chung, reskin hoạt hình 2D, giữ nguyên audio/voice gốc và xuất 4K  
**Đối tượng đọc:** Stakeholder, Product/BA, UX/UI, Engineering, QA

---

## 1. Product vision

MotionForge 2D là ứng dụng Windows local-first giúp người dùng thay đổi nhân vật/đồ vật trong video hoạt hình 2D và chuyển ngôn ngữ của video bằng một quy trình đơn giản, trực quan và có thể xử lý hàng loạt.

Trải nghiệm mục tiêu:

```text
Đưa video vào
-> Hệ thống tự phân tích cảnh và tìm object xuất hiện
-> Người dùng chọn object muốn thay
-> Đưa ảnh/Character Pack mới vào
-> Tạo Reskin Demo trên các cảnh đại diện
-> Xem Before/After và chỉnh đến khi đạt
-> Xác nhận áp dụng reskin toàn video
-> Chỉ kiểm tra các cảnh có lỗi
-> Xuất video 4K với nguyên audio/voice gốc
```

Sản phẩm không cố trở thành phần mềm dựng phim tổng quát. Nó tập trung giải quyết nhanh bốn công việc:

1. **Nhận biết và quản lý object xuyên suốt video.**
2. **Reskin object bằng asset mới với ít chỉnh tay nhất.**
3. **Xem demo trước khi xử lý toàn video và xuất video chất lượng cao với audio gốc.**
4. **Quản lý nhiều project/video/kênh và tái sử dụng kho nhân vật trong toàn hệ thống.**

Localization và thay voice là Phase 2, chỉ bắt đầu sau khi luồng reskin Phase 1 ổn định.

---

## 2. Mục tiêu sản phẩm

### 2.1 Mục tiêu chính

- Người dùng không cần cắt video hoặc xử lý từng frame thủ công.
- Object được tổ chức theo vai trò xuyên suốt toàn video, không chỉ theo từng scene rời rạc.
- Một lần gán asset mới có thể áp dụng cho mọi scene có cùng object.
- Hệ thống tự xử lý phần lớn scene và chỉ yêu cầu người dùng sửa ngoại lệ.
- Phase 1 giữ nguyên audio/voice gốc và remux chính xác vào video reskin.
- Final output giữ đúng duration, âm thanh đồng bộ và hỗ trợ độ phân giải 4K.
- Mọi job dài chạy nền, có progress, cancel, retry và resume.

### 2.2 North-star metric

**Thời gian thao tác chủ động của người dùng để tạo một phút video reskin + bản địa hóa đạt yêu cầu.**

### 2.3 Chỉ số hỗ trợ

- Thời gian từ import đến khi thấy danh sách object đầu tiên.
- Tỷ lệ object được hệ thống nhóm đúng xuyên suốt video.
- Tỷ lệ scene có thể auto-pass mà không cần sửa.
- Số thao tác trung bình để thay một character cho toàn video.
- Tỷ lệ render hoàn thành sau restart/retry.
- Tỷ lệ output không bị A/V drift hoặc lỗi kích thước/codec.

---

## 3. Phạm vi hiện tại

### 3.1 Trong phạm vi

- Import video local.
- Tự động phát hiện scene/shot.
- Tự động tìm candidate object trong các scene.
- Group các lần xuất hiện thành Object Role toàn video.
- Cho người dùng chọn object muốn thay hoặc bỏ qua.
- Import ảnh PNG hoặc chọn Character Pack.
- Theo vết, loại bỏ object gốc và composite object mới.
- Anchor, scale, pose, layer và keyframe correction.
- Giữ nguyên audio/voice/nhạc nền/hiệu ứng của source.
- Reskin Demo bắt buộc trước khi apply toàn video.
- Review các scene/frame/object có vấn đề.
- Render MP4 4K, 1080p và preview proxy.
- Output validation, resume và safe cleanup.

### 3.2 Tạm thời ngoài phạm vi

- License, copyright và rights workflow.
- Upload/publish lên YouTube hoặc nền tảng khác.
- Channel monetization và content analytics.
- Cloud collaboration/multi-user.
- Full video editor/NLE.
- Tự tạo kịch bản hoặc thay đổi nội dung câu chuyện.
- Bảo đảm generative lip-sync hoàn hảo cho mọi phong cách hoạt hình.
- Nhận diện thoại, dịch nội dung và tạo voice mới (hoãn sang Phase 2).
- macOS/Linux packaged release.

---

## 4. Product operating model

### 4.1 Cấu trúc hệ thống

```text
Workspace
├── Projects
│   └── Project
│       ├── Source Channel
│       ├── Production Channel
│       ├── Video Items
│       ├── Project Cast Mapping
│       └── Output Versions
├── Channels
│   ├── Source Channels
│   └── Production Channels
├── Character Library
│   ├── Ready Characters
│   ├── Draft/Generating
│   └── Archived
├── Global Jobs
└── Storage/System
```

### 4.2 Channel

Channel là metadata dùng để phân loại nguồn và đầu ra; không phải Project.

**Source Channel** gồm:

- ID, tên, avatar/màu;
- mô tả/tag;
- danh sách source videos;
- số video đã/đang xử lý;
- projects đang sử dụng;
- object roles thường xuất hiện.

**Production Channel** gồm:

- ID, tên, avatar/màu;
- output profile mặc định;
- aspect ratio/resolution mặc định;
- Character Set thường dùng;
- projects/video outputs;
- language field để mở rộng Phase 2, không kích hoạt localization trong Phase 1.

Một Project Phase 1 có tối đa một Source Channel chính và một Production Channel chính. Video Item vẫn giữ source metadata riêng để sau này hỗ trợ nhiều nguồn mà không đổi schema lớn.

### 4.3 Project

Project là container sản xuất cho một series, chủ đề hoặc đợt nội dung và chứa nhiều Video Items.

Project fields:

- ID, tên, cover, description, tags;
- Source Channel và Production Channel;
- default Character Set;
- default output preset;
- video count và aggregate progress;
- storage usage;
- created/updated timestamps;
- status: Draft, Active, Needs Review, Rendering, Completed, Archived.

Project Detail gồm bốn tab:

1. **Overview:** progress, recent activity, blockers, storage.
2. **Videos:** video grid/list và pipeline status.
3. **Cast Mapping:** source roles -> Character Pack versions.
4. **Outputs:** render versions theo video.

### 4.4 Video Item

Video Item là đơn vị chạy pipeline reskin:

```text
Imported -> Analyzing -> Objects Ready -> Mapping Required
-> Demo Required -> Demo Approved -> Applying Reskin
-> Needs Review -> Ready to Export -> Rendering -> Completed
```

Video card hiển thị:

- thumbnail, title, duration, source resolution;
- source channel;
- objects detected/selected/mapped;
- Reskin Demo status;
- issue count;
- current job/progress;
- latest output/version;
- primary CTA theo current state.

### 4.5 Project Cast Mapping

Cast Mapping cho phép reuse lựa chọn nhân vật giữa nhiều video trong cùng Project:

```text
Source Role/Class Hint -> Character Pack Version -> Mapping Strategy
```

- Mapping mới chỉ là suggestion cho Video Item cho đến khi user confirm.
- Không tự áp khi grouping/role confidence thấp.
- User chọn apply cho video hiện tại hoặc selected videos.
- Mapping phải pin Character Pack version để output cũ tái lập được.

---

## 5. Character Library

### 5.1 Mục tiêu

Character Library nằm ở cấp Workspace và tái sử dụng cho mọi Project, Video Item và Production Channel.

### 5.2 Character entity

Mỗi Character gồm:

- stable Character ID, ví dụ `@FARMER`;
- display name, type và tags;
- style, outline và palette summary;
- symmetry/asymmetry;
- thumbnail;
- current/default Pack Version;
- all Pack Versions;
- Ready/Draft/Generating/Needs Review/Archived status;
- pose/view coverage;
- usage references và last used;
- generation metadata khi được tạo bởi Character Generator.

### 5.3 Library actions

- Search/filter/sort.
- Import Character Pack.
- Create from Reference.
- Duplicate character.
- Create new Pack Version.
- Add/replace pose.
- Validate/preview/test in Reskin Demo.
- Set default version.
- Archive/restore.

Không hard-delete pack version đang được Project/Video sử dụng.

### 5.4 Core Character Pack V1

Core Pack bắt buộc sáu transparent PNG:

1. `front.png`
2. `three_quarter.png`
3. `side.png`
4. `back.png`
5. `sitting.png`
6. `walking.png`

Recommended optional assets:

- left/right variants cho asymmetric character;
- talking open/closed;
- lying/holding;
- expressions;
- signature prop.

Mỗi asset chứa:

- view/pose ID;
- canvas width/height;
- alpha PNG reference;
- anchors: feet center, body center, head center;
- sitting bổ sung seat contact;
- optional mirror permission;
- validation status.

### 5.5 Pack compatibility

Khi chọn Character cho Object Role, app so sánh occurrence needs với pack coverage:

```text
Required: front, side, sitting, back
Available: front ✓, side ✓, sitting ✓, back ✗
Compatibility: Good
Fallback: three-quarter
Needs Review: 2 scenes
```

Compatibility là recommendation, không phải cam kết output.

---

## 6. Character Generator

### 6.1 Mục tiêu và giới hạn

Character Generator tạo Core Character Pack từ một hoặc vài reference images cho hoạt hình 2D đơn giản. Nó không phải character design suite hoặc rigging tool.

Một ảnh không thể xác định chắc chắn phần bị che/mặt sau; mọi AI-generated view phải được user approve.

### 6.2 Input

Minimum:

- một ảnh toàn thân front hoặc three-quarter;
- subject không bị che đầu/tay/chân;
- background đủ sạch;
- resolution tối thiểu theo validator.

Recommended:

- front + side/three-quarter reference;
- mô tả đặc điểm phải giữ;
- optional signature prop.

### 6.3 Character Profile

Sau import, app tự đề xuất và user xác nhận:

- name và Character ID;
- character type;
- style: doodle, flat cartoon, vector-like, hand-drawn;
- outline color/weight/sketchiness;
- palette;
- head/body proportions;
- face/eyes/brows;
- clothes/accessories;
- signature features/prop;
- symmetry;
- negative constraints.

### 6.4 Generator flow

```text
Import Reference
-> Crop/Remove Background
-> Confirm Character Profile
-> Choose Core or Custom Pack
-> Generate Contact Sheet Candidates
-> Approve Design Direction
-> Generate/Refine Individual Panels
-> Validate Consistency/Alpha/Canvas
-> Approve or Regenerate Each Panel
-> Set Anchors
-> Save Character Pack Version
-> Optional Reskin Demo Test
```

### 6.5 Review UI

Panel grid:

```text
Reference | Front | 3/4 | Side | Back | Sitting | Walking
```

Mỗi panel có:

- candidate carousel;
- Approve/Regenerate/Replace;
- Crop/Flip/Remove Background;
- Edit Anchor;
- mark unavailable với reason.

Pack chỉ Ready khi tất cả Core assets bắt buộc pass hoặc được user chấp nhận fallback rõ ràng.

### 6.6 Technology direction

Character Generator là một adapter/out-of-process engine riêng:

```text
MotionForge -> Character Generation Job -> Generator Adapter
            -> Candidates -> Pack Validator -> Character Library
```

Recommended local implementation:

- ComfyUI local API/workflow engine;
- reference-image conditioning bằng IP-Adapter-type adapter;
- ControlNet/OpenPose hoặc pose-image conditioning;
- SAM/OpenCV/background removal preprocessing;
- Pillow/OpenCV + feature similarity cho validation;
- model/resource scheduler dùng chung GPU Job Center.

Không expose node graph, sampler, scheduler, CFG hoặc adapter weights trong quick UI. User chỉ thấy Creativity, Keep Identity, Style, Pack Type và Candidate Count.

Không train LoRA trong V1. Generator phải optional: manual Character Pack import và reskin vẫn hoạt động khi engine chưa cài.

### 6.7 Generator quality checks

Technical:

- alpha/background;
- minimum resolution;
- full body not clipped;
- canvas/anchor validity;
- no text/grid/watermark;
- no duplicate panel.

Consistency:

- palette distance;
- head/body proportion;
- outline consistency;
- feature similarity;
- pose compliance;
- extra/missing limb heuristic.

Score chỉ là gợi ý; approval của user là authority cuối.

---

## 7. Người dùng mục tiêu

### Primary persona - Reskin Operator

Người dùng muốn xử lý một hoặc nhiều video hoạt hình mà không phải thành thạo compositing, tracking hoặc audio engineering.

Nhu cầu:

- workflow rõ ràng;
- nhiều automation;
- batch apply;
- preview dễ so sánh;
- biết chỗ nào lỗi;
- không phải xem lại mọi frame;
- final video chất lượng cao.

### Secondary persona - Advanced Reviewer

Người có thể chỉnh mask, anchor, keyframe, layer hoặc transcript khi automation chưa đạt.

Sản phẩm phục vụ primary persona bằng mặc định đơn giản, còn công cụ nâng cao nằm trong panel mở rộng.

---

## 8. Nguyên tắc trải nghiệm

### UX-01 One project, one guided flow

Mỗi project hiển thị một flow duy nhất:

```text
Import -> Objects -> Reskin Demo -> Apply Reskin -> Review -> Export 4K
```

Người dùng có thể quay lại bước trước, nhưng luôn biết:

- đang ở bước nào;
- bước đã hoàn thành hay còn lỗi;
- hành động tiếp theo là gì;
- thay đổi hiện tại ảnh hưởng phần nào.

### UX-02 Global-first, scene-second

Người dùng chọn và gán object ở cấp toàn video trước. Scene chỉ xuất hiện khi:

- cần xem các lần xuất hiện;
- cần sửa track/pose/layer;
- scene có issue;
- người dùng muốn override.

Không yêu cầu lặp cùng một thao tác cho hàng trăm scene.

### UX-03 Automation before configuration

App tự chọn profile tốt dựa trên video và phần cứng. Các setting nâng cao không chặn flow mặc định.

### UX-04 Review by exception

Scene đủ confidence tự được đánh dấu Ready. Người dùng tập trung vào danh sách lỗi được sắp theo mức độ.

### UX-05 Preview before expensive processing

Mọi batch reskin/render đều có preview nhanh trên representative scenes trước khi chạy toàn video.

### UX-06 Non-blocking jobs

Job dài không dùng modal khóa app. Người dùng có thể chuyển tab, sửa phần khác hoặc đóng/mở lại app.

### UX-07 Safe and reversible

Operation quan trọng có undo/version hoặc Trash. Không ghi đè source/final output cũ.

---

## 9. Luồng hoạt động tối ưu

## Step 1 - Import & Analyze

### Mục tiêu người dùng

Đưa video vào và để hệ thống chuẩn bị project tự động.

### Giao diện

- Drop zone/chọn file.
- Tên project tự lấy từ filename nhưng sửa được.
- Output profile mặc định: `4K Master`, có thể đổi sau.
- Thẻ kiểm tra GPU, disk và model.
- Nút chính duy nhất: **Phân tích video**.

### Hệ thống tự làm

1. Probe codec, resolution, FPS, timebase, audio và duration.
2. Tạo proxy nhẹ để preview.
3. Phát hiện scene/shot theo nội dung.
4. Chọn keyframe đại diện cho mỗi scene.
5. Trích audio/waveform.
6. Khởi chạy object discovery.
7. Ước tính disk/time theo hardware.

### Kết quả

- Video có timeline và scene boundaries.
- Object candidates bắt đầu xuất hiện dần trong màn Objects.
- User không phải bấm “cắt cảnh” riêng nếu mặc định đã hợp lý.

### Acceptance criteria

- User thấy preview/progress trong vòng thời gian hợp lý.
- Có thể cancel và resume analysis.
- Restart app không mất scene/object candidates đã hoàn thành.
- Video CFR/VFR đều map về canonical timebase chính xác.

---

## Step 2 - Choose Objects

### Mục tiêu người dùng

Thấy các nhân vật/đồ vật xuất hiện và chọn những object muốn thay.

### Giao diện chính

**Object Gallery toàn video**, mỗi card gồm:

- thumbnail tốt nhất;
- tên tạm như `Nhân vật 1`, `Ghế 1`;
- loại: Character/Prop/Other;
- số scene và tổng thời gian xuất hiện;
- confidence grouping;
- nút `Thay object này`;
- nút `Bỏ qua`;
- nút mở occurrences.

Toolbar:

- filter Character/Prop/Selected/Uncertain;
- search/name;
- select multiple;
- `Tìm thêm object` bằng click/bbox trên canvas;
- merge/split object group.

### Hệ thống tự làm

- Detect candidates trên keyframes.
- Tạo mask và thumbnail.
- Track trong từng scene.
- Gợi ý group occurrences của cùng một object xuyên scene.
- Chấm confidence cho detection, track và grouping.

### Người dùng làm

1. Đổi tên role nếu cần.
2. Chọn object cần thay.
3. Merge nếu cùng object bị chia thành nhiều card.
4. Split nếu hệ thống gộp nhầm.
5. Thêm object bằng click/box khi bị bỏ sót.

### Convenience requirements

- Không cần mở scene để chọn object thông thường.
- Hover/card preview cho thấy nhanh các occurrences.
- Merge/split có preview impact và undo.
- Batch select nhiều object trước khi sang Reskin.
- App ghi nhớ quyết định bỏ qua.

### Acceptance criteria

- Mỗi selected object có stable Object Role ID.
- Tất cả occurrences có thể truy cập từ card.
- Uncertain grouping được đưa vào Review, không tự áp asset im lặng.

---

## Step 3 - Assign New Looks

### Mục tiêu người dùng

Đưa ảnh/Character Pack mới vào một lần và áp dụng cho object xuyên suốt video.

### Giao diện

Mỗi selected object có một Reskin Mapping card:

```text
Object gốc | -> | Asset/Character Pack mới | Preview | Status
```

Nguồn asset:

- import PNG trong suốt;
- import nhiều pose;
- chọn Character Pack có sẵn;
- reuse asset đã dùng trong project khác nếu library hỗ trợ.

### Quick flow mặc định

1. Chọn object.
2. Kéo ảnh mới vào.
3. Hệ thống xóa nền/validate alpha nếu cần.
4. Hệ thống đề xuất anchor và scale.
5. Mở **Reskin Demo** trên 3-5 representative scenes.
6. Xem Before/After và chỉnh asset/anchor/scale/pose nếu cần.
7. User chọn **Duyệt Demo & Áp dụng toàn video**.

### Reskin Demo - yêu cầu bắt buộc

Reskin Demo là bước an toàn giữa việc chọn asset và xử lý video thật. Hệ thống không tự chạy apply-all ngay sau upload asset.

Demo phải chọn tự động các cảnh đại diện, ưu tiên:

- cảnh object xuất hiện rõ nhất;
- pose/góc nhìn khác nhau;
- cảnh có chuyển động;
- cảnh có occlusion hoặc background phức tạp;
- cảnh confidence thấp nhất nếu có.

Demo UI gồm:

- danh sách 3-5 scene demo;
- video loop ngắn cho từng scene, không chỉ một ảnh tĩnh;
- chế độ Original, Result, 50/50, Wipe và Blink;
- nút play đồng bộ Before/After;
- quick controls: asset, pose strategy, anchor, scale, offset, removal mode;
- `Tạo lại Demo` sau khi sửa;
- trạng thái từng demo scene: Good/Needs adjustment/Failed;
- ước tính thời gian và dung lượng khi apply toàn video;
- CTA chính chỉ bật khi ít nhất một demo hợp lệ: **Duyệt Demo & Áp dụng toàn video**;
- CTA phụ: **Quay lại chọn asset**.

Demo sử dụng proxy/resolution thấp để trả kết quả nhanh nhưng phải dùng cùng transform, tracking, removal và compositing logic với final pipeline. Hệ thống phải ghi rõ `Demo Quality` để người dùng không nhầm với final 4K.

Nếu demo không đạt, người dùng có thể:

- đổi asset/Character Pack;
- chọn pose khác;
- sửa anchor/scale;
- sửa mask trên scene demo;
- chọn scene demo khác;
- hủy mapping mà không tạo batch artifacts toàn video.

### Character Pack

Character Pack V1 hỗ trợ:

- manifest;
- preview;
- standing/sitting/walking/talking/back/three-quarter nếu có;
- mỗi pose có anchor;
- fallback pose;
- pack version.

Một PNG vẫn được chấp nhận như Simple Asset nhưng app phải nói rõ hạn chế pose.

### Hệ thống tự làm

- Track mask xuyên scene.
- Suy ra transform, anchor, scale và rotation.
- Chọn pose phù hợp từ pack.
- Remove/inpaint object gốc.
- Composite asset mới.
- Xử lý layer/occlusion cơ bản.
- Tạo issues khi pose thiếu, track mất, edge lỗi hoặc contact sai.

### Advanced correction

Chỉ mở khi cần:

- point+/point-/bbox/brush sửa mask;
- anchor presets/custom;
- scale/offset/rotation;
- pose override;
- layer front/behind;
- keyframe correction;
- clean plate/patch/inpaint mode.

### Acceptance criteria

- Một mapping được áp cho toàn bộ occurrences hợp lệ.
- Scene confidence cao không cần user mở.
- Sửa một segment không bắt buộc recompute toàn video.
- Thay asset khác invalidate composite/render liên quan, không chạy lại ASR.

---

## Step 4 - Preserve Original Audio

### Mục tiêu người dùng

Video reskin giữ nguyên chính xác voice, nhạc nền và hiệu ứng của video nguồn mà không cần thiết lập audio.

### Hệ thống tự làm

- Giữ nguyên audio stream khi codec/container cho phép.
- Nếu phải remux/transcode, giữ duration, sample rate/channels hợp lệ và không tạo drift.
- Gắn audio theo canonical timeline sau khi ghép các scene reskin.
- Không chạy Demucs, Whisper, dịch hoặc TTS trong Phase 1.
- Kiểm tra audio stream, duration, silence bất thường và A/V sync trước Complete.

### Giao diện

Không tạo một workspace Language riêng trong Phase 1. Project Summary hiển thị:

- `Audio: Giữ nguyên từ video nguồn`;
- codec/channels/duration;
- nút preview audio cùng Reskin Demo;
- cảnh báo nếu source không có audio hoặc audio không thể remux trực tiếp.

### Phase 2

Sau khi Phase 1 đạt release gate, thêm workspace Language với transcript, translation, speaker/voice mapping, per-utterance regeneration và timing sync. Data/job architecture Phase 1 phải chừa extension point nhưng không triển khai UX/processing này trước.

### Acceptance criteria

- Final proxy và output phát đúng audio nguồn.
- A/V drift nằm trong tolerance đã chốt.
- Reskin correction không làm thay đổi audio.
- Project không tải các model/dependency localization để hoàn thành Phase 1.

---

## Step 5 - Review

### Mục tiêu người dùng

Không phải xem lại toàn bộ từng frame nhưng vẫn biết video có thể xuất hay chưa.

### Review Summary

- Object coverage: số object/occurrence đã xử lý.
- Reskin coverage: scene Ready/Needs review/Blocked.
- Video checks: A/V sync, missing asset, black frame, audio silence/clipping.
- Estimated final render time/disk.

### Review Queue

Filter:

- Blocker/Warning.
- Object/Mask/Pose/Composite.
- Original audio/A-V sync.
- Scene/Object.

Click issue:

1. mở đúng scene/frame/object;
2. hiển thị lý do và suggested fix;
3. user sửa hoặc accept/waive;
4. hệ thống re-check;
5. chuyển issue tiếp theo.

### Auto-pass

- Scene đủ threshold có thể tự Ready.
- User có thể yêu cầu manual approval mọi scene.
- Blocker phải được resolve hoặc explicit accept trước final render.

### Acceptance criteria

- Không có issue mơ hồ chỉ ghi “failed”.
- Mỗi issue có location, reason và action.
- Change upstream làm affected item Dirty và đưa lại vào queue.

---

## Step 6 - Export 4K

### Mục tiêu người dùng

Xuất một video hoàn chỉnh, đúng độ nét, đúng duration và dễ tìm.

### Export presets

**Primary preset:**

- `4K Master`: 3840x2160, MP4 H.264 hoặc HEVC nếu hỗ trợ, AAC, high quality.

**Additional presets:**

- 1080p Master.
- Source resolution.
- 4K vertical 2160x3840 nếu chọn 9:16.
- Draft Preview.

### 4K behavior

- Nếu source dưới 4K, app phải ghi rõ đây là upscale.
- Scaling mode: contain/crop/fill/AI upscale adapter nếu có.
- Không gọi output “giữ nguyên 4K” nếu source không phải 4K.
- Preview dùng proxy; final composite/render dùng target resolution hoặc quality-safe scaling.
- Kiểm tra VRAM/disk trước render.
- NVENC được dùng nếu codec/GPU/driver hỗ trợ; CPU fallback nếu không.

### Render variant

Mỗi variant gồm:

- resolution/aspect;
- codec/quality;
- subtitle mode;
- audio/stems;
- output filename/location.

### Output validation

Trước khi đánh dấu Complete:

- file mở/probe được;
- đúng resolution/codec;
- đúng stream audio;
- duration/frame/timebase trong tolerance;
- không A/V drift đáng kể;
- không missing frames/artifacts;
- output không phải `.partial`.

### Acceptance criteria

- Render cancel/restart/resume được.
- Không ghi đè output cũ; tạo version.
- User có thể Open Folder/Play/Render Another Variant.

---

## 10. Information architecture

### Home

- Primary navigation: Projects, Channels, Character Library, Jobs, Storage/System.
- Recent projects and video jobs.
- New Project and Create Character shortcuts.
- Search/filter across projects, videos and characters.
- Overall jobs and storage/capability status.

### Project Detail

```text
Overview | Videos | Cast Mapping | Outputs
```

- Overview: aggregate progress, blockers, activity and storage.
- Videos: grid/list with pipeline status and primary CTA.
- Cast Mapping: reusable role-to-pack suggestions/mappings.
- Outputs: versioned renders grouped by Video Item.

### Character Library

```text
Ready | Draft/Generating | Archived
```

- Character grid/list, search/filter and usage.
- Import Character Pack.
- Create from Reference.
- Open Character Detail/Pack Versions/Generator Review.

### Project Shell

```text
Top: Home | Project | Save/Version | Hardware | Jobs
Steps: Import | Objects | Reskin Demo | Apply Reskin | Review | Export
Center: Current workspace
Bottom: Timeline/waveform when relevant
Right: Context properties or issue detail
```

### Mobile/responsive

Không phải mục tiêu. UI tối ưu desktop tối thiểu 1440x900; hỗ trợ 1920x1080 và 4K display scaling.

---

## 11. Functional requirements

### FR-PM Project/video management

- Project chứa nhiều Video Items.
- Aggregate status/progress/issue/storage từ video jobs.
- Project Detail có Overview, Videos, Cast Mapping và Outputs.
- Video Item có state machine và primary next action.
- Output version gắn đúng Project/Video Item/project version.
- Archive/restore Project; không hard-delete artifacts dùng chung.

### FR-CH Channel management

- CRUD/archive Source và Production Channels.
- Gán channel cho Project và hiển thị video/output liên quan.
- Channel defaults cho output profile và Character Set.
- Không phụ thuộc external platform API trong Phase 1.

### FR-CL Character Library

- Workspace-level reusable Characters và versioned Packs.
- Search/filter/sort, usage references và status.
- Import/validate/preview Character Pack.
- Pin Pack Version trong ReskinMapping.
- Archive/restore và reference-safe deletion.
- Asset Picker hiển thị pose coverage/compatibility.

### FR-CG Character Generator

- Import one/multiple reference images.
- Preprocess/crop/background removal.
- Generate/edit Character Profile.
- Generate contact-sheet candidates và individual Core panels.
- Per-panel approve/regenerate/replace/crop/flip/anchor.
- Technical/consistency validation.
- Save versioned pack vào Character Library.
- Optional Reskin Demo test.
- Generator unavailable không chặn manual pack import/reskin.

### FR-01 Project và resume

- Backend là source of truth.
- Auto-save atomic.
- Restore đúng project, step, scene, object và playhead.
- Schema version/migration.
- Job/artifact đã hoàn thành không mất sau restart.

### FR-02 Media ingest

- Probe codec/resolution/FPS/CFR/VFR/audio.
- Proxy và canonical timebase.
- Disk/time estimate.
- Capability checks.
- Import progress/cancel/retry.

### FR-03 Scene analysis

- Content-aware detection.
- Split/merge/disable.
- Boundary frame-accurate.
- Representative keyframes.
- Re-detect có impact warning.

### FR-04 Object discovery và grouping

- Candidate detection trên toàn video.
- Multi-object mask/track.
- Cross-scene Object Role suggestions.
- Object Gallery và occurrences.
- Merge/split/add/ignore.
- Confidence/uncertainty issues.

### FR-05 Reskin mapping

- Map Object Role -> asset/pack.
- Batch apply toàn video.
- Representative preview.
- Transform/anchor/pose/layer.
- Partial correction/recompute.
- Removal/inpainting modes.

### FR-06 Character asset management

- PNG/simple asset.
- Character Pack manifest/validator.
- Pack library và version.
- Missing pose/anchor issue.
- Legacy six-pose import.

### FR-07 Original audio preservation

- Preserve/remux source audio automatically.
- Maintain canonical timing and A/V sync.
- Do not require audio configuration in the happy path.
- Validate audio stream and duration before Complete.
- Keep adapter/domain extension points for Phase 2 localization.

### FR-08 Review/QC

- Unified Review Queue.
- Severity/reason/location/action.
- Auto-pass threshold.
- Dirty dependency invalidation.
- Resolve/accept audit state.

### FR-09 Jobs

- Persistent state.
- Step/dependency/resource class.
- Progress, ETA estimate, cancel, retry, resume.
- Structured actionable errors.
- Global Job Center.

### FR-10 4K render

- 3840x2160 primary.
- Source/upscale distinction.
- GPU capability/fallback.
- Variant matrix.
- Output validation/versioning.

### FR-11 Storage/cleanup

- Storage breakdown.
- Cleanup preview.
- Trash/restore.
- Protect source/final/shared artifacts.
- Path containment.

### FR-12 Undo/versioning

- Undo/redo editor actions.
- Snapshot trước batch change.
- Output/project version không ghi đè.

---

## 12. Non-functional requirements

### Reliability

- Force-close không làm corrupt project.
- Job retry không duplicate output/entity.
- Completed chỉ sau validation.

### Performance

- UI không block bởi job backend.
- Proxy playback mượt trên hardware support tier.
- Cache analysis/track/audio giữa render variants.
- Metric theo hardware, resolution, duration và object count.

### Quality

- Mask/track: IoU/J&F, jitter, identity switch, corrections/minute.
- Composite: edge halo, contact, occlusion, flicker.
- Audio: source-stream preservation, duration và A/V drift.
- Render: resolution, duration, stream, frame integrity.

### Privacy/local-first

- Visual/reskin/render local mặc định.
- Phase 1 không cần gửi media/audio ra provider localization.
- Không gửi media ra ngoài khi người dùng chưa chọn provider online.

### Maintainability

- Adapter cho models/providers.
- Typed APIs.
- Migration/contract tests.
- Không duplicate source of truth giữa DB/Zustand/filesystem.

### Accessibility

- Keyboard cho play/frame step/next issue/undo.
- Status không chỉ dùng màu.
- Focus/labels/tooltips cho controls chính.

---

## 13. Core data model

| Entity | Vai trò |
|---|---|
| SourceChannel | Nhóm nguồn video và project references |
| ProductionChannel | Nhóm output và defaults |
| Project | Container nhiều Video Items, channels, defaults và aggregate status |
| VideoItem | Đơn vị chạy pipeline reskin và có outputs riêng |
| ProjectCastMapping | Role/class hint -> Character Pack Version suggestion |
| MediaAsset | Source/proxy/audio/image/render artifact |
| Scene | Khoảng time/frame và status |
| ObjectCandidate | Detection chưa được user xác nhận |
| ObjectRole | Object toàn video đã group/xác nhận |
| Occurrence/Track | ObjectRole trong một scene |
| Character | Identity dùng chung và metadata/style |
| CharacterPackVersion | Versioned views/poses/anchors/validation |
| CharacterAsset | Một pose/view image trong pack |
| CharacterGeneration | Reference/profile/job/candidates/approvals |
| ReskinMapping | ObjectRole -> Character Pack Version + strategy |
| Motion/CompositeOverride | Transform/keyframe/layer/inpaint corrections |
| QCItem | Issue/resolution/acceptance |
| Job/JobStep | Processing state/checkpoint/dependency |
| RenderVariant/Manifest | Output configuration và validation |

---

## 14. Error/recovery requirements

| Tình huống | Hành vi |
|---|---|
| Thiếu disk | Dừng trước job hoặc checkpoint an toàn; chỉ dung lượng cần |
| GPU OOM | Retry profile/chunk nhỏ hoặc fallback nếu được |
| Tracking mất object | Tạo issue tại frame đầu; correction + partial propagate |
| Group nhầm object | Split group và recompute affected mapping |
| Pose thiếu | Dùng fallback có cảnh báo hoặc yêu cầu override |
| Inpaint lỗi | Cho đổi mode/clean plate và tạo issue |
| Render fail | Giữ checkpoint/log; output partial không được Complete |
| App crash | Startup reconcile; resume/retry từ step gần nhất |

---

## 15. Release success gates

### Flow gate

Một người dùng mới có thể hoàn thành:

```text
Import -> chọn object -> gán asset -> duyệt Reskin Demo -> xử lý issues -> export 4K với audio gốc
```

mà không cần đọc tài liệu kỹ thuật.

### Foundation gate

- Project/job survive restart.
- Lint/type/build/tests green.
- Clean install reproducible.
- Cleanup/path safety pass.

### Production management gate

- Project chứa/quản lý nhiều Video Items.
- Source/Production Channel filters và defaults hoạt động.
- Video/output/progress được tổng hợp đúng vào Project.

### Character Library gate

- Pack import/validation/versioning/reuse hoạt động.
- Pack đang được dùng không bị ghi đè/xóa ngoài ý muốn.
- Asset Picker hiển thị compatibility và mở Reskin Demo.

### Character Generator gate

- Reference -> Character Profile -> candidates -> approved Core Pack hoạt động.
- User có thể regenerate một panel mà không chạy lại toàn pack.
- Generator/ComfyUI unavailable không chặn manual Library/reskin flow.

### Reskin gate

- Object Gallery, grouping, batch mapping và partial correction hoạt động.
- Benchmark set đạt quality target đã chốt.

### Original audio gate

- Voice/BGM/SFX nguồn được giữ nguyên.
- A/V sync và duration validation pass.
- Reskin pipeline không phụ thuộc translation/TTS services.

### 4K gate

- 4K output đúng resolution/codec/duration/audio.
- Render resume/fallback/validation pass.
- Source-below-4K được ghi rõ upscale.

---

## 16. Product decisions mặc định để lập Master Plan

1. Primary user là solo Reskin Operator.
2. Default Phase 1 flow có sáu bước: Import, Objects, Reskin Demo, Apply Reskin, Review, Export.
3. Object được quản lý global theo Object Role; scene là nơi occurrence và correction.
4. Character Pack V1 ưu tiên PNG pose; simple PNG vẫn được hỗ trợ.
5. Phase 1 giữ audio/voice gốc; localization và voice replacement là Phase 2.
6. 4K Master là output chính; dưới 4K được mô tả là upscale.
7. Phase 1 xử lý visual local và giữ audio gốc; provider localization chỉ được xem xét ở Phase 2.
8. Không upload/publish trong V1.
9. Review-by-exception là mặc định.
10. Không rewrite stack nếu migration incremental đáp ứng mục tiêu.
11. Project chứa nhiều Video Items; Channel là metadata phân loại nguồn/đầu ra.
12. Character Library dùng chung toàn Workspace và pack được version hóa.
13. Character Generator là optional adapter; Core Pack có sáu asset bắt buộc.
14. Contact sheet duyệt design trước, sau đó refine từng panel.
15. Không train LoRA và không expose node graph trong V1.

---

## 17. Research UX áp dụng

- [Adobe Text-Based Editing](https://helpx.adobe.com/premiere/desktop/edit-projects/edit-video-using-text-based-editing/overview-of-text-based-editing.html): transcript gắn với timecode và workspace theo công việc.
- [Descript editor interface](https://help.descript.com/hc/en-us/articles/37585546799757-The-editor-interface): kết hợp script, scene, canvas và timeline mà vẫn thân thiện người mới.
- [Runway Remove Background](https://help.runwayml.com/hc/en-us/articles/19112532638995-Remove-Background): prompt mask nhanh, refine rồi đưa vào editor.
- [Meta SAM 2](https://github.com/facebookresearch/sam2): promptable multi-object segmentation/tracking phù hợp cho object occurrences, nhưng cần correction flow.
- [NVIDIA FFmpeg GPU guide](https://docs.nvidia.com/video-technologies/video-codec-sdk/13.1/ffmpeg-with-nvidia-gpu/index.html): capability-based hardware encode/decode/transcode; không giả định mọi GPU hỗ trợ giống nhau.
- [Google Doc tham chiếu - Prompt tham khảo/Ref Smart](https://docs.google.com/document/d/1ym5YJonF5Am1v7KibaR2HuVAS1oxi52N8K-0RBCIu44/edit): character reference sheet, consistency/style/negative constraints và character code như `@FARMER`.
- [Diffusers IP-Adapter](https://huggingface.co/docs/diffusers/v0.27.0/using-diffusers/ip_adapter): image-reference conditioning có thể kết hợp ControlNet.
- [ControlNet](https://github.com/lllyasviel/controlnet): pose/edge/depth/segmentation conditioning.
- [ComfyUI](https://docs.comfy.org/): local workflow/API engine cho optional Character Generator.

---

## 18. Product summary

MotionForge 2D V1 phải tạo cảm giác như một hệ thống **quản lý - chọn - thay - xem demo - xuất**, không phải một phòng lab AI.

Tất cả thiết kế và engineering phải phục vụ sáu câu hỏi của người dùng:

1. Project/kênh/video nào đang làm và đang ở trạng thái nào?
2. App đã tìm thấy những object nào?
3. Tôi muốn thay object nào bằng nhân vật nào trong Library?
4. Character Pack có đủ góc/pose cho video này không?
5. Demo cho thấy kết quả sẽ trông như thế nào trước khi xử lý toàn video?
6. Còn lỗi nào trước khi xuất 4K với audio gốc?

Nếu một setting, màn hình hoặc bước không giúp trả lời sáu câu hỏi này, nó không được nằm trong quick flow mặc định.
