# S10-C3 EXIT 9 gates — fresh verification after 4 serialized corrections (verified 29/08 18:51)

All 4 C3 owners completed with same route `--provider custom -m meta max/OFF TTFB900` before EXIT: T03-C3 13/13×2, T04A-C3 41/41×2, T01C-C5 23/23×2 + 170, T04C-C2 run1 48.3s + run2 48.2s KIWvay6FvLdiWmVFduSMG.

## 9 gates run by Manager (fresh, not trusting worker reports)

1. **J1-v4 direct** `13/13` exact bytes, 12 LF + 1 CRLF — `freeze_manifest_v4_after.json` hash check
2. **Full `tests/test_s10*.py` ×2** distinct basetemp `s10c3-exit-a/b`, `MOTIONFORGE_DATABASE_URL UNSET`, `-p no:cacheprovider --override-ini="addopts=" -q` — **170 passed ×2** (235.87s + 203.94s) zero fail/skip — logs `output/s10/c3/exit/full-a.log` + `full-b.log`
3. **Ruff F** `All checks passed!` — `python -m ruff check app/services/s10_recompute.py app/services/s10_structural_compare.py app/services/s10_full_apply.py app/workflow/s10_full_apply_jobs.py app/api/routes/s10_full_apply.py --select F`
4. **9-file mypy** `15 errors in 3 files` — 8 unused-ignore + 3 type-arg + 2 no-untyped-def + 1 dup — carry-forward T03/T04A + helper `_c4_stage_source_and_assets` — status `fair` per prompt (T01C own 0, not blocking)
5. **git diff --check** EXIT 0 (warn LF/CRLF `frontend/playwright-report` pre-existing)
6. **Alembic** single head `a10b11c12d3e` — must `cd worktree` before `alembic heads`
7. **verify-build-only 7/7** BUILD_ID `KIWvay6FvLdiWmVFduSMG` scanned 201 matched 8201=10 forbidden 0 hash `734576402cff` — `node output/s10/run-s10.js --verify-build-only`
8. **Ports** `8201/3015` free, `MOTIONFORGE_DATABASE_URL UNSET`, `3014` preserved
9. **DB/file truth** `run1+run2` distinct DB/runtime/output, same manifest, `0<verified<total` + lease `requeued 1`, decodable `.mp4` not `.bin`, SHA64/size khớp, publication binds manifest — no copy from `output/s10/r1`/`c2/migr` (historical preserved)

## Why ×2 matters
Single run passed does not prove deterministic planner purity (S10 T01B reference 26×2) or isolated DB hygiene. Two fresh nested roots with UNSET DB + no cacheprovider proves no shared-state leak.

## Repro
```
unset MOTIONFORGE_DATABASE_URL
python -m pytest tests/test_s10*.py -q -p no:cacheprovider --override-ini="addopts=" --basetemp=$(mktemp -d)   # ×2 distinct
python -m ruff check app/services/s10_recompute.py app/services/s10_structural_compare.py app/services/s10_full_apply.py app/workflow/s10_full_apply_jobs.py app/api/routes/s10_full_apply.py --select F
python -m mypy app/workflow/s10_full_apply_jobs.py app/services/s10_structural_compare.py app/services/s10_recompute.py app/services/s10_multi_role_apply.py app/services/s10_full_apply.py app/services/s10_chunk_plan.py app/schemas/s10_full_apply.py app/persistence/s10_full_apply.py app/api/routes/s10_full_apply.py --ignore-missing-imports
node output/s10/run-s10.js --verify-build-only   # 7/7 KIW...
alembic heads   # from worktree
git diff --check
```
 Evidence canonical: `output/s10/_build/frontend-build-manifest.json` + `output/s10/c3/t04c-c2/run1+run2` + `output/s10/c3/exit/full-a/b.log` — historical `output/s10/r1` + `output/s10/c2/t04c-c1/run*-migrated-from-r1` preserved.
