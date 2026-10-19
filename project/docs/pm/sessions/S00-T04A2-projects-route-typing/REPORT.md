# S00-T04A2 - Implementation Report

**Status:** SUBMITTED

## Outcome

Resolved all 81 mypy errors in `app/api/routes/projects.py` (`python -m mypy app` → **0 errors**). No API payload, alias, status code, media behavior, or runtime behavior changed. No suppression, no casts, no mypy weakening. Only `app/api/routes/projects.py` + session LOG/REPORT were modified.

## Acceptance evidence

| AC | Status | Evidence |
|---|---|---|
| AC1 | PASS | `python -m mypy app` → `Success: no issues found in 41 source files` (baseline: `Found 81 errors in 1 file (checked 41 source files)`). Verified twice (after edits + in quality-baseline Gate 4, exit 0). |
| AC2 | PASS | `grep "type: ignore\|cast(\|# type:"` in `app/api/routes/projects.py` → none. `ReplacementConfig` built via `ReplacementMode.STATIC_ASSET` enum + `assetPath` alias (schema contract, `populate_by_name=True`); attribute mutation uses `.asset_path`. `SceneStatus(body.status)` after unchanged string-whitelist validation. No `[tool.mypy]` change (strict=true remains). |
| AC3 | PASS | Targeted tests unchanged and pass twice: `70 passed` (baseline 70 passed). Locks `assetPath` alias serialization (`test_preset_manager.py:203`), apply/auto-match behavior (`pose=="sitting"`), replacement-settings 200/404, trailing-slash 200s, auto-segment crop base64 PNG, dedupe. Real project JSON SHA256 before == after (`2dc14177a212=ad9a44d9b40a5842`, `4503582811e8=e1b9760e5160c06a`). No route paths/status codes/media types touched. |
| AC4 | PASS | `python -m pytest -q -m "not gpu and not sam2 and not integration"` → `160 passed, 8 skipped, 7 deselected` (twice, 12.93s / 12.88s). `python -m ruff check app tests` → `All checks passed!` (exit 0). |
| AC5 | PASS | `scripts/quality-baseline.ps1` run `20260803-140338`: Gates 1,2,3,4,5,7 PASS; Gate 6 (frontend eslint) FAIL with exactly the documented baseline errors (e2e/gpu-workflow.spec.ts + happy-path.spec.ts `no-require-imports`, AssemblyModal.tsx `no-unescaped-entities`, CompositeCanvas.tsx `set-state-in-effect`). Gate 4 flipped FAIL→PASS; Gate 6 unchanged. No frontend files touched. |
| AC6 | PASS | Only `app/api/routes/projects.py` added to pre-existing dirty set (`git diff --name-only` vs baseline list confirms). All 23 pre-existing modified + 14 untracked files preserved byte-for-byte. LOG.md complete (baseline + implementation + validation runs). REPORT.md complete. PM_REVIEW.md untouched. No commit/push. |

## Files changed

- `app/api/routes/projects.py` — typed annotations (`dict[str, object]`, helper/closure signatures, `_sort_key`, `worker`, `seg_progress`), `ReplacementMode`/`assetPath` schema-contract construction, runtime narrowing guards (`SelectionInput.width/height`, `BoundingBox.width/height`, `VideoMetadata`), `SceneStatus` enum assignment, `buf.tobytes()` b64, corrupt-gallery guard. +137/−84.
- `docs/pm/sessions/S00-T04A2-projects-route-typing/LOG.md` — appended (baseline, plan, implementation, validation runs 1–2, notes).
- `docs/pm/sessions/S00-T04A2-projects-route-typing/REPORT.md` — this report.
- No test files changed (existing tests already lock behavior — AC3).

## Validation (all commands run, real output)

```
python -m mypy app                                            → Success: no issues found in 41 source files
python -m pytest -q tests/test_preset_manager.py tests/test_api.py tests/test_trailing_slash.py \
  tests/test_delete_and_autosegment.py tests/test_list_projects.py tests/test_list_objects.py
                                                              → 70 passed (run 1), 70 passed (run 2)
python -m pytest -q -m "not gpu and not sam2 and not integration"
                                                              → 160 passed, 8 skipped, 7 deselected (run 1)
                                                              → 160 passed, 8 skipped, 7 deselected (run 2)
python -m ruff check app tests                                → All checks passed!
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
                                                              → run 20260803-140338; Gate 4 mypy PASS (was FAIL)
git diff --check                                              → exit 0 (CRLF warnings only, cosmetic)
git status --short                                            → only pre-existing changes + projects.py
```

## Deviations / limitations

- None. No schema/behavior expansion was required; stop conditions were not triggered.

## Out-of-scope findings (recorded, NOT fixed)

- Quality-baseline Gate 6 (frontend eslint) still fails on the documented pre-existing errors (e2e `no-require-imports`, `AssemblyModal` unescaped entities, `CompositeCanvas` setState-in-effect) — untouched per forbidden scope (frontend).
- `output/quality-baseline/` runs are git-ignored artifacts; no cleanup needed.

## Test pass/fail/not-run

- Pass: targeted route tests (70), full non-GPU suite (160 passed, 8 skipped, 7 deselected), ruff.
- Not-run: `tests/test_integration.py` (pre-existing SAM2 segfault — documented baseline; excluded by the required `-m "not gpu and not sam2 and not integration"` marker).

## Recommended PM decision

PENDING — ready for PM review.
