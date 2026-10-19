---
name: motionforge-2d-project
description: "MotionForge 2D project conventions, architecture, and workflow"
tags: [motionforge, video-editor, fastapi, nextjs, sam2]
---

# MotionForge 2D — Project Conventions

## Validation pitfalls (verified 2026-08)

- **Manager must NOT trust a writer's REPORT — verify independently.** PREFLIGHT: sha256 every
  file expected to change BEFORE dispatch, re-run each suite + the combined focused suite yourself
  (isolated DB discipline), write a STANDALONE manager repro script (in Temp, NOT importing writer
  tests) that seeds its own data and asserts each required repro, and grep for whole-file
  `# ruff: noqa:` headers (a writer can clear "ruff 0" by suppressing rather than fixing).
  A reported-vs-raw-log mismatch = immediate STOP/CHANGES_REQUIRED. Playbooks: `references/` (s07, s08-a02-*, s09-t00-wave-facts, s10-c4-c6a-authority-acceptance, s10-c6d-c6e-correction-playbook, r27-cpu-correction-round, delivery-takeover-scene-unit-proof, comfy-wan-scene-unit-profile).

- **Follow-on-task authority often lives in planning artifacts, not ROADMAP/sprint contracts.**
  When a task ID (e.g. A02-T02) is referenced by TASK.md but absent from sprint contracts, the
  spec is in `output/overnight-planning/*DRAFT*.md` + `output/*/ro*-*planning*.md`. Gate dispatch
  on 8 aspects (outcome, producer/consumer, API/domain contract, allowlist, out-of-scope, binary
  AC, migration policy, test plan); map each TASK requirement to file:line. Missing any → discovery
  report + BLOCKED_<TASK>_SCOPE + ONE question, never invent scope.
- **A test can pass alone 10/10 yet flake ~1/12 in the combined suite** (order/timing sensitive).
  Prime cause: a `contextlib.suppress(Exception)` / broad `except` in the SAME test's setup leaves
  the SQLAlchemy session in pending-rollback, so the measured call emits extra ROLLBACK/BEGIN and
  trips a tight statement-count guard (`<=N`). Never dismiss "passes alone"; isolate (alone → own
  file → combined order), find the broad-except, and if the flaky test is OUT of the current
  allowlist, record known-limitation + root-cause hypothesis for Codex (or harden in-scope: narrow
  the except, raise bound to still-below-real-N+1).
- **Inline `# noqa` triage by rule, not by count**: PLC0415/BLE001/F401 on capability-gated local
  imports + `except Exception` probes are pre-existing deliberate patterns; E501 on long
  deterministic ids is formatting. Only a whole-file `# ruff: noqa:` header is the red flag.
  Verify "no new migration" by hash-unchanged of migrations/ + models.py, not just `alembic heads`.
- **User pings mid-run ("bao giờ xong?" / "sao lâu thế?"): answer immediately with a status table**
  (phase, suite counts, gates, ETA, and the concrete cause of any slow phase like a flaky-test
  investigation), then keep working. An unexplained long phase reads as a stall.
- Full detail (authority drill, flaky repro, noqa tables): `references/a02-t02-authority-gate-and-flaky-tests.md`.

- **Writer test-quality smells to grep for** (Codex flags these every cycle):
  1. test named `concurrent` that actually runs calls SEQUENTIALLY → require real threads +
     `threading.Barrier` + independent sessions, one winner;
  2. NaN/Infinity test hitting the wrong field (422 fires for an unrelated reason) → use a real
     `allow_inf_nan=False` DTO float field in an otherwise-valid payload;
  3. broad `try/except Exception` turning unexpected errors into PASS.

- **Ownership/binding validation must enumerate ALL identity columns** (workspace_id, project_id,
  video_item_id, source_generation, kind) — a role/job/artifact can match ws/video/gen/kind yet
  differ in `project_id` and be wrongly bound. Missing-column checks are the #1 adversarial finding.

- **`scripts/quality-baseline.ps1` Gate 2 (full Python pytest suite) takes 13–14 minutes** (~800s; Gate 1 env ~0s, Gates 3–7 quick). A Hermes tool timeout of 180s (or 60s) kills it mid-run with `exit 124` / `exit 143` (SIGTERM). Run it in the background (`terminal background=true`) or with an explicit `timeout ≥900s`, then watch `output/quality-baseline/<run_id>/summary.json` gates — the `overall.status` stays `RUNNING`/`exit_code:1` until ALL gates finish, so don't treat that interim status as a failure. Full 7/7 PASS is the only green signal.

## Project Overview

Local-first video object extraction and replacement tool. Input: MP4 video. Output: MP4 video with replaced objects.

## Architecture

### Backend (Python 3.11 + FastAPI)
- `app/workflow/` — service modules (project_workflow, ingest, segmentation, object_extraction, replacement, render, job_service, scene_chunking, scene_stitch, audio_dubbing, preset_service, channel_service)
- `app/api/` — FastAPI route handlers (never call AI libraries directly from routes)
- `app/adapters/` — AI model adapters (segmentation adapter with SAM2 + contour backends)
- `app/services/` — shared utilities (ffmpeg_utils, gpu_encoder, cleanup_service)
- `app/schemas/` — Pydantic v2 models (v2.0.0 with tracking metadata, occlusion, confidence, SceneStatus, ChannelWorkspace, TaskStatus)
- `app/main.py` — FastAPI entry point (uvicorn app.main:app)

### Frontend (Next.js + React + TypeScript strict)
- `frontend/src/components/` — Screen components (ScreenA through ScreenE), CompositeCanvas, SceneSelector, ScenePreview, AssemblyModal, DubbingPanel, PresetManager, ChannelDashboard
- `frontend/src/stores/` — Zustand stores
- `frontend/src/lib/` — API client and coordinate utilities
- `frontend/e2e/` — Playwright tests

### Key Conventions
- All new files use `from __future__ import annotations`
- TypeScript strict mode, no `any` types
- All UI labels in Vietnamese
- Ruff for linting, MyPy for type checking
- Pytest for tests
- Docker Compose for infrastructure

## Milestones
- M0: Technical Discovery & Vertical Spike
- M0.5: Core Tracking Validation (SAM2 GPU)
- M1A: Object Extraction Review UI (backend API + frontend scaffold)
- M1A.1: UI Integration & Acceptance (real preview, Playwright E2E, cancel, persistence) — COMPLETE (2d3fbae)
- M1B: Scene Chunking + Synced Audio + Step-by-Step Approval UI — COMPLETE (ec7ca8c)
- M1C: Background Cleaning & Inpainting — COMPLETE (e49055f: inpainting service, frame_sequence render, bulk mapping, 80 tests pass)
- M1D: Voice Separation, STT, Translation, TTS, Audio Remuxing — COMPLETE (ce8664f: audio dubbing service, 84 tests pass)
- M1D+Future: Demucs integration for better vocal separation (currently uses FFmpeg center-pan)
- M2: Multi-Object, Preset Manager, Multi-Format Render, Export ZIP — COMPLETE (d5720a0, 92 tests pass)
- M2+Hotfix: Ingest timeout fix + JPG frame extraction + find_frame_path helper — COMPLETE (43bbfff)
- M2+Architecture: On-Demand Video Chunking (ingest 3-5s for any video length) — COMPLETE (6fa94d5, 98 tests)
- M3: Multi-Channel Workspace Dashboard — COMPLETE (d38b638, 106 tests: Channel CRUD, task status, dashboard UI)
- M3.5: Performance & Automation — COMPLETE (99e9700, NVENC GPU encoder, lip-sync rate adjuster, cleanup service, auto-match endpoint, 108 tests pass)
- M4: State Rehydration & Persistent Session — COMPLETE (264008e, 111 tests: localStorage session, auto-resume on F5, recent projects list, GET /api/projects)
- M5: Master Performance & Auto-Segment — COMPLETE (115 tests: DELETE /api/projects/{id}, POST /api/projects/{id}/auto-segment-objects, cv2.setNumThreads(8))
- M6: UX & Navigation Overhaul — COMPLETE (f7cc37e, 123 tests: redirect_slashes=False fix, trailing slash aliases, NavigationHeader, button micro-descriptions, auto-mask-on-click)
### M6+Hotfix: list_all_projects cap removal + junk purge — COMPLETE (a888001, 15a6ffc: removed 30-project cap, sort by scenes_count, purged 1295 junk test projects freeing 3.6GB)
- M6.5: UX Legibility & Full Button Descriptions — COMPLETE (7b91d72: brightened text-gray-500→text-gray-400 + text-[10px]→text-[11px], added descriptions to every button on Screens B/C/D/E)
- M6.6: Test isolation & junk purge — COMPLETE (db7a2d9: centralized conftest client fixture with tmp project root, tests no longer write to real projects/, 117 passed + 6 skipped; purged 1295 junk test projects freeing 3.6GB, then 24 more — keep only the 2 real 235-scene projects)
- M7: ScreenD 3-column simplify + thumbnail API — COMPLETE (8c9f3d2, 127 tests: auto-select objects[0], object cards w/ thumbnails, 4 Vietnamese sliders, purple apply-all button, GET /objects with thumbnail_base64)
- M7.1: Auto crop thumbnails — COMPLETE (74e1124, 129 tests: TrackedObject.crop_path, _auto_crop_object on create, GET /objects/{id}/crop auto-generates, getObjectCropUrl, ScreenB/D crop display)
- M7.2: Distinct object names + crop base64 fallback — COMPLETE (048550d, 130 tests: auto-segment names 'Nhân vật #N (W×Hpx)'/'Vật thể #N (W×Hpx)', create_object name dedup, thumbnail_base64 fallback in img onError)
- M7.3: Inline crop base64 + clear objects + ScreenB delete/select — COMPLETE (89a6561, 132 tests: auto_segment_objects returns crop_png_base64 per object, DELETE /objects clears all + disk dirs, ScreenB 🗑️ Xóa Tất Cả Nhân Vật Cũ + ✅ Chọn Nhân Vật Này cards)
- M7.4: Delete single object + dedupe + gpu-info route ordering — COMPLETE (310e3e5, 849b47f, 98149ab, 136→137 tests: DELETE /objects/{id} removes one object + rmtree its dir, create_object dedupes same-bbox duplicates returning existing object, GET /gpu-info moved BEFORE /{project_id} to stop being captured as a project id, EncoderInfo is a dataclass not dict)
- M7.5: ScreenD preview-before-upload flow + replacement flow fix — COMPLETE (a91943f, 807b851, 137 tests: file input accept=image/*,.png,.jpg,.jpeg,.webp, select→local preview→side-by-side modal→confirm-upload, uploadReplacementSettings wrapped in {replacement_config}, added GET /objects/{id}/replacement-image endpoint, replacementUrl uses API_BASE helper not hardcoded :8000)
- M7.6: Auto-match 400 fix + ScreenD progress modal + voice toggle — COMPLETE (86182e2, 138 tests: auto_match_character no longer raises 400 when motion is None — falls back to selection bbox and applies replacement_config to all other-scene objects; ScreenD isApplying/applyProgress modal 10→40→80→100 with soft try/catch around autoMatchCharacter; DubbingPanel Voice Gốc (Original) vs AI Dubbing mode toggle)
- M7.7: ScreenD modal hang + canvas fallback draw + 50/50 comparison — COMPLETE (ed43d74, 138 tests: confirm-replace closes modal IMMEDIATELY + setPreviewMode('result') + kicks upload async; CompositeCanvas draws replacement even when frameMotion is null via fallback centroid (frame center, 30% height) so bbox-created objects render; comparison split with 📷 Ảnh Gốc / 🎨 Kết Quả Thay Thế label bars; next-render disabled until replacement asset exists)
- M7.8: Cache-bust + inpainted background + auto bottom-anchor — COMPLETE (301a09a, 140 tests: replacementUrl cache-busted ?t=Date.now()&v=asset_path so re-upload never shows stale image; NEW backend GET /objects/{id}/masks/{frame} + /objects/{id}/inpainted/{frame} (on-demand inpaint via InpaintingService, fallback to original frame when no mask); inpainted frame as base canvas layer under replacement; auto-anchor lifts default (0.5,0.5)→(0.5,1.0) bottom-center so feet/hips sit on original surface)
- M7.9: Multi-pose character presets + AI auto-pose match + auto-save sliders — COMPLETE (22f3af9, 141 tests: NEW app/services/preset_manager.py with 3 built-in sets (Bộ Boy Cool / Thỏ Cute / Gấu Nâu) × 4 poses (sitting/standing/walking/talking) as generated transparent PNGs; auto_pose_for_bbox aspect heuristic (w>h*1.1→sitting, h>w*1.3→standing, else talking); character routes declared BEFORE /{project_id} AND the apply route includes the {project_id} segment; auto_match_character returns 'pose' + copies pose asset to every other-scene object; ScreenD 🎭 Thư Viện Nhân Vật Mẫu Đa Tư Thế collapsible panel; transform sliders auto-save via debounced updateReplacementSettings (500ms); CompositeCanvas position = centroid + offset with bottom anchor (0.5,1.0))

## Stack
- Backend: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy/SQLModel, SQLite, FFmpeg, OpenCV, PySceneDetect, PyTorch, SAM 2.1, Pytest, Ruff, MyPy
- Audio pipeline: edge-tts (TTS), openai-whisper (STT), deep-translator (Google Translate)
- Frontend: Next.js, React, TypeScript strict, Tailwind CSS, Zustand, TanStack Query, Konva.js, Vitest, Playwright
- Infrastructure: Docker Compose, local filesystem storage, Makefile

## Writer BLOCKED liveness & scope-audit (verified S08-A02-T01-R1 recovery, 2026-08-20)

One-shot spawned writers (`hermes chat -q ... --yolo --source tool`) have NO user-visible
notification channel — they run headless until `notify_on_complete` fires on process exit. Real
failure mode seen this session (user: "sao block lại ko có heartbeat để thông báo?"):

1. **Poll REPORT status, not process exit.** A writer can sit at `REPORT.md = BLOCKED` for many
   minutes after its real work stopped (the A02-T01-R1 writer was BLOCKED ~10 min before the user
   noticed). The manager MUST read the writer's REPORT status line on every heartbeat and surface a
   `DECISION_NEEDED`/notification the moment BLOCKED appears — never assume a still-running process
   means no gate is pending. `notify_on_complete=true` only fires at process exit; a BLOCKED writer
   often keeps running (waiting on baseline/cleanup) so exit-notify is NOT a reliable block signal.

2. **Writer clarify-timeout must NOT self-widen the allowlist.** When a spawned writer's own
   `clarify` times out and the tool nudges "use best judgement", it MUST keep REPORT=BLOCKED and
   leave out-of-allowlist files untouched; the manager escalates the one question. The A02-T01-R1
   writer instead patched **8 allowlist-external test files** on best judgement after the timeout —
   mechanically correct, but a scope violation that only became acceptable after the USER's explicit
   later authorization. Never treat "best judgement" as a mandate to write outside the packet.

3. **Scope extension requires transparency (user-mandated).** Any out-of-allowlist edit must ship
   with a before/after SHA-256 snapshot and the exact per-file diff recorded in REPORT for Codex
   review. If edits already happened before authorization, reconstruct the before-state from the
   writer's `hermes chat -q` tool-call log (the `patch` blocks carry before/after strings) — never
   fabricate a before-hash. See `references/s08-writer-blocked-scope-audit.md`.

4. **New Alembic head breaks the pre-existing head-hardcoded test set.** Adding a migration head
   makes ~8 existing S08 suites fail mechanically (`test_s08_a01_role_taxonomy`,
   `test_object_intelligence_domain`, `test_object_grouping`, `test_object_correction`,
   `test_object_extraction`, `test_s08_a01_c1_migration_safety`, `test_persistence_bootstrap`,
   `test_durable_job_persistence`) because they hard-code `upgrade head -> version_num == "<old>"`.
   This is expected mechanical maintenance (recorded precedent in `references/s08-object-intelligence-domain.md`),
   so a migration-task packet should pre-authorize the head-literal/table-set bump explicitly rather
   than discovering it at the BLOCKED gate mid-run.

5. **Verify writer model/session from state.db, not from log head.** `hermes chat -q` logs do NOT
   print a session banner near the top; `--pass-session-id` only injects the id into the prompt. Real
   provenance evidence must come from ~/AppData/Local/hermes/state.db `sessions` table
   (newest `source='tool'` row for the launched session, `.model` column). reasoning=max is a config
   setting (`agent.reasoning_overrides`), not a CLI flag to pass.

## References
- `references/scene-chunking-stitching.md` — Scene chunking/stitching services, API endpoints, audio extraction flow, stitching flow
- `references/m1c-inpainting-frame-sequence.md` — Inpainting service, frame sequence rendering, bulk character mapping patterns
- `references/m1d-audio-dubbing.md` — Audio dubbing service (vocal separation, STT, translation, TTS, remux), pipeline architecture, edge-tts async patterns
- `references/m1d-frontend-dubbing-controls.md` — Frontend dubbing panel (DubbingPanel.tsx), step-by-step pipeline progress pattern, collapsible section integration, Edge TTS voice mapping
- `references/m2-preset-multiformat-export.md` — Preset manager service, multi-format render, export ZIP patterns
- `references/m2-frontend-implementation.md` — M2 frontend: multi-object canvas, PresetManager component, format selector, export ZIP button
- `references/multi-channel-workspace-dashboard.md` — Channel management dashboard: CRUD, project status tracking, Zustand store extension, Zustand.getState() in callbacks
- `references/m3.5-performance-automation.md` — NVENC GPU encoder, lip-sync rate adjuster, cleanup service, auto-match endpoint
- `references/ruff-import-ordering.md` — Ruff import sorting rules (I001, E402), stdlib-before-third-party, ternary (SIM108)
- `references/state-rehydration-persistence.md` — localStorage session persistence, useProjectRehydration hook, recent projects list, auto-resume on F5
- `references/s08-manager-handoff-experimental-writer.md` — PM-gated S08 manager handoff: packet-first launch, single writer, experimental model evidence, prior-verdict bookkeeping
- `references/s08-writer-worker-model-override.md` — Mid-session user steering for writer/worker model/provider/reasoning changes before launch; update packet/state and use explicit Hermes CLI flags
- `references/s08-writer-premature-exit-recovery.md` — Treat writer exit code 0 as only process completion; audit REPORT/LOG/expected artifacts, then resume the same session if incomplete
- `references/s08-writer-launch-and-verification.md` — Launch spawned writers (hermes chat flags), confirm the mandated model via `state.db` `sessions` table (reasoning=max is config-only — no `--reasoning` flag), prove no competing writer via tasklist + worktree mtime scan (wmic CommandLine-like self-matching noise), verify an unreleased migration head is safe to rewrite (read-only alembic_version scan), recovery-packet bookkeeping order
- `references/s08-writer-blocked-scope-audit.md` — Writer BLOCKED liveness (poll REPORT status, not process exit; one-shot writers push no notifications), clarify-timeout must NOT self-widen allowlist, user-mandated before/after-hash + diff transparency for out-of-allowlist edits, the 8 head-hardcoded S08 test files a new migration head breaks, manager re-run verification
- `references/s08-a02-r1-c1-semantic-correction.md` — C1 semantic-correction contract (F1 generation two-workflow design, F2 logical_id/branch safety, F3 idempotency identity fields, F4 frame+time containment, F5 ownership/artifact, F6 domain validation, F7 RESTRICT delete) + the +07 timezone UTC 24h-off bookkeeping pitfall
- `references/s08-a02-r1-r2-schema-api.md` — R2 schema/API layer on a verified core: R2 boundary (create schemas/router/tests only; app.py import+register only), strict Pydantic v2 rules (extra=forbid, finite-only + recursive finite walk, derived enums, no client logical_id/source_generation), the CRITICAL NaN-safe-validation-in-the-router pattern (default FastAPI 422 handler + Starlette JSONResponse allow_nan crash → 500), router/error/transaction contract, 30-item API test matrix, and the protected-`channels.json`-root-vs-fixture hash clarification
- `references/s08-overnight-manager-protocol.md` — Overnight/background manager continuation: timeboxed authority, phase gating (C1→R2→planning), packet-first bookkeeping, ≤2 parallel read-only reviewer lanes (RO-1 review / RO-2 next-task prep), heartbeat cadence, 502-resume, cutoff & OVERNIGHT HANDOFF contents
- `references/s08-a02-t01-r1-scope-recovery.md` — Full S08-A02-T01-R1 recovery recipe: writer clarify-timeout scope-self-expansion, mtime + tracked/untracked audit, reconstruct before/after SHA-256 from the writer tool log (indentation-tolerant reverse-apply + assert-count guards + ast.parse), user authorization with evidence conditions, manager addendum + evidence file
- `references/s08-correction-cycle-manager.md` — C1→C2 Correction-cycle manager orchestration on Codex CHANGES_REQUESTED: read current code per finding before writing TASK (cite real file:line), append-only verdict bookkeeping, single DeepSeek writer + 2 read-only reviewer lanes (RO-1 lineage/re-analysis/SQLite, RO-2 API strictness/OpenAPI/history), 18-step validation, C2 manager spot-checks (no role.source_generation mutation in tests, raw-SQL branch refused by DB, OpenAPI requestBody $ref, historical no-current-mix). Timestamp discipline (Asia/Bangkok +07:00, UTC=local−7h, at write time, never estimate; append ERRATA not rewrite). `custom` provider = local 9Router ocg/deepseek-v4-flash reasoning max. Pitfalls: `tee` needs the evidence dir to exist before launch; `git -C <MAIN>` fails under MSYS (cd into MAIN); migration rewrite allowed only within same unreleased revision id.
- `references/navigation-header-ux-overhaul.md` — NavigationHeader component, auto-mask-preview on click, button micro-descriptions pattern
- `references/m5-performance-autosegment.md` — Delete project endpoint, auto-segment objects (OpenCV contour detection), cv2.setNumThreads optimization
- `references/ux-navigation-overhaul.md` — NavigationHeader component, auto-mask-preview on click, button micro-descriptions, trailing slash 405 fix
- `references/screend-replacement-ui.md` — ScreenD 3-column replacement UI: auto-select first object, object cards + upload, 4-slider transform panel, save-then-auto-match apply-all button, scene count from project data
- `references/crop-thumbnail-object-naming.md` — Auto-crop thumbnail pattern (crop_path field, _auto_crop_object helper, GET crop endpoint with auto-generate), distinct object naming (Nhân vật/Vật thể #N (W×Hpx)), base64 fallback in <img> onError, synthetic-frame test setup
- `references/m7.3-crop-base64-clear-objects.md` — Inline crop_png_base64 in auto-segment JSON, DELETE /objects clear-all endpoint, ScreenB 🗑️ Xóa Tất Cả Nhân Vật Cũ + ✅ Chọn Nhân Vật Này card pattern, PNG magic-byte test assertion
- `references/screend-replacement-flow-fix.md` — M7.5 replacement flow: 422 wrapper-field fix, missing replacement-image endpoint, hardcoded :8000 port bug, gpu-info static-route ordering, cv2.imencode test recipe, live-verification curl pattern
- `references/screend-replacement-canvas-fixes.md` — M7.6–M7.8 replacement canvas: auto-match no-motion fallback, confirm-replace immediate modal close, CompositeCanvas fallback draw when frameMotion null, replacementUrl cache-busting (?t=&v=), inpainted+mask endpoints, auto bottom-anchor, split comparison labels, synthetic mask tests + patch-tool helper-insertion gotcha
- `references/m7.9-character-presets-pose-match.md` — M7.9 multi-pose character presets: preset_manager.py asset generation + aspect-ratio pose heuristic, character routes (router-prefix + missing-{project_id}-segment 404 traps), apply flow, auto-match pose branch, debounced slider auto-save, ScreenD library panel, 9 tests
- `references/s00-test-data-isolation.md` — S00-T01: constructor-DI test isolation for channels.json + preset assets, function-scoped tmp fixture pitfall (session-scoped = order-dependent), certutil hash before/after validation sequence, PM session protocol run-through
- `references/s08-object-intelligence-domain.md` — S08-T01 ObjectRole/ObjectOccurrence domain: schema + migration e7f8a9b0c1d2, repository/API contract under /api/v2/object-intelligence, idempotency/CAS/ownership semantics, validation recipe (read before S08-T02…T06)
- `references/s08-a01-migration-safety-single-authority.md` — S08-A01/A01-C1 taxonomy bridge: surgical SQLite `writable_schema` CHECK edit (why NOT batch_alter_table), fail-closed F1 downgrade guard, single `OBJECT_KINDS` runtime authority deriving ORM CHECK + schema pattern (F3), shared execute/preview invariant (F2), and the manager F1 round-trip/seed traps

### Scene status approval workflow pattern
When building step-by-step approval flows (user reviews each scene before proceeding):
- Use a status enum: `PENDING` → `DRAFT` → `APPROVED` (schema: `SceneStatus`)
- Frontend `SceneSelector` shows all items with color-coded badges (🟢🟡⚪)
- "Approve" button on active item → mutation → invalidate query → auto-advance to next unapproved item
- Assembly/completion gate: all items must be `APPROVED` before final action (e.g., stitch)
- Audio preview: `<audio>` element with `src` updated via `useEffect` when active item changes
- Pattern: TanStack Query for server state + Zustand for `activeSceneId` selection

### BA/PM architectural feedback loop
When BA/PM reviews a fix and says it's "only addressing symptoms" (e.g., "tăng timeout lên 300s mới chỉ là sửa bề mặt"), this triggers an architectural redesign. The pattern:
1. **Agent proposes quick fix** (e.g., increase timeout, change format)
2. **BA/PM rejects** with specific technical reasoning (e.g., "giải nén hàng chục nghìn frame ngay lúc ingest là SAI BẢN CHẤT KIẾN TRÚC")
3. **BA/PM provides new architecture** with concrete implementation steps
4. **Agent implements the new architecture** — do NOT defend the original fix
5. **Key lesson**: When the user says the approach is wrong, pivot immediately. Don't argue.

In MotionForge, this happened with the ingest timeout: agent increased timeout → BA said "wrong architecture" → agent implemented on-demand video chunking (3-5s ingest for any video length). The BA's architectural feedback was 100% correct and the resulting solution was far superior.

### Milestone completion workflow pattern
When completing a milestone (M1A, M1B, M1C, M1D, ...):
1. **Verify baseline** — `pytest tests/ -q`, `ruff check app/ tests/`, `npx tsc --noEmit`, `npx next build`
2. **Delegate backend + frontend in parallel** — dispatch two subagents simultaneously with full context
3. **Wait for both** — check live transcripts with `tail` on delegation logs; don't poll, wait for completion
4. **Verify independently** — run all 4 checks after each subagent completes
5. **Fix integration issues** — field name mismatches, missing imports between backend/frontend
6. **Commit** — single commit with all changes, descriptive message including test count
7. **Create progress report** — `docs/MILESTONE_{X}_PROGRESS.md` with: features delivered, tests added, verification results, files created/modified
8. **Update roadmap** — `docs/MILESTONES.md` with status markers (COMPLETE, IN PROGRESS, etc.)

Each milestone typically adds: new service(s), new schema fields, new API endpoints, new frontend components, new tests, progress report.

### Parallel backend+frontend delegation
For features touching both backend (Python) and frontend (TypeScript):
- Delegate backend to one subagent, frontend to another — they run concurrently
- Backend subagent: schemas, services, API endpoints, unit tests, ruff, pytest
- Frontend subagent: components, store updates, API client additions, tsc, build
- Each subagent gets FULL context (schema shapes, endpoint signatures, existing file contents)
- Verify independently: `python -m pytest tests/ -q` + `npx tsc --noEmit` + `npx next build`
- Fix integration issues after both complete (e.g., field name mismatches, missing imports)

### Ruff import sorting with `from __future__ import annotations` (I001)
Ruff enforces a blank line between `from __future__ import annotations` and subsequent imports. When replacing module headers (e.g., via the patch tool), always ensure:
```python
"""Module docstring."""

from __future__ import annotations

from collections.abc import Callable  # ← blank line required above
```
Without the blank line, ruff flags I001 (un-sorted imports) and E402 (module-level import not at top). This is easy to miss when patching the top of a file.

### Ruff UP017: `datetime.UTC` not `datetime.timezone.utc`
On Python 3.11+, ruff enforces `datetime.UTC` over `datetime.timezone.utc` (UP017). Combined with import sorting (I001), the correct import is:
```python
from datetime import UTC, datetime  # ← alphabetical: UTC before datetime
```
NOT `from datetime import datetime, UTC` — ruff will flag I001 on the reordered names. This pair of issues appears on nearly every new file that uses timestamps.

### Ruff SIM108 / SIM222
- **SIM108**: Use ternary for simple if/else assignments: `flag = A if cond else B` instead of 4-line if/else block. `ruff check --fix` does NOT auto-fix this.
- **SIM222**: `assert x != y or True` is always true — just use `assert x != y`. Common pattern when writing placeholder assertions that should be tightened later.

### Ruff E501 line-too-long
`ruff check --fix` does NOT auto-fix E501 (line too long). Must manually break long lines:
- Break at natural points: after `(`, before `/`, after `,`
- For f-strings: break the string or extract variables
- For `sorted(key=lambda)`: extract lambda to a variable or break across lines
- For path constructions: break at `/` operator

## Pitfalls

### MOTIONFORGE_DATABASE_URL env var leaks into every later alembic run
`migrations/env.py` resolves the DB URL in this order: `-x db_url=` flag >
`MOTIONFORGE_DATABASE_URL` env var > `alembic.ini`. Hermes terminal state
persists exported env vars across calls, so a one-off CLI migration run
(`export MOTIONFORGE_DATABASE_URL=...`) silently redirects EVERY later alembic
invocation — including pytest fixtures that build their own Config with
`set_main_option("sqlalchemy.url", ...)` — to the old target. Symptom: a whole
regression suite fails at fixture setup with `sqlite3.OperationalError: no
such table: workspace` while alembic logs show NO "Running upgrade" lines (it
connected to an already-upgraded DB). ALWAYS `unset MOTIONFORGE_DATABASE_URL`
and verify with `echo $VAR` after one-off migration runs; when DB tests
suddenly break with empty-tables errors, check the leaked env first.

### Windows MAX_PATH breaks deep basetemp pytest runs (ENOENT lies)
A deep `--basetemp` under a long worktree path (e.g.
`output/s08-sprint/<run-id>/...`) pushes pytest tmp_path + managed artifact
chains over Windows' 260-char MAX_PATH. Symptom: S05 production-wiring-style
tests fail inside jobs with
`failed reading source during copy: [Errno 2] No such file or directory:
'...artifacts\staging\<job>\import\...staging'` — `open("xb")` on a >260-char
path returns ENOENT. The error is a LIE about the file: the path is simply too
long. Prove it standalone: build the same path, `print(len(path))`, then
`open(path, 'xb')` → identical ENOENT. Fix: run artifact-chain tests with
SHALLOW basetemps (`C:/Users/Admin/AppData/Local/Temp/s08t01-*`), never under
`output/s08-sprint/<run-id>/...`; keep deep run dirs for pure-DB tests.
Classify such failures as harness/path incidents ONLY after the standalone
path-length reproduction, never by assuming code innocence.

### Background CLI delegates die with the turn; orphans can outlive it
`terminal(background=true)` children are killed when the Hermes turn/session
ends — a codex/claude exec launched in the background and then abandoned never
completes. Never end a turn before a background delegate finishes; use
foreground calls with bounded timeouts (chunked if >600s). Worse: an orphaned
`codex exec` can SURVIVE the session and keep writing files — a competing
writer silently corrupts concurrent edits. Before writing, verify no competing
writer: `wmic process where "name like '%codex%'" get ProcessId,CommandLine`
(or tasklist + grep) and match the exact exec command line, then kill
precisely with `MSYS_NO_PATHCONV=1 taskkill /PID <pid> /T /F`. NEVER
broad-kill node.exe/python.exe (Hermes desktop + dev servers run on them).

### FastAPI 0.139 / Starlette 1.3: included routers are _IncludedRouter objects
`app.routes` no longer contains plain APIRoute entries for included routers —
they appear as `_IncludedRouter` wrappers with NO `.path` attribute (iterating
`r.path` raises AttributeError). Debug route registration via the ROUTER
MODULE's own `router.routes` (paths already include the prefix) or via
TestClient probes — not by walking `app.routes`. A 404 on a route that exists
in `router.routes` is usually a URL-contract mismatch (tests calling
`/roles` while the collection is registered at `""`) — fix by adding path
aliases, not by reordering.

### Idempotent POST replay → 200: use `response: Response` param, not Response returns
For "idempotent create returns 201 first time, 200 on replay", declare
`response: Response` as a FastAPI parameter and set `response.status_code =
200` on replay, then return the DTO normally. Returning `Response(...)` from a
route annotated `-> RoleData` fails mypy strict (`Incompatible return value
type`) and bypasses response-model serialization. Same pattern applies to any
status-override-on-replay endpoint.

### Legacy project.json TrackedObject payloads REQUIRE selection.mode
`ProjectData.objects[].selection` is `SelectionInput` with a REQUIRED `mode`
field (`point`/`bounding_box`). Test fixtures that hand-write legacy
project.json objects without `selection.mode` make the legacy-mapping endpoint
500 (Pydantic ValidationError is not FileNotFoundError → uncaught). Include
`"mode": "bounding_box"` in every hand-written legacy object selection.

### S08 Object Intelligence domain (see references/s08-object-intelligence-domain.md)
Durable video-global `ObjectRole` + `ObjectOccurrence` domain: migration
`e7f8a9b0c1d2` (reversible), repository `app/persistence/object_intelligence.py`,
routes `/api/v2/object-intelligence`, idempotency/CAS/ownership semantics and
the S08-T01 validation recipe are captured in the reference file — read it
before S08-T02…T06 work.

### JSX `&amp;` HTML entity in text content
When writing JSX text content with `&`, use the literal `&` character — NOT the HTML entity `&amp;`. JSX is not HTML; it auto-escapes `&` when rendered.
```tsx
// ❌ WRONG — renders as literal "&amp;" on screen
<button>📁 Quản Lý Kênh &amp; Dự Án</button>
// ✅ CORRECT — renders as "&" on screen
<button>📁 Quản Lý Kênh & Dự Án</button>
```
This is easy to introduce when copying HTML into JSX or when the patch tool inserts HTML-encoded text. Always verify rendered text after creating components with ampersands.

### Patch tool can duplicate lines at file boundaries
When using the `patch` tool to replace content at the very start or end of a file, the old_string may match a substring that overlaps with adjacent content. This can produce duplicate lines (e.g., two docstrings at the top). Always verify the first few lines after patching module headers. If duplication occurs, re-patch with the duplicated block as old_string and the correct single version as new_string.

### Pydantic v2 alias serialization (CRITICAL)
When backend Python field name differs from what the frontend expects in JSON:
- **DO NOT** use `model.model_dump(by_alias=True)` on all routes — it converts ALL fields to camelCase, breaking tests and other consumers that expect snake_case
- **DO** create a helper function for specific field renames:

```python
# app/api/helpers.py
def job_response(info: JobInfo) -> dict:
    """Serialize JobInfo with 'status' key for frontend compatibility."""
    data = info.model_dump()
    data["status"] = data.pop("state")
    return data
```

- Use `job_response(info)` in all routes that return job status
- For other mismatches, use the same pattern: `model_dump()` then rename specific keys
- Only use `by_alias=True` when you genuinely want ALL fields in camelCase (e.g., a dedicated frontend-facing endpoint)

### MSYS/Git-Bash path issues on Windows
- FFmpeg and other Windows-native binaries CANNOT use MSYS paths like `/c/Users/...`
- Must use Windows-native paths: `"C:\\Users\\Admin\\..."` or `"C:/Users/Admin/..."`
- Symptom: ffmpeg silently fails with "No such file or directory" on MSYS paths
- Workaround: use Windows path for ffmpeg output, MSYS path for Python/shell operations

### `sed -i` corruption on Windows/MSYS
`sed -i` on MINGW64 silently corrupts files when substitutions involve parentheses, pipe chars, or multi-line patterns. The corruption is only visible on the next `read_file` — the file appears to have the wrong content (e.g., wrong line replaced, special chars mangled).
- **Never use `sed -i` for complex substitutions on Windows**
- Use the `patch` tool or Python script via `terminal` instead
- Always verify with `read_file` after any `sed -i`

### Concurrent sibling-agent edits to shared files (frontend/backend split)
When the backend+frontend split is delegated as parallel subagents, the two may touch the SAME file (e.g., `frontend/src/lib/api.ts` — backend agent adds `listObjects`, frontend agent adds a `scene_details` field). Symptom: the `patch`/`write_file` tool warns "file was modified by sibling subagent after this agent's last read".

Workflow that keeps both changes:
1. **Re-read the file after any sibling-modification warning** before continuing to edit — confirm your intended region is intact and the sibling's addition is compatible (types only, no conflicts).
2. **Patch minimally** — a one-line `scene_details: SceneDetail[];` addition, not a rewrite of the interface.
3. **Verify after each external change**: re-run `npx tsc --noEmit` and `npx next build` at the end, since `api.ts` may have gained a sibling's code that must still typecheck.
4. **Attribute diffs precisely**: when reporting, use `git diff <file>` and state which lines are yours vs the sibling's (e.g., "the `listObjects` addition is from the sibling agent, my change is only the `scene_details` field") so the user isn't confused by unrelated hunks.

### Playwright browser installation
- `npm install -D @playwright/test` does NOT install browser binaries
- Must separately run: `npx playwright install chromium`
- Browser installed to: `C:\Users\Admin\AppData\Local\ms-playwright\`

### Frontend-backend schema alignment
- Frontend API client (`frontend/src/lib/api.ts`) defines TypeScript interfaces independently from backend Pydantic models
- Always verify field names match: check `api.ts` interface vs `app/schemas/__init__.py` model
- Common mismatch: `status` vs `state`, `clipMode` vs `clip_mode`
- Backend aliases (`alias="camelCase"`) must have matching `serialization_alias` to actually appear in JSON responses
- **Missing-field instance**: `ProjectData` in `api.ts` originally lacked `scene_details` even though the backend Pydantic model has it (`scene_details: list[SceneDetail] = Field(default_factory=list)`). A UI needing `project.scene_details?.length` hit a type error. Fix: add `scene_details: SceneDetail[];` to the frontend interface (clean, typed) instead of casting `project as { scene_details?: unknown[] }`. Prefer extending the interface over a cast — the backend serializes it by default, so the type is accurate.

### Playwright E2E: wait for destination, not transient text
When the app auto-navigates after a quick operation (e.g., ingest completes → navigates to selection screen), the transient text (e.g., "Hoàn tất!") disappears before Playwright can assert on it.
- **Fix**: Wait for the DESTINATION screen text instead of the transient completion text
- Example: `await expect(page.locator("text=Chọn vật thể")).toBeVisible({ timeout: 90_000 })`
- Do NOT: `await expect(page.locator("text=Hoàn tất!")).toBeVisible()` — this races with auto-navigation

### Propagate mask fallback race condition
The propagate endpoint needs `objects/{oid}/masks/initial_mask.png`. A fallback exists that copies from `debug/preview_mask_{frame}.png`, but:
- The preview mask is saved at the frame index used for preview (e.g., `preview_mask_45.png`)
- The propagate endpoint looks for ANY `preview_mask_*.png` in debug/
- In E2E tests, the preview and propagate may use different projects/sessions, causing the fallback to miss
- **Fix for E2E**: Frontend should send `mask_data` (base64 PNG) when creating the object, so the mask is stored directly with the object
- **Fix for API**: Always pass mask_data in createObject call if you have it from previewMask response

### SAM2 post-processing warning
- `cannot import name '_C' from 'sam2'` warning is cosmetic — SAM2 still works
- Missing `_C` means post-processing (hole filling) is skipped, but results are fine in most cases

### Patch tool double-slash on path aliases
When using the `patch` tool to add TypeScript imports with path aliases (`@/lib/api`), the tool may corrupt the path to `@//lib/api` (double slash). This silently passes `tsc --noEmit` but breaks at runtime.
- **Symptom**: `Module not found: Can't resolve '@//lib/api'` at build/runtime
- **Always verify**: After any patch that touches `from "@/..."` imports, grep the file for `@//` and fix immediately
- **Root cause**: The patch tool's string matching can insert an extra `/` when the context line ends with a path separator or quote

### useEffect before variable declaration (TS2448/TS2454)
When adding a `useEffect` that references a variable (e.g., a mutation from `useMutation`), placing the useEffect **before** the variable declaration causes TypeScript errors:
```
error TS2448: Block-scoped variable 'previewMut' used before its declaration.
error TS2454: Variable 'previewMut' is used before being assigned.
```
**Fix**: Always place useEffects that reference component-level variables **after** those variables are declared. The natural order is:
1. State declarations (`useState`)
2. Refs (`useRef`)
3. Derived values
4. Effects that only use state/refs (safe to place early)
5. Mutations (`useMutation`)
6. Effects that reference mutations (must come after step 5)
7. Callbacks (`useCallback`)

This is easy to miss when inserting new effects into existing components — always check that the effect's dependencies are declared above it.

### Ref flag pattern for deferred mutation trigger
When you need to trigger a mutation (e.g., mask preview) automatically after a state update inside a `useCallback`, you can't call `mutate()` directly because the state hasn't updated yet in the closure. The clean pattern uses a ref flag:

```tsx
const autoPreviewRef = useRef(false);

// In the click handler (useCallback):
const handleCanvasClick = useCallback((e) => {
  // ... compute coordinates ...
  setPoints((prev) => [...prev, newPoint]);
  autoPreviewRef.current = true;  // flag for useEffect
}, [meta, tool]);

// After the useMutation declaration:
const previewMut = useMutation({ mutationFn: async () => { /* ... */ } });

useEffect(() => {
  if (autoPreviewRef.current && points.length > 0) {
    autoPreviewRef.current = false;
    previewMut.mutate();
  }
}, [points, previewMut]);
```

**Why not setTimeout**: `setTimeout(() => previewMut.mutate(), 100)` relies on React re-rendering within the timeout window — fragile and race-prone. The ref+useEffect approach guarantees the mutation fires after React has committed the state update.

**Pitfall**: The useEffect must be placed **after** the `useMutation` declaration (see "useEffect before variable declaration" pitfall above).

### Button micro-descriptions for tool panels
When building tool/action panels (e.g., ScreenB selection tools), add small gray description text under each button to explain what it does:
```tsx
<button className="w-full px-2 py-1.5 text-xs rounded bg-blue-600 text-white">
  Điểm +
</button>
<p className="text-[11px] text-gray-400 mt-1">
  Click 1 điểm màu xanh trên thân nhân vật đối thủ.
</p>
```
- **READABILITY IS THE #1 COMPLAINT — use `text-[11px] text-gray-400` (bright), NOT `text-[10px] text-gray-500`.** The user explicitly rejected `text-[10px] text-gray-500` as "font chữ khá tối ko nhìn đc" (too dark to see) on the dark theme. `text-gray-500` on `bg-gray-900` panels is nearly invisible; `text-gray-400` at 11px is legible. If the user says "các nút chưa có giải thích" but descriptions already exist in code, the problem is usually CONTRAST (too dark/too small), not missing text — grep for `text-[10px] text-gray-500` and brighten before adding new content.
- Keep descriptions to 1 line, Vietnamese, action-oriented
- Apply the pattern to EVERY action button on ALL screens (B: Điểm+/Điểm−/Hộp/Xóa/Xem mask/Chấp nhận/Auto-detect; C: Thay ảnh/Sửa vùng chọn/Xóa object; D: Áp dụng/Đặt lại/Tiếp Render/Bulk/Auto-Match; E: Preview/Final/Format/Export/Cleanup) — not just the primary screen
- For tool grids with descriptions, switch from `grid grid-cols-2` to `space-y-2` stacked layout to give each button+description its own row

### ESLint pre-existing error baseline in CompositeCanvas
CompositeCanvas.tsx has 3 pre-existing `react-hooks/set-state-in-effect` errors from image-loading effects (frame, mask, replacement). These are not regressions — they're the established pattern. When adding a new image-loading effect (e.g., sequence frame), follow the same `setState(null)` pattern and note that the eslint error is consistent with existing code. Also has pre-existing warnings for unused variables (`anchorAbsX`, `anchorAbsY`, `clipOpFor`).
- **Do not** treat these as blockers for `tsc --noEmit` or `next build` — both pass cleanly
- **Do not** refactor existing effects to fix the lint unless explicitly asked

### Next.js page.tsx with screen switcher — unreachable code
When `page.tsx` has a `switch(screen)` with `return` in every case, any JSX added after the switch is unreachable (TypeScript won't error, but the code never runs).
- **Fix**: Extract the switch into a sub-component (`ScreenRouter`), then wrap it in the parent with floating UI:
```tsx
function ScreenRouter() {
  const screen = useProjectStore((s) => s.screen);
  switch (screen) { /* ... */ }
}
export default function Home() {
  return <><ScreenRouter /><FloatingButtons /></>;
}
```
- This keeps the screen switch clean while allowing persistent overlays (modals, FABs) across all screens

### Adding feature panels to existing multi-column layouts
When adding a new sidebar panel (e.g., scene selector) to an existing multi-column layout (like ScreenD's left/center/right):
1. Read the full current layout structure first — identify all flex children and their widths
2. Add the new panel as a `flex-shrink-0` child with explicit width (e.g., `w-52`)
3. Place it before or after existing panels depending on information hierarchy
4. Keep the center content area as `flex-1 min-w-0` so it absorbs remaining space
5. If the layout was single-column, convert to `grid grid-cols-[200px_1fr_280px]` or equivalent flex

### TrackedObject.replacement_config is nullable
`TrackedObject.replacement_config` is `ReplacementConfig | None = None`. When building presets or iterating objects:
- Always check `if obj.replacement_config` before accessing `.asset_path`, `.model_dump()`, etc.
- When creating objects without replacement, `replacement_config` is `None`, not an empty `ReplacementConfig()`
- Pattern in preset save: `rc.asset_path if rc else ""` and `rc.model_dump(by_alias=True) if rc else {}`

### Port conflict / zombie uvicorn processes
Port 8000 on this machine is permanently occupied by a zombie uvicorn process from another project ("Goha MMO Clone"). The zombie cannot be killed (`taskkill` says "not found" but `netstat` still shows LISTENING). **Always use port 8002 for MotionForge backend.**

Configuration:
- `frontend/.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8002`
- Backend start: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8002`
- `.env.local` is gitignored — must be created manually after clone

Debugging port conflicts:
1. `netstat -ano | grep ":PORT.*LISTENING"` → get PID
2. `wmic process where "PID=X" get Name,CommandLine` → identify the app
3. If it's NOT your app: `cmd.exe /C "taskkill /PID X /F /T"`
4. If taskkill says "not found" but netstat still shows LISTENING → zombie, use different port
5. Update `frontend/.env.local` to point to the new port
6. Restart frontend dev server to pick up the change

### QA environment for browser E2E (S06 character library + worktrees)
Browser E2E runs against TWO long-lived servers rooted at the WORKTREE (not MAIN):

- Backend :8002: `MOTIONFORGE_ROOT=<worktree>/output/qa-root` AND **cwd = `<worktree>/output/qa-root`**:
  `cd output/qa-root && MOTIONFORGE_ROOT=<abs qa-root> python -m uvicorn --app-dir <worktree> app.main:app --host 127.0.0.1 --port 8002`
- Frontend :3010: `cd frontend && npm run dev -- -p 3010` (`.env.local` sets `NEXT_PUBLIC_API_URL=http://localhost:8002`).
- Playwright: `npx playwright test --config=playwright.s06t0X.config.ts` (baseURL :3010, API :8002).

**CRITICAL cwd gotcha — the managed root is RELATIVE.** `JobService._managed_root` defaults to `"artifacts"` and resolves against the server's CWD; only the DB path uses `MOTIONFORGE_ROOT`. If the server's cwd is wrong, `GET .../validation` reports "artifact file missing on disk: characters/..." for EVERY asset even though the files exist under `output/qa-root/artifacts/...` (the validator resolves `storage_root / relative_path` from cwd). Symptom: content endpoint 404s/validation fails while `ls` shows the files. Fix: start uvicorn with cwd = `output/qa-root`. Verify with `curl .../validation` → `"status":"valid"` and `curl -o /dev/null -w "%{http_code}" .../assets/{id}/content` → 200.

**Servers die/age silently.** Background uvicorn can be reaped (check `process(action='list')`, then `curl`); a long-lived `next dev` can hang so every `page.goto` times out (T04 review hit this too). Restart both, then probe: `curl -s -o /dev/null -w "%{http_code}" http://localhost:3010/characters` (expect 200) before re-running Playwright.

**Seeding real QA data (user rejects mocks).** `output/qa-seed-s06-t05.py` pattern: open the isolated DB with `create_engine_for_path(output/qa-root/data/motionforge.db)` and use the APPROVED importer/repository directly — real rows + real managed PNGs. Idempotent: skip codes that exist; ALWAYS create a fresh timestamped success target (`co_t05_<HHMMSS>`) per run and write `output/qa-s06-t05/seed-state.json` for the spec. Prefer fresh unique codes over destructive `--reset` (rmtree-style resets trip approval gates and lose evidence). On Windows git-bash kill a stale server with `MSYS_NO_PATHCONV=1 taskkill /PID <pid> /F` (bare `//PID` gets mangled by MSYS path conversion).

### FastAPI error envelope `{"detail": payload}` — unwrap in the fetch layer (CRITICAL)
FastAPI wraps EVERY error payload in `{"detail": <payload>}` — for a 422 raised with `HTTPException(422, detail={...})` the body is `{"detail": {message, missing_slots, errors}}`. If the frontend fetch layer stores the raw body as the error's `detail`, UI code reading `error.detail.message` gets `undefined` and silently falls back to a generic message (and `missing_slots`/`errors` lists render empty). Fix once in the client:

```ts
class ApiError extends Error { status: number; detail: unknown; ... }
// in apiFetch on !res.ok:
const body: unknown = await res.json();
const detail = typeof body === "object" && body !== null && "detail" in body
  ? (body as { detail: unknown }).detail
  : body;
throw new ApiError(res.status, detail, `API ${res.status}: ${JSON.stringify(detail ?? "")}`);
```

Note: for 409 raised as `HTTPException(409, "string message")`, `detail` unwraps to a plain STRING — status-code dispatch, not detail shape, is the reliable discriminator. Also: transient success/error feedback must render OUTSIDE the conditional panel that unmounts on state change (e.g., a publish panel that disappears once the version becomes published) or the "Đã xuất bản" message vanishes; reset such feedback in event handlers, not `useEffect` (`react-hooks/set-state-in-effect` fails the lint gate).

### FastAPI route ordering: empty path before path parameters
When adding a new endpoint to `app/api/routes/projects.py` that shares a prefix with an existing parameterized route, the empty-path route MUST be defined BEFORE the parameterized one. FastAPI matches routes in definition order — if `/{project_id}` is defined first, `GET ""` will never match because FastAPI treats the empty string as a valid `project_id`.

```python
# ❌ WRONG — GET "" never matches, captured by /{project_id}
@router.get("/{project_id}")
def get_project(project_id: str) -> ProjectData: ...

@router.get("")
def list_all_projects() -> list[dict]: ...

# ✅ CORRECT — empty path matches first
@router.get("")
def list_all_projects() -> list[dict]: ...

@router.get("/{project_id}")
def get_project(project_id: str) -> ProjectData: ...
```

This applies to all HTTP methods. Always place `""` routes before `"/{param}"` routes in the file.

### Getting the projects root directory
`ProjectWorkflowService` has a `projects_dir` property that returns `self._projects_dir` (the directory containing all project subdirectories). Use this directly — do NOT use `pwf._project_dir("").parent` which goes one level too high:

```python
# ❌ WRONG — .parent goes to the parent of projects_dir
projects_dir = pwf._project_dir("").parent

# ✅ CORRECT — use the property
projects_dir = pwf.projects_dir
```

`_project_dir("")` returns `self._projects_dir / ""` = `self._projects_dir`. Adding `.parent` navigates UP to `config.project_root`, which is NOT where projects live.

### Creating new test files with project root isolation
**PREFERRED (supersedes the per-file copy below): centralize fixtures in `tests/conftest.py`.** Since commit `db7a2d9`, conftest defines ONE global `client` fixture + `_patch_project_root` fixture that patch `deps._config`, `deps._project_wf`, and `deps._job_service` to a tmp path. New test files simply declare `client` as a parameter — do NOT define a local `client` fixture (a local fixture with the same name OVERRIDES the conftest one, silently reintroducing disk pollution).

```python
# tests/conftest.py (the canonical version)
@pytest.fixture()
def _patch_project_root(monkeypatch, tmp_path: Path) -> Path:
    test_root = tmp_path / "motionforge_test"
    test_root.mkdir(exist_ok=True)
    monkeypatch.setenv("MOTIONFORGE_PROJECT_ROOT", str(test_root))

    from app.api import deps
    from app.config import AppConfig
    test_config = AppConfig(project_root=test_root, models_dir=test_root / "models", output_dir=test_root / "output")
    monkeypatch.setattr(deps, "_config", test_config)
    monkeypatch.setattr(deps, "_project_wf", ProjectWorkflowService(test_config))
    monkeypatch.setattr(deps, "_job_service", JobService())
    return test_root

@pytest.fixture()
def client(_patch_project_root: Path):
    from fastapi.testclient import TestClient
    from app.api.app import app
    return TestClient(app, raise_server_exceptions=False)
```

**CRITICAL GOTCHA — the `config` global singleton is NOT patched:** `from app.config import config` returns the REAL global (project_root = the real `C:\Users\Admin\MotionForge2D`). Patching `deps._config` only redirects API calls. Tests that read project files from disk must use `deps._config.project_root`, never `config.project_root`:

```python
# ✅ CORRECT — reads the tmp root the API actually wrote to
from app.api import deps
project_file = deps._config.project_root / "projects" / pid / "project.json"

# ❌ WRONG — points at the REAL projects/ dir (assert False or, worse, reads real data)
from app.config import config
project_file = config.project_root / "projects" / pid / "project.json"
```

**Frame-dependent tests in isolated root:** tests that rely on pre-extracted frames (e.g., preview-mask at `frame_index: 45`) get 404 in a fresh tmp root because on-demand extraction isn't wired into raw TestClient. Handle in the fixture — check the preview-mask response and `pytest.skip(...)` with a clear reason instead of failing:

```python
r = client.post(f"/api/projects/{pid}/objects/preview-mask", json={...})
if r.status_code != 200:
    pytest.skip("Frame 45 not extractable in isolated test root")
```

**Verify zero pollution:** after running the full suite, confirm `projects/` gained no new dirs:
```bash
python -c "from pathlib import Path; print([d.name for d in Path('projects').iterdir() if d.is_dir()])"
```
If junk appeared, a test file is still using a local client fixture or raw `TestClient(app)` — grep for `def client()` in `tests/`.

### PM session protocol (docs/pm gated tasks)
MotionForge 2D now runs PM-gated tasks under `docs/pm/sessions/<ID>/` (SESSION_PROTOCOL.md + TASK.md + LOG.md + REPORT.md + PM_REVIEW.md). When a task prompt references this structure:
1. **Read in order**: `docs/pm/SESSION_PROTOCOL.md` → `<session>/TASK.md` → every file in TASK.md "Required reading". Do NOT roam into PRD/Master Plan/milestone docs.
2. **Confirm in chat before coding**: Task ID, outcome, allowed write scope, forbidden scope, validation commands, plan ≤ 7 steps.
3. **Protect user changes**: `git status --short` first; identify user-modified files (e.g. preset manager, tests, `channels.json`, character assets) and never overwrite them.
4. **LOG.md is append-only** — never rewrite old entries; record corrections as new entries. Baseline commands/results go in first, before any code change.
5. **Stop conditions** (need to touch `channels.json`, out-of-scope file, risk overwriting user changes, architecture expansion, can't distinguish prod/test data, contradictory AC) → set REPORT.md to `BLOCKED`, log it, ask exactly ONE minimal question.
6. **Finish**: REPORT.md → `SUBMITTED` (never self-`APPROVED`), evidence per AC, list changed files, record deviations/out-of-scope findings, no commit/push. See `references/s00-test-data-isolation.md` for the S00-T01 run-through.

### Test-data isolation from production-root storage (channels.json, preset assets)
When tests must stop writing to production-root data (`channels.json`, `presets/characters/*.png`):
1. **Constructor DI hook, not global monkeypatch** — add an optional path param that defaults to the production path:
```python
def __init__(self, config: AppConfig, channels_file: Path | None = None) -> None:
    self._config = config
    self._channels_file = channels_file or (config.project_root / "channels.json")
```
   Default preserves runtime behavior exactly; tests inject a temp path. No global path monkeypatching → parallel/order-free safe.
2. **Function-scoped `tmp_path` for isolated storage fixtures** — CRITICAL pitfall: a session-scoped shared tmp file makes tests ORDER-DEPENDENT (each test passes alone, but the file run fails because earlier tests polluted the shared store — exactly the `len(channels) == 2` style failure). Isolation fixture must be function-scoped so every test starts from an empty store.
3. **Preset/singleton services**: don't call the production singleton (`get_preset_manager()` roots at `deps._config.project_root/presets/characters` and `ensure_assets()` writes PNGs). Construct the class directly with an isolated root: `CharacterPresetManager(tmp_path / "presets" / "characters")`.
4. **Regression evidence**: (a) in-test byte compare of the root file before/after CRUD; (b) CLI-level SHA256 of root `channels.json` before and after TWO consecutive targeted runs — hashes must be identical. On Windows git-bash use `certutil -hashfile channels.json SHA256 | sed -n '2p'` (PowerShell `Get-FileHash` equivalent).
5. **Watch for pollution timing**: a baseline run BEFORE the fix may still write once — the diff grows during baseline, then stays frozen. Record before/after around the *fixed* runs as the proof.
6. **A local `client` fixture — even `scope="session"` — silently bypasses conftest isolation (CAUGHT IN PM REVIEW).** `tests/test_preset_manager.py` originally defined `@pytest.fixture(scope="session") def client(): from app.main import app; with TestClient(app) as c: yield c`. A local fixture with the same name OVERRIDES the conftest one, and because it never depends on `_patch_project_root`, route-level `get_preset_manager()` resolved to the REAL `deps._config` → production preset dir reachable. Any endpoint test module must use the conftest `client` fixture; if a module defines its own `client`, delete it. Grep check after wiring: no `def client(` in `tests/` outside conftest.py.
7. **Never construct a production-rooted manager in a test — even for a "no-op".** The first `TestIsolation::test_isolated_manager_writes_only_tmp_assets` created `CharacterPresetManager(prod_dir)` and called `pm2.ensure_assets()` "to prove it adds nothing". It passed ONLY because all 28 assets already existed — pass-by-machine-state, not by safety contract (a missing asset would have been created before the assertion ran). Correct contract: snapshot the production dir READ-ONLY (filename → sha256 dict via a `_snapshot_preset_dir()` helper), generate everything on a tmp root, then assert the snapshot is unchanged. Also verify with grep that the ONLY `ensure_assets()` calls in tests run on tmp roots.
8. **Endpoint-level regression proof**: with the conftest `client`, `GET /api/projects/presets/characters` generates assets under `deps._config.project_root/presets/characters` (tmp) — assert ≥ 4×6 PNGs exist there, production preset snapshot unchanged, and root `channels.json` bytes unchanged, all in one test (`TestIsolation::test_endpoint_generates_assets_under_tmp_root`).
9. **PM validation demands asset-level hashes, not just file-set**: snapshot per-file sha256 of production preset assets before/after (`sha256sum presets/characters/*.png | sort -k2 > before.sha256`, `diff` after) in addition to the `channels.json` hash — file-set equality misses content mutation.

### Legacy per-file fixture (only if you can't use conftest)
Each test file that tests API endpoints needs its own `_patch_project_root` fixture (autouse=True) because it's defined locally in `test_api.py`, not in `conftest.py`. When creating a new test file, copy the full fixture:

```python
@pytest.fixture(autouse=True)
def _patch_project_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Override project root so all tests use a temp directory."""
    test_root = tmp_path / "motionforge_test"
    test_root.mkdir()

    from app.api import deps
    from app.config import AppConfig

    test_config = AppConfig(
        project_root=test_root,
        models_dir=test_root / "models",
        output_dir=test_root / "output",
    )
    monkeypatch.setattr(deps, "_config", test_config)
    monkeypatch.setattr(
        deps, "_project_wf",
        __import__(
            "app.workflow.project_workflow", fromlist=["ProjectWorkflowService"],
        ).ProjectWorkflowService(test_config),
    )
    monkeypatch.setattr(
        deps, "_job_service",
        __import__(
            "app.workflow.job_service", fromlist=["JobService"],
        ).JobService(),
    )
    monkeypatch.setattr(
        deps, "_replacement_service",
        __import__(
            "app.workflow.replacement_service", fromlist=["ReplacementService"],
        ).ReplacementService(deps._project_wf),
    )
    monkeypatch.setattr(
        deps, "_seg_service",
        __import__(
            "app.workflow.segmentation_service", fromlist=["SegmentationService"],
        ).SegmentationService(test_config),
    )
    return test_root


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    from app.api.app import app
    return TestClient(app, raise_server_exceptions=False)
```

All service singletons (`_config`, `_project_wf`, `_job_service`, `_replacement_service`, `_seg_service`) must be patched, or tests will use the real filesystem/config.

### Adding `_save_project` to `ProjectWorkflowService`
`ProjectWorkflowService` wraps `ProjectService` for all persistence. When you need to save a modified `ProjectData` object directly (e.g., after mutating `scene_details`), add or use `_save_project`:
```python
def _save_project(self, project_id: str, data: ProjectData) -> None:
    """Save project data directly."""
    svc = ProjectService(self._project_json(project_id))
    svc._data = data
    svc.save()
```
This is needed when endpoints modify the in-memory `ProjectData` (from `get_project`) and want to persist without round-tripping through `ProjectService.load()` again. The pattern `pwf._save_project(project_id, proj)` is used in API routes.

### "Failed to fetch" = backend crashed or not running
When the frontend shows "Failed to fetch" or "Không thể thực hiện" errors, the backend process has crashed or exited. This is NOT a frontend bug.

**Diagnosis:**
```bash
curl -s http://127.0.0.1:8002/health 2>&1
# If exit code 7 (connection refused) → backend is down
```

**Fix — restart backend WITH FFmpeg in PATH:**
```bash
export PATH="$PATH:/c/Users/Admin/AppData/Local/Microsoft/WinGet/Links"
cd C:/Users/Admin/MotionForge2D
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

**Root cause**: The `conftest.py` PATH fix only applies to the pytest process, NOT to background uvicorn processes spawned by `terminal(background=true)`. The backend process loses FFmpeg access and crashes when it tries to run scene detection or frame extraction.

**Prevention**: Always set `export PATH` before starting uvicorn in background. The `start_app.bat` script handles this automatically.

### FFmpeg discovery pattern for workflow services
Services that call FFmpeg/FFprobe should use a `_find_ffmpeg()` / `_find_ffprobe()` method with this fallback chain:
```python
import shutil
from pathlib import Path

def _find_ffmpeg(self) -> str:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg
    win_path = Path(r"C:\Users\Admin\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe")
    if win_path.exists():
        return str(win_path)
    raise FileNotFoundError("ffmpeg not found")
```
- Always try `shutil.which` first (works when PATH is set)
- Fall back to the known Windows install path
- Raise `FileNotFoundError` with a clear message
- Use `subprocess.run(cmd, capture_output=True, check=True)` for execution
- For audio extraction, use `-acodec copy` (no re-encode) with `-avoid_negative_ts make_zero`

**IMPORTANT for background processes**: `conftest.py` auto-fixes PATH for pytest, but background uvicorn processes do NOT get this fix. Always `export PATH="$PATH:/c/Users/Admin/AppData/Local/Microsoft/WinGet/Links"` before starting uvicorn. Without this, the backend crashes silently when ingest/scene-detect calls FFmpeg.

**IMPORTANT**: For shared/utility code, use `from app.services.ffmpeg_utils import find_ffmpeg, find_ffprobe` instead of duplicating the fallback chain. Workflow services (audio_dubbing, scene_chunking, etc.) use private `_find_ffmpeg()` / `_find_ffprobe()` methods, but new services should import from the shared module.

### `test_integration.py` segfault is pre-existing
`tests/test_integration.py` segfaults (exit 139) due to heavy SAM2/cv2 imports — this is NOT caused by recent changes. When running the full test suite, use:
```
python -m pytest tests/ -q --ignore=tests/test_integration.py
```
Always verify this is pre-existing by running with `--ignore` before investigating as a regression.

### Ruff F821: loop variable vs outer scope in FFmpeg filter chains
When building multi-stage FFmpeg filter chains in a loop (e.g., TTS rate adjustment → atempo fallback), variable names can shadow or confuse loop-scoped names with outer scope:
```python
# ❌ WRONG — output_path doesn't exist here, out_path is the loop variable
tmp_path = output_path.with_suffix(".tmp.wav")

# ✅ CORRECT — use the loop variable
tmp_path = out_path.with_suffix(".tmp.wav")
```
This is easy to miss when the method has a parameter called `output_path` (e.g., in `remux_audio`) and a loop variable called `out_path` (in `tts_segments`). Ruff catches this as F821 (undefined name).

### Ruff F841: unused test variables
When a test only asserts on side effects (e.g., directory deletion) and doesn't need the stats dict, assign to `_` or call without assignment:
```python
# ❌ WRONG — stats unused
stats = svc.cleanup_project(tmp_path)
assert not dir.exists()

# ✅ CORRECT — call without assignment
svc.cleanup_project(tmp_path)
assert not dir.exists()
```

### Ruff F401: unused pytest import
If a test file uses `pytest` fixtures via conftest.py autouse or doesn't use `pytest.mark`/`pytest.raises`, the import is flagged as unused. Remove it:
```python
# ❌ WRONG — pytest imported but not used
import pytest

# ✅ CORRECT — only import what you use
from pathlib import Path
from app.services.cleanup_service import CleanupService
```

### Adding new API endpoints for project sub-resources
Pattern for adding endpoints to `app/api/routes/projects.py`:
1. Import any new deps at the top (e.g., `get_config` from `app.api.deps`)
2. Lazy-import heavy services inside the endpoint function (e.g., `from app.workflow.scene_chunking_service import SceneChunkingService`)
3. Use `pwf.get_project(project_id)` to validate project exists, wrap in try/except
4. Use `pwf._project_dir(project_id)` for filesystem paths
5. Use `pwf._save_project(project_id, proj)` to persist changes
6. Return dicts with `model_dump()` for Pydantic models

### TanStack Query + Zustand integration for feature modules
Pattern for adding server-backed features alongside existing Zustand state:
- **Server state** (list of items from API): use TanStack Query with `queryKey: ["feature", projectId]`
- **Client state** (selected item, UI toggles): add to Zustand store (`activeSceneId`, `setActiveSceneId`)
- **Mutations**: use `useMutation` + `queryClient.invalidateQueries({ queryKey: ["feature", projectId] })` on success
- **Auto-advance**: after approving/selecting an item, find the next unprocessed item and auto-select it
- Import the data type from `api.ts` into the Zustand store for type consistency

### Pattern: "Run detection, show results" UI (auto-segment pattern)
When adding a feature that runs a detection/analysis API call and shows results as a selectable list:
1. **State**: `const [results, setResults] = useState<Array<{...}>>([])` + `const [isLoading, setIsLoading] = useState(false)`
2. **Handler**: `setIsLoading(true)` → `await api.detectSomething(projectId)` → `setResults(result.objects)` → `finally setIsLoading(false)`
3. **Button**: Purple accent, disabled while loading, Vietnamese label with 🪄 emoji
4. **Results list**: `max-h-40 overflow-y-auto`, each item is a clickable `<button>` that sets selection/focus on click
5. **Error handling**: `alert(\`Lỗi: ${(err as Error).message}\`)` — Vietnamese error prefix
Used in ScreenB for auto-segment objects (`autoSegmentObjects` API → scrollable list of detected objects with bbox dimensions).

### Pattern: Auto-crop thumbnail for tracked objects (CRITICAL for object cards)
Every `TrackedObject` should have a cropped thumbnail so UI object cards show the actual detected character/prop instead of an empty box. Implement in three layers:

1. **Schema**: `TrackedObject.crop_path: str | None = None`
2. **Backend helper** (`_auto_crop_object` in `projects.py`) — crop from the frame at selection coordinates, save to `projects/{id}/objects/{oid}/crop.png`:
```python
def _auto_crop_object(proj_dir, object_id, selection, pad=10):
    # find frame via find_frame_path(scene_dir, selection.frame_index)
    # bbox mode: frame[y:y+h, x:x+w] with pad; point mode: 160×160 window centered
    # clamp to frame bounds; cv2.imwrite(crop_file, crop_img)
```
   - Call it in `create_object` right before `pwf.add_tracked_object`, assign `obj.crop_path`
3. **GET endpoint with auto-generate fallback** — serve the crop, generate on demand if missing:
```python
@router.get("/{project_id}/objects/{object_id}/crop")
@router.get("/{project_id}/objects/{object_id}/crop/")
def get_object_crop(project_id, object_id) -> FileResponse:
    crop_file = proj_dir / "objects" / object_id / "crop.png"
    if not crop_file.exists():
        generated = _auto_crop_object(proj_dir, object_id, obj.selection)
    return FileResponse(str(crop_file), media_type="image/png")
```
4. **Frontend**: `getObjectCropUrl(projectId, objectId)` in `api.ts`; in object-card `<img>` use `onError` → fallback to `thumbnail_base64` (data URL from `GET /objects`) then hide:
```tsx
<img
  src={api.getObjectCropUrl(projectId, obj.object_id)}
  className="w-12 h-12 object-contain bg-black/80 rounded border border-purple-500/50"
  onError={(e) => {
    const el = e.target as HTMLImageElement;
    if (obj.thumbnail_base64) { el.src = obj.thumbnail_base64; el.onerror = null; }
    else { el.style.display = "none"; }
  }}
/>
```
- `GET /objects` (`list_objects`) attaches `thumbnail_base64` to each object's `model_dump()` so the UI has a data-URL fallback without an extra request
- Frontend `TrackedObject` interface needs `thumbnail_base64?: string` added to stay type-safe

### Pattern: Distinct object names (avoid duplicate labels)
When auto-detecting or auto-creating objects, give each a unique human-readable name so cards/lists don't show identical "Test Object" entries:
```python
# auto_segment_objects — name by size + position
center_dist = abs(cx - w / 2) + abs(cy - h / 2)
is_character = full_area > (w * h * 0.05) and center_dist < (w * 0.4)
label = "Nhân vật" if is_character else "Vật thể"
name = f"{label} #{len(objects) + 1} ({full_w}×{full_h}px)"
```
- `create_object`: if the client name is empty or a generic placeholder (`test`, `object`, `vật thể`, `nhân vật`), auto-generate `Vật thể #{existing_count + 1} ({sw}×{sh}px)` from selection size
- Include the pixel dimensions in the name — it doubles as a size hint in the UI and guarantees uniqueness across objects

### Pattern: Inline crop base64 in auto-segment response
When auto-segment returns detected objects, embed the cropped thumbnail directly in the JSON so the UI can render cards without a second request per object:
```python
# inside auto_segment_objects loop, after computing full_x/full_y/full_w/full_h
crop_png_base64 = ""
try:
    crop_img = img[full_y : full_y + full_h, full_x : full_x + full_w]
    if crop_img.size > 0:
        _, buf = cv2.imencode(".png", crop_img)
        crop_png_base64 = base64.b64encode(buf).decode("utf-8")
except Exception:
    crop_png_base64 = ""
# add "crop_png_base64": crop_png_base64 to the object dict
```
- `import base64` at top of projects.py (alongside shutil/uuid)
- Frontend type: `crop_png_base64?: string` in the autoSegmentObjects objects array; render `<img src={`data:image/png;base64,${obj.crop_png_base64}`} className="w-14 h-14 object-contain bg-black/80 rounded border border-purple-500/50" />`
- Test: decode and assert PNG magic bytes `raw[:8] == b"\x89PNG\r\n\x1a\n"` — proves a valid image, not empty string

### Pattern: Clear-all objects endpoint (DELETE /objects)
To reset a project's tracked objects (e.g., a "🗑️ Xóa Tất Cả Nhân Vật Cũ" button):
```python
@router.delete("/{project_id}/objects")
@router.delete("/{project_id}/objects/")
def clear_objects(project_id: str) -> dict:
    proj = pwf.get_project(project_id)
    proj.objects = []
    pwf._save_project(project_id, proj)
    # also rmtree each child dir under proj_dir/"objects"
    return {"status": "ok", "message": "Cleared all objects"}
```
- Frontend handler: `confirm(...)` → `api.clearObjects(projectId)` → `api.getProject(projectId)` → `setProject(updated)` + `setActiveObject(null)` + clear any auto-detect list state. Reloading the project from the API is the reliable way to reset `project.objects` in the Zustand store — don't try to mutate the array in place.

### Pattern: Preview-before-upload with side-by-side comparison modal
When uploading a replacement image (or any file that replaces existing content), the BA/PM flow requires **Xem trước → Đối chiếu → Xác nhận** — NEVER upload immediately on file select. Implementation:

1. **State**: `pendingFile: File | null` + `pendingPreview: string | null` (object URL)
2. **handleFileChange**: store file + `URL.createObjectURL(file)` — do NOT call upload. Reset `e.target.value = ""` so re-selecting the same file re-triggers.
3. **Modal**: `fixed inset-0 z-50 bg-black/70 backdrop-blur-sm`, `max-w-3xl`, two `grid grid-cols-2` columns:
   - Left = original crop (`api.getObjectCropUrl(projectId, objectId)` with `object-contain`)
   - Right = new file preview (`<img src={pendingPreview}>`) + filename
4. **Actions**:
   - Hủy: `URL.revokeObjectURL(pendingPreview)` + clear both states
   - Xác Nhận Thay Thế: `uploadMut.mutate(pendingFile)` with `disabled={uploadMut.isPending}` and label switching to "Đang tải lên..."
   - `onSuccess` of the mutation clears both states (auto-closes modal)
5. **Accept**: `accept="image/*,.png,.jpg,.jpeg,.webp"` (NOT just `.png`) — user explicitly complained that restricting to PNG hid valid JPG/WebP files.
6. **Images**: `aspect-square` frame + `object-contain` so aspect ratio is preserved, never distorted.
7. Clicking the modal backdrop should cancel (but `stopPropagation` on the inner card so card clicks don't close).

### Pattern: Auto-detected object card with 1-click select
Each auto-segment result card should be a `<div>` (not a `<button>`) containing the crop `<img>`, the distinct name, and a nested green action button — nested interactive elements inside a `<button>` are invalid HTML:
```tsx
<div key={obj.object_index} className="w-full ... bg-gray-800/80 border ... rounded-lg">
  <div className="flex items-center gap-2">
    {obj.crop_png_base64 && <img src={`data:image/png;base64,${obj.crop_png_base64}`} ... />}
    <div className="min-w-0 flex-1">
      <p>🎯 {obj.name ?? `Vật thể #${obj.object_index + 1}`}</p>
      <p>Kích thước {obj.bbox.width}×{obj.bbox.height}px</p>
    </div>
  </div>
  <button onClick={() => { setSelection({mode:"bounding_box", ...obj.bbox}); previewMut.mutate(); }}
    className="mt-2 w-full py-1.5 text-[11px] bg-green-600 ...">
    ✅ Chọn Nhân Vật Này
  </button>
</div>
```
- The "✅ Chọn" button sets the bbox selection AND triggers mask preview in one click
- Keep the crop image at `w-14 h-14` (slightly larger than the w-12 used in ScreenD object cards)

### Pattern: Synthetic-frame test for detection endpoints
When unit-testing contour-detection / crop endpoints without real video fixtures, write a synthetic frame directly into the isolated test project root:
```python
from app.api import deps
proj_root = deps._config.project_root
frame_dir = proj_root / "projects" / pid / "frames" / "scene_0"
frame_dir.mkdir(parents=True, exist_ok=True)
frame = np.full((300, 400, 3), 255, dtype=np.uint8)  # WHITE bg, dark objects
frame[50:200, 50:150] = (0, 0, 0)   # object 1
frame[80:130, 250:350] = (0, 0, 0)  # object 2
cv2.imwrite(str(frame_dir / "frame_000000.png"), frame)
```
- **Use WHITE background + dark objects** — `THRESH_BINARY_INV + THRESH_OTSU` on a black background produces ONE contour covering the whole frame (test asserts `len >= 2` fail). White bg isolates each dark object as its own contour.
- Always use `deps._config.project_root` (patched tmp root), never the real `config.project_root` singleton.

### Pattern: Delete project button (cross-component)
Reusable delete pattern for project cards in ScreenA, ChannelDashboard, etc.:
```tsx
<button
  onClick={async () => {
    if (!confirm(`Xóa dự án "${proj.name}"? ...`)) return;
    try {
      await api.deleteProject(proj.project_id);
      // ScreenA: refetchProjects() (TanStack Query refetch)
      // ChannelDashboard: queryClient.invalidateQueries({ queryKey: [...] })
    } catch (err) {
      alert(`Lỗi: ${(err as Error).message}`);
    }
  }}
  className="px-2 py-1 text-[10px] bg-red-900/50 hover:bg-red-800 rounded text-red-300"
>
  🗑️
</button>
```
- Always wrap in `confirm()` with Vietnamese warning message
- Use `bg-red-900/50 hover:bg-red-800` for dark theme consistency
- Invalidate/refetch the appropriate query after deletion

### Pattern: Extending `api.ts` with new domain endpoints
When adding a new domain (e.g., channels, dubbing, presets) to `api.ts`:
1. **Types first**: Add TypeScript interfaces above the `api` object (after existing interfaces, before `// ─── API Functions`)
2. **Methods in `api` object**: Add new methods grouped under a `// ─── DomainName ───` comment
3. **Naming**: Use verb-noun pattern — `createChannel`, `listChannels`, `getChannelProjects`, `deleteChannel`
4. **Mutations**: Return `{ ok: boolean }` for DELETE/PATCH mutations
5. **Path params**: Use template literals: `` `/api/projects/channels/${channelId}` ``
6. **Query params**: Inline in URL: `` `?channel_id=${channelId}` ``
7. **POST/PATCH bodies**: Use `JSON.stringify()` with explicit `Content-Type: application/json` header
8. **Types must be exported** so components can import them: `import { type ChannelWorkspace, type ChannelProject } from "@/lib/api"`

### Pattern: Accessing Zustand store outside React context
When passing callbacks to non-React contexts (e.g., `onResumeProject` prop, event handlers outside components), use `useProjectStore.getState()`:
```tsx
onResumeProject={(pid) => {
  const store = useProjectStore.getState();
  store.setProjectId(pid);
  api.getProject(pid).then((proj) => {
    store.setProject(proj);
    store.setScreen("selection");
  });
}}
```
This avoids stale closures. Inside React render/hook context, use the selector pattern: `useProjectStore((s) => s.setProjectId)`.

### Frontend poll timeout for long-running backend jobs
When the frontend polls a backend job (ingest, propagate, render), the poll timeout must be proportional to the expected job duration. A fixed 90-second timeout causes "Quá trình xử lý bị quá thời gian" (timeout error) for longer videos.
- **Ingest** (scene detect + frame extract + audio): 300s for a 10-minute video
- **Propagation** (SAM2): 600s for 180+ frames
- **Render**: 300s for final composite
- Set `maxAttempts` in the poll loop, not a separate timeout.
- **Fast polling (300ms)**: `const maxAttempts = 1000; for (let i = 0; i < maxAttempts; i++) { await sleep(300); ... }` — gives 300s total with better responsiveness
- **Standard polling (1s)**: `const maxAttempts = 300; for (let i = 0; i < maxAttempts; i++) { await sleep(1000); ... }` — gives 300s total
- Prefer 300ms polling for UX-sensitive jobs (ingest) where progress messages change frequently; use 1s for background jobs where responsiveness matters less
- Frontend error message should be in Vietnamese: `"Quá trình xử lý bị quá thời gian. Vui lòng thử lại."`

### On-Demand Video Chunking Architecture (BA/PM validated)
When ingest is too slow for long videos (10+ minutes), the root cause is extracting ALL frames at upload time. The fix is NOT to increase timeouts — it's to change the architecture:

**Old pattern (broken for long videos):**
```
Upload → Probe → Detect scenes → Extract ALL frames → Done (2-5 min)
```

**New pattern (3-5 seconds for any video length):**
```
Upload → Probe → Detect scenes → Slice scene clips (FFmpeg -c copy) → Done (3-5s)
User selects scene → Extract frames on-demand (~0.2-1s per scene)
```

Implementation:
1. **`scene_chunking_service.py`**: Add `slice_scene_videos()` using FFmpeg `-c copy` (stream copy, no re-encode, instant)
2. **`scene_chunking_service.py`**: Add `extract_frames_on_demand()` that extracts from a single scene clip, with caching (check if frames already exist)
3. **`ingest_service.py`**: Remove the frame extraction loop entirely. Ingest = probe + detect + slice + audio only.
4. **`project_service.py`**: Add `set_scene_details()` that sets both `scene_details` and backward-compatible `scenes`
5. **API**: Add `POST /scenes/{id}/extract-frames` endpoint for on-demand extraction
6. **Frontend**: Add `extractSceneFrames()` to api.ts, call when user selects a scene

File structure:
```
projects/{id}/
├── scenes/          ← scene clips (stream copy, ~1MB each)
│   ├── scene_000.mp4
│   └── scene_001.mp4
├── audio/           ← per-scene audio (codec copy)
├── frames/          ← extracted on-demand per scene
│   └── scene_0/
└── renders/
```

**BA/PM feedback**: "Việc cố giải nén hàng chục nghìn frame của toàn bộ video ngay từ lúc ingest là SAI BẢN CHẤT KIẾN TRÚC" — this is the authoritative validation that on-demand is correct.

### Frame format change requires full-stack update
When changing frame extraction format (e.g., PNG→JPG for 10x speedup), the change cascades through the entire stack:
1. `frame_extraction.py`: change default `format` parameter
2. `projects.py` API: update `get_frame` to try multiple extensions (use `find_frame_path` helper)
3. `projects.py` API: update `preview_mask` frame lookup
4. `projects.py` API: update `propagate` frame lookup
5. `projects.py` API: update `object_extraction` frame lookup
6. `projects.py` API: update `media_type` in FileResponse (image/jpeg vs image/png)
7. Any existing projects with old-format frames still need to work (backward compatible)
Use a `find_frame_path(scene_dir, frame_index)` helper in `app/api/helpers.py` that tries `jpg/jpeg/png` in order.

### FastAPI trailing slash 405 on POST/DELETE (CRITICAL)
FastAPI default `redirect_slashes=True` redirects `DELETE /api/projects/abc/` → `GET /api/projects/abc` (301), changing method to GET → 405. This affects ALL POST/DELETE endpoints when the frontend or browser appends a trailing slash.

**Fix (two parts):**
1. `app/api/app.py`: `FastAPI(redirect_slashes=False)`
2. Add trailing slash aliases for all DELETE/POST endpoints:
```python
@router.delete("/{project_id}")
@router.delete("/{project_id}/")   # ← alias
def delete_project(project_id: str) -> dict: ...
```

**Test pattern:** `tests/test_trailing_slash.py` — test both `/path` and `/path/` return correct status (not 405).

**When to add aliases:** Only for endpoints called directly by frontend (DELETE, POST mutations). GET endpoints rarely need aliases.

### FastAPI Pydantic wrapper-field mismatch → 422 (CRITICAL)
When the backend request model wraps fields in a named container (e.g., `ReplacementSettingsRequest` has `replacement_config: ReplacementConfig`), the frontend MUST send the nested object:
```python
# backend
class ReplacementSettingsRequest(BaseModel):
    replacement_config: ReplacementConfig
```
```ts
// frontend api.ts — WRONG → 422 Unprocessable Entity (detail: "replacement_config: Field required")
body: JSON.stringify(settings)
// CORRECT — wrap in the container field
body: JSON.stringify({ replacement_config: settings })
```
**Symptom**: `PATCH .../replacement-settings` → 422 with `"loc":["body","replacement_config"],"msg":"Field required"` in the response detail. The button click "does nothing" (mutation errors swallowed). **Always check the request-model schema when a mutation silently 422s** — grep the route's body param type, then compare the frontend payload shape. The 422 detail JSON tells you exactly which field is missing.

### Hardcoded API port in components (CRITICAL)
Never hardcode `http://localhost:8000` in frontend components — MotionForge runs on port **8002** (port 8000 is a zombie from another project). Hardcoded URLs silently 404 the image/asset and the UI "shows nothing" after a successful upload.
```ts
// ❌ WRONG — replacementUrl never resolves (404 on :8000)
const replacementUrl = `http://localhost:8000${replacement.asset_path}`;
// ✅ CORRECT — always via api.ts helpers that use API_BASE
const replacementUrl = api.getReplacementImageUrl(projectId, objectId);
```
**Lesson**: grep for `localhost:8000` in `frontend/src/` after any feature touches asset URLs. Any URL built outside `api.ts` is suspect.

### Static routes must be declared BEFORE /{project_id} paths
FastAPI matches routes in definition order. A static path like `/gpu-info` declared AFTER `/{project_id}` is captured as a project_id → 404 (or 405 for the wrong method). When the frontend calls `GET /api/projects/gpu-info` and gets 404 while the route clearly exists at line 1600+, the route is shadowed. Move the static route above the parameterized ones (right after `list_all_projects`), or the frontend will keep hitting 404. Also check the helper's return type: `detect_nvenc()` returns an `EncoderInfo` **dataclass** (fields `has_nvenc`, `gpu_name`, `encoder_name`), not a dict — use attribute access.

### Router prefix + route path segments (CRITICAL — 404 despite correct ordering)
`projects.router` has `prefix="/api/projects"`. Three separate traps combine to cause 404s that look like ordering bugs but are NOT:

1. **Full URL = prefix + route path.** `@router.get("/presets/characters")` → URL `/api/projects/presets/characters` (NOT `/api/presets/characters`). If a test or frontend calls `/api/presets/characters`, it 404s even though the route "exists". **Always compute the full URL when writing tests/client calls** — grep the router prefix first (`projects.router.prefix` prints it).

2. **Route path must include ALL path params.** `@router.post("/presets/characters/{set_key}/{pose}/apply")` with a function signature `(project_id, set_key, pose)` NEVER matches `/api/projects/xxx/presets/...` because `xxx` has no placeholder in the path. The route must be `@router.post("/{project_id}/presets/characters/{set_key}/{pose}/apply")` to capture project_id. Symptom: direct TestClient call to the full URL → 404 with `{"detail":"Not Found"}` while `projects.router.routes` clearly lists the route.

3. **Verify actual registered routes**, don't trust the source: `python -c "from app.api.routes import projects; [print(r.path, r.methods) for r in projects.router.routes]"` — this shows the true matched paths including prefix expansion and any shadowing.

**Diagnosis recipe for "route exists but 404":** (a) check prefix, (b) verify the full URL string matches prefix+path exactly, (c) check every `{param}` in the function signature has a placeholder in the path, (d) print `router.routes` to see the real registration order.

### Pattern: Debounced auto-save of transform sliders (persist-before-apply)
When transform sliders (scale/rotation/offset) should persist to the backend as the user drags — and "Áp dụng" then broadcasts the canonical config — use a debounced `useEffect` over `settingsMut.mutate()` instead of saving on every `onChange`:

```tsx
const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
useEffect(() => {
  if (!projectId || !objectId) return;
  if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
  saveTimerRef.current = setTimeout(() => { settingsMut.mutate(); }, 500);
  return () => { if (saveTimerRef.current) clearTimeout(saveTimerRef.current); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, [replacement.scale, replacement.rotation_offset_deg,
    replacement.offset.x, replacement.offset.y, replacement.opacity,
    projectId, objectId]);
```
- Dependency list = the exact slider-bound fields; the mutation closure reads `replacement` fresh each run
- 500ms debounce: last drag position wins, no request spam during a drag
- The effect MUST be declared AFTER `settingsMut` (see "useEffect before variable declaration" pitfall)
- Add `useRef` to the React import when adding this pattern to a component that lacks it

### Pattern: Multi-pose character preset library (backend assets + AI pose choice)
When the BA asks for a "library of template characters" the user can drop into the canvas:
1. **Asset generation**: don't ship binary PNGs — generate them at runtime with OpenCV if absent (`ensure_assets()` + `_generate_asset`), transparent via 4-channel canvas + alpha mask from the drawn silhouette. Wide canvas for sitting, tall for standing/walking.
2. **Serve + apply routes** (remember router prefix + path segment rules):
   - `GET /{project_id}/presets/characters` — list sets/poses (can be static, declared early)
   - `GET /{project_id}/presets/characters/{set}/{pose}/image` — FileResponse PNG
   - `POST /{project_id}/presets/characters/{set}/{pose}/apply` — copies asset into `objects/{oid}/replacement.png`, sets `replacement_config.mode="static_asset"` + `asset_path`, `_save_project`
3. **Pose choice by bbox aspect ratio** (the "AI" heuristic):
```python
if width <= 0 or height <= 0: return "talking"
if width > height * 1.1: return "sitting"    # wide → lying/sitting
if height > width * 1.3: return "standing"   # tall → standing/walking
return "talking"                              # balanced
```
4. **auto_match_character extension**: after computing source_bbox, call the pose heuristic, copy the chosen pose PNG + replacement config to every other-scene object, and include `"pose"` in the response.
5. **Frontend**: collapsible panel (3 sets × 4 poses as image buttons); apply mutation updates `replacement` + banner so canvas redraws immediately.

### Pattern: Browser image cache-busting for replaced assets
When the same URL (`GET /objects/{id}/replacement-image`) serves a NEW image after re-upload, the browser serves the cached OLD one. Fix in the URL consumer:
```ts
const replacementUrl =
  projectId && objectId && replacement.asset_path
    ? `${api.getReplacementImageUrl(projectId, objectId)}?t=${Date.now()}&v=${encodeURIComponent(replacement.asset_path)}`
    : null;
```
- `t=Date.now()` forces a fresh fetch every mount; `v=asset_path` changes per upload (content-addressed invalidation)
- Same pattern applies to any endpoint whose file changes under a stable URL (masks, inpainted frames, crops)
- Backend log showing the frontend already sending `?t=...` while the server 404s = the server predates the endpoint (restart it, don't re-debug the frontend)

### Patch-tool helper insertion can orphan the next function's docstring
When inserting a new helper method (`_make_object_with_mask`) directly ABOVE an existing test method via the patch tool, the match can land INSIDE the old_string boundary and leave the following method's docstring stranded above a wrong `def` (or remove its first lines). Symptoms: `def test_delete_single_object` followed by a docstring that belongs to it but appears under a different method; `AttributeError: ... has no attribute '_make_project'` when a new test calls a helper that was never created.
- After any helper insertion, re-read the region and check: (1) the new helper's body is complete, (2) the NEXT method's `def` + docstring are intact and adjacent
- When a new test references a helper, grep the file first to confirm it exists — don't assume the patch created it
- If the file got mangled, restore from git (`git checkout HEAD -- file`) and re-apply changes in smaller patches with unique context

### read_file truncation on long lines / write_file byte mismatch
`read_file` returns `LINE|content`; lines are truncated at ~100 chars with `...[truncated]`. Building an edit script from read_file output and writing it back via `write_file` **loses the truncated content** (the script writes the truncated text, not the original). This silently corrupts files. If you must transform via script: use Python `open().read()` directly in the script (via `terminal`/`execute_code`) instead of read_file → write_file round-trips. Also note: editing a Python file by string-replacing only the long lines leaves the file's total line count/indentation consistent ONLY if every replaced block is balanced — verify with `python -c "import ast; ast.parse(open(f).read())"` after bulk string edits, and `git diff --stat` to confirm nothing beyond the intended block changed.

### cv2.imwrite cannot write to BytesIO
`cv2.imwrite(buf, img)` with a `BytesIO` raises `error: (-5:Bad argument) ... Expected 'filename' to be a str or path-like object`. In tests that build an in-memory PNG for upload, use `cv2.imencode`:
```python
ok, enc = cv2.imencode(".png", np.full((64, 64, 3), 200, dtype=np.uint8))
png_bytes = enc.tobytes()
client.post(url, files={"file": ("char.png", png_bytes, "image/png")})
```

### STALE BACKEND PROCESS = 405 / missing features (CRITICAL)
**The #1 cause of "nút không chạy" / 405 / feature-missing after a fix is a STALE backend process.** Background uvicorn started via `terminal(background=true)` does NOT hot-reload. When you commit a fix (e.g., the trailing-slash 405 fix), the running backend still serves the OLD code.

**Diagnosis — check the process start time vs the fix commit:**
```bash
# 1. Is the backend running OLD code? Check process uptime:
process(action='list')   # started_at earlier than your commit = stale
# 2. Confirm the symptom in backend log:
#    "DELETE /api/projects/xxx HTTP/1.1 405 Method Not Allowed" ← old code
# 3. Verify current code actually has the fix (grep the source)
```

**Fix — always restart backend after code changes:**
```bash
process(action='kill', session_id=<old_backend_sid>)
# Then start fresh:
export PATH="$PATH:/c/Users/Admin/AppData/Local/Microsoft/WinGet/Links"
cd C:/Users/Admin/MotionForge2D
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

**Lesson:** When the user reports an error that the code already appears to fix, FIRST check whether the running server predates the fix. Restart, then verify with a live curl — don't immediately re-debug the code.

### list_all_projects: no hard cap, sort real projects first
`GET /api/projects` (list_all_projects) must NOT cap results (e.g., `if len(results) >= 30: break`) and must sort by `scenes_count` desc (real projects) before mtime. A cap + mtime-only sort lets dozens of junk "Test"/"Clip Test" projects (created seconds ago by test suites) push the user's real multi-scene project OUT of the visible list — user thinks their project was DELETED.

```python
def _sort_key(p):
    try:
        data = json.loads((p / "project.json").read_text(encoding="utf-8"))
        return (len(data.get("scenes", [])), p.stat().st_mtime)
    except Exception:
        return (0, 0)
dirs.sort(key=_sort_key, reverse=True)  # no cap in the loop
```

### Junk project accumulation from test suites
Pytest/E2E test runs create MANY real on-disk projects named "Clip Test", "Test", "E2E Test", "Debug" (test fixtures write to the actual projects/ dir unless project_root is patched). Over time these can reach 1000+ projects and gigabytes. When the user asks to clean up:
1. **List + count first** — categorize by `name` from `project.json` (Counter)
2. **Never delete real projects** — identify by name (Dự án MotionForge) or scenes_count > 1
3. **Purge via Python script** — `shutil.rmtree(d)` for each junk dir (faster than API DELETE for hundreds)
4. **Verify** — `ls projects/` shows only real dirs; API returns only real projects
5. **Test isolation root cause**: new test files must use the `_patch_project_root` fixture (see below) so tests never write to the real projects/ dir

### Next.js `.next` cache corruption
When the browser shows `Cannot find module '@file:\`tanstack/react-query\``' or similar corrupted import paths, the `.next` build cache is corrupted. This happens after subagents modify source files while the dev server is running — Turbopack's incremental compilation produces stale/corrupted chunk files.

**Fix:**
```bash
cd frontend
rm -rf .next
# Kill old dev server process
# Restart: npm run dev
```

**Diagnosis:** The corrupted path `@file:\`...\`` is NOT in any source file — it's only in `.next/dev/static/chunks/`. Source code is correct; the build cache is wrong.

**Prevention:** After any subagent modifies frontend files while the dev server is running, clear `.next` and restart the dev server before testing in the browser.

### State rehydration on F5 / app reopen
When the user F5s or reopens the app, all Zustand state is lost. The fix uses localStorage + API rehydration:
1. **`useProjectRehydration` hook** reads `motionforge_session` from localStorage on mount
2. Calls `GET /api/projects/{id}` to restore full project state
3. Sets Zustand store (projectId, project, screen, activeSceneId) from saved session
4. Shows "Đang khôi phục phiên làm việc..." loading state while rehydrating
5. Session expires after 7 days
6. `saveSession()` called on every projectId/screen/activeSceneId change
7. `clearSession()` called when project is cleared

Recent projects list on ScreenA uses `GET /api/projects` (list all) with TanStack Query.
"▶️ Tiếp tục" button determines target screen based on task_status and project state.

See `references/state-rehydration-persistence.md` for full implementation details.