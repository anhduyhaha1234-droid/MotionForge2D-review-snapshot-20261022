# MotionForge 2D - Master Plan V3

**Trạng thái:** Approved planning baseline  
**Ngày:** 2026-08-03  
**Căn cứ:** Product Requirements V4 + codebase audit + UX/technology research  
**Mục tiêu Phase 1:** Xây hệ thống quản lý Project/Channel/Video, Character Library/Generator và flow `Import -> Objects -> Reskin Demo -> Apply Reskin -> Review -> Export 4K`, giữ nguyên audio/voice gốc.  
**Lưu ý:** Đây là kế hoạch cấp chương trình. Chưa chia sprint hoặc coding task.

---

## 1. Master outcome

Khi chương trình hoàn thành, một người dùng mới có thể:

1. tạo Source/Production Channel và Project;
2. quản lý nhiều Video Items trong Project;
3. chọn hoặc tạo nhân vật trong Character Library dùng chung;
4. kéo video vào app và chờ hệ thống phân tích;
5. xem Object Gallery toàn video;
6. chọn các nhân vật/đồ vật muốn thay;
7. map Object Role với Character Pack Version;
8. xem Reskin Demo Before/After trên các cảnh đại diện;
9. chỉnh asset và xác nhận áp dụng reskin toàn video;
10. xử lý danh sách ngoại lệ do app phát hiện;
11. xuất video MP4 4K đúng duration với audio/voice gốc.

Người dùng không phải:

- tự cắt video thành clip 3 giây;
- chọn lại cùng object ở từng scene;
- chỉnh từng frame khi track đủ confidence;
- chạy lại toàn pipeline khi sửa một scene/câu;
- xem progress modal khóa app;
- đoán scene nào đang lỗi;
- biết lệnh FFmpeg, model hoặc cấu hình GPU.

---

## 2. Product strategy

### 2.1 Positioning cho giai đoạn này

**MotionForge 2D Phase 1 là một guided reskin studio cho video hoạt hình 2D.**

Năm năng lực lõi:

- **Production Organization:** Project chứa nhiều video, phân loại theo Source/Production Channel.
- **Object Intelligence:** tìm, track và group object xuyên video.
- **Reusable Character System:** Character Library/Pack Versions và generator 2D đơn giản.
- **Global Reskin Mapping:** gán pack một lần cho mọi occurrence.
- **Previewed 4K Delivery:** duyệt Reskin Demo, review ngoại lệ và xuất 4K với audio gốc.

### 2.2 Product principles

1. **Global-first:** người dùng thao tác theo object toàn video trước, scene sau.
2. **Automation-first:** app tự phân tích và đề xuất mặc định.
3. **Review-by-exception:** chỉ mở lỗi cần quyết định.
4. **Preview-first:** thử representative scenes trước batch.
5. **Non-destructive:** không ghi đè source hoặc output cũ.
6. **Resume-safe:** job và project sống qua restart.
7. **Progressive disclosure:** quick flow ít setting; advanced tools khi cần.
8. **4K-aware:** mọi quyết định preview/render phân biệt proxy, source và final resolution.

### 2.3 Không làm trong Master Plan này

- License/copyright workflow.
- Upload/publish YouTube.
- Channel monetization/analytics.
- Full NLE/editor tổng quát.
- Multi-user/cloud collaboration.
- Generative lip-sync bắt buộc.
- Translation, TTS và voice replacement trong Phase 1.
- Auto-generate story/script.
- Rewrite toàn bộ stack.

### 2.4 Approved operating model

```text
Workspace
├── Projects
│   └── Project
│       ├── Source Channel
│       ├── Production Channel
│       ├── Video Items
│       ├── Cast Mapping
│       └── Output Versions
├── Channels
├── Character Library
├── Jobs
└── Storage/System
```

Rules:

- Project chứa nhiều Video Items.
- Channel là metadata phân loại, không phải thư mục project state.
- Character Library dùng chung Workspace.
- ReskinMapping pin Character Pack Version.
- Generator là optional adapter; manual pack import luôn khả dụng.
- Project/video output cũ không tự nâng Character Pack version.

---

## 3. Code reality và hướng chuyển đổi

### 3.1 Những gì code hiện tại đã có

- FastAPI backend và Next.js frontend.
- Project/channel cơ bản.
- Video import/ingest/probe.
- Scene detection/chunking/stitching.
- Frame extraction.
- SAM2/contour adapter và mask preview.
- Object create/list/delete/propagate/gallery.
- Motion extraction và replacement settings.
- Preset/character pose hiện tại.
- Inpainting/composite/preview/render.
- Audio separate/transcribe/translate/TTS/remux.
- GPU/NVENC detection.
- Cleanup/export ZIP.
- 144 Python tests pass; TypeScript check pass.

### 3.2 Những giới hạn chặn flow mới

| Giới hạn hiện tại | Chặn trải nghiệm nào | Cần thay đổi |
|---|---|---|
| Object chủ yếu thuộc scene | Phải chọn lại nhiều lần | ObjectCandidate -> ObjectRole -> Occurrences |
| Không có cross-scene grouping | Không có Object Gallery thật | Discovery/grouping pipeline + confirm UI |
| Scene A-E là navigation chính | Flow nặng theo kỹ thuật | Sáu bước theo mục tiêu người dùng |
| Job chỉ ở RAM | Không resume | Durable job DB/checkpoint |
| Project JSON ghi trực tiếp | Rủi ro corrupt/lost update | SQLite + atomic artifacts + migration |
| Dubbing pipeline đã có nhưng chưa cần cho Phase 1 | Dễ làm loãng trọng tâm reskin | Giữ code tương thích, không đưa vào quick flow; lập kế hoạch lại ở Phase 2 |
| Progress qua mutation/modal | Khóa/không rõ toàn cục | Global Job Center + event stream |
| Scene status pending/draft/approved | Không biết dirty/issue/block | State machine + QC/invalidation |
| Base64 mask/crop payload | Không scale nhiều object/frame | Artifact IDs/URLs + thumbnail cache |
| Direct `rmtree` | Cleanup/delete rủi ro | Trash + containment + preview |
| `projects.py` gần 2.000 dòng | Khó thay domain an toàn | Modular routers/application services |
| Audio deps/hardcoded FFmpeg | Clean machine có thể fail | Dependency profiles + capability manager |
| ESLint 28 errors/21 warnings | UI foundation thiếu ổn định | Quality gate trước UI rewrite |
| `channels.json` bị test/dev ghi lặp nhiều Channel A/B/Test Channel | Test data và production data không cô lập | Không reuse storage này; migrate schema mới và test root riêng |
| Channel model chỉ có name/target_lang/default preset | Không phân biệt source/production, không aggregate videos | Rebuild domain/repository/UI Channel Management |
| Preset manager sinh/đọc sáu pose theo thư mục | Có giá trị prototype nhưng thiếu identity/version/manifest | Giữ validation/image helpers; rebuild thành Character Library/Pack domain |

### 3.3 Quyết định migration

- **Không xóa service cũ ngay.** Bọc chúng bằng application/domain services.
- **Không big-bang UI.** Xây Project Shell trước, chuyển từng vertical flow.
- **Không bỏ `project.json` ngay.** Tạo importer/migration sang store mới và export manifest tương thích.
- **Không thêm AI model trước foundation.** Dùng SAM2/contour hiện có để xây flow đúng, sau đó tối ưu quality.

### 3.4 Build strategy decision

**Quyết định: hybrid rebuild, không full rewrite và không tiếp tục vá UI/domain cũ.**

Giữ stack và media engines; xây mới domain/persistence/API application layer và UI shell theo PRD V4.

| Layer | Quyết định | Lý do |
|---|---|---|
| Python/FastAPI runtime | Giữ | Phù hợp FFmpeg/OpenCV/SAM2; tests và services đã tồn tại |
| Next.js/React/TanStack/Konva | Giữ stack | Đủ khả năng làm desktop editor; không có bằng chứng đổi framework giải quyết vấn đề |
| FFmpeg probe/extract/render/GPU helpers | Giữ + harden | Vertical pipeline đã có giá trị và test coverage |
| Scene detection | Giữ + sửa deprecation/timebase | Logic phù hợp nhưng cần golden CFR/VFR tests |
| SAM2/contour adapters | Giữ qua adapter contract | Nền tracking sẵn có; cần anomaly/correction flow |
| Motion/compositing/inpainting | Giữ lõi thuật toán, refactor interface | Có thể tái sử dụng trong preview/apply/render jobs |
| Project/channel JSON storage | Thay mới | Không đáp ứng multi-video, transactions, concurrent jobs, integrity |
| In-memory JobService | Thay mới | Không resume/reconcile/resource schedule |
| `projects.py` monolithic routes | Tách/xây lại application API | Domain mới lớn hơn, vá tiếp sẽ tăng coupling |
| Zustand persisted project state | Thay ownership | Backend DB/TanStack Query là authority; Zustand chỉ editor transient |
| Screen A-E navigation/UI | Xây mới theo Project Shell | Mental model cũ không phù hợp Projects/Library/object-first demo flow |
| CompositeCanvas interaction math | Trích xuất/reuse có test | Có logic canvas đáng giữ nhưng component 738 dòng và lint lỗi cần viết shell/component mới |
| ChannelDashboard | Xây mới | Model/UI hiện không đáp ứng source/production/project/video hierarchy |
| PresetManager | Thay UI/domain; reuse utilities/assets | Character Library/versions/generator cần model mới |
| Dubbing UI/services | Đóng khỏi Phase 1, giữ code cô lập | Audio gốc Phase 1; tránh xóa để dùng Phase 2 sau audit |

Không nên build repository mới hoàn toàn từ số 0 vì sẽ mất các media services/tests đã chứng minh. Không nên tiếp tục sửa trực tiếp Screen A-E vì navigation và state model đã sai với product mới. Hướng đúng là **strangler migration**: app shell/domain mới chạy cạnh legacy services, chuyển từng vertical slice, rồi retire legacy UI/routes.

---

## 4. Target user journey

## Phase U0 - Organize Production

### User sees

- Workspace Home with Projects, Channels, Character Library and Jobs.
- Source/Production Channel manager.
- Project Detail: Overview, Videos, Cast Mapping, Outputs.
- Video cards with current state and next action.

### User actions

- create/select Source and Production Channels;
- create a Project;
- add multiple Video Items;
- set default output profile/Character Set;
- resume the next actionable video.

### Exit condition

- Project and channels exist in durable store.
- At least one Video Item is ready for Import/Analyze.
- Project defaults and storage location are known.

## Phase U1 - Import

### User sees

- Drop video.
- Project name.
- `4K Master` là output profile mặc định.
- Hardware/disk readiness ngắn gọn.
- Một CTA: **Phân tích video**.

### System does

- preflight;
- proxy;
- scene detection;
- keyframe extraction;
- waveform/audio preparation;
- starts object discovery.

### User value

Không phải hiểu chunking/model/FPS trước khi bắt đầu.

### Exit condition

- Source hợp lệ.
- Canonical timebase được lưu.
- Scene/keyframes sẵn sàng.
- Object discovery đã bắt đầu hoặc có reason rõ nếu unavailable.

---

## Phase U2 - Objects

### User sees

Một Object Gallery toàn video thay vì danh sách scene trước.

Object card:

- best thumbnail;
- name/type;
- occurrence count;
- time coverage;
- confidence;
- quick preview;
- `Thay object này` / `Bỏ qua`.

### System does

- detect objects trên representative frames;
- track trong scene;
- compute embeddings/features phù hợp;
- suggest same-object grouping across scenes;
- generate uncertain grouping issues.

### User actions

- select/ignore;
- rename;
- merge/split groups;
- add missed object bằng click/box;
- inspect occurrences khi cần.

### Exit condition

- Selected Object Roles có stable identity.
- Group uncertain đã được confirm hoặc đưa Review.
- Mỗi role có occurrence/track refs.

---

## Phase U3 - Reskin Demo & Apply

### User sees

Mapping board:

```text
[Object gốc] -> [Drop image / Choose Character Pack] -> [Preview status]
```

### System does

- validates asset/pack;
- proposes anchor/scale/pose strategy;
- selects 3-5 representative scenes;
- creates a Reskin Demo using 3-5 representative scene loops;
- supports Original/Result/50-50/Wipe/Blink comparison;
- regenerates the demo after quick adjustments;
- only after explicit demo approval, processes all valid occurrences;
- creates issues for failures/uncertainty.

### User actions

- drop asset/choose pack;
- choose a pinned Pack Version from Character Library or create/import a character;
- adjust quick settings;
- inspect demo loops with original audio;
- adjust asset/pose/anchor/scale/removal and regenerate demo;
- click `Duyệt Demo & Áp dụng toàn video`;
- open advanced correction only for issues.

### Exit condition

- Every selected Object Role has an approved demo or explicit deferred status.
- Batch draft completed/checkpointed.
- Visual blockers are in Review Queue.

---

## Phase U4 - Preserve Original Audio

### User sees

- `Audio: Giữ nguyên từ video nguồn` in project summary/export.
- Source audio codec/channels/duration.
- Original audio plays with every Reskin Demo and full proxy.
- Warning only when source has no audio or remux requires fallback.

### System does

- preserves/remuxes the original audio stream;
- keeps canonical timing after scene assembly;
- validates audio presence, duration and A/V sync;
- does not run separation, ASR, translation or TTS.

### User actions

- no audio configuration in the happy path;
- preview original audio with demo/final proxy;
- acknowledge only actionable source/remux issues.

### Exit condition

- Original audio is attached to the reskin proxy.
- A/V sync validation passes or an actionable issue exists.
- Reskin changes do not alter the audio stream.

---

## Phase U5 - Review

### User sees

- Coverage summary.
- Unified Review Queue.
- Full proxy player.
- Next Issue action.

### System does

- aggregates visual/audio/project issues;
- rechecks after fix;
- marks downstream dirty when upstream changes;
- calculates final readiness.

### User actions

- fix/accept issue;
- compare original/result;
- scrub full proxy if desired;
- continue to Export when Ready.

### Exit condition

- No unresolved blocker.
- Project version is render-ready.

---

## Phase U6 - Export

### User sees

- `4K Master` primary preset.
- Aspect/codec/quality options.
- Source vs upscale information.
- Time/disk estimate.
- Background render status.

### System does

- builds render plan;
- reuses analysis/track/audio caches;
- uses NVENC when supported, CPU fallback otherwise;
- renders resumably;
- validates final file;
- versions output.

### User actions

- choose variants;
- start/cancel/retry;
- play/open folder;
- render another variant;
- safe cleanup optional.

### Exit condition

- Validated 4K/selected output is available and not partial.

---

## 5. Target UX/UI architecture

### 5.1 Home

- Primary navigation: Projects, Channels, Character Library, Jobs, Storage/System.
- New Project/Create Character shortcuts.
- Recent projects with aggregate video progress and last activity.
- Recent video jobs and blockers.
- Search/filter across projects/videos/characters.
- Storage and system readiness.

### 5.1A Project Detail

```text
Overview | Videos | Cast Mapping | Outputs
```

- Overview: aggregate progress, activity, blockers, defaults and storage.
- Videos: grid/list, bulk selection and state-driven CTA.
- Cast Mapping: reusable role hints -> pinned Character Pack Versions.
- Outputs: versioned results grouped by Video Item.

### 5.1B Character Library

```text
Ready | Draft/Generating | Archived
```

- Character cards show thumbnail, Character ID, Pack Version, coverage, status and usage.
- Actions: Import Pack, Create from Reference, New Version, Validate, Test Demo, Archive.
- Character Detail contains Profile, Pack Versions, Assets/Anchors, Generator Jobs and Usage.

### 5.1C Character Generator

Guided steps:

```text
Reference -> Profile -> Pack Type -> Contact Sheet
-> Panel Review -> Anchors/Validation -> Save Version
```

The UI hides model/node parameters and provides per-panel candidate/regenerate controls.

### 5.2 Project Shell

```text
┌────────────────────────────────────────────────────────────┐
│ Home | Project | Saved/Version | GPU/Disk | Jobs           │
├────────────────────────────────────────────────────────────┤
│ Import | Objects | Reskin Demo | Apply | Review | Export  │
├──────────────┬──────────────────────────┬──────────────────┤
│ Context/List │ Main Canvas or Editor    │ Properties/Issue │
├──────────────┴──────────────────────────┴──────────────────┤
│ Timeline / Waveform / Issue markers (when relevant)       │
└────────────────────────────────────────────────────────────┘
```

### 5.3 Step behavior

Mỗi step có:

- status icon + text;
- completion percentage chỉ khi meaningful;
- Ready/Needs Review/Processing/Dirty/Blocked;
- primary CTA;
- explanation ngắn;
- no hidden blocking error.

### 5.4 Quick vs Advanced

**Quick default:**

- choose/drop asset;
- preview;
- apply all;
- approve the Reskin Demo before apply-all;
- resolve highlighted issues;
- export.

**Advanced on demand:**

- scene boundaries;
- mask prompt/brush;
- track correction;
- transform/keyframes;
- pose/layer/inpaint;
- original-audio diagnostics/remux fallback;
- codec/scaling details.

### 5.5 Timeline strategy

- Objects: occurrence and confidence markers.
- Reskin: visual issue/keyframe markers.
- Reskin Demo: representative scene loops + visual comparison.
- Review: all issue markers.
- Export: read-only render range/variant context.

Một canonical playhead/timecode được dùng xuyên mọi step.

### 5.6 Global Job Center

- Non-modal.
- Persistent across pages/restart.
- Shows project/job/stage/resource/progress/ETA.
- Cancel/retry/open log/open result.
- Queue policy prevents GPU overload.

### 5.7 UX research decisions

- Adobe: workspace/task focus + transcript linked timecode.
- Descript: document-like transcript plus canvas/timeline.
- ElevenLabs: per-clip editing/regeneration and explicit duration behavior.
- Runway: fast mask prompt/refine before editor.

MotionForge combines these patterns but keeps a guided six-step flow instead of exposing a full professional NLE.

---

## 6. Target domain model

### 6.0 Production hierarchy

```text
Workspace
  -> SourceChannels / ProductionChannels
  -> Projects
      -> VideoItems
          -> ProjectVersion / Processing State / Outputs
      -> ProjectCastMappings
  -> Characters
      -> CharacterPackVersions
          -> CharacterAssets
      -> CharacterGenerations
```

Project aggregate progress is derived from Video Items/jobs/issues; it is not a manually maintained independent status string.

### 6.1 New object hierarchy

```text
ObjectCandidate
  -> user/system confirms/groups
ObjectRole (global identity in project)
  -> has many
ObjectOccurrence (role in one scene/time range)
  -> has one or more
TrackSegment / MaskArtifacts / MotionData
```

This is the most important domain change. It enables one global reskin mapping.

### 6.2 Reskin hierarchy

```text
CharacterAsset or CharacterPackVersion
  -> assigned by
ReskinMapping(ObjectRole, asset, strategy)
  -> expanded into
OccurrenceCompositeDrafts
  -> corrected by optional
CompositeOverrides / Keyframes
```

ReskinMapping must reference immutable/pinned `character_pack_version_id`, not a mutable filesystem path.

### 6.2A Character generation hierarchy

```text
CharacterGeneration
  -> ReferenceAssets
  -> CharacterProfile
  -> GeneratorConfig/Workflow Version
  -> ContactSheet Candidates
  -> PanelGeneration Candidates
  -> Panel Approvals
  -> Pack Validation
  -> CharacterPackVersion
```

Generation artifacts remain traceable but can be cleaned according to retention after an approved Pack Version is promoted.

### 6.3 Original audio reference

```text
SourceAudioAsset
  -> canonical timeline mapping
  -> ProxyAudioReference
  -> FinalRemuxValidation
```

Phase 1 không tạo transcript, translation hoặc generated voice entities. Schema giữ khả năng mở rộng Phase 2 mà không đưa chúng vào flow hiện tại.

### 6.4 Quality hierarchy

```text
QCItem
  location: project/scene/frame/object/audio/render
  stage: discovery/track/reskin/original-audio/render
  severity/reason/evidence/suggestion/status
```

### 6.5 Processing hierarchy

```text
Job
  -> JobSteps
  -> Dependencies
  -> Checkpoints
  -> Input/output Artifacts
```

---

## 7. Technical architecture plan

### 7.1 Persistence

Implement:

- SQLite for domain metadata, status, jobs and QC.
- Filesystem for source/proxy/masks/frames/audio/renders.
- Artifact registry with IDs, hash, producer, config/version and validation state.
- Atomic temp-write -> validate -> promote.
- Migration/import from existing `project.json` v2.
- Exportable project manifest.

### 7.2 Durable processing

Implement job classes:

- `ANALYZE_MEDIA`
- `DISCOVER_OBJECTS`
- `TRACK_OCCURRENCES`
- `GROUP_OBJECTS`
- `GENERATE_RESKIN_PREVIEW`
- `APPLY_RESKIN`
- `GENERATE_CHARACTER_CONTACT_SHEET`
- `GENERATE_CHARACTER_PANEL`
- `VALIDATE_CHARACTER_PACK`
- `ATTACH_ORIGINAL_AUDIO`
- `RUN_QC`
- `RENDER_VARIANT`
- `VALIDATE_OUTPUT`
- `CLEANUP`

Each job declares resource class, dependencies, cache key, cancellation/checkpoint behavior and output artifacts.

### 7.3 Modular backend

Target modules:

```text
app/domain/
  channels projects videos characters scenes objects reskin qc jobs renders artifacts
app/application/
  commands queries orchestration
app/infrastructure/
  sqlite filesystem ffmpeg models providers generators
app/api/routes/
  channels projects videos characters scenes objects reskin qc jobs renders system
```

Migrate incrementally; service implementation may remain in current folders until moved with tests.

### 7.4 Frontend architecture

Target feature modules:

```text
features/workspace-home
features/channels
features/projects
features/video-items
features/character-library
features/character-generator
features/project-shell
features/import
features/objects
features/reskin
features/review
features/export
features/jobs
features/timeline
shared/ui
shared/api
```

Rules:

- TanStack Query owns server state.
- Zustand owns transient editor/tool/navigation state only.
- One restore path.
- API client generated/typed from schema when practical.
- Component boundaries follow domain/use-case, not arbitrary line counts.

### 7.5 Model/provider adapters

- Scene detector.
- Object detector/grounder.
- Segmentation/tracker.
- Object grouping/re-identification.
- Inpainting.
- Encoder/upscaler.
- Character generator workflow adapter.

Use existing SAM2/contour/FFmpeg as first implementations. Add other backends only after adapter and benchmark contract exists.

### 7.6 4K pipeline

Separate:

- source resolution;
- proxy resolution;
- composite working resolution;
- final target resolution.

Rules:

- UI preview never requires 4K frames for normal editing.
- Masks/motion must transform correctly between coordinate spaces.
- Final assets must meet scale/quality checks.
- Source below 4K uses explicit upscale policy.
- Capability service decides H.264/HEVC/NVENC/CPU.
- Render cache keys include target resolution/codec/scaling.

---

## 8. Program workstreams

## WS-00 Production Management

### Outcome

User quản lý nhiều Project, Video Items, Source/Production Channels và outputs trong một Workspace rõ ràng.

### Deliverables

- SourceChannel/ProductionChannel domain + repository/API/UI.
- Project multi-video aggregate.
- Video Item state machine/cards/bulk actions.
- Project Detail: Overview, Videos, Cast Mapping, Outputs.
- Project defaults và aggregate progress/issues/storage.
- Archive/restore và safe references.
- Migration/import từ legacy project/channel metadata có kiểm tra duplicate.

### Exit gate

- Một Project chứa nhiều video và resume đúng từng video.
- Channel filters/defaults hoạt động nhưng không phụ thuộc external API.
- Output version được tìm từ Project/Video Item.
- Test data không ghi vào production `channels.json` hoặc workspace.

## WS-01 Foundation Stabilization

### Outcome

Codebase có thể phát triển flow mới mà không mất dữ liệu hoặc thất bại trên clean machine.

### Deliverables

- Fix frontend lint errors/warnings theo agreed gate.
- Keep TypeScript/Python tests green.
- Separate optional localization dependencies so Phase 1 clean install does not require them.
- Remove hardcoded FFmpeg user path.
- Atomic persistence baseline.
- SQLite schema/migration framework.
- Durable Job/JobStep framework.
- Structured errors/logs.
- Capability/disk service.
- Trash/path-safe cleanup.
- CI profiles: unit, media integration, GPU, provider.

### Exit gate

- Clean Windows setup passes.
- Force-close project/job recovery passes.
- Lint/type/build/tests pass.
- Delete/cleanup containment tests pass.

---

## WS-02 Project Shell & Guided Flow

### Outcome

User có six-step navigation và biết trạng thái/hành động tiếp theo.

### Deliverables

- Home/recent projects.
- Project Shell.
- Six stepper statuses.
- Canonical routing/session restore.
- Global Job Center.
- Shared empty/loading/error/dirty states.
- Timeline shell/canonical playhead.
- Design tokens/component primitives.
- Keyboard/accessibility baseline.

### Exit gate

- Refresh/restart returns correct project/step/context.
- Long job does not lock UI.
- User can understand current/next step without documentation.

---

## WS-03 Import & Analyze

### Outcome

One action turns source video into scenes, proxy and analysis-ready project.

### Deliverables

- Import drop zone/preflight.
- 4K output intent selection.
- Canonical timebase/CFR-VFR policy.
- Proxy/waveform.
- Scene detection/keyframes.
- Disk/time estimate.
- Analyze job DAG.
- Advanced scene split/merge view.

### Exit gate

- Analyze resumes after restart.
- Boundaries/time mapping pass golden fixtures.
- User does not need manual chunking in happy path.

---

## WS-04 Object Intelligence

### Outcome

User sees and selects objects globally across video.

### Deliverables

- ObjectCandidate schema/storage.
- Representative-frame candidate detection.
- Per-scene multi-object tracking.
- Cross-scene grouping suggestion.
- ObjectRole/Occurrence/Track model.
- Object Gallery cards/filter/search.
- Occurrence preview strip.
- Select/ignore/rename.
- Merge/split/add missed object.
- Confidence and grouping issues.
- Partial recompute/invalidation.

### Exit gate

- One role can represent the same character across multiple scenes.
- Merge/split is reversible and updates affected dependencies.
- Selected roles are ready for global mapping.
- Benchmark records grouping accuracy and correction time.

---

## WS-05 Reskin Studio

### Outcome

User assigns a new look once and applies it across the entire video.

### Deliverables

- Mapping board.
- Simple PNG import/alpha validation.
- Character Pack manifest/import/validator/library.
- Legacy six-pose migration.
- Anchor/scale/pose proposal.
- Representative scene selection.
- Fast preview generation.
- Apply-all job.
- Motion/transform/keyframes.
- Object removal/inpainting modes.
- Occlusion/layer correction.
- Visual QC issue generation.
- Advanced correction tools.

### Exit gate

- Mapping applies across valid occurrences.
- Failed/uncertain occurrences become issues, not silent errors.
- Correction recomputes only affected segments.
- Output preview is stable enough for user approval on benchmark set.

---

## WS-05A Character Library

### Outcome

User import, version, tìm kiếm và tái sử dụng nhân vật cho nhiều Project/Video/Channel.

### Deliverables

- Character/PackVersion/CharacterAsset domain.
- Core six-pose manifest and validators.
- Legacy preset migration/import.
- Library grid/detail/version/usage UI.
- Import/replace/add panel and anchor editor.
- Pack compatibility/coverage calculation.
- Version pinning in ReskinMapping.
- Archive/reference-safe cleanup.

### Exit gate

- Manual Core Pack import -> Ready -> Reskin Demo works.
- Existing video mappings remain pinned after new pack version.
- Invalid/missing pose pack cannot silently appear Ready.

---

## WS-05B Character Generator

### Outcome

User tạo một versioned Core Character Pack từ reference images mà không tương tác node graph/model parameters.

### Deliverables

- Character Profile extraction/editor.
- Generator adapter/capability check.
- Optional local ComfyUI workflow integration.
- Reference preprocessing.
- Contact-sheet candidate generation/review.
- Per-panel generation/regeneration/candidate selection.
- Background/crop/flip/anchor tools.
- Technical/consistency validator.
- Promotion to Character Pack Version.
- Model/GPU resource scheduling and diagnostics.

### Exit gate

- Reference -> approved Core Pack -> Library -> Reskin Demo works.
- Per-panel regenerate does not rerun approved panels.
- Generator unavailable leaves manual Library/reskin fully usable.
- UI exposes simple controls only; workflow version is traceable.

---

## WS-06 Original Audio Preservation

### Outcome

Video reskin giữ nguyên voice, BGM và SFX nguồn mà người dùng không phải cấu hình audio.

### Deliverables

- Source audio artifact/reference.
- Canonical time mapping across scene processing and final assembly.
- Stream-copy/remux strategy when compatible.
- Safe audio transcode fallback when required.
- Original audio playback in Reskin Demo and full proxy.
- Audio presence/duration/stream/A-V sync validation.
- Actionable issue for missing/corrupt/unsupported source audio.
- Phase 2 extension point without shipping ASR/translation/TTS in Phase 1.

### Exit gate

- Reskin Demo and final proxy play original audio in sync.
- Final output preserves source voice/BGM/SFX within accepted codec behavior.
- Reskin correction never changes the original audio content.
- Phase 1 clean install/run does not require localization models/providers.

---

## WS-07 Review & Quality Control

### Outcome

User resolves only important exceptions and knows when video is ready.

### Deliverables

- Unified QCItem model.
- Visual/audio/render reason codes.
- Review Summary.
- Filterable Review Queue.
- Click-to-context navigation.
- Resolve/accept/recheck.
- Auto-pass thresholds.
- Dirty dependency propagation.
- Full proxy preview.
- Readiness gate.

### Exit gate

- Every blocker has location/reason/action.
- Fix returns item to recheck automatically.
- No unresolved blocker reaches final render without explicit acceptance.

---

## WS-08 4K Render & Delivery

### Outcome

User receives validated 4K output reliably.

### Deliverables

- RenderVariant/Manifest.
- 4K Master preset 3840x2160.
- Source vs upscale display.
- Aspect/scaling policy.
- H.264/HEVC capability selection.
- NVENC/CPU fallback.
- Render DAG/checkpoint/resume.
- Cache reuse across variants.
- Output versioning/naming.
- Validation: resolution, codec, streams, duration, frames/timebase, A/V drift.
- Play/open folder/render another.
- Optional subtitles/stems/project export.
- Safe cleanup/storage view.

### Exit gate

- 4K golden renders pass validation.
- Cancel/restart/retry does not corrupt complete output.
- Low-resolution source is labeled/scaled according to chosen policy.
- Completed output can be opened and traced to its project version/config.

---

## WS-09 Performance, Testing & Packaging

### Outcome

Application works consistently on supported Windows hardware.

### Deliverables

- Golden dataset: animation styles, object counts, occlusion, camera motion, source-audio variants, CFR/VFR, 720p-4K.
- Unit/contract/media integration/E2E/GPU/provider/fault/soak suites.
- Mask/track/grouping/composite/audio/render metrics.
- Hardware-tier benchmark harness.
- Windows installer/launcher/update/uninstall.
- Model/dependency manager.
- Diagnostics bundle.
- Performance/storage dashboards.

### Exit gate

- Supported hardware matrix passes.
- No critical data loss/path deletion defects.
- Quality/performance claims have reproducible evidence.
- Installer works on clean target machine.

---

## 9. Program stages

## Stage A - Make the foundation trustworthy

Workstreams:

- WS-00 domain/persistence contracts for production management.
- WS-01 critical foundation.
- UX specification/design system portion of WS-02.
- Domain contracts for ObjectRole, jobs, artifacts and timebase.

Do not start major AI expansion before Stage A gate.

**Program result:** codebase is safe to change; Project, Channel, Video Item and job state can persist/resume reliably.

## Stage B - Create the new product spine

Workstreams:

- Finish WS-02 Project Shell.
- Finish WS-00 Project/Channel/Video management UI and APIs.
- WS-03 Import & Analyze.
- Durable jobs/artifacts integrated into real flow.

**Program result:** users can organize source/production channels, manage multiple videos in one project, and turn an imported video into a resumable analyzed Video Item.

## Stage C - Establish the reusable character system

Workstreams:

- WS-05A Character Library.
- Manual Character Pack import and validation.
- Project Cast Mapping and pinned Pack Version.

**Program result:** users can curate a reusable character library and safely reuse one approved character pack across projects, videos and channels.

## Stage D - Deliver object-first reskin and original-audio path

Workstreams:

- WS-04 Object Intelligence.
- WS-05 Reskin Studio.
- WS-06 Original Audio Preservation.
- Visual and A/V-sync portions of WS-07.

Can overlap Stage C after canonical timebase and artifact foundation are stable.

**Program result:** user maps source roles to pinned library characters, approves representative demo loops, and receives a full-video reskin proxy with unchanged source audio in sync.

## Stage E - Add the guided 2D character generator

Workstreams:

- WS-05B Character Generator.
- Reference-sheet review and panel regeneration.
- Publish approved output as a versioned Character Pack.

This stage can begin after Character Library contracts are stable. It must not block manual pack import or the first reskin alpha.

**Program result:** one simple 2D reference can become a reviewed six-pose pack without model training.

## Stage F - Deliver validated 4K

Workstreams:

- Complete WS-07.
- WS-08 Render & Delivery.
- WS-09 beta hardening/packaging.

**Program result:** full six-step workflow produces validated 4K output.

---

## 10. Dependency map

```text
Persistence + Jobs + Artifacts + Timebase
        |
        +-> Channels/Projects/Video Items -> Project Shell -> Import/Analyze
        |                                                        |
        |                                                        +-> Object Intelligence
        |                                                                    |
        +-> Character Library -> Pack Version -> Cast Mapping ---------------+-> Reskin Demo/Apply -> Visual QC
        |                 |
        |                 +-> Character Generator -> approved Pack Version
        |
        +-> Original audio mapping/remux ------------------------------> Audio QC
                                                                         |
Visual QC + Audio QC + Project readiness --------------------------------+-> 4K Render
```

Critical constraints:

- Cross-scene grouping requires stable Scene/ObjectOccurrence IDs.
- Global reskin mapping requires ObjectRole.
- Review Queue requires normalized QCItem and canonical location/timecode.
- Partial regenerate/recompute requires dependency/artifact graph.
- Reliable 4K requires coordinate/timebase contracts and durable render jobs.
- Cross-project reuse requires immutable/pinned Character Pack Versions.
- Character generation is optional input to the Library; it is not a hard dependency for reskin.

---

## 11. Quality gates

### G0 - PRD/MP approved

- Six-step flow approved.
- Project/Channel/Video hierarchy approved.
- Character Library and Generator scope approved.
- Object-global strategy approved.
- Timing-sync and 4K scope approved.
- Out-of-scope items accepted.

### G1 - Foundation green

- Clean dependency install.
- Python/TypeScript/lint/build/test gates green.
- Project/job survive force-close.
- SQLite/artifact migration tests pass.
- Cleanup/delete path safety pass.

### G2 - Production shell alpha

- Channel, Project and multi-video management works without shared JSON files.
- New shell/restore/job center usable.
- Import/analyze/resume works.
- Scene/timebase fixtures pass.

### G2.5 - Character Library alpha

- Manual Character Pack import, six-pose validation and version pinning work.
- One approved pack can be reused across at least two projects without copying mutable state.
- Project Cast Mapping resolves source Object Roles to pinned Pack Versions.

### G3 - Object-first reskin alpha

- Object Gallery/grouping/selection works.
- Global mapping and representative preview works.
- Apply-all/checkpoint/correction works.
- Visual issues are actionable.

### G4 - Reskin Demo and original audio alpha

- Representative scene-loop demo and comparison modes work.
- Demo adjustments regenerate without apply-all.
- Explicit approval gates full-video processing.
- Original audio playback/remux and A/V sync checks work.

### G4.5 - Character Generator alpha

- One reference image produces the required six-pose review sheet through an adapter-based workflow.
- User can approve/regenerate individual panels and publish only a complete validated pack.
- Generator failure never blocks manual pack import or existing library usage.

### G5 - 4K beta candidate

- Unified Review Queue/readiness works.
- 4K render/resume/validation works.
- Installer/hardware matrix/golden suite passes.

---

## 12. UX acceptance scenarios

### Scenario A - One character, one image

Given a video with one dominant character, when the user imports it, selects the character card and drops one transparent PNG, then the app previews representative scenes and applies the replacement across the video without requiring scene-by-scene confirmation.

### Scenario B - Same character appears in multiple scenes

The app groups occurrences into one role. If grouping is uncertain, it shows the candidate pair for confirm/deny before apply-all.

### Scenario C - Two objects replaced

The user can select two Object Roles, assign two assets and process both in one batch while retaining independent mappings and issues.

### Scenario D - One scene tracks badly

All good scenes remain Ready. Review Queue opens the first bad frame; the user corrects the mask and only the affected track/composite segment reruns.

### Scenario E - Demo result is not acceptable

The user changes asset/pose/anchor/scale or fixes a demo mask, regenerates only the demo, and no full-video batch starts until `Duyệt Demo & Áp dụng toàn video` is confirmed.

### Scenario F - Source is 1080p, export is 4K

Export clearly shows `4K Upscale`, selected scaling method and estimate. Final validation confirms 3840x2160 but does not misrepresent the source as native 4K.

### Scenario G - App closes during render

On restart the project opens at Export, the job reconciles from checkpoint, and no `.partial` file is presented as complete.

### Scenario H - One project contains multiple videos

The user opens a project, sees source channel, production channel, per-video status and latest output, then resumes the next actionable Video Item without searching the filesystem.

### Scenario I - Reuse one character across channels

The user selects a validated Character Pack from the global library for two projects. Each project pins a Pack Version, so later library edits do not silently change prior outputs.

### Scenario J - Generate a simple 2D character pack

The user uploads one reference, confirms identity/style constraints, reviews six generated pose panels, regenerates one failed side view, and publishes the approved pack to the Library.

---

## 13. Performance and quality plan

### Dataset dimensions

- 1/2/5+ objects.
- Flat-color/textured animation.
- Static/moving camera.
- Occlusion/crossing/out-of-frame.
- Standing/sitting/walking/talking/back.
- Static/complex/moving background.
- Source with/without audio and different audio codecs/channel layouts.
- CFR/VFR, 24/30/60 fps.
- 720p/1080p/4K source.
- Short/medium/long duration.

### Metrics

Object discovery/grouping:

- candidate recall;
- grouping precision/recall;
- manual merge/split rate;
- time to select roles.

Tracking/reskin:

- mask J&F/IoU;
- identity switch;
- jitter/flicker;
- corrections per minute;
- edge/contact/occlusion issue rate.

Original audio:

- stream preservation/remux success;
- duration/A-V drift;
- codec/channel fallback rate;
- missing/silent-range detection.

Render:

- real-time factor by hardware tier;
- peak RAM/VRAM/disk;
- retry/resume success;
- output validation success.

UX:

- time to first Object Gallery;
- time to first reskin preview;
- active user minutes per output minute;
- issue resolution time;
- six-step completion rate.

---

## 14. Risks and mitigation

| Risk | Mitigation |
|---|---|
| Cross-scene grouping inaccurate | suggestions + confidence + confirm/merge/split; never silently map low confidence |
| One PNG looks wrong across poses | simple asset warning, pose pack, fallback and issue-based correction |
| SAM2 drift/VRAM | anomaly detection, correction, chunking and fallback |
| Inpainting artifacts | multiple modes, clean plate/manual patch, QC |
| 4K too slow/heavy | proxy workflow, preflight, resolution-aware assets, GPU/CPU profiles, checkpoint |
| Upscale creates false expectation | explicit source vs target label and scaling mode |
| Voice/localization làm loãng Phase 1 | giữ audio gốc; tách Phase 2 sau khi reskin release gate đạt |
| Job/persistence migration breaks projects | backup/import validation/backward fixture/rollback |
| New UI hides advanced control | progressive disclosure and context jump from issue |
| Scope expands into full editor | six-step product filter and explicit out-of-scope list |

---

## 15. Hermes delivery contract after approval

Mỗi Epic/Sprint/Task sau này phải nối trực tiếp tới:

- một user phase U1-U6;
- một workstream WS-00-09;
- một quality gate G1-G5;
- một measurable outcome.

### Required task template

```text
Title:
User outcome:
Parent workstream/gate:
Current behavior/evidence:
Target behavior:
In scope:
Out of scope:
Domain/schema impact:
API impact:
UX states:
Job/error/recovery behavior:
Dependencies:
Acceptance criteria:
Tests/evidence required:
Migration/backward compatibility:
Known constraints:
```

### Coding rules

- Read repository instructions and local Next.js docs before frontend changes.
- Do not rewrite working media algorithms without evidence.
- Do not add schema without migration/backward test.
- Do not store durable business state only in Zustand/LocalStorage/RAM.
- Do not run long operations synchronously in UI/HTTP request.
- Do not expose arbitrary filesystem paths.
- Do not recursively delete outside safe Trash/containment contract.
- Do not add provider/model without dependency, version, capability and test profile.
- Do not mark task complete while required lint/type/build/tests fail.
- Return commands/results/screenshots/benchmark evidence.

### Hermes completion report

```text
Outcome delivered:
Workstream/gate contribution:
Files changed:
Schema/migration:
Jobs/artifacts affected:
Tests and exact results:
Manual UX path verified:
Screenshots/output artifacts:
Performance/quality evidence:
Known limitations:
Follow-up dependency:
```

---

## 16. Decisions to approve before sprint planning

### D1 - Six-step flow

Approve: `Import -> Objects -> Reskin Demo -> Apply Reskin -> Review -> Export`.

### D2 - Global object model

Approve ObjectRole across video with scene Occurrences, rather than object identity limited to one scene.

### D3 - Default asset support

Proposed: accept one PNG for convenience and multi-pose Character Pack for quality. Warn when simple asset cannot represent pose.

### D4 - Audio Phase 1

Proposed: preserve/remux original voice, BGM and SFX. Translation/TTS/voice replacement moves entirely to Phase 2.

### D5 - 4K definition

Proposed: 3840x2160 16:9 Master. If source below 4K, label as upscale and let user choose scaling method.

### D6 - Auto-pass

Proposed: high-confidence items Ready automatically; user reviews blockers/warnings and may enable strict manual review.

### D7 - Provider boundary

Proposed: Phase 1 reskin/render local and original audio only; no localization provider is required.

### D8 - Stack

Proposed: retain FastAPI + Next.js and migrate incrementally; packaging shell evaluated separately after core flow works.

### D9 - Supported hardware

Proposed initial target: Windows 10/11, CPU fallback, NVIDIA 8 GB VRAM minimum for accelerated AI, 12 GB+ recommended; final matrix after benchmark.

### D10 - UI language

Proposed: Vietnamese default with i18n-ready strings and English option later.

### D11 - Production hierarchy

Approve: Workspace có Channels và Projects; một Project có source channel, production channel và nhiều Video Items.

### D12 - Character reuse model

Approve: Character Library là kho dùng chung; mỗi project map Object Role tới một Pack Version bất biến.

### D13 - Character generator scope

Approve: generator đơn giản cho hoạt hình 2D, ưu tiên six-pose pack, adapter-based generation + pose conditioning + human review; chưa train LoRA trong Phase 1.

### D14 - Build strategy

Approve: hybrid rebuild/strangler migration — giữ stack và media engines có giá trị, xây lại domain/persistence/jobs/product shell; không vá tiếp Screen A-E thành sản phẩm đích và không rewrite từ repo trắng.

---

## 17. What happens after approval

1. Record decisions D1-D14.
2. Freeze PRD V4 and Master Plan V3 for initial planning baseline.
3. Break Stage A into Epics.
4. Define baseline CI/evidence and migration fixtures.
5. Plan only the next 1-2 sprints in detail.
6. Deliver a reviewable vertical outcome each sprint.
7. Demo against UX acceptance scenarios, not only API/tests.
8. Reassess later stages using benchmark and usability evidence.

Recommended first planning sequence after approval:

```text
Foundation quality/persistence/jobs
-> Production management + Project Shell
-> Import/Analyze vertical slice
-> Character Library + Cast Mapping
-> ObjectRole/Object Gallery vertical slice
```

Do not begin by polishing every existing Screen A-E. The first UI investment should create the new shell and object-first flow; old screens are migrated or retired as their replacement becomes usable.

---

## 18. Approval status

Master Plan V3 is approved when Stakeholder confirms:

- six-step flow;
- global ObjectRole strategy;
- simple PNG + Character Pack approach;
- original-audio preservation scope and Phase 2 deferral;
- 4K/upscale definition;
- auto-pass/review behavior;
- foundation-first incremental migration.
- Project/Channel/multi-video operating model;
- reusable versioned Character Library;
- simple reviewed 2D Character Generator;
- hybrid rebuild strategy.

**Current status:** `APPROVED AS PLANNING BASELINE`

---

## 19. Research references

- [Adobe Premiere Text-Based Editing](https://helpx.adobe.com/premiere/desktop/edit-projects/edit-video-using-text-based-editing/overview-of-text-based-editing.html)
- [Descript editor interface](https://help.descript.com/hc/en-us/articles/37585546799757-The-editor-interface)
- [Runway Remove Background](https://help.runwayml.com/hc/en-us/articles/19112532638995-Remove-Background)
- [Meta SAM 2](https://github.com/facebookresearch/sam2)
- [NVIDIA FFmpeg GPU acceleration](https://docs.nvidia.com/video-technologies/video-codec-sdk/13.1/ffmpeg-with-nvidia-gpu/index.html)
