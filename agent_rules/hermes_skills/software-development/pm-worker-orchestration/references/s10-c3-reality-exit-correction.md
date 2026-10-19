# S10-C3 Reality Exit Correction — Serial DAG with Path-Budget & Measured Gates (2026-08-29)

Source: `docs/pm/reviews/S10_C2_PM_REVIEW_2026-08-29.md` (CHANGES_REQUESTED → C3) and C3 prompt `S10_C3_REALITY_EXIT_CORRECTION_MANAGER_2026-08-29.md`. Serial DAG: `PREP → T03-C3 → J1 → T04A-C3 → J2 → T01C-C5-STATIC → J3 → T04C-C2 → EXIT`. No parallel writers (shared API/type joins); T04C only after all production joins green.

## Findings (5, frozen)

1. **T03 fabricates frames** — `s10_recompute.py:637-651` hashes correction metadata → 64×64 NumPy color frames → MP4; `676-688` sets `route/effective_adapter = correction_kind` (no T02 call). Must call corrected T02 authoritative executor with pinned source/pack/asset/role/layer/shot/range/dependency identities + correction provenance; evidence `route/effective_adapter` = renderer return value.
2. **T03 path-budget** — full S10 suite fails `test_unaffected_preserved_and_affected_attempt_plus_one` + `test_restart_during_partial_recompute_resumes` with `FileNotFoundError` at `695` for `*.mp4.evidence.json.staging`; short root `C:\tmp\mfs10-*` passes. Fix = bounded relative names + atomic strategy inside managed root; tests must assert staging/final in-root, atomic, no orphan.
3. **T04A fixed metrics** — `s10_full_apply.py:1086-1106` even-spacing/sentinel source cuts; `1175-1189` fixed `[0.05,...]` arrays; `1193-1209` missing→`0/False`; `1227-1241` midpoint/chunk-derived annotations; hash-only substitution. All must derive from persisted source manifest + decoded publication; missing → `BLOCKED`.
4. **Mypy 76 errors in 5 files** — nine-file command `mypy app/workflow/s10_full_apply_jobs.py app/services/s10_structural_compare.py app/services/s10_recompute.py app/services/s10_multi_role_apply.py app/services/s10_full_apply.py app/services/s10_chunk_plan.py app/schemas/s10_full_apply.py app/persistence/s10_full_apply.py app/api/routes/s10_full_apply.py` must return 0; owners fix own files, then T01C static-only joins.
5. **T04C no C2 evidence** — wrapper `EXIT=1` 7B, migrated `g3s0EKHByfzsFsRNZpWRI` runs (not `UoAHhbO6043uUWKNz2JTZ`), `.bin`/NULL SHA, no recompute table, harness fabricates frame/scene/mapping (lines 69/209/488-515/591-600/683-731/735-750). Need 2 fresh sequential current-build runs, `0 < verified < total` stop, replace PID, decodable media, affected-only recompute, measured structural compare.

## Ownership & Route

Exact sessions: T03 `20260828_011920_b79bd6`, T04A `20260828_014304_25d94a`, T01C `20260828_003035_859fe5`, T04C `20260828_023122_76b87e`. Route ` --provider custom -m meta --yolo` max/OFF/TTFB900; transient 5-min wait same session.

## Verification Signatures

- T03: `pytest test_s10_partial_recompute.py -v -p no:cacheprovider --basetemp <nested-Windows-root>` ×2 + rerun 2 failing tests on nested root + direct DB/file/ffprobe probe + Ruff `F*` + mypy touched + full `test_s10*.py` ×2.
- T04A: focused ×2 fresh roots + T03/T01C/T02 regressions + direct API pass/fail probes + source sweep (no fixed arrays/sentinels) + OpenAPI + mypy + full suite.
- T01C-C5: nine-file mypy `Success: no issues found in 9 source files` + T01C ×2 + full suite + Ruff F* + diff-check + OpenAPI no drift.
- T04C: 2 fresh current-build runs (distinct roots/DBs/run IDs, same BUILD_ID from 7/7 validator), `BUILD_ID UoAHhbO6043uUWKNz2JTZ` (201 files), stop `0<verified<total`, PID lifecycle, decodable, SHA/size non-null, publication bound, affected-only, measured structural `REVIEW_REQUIRED`.
- Exit: J1-v4 13/13, full suite ×2 0 fail/skip, Ruff F* green, nine-file mypy green, diff-check green, alembic 1 head `a10b11c12d3e`, OpenAPI additive, TSC/ESLint/build 7/7, source sweeps (no color generator, no `.bin`, no fixed metrics), ledger/pid/cleanup checks.

## Pitfalls

- Path-budget is Windows `MAX_PATH` on `*.evidence.json.staging` sidecar, not missing `mkdir(parents=True)` — shortening reviewer root hides the bug.
- Mypy `unused-ignore` stale suppressions block other owners; route remaining errors to owning file.
- T04C harness must not tolerate missing recompute or 404/422 fallback, and must not allocate `--provider custom` without `-m meta`.
