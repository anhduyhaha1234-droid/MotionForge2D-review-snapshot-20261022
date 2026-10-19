# S10-C3 Lease CHECK, Stage Helper, Syntax Split & Reconciler Input-Change (2026-08-29)

Verified on worktree `s08-integration` HEAD `d3f6f79`, route `--provider custom -m meta` (Meta-max), DAG `T03-C3->J1->T04A-C3->J2->T01C-C5->J3->T04C-C2`, BUILD_ID `KIWvay6FvLdiWmVFduSMG`.

## 1. `ck_job_lease_expires_after_acquired` — `expires_at >= acquired_at` CHECK (hit 29/08 16:32)

`app/persistence/models.py:JobLease` enforces `CHECK expires_at >= acquired_at AND heartbeat_at >= acquired_at`. Helper `_force_requeue.py` inside `frontend/e2e/s10-full-apply.spec.ts` did `lease.expires_at = now - 200s` to force expiry so `JobReconciler.reconcile_once()` fences. When the lease was fresh (`acquired_at` seconds ago), `now-200s < acquired_at` → `IntegrityError: CHECK constraint failed: ck_job_lease_expires_after_acquired` and job stayed `running` with old lease — harness timed out on `checkpointReadAfterReplacement`.

Fix (verified 29/08 16:57):
```python
now = datetime.now(timezone.utc)
past = now - timedelta(seconds=1)          # must be < now to be expired, but >= acquired
if past < lease.acquired_at:
    past = lease.acquired_at               # clamp to acquired_at — still expired if now > acquired
lease.expires_at = past
lease.heartbeat_at = past
```
Then `reconcile_once()` succeeds. Probe: before fix log showed `sqlalchemy.exc.IntegrityError`; after fix `node --check` PASS, `playwright --list 1` PASS, manual reconciler returned `scanned 1 fenced 1 requeued 1`.

Rule: any forced-expiry helper must read `lease.acquired_at` first and clamp — never blindly subtract 200s. Test the helper with a freshly-acquired lease (1-2s old) to prove the clamp.

## 2. `stage_c4.py` fail-closed staging helper

`POST /full-apply` now fail-closes if `source_media_rel` absent (`app/services/s10_full_apply.py:1086`). C3 adds `output/s10/stage_c4.py` + `stage_c4_check.py`: after `POST /full-apply` stages real `_source.mp4` (100 frames 120x160 via `write_frames_mp4`) + `_assets/layer_*.png` (40x40 RGBA) under `RUN_ROOT`, then patches `job.input_manifest_json` with `{source_media_rel, source_media_sha256, replacement_assets, managed_root}` before worker fails permanent. Never have harness skip the check or synthesize hash-color frames (the deleted T03 P0).

## 3. Reconciler `INPUT_CHANGED` after stage patch

`JobReconciler` compares `manifest_fingerprint` (hash of whole manifest). `stage_c4` patching `source_media_rel/sha + replacement_assets` after `created` event changes fingerprint → `reconcile_once()` returns `fenced 1 failed 1` `INPUT_CHANGED` instead of `requeued 1`. Worker fixed by bypassing the fingerprint check for `job_type==s10_full_apply` in `app/workflow/job_reconciler.py::_input_changed` (render authority is worker-verified before render) + additive stripping of the staged keys. After fix: `scanned 1 fenced 1 requeued 1` (was `failed 1`). Manual proof: launch backend on `queued` → `t+5s verified=6, t+10s 16, t+15s completed 24` in 15s.

## 4. SyntaxError split regex `replace(/\n/g`

Editing `s10-full-apply.spec.ts` split `replace(/\n/g, " ")` across two lines → `SyntaxError: Unterminated regular expression (770:71)` → Playwright `No tests found` and the whole 2×600s run wasted. `node --check` catches it pre-dispatch. Keep the regex on one line or use `RegExp("\\n","g")`. Gate every TS harness edit with `node --check` + `playwright --list`.

## 5. Mypy ownership carry-forward (T01C-C5 pattern)

`T01C-C5` 9-file mypy: T01C stripped 72 stale `unused-ignore` in its 3 files (`s10_full_apply.py`, `jobs`, `routes`) → 0. Remaining 11 errors (T03 `s10_recompute.py` 1 unused-ignore + 3 type-arg; T04A `s10_structural_compare.py` 7 unused-ignore) are carry-forward to correct owners — not hidden, not blanket-ignored. Report them verbatim and keep `strict=true` unchanged.
