# S10-T04C-C2 Strict Vertical Harness — Class Lesson (2026-08-29)

Source: `frontend/e2e/s10-full-apply.spec.ts` overhaul for 8 binary requirements, worktree `s08-integration`, BUILD_ID `KIWvay6FvLdiWmVFduSMG`.

## What "strict" means
- No hard-coded `source_generation` (gen-1), `frame_count` 100, `shot_a/b`, `layer_bg/fg/phone`, metric arrays (`source_frame_count`, `rendered_frame_count`, `trajectory_errors`...), or synthetic checkpoint authority at spec top-level. All must be created/read via `tests/fixtures/s10_full_apply/manifest.json` + app handlers/APIs, then derived from persisted server authority (DB probes, API GETs, checkpoint verify, manifest hash, `s10_full_apply_run/chunk/publication` tables).
- Spec hardness gate: remove `EXPECTED_FRAME_COUNT` constant or derive it from fixture manifest at runtime in `test.beforeAll`.

## The 8 binary requirements (enforce in harness)
1. **Server-derived truth** — fixture -> API -> DB. No fabricated constants beyond reading fixture.
2. **Recompute must succeed** — `POST /full-apply/{run_id}/recompute` with `{correction_id, correction_kind: mask|z_order|contact|route|asset, target_layer_ids:[real], target_shot_ids:[real], expected_revision}` must return 200/201, then poll `GET /full-apply/{run_id}/recompute/{correction_id}` until completed, then DB probe affected vs unaffected. Delete any `404 as success` or skip-recompute tolerance.
3. **Real durable checkpoint observed** — each run must hit `0 < verified_chunks < total_chunks` via polling `s10_full_apply_run/chunks` API + DB probe, record `initialLaunched.proc.pid`, `stopLaunched` exact PID, prove port owner null/different, launch replacement PID and prove it owns port, `POST /full-apply/{run_id}/resume`, poll to completed, verify artifact SHA unchanged for verified-before. If too fast, use `chunk_frames: 15-20` and 200ms poll, not production `stop_after_chunk` param.
4. **Two sequential distinct roots** — fresh nested roots + distinct SQLite DB + distinct run/job IDs, same `BUILD_ID` from corrected tree (`frontend/.next/BUILD_ID`). Never use `g3s0EKHByfzsFsRNZpWRI` or migrated roots. Orchestrate via `output/s10/run-s10.js --run-label --runtime-root --output-root` which validates 7/7 before each run.
5. **Media playable** — chunk/publication `.mp4` decodable via `decode_rgb_frames`/`ffprobe`, zero `.bin`, SHA/size non-null matches file bytes, publication binds current run/manifest.
6. **Affected-only correction** — adapter calls >0 (probe recompute checkpoint `executed_json`), affected attempt +1 / new media / new publication (SHA diff), unaffected byte-exact + 0 calls, replay dedupes (second POST same `correction_id` returns `reused:true` without new attempt).
7. **Structural compare server-derived** — `POST /full-apply/{run_id}/structural-compare` with `{}` (no caller metrics). Server derives from checkpoint-pinned manifest + decoded publication + evidence hashes. Assert `REVIEW_REQUIRED` + `server_derived:true` + evidence hashes present, then negative `BLOCKED` via tampered file (append byte, re-POST, expect BLOCKED/422, restore).
8. **Evidence per run** — env, branch/HEAD, dirty snapshot, hash manifest, BUILD_ID, PID/port timeline (initial/replacement, timestamps), API bodies/status, DB probes before checkpoint/after resume/before+after correction, ffprobe, SHA/size, adapter invocation, structural evidence, screenshots/traces, cleanup. Ports 8201/3015 free after, 3014 preserved.

## Code locations fixed
- `spec:69` `EXPECTED_*` constants -> derived `fixtureTruth` in `beforeAll`.
- `spec:209,488-515` synthetic `approved_checkpoint`/`structural_lock_manifest`/`scene_manifest`/`mapping` with `gen-1`/`100`/`shot_a/b` -> `probeCheckpointAndManifest` + fixture-derived `scene_manifest`/`mapping` (executable routes with `affected_region`, `mesh_warp` -> `sprite_affine`).
- `spec:683-750` tolerate-missing recompute + hard-coded `structuralPayload` -> strict `POST recompute` + empty `POST structural-compare`.
- `spec:570-600, 640-680` weak checkpoint/resume polling -> tight 200ms + DB-verified partial checkpoint + exact SHA skip proof.

## Reusable helpers added to spec
- `probeS10Run(runId)` — run/chunks/publications/artifacts/jobs/steps.
- `probeRecomputeCheckpoint(correctionId)` — `s10_recompute_checkpoint` next_index/executed_json/completed.
- `probeCheckpointAndManifest(checkpointId)` — `apply_checkpoint` + `structural_lock_manifest` manifest_json/hash/policy/generation/frame_count.
- `resolveManagedArtifactPath(rel)` — `RUN_ROOT/artifacts/<rel>` + fallback.
- `fixtureTruth` runtime object + `chunk_frames:15` for observable checkpoint.

## Pitfalls to prevent next time
- Do not reintroduce top-level `const EXPECTED_FRAME_COUNT = 100`; C2 review flags it as fabrication.
- `structural_lock_manifest.source_generation` from DB is `1`, not `gen-1` — use DB value.
- `policy_version` pinned is `structural-thresholds-v1`, not `v1`; take from manifest row.
- `_probe_s10.py` must select `revision` column or harness loses `expected_revision` truth.
- Triple-use `s08-integration` mapping `mesh_warp` is not executable in production worker (`_EXECUTABLE_ROUTES = {sprite_affine,pose_swap,controlled_redraw}`); coerce to `sprite_affine` in fixture-derived mapping.
- Spec file must be TS-only `tsc --noEmit` clean and `python -m ruff check --select F app/` green; ruff on `.ts` is invalid (it parses as Python).
