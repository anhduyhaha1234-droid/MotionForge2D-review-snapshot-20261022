# S10-C2 — T04A measured server structural gate + J4 (verified 2026-08-29 02:14–02:57)

Continuation of `s10-c2-t03-report-finalization.md` — same session `20260828_180654_be71b5`, worktree `s08-integration`, owner `20260828_014304_25d94a` (T04A), route `custom/meta` (Meta-max).

## Why this exists
T04A-C2 is the `measured server structural gate` — the server must derive `ServerDerivedCompareResult` from manifest-pinned evidence (hashes, chunk boundaries, segment z_order), not from fabricated `shot_a` / mirrored rendered cuts / hard-coded `0.05/0.1` pass. Prompt C2 mandates: every placeholder surface grep ZERO in product code before `TASK_SUBMITTED`.

## Fix (exclusive write-set, no migration/model/frontend/S11/S13/J1)

### `app/services/s10_structural_compare.py`
- Docstring + `__all__` add `MEASUREMENT_METHOD="s10-structural-v1"` `MEASUREMENT_VERSION="1"`.
- `ServerDerivedCompareInput` add `measurement_method/version` defaults.
- `ServerDerivedCompareResult` add `measurement_method/version`, `evidence_hashes`, `decoded_frame_count`, `to_dict` writes all 4 hashes + method/version.
- `build_server_derived_result` unified: source `fps_num/den` ONLY from manifest `timebase` (remove `if rendered_cut_frames -> src` + synthetic sentinel), single-shot `len==0/1` conditional else `CUT_FRAMES_MISSING` BLOCKED, `evidence_hashes` collect `routes/contacts/visibility+z_order/motion`, trajectory/scale/rotation/contact query `segment_motion` count then measured vs chunk-derived, `z_order_inversions` from `occurrence_segment.z_order` adjacent decrease.

### `app/api/routes/s10_full_apply.py` (968-1311 measured gate)
- Source `frame_count/fps/shot_order` ONLY from manifest pin, missing `shot_order` -> `SHOT_ORDER_MISSING` BLOCKED.
- `chunks` missing -> `EVIDENCE_MISSING` BLOCKED.
- `rendered_shot_order/cut_frames` from chunk `core_start_frame` boundaries, `source_cut_frames` from `manifest_dict.get("cut_frames")` else `frame_count//len(shots)` else single-shot sentinel conditional — no defensive mirroring.
- Remove 3× `manifest_dict.get("shot_order",["shot_a"]) -> []`, placeholder `source_cut = rendered`, synthetic `[source_frame_count]`, defensive mirror, `0.05/0.1/0.08` always-pass, fake `["shot_a"]` fallback -> `[]`.

Verify after patch: `grep shot_a` only comment, `synthetic/mirrored` only docstring, `py_compile` success both files.

### `tests/test_s10_structural_compare.py` (34 -> 41)
- Helper `_seed_publication_directly` (100 frames `write_frames_mp4` + `hash_file` + INSERT `artifact/artifact_owner/s10_full_apply_publication` with `frame_metadata_json` bind) to avoid `render_authority missing`.
- Fix 6 existing tests to use direct seeding (`tampered_rendered_file_blocks`, `only_server_green_can_review`, `measurement_method_version_present_in_green`, `cut_drift_via_chunk_boundary_blocks`, `z_order_inversion_blocks_via_segment`, `removed_evidence_blocks_api`).
- Add 6 C2 tests: `measurement_method_version_present`, `measurement_hashes_present_even_when_blocked`, `cut_drift_via_chunk_boundary`, `z_order_inversion_blocks_via_segment`, `no_mirroring_source_cuts_stay_independent`, `removed_evidence_blocks_api`, `no_fake_shot_a`.
- Fix `frame_metadata_json` bind `:fmj` + `occurrence_segment.logical_id` missing -> `test_z_order_inversion_blocks_via_segment` was FAILED NOT NULL `reasons_json` then `REVIEW_REQUIRED` due `ORDER BY z_order` masking inversion, now `BLOCKED Z_ORDER_INVERSION`.

## Validation arc (DB UNSET, fresh basetemp, `custom/meta`)

| Attempt | Log | Result |
|---|---|---|
| R1 02:14 | `dispatch-meta.log` 90 B | `CommandCode Network connection lost` (same transient as T03) |
| R2 02:14->02:36 | `dispatch-meta-r2.log` 4958 B | Checkpoint: 40 passed 1 failed (`z_order logical_id` patched not yet re-run) |
| R3 02:36->02:56 | `dispatch-meta-r3.log` 2523 B | Stray `_append_task.py` cleared, re-verify fresh: 41/41 -q (13.54s), then 41 passed x2 (13.49s/13.46s) verbatim `pytest-run1/2.log`, ruff 0 F, mypy Success, TASK/LOG/REPORT CORRECTION C2 |

Evidence preserved `output/s10/c2/t04a-c2/**`: `pytest-run1.log` `pytest-run2.log` `pytest-t03/t01c/t02-regression.log` (9/23/46), `ruff_F.log`, `mypy.log`, `diffcheck`, `git_status`, `openapi` (327 unique, `/api/v2/full-apply/{run_id}/structural-compare` present), `basetemp`, `db_guard`, `source-*`, `fileline-after`.

## J4 Manager gate (independent, not trust worker)

```
mkdir -p output/s10/c2/j4
unset MOTIONFORGE_DATABASE_URL
python -m pytest tests/test_s10_structural_compare.py -q -p no:cacheprovider --override-ini="addopts=" --basetemp=C:/Users/Admin/AppData/Local/Temp/s10c2-j4a -> 41 passed 23 warnings 13.61s -> j4-run1.log
python -m pytest tests/test_s10_structural_compare.py -q -p no:cacheprovider --override-ini="addopts=" --basetemp=C:/Users/Admin/AppData/Local/Temp/s10c2-j4b -> 41 passed 23 warnings 13.70s -> j4-run2.log
```

Registry: `2026-08-29 02:57 +07 — J4 (C2) GATE MANAGER_VERIFIED — T04A-C2 DONE 41/41 x2 (Meta-max)` — opening T04B-C1-R1 (`proc_be8be4d7d020`, owner `20260828_020206_b1f8af`, `custom/meta`).

## Rules to carry
1. **Measured gate grep ZERO**: `shot_a` (outside comment), `synthetic`/`mirrored` (outside docstring), hard-coded `0.05` pass, `hash-only proof` must be gone in `app/` before gate. Check with `grep -rn` scoped to `app/`.
2. **Direct seeding for structural tests**: publications via `_seed_publication_directly` (100-frame mp4 + hash) not via full worker `render_authority` path, or 6 tests fail closed.
3. **Same transient retry**: 90 B `Network connection lost` + wrapper EXIT=0 -> retry same owner same `custom/meta`, not new session (seen in T03 and T04A R1).
4. **z_order inversion needs logical_id**: `occurrence_segment` join must expose `logical_id` for inversion count; `ORDER BY z_order` alone masks it.
