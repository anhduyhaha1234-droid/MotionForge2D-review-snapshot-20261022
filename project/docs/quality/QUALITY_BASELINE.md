# MotionForge 2D — Quality Baseline

**Generated:** 2026-08-03 by `scripts/quality-baseline.ps1`
**Baseline type:** first reproducible quality snapshot (S00-T02)
**Runner exit code:** 1 (non-zero is EXPECTED — baseline contains known failures; failures are recorded as data, not fixed here)

## How to re-run

From anywhere (repo root is auto-detected from the script location):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
```

- Each run creates a new timestamped directory under `output/quality-baseline/<run-id>/`
  with per-gate `.log`/`.err.log` files and a `summary.json` (machine-readable).
- All seven gates are always recorded; runnable gates execute, while
  preflight-blocked gates are recorded as `SKIPPED/PREFLIGHT_BLOCKED`.
- Exit code: `0` only if every required gate passes; `1` if any gate FAILs;
  `2` if preflight blocks the run.
- Generated artifacts under `output/quality-baseline/` are git-ignored.

## Tool versions (2026-08-03)

| Tool | Version |
|---|---|
| Python | 3.11.9 |
| Node | v26.4.0 |
| npm | 11.17.0 |
| Frontend deps | installed (`node_modules` present; tsc/eslint/next binaries available) |

## Gate results — run 1 (`20260803-120140`)

| Gate | Command | Status | Exit | Duration |
|---|---|---|---|---|
| 1. Environment/Preflight | version checks + frontend deps | PASS | 0 | 0s |
| 2. Python tests | `python -m pytest -q -m "not gpu and not sam2 and not integration"` | PASS | 0 | 14.38s |
| 3. Python lint | `python -m ruff check app tests` | PASS | 0 | 0.06s |
| 4. Python typing | `python -m mypy app` | **FAIL** | 1 | 0.52s |
| 5. Frontend typecheck | `npx tsc --noEmit` (frontend/) | PASS | 0 | 1.55s |
| 6. Frontend lint | `npm run lint` (frontend/) | **FAIL** | 1 | 3.12s |
| 7. Frontend build | `npm run build` (frontend/) | PASS | 0 | 5.34s |

## Gate results — run 2 (`20260803-120105`)

| Gate | Command | Status | Exit | Duration |
|---|---|---|---|---|
| 1. Environment/Preflight | version checks + frontend deps | PASS | 0 | 0s |
| 2. Python tests | `python -m pytest -q -m "not gpu and not sam2 and not integration"` | PASS | 0 | 13.87s |
| 3. Python lint | `python -m ruff check app tests` | PASS | 0 | 0.06s |
| 4. Python typing | `python -m mypy app` | **FAIL** | 1 | 0.53s |
| 5. Frontend typecheck | `npx tsc --noEmit` (frontend/) | PASS | 0 | 1.54s |
| 6. Frontend lint | `npm run lint` (frontend/) | **FAIL** | 1 | 3.06s |
| 7. Frontend build | `npm run build` (frontend/) | PASS | 0 | 5.39s |

## Known failures (baseline data — NOT fixed in this task)

### Gate 4 — Python typing (`mypy app`): FAIL, 123 errors in 16 files (41 checked)
Representative errors (full list in run logs):
- `app/api/routes/projects.py:1943-1970` — `ReplacementConfig` mode/asset_path type mismatches
  (`Argument "mode" to "ReplacementConfig" has incompatible type "str"; expected "ReplacementMode"`,
  `Unexpected keyword argument "asset_path"; did you mean "assetPath"?`,
  `Incompatible types in assignment`).
- `app/api/app.py:36` — `Missing type arguments for generic type "dict"`.
- Additional errors across 14 more files (see `output/quality-baseline/<run-id>/Gate_4_-_Python_typing.log`).

### Gate 6 — Frontend lint (`npm run lint` = eslint): FAIL
Representative errors (full list in run logs):
- `frontend/e2e/gpu-workflow.spec.ts:11` and `frontend/e2e/happy-path.spec.ts:11` —
  `@typescript-eslint/no-require-imports` (require() style import forbidden).
- `frontend/src/components/AssemblyModal.tsx:113` — 4× `react/no-unescaped-entities` (`"` should be escaped).
- `frontend/src/components/CompositeCanvas.tsx:157` — `Error: Calling setState synchronously within an effect` (React 19 rule).
- Warnings (non-blocking): unused vars in `ChannelDashboard.tsx:5`, `CompositeCanvas.tsx:116`, and others.

## Warnings observed (non-blocking)

- Python tests: Pydantic serializer warnings (`PydanticSerializationUnexpectedValue`,
  field `mode` = `static_asset`) — pre-existing.
- `git diff --check` emits CRLF warnings on Windows for edited files — cosmetic.

## Notes

- Gate 2 (Python tests) summary: `141 passed, 6 skipped, 7 deselected` (matches S00-T01 approved baseline).
- No gate was skipped or made optional; all 7 gates ran in both official runs.
- No source, dependency, test or lint/type/build behavior was modified by this task.
- Production data (`channels.json`, character assets) untouched — verified via `git status`.
