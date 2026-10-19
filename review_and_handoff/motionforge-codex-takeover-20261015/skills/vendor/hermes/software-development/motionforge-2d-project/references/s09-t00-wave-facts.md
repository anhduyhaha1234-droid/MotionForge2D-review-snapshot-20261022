# S09 T00 implementation wave — verified facts & recipes (2026-08-23)

Session-specific detail backing the manager-liveness reference. Facts below were all
manager-verified on disk (never trusted from worker reports).

## Schema state after S09-T00-I01 (MANAGER_VERIFIED)
- Alembic single head: `d8e9f0a1b2c3` (down_revision `c9d0e1f2a3b4`, which sits on `b2c3d4e5f6a7b`).
- New tables: `structural_lock_manifest`, `segment_render_route`.
  - Route enum CHECK: `{pose_swap,sprite_affine,mesh_warp,part_rig,controlled_redraw}` — single authority constant `RENDERER_ROUTES` / `RENDERER_ROUTE_CHECK_SQL` in models.py.
  - Anchors normalized x/y ∈ [0,1] CHECK-bound; NaN binds as NULL in SQLite so finiteness is enforced repo-side (repository rejects non-finite).
  - Natural keys: manifest UNIQUE(workspace_id, project_id, video_item_id, source_generation, version); route UNIQUE(occurrence_segment_id, route, start_frame). Workspace-scoped idempotency UNIQUE(workspace_id, idempotency_key) WHERE NOT NULL on both.
  - Supersede lineage: status draft→active→superseded/voided; `superseded_by_id` FK RESTRICT self-ref + no-self-link CHECK.
  - Pins: additive columns `structural_lock_manifest_id` (FK RESTRICT) + `lock_policy_version` on ReskinConfig AND ApplyCheckpoint.
- models.py additive-only proven vs baseline copy `output/s09/20260823_sprint_full/t00-i01/models_baseline_eaf8a484.py`: difflib removed-lines = 0 (308 added).
- ORM classes: `app/persistence/models.py` ~line 2318 (`StructuralLockManifest`), ~2445 (`SegmentRenderRoute`); repo `app/persistence/structural_lock.py`; schemas `app/schemas/structural_lock.py`. PK default is `_new_id()` (uuid4) — rows created WITHOUT explicit id get it at flush; assigning `row.id` before flush yields None (bit a worker test once).

## I04 normalization pattern (cross-sprint migration-head tests)
- Six regression files converted from hard-coded head to live discovery via `ScriptDirectory.get_heads()`; expected-tables set extended additively with the new S09 tables while keeping the unexpected-tables assertion adversarial (planted fake table must still FAIL).
- Adversarial proof script pattern (`t00-i04/adversarial_proof.py`): plant fake table → assertion fails with message listing it; plant fake revision in alembic_version → head-equality assertion fails; clean DB passes. Windows gotcha: dispose the SQLAlchemy engine BEFORE `shutil.rmtree(work)` or the temp dir cleanup hits PermissionError (handle-and-warn, proofs already captured).

## Renderer/router environment facts (lane-B/C audits + I02)
- FFmpeg 8.1.2 present; h264_nvenc WORKS on RTX 5070 (SM 12.0) but NVENC rejects probe frames below min dimension (~145px) — probe with `nullsrc=s=256x256:d=0.2:r=10`, exit 127/-22 at 64×64 is a PROBE bug not missing encoder.
- SAM-2 Apache-2.0 available info-wise; Cutie MISSING (import ValueError). No model downloads without user authority — adapters fail closed when binaries absent.
- Lane-C measured numbers usable as reference: timebase roundtrip 240/240 mismatch=0; centroid residual median 1.75px / P95 22.15px (bbox-affine NOT fidelity-sufficient); cost 0.90ms/frame.

## Benchmark harness contract (I03)
- Freeze BEFORE measuring: print schema_version=1 + content SHA256 over (harness source + fixture set + thresholds) before first measured run; every result cites the frozen SHA.
- Metric fields include trajectory_median_pct (accidentally dropped by a worker patch once — restored), annotated_swaps, pose_states_measured; same-seed runs byte-compare identical except wall-runtime/VRAM fields.
- Golden fixtures are ffmpeg-synthetic (testsrc/smptebars/gradients) covering 6 risk classes: hard cut, mouth/expression, phone contact, whole-body rotation/bed contact, group occlusion, semantic graphic replacement. Verified-reference fixture SHA 5A175454… was NOT on disk → SKIP_WITH_REASON path, never fake pass.

## Wave timeline (for ETA calibration)
- 12:05 dispatch Wave 1 (I01∥I04) → both died early/odd (~14:20) → correction-r1 resume → both TASK_SUBMITTED + MANAGER_VERIFIED by 17:45. Wave 2 (I02∥I03) dispatched 17:50 → simultaneous silent death #1 ~19:45 → R1 resume → silent death #2 ~21:00 → R2 resume. Overnight waves on this machine should budget ≥2 revival cycles per parallel pair.
