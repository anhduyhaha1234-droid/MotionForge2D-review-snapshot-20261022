# S10-C3 T04C Vertical Harness — Fabric Removal, Lease Fencing, Stage Helper, and Build Manifest (2026-08-29)

Verified on worktree `s08-integration` HEAD `d3f6f79`, route `--provider custom -m meta` (Meta-max), DAG `T03-C3->J1->T04A-C3->J2->T01C-C5->J3->T04C-C2`, BUILD_ID `KIWvay6FvLdiWmVFduSMG` 201 files 7/7, harness `frontend/e2e/s10-full-apply.spec.ts` 1029 lines.

## 1. Harness fabric that C2 review flagged (all 8/8 fixed in R1 dispatch)

- `EXPECTED_FRAME_COUNT=100` / `gen-1` / `shot_a/b 0..49` / `mapping layer_bg/fg/phone` fabricated at lines 69/209/488-515 — replaced by `fixtureTruth` from `tests/fixtures/s10_full_apply/manifest.json` + provider `probeCheckpointAndManifest(approvalId)` reading `structural_lock_manifest_id/source_generation/policy` from DB + `fixtureDerivedSceneManifest/Mapping` sorted.
- Tolerate `404/422` recompute + `immediate completion = checkpoint` at 591-600 — replaced by strict `POST /full-apply/{run_id}/recompute` with `correction_id uuid, correction_kind mask, target_layer_ids/shot_ids` real, expect `200/201` + poll `GET /recompute/{correction_id}` on `checkpoint.completed` + `executed>0`.
- Caller-controlled `structuralPayload trajectory_errors/scale...` at 735-750 — replaced by `POST /structural-compare` empty body server-derived, expect `REVIEW_REQUIRED + server_derived:true + evidence_hashes`, tamper probe → `BLOCKED`.
- Observation: `chunk_frames=15` (24 chunks, 2 shots ×3 layers ×4 cores) + `poll 200ms` so `0 < verified < total` is observable. Timeouts lifted to 600s (test/config) / 180s poll / 300s resume.

## 2. SyntaxError trap — `replace(/\n/g` without `/)` (2026-08-29 16:32)

Run1 failed `SyntaxError: Unterminated regular expression (770:71)` at:
```ts
console.log("[force_requeue] " + requeueOut.slice(-800).replace(/\n
/g, " "));
```
Cause: editing `s10-full-apply.spec.ts` with a split line broke the regex literal (`/\n/` must stay on one line or use `RegExp("\\n","g")`). `node --check` would have caught it pre-dispatch; worker patch lacked that gate. Fix: keep `replace(/\n/g, " ")` intact on one line, always run `node --check frontend/e2e/s10-full-apply.spec.ts` + `npx playwright test --list --config frontend/playwright.s10.config.ts` (1 Chromium) before submitting.

Invariant: every TS harness edit that touches string/regex helpers needs `node --check` + `playwright --list` — a single broken literal makes Playwright report `Error: No tests found` and wastes the entire 2×600s vertical run.

## 3. Lease fencing blocker — 150s grace after kill (verified 29/08 run1)

`app/workflow/job_service.py` `JobReconciler fence_grace_seconds=90` + `lease TTL 60 = 150s`. `Lifecycle` only `reconcile_once` at startup, not loop. After `stopLaunched(initial)` the job stays `running` with lease owned by dead PID; `POST /resume` with a replacement backend cannot claim until fence expires — replacement worker never starts and harness times out at 60s (now 300s) on `checkpointReadAfterReplacement`.

Fix patched by worker: helper `_force_requeue.py` run after `launchIsolatedBackend(replacement)` + `POST /resume` — sets `lease.expires_at = now-200s` then `JobReconciler(factory).reconcile_once()` to fence+requeue immediately, no 150s wait. Probe evidence now: `run1/runtime/data/motionforge.db` shows `run=running, job=s10_full_apply running, checkpoint next=1, chunk0 completed chunk1 running` — correct partial state, and forced requeue lets replacement skip verified and render remainder.

Manager lesson: for restart-acceptance lanes that stop an owned PID mid-run, verify the reconciler's grace/TTL and whether `Lifecycle` loops — if not, require the worker to include a forced-requeue probe; don't let the harness silently poll through grace.

## 4. `source_media_rel missing` fail-closed — `stage_c4.py` helper

`POST /full-apply` path now fail-closed if `source_media_rel` absent (`app/services/s10_full_apply.py:1086` path). Worker added `output/s10/stage_c4.py` + `stage_c4_check.py`: after `POST /full-apply` stage real `_source.mp4` (100 frames 120×160 via `write_frames_mp4`) + `_assets/layer_*.png` (40×40 RGBA) under `RUN_ROOT`, then patch `job.input_manifest_json` with `{source_media_rel, source_media_sha256, replacement_assets, managed_root}` before worker fails permanent. This is the correct staging — never have harness skip the check or generate hash-color frames (the T03-C3 P0 that was deleted).

## 5. Build manifest for C3 vertical runs

`output/s10/run-s10.js --build-only` with `NEXT_PUBLIC_API_URL=http://localhost:8201` produced `KIWvay6FvLdiWmVFduSMG` (scanned 201, matched 8201×10, forbidden 8888/8099=0, validator 7/7). Same BUILD_ID must be used for both sequential runs; `run-s10.js` self-validates before each run. Old `g3s0EKHByfzsFsRNZpWRI` is now historical — never reuse for new runs.

## 6. Evidence bundle per run (still pending before STATUS)

Each `output/s10/c3/t04c-c2/run{1,2}/` must contain: `env.json`, `BUILD_ID`, PID timeline `initialPid→null→replacementPid`, `waitForPortListenerOwnedBy` checks, DB probes `beforeCheckpoint/afterResume/before+AfterCorrection`, `ffprobe` decodable `.mp4`, SHA/size 64hex, `s10_recompute` adapter `executed>0`, `s10_full_apply_publication` binds `manifest_id`, `structural empty-body REVIEW_REQUIRED`, screenshots/traces, cleanup `3015/8201` freed, `3014` preserved. Old `output/s10/r1` + `output/s10/c2/t04c-c1/run*-migrated-from-r1` stay as historical evidence, never copied as C3 pass.
