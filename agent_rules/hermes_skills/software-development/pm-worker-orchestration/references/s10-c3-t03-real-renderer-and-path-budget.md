# S10-C3 T03 Real Renderer + Windows Path-Budget — Verified Execution (2026-08-29 12:15)

T03-C3 resume `20260828_011920_b79bd6` (`--provider custom -m meta`) closed P0+P1 in one shot — 13 passed ×2 (72.80s/73.39s, nested Windows basetemp, DB UNSET) + nested reruns 9.08s/9.00s, no fabric residue.

## Why fabric had to go
`app/services/s10_recompute.py:637-696` hashed `correction/cid/attempt` → 64×64 NumPy zeros → `write_frames_mp4` + `route=correction_kind` (== `effective_adapter`). No T02 call → decoded bytes, SHA/size, publication were internally consistent but never measured from approved content. Gate now requires adapter invocation >0 with exact request/route identity.

## Real renderer wiring that passed
- SELECT expanded `layer_id/chunk_index/order_index/overlap_*` at 581.
- Short ids `_run_short/_corr_short = sha256(run/corr)[:8]` (<30 chars) to bound dir length.
- Per-affected: load `_run_row` (project/video/fps) + durable job manifest `SELECT input_manifest_json FROM job WHERE idempotency_key='s10_full_apply_job:{run}'` with fallback scan `s10_full_apply/{run}/_source.mp4 + _assets/*.png` + fallback `sprite_affine`; build `_authoritative_mapping_by_layer` + `S10MultiRoleService` + `SourceTimebase`; deterministic perturbation `affected_region delta=(corr_hash%7)*0.005` so affected bytes change via real adapter, not hash color.
- Call `S10MultiRoleService.execute_role_chunk(workspace_id, project_id, video_id, workspace_root, source_media, assets_dir, output_media, source_timebase, roleMapping(deps/contact_anchor/z_order/affected_region), authoritativeMapping)` — evidence `route/effective_adapter` taken from renderer return (`SpriteAffineAdapter/sprite_affine`), `correction_kind` kept only as provenance.

## Windows path-budget fix (the real defect)
`FileNotFoundError` at 695 on `*.mp4.evidence.json.staging` is `MAX_PATH` on the sidecar name, not missing `mkdir`. Verified: same tests pass on `C:\tmp\mfs10-*` (short root) and fail on `C:\Users\Admin\AppData\Local\Temp\s10c3-*` nested root.
- Bounded rel: `f"{_base_dir_rel}/c_{idx:04d}.mp4"` with `_base_dir_rel = s10_recompute/{run8}/{corr8}` (rel <80, ev_rel <100, abs <260).
- Evidence via `ManagedRoot.atomic_write_bytes(evidence_rel, _ev_bytes)` — same-dir random staging, fsync+verify, no orphan, in-root.
- Stitch full: `f"s10_recompute/{_run_s}/{_corr_s}/full_{hash}.mp4"`.
- Tests assert `rel < 80`, `ev_rel < 100`, `abs < 260`, staging/final in-root, atomic, zero `.staging` orphan on nested `a*20/b*20/deep_root` probe.

## Instrumented tests added (4)
`test_c3_affected_adapter_invocation_and_evidence` — patch `execute_role_chunk`, assert calls == affected count, exact workspace/project/video/workspace_root/source_media/assets_dir/output_media/source_timebase, `effective_adapter/route` from renderer, affected bytes changed / unaffected byte-exact.
`test_c3_decodable_media_and_atomic_evidence` — decodable range/timebase 30/1, `SHA/size == hash_file()` + DB row, evidence in-root atomic no orphan, publication row exists.
`test_c3_nested_windows_root_path_budget` — nested `a*20/b*20/deep_root`, rel/ev_rel/abs bounds + no orphan.
`test_c3_no_fabric_sources` — grep ` _np.zeros / effective_adapter.*route.*fabric / with_suffix.*staging / recompute.*hash.*fabric / chunk.*.bin` == 0 across `app/`.

## Sweeps that must stay 0
`grep -rn "_np.zeros\|effective_adapter.*route.*fabric\|with_suffix.*staging\|recompute.*hash.*fabric\|chunk_.*\.bin" app/` — all 0 after fix (ruff `F` PASS, mypy `Success`).

## Pitfall to carry forward
Shortening the reviewer basetemp hides the bug — verification MUST keep the C2-required nested Windows root (`C:\Users\Admin\AppData\Local\Temp\s10c3-*`) for the path-budget probe. `mkdir(parents=True)` already existed at 692-694; length, not existence, was the failure.
