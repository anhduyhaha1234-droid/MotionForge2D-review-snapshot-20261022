# MotionForge 2D — Source-Locked 2D Target Profile

**Status:** APPROVED ROADMAP OVERLAY

**Approved:** 2026-08-19

**Reference:** https://www.youtube.com/watch?v=0xki_leZBzA

**Owner:** Product/PM

## 1. Verified reference profile

The user supplied an authorized local copy of the reference on 2026-08-19. PM
decoded and sampled that file directly; the facts below supersede the previous
URL-only assumptions.

### Source fingerprint

| Field | Verified value |
|---|---|
| SHA-256 | `5A175454C2C2965BAC5013A53926E210A9F70A185D802D0F2E0083A6FB399FA2` |
| File size | 36,971,916 bytes |
| Container duration | 00:22:01.22 |
| Video | H.264 Main, 640x360, SAR 1:1, 16:9, 30 fps, yuv420p BT.709 progressive |
| Decoded video frames | 39,634 |
| Audio | AAC-LC, 44.1 kHz, stereo, approximately 95 kb/s |
| Strong scene-change candidates | 208 at scene score `> 0.45`; candidate spacing P50 4.20 s, P90 12.73 s |
| Looser scene-change candidates | 224 at scene score `> 0.25`; candidate spacing P50 4.10 s, P90 11.97 s |
| Exact consecutive decoded-frame repeats | 2,675 transitions (6.75%); longest exact hold 57 frames |

Scene-change counts are analyzer candidates, not approved editorial truth. S05
must persist the detected score and allow golden-fixture correction rather than
silently treating a threshold as ground truth.

### Observed visual and motion grammar

- Flat-color, thick-outline cutout 2D with simple reusable rooms and mostly
  static framing.
- Animation is dominated by pose/expression swaps, rigid sprite translation,
  crop/scale changes, whole-body rotation and hard cuts. Dense natural
  deformation is not the dominant case.
- Shots commonly contain one or two primary characters, but group scenes show
  up to four visible characters. Tier A cannot assume a maximum of three visible
  roles.
- High-value contacts include phone-to-hand-to-face, hand-to-book/document,
  cup-to-table, body-to-chair, body-to-bed and car-to-road.
- Important occlusion order includes character behind table/chair, characters
  crossing/grouping, body on or behind bed layers, and props held in front of
  the torso/face.
- The source mixes drawn assets with photo inserts, especially the car and wall
  images. A replacement must preserve direction, footprint and contact while
  removing source visual identity.
- Phone screens, contracts, signs, advertisement cards and narrative text are
  semantic graphic layers, not backgrounds. The persistent source
  logo/watermark is a source-only overlay and must not leak into a newly rendered
  result.
- Original narration/audio is structurally important; visual replacement does
  not authorize retiming it.

### Consequence for V1

The fastest fidelity path for this reference is a deterministic **cutout scene
reconstruction engine**: shot manifest + role/layer graph + pose states +
keyframed transforms + contact anchors + z-order. Optical flow, mesh warp and
part rigs remain escalation routes for residual motion; full-frame diffusion is
not the default renderer.

## 2. Product objective

MotionForge's first quality target is not generic video-to-video generation. It
is **source-locked visual reconstruction for 2D animation**:

1. Import a source video.
2. Separate and classify character, prop, background, foreground, semantic
   graphic/text/screen and source-only overlay layers.
3. Group recurring entities into reusable roles.
4. Let the user map each role to a versioned replacement asset/pack.
5. Evaluate whether every replacement is structurally compatible with the
   source occurrences before confirmation.
6. Generate risk-selected demo loops.
7. Rebuild the complete video with new visual assets while preserving source
   timing, action, camera/framing, contacts, cuts and original audio.

### Locked structure

- exact frame count and canonical timebase;
- source duration, cut boundaries and shot order;
- camera path, framing and scale trajectory;
- character/object motion trajectories and action timing;
- hand/prop, foot/ground and character/character contact events;
- visibility, occlusion order and entry/exit timing;
- source audio content and synchronization.

### Replaceable appearance

- character identity and design;
- prop identity and design;
- background/foreground artwork;
- semantic graphic/text/screen presentation while preserving required content;
- style, outline, palette, texture and shading, subject to compatibility.

The product must never describe an output as structurally equivalent if a
locked invariant is outside the accepted tolerance.

## 3. Target tiers

### Tier A — first release target

- raster or vector-like 2D;
- flat/cutout/limited animation;
- mostly static or simple camera motion;
- one to four visible characters, with one or two primary recurring roles;
- reusable poses/views and moderate limb deformation;
- props with explicit grip/contact points;
- backgrounds that can be represented as static or shallow parallax layers;
- semantic text/screen/card layers that can be restyled without changing story
  timing or required content.

### Tier B — after Tier A passes

- articulated characters with stronger deformation;
- character turns, foreshortening and partial occlusion;
- multiple interacting characters and props;
- foreground occluders, moving camera and multi-plane parallax.

### Tier C — later research target

- dense frame-by-frame animation;
- extreme perspective and rapid shape changes;
- complex cloth/hair/smoke/liquid;
- shots that require controlled generative redraw rather than deterministic
  layer retargeting.

Tier C must not delay the Tier A product.

## 4. Core technical direction

Use a hybrid, layer-aware renderer. Deterministic reconstruction is the default;
generative redraw is a per-shot fallback.

### P0 — required for Tier A

1. **Canonical media contract**
   - FFmpeg/ffprobe for stream probing, CFR/VFR normalization, exact frame
     indexing, proxy generation, stitching and original-audio remux.
   - Persist a StructuralLockManifest per Video Item.

2. **Promptable masks and correction**
   - Keep SAM 2.1 as the primary segmentation adapter.
   - Benchmark Cutie as a permissively licensed fallback for mask propagation.
   - Store keyframe prompts, masks, confidence and correction history; never
     store only the final flattened mask.

3. **Motion contract beyond bounding boxes**
   - Detect holds, cuts, pose/expression state changes and per-layer keyframes
     before invoking dense tracking.
   - Fit camera-relative translation, scale and rotation from masks/features as
     the default path for this reference.
   - Add a permissive dense/point-motion adapter. Start with TorchVision RAFT or
     SEA-RAFT and benchmark Google TAPIR/TAPNext++ for shots whose residual error,
     occlusion or deformation exceeds the affine route.
   - Fit deformable mesh or part motion only where the measured residual and
     contact constraints require it.
   - Current centroid/bbox-only motion remains a prototype fallback, not the
     final fidelity path.

4. **Scene and occlusion graph**
   - First-class roles: character, prop, background, foreground occluder,
     semantic graphic/text/screen and source-only overlay.
   - Persist z-order, containment, contact anchors, visibility and interaction
     edges per occurrence/segment.
   - Separate camera motion from object motion.

5. **Replacement Asset Pack**
   - Character Pack remains supported but must be extensible beyond six PNGs.
   - Add view coverage, pose range, deformable parts/rig profile, anchors,
     mirror rules, mouth/expression variants and optional prop-grip anchors.
   - Add Prop Pack, Background Pack and Graphic Template profiles without
     duplicating mapping logic.

6. **Compatibility engine before Confirm**
   - Compare source needs with replacement capabilities.
   - Return evidence per shot/occurrence, not one opaque global score.
   - Policy and thresholds are backend-owned, versioned and calibrated on the
     golden dataset.

7. **Adaptive renderer router**
   - sprite_affine: rigid/limited motion;
   - mesh_warp: silhouette-preserving deformable motion;
   - part_rig: articulated characters and anchored props;
   - controlled_redraw: exceptional complex shots only.
   - Renderer choice is persisted per occurrence segment and can be overridden
     during Demo review.

8. **Commercial-safe removal/inpainting**
   - Prefer clean-plate/background reuse for flat 2D.
   - Use OpenCV Telea only as a fast fallback.
   - Benchmark Apache-licensed OpenCV Zoo LaMa ONNX for difficult still regions.
   - Temporal consistency must be measured across the shot.
   - Source watermark/logo pixels must be classified and removed; they may not
     be baked into a clean plate or replacement background.

### P1 — required for Tier B

- DWPose/whole-body pose as an optional signal for human-like characters; never
  make it mandatory for stylized/non-human cartoons.
- DINOv2 embeddings for occurrence grouping, identity consistency and
  appearance/style compatibility.
- Video Depth Anything only for camera/parallax/background plane estimation.
- part-level segmentation, mesh/triangle constraints and contact-aware warping.
- controlled edge/pose/depth-conditioned generation through a provider adapter.

### P2 — defer until deterministic path is proven

- full-frame diffusion as the default renderer;
- per-video LoRA training;
- unconstrained prompt-only redesign;
- automatic background regeneration without perspective/parallax validation.

These paths increase identity drift, flicker and structural deviation and are
not the foundation of the first 2D target.

## 5. Compatibility contract

### Character dimensions

- head/body and limb proportions;
- aspect ratio and silhouette envelope;
- front/three-quarter/side/back coverage;
- pose and articulation range;
- turn/foreshortening coverage;
- feet, body, head and seat anchors;
- mouth/expression support where required;
- outline, palette, texture and shading compatibility.

### Prop dimensions

- size relative to character and frame;
- hand/grip/contact anchors;
- rotation/articulation range;
- side/front/back appearance coverage;
- occlusion and layer behavior.

### Background dimensions

- horizon, ground plane and perspective;
- camera movement and parallax depth;
- foreground occluders;
- light/shadow direction;
- safe zones for character trajectories and props.

### Graphic/text/screen dimensions

- semantic content that must remain readable or story-equivalent;
- safe area, line count, reading order and on-screen duration;
- perspective/rotation when attached to a phone, document, wall or sign;
- font/style/palette as replaceable appearance;
- explicit source-only state for watermark, channel logo or platform overlay
  that must be removed rather than reproduced.

### Decision states

- Compatible: deterministic route is expected to preserve structure.
- Review: Demo must include every detected risk class.
- Incompatible: confirmation is blocked until the asset, route or explicit
  source requirement changes.

The UI must explain the failing dimensions and link to the affected demo loops.

For the verified reference, hard blockers include a replacement that cannot
maintain a phone-to-face grip, seated/lying body anchors, visible role count,
required view/pose state, prop footprint/direction or background safe zone. A
style embedding score cannot override these geometric failures.

## 6. Demo selection and approval

The existing representative-demo requirement is expanded to **risk-selected
demo**. The 3–5 loops must cover as many of these as possible:

- closest shot and largest on-screen scale;
- full-body shot and ground contact;
- fastest motion and largest direction change;
- largest rotation/turn/foreshortening;
- occlusion and reappearance;
- hand/prop or character/character contact;
- camera motion and scale change;
- lowest mask/track/compatibility confidence;
- multi-character or multi-prop interaction.

Approval creates an immutable checkpoint containing:

- pinned asset/pack versions;
- CompatibilityPolicy version and evidence;
- renderer route per segment;
- StructuralLockManifest version;
- accepted warnings and user overrides;
- demo artifacts and correction history.

## 7. Roadmap overlay

This overlay does not reopen completed foundation work. It changes the
acceptance contract of future tasks and adds bounded prerequisites where
necessary.

### S05 — Import and Analyze

- S05-T03: add StructuralLockManifest, exact source frame/time/audio mapping and
  camera-vs-object coordinate spaces.
- S05-T04: persist shot boundaries, camera-motion class, background motion class
  and representative risk frames.
- S05-T06: add a fixture manifest for the verified local reference, keyed by the
  SHA-256 above. Do not commit or redistribute the user-supplied media; the test
  must report a clear skip when that authorized fixture is absent.

### S06/S07 — Library and Mapping

- Do not rewrite the existing Character Library task.
- Add an additive PackCapabilityProfile before S07-T02: view/pose/deformation,
  anchors, rig/parts, mirror rules and style summary.
- S07-T01 mapping must support role type and pin both pack version and
  CompatibilityPolicy version.
- S07-T02 becomes evidence-based compatibility UI for character, prop and
  background replacements, not only a pose warning.

### S08 — Object Intelligence

- ObjectRole type must include character, prop, background, foreground,
  semantic graphic/text/screen and source-only overlay.
- ObjectOccurrence must support masks, point/flow motion, contact events,
  occlusion edges and camera-relative transforms.
- Grouping confidence must combine visual identity and motion/interaction
  evidence.
- Golden dataset must include stylized/non-human characters where human pose
  detection is unreliable.

### S09 — Demo-first Reskin

Add a prerequisite contract before implementation:

**S09-T00 — SceneGraph, MotionContract and RendererRouter spike**

- compare bbox-only, pose-swap/affine, mesh and part-rig routes on the
  reference/golden loops;
- choose the smallest renderer that passes structural metrics;
- record runtime, VRAM, drift, flicker, contact and correction counts;
- license-gate every model/checkpoint.

Update existing tasks:

- S09-T01 stores compatibility evidence and per-segment renderer route.
- S09-T02 may reuse legacy canvas math only behind the new renderer contract;
  bbox/centroid compositing is not the final fidelity implementation.
- S09-T03 uses risk-selected loops.
- S09-T05 corrections include z-order, contact anchors, mesh/part controls and
  renderer override.
- S09-T06 pins all structural and compatibility contracts in the apply
  checkpoint.

### S10 — Full Apply

- Process per shot/layer with overlap and deterministic checkpoints.
- Preserve exact frame count, cuts, camera/framing and source action timing.
- Recompute only affected layers/segments.
- Run automatic structural comparison before a result can enter Review.

### S11 — Review and Original Audio

- Audio extraction/reference must exist from S05; S11 implements final
  remux/fallback and QC rather than discovering timing late.
- Add QC reasons for trajectory drift, cut drift, contact break, z-order error,
  silhouette clipping, identity drift, edge halo and temporal flicker.
- Review Queue jumps directly to the failing layer and renderer route.

### S12 — Export

- Exact frame count, duration, timebase, cuts and A/V sync are hard gates.
- Export manifest records source lock, pack versions, renderer routes,
  compatibility policy and accepted exceptions.
- 4K upscale must not hide structural or temporal QC failures.

### Implementation activation sequence

The roadmap should now execute in this dependency order. A later lane may not
invent its own media, scene or compatibility contract to run early.

| Order | Task packet(s) | Required exit evidence | Parallel rule |
|---|---|---|---|
| 1 | S05-T01 to S05-T02 | deterministic probe/import, source SHA-256, managed immutable source | sequential |
| 2 | S05-T03 | StructuralLockManifest round-trips exact video frames/timebase and separate audio stream facts | sequential after S05-T02 |
| 3 | S05-T04 | stable shot IDs, scored cut candidates, correction history, camera/background class and risk features | sequential after S05-T03 |
| 4 | S05-T05 to S05-T06 | resumable Analyze UI plus verified-reference fixture manifest/restart evidence | sequential |
| 5A | S06-T01 to S06-T05 | versioned Character Pack plus PackCapabilityProfile and anchors | may run beside 5B with disjoint write scopes |
| 5B | S08-T01 to S08-T06 | role/layer graph, masks, grouping, contacts/occlusion and golden metrics | may run beside 5A with disjoint write scopes |
| 6 | S07-T01 to S07-T03 | role-to-pack mapping, pinned policy and evidence-based compatibility decision | after required S06/S08 contracts |
| 7 | S09-T00 | renderer benchmark proves the smallest passing route per risk class | before S09-T01 |
| 8 | S09-T01 to S09-T06 | risk-selected before/after Demo, targeted corrections and immutable approval | sequential product slice |
| 9 | S10-T01 to S11-T06 | resumable full apply plus structural/audio QC and targeted rerun | after Demo approval |
| 10 | S12 | validated delivery; upscale remains a separate post-process | final |

The first new coding packet is S05-T01 unless an integration review proves it is
already APPROVED. Dirty or parallel worktree activity is not approval evidence.

### Binary acceptance additions for implementation packets

- **S05-T03:** the verified fixture reports 39,634 decoded video frames and
  preserves independent container/video/audio timing facts; no duration is
  reconstructed from rounded FPS alone.
- **S05-T04:** cut detector stores score and algorithm version; strong candidates
  can reproduce the observed 208-candidate baseline within an explicitly
  versioned tolerance, and manual corrections retain stable shot IDs.
- **S08-T01/T02:** a phone interaction can represent character, phone, hand/face
  anchors, visibility and z-order without flattening them into one opaque bbox.
- **S07-T02:** intentionally incompatible assets fail closed for seated/lying
  anchors, view/pose coverage, visible-role count and prop direction/footprint;
  the UI links every failure to an occurrence/loop.
- **S09-T00:** pose-swap/affine is benchmarked first; mesh/part/flow is selected
  only where it reduces measured structural error, and renderer choice is
  persisted per segment.
- **S09-T03:** selected loops jointly cover hard cut, mouth/expression swap,
  phone contact, whole-body rotation/bed contact, group occlusion and semantic
  graphic replacement.
- **S10/S11:** frame count, shot order, cut frame, camera/framing, contacts,
  z-order and A/V sync are machine-checked before PM visual approval.

## 8. Reference benchmark gate

### Provisional risk loops from the verified file

These windows are seeded from decoded scene-change candidates and PM visual
inspection. S05-T04 must snap them to canonical frame IDs and preserve any
correction history.

| Loop | Source time window | Required coverage |
|---|---|---|
| REF-R01 | 00:17.867-00:24.933 | car/character composition, hard cuts and semantic graphic transition |
| REF-R02 | 01:37.200-01:45.133 | wide-to-close framing plus mouth/expression pose swaps |
| REF-R03 | 08:15.667-08:22.800 | phone/hand/face contact and prop z-order |
| REF-R04 | 15:29.867-15:35.000 | whole-body rotation, phone placement and body-to-bed contact |
| REF-R05 | 17:57.133-18:03.033 | multi-character group movement/occlusion and shot transition |

### Reference-specific renderer priority

| Observed class | Default route | Escalation trigger |
|---|---|---|
| held pose or mouth/expression change | versioned pose/expression swap | missing state or identity failure |
| rigid person/prop/car motion | anchored affine/keyframe | residual silhouette/contact error above gate |
| seated, phone, book, cup or bed interaction | affine plus explicit contact anchors/z-order | part-rig when one transform cannot keep all anchors |
| simple room/exterior | rebuilt static Background Pack with layout/safe-zone anchors | shallow parallax only when camera evidence exists |
| phone/document/sign/ad card | Graphic Template attached to its host plane | controlled redraw only if deterministic text/layout fails |
| local deformation/occlusion | mask-guided mesh/point track | part-rig or controlled redraw after benchmark evidence |

### Initial structural thresholds

S09-T00 must report these in normalized source coordinates. It may tighten them;
loosening one requires PM evidence and a versioned CompatibilityPolicy change.

- exact 39,634 decoded video frames for the verified input and exact shot order;
- cut/action event timing error no greater than one source frame;
- trajectory center error median <= 0.5% and P95 <= 1.0% of source-frame
  diagonal;
- scale relative error P95 <= 3% and rotation error P95 <= 3 degrees;
- annotated contact-anchor error P95 <= 1.0% of source-frame diagonal;
- zero annotated z-order inversions and zero unexplained visibility events;
- zero clipping caused by reusing the source silhouette as the replacement
  silhouette; new alpha may extend outside the old mask subject to layout gates;
- final A/V start/end drift <= one source video frame, while preserving the
  original audio content and stream mapping decision in the export manifest.

Before Tier A is declared successful, the reference video must have:

1. source metadata and frame-accurate shot manifest;
2. annotated primary character, prop, background and foreground roles;
3. annotated risk loops covering turn, occlusion, contact and camera motion
   present in the source;
4. at least two replacement sets: one compatible and one intentionally
   incompatible;
5. exact frame count/cuts/audio after Apply;
6. trajectory, scale, rotation, contact, occlusion, identity and flicker
   metrics;
7. PM visual review of synchronized before/after loops;
8. thresholds calibrated from evidence, then frozen in a versioned policy.

## 9. Current code gaps this overlay addresses

- app/services/motion_extraction.py derives motion primarily from contour
  centroid, bounding box, scale and a single rotation value.
- app/services/compositing.py resizes one replacement image to the tracked box
  and clips it with the source mask.
- This is useful for a prototype and simple rigid assets, but it cannot preserve
  articulated action, new silhouettes, contact, foreground occlusion or
  character turns at the required fidelity.

The existing code should remain as the sprite_affine fallback while the mesh,
part-rig and compatibility contracts are added behind adapters.

## 10. Technology and license gate

| Candidate | Intended use | Product decision |
|---|---|---|
| SAM 2.1 | promptable multi-object masks | P0 primary; Apache 2.0 |
| Cutie | mask propagation fallback | P0 benchmark; MIT, Windows validation required |
| TorchVision RAFT / SEA-RAFT | dense motion and mesh fitting | P0 benchmark; permissive implementation path |
| TAPIR/TAPNext++ | long-range point tracks/occlusion | P0/P1 benchmark; Apache 2.0 repo/checkpoints |
| DINOv2 | grouping and visual compatibility embeddings | P1 adapter; Apache 2.0 |
| DWPose | human-like pose signal | P1 optional; benchmark cartoons before use |
| OpenCV Zoo LaMa ONNX | difficult clean-plate regions | P0 optional; Apache directory/model package |
| Video Depth Anything | camera/parallax support | P1 only; not required for flat backgrounds |
| ControlNet/provider adapter | controlled exceptional redraw | P1 fallback, never default |
| CoTracker3 | research point-tracking comparison | benchmark only; majority CC-BY-NC |
| ProPainter/E2FGVI | research video-inpainting comparison | do not ship without commercial permission |
| DINOv3 | future dense-feature evaluation | license review before product adoption |

No model is approved for bundling merely because its source code is public.
Code license, checkpoint license, redistribution, Windows support, VRAM and
offline installation must all pass the provider/model gate.

## 11. Product comparison applied

- Runway validates a fast upload/edit/compare/generate interaction model.
- Viggle validates reusable character/scene preprocessing and source-motion
  transfer.
- Moho/Cartoon Animator validate rig, anchors, IK/contact and reusable motion.

MotionForge should combine these ideas around its differentiator:
**local, reviewable, version-pinned, source-locked reconstruction with
compatibility evidence before compute is committed.**
