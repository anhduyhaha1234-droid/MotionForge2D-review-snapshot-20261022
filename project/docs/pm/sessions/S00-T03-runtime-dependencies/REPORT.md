# S00-T03 — Runtime dependencies and portable FFmpeg discovery

**Status:** SUBMITTED
**Date:** 2026-08-03
**Session:** docs/pm/sessions/S00-T03-runtime-dependencies
**Review round:** 2 (CHANGES_REQUESTED round 1 → corrected, re-submitted)

## Summary

MotionForge now discovers FFmpeg/ffprobe through a single shared authority
(`app/services/ffmpeg_utils.py`) with a documented, testable resolution
order. All machine-specific hard-coded paths were removed from `app/`.
Phase 2 dubbing dependencies (`edge-tts`, `openai-whisper`,
`deep-translator`) are declared in a new optional `dubbing` group and the
unconditional `edge_tts` module import is guarded with an actionable error.
README documents portable install/config instructions with no
machine-specific paths.

Round 2 adds the executable-suitability contract requested in PM review:
explicit overrides (and WinGet candidates) are validated as
executable-suitable (Windows: `.exe` suffix; POSIX: regular file + execute
bit), and invalid candidates raise an actionable error without falling
back.

## Acceptance criteria evidence

### AC1 — No hard-coded user-specific FFmpeg/ffprobe path in `app/`

Command (git-bash equivalent of TASK validation):

```
rg -n -F 'C:\Users\Admin' app
```

Before: 5 hits (audio_dubbing_service.py:448,460; scene_stitch_service.py:153;
scene_chunking_service.py:189,199).
After: **0 hits**. All `C:\Users\Admin\AppData\Local\Microsoft\WinGet\Links\...`
paths replaced by `LOCALAPPDATA`-derived resolution in `ffmpeg_utils.py`.

### AC2 — Three workflows use the shared discovery authority; media behavior unchanged

- `scene_chunking_service.py`, `scene_stitch_service.py`,
  `audio_dubbing_service.py` now call `find_ffmpeg()` / `find_ffprobe()` from
  `app.services.ffmpeg_utils`. Their `_find_ffmpeg`/`_find_ffprobe` methods are
  one-line delegators (kept to minimize diff and preserve the private API used
  by tests).
- `rg -n 'shutil.which' app/workflow/{scene_chunking,scene_stitch,audio_dubbing}_service.py`
  → no direct discovery calls remain.
- Every FFmpeg/ffprobe **command line** (slice `-c copy`, audio extract
  `-acodec copy`, concat, center-pan separation, atempo, remux) is byte-for-byte
  unchanged — only the binary path resolution changed.
- Targeted workflow tests: `30 passed` (17 pre-existing + 14 new discovery − 1
  removed/replaced = 30; see AC3).

### AC3 — Tests cover valid override, invalid override, PATH, WinGet/LOCALAPPDATA, not-found

`tests/test_ffmpeg_discovery.py` — 21 tests (19 run + 2 platform-scoped
skips on Windows), all machine-independent (tmp dirs + monkeypatched env;
no installed FFmpeg required):

| Scenario | Test |
|---|---|
| Valid `MOTIONFORGE_FFMPEG` override wins | `test_ffmpeg_override_wins` |
| Valid `MOTIONFORGE_FFPROBE` override wins | `test_ffprobe_override_wins` |
| Invalid override raises (no silent fallback) | `test_ffmpeg_invalid_override_raises`, `test_ffprobe_invalid_override_raises` |
| Text/non-executable override rejected, no fallback | `test_text_file_override_rejected` |
| Unsupported-suffix override rejected (Windows) | `test_unsupported_suffix_override_rejected` (skips on POSIX) |
| Non-executable override rejected (POSIX) | `test_non_executable_override_rejected_on_posix` (skips on Windows) |
| Missing override rejected even with valid PATH candidate | `test_missing_override_rejected_no_fallback` |
| PATH discovery (.exe) | `test_path_used_when_no_override` |
| PATH/PATHEXT discovery (.cmd on Windows) | `test_path_respects_pathexe_on_windows` |
| WinGet Links via LOCALAPPDATA | `test_winget_links_used` |
| No LOCALAPPDATA → skipped, not-found | `test_winget_links_ignored_without_localappdata` |
| Not-found actionable error | `test_not_found_error_is_actionable`, `test_ffprobe_not_found_error` |
| Suitability contract unit tests | `test_candidate_contract_exe_accepted`, `test_candidate_contract_missing_rejected`, `test_candidate_contract_text_file_rejected`, `test_candidate_contract_posix_execute_bit` |
| Module contract | `test_module_is_single_authority`, `test_winget_helper_returns_none_without_localappdata`, `test_portable_candidate_is_reserved` |

Executable-suitability contract (round 2, per PM review): `_env_override()`
now validates via `_is_executable_candidate()` — Windows requires the
supported `.exe` suffix; POSIX requires a regular file with execute
permission. A set-but-invalid override (text file, unsupported suffix,
missing file) raises actionable `FileNotFoundError` naming
`MOTIONFORGE_FFMPEG`/`MOTIONFORGE_FFPROBE` and never silently falls back
(verified even when a valid binary exists on PATH). `_winget_links_candidate()`
uses the same check. The candidate is never executed during discovery.

Command:
`python -m pytest -q tests/test_ffmpeg_discovery.py tests/test_scene_chunk_stitch.py
tests/test_audio_dubbing.py tests/test_video_slicing.py --cache-clear`
→ **36 passed, 2 skipped, 5 warnings in 2.34s**.

Note on portability discovery: on Windows `shutil.which` only matches
PATHEXT extensions (`.EXE` normalized uppercase); a no-extension `ffprobe`
file is NOT findable via PATH on Windows. Tests assert resolved-path equality
to stay platform-neutral. `.cmd` is PATH-discoverable (PATHEXT) but is NOT a
supported override suffix — the override contract requires `.exe` on Windows.

### AC4 — Runtime imports absent from package contract declared in correct optional group / guarded

- `pyproject.toml`: new optional group
  ```
  dubbing = [
      "edge-tts>=7.0",
      "openai-whisper>=20240601",
      "deep-translator>=1.11",
  ]
  ```
  Core dependencies unchanged (Phase 1 stays minimal).
- `audio_dubbing_service.py`: module-level `import edge_tts` is now guarded —
  absence raises `ImportError("edge-tts is required for audio dubbing (Phase 2
  feature). Install it with: pip install -e \".[dubbing]\"")`. Verified by
  simulating absence via a `sys.meta_path` blocker: guard raises correctly.
- `whisper` (in `transcribe()`) and `deep_translator` (in
  `translate_segments()`) are lazy-imported — now documented in README
  "Dubbing dependencies (Phase 2, optional)".

### AC5 — README clean, portable install/config without machine-specific paths

- "Installing FFmpeg" subsection: winget / apt / brew / manual, no hard-coded
  user path.
- "FFmpeg configuration" section: full resolution order + `MOTIONFORGE_FFMPEG` /
  `MOTIONFORGE_FFPROBE` env vars in the configuration table; override validity
  contract documented (Windows: `.exe`; POSIX: regular file + execute bit;
  invalid override raises, never falls back).
- Quick Start: optional `pip install -e ".[dubbing]"` + SAM 2 / models marked
  optional.
- "Dubbing dependencies (Phase 2, optional)" section.
- Verified no `C:\Users\Admin` or `/c/Users/Admin` in README diff.

### AC6 — Targeted tests, full non-GPU tests, Ruff pass; type/build baseline has no new failure

```
python -m pytest -q -m "not gpu and not sam2 and not integration" --cache-clear
160 passed, 8 skipped, 7 deselected, 14 warnings in 12.78s   (round 1: 154 passed, 6 skipped, 7 deselected)
python -m ruff check app tests   -> All checks passed!
python -m mypy app               -> Found 121 errors in 15 files (baseline: 123 errors in 16 files)
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
  Gate 1 env PASS | Gate 2 tests PASS | Gate 3 lint PASS | Gate 4 typing FAIL (121)
  | Gate 5 tsc PASS | Gate 6 eslint FAIL | Gate 7 build PASS
```

Mypy delta: per-error-line diff between baseline run `20260803-120140` and
this run is **IDENTICAL** — no new mypy errors attributable to this task
(the 7 `audio_dubbing_service.py` `Missing type arguments for generic type
"dict"` errors are pre-existing, same file:line in the baseline log). The
123→121 count delta is the `Found N errors` summary line, not per-error
lines. Gates 5/6/7 frontend logs identical to baseline (eslint FAIL is the
documented pre-existing baseline).

`git diff --check` → exit 0 (CRLF warnings are the documented cosmetic
baseline issue).

### AC7 — Existing user/S00 changes and production data untouched; report/log complete

- Pre-existing user-modified files retain their exact pre-work diffs
  (git diff --stat identical to session-start snapshot):
  `.gitignore`, `app/services/preset_manager.py`, `app/workflow/channel_service.py`,
  `channels.json`, `tests/test_channel_workspace.py`, `tests/test_preset_manager.py`.
- channels.json SHA256 `dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555`
  — untouched by this task (its diff is the pre-existing user change).
- 6 untracked `presets/characters/dan_choi_*.png` assets still present.
- LOG.md append-only complete; REPORT.md SUBMITTED; PM_REVIEW.md untouched;
  no commit, no push.

## Changed files

| File | Change |
|---|---|
| `app/services/ffmpeg_utils.py` | Rewritten as single discovery authority (env override → PATH → WinGet/LOCALAPPDATA → portable → actionable error); round 2: added `_is_executable_candidate()` cross-platform suitability contract (Windows `.exe`; POSIX regular file + execute bit), applied in `_env_override()` and `_winget_links_candidate()` |
| `app/workflow/scene_chunking_service.py` | Removed hard-coded paths + shutil; `_find_ffmpeg`/`_find_ffprobe` delegate to shared authority |
| `app/workflow/scene_stitch_service.py` | Same (ffmpeg) |
| `app/workflow/audio_dubbing_service.py` | Same + guarded `edge_tts` import |
| `pyproject.toml` | Added optional `dubbing` group |
| `README.md` | FFmpeg install/config section (incl. override validity contract), env vars, dubbing extra docs (dependency/install/FFmpeg sections only) |
| `tests/test_ffmpeg_discovery.py` | NEW — 21 discovery/suitability tests (19 run + 2 platform-scoped skips on Windows), machine-independent |
| `docs/pm/sessions/S00-T03-runtime-dependencies/LOG.md` | Session log (append-only; round 2 correction entry) |
| `docs/pm/sessions/S00-T03-runtime-dependencies/REPORT.md` | This report |

## Deviations / limitations

- Kept the one-line `_find_ffmpeg`/`_find_ffprobe` delegator methods on the
  three services instead of deleting them, so the private API surface used by
  existing tests (`test_video_slicing.py:91` calls `svc._find_ffprobe()`) stays
  stable. They add no discovery logic.
- Round 2: the executable-suitability contract is deliberately
  conservative — on Windows only `.exe` is accepted (documented; other
  suffixes intentionally unsupported). The check is suffix/permission based
  (matching how the OS itself treats executability) and never executes the
  candidate, per the PM requirement. Two tests are platform-scoped with
  `pytest.skip` on the opposite OS (unsupported-suffix applies on Windows;
  execute-bit applies on POSIX).
- Removed the previous `C:\ffmpeg\bin` and `C:\Program Files\FFmpeg\bin`
  checks from `ffmpeg_utils.py` (they were guesses, not a contract). The
  portable app-managed location (target-contract item 4) is reserved with a
  documented hook (`_portable_candidate`) because no such contract exists in
  the repo yet — README documents this explicitly.
- `scripts/setup.sh` still contains `/c/Users/Admin/...` WinGet references —
  OUT OF SCOPE (not in allowed write scope). Flagged for a future task:
  it should use `$LOCALAPPDATA` for portability.
- pyproject `dubbing` group uses loose version bounds (`>=`) matching the
  installed versions; no lock update performed (forbidden by task).

## Out-of-scope findings

- `scripts/setup.sh:26,51` — machine-specific `C:\Users\Admin` FFmpeg path
  fallbacks. Not in allowed write scope; recommend a follow-up task to make
  the setup script portable via `LOCALAPPDATA`.

## Tests: pass / fail / not-run

- Targeted (4 files): **36 passed, 2 skipped** — PASS (round 1: 30 passed)
- Discovery file alone: **19 passed, 2 skipped** — PASS
- Full non-GPU (`-m "not gpu and not sam2 and not integration"`): **160 passed, 8 skipped, 7 deselected** — PASS (round 1: 154/6)
- Ruff (`app tests`): **All checks passed** — PASS
- Mypy (`app`): **121 errors in 15 files — identical per-error set to approved baseline** — baseline FAIL, no new errors
- quality-baseline.ps1: gates 1,2,3,5,7 PASS; gates 4,6 FAIL (approved baseline) — no regression
- git diff --check: PASS (exit 0)
- Not run: GPU/SAM2/integration tests (excluded by marker, per protocol and pre-existing SAM2 segfault in test_integration.py)
