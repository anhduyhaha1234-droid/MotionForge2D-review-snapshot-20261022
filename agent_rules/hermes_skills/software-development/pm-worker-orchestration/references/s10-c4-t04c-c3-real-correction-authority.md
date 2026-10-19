# S10-C4A T04C-C3 — real-correction authority phase (verified 2026-08-30)

Continuation of `references/s10-c4-t04c-c3-strict-harness.md`. After the
harness restructure (no stage_c4/_force_requeue/DB-write), the next failure
class was the SPEC sending synthetic correction input while production
correctly fails closed. Full R4/R5 diagnostic path with exact probes.

## 1. Real typed correction is mandatory (not randomUUID)

- Symptom: run1 rendered 25 chunk MP4 + 25 evidence.json real, DB run
  `8375addb…` completed, 24/24 chunks verified, 2 publications — but test
  failed at recompute POST receiving 404/422 instead of 200/201.
- Root cause: spec sent `correction_id = randomUUID()`, but
  `S10RecomputeService._resolve_correction_authority`
  (`app/services/s10_recompute.py:325`) requires the id to resolve a
  persisted `s09_correction` row: status `applied`, natural_key bound,
  same project/video, `target_layer_ids == impact.affected_layer_ids`, and
  `affected_loop_ids` NON-EMPTY. Fixture seeded `affected_loop_ids = []` →
  even an applied row fails.
- Working flow (verified probe): POST `/s09-corrections` with kind
  `route_override` (sprite_affine→pose_swap) + idempotency key + target =
  real segment probed from DB → confirm → read persisted
  `correction_id`/`impact` → POST `/full-apply/{run_id}/recompute` with
  `correction_kind="route"`, `target_layer_ids=impact.affected_layer_ids`,
  `target_shot_ids=impact.affected_loop_ids`. Remove unused `randomUUID`
  import.

## 2. Generation skew blocks every mutation (fixture, in-scope fix)

- Seeder's DISCOVER_OBJECTS job `input_manifest_json.source_sha256` held a
  fake hash (`_sha(861)`); post-seed then wrote real source media + real
  Artifact sha → `current_generation` resolved to `"2"` while
  `OccurrenceSegment.source_generation` stayed `"1"` → every mutation
  rejected `stale generation` (probe-proven).
- Fix: `post_seed_real_authority.py` must sync the DISCOVER job manifest
  source sha to the real artifact sha. Probe the generation pair before
  blaming recompute.

## 3. Mask kind = suspected production gap; probe before routing

- `_validate_prompt_evidence` (`app/services/structural_evidence.py:492`)
  REJECTS `affected_region` as a segmentation prompt evidence key.
- `_render_mask_effect` (`app/services/s09_correction.py:805`) never writes
  `affected_region` into render_effect → `_apply_correction_facts`
  (`s10_recompute.py`) fails "carries no affected_region".
- Consequence: mask cannot drive recompute today; only `route_override`
  completes submit→confirm→recompute-facts (probe verified CONFIRM OK,
  effect `route_to/controlled_redraw` + FACTS OK).
- T04C worker must NOT patch `s09_correction.py` (production, outside
  harness scope). Route as BLOCKED_WITH_FINDINGS with file:line to the
  owning task (T03/T04A) if it stands after byte-diff probe.

## 4. Byte-diff probe before accepting the route (avoid C3 rerender trap)

- `probe3` ran both adapters on the same correction:
  `sprite_affine` 3288B sha `5860aead…` vs `pose_swap` 3757B sha
  `9c65c7aa…` — genuine byte difference, affected SHA changes (no
  byte-identical-rerender illusion). `controlled_redraw` failed
  `BACKEND_BINARY_MISSING` → choose `pose_swap` (licensed adapter works).

## 5. Final structural BLOCKED can be correct fail-closed (fixture fix)

- Repro `_repro_structural.py` (read-only on run1-final DB) over the real
  `structural_compare_gate` code path returned BLOCKED with exactly 3
  reasons:
  - `CUT_FRAMES_MISSING` — fixture `structural_lock_manifest.manifest_json`
    had `segments:[]` and no `cut_frames`.
  - `CLIPPING_MISSING` — `occurrence_segment.mask_artifact_id = NULL`.
  - `ANNOTATIONS_MISSING` — dependent on missing source cuts.
- NO production defect: server fail-closed refused empty caller truth (C3's
  old "structural fallback synthesized" is explicitly forbidden in C4A).
- In-scope fixture fix: post-seed adds `cut_frames:[50]` + `segments`
  entries (start/end/mask refs from the already-written segment rows) +
  point `mask_artifact_id` at the real asset PNG Artifact, re-sync
  `manifest_hash`/`canonical_manifest_json`, then rerun run1 + run2.

## Manager routing decision for this phase

- Every 404/422/BLOCKED during C4A T04C bring-up was fail-closed CORRECT
  behavior exposing a harness/fixture deficiency OR a suspected
  production semantics gap (mask). Classify by which SIDE supplied the bad
  value (driver vs fence vs fixture authority) before escalating. No
  production defect was confirmed in this phase; no owner resume was
  needed; harness-only resumes (same owner `20260828_023122_76b87e`, same
  prompt, same `-m ocg/deepseek-v4-flash` route) were sufficient.