# MotionForge2D Phase 1 Backlog — Gemini Lane

## Batch A: Engineering Tuần Tự (Chưa GPU/Render)
- [ ] **A1 — CODEX-C02B2-PER-ACTOR-VERIFIED-REUSE** (Đang chạy từ Checkpoint 015)
  - Hoàn tất P1–P6 của TASK_C02B2
  - Full negative matrix + positive controls
  - Standalone gate import without heavy adapter
  - Regression 40 test C01/C02A/C02B1
  - Self-review & freeze candidate A1
- [ ] **A2 — GEMINI-C02B3-ASSET-VERIFIED-REUSE**
  - Asset producer provenance, skip_allowed caller wiring
  - Legacy decisions fail-closed, no auto-upgrade
  - Descendant invalidation proof
- [ ] **A3 — Event timing, child outcome và tracking**
  - Event keys timing, exact frame mapping
  - Stage2 child failure fail-closed
  - CoTracker reader exact contract
  - Crop/stitch/resize/pad transform round-trip
- [ ] **A4 — Evidence, gate, registry/lease conformance**
  - Assembler/submit calls real gate with candidate binding
  - Q01–Q12 & T01–T15 conformance matrix update
  - True-race 2-controller barrier verification
- [ ] **G1 Review Gate**: Nộp frozen engineering batch A1–A4 cho Codex độc lập nghiệm thu

## Batch B: Correction Media & Pilot (Sau G1 Approved)
- [ ] **B1 — Preflight & Hard Excerpts**
  - SAM2, FLUX2, CropAndStitch, VACE, EbSynth, CoTracker hard cases
- [ ] **B2 — Full Pilot 300s (5 phút)**
  - Source 01:34–06:34, 9000f, 30fps, 640x360, original audio
- [ ] **G2 Review Gate**: Nộp pilot 300s cho Codex độc lập nghiệm thu

## Batch C: Hoàn Thiện Sản Phẩm Phase 1 (Sau G2 Approved)
- [ ] **C1**: Production organization (Channel, Project, Multi-video)
- [ ] **C2**: Character Library (Pack Version, stable ID, anchors)
- [ ] **C3**: Character Generator (Ref/profile -> pack draft -> preview)
- [ ] **C4**: Import và Objects (Video -> probe/cuts -> Object Gallery)
- [ ] **C5**: Mapping và Demo (Assign asset -> demo review -> approve)
- [ ] **C6**: Apply/Review (Pipeline job service -> review queue)
- [ ] **C7**: Jobs và Recovery (Background progress, cancel/retry/resume)
- [ ] **C8**: Export và Versions (Audio original, 1080p/4K presets)
- [ ] **C9**: Storage và Delivery (Safe cleanup, local-first Windows)
- [ ] **Full-source 22:01 Proof & 4K Export Gate**
- [ ] **G3 Final Gate**: Codex nghiệm thu độc lập toàn bộ sản phẩm Phase 1
