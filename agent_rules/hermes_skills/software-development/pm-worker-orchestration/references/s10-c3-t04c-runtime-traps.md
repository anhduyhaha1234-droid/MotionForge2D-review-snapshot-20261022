# S10-C3 T04C runtime traps — managed_root, recompute session, lease CHECK, perturbation delta

Verified 29/08 C3 T04C-C2 R1→R4 (owner 76b87e, BUILD KIWvay6FvLdiWmVFduSMG). Three traps that blocked the strict vertical harness after fence was green:

## 1. managed_root /artifacts mismatch → RENDERED_FILE_MISSING
- `JobService.managed_root` is `runtime/artifacts` (via `get_job_service().managed_root`).
- Naive stage helper wrote helper media to `runtime/s10_full_apply/{run}/_source.mp4` (no `/artifacts`).
- Handler `s10_full_apply_jobs.py` writes chunks to `managed_root / s10_full_apply/{run}/chunk_*.mp4` → `runtime/artifacts/...`
- `s10_structural_compare.py` read path used `managed_root / rel` where `rel` was already `s10_full_apply/...` → mismatch read `runtime/artifacts/s10_full_apply/...` vs actual `runtime/s10_full_apply/...` → BLOCKED.
- Fix: `_c4_stage_source_and_assets()` in `app/api/routes/s10_full_apply.py` + `output/s10/stage_c4.py` canonical `managed_root = Path(managed) / "artifacts"` and patch helper to write under `artifacts/`. Verify with `rglob("artifacts/s10_full_apply/*/chunk_*.mp4")` matches `artifact.relative_path`.

## 2. Recompute checkpoint — isolated session_factory swallowed exception
- `POST /full-apply/{run}/recompute` handler branched `if hasattr(session, "bind") and session.bind` → in QA isolated runtime (`MOTIONFORGE_ROOT=runtime`) `session.bind` is None → fell into `except: pass` and left `s10_recompute_checkpoint` with `completed 0 executed []` despite `200 affected 4`.
- Fix: use `deps.get_job_service().session_factory` (engine bound to isolated DB) with fallback `create_engine_for_path(default_database_path())`, explicit `commit()`, and log to `managed_root/_recompute_execute_error.log`. Probe: direct `S10RecomputeService.execute_partial` gives `completed True executed 4` with `.evidence.json`.

## 3. Lease CHECK `ck_job_lease_expires_after_acquired` → force_requeue IntegrityError
- `frontend/e2e/s10-full-apply.spec.ts` `_force_requeue.py` did `lease.expires_at = now-200s` (aware) vs `acquired_at` naive → `TypeError` then `CHECK constraint failed: expires_at >= acquired_at`.
- Fix: `past = max(lease.acquired_at, now - 1s)` with both naive, also set `heartbeat_at = past`, use `ReconcileConfig(fence_grace_seconds=0)` so `cutoff = now` fences immediately (`scanned 1 fenced 1 requeued 1` vs `scanned 0` with 90s grace).

## 4. Perturbation delta 0 → recompute bytes identical
- `_delta = ((_corr_h %7))*0.005` can be 0 for hash `28446…` → `after sha == before sha` fails `expect(after).not.toBe(before)`.
- Fix: `((_corr_h %6)+1)*0.005` (range 0.005..0.03, never 0). Verified in `app/services/s10_recompute.py:890-918`.

Repro: `node output/s10/run-s10.js --run-label run1 --runtime-root .../run1/runtime --output-root .../run1` (timeout 600s) must reach `structural REVIEW_REQUIRED` not BLOCKED. Gates before SUBMITTED: `node --check` + `playwright --list 1 Chromium` PASS, `ruff --select F` ALL PASS, `git diff --check` 0.
