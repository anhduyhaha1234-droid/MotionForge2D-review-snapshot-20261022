# S00-T03 — Execution Log

## Session metadata

- Task: S00-T03 — Runtime dependencies and portable FFmpeg discovery
- Session started: 2026-08-03
- Status: IN PROGRESS

## Required reading checklist

- [x] docs/pm/SESSION_PROTOCOL.md
- [x] docs/pm/sessions/S00-T03-runtime-dependencies/TASK.md
- [x] pyproject.toml
- [x] README.md (install/run sections)
- [x] app/services/ffmpeg_utils.py
- [x] app/workflow/scene_chunking_service.py
- [x] app/workflow/scene_stitch_service.py
- [x] app/workflow/audio_dubbing_service.py
- [x] tests/test_scene_chunk_stitch.py
- [x] tests/test_audio_dubbing.py
- [x] tests/test_video_slicing.py
- [x] docs/quality/QUALITY_BASELINE.md
- [x] tests/conftest.py (optional — FFmpeg PATH behavior)

## Protected pre-existing user changes (git status --short before work)

```
 M .gitignore
 M app/services/preset_manager.py
 M app/workflow/channel_service.py
 M channels.json
 M tests/test_channel_workspace.py
 M tests/test_preset_manager.py
?? automation/
?? docs/CODEBASE_STRATEGY_REVIEW.md
?? docs/MASTER_PLAN_V1.md
?? docs/PRODUCT_REQUIREMENTS_V2.md
?? docs/pm/
?? docs/quality/
?? presets/characters/dan_choi_*.png (6 files)
?? scripts/quality-baseline.ps1
```

None of these files are in the allowed write scope of this task. They will NOT be touched.
Snapshot of user-modified files (git diff) preserved for end-of-session comparison.

## Baseline commands + results (BEFORE any change)

### 1. rg scan for machine-specific paths / private discovery (validation command)

Command (git-bash equivalent of TASK.md's PowerShell `rg -n "C:\\Users\\Admin|_find_ffmpeg|_find_ffprobe" app`):

```
rg -n -F 'C:\Users\Admin' app
```

Result — 5 hard-coded user-specific FFmpeg/ffprobe paths:

```
app/workflow/audio_dubbing_service.py:448  win_path = Path(r"C:\Users\Admin\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe")
app/workflow/audio_dubbing_service.py:460  win_path = Path(r"C:\Users\Admin\AppData\Local\Microsoft\WinGet\Links\ffprobe.exe")
app/workflow/scene_stitch_service.py:153   win_path = Path(r"C:\Users\Admin\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe")
app/workflow/scene_chunking_service.py:189 win_path = Path(r"C:\Users\Admin\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe")
app/workflow/scene_chunking_service.py:199 win_path = Path(r"C:\Users\Admin\AppData\Local\Microsoft\WinGet\Links\ffprobe.exe")
```

Private discovery copies (`_find_ffmpeg`/`_find_ffprobe`): 14 occurrences across 3 files
(9 `_find_ffmpeg`, 5 `_find_ffprobe`; each file defines its own private copy).

### 2. Targeted tests (3 direct workflow test files) — BEFORE

```
python -m pytest -q tests/test_scene_chunk_stitch.py tests/test_audio_dubbing.py tests/test_video_slicing.py --cache-clear
```

Result: `17 passed, 5 warnings in 2.46s` (exit 0). 5 warnings = PySceneDetect deprecation warning (pre-existing, unrelated).

### 3. Environment facts

- `edge_tts` 7.2.7, `openai-whisper` 20250625, `deep-translator` 1.11.4 are INSTALLED in this machine's site-packages but NOT declared in pyproject.toml (neither core nor optional).
- `audio_dubbing_service.py` has a module-level `import edge_tts` (unconditional) — import at `from app.workflow.audio_dubbing_service import AudioDubbingService` fails if edge-tts absent.
- `transcribe()` lazily imports `whisper`; `translate_segments()` lazily imports `deep_translator` — already guarded by lazy import, but NOT documented/declared.
- pyproject has only `dev` and `sam2` optional groups. No `dubbing` group.

## Plan (≤7 steps)

1. Rewrite `app/services/ffmpeg_utils.py` as the single discovery authority (env override → PATH → WinGet/LOCALAPPDATA → portable location → actionable error; validate override, no silent fallback).
2. Refactor `scene_chunking_service.py`, `scene_stitch_service.py`, `audio_dubbing_service.py` to use the shared authority; delete private `_find_ffmpeg`/`_find_ffprobe` and hard-coded `C:\Users\Admin` paths; media commands untouched.
3. Declare Phase 2 dubbing dependencies as optional group `dubbing` in pyproject.toml; guard module-level `edge_tts` import with actionable error; document whisper/deep-translator lazy imports.
4. README: portable FFmpeg install/config instructions (env override, PATH, WinGet, portable dir), no machine-specific paths; document `dubbing` extra.
5. Add targeted tests (tests/test_ffmpeg_discovery.py) for valid/invalid override, PATH, WinGet/LOCALAPPDATA, not-found; keep machine-independent (no reliance on installed FFmpeg).
6. Run targeted tests, full non-GPU suite, ruff, mypy, quality-baseline.ps1, git diff --check.
7. Compare deltas vs QUALITY_BASELINE.md (123 mypy errors / eslint FAIL / others PASS), fill REPORT.md SUBMITTED, append LOG.md, STOP.

## Execution log

(append-only below)

### 2026-08-03 — Implementation

1. Rewrote `app/services/ffmpeg_utils.py` as the single discovery authority:
   resolution order = env override (`MOTIONFORGE_FFMPEG`/`MOTIONFORGE_FFPROBE`,
   validated, no silent fallback) → `shutil.which` (PATH) → WinGet Links via
   `LOCALAPPDATA` → portable location (reserved, no contract yet) → actionable
   FileNotFoundError with install guidance (never a guessed username path).

2. Refactored the three workflow services to delegate to the shared authority:
   - `scene_chunking_service.py`: removed `shutil` import + hard-coded
     `C:\Users\Admin\...WinGet\Links` paths; `_find_ffmpeg`/`_find_ffprobe` now
     thin wrappers calling `find_ffmpeg`/`find_ffprobe`.
   - `scene_stitch_service.py`: same (ffmpeg only).
   - `audio_dubbing_service.py`: same; also converted module-level `import edge_tts`
     into a guarded import with actionable error (`pip install -e ".[dubbing]"`).

3. `pyproject.toml`: added optional `dubbing` group
   (`edge-tts>=7.0`, `openai-whisper>=20240601`, `deep-translator>=1.11`).
   Core dependencies unchanged.

4. `README.md`: portable FFmpeg install/configuration section (resolution order,
   env overrides, no machine-specific paths), documented `dubbing` extra +
   lazy imports (whisper, deep-translator).

5. New `tests/test_ffmpeg_discovery.py` (14 tests): valid override, invalid
   override (no silent fallback), PATH (.exe + .cmd/PATHEXT), WinGet/LOCALAPPDATA,
   not-found actionable error, module contract. Machine-independent — uses tmp
   dirs and monkeypatched env, no installed FFmpeg required.

### 2026-08-03 — Targeted test runs

Run 1 (before fixes): `17 passed` baseline (3 files); new discovery file first
run: 2 PATH-test failures (Windows `shutil.which` uppercases `.EXE`; no-extension
names not PATHEXT-resolvable on Windows). Fixed tests to compare resolved paths +
case-insensitive names, and switched unix-name case to `.cmd`.

Run 2 (final, 4 files):
```
python -m pytest -q tests/test_ffmpeg_discovery.py tests/test_scene_chunk_stitch.py tests/test_audio_dubbing.py tests/test_video_slicing.py --cache-clear
30 passed, 5 warnings in 2.42s
```
(5 warnings = pre-existing PySceneDetect deprecation.)

Guard verification (edge_tts absence simulated via sys.meta_path blocker):
module import raises `ImportError: edge-tts is required for audio dubbing
(Phase 2 feature). Install it with: pip install -e ".[dubbing]"` ✓

### 2026-08-03 — Full validation (AFTER changes)

```
python -m pytest -q -m "not gpu and not sam2 and not integration" --cache-clear
154 passed, 6 skipped, 7 deselected, 14 warnings in 12.90s   (baseline: 141 passed, 6 skipped, 7 deselected)
python -m ruff check app tests        -> All checks passed!
python -m mypy app                    -> Found 121 errors in 15 files (checked 41 source files)
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
  Gate 1 env PASS, Gate 2 tests PASS, Gate 3 lint PASS,
  Gate 4 typing FAIL (121 errors — baseline 123), Gate 5 tsc PASS,
  Gate 6 eslint FAIL (unchanged), Gate 7 build PASS
```

Mypy delta vs baseline: per-error-line diff between baseline run
`20260803-120140` and this run `20260803-131950` is IDENTICAL — the 7
`audio_dubbing_service.py` `Missing type arguments for generic type "dict"`
errors are PRE-EXISTING (present in baseline log, same line numbers). No new
mypy errors attributable to this task. Error-count delta (123→121) is the
`Found N errors` header, not per-error lines.

rg scan after changes:
```
rg -n -F 'C:\Users\Admin' app   -> NONE
rg -n '_find_ffmpeg|_find_ffprobe' app -> only thin delegators (one line each) calling shared authority
rg -n 'shutil.which' app/workflow/{scene_chunking,scene_stitch,audio_dubbing}_service.py -> NONE
```

git diff --check: exit 0 (CRLF warnings are the documented cosmetic baseline).

### 2026-08-03 — AC7 / data safety

- Pre-existing user-modified files retain their exact pre-work diffs:
  `.gitignore`, `app/services/preset_manager.py`, `app/workflow/channel_service.py`,
  `channels.json`, `tests/test_channel_workspace.py`, `tests/test_preset_manager.py`
  (git diff --stat identical to session-start snapshot).
- channels.json SHA256: dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555
  (untouched by this task — 224-line diff is the pre-existing user change).
- 6 untracked `presets/characters/dan_choi_*.png` assets still present.
- Changed files (allowed scope only): README.md, app/services/ffmpeg_utils.py,
  app/workflow/audio_dubbing_service.py, app/workflow/scene_chunking_service.py,
  app/workflow/scene_stitch_service.py, pyproject.toml + new
  tests/test_ffmpeg_discovery.py + session LOG.md/REPORT.md.
- No commit, no push, PM_REVIEW.md untouched.

### 2026-08-03 — CORRECTION (PM review round 1, CHANGES_REQUESTED)

PM finding: `_env_override()` only checked `Path.is_file()`, so a regular text
file was accepted as an FFmpeg executable; tests proved existence only, not
executable suitability.

Fix implemented (scope: app/services/ffmpeg_utils.py, tests/test_ffmpeg_discovery.py,
README.md FFmpeg section, LOG/REPORT only):

1. New `_is_executable_candidate(path)` cross-platform suitability contract in
   `ffmpeg_utils.py` — never executes the candidate:
   - Windows (`os.name == "nt"`): supported executable suffix required;
     the only supported suffix is `.exe` (`.bat`/`.cmd`/`.ps1`/no suffix
     intentionally NOT accepted — FFmpeg/ffprobe are native executables).
   - POSIX: regular file (`is_file()`) AND execute permission
     (`os.access(path, os.X_OK)`).
2. `_env_override()` now calls `_is_executable_candidate`; a set-but-invalid
   override raises actionable FileNotFoundError (message names the platform
   contract) and never falls back. `_winget_links_candidate()` also uses the
   same check. Module docstring + README updated to document the contract.
3. Tests updated:
   - Valid override tests + PATH .exe test + WinGet test now build candidates
     via `_make_platform_executable()` (satisfies current platform contract:
     .exe suffix on Windows, chmod +x on POSIX).
   - New `TestInvalidOverrideCandidate` (4 tests): text/non-executable
     override rejected (no fallback to a valid PATH candidate), unsupported
     suffix rejected on Windows, missing override rejected even with valid
     PATH candidate.
   - New `_is_executable_candidate` unit tests (4): .exe accepted, missing
     rejected, text-file-per-platform rejected, POSIX execute-bit behavior.
   - 2 platform-scoped tests skip on the opposite OS (unsupported-suffix
     applies on Windows; execute-bit applies on POSIX).
   - `test_path_with_cmd_name` renamed `test_path_respects_pathexe_on_windows`
     with docstring clarifying .cmd is PATH/PATHEXT discovery only, NOT a
     supported override suffix.

Discovery order, media commands, APIs, dependency scope, frontend: UNCHANGED.

### 2026-08-03 — CORRECTION validation results

```
python -m pytest -q tests/test_ffmpeg_discovery.py --cache-clear
19 passed, 2 skipped in 0.11s        (2 skips = platform-scoped, Windows)

python -m pytest -q tests/test_ffmpeg_discovery.py tests/test_scene_chunk_stitch.py tests/test_audio_dubbing.py tests/test_video_slicing.py --cache-clear
36 passed, 2 skipped, 5 warnings in 2.34s

python -m pytest -q -m "not gpu and not sam2 and not integration" --cache-clear
160 passed, 8 skipped, 7 deselected, 14 warnings in 12.78s
   (prior round: 154 passed, 6 skipped — +6 discovery tests, +2 platform skips)

python -m ruff check app tests
All checks passed!

python -m mypy app
Found 121 errors in 15 files (checked 41 source files)
per-error diff vs approved baseline run 20260803-120140 -> IDENTICAL (no new errors)

powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1  (run 20260803-132830)
Gate 1 env PASS | Gate 2 tests PASS | Gate 3 lint PASS | Gate 4 typing FAIL (121, baseline)
| Gate 5 tsc PASS | Gate 6 eslint FAIL (baseline) | Gate 7 build PASS
-- same statuses as prior round; no regression.

git diff --check -> exit 0 (CRLF warnings only, cosmetic baseline)
rg -n -F 'C:\Users\Admin' app -> NONE (AC1 still satisfied)
```

Test-isolation note: all new tests machine-independent (tmp dirs + monkeypatched
env; no installed FFmpeg required). Existing user changes untouched (git status
identical to session-start snapshot); channels.json SHA256 unchanged
(dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555).
