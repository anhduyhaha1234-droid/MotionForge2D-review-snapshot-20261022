# S10-C4/C4A T04C-C3 — strict vertical harness without DB writes or requeue helpers

Verified 2026-08-30. Owner session `20260828_023122_76b87e`, route
`-m ocg/deepseek-v4-flash` (no provider flag), reasoning max, fallback OFF,
TTFB 900.

## Why this correction existed

C3-era T04C harness used `output/s10/stage_c4.py` (synthetic 100-frame NumPy
source + hash-colored assets, direct `UPDATE job SET input_manifest_json` via
SQLite) and `_force_requeue.py` (direct lease expiry + zero-grace reconciler).
Codex C3 review flagged both as P1: the runs proved a mutation path, not the
normal production restart/recovery contract. C4 prompt §9 then demanded strict
vertical runs: real canonical fixture media/assets, authority created through
product handlers/APIs, DB access read-only probe only, real typed durable
correction + recompute by persisted ID, natural lease/reconciler recovery.

## The clean harness shape that worked (R1, first exit)

1. **Fixture regeneration** — `generate_fixtures.py` produces REAL decodable
   media (`media/source.mp4` 17186 B + `media/assets/layer_*.png`), updates
   `manifest.sha256` (8 fixture files). Critical: after regen the build
   validator must STILL pass 7/7 (`node run-s10.js --verify-build-only` PASS
   with BUILD_ID KIWvay6FvLdiWmVFduSMG). A fixture change that breaks the
   manifest contract fails preflight, not mid-run.

2. **Authority seeding through product models only** —
   `post_seed_real_authority.py` (new, in fixture scope): source artifact pin
   (sha/size matching the real file), CharacterAsset for the pack,
   OccurrenceSegment ×2, SegmentMotion ×2, SceneGraphContact ×1,
   SegmentRenderRoute ×6 — all with CHECK constraints satisfied. Proved by
   live output: `POST_SEEDED … seg=2 motion=2 contact=1 route=6 artifacts=4`.
   No `stage_c4.py`, no `input_manifest_json` patch, no lease/grace=0 touch,
   no direct reconciler invocation. global-setup.ts calls post-seed after the
   SEEDED marker.

3. **Natural restart recovery** — spec removed the block that ran
   `stage_c4.py`, the retry/resume hack, `_force_requeue.py` and grace=0.
   Recovery: production `POST /resume` + the replacement backend's reconciler
   does its real 90s fence/requeue. Spec polls up to 420s (test timeout
   raised to 900s), asserts job `attempt >= 2` / attempt rows >= 2 AND job
   completed.

4. **Manifest hash comes from the manifest** — spec parses the REAL
   `manifest_hash` from `structural_lock_manifest` (not the approval
   checkpoint hash). Mapping pins `pack_version_id` (C6 authority).
   Structural rows probed (never zero-row fallback), ffprobe/decode/DB
   frame-range/>260 path evidence files: `media-evidence.json`,
   `recovery-timeline.json`, `structural-rows.json`, screenshots step1-3.

## Smoke-run finding: fail-closed 422 = fence working

Live smoke on an isolated backend (port 8299, runtime path 194 chars):
seeder + post-seed OK; approval 201; verify 200 True; then full-apply submit
returned **422** `manifest_hash mismatch: client '09a6c553…' vs manifest
'9f77b8c3…'`.

Attribution: the SMOKE DRIVER passed the approval `checkpoint_hash` where the
C6 authority resolve/validate path requires the `structural_lock_manifest
.manifest_hash`. The server was right; the driver was wrong.

Manager lesson: a fail-closed rejection during harness bring-up is evidence
the fence under test WORKS — before flagging a product defect, determine
which side supplied the wrong value (read the error message: it names both
client and server values). Record it in the worker report as a positive
control alongside the negative tests.

## Exit shape → next action

Worker exited R1 with honest `STATUS: RUNNING` — harness restructured,
everything proven except the 2 official runs; blocker was the smoke driver
hash bug, fix APPLIED but not yet re-run (iteration cap). Because the
diagnosis was a work-continuation blocker (not infra), Manager resumed
IMMEDIATELY with the SAME prompt (`proc_49d02bf71427`, dispatch-r2.log) —
no 5-minute wait (RESUME-IMMEDIATELY rule).

## Evidence checklist still required at final exit

- ffprobe every chunk/publication/recompute artifact (codec/width/height/
  time_base, decode frames == DB core range)
- final/staging path >260 chars asserted per run, no reviewer-root shortening
- job attempt >= 2 (natural recovery), 0 < verified < total at stop
- structural rows present in read-only DB probe (non-empty authority)
- ports 8201/3015/3014 cleanup via netstat; unrelated processes preserved
- same validated build manifest both runs; distinct fresh roots/DBs/run/job/
  correction IDs; zero `.bin`/`.partial`/`.staging`

## Related

- `s10-c3-t04c-vertical-harness.md` — the C3 harness it replaced.
- `s10-c4-authority-fence-preflight.md` — where the C6 authority resolve/
  pin contract was built (T01C-C6).