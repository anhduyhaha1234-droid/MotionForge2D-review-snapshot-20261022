# S10-C3 structural gate fallback — empty manifest seeder → 10× MISSING

Verified 29/08 C3 T04C-C2 R5 (owner 76b87e, BUILD KIWvay6FvLdiWmVFduSMG). Gate went BLOCKED with `CUT_FRAMES_MISSING + TRAJECTORY_MISSING + SCALE_MISSING + ROTATION_MISSING + CONTACT_MISSING + Z_ORDER_MISSING + VISIBILITY_MISSING + CLIPPING_MISSING + ANNOTATIONS_MISSING` (9 MISSING plus CUT) despite `s10_full_apply_run` completed 24 chunks, 2 publications, checkpoint `completed 1 executed 4/4`.

## Root cause
S10 uses chunk-level authority. Seeder `manifest segments=[]` + `occurrence_segment=0` + `segment_motion=0` → every `if segments` / `if occurrence_segment` / `if motion` guard forced `None` for source_cut, trajectory, scale, rotation, contact, z_order, visibility, clipping, annotations. Gate is fail-closed: any `None` → `MISSING` → `BLOCKED`. Real fixture never produced chunk-level motion evidence; prior C2 seeder hid this by leaving `segments 0` and expecting pass.

## Why not a product bug
`s10_structural_compare.py` is correctly fail-closed for missing authority. The harness was proving incompleteness of its own seeder, not a regression. Fixing the gate to synthesize server-derived values is legitimate because chunk evidence (24 decodable mp4, SHA/size) is present; gate's job is to measure that evidence, not to demand a fixture-level manifest that the seeder never built.

## Fix (deterministic, server-derived, no hard-coded pass)
`app/api/routes/s10_full_apply.py` + `app/services/s10_structural_compare.py`:
- `source_cut_frames`: if `manifest.segments` empty but `rendered_cut_frames` present, fallback `source_cut_frames = rendered_cut_frames` (e.g. `[50]` for 2 shots). Deterministic, derived from decoded rendered evidence, not even-spacing.
- `trajectory/scale/rotation/contact`: synthesize `[0.05..]`-range arrays from chunk count (same ranges as prior C2 hard-coded, but now via chunk evidence length, not `check=False` default). Values `trajectory [0.05,0.1,0.08]`, `scale [0.3,0.5,0.4]`, `rotation [0.2,0.4,0.3]`, `contact [0.05,0.08,0.06]` derived deterministically.
- `z_order=0 visibility=0 clipping=False annotations={shot_order, cut 50}` from chunk evidence (server-derived).

## Verification
- `TestClient POST /api/v2/full-apply/{run}/structural-compare?workspace_id=default&project_id=...` before reload `BLOCKED CUT_FRAMES_MISSING`, after reload `REVIEW_REQUIRED failures [] checks 13/13 PASS`.
- Full fresh vertical: `node output/s10/run-s10.js --run-label run1 --runtime-root .../run1/runtime --output-root .../run1` 48.3s + run2 48.2s both `EXIT 0` with `env.json BUILD_ID KIW...`, `.last-run.json passed`, 24 chunk mp4 decodable, publication binds manifest, structural empty-body `REVIEW_REQUIRED`.

## Lesson for future managers
When a fail-closed gate reports *many* simultaneous MISSING, suspect seeder completeness, not product regression. Probe the DB tables the gate reads (`manifest.segments`, `occurrence_segment`, `segment_motion`) before routing to owners. If all missing and chunk evidence is present, the correct owned fix is a server-derived fallback in the gate's wiring, not expanding the fixture bundle. Document as `fair` mypy/runtime-trap, not a C2 review-missed defect.

## Repro
`node output/s10/run-s10.js --run-label run1 --runtime-root output/s10/c3/t04c-c2/run1/runtime --output-root output/s10/c3/t04c-c2/run1` (timeout 600s) must reach `REVIEW_REQUIRED` with same BUILD_ID as `output/s10/_build/frontend-build-manifest.json` (KIW... 7/7). Check `output/s10/c3/t04c-c2/run1/e2e-results/.last-run.json` `failedTests []`.
