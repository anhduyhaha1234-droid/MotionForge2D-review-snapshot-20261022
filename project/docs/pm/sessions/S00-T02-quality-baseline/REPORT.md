# S00-T02 Report — Reproducible quality baseline runner

**Status:** SUBMITTED
**Session:** `docs/pm/sessions/S00-T02-quality-baseline`
**Date:** 2026-08-03

## 1. Summary

Built `scripts/quality-baseline.ps1` — a single PowerShell command that runs all
seven required quality gates sequentially, captures each gate's command,
stdout/stderr, exit code, duration and status independently, never stops at the
first failure, and writes machine-readable per-run artifacts under
`output/quality-baseline/<run-id>/`. The runner exits non-zero because the
current baseline contains real failures (mypy 123 errors, eslint errors);
those failures are recorded as baseline data, NOT fixed (per task scope).

## 2. Files changed (tracked)

| File | Change | Scope |
|---|---|---|
| `scripts/quality-baseline.ps1` | NEW: 7-gate quality runner (PS 5.1 compatible) | Allowed |
| `.gitignore` | Added `output/quality-baseline/` (generated artifacts) | Allowed |
| `docs/quality/QUALITY_BASELINE.md` | NEW: exact baseline results, versions, known failures, re-run instructions | Allowed |
| `docs/pm/sessions/S00-T02-quality-baseline/LOG.md` | Session log (append-only) | Allowed |
| `docs/pm/sessions/S00-T02-quality-baseline/REPORT.md` | This report | Allowed |

**Preserved (untouched):** all S00-T01-approved changes (`app/services/preset_manager.py`,
`app/workflow/channel_service.py`, `tests/test_channel_workspace.py`,
`tests/test_preset_manager.py`), `channels.json` (pre-existing pollution, not
modified), `presets/characters/*.png` user assets, all frontend source,
`pyproject.toml`, `frontend/package.json`, lockfiles, PRD/MP/TASK.md/PM_REVIEW.md.

## 3. Runner design (isolation/robustness)

- **Repo root resolution**: `Split-Path -Parent $MyInvocation.MyCommand.Path` →
  `scripts/` parent; works from any cwd (verified AC1).
- **Per-gate record**: command, stdout log, stderr log, exit code, duration,
  status (`PASS`/`FAIL`/`SKIPPED/PREFLIGHT_BLOCKED`), log path — all in
  `summary.json` plus per-gate `.log`/`.err.log` files.
- **Continue-on-fail**: all seven gates are always recorded; runnable gates
  execute, while preflight-blocked gates are recorded as
  `SKIPPED/PREFLIGHT_BLOCKED`. A failing gate never prevents later gates.
- **Exit code**: `0` only if all required gates pass; `1` if any FAIL;
  `2` if preflight blocked. Report artifacts are still fully written.
- **No auto-install**: preflight only checks tool/dependency presence.
- **No secrets/env dump**: only tool versions are recorded.
- **No absolute machine paths in tracked docs** (`QUALITY_BASELINE.md` uses
  relative commands; run logs live in git-ignored `output/`).
- Windows PS 5.1 fixes (documented in LOG.md): no `ProcessStartInfo.ArgumentList`
  (uses `$psi.Arguments` + quoting helper), `$Args` param name collision,
  `-and` line continuation, `.cmd` absolute paths, UTF-8 no-BOM JSON,
  async stdout/stderr reads.

## 4. Validation evidence

### AC1 — One command works from repo root or elsewhere
```
$ powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1   # from repo root → OK
$ cd C:\Users\Admin && powershell -NoProfile -ExecutionPolicy Bypass -File C:/Users/Admin/MotionForge2D/scripts/quality-baseline.ps1
repo root detected: C:\Users\Admin\MotionForge2D → run 20260803-120225, all 7 gates present
```
**PASS.**

### AC2 — All 7 gates have per-gate records; failure doesn't block later gates
Both official runs + cwd-variant run contain exactly 7 gate records, each with
command, exit code, duration, status, log path. Gate 4 FAIL → Gates 5/6/7 still
ran and produced results. **PASS.**

### AC3 — Exit 0 only when all required gates pass
`$firstExit = 1`, `$secondExit = 1` — non-zero because Gate 4 and Gate 6 FAIL.
This is the expected behavior for a failing baseline (not a runner bug).
**PASS.**

### AC4 — Generated artifacts only under output/quality-baseline/ and ignored
All logs/summaries are under `output/quality-baseline/<run-id>/`;
`git check-ignore output/quality-baseline/20260803-120105/summary.json` → ignored.
**PASS.**

### AC5 — QUALITY_BASELINE.md records exact results
Written with timestamp, tool versions (Python 3.11.9, Node v26.4.0, npm
11.17.0), per-gate status/exit/duration for both official runs, honest known
failures (mypy 123 errors; eslint errors with file:line), warnings, and
re-run instructions. No false green claims. **PASS.**

### AC6 — Two runs succeed as orchestration; full reports; no production changes
Run 1 (`20260803-120140`): 7 gates recorded, overall FAIL exit 1.
Run 2 (`20260803-120105`): 7 gates recorded, overall FAIL exit 1.
`git status --short` shows only task files + pre-existing S00-T01/user changes;
no production source/data modified. **PASS.**

### AC7 — Script syntax/error handling tested; git diff --check passes
- Syntax: script parsed and executed successfully (5 development iterations
  fixed PS 5.1 issues; final version runs clean).
- Error handling: gate start-failure, timeout, preflight-blocked paths all
  produce records without aborting the run; JSON summaries are valid UTF-8.
- `git diff --check` → exit 0 (only CRLF warnings on Windows). **PASS.**

## 5. Exact gate results (both official runs)

### Run 1 — `20260803-120140` (exit 1)
| Gate | Status | Exit | Duration |
|---|---|---|---|
| 1. Environment/Preflight | PASS | 0 | 0s |
| 2. Python tests | PASS | 0 | 14.38s |
| 3. Python lint | PASS | 0 | 0.06s |
| 4. Python typing | FAIL | 1 | 0.52s |
| 5. Frontend typecheck | PASS | 0 | 1.55s |
| 6. Frontend lint | FAIL | 1 | 3.12s |
| 7. Frontend build | PASS | 0 | 5.34s |

### Run 2 — `20260803-120105` (exit 1)
| Gate | Status | Exit | Duration |
|---|---|---|---|
| 1. Environment/Preflight | PASS | 0 | 0s |
| 2. Python tests | PASS | 0 | 13.87s |
| 3. Python lint | PASS | 0 | 0.06s |
| 4. Python typing | FAIL | 1 | 0.53s |
| 5. Frontend typecheck | PASS | 0 | 1.54s |
| 6. Frontend lint | FAIL | 1 | 3.06s |
| 7. Frontend build | PASS | 0 | 5.39s |

Consistent across both runs — reproducible baseline.

## 6. Known failures (baseline data, not fixed — out of scope)

- **Gate 4 — mypy**: 123 errors in 16 files (41 checked). Representative:
  `app/api/routes/projects.py` ReplacementConfig `mode`/`asset_path` typing
  (lines 1943–1970), `app/api/app.py:36` missing dict type args.
- **Gate 6 — eslint**: `no-require-imports` in `frontend/e2e/*.spec.ts:11`,
  `react/no-unescaped-entities` in `AssemblyModal.tsx:113`,
  setState-in-effect in `CompositeCanvas.tsx:157`, plus unused-var warnings
  (`ChannelDashboard.tsx:5`, `CompositeCanvas.tsx:116`).
- Non-blocking: Pydantic serializer warnings in pytest; CRLF warnings in
  `git diff --check` on Windows.

## 7. Deviations / limitations

- `powershell` on this machine is Windows PowerShell 5.1; the runner was built
  and verified against it (no PS 7 dependency). Documented in LOG.md.
- The task's example captures `$LASTEXITCODE` inside a PowerShell session; here
  `$LASTEXITCODE` was captured via `echo $?` after a non-piped invocation
  (`$firstExit = 1`, `$secondExit = 1`), equivalent semantics.
- Official validation run 1 id is `20260803-120140` (the non-piped run);
  earlier debug runs exist under `output/quality-baseline/` from development —
  all git-ignored.
- `QUALITY_BASELINE.schema.json` was NOT created (schema for summary.json is
  self-describing in the script; optional per task).

## 8. Out-of-scope findings

- mypy and eslint failures are substantial and pre-existing; they are the
  natural first targets for the next baseline-improvement tasks (NOT S00-T02).
- `npm`/`npx` required `.cmd` absolute-path resolution under ProcessStartInfo —
  environment quirk recorded for future tasks using PowerShell runners.

## 9. Status

**SUBMITTED** — awaiting PM review. No commit/push; no `PM_REVIEW.md` edit;
no S00-T03/S00-T04 started.
