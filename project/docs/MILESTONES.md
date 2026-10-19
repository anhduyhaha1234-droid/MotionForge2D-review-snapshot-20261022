# MotionForge 2D — Milestones

## Milestone 0: Technical Discovery & Vertical Spike

**Goal:** Prove the end-to-end pipeline works from MP4 input to MP4 output.

**Status:** `CONDITIONALLY ACCEPTED` (2026-07-29)

**Reason:** Pipeline runs end-to-end but contour mask propagation fails (only 1/90 frames tracked). SAM2 backend was not tested in M0 due to missing checkpoint.

**Resolution:** Milestone 0.5 validated SAM2 backend with 100% tracking on all fixtures.

---

## Milestone 0.5: Core Tracking Validation

**Goal:** Validate SAM2 end-to-end: segmentation, propagation, compositing on real GPU.

**Status:** ✅ Complete (2026-07-29)

**Key results:**
- SAM2 runs on RTX 5070 (2.7GB VRAM, 3.1 fps at 640×360)
- All 3 fixtures: 100% tracked, 100% composited
- Schema upgraded to v2.0.0 (confidence, occlusion, mask_path)
- Occlusion limitation documented (SAM2 tracks occluder, not hidden object)

---

## Milestone 1A: Object Extraction Review UI

**Goal:** FastAPI backend + Next.js frontend with full upload→extract→replace→render workflow.

**Status:** `CONDITIONALLY ACCEPTED` (2026-07-30)

**Reason:** Backend API and SAM2 workflow verified end-to-end. Frontend builds and serves. Missing: Playwright E2E, real composite preview on Screen D.

**Key results:**
- 18 API endpoints, all tested
- 67 backend tests pass
- SAM2 propagation via API: 180/180 tracked
- Output video: H.264 640×360 30fps 180frames + AAC audio
- Schema v2.0.0 with ReplacementConfig, clip modes

---

## Milestone 1A.1: UI Integration & Acceptance ⬅ CURRENT

**Goal:** Browser-verified UI with real composite preview, Playwright E2E, cancel, and persistence.

**Status:** 🔄 In Progress

**Deliverables:**
- [ ] Screen D: real Konva composite preview (no placeholder)
- [ ] Transform spec: clipMode with 3 modes
- [ ] Playwright: fast deterministic E2E test
- [ ] Playwright: real GPU E2E test
- [ ] Canvas coordinate validation (roundtrip ≤1px)
- [ ] Mask preview validated on browser
- [ ] Job cancellation tested
- [ ] Restart persistence tested
- [ ] Screenshots (9 screens)
- [ ] Review packages (7 documents)

---

## Milestone 1B: Frame Sequence & Keyframe Replacement

**Goal:** Support frame-by-frame replacement assets and keyframe interpolation.

**Deliverables:**
- [ ] frame_sequence replacement mode
- [ ] keyframe_assets replacement mode
- [ ] Timeline with keyframe markers
- [ ] Interpolation between keyframes
- [ ] Per-frame asset assignment UI

---

## Milestone 1C: Background Cleaning & Inpainting

**Goal:** Remove original object from background after replacement.

**Deliverables:**
- [ ] Clean plate from another frame
- [ ] User-uploaded clean background
- [ ] Local inpainting model integration
- [ ] Preview vs final quality controls

---

## Milestone 2: Multi-Object & Multi-Scene

**Goal:** Track multiple objects across multiple scenes.

**Deliverables:**
- [ ] Multi-object tracking in a scene
- [ ] Object assignment across scenes
- [ ] Motion path visualization
- [ ] Keyframe editing per object
- [ ] Timeline with multi-track support

---

## Milestone 3: Rendering & Export

**Goal:** Full render pipeline with preview and format options.

**Deliverables:**
- [ ] Preview mode (low-res fast render)
- [ ] Full quality render
- [ ] Format options (MP4, WebM, GIF)
- [ ] Resolution options
- [ ] Batch scene rendering
- [ ] Audio mixing controls

---

## Milestone 4: Polish & Distribution

**Goal:** Production-ready application.

**Deliverables:**
- [ ] Error handling and recovery
- [ ] Undo/redo system
- [ ] Keyboard shortcuts
- [ ] Docker Compose setup
- [ ] Installation guide
- [ ] User documentation
