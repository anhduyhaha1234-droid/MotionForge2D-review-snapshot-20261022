# S00-T01 Session Log — Baseline & Isolation

Session: `docs/pm/sessions/S00-T01-baseline-isolation`
Task: Isolate test data from production-root storage
Status: IN PROGRESS

## 2026-08-03 — Baseline inventory & pollution proof

### Required reading completed
- [x] `docs/pm/SESSION_PROTOCOL.md`
- [x] `docs/CODEBASE_STRATEGY_REVIEW.md`
- [x] `app/services/preset_manager.py`
- [x] `tests/test_preset_manager.py`
- [x] Channel storage modules found via `rg` (scope: `app/`, `tests/`):
  - `app/workflow/channel_service.py` — `ChannelService` writes `config.project_root / "channels.json"`
  - `app/api/routes/projects.py` — channel endpoints construct `ChannelService(config)` from `get_config()`; preset endpoints use `get_preset_manager()` singleton
  - `app/services/preset_manager.py` — `get_preset_manager()` singleton rooted at `deps._config.project_root / "presets" / "characters"`; `ensure_assets()` writes PNGs
  - `tests/test_channel_workspace.py` — direct `ChannelService(app_config)` → writes ROOT `channels.json`
  - `tests/test_preset_manager.py` — endpoint tests use `client` fixture (`_patch_project_root`), but `test_reference_packs_endpoint` calls `get_preset_manager()` singleton directly
- [x] `pyproject.toml` (read-only) — pytest markers: integration/gpu/sam2/slow

### Pre-existing user changes (PROTECT — do not overwrite)
- `M app/services/preset_manager.py` — adds `dan_choi` (Dân Chơi Streetwear) character set + 6 PNG asset filenames (user change)
- `M tests/test_preset_manager.py` — relaxes `== 3` → `>= 4`, adds `dan_choi` assertions (user change)
- `M channels.json` — 196 lines added in working copy; **contains 382 records incl. 95× "Test Channel", 95× "Channel A", 95× "Channel B", 95× "Find Me", 2× "test"** — TEST POLLUTION (read-only; forbidden to modify)
- `?? presets/characters/dan_choi_*.png` — 6 untracked character assets (user assets; PROTECT)

### Baseline commands & results (BEFORE any code change)
```
$ git status --short
M app/services/preset_manager.py
M channels.json
M tests/test_preset_manager.py
?? docs/CODEBASE_STRATEGY_REVIEW.md
?? docs/MASTER_PLAN_V1.md
?? docs/PRODUCT_REQUIREMENTS_V2.md
?? docs/pm/
?? presets/characters/dan_choi_back.png
?? presets/characters/dan_choi_sitting.png
?? presets/characters/dan_choi_standing.png
?? presets/characters/dan_choi_talking.png
?? presets/characters/dan_choi_three_quarter.png
?? presets/characters/dan_choi_walking.png

$ certutil -hashfile channels.json SHA256
0c1accfbe3edf93567aee81eb9d356bf6886dec72df9c525523df36d511eebb3   (BEFORE targeted run)

$ python -m pytest -q tests/test_channel_workspace.py tests/test_preset_manager.py
20 passed, 2 warnings in 2.00s

$ certutil -hashfile channels.json SHA256
dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555   (AFTER targeted run)
```

### POLLUTION PROOF (baseline)
Root `channels.json` SHA256 changed after ONE targeted test run:
`0c1accfb…` → `dd7aae26…` — confirms tests write to production-root storage.

Root cause:
1. `tests/test_channel_workspace.py::svc` fixture → `ChannelService(app_config)` where `app_config = app.config.config` singleton → `project_root = ~/MotionForge2D` → writes root `channels.json`.
2. `tests/test_preset_manager.py::test_reference_packs_endpoint` calls `get_preset_manager()` → rooted at `deps._config.project_root / presets/characters` → `ensure_assets()` writes PNGs into real preset dir when missing.

### Plan (7 steps)
1. Add `channels_file` path injection to `ChannelService.__init__` (optional param, default preserves current behavior) — minimal DI.
2. Update `tests/test_channel_workspace.py`: `svc` fixture uses `tmp_path`-based isolated `channels.json`; assert no root pollution.
3. Update `tests/test_preset_manager.py`: `test_reference_packs_endpoint` uses isolated assets root (no `get_preset_manager()` singleton write); keep all user changes.
4. Add regression test: root `channels.json` unchanged after service CRUD; production preset dir file-set unchanged after `ensure_assets()`.
5. Run targeted tests twice + hash before/after; run full non-GPU suite.
6. `git diff --check` + `git status --short`.
7. Fill `REPORT.md` → `SUBMITTED`.

### Notes
- No commit/push; no `PM_REVIEW.md` edit; no cleanup of already-polluted root data (out of scope).

## 2026-08-03 — Implementation & validation (append)

### Changes made (allowed scope only)
1. `app/workflow/channel_service.py` — added optional `channels_file: Path | None = None` param to `ChannelService.__init__`; default preserves production behavior (`config.project_root / "channels.json"`). Minimal DI hook for test isolation.
2. `tests/test_channel_workspace.py` — `svc` fixture now builds `ChannelService` with function-scoped `tmp_path`-based `channels.json` (isolated per test, order-free). Added `TestIsolation` regression tests:
   - `test_service_writes_isolated_file_only` — root `channels.json` bytes unchanged after CRUD.
   - `test_isolated_file_is_temporary` — injected file lives under pytest tmp dir.
3. `tests/test_preset_manager.py` — `test_reference_packs_endpoint` now uses `CharacterPresetManager(isolated_assets_root)` (session tmp) instead of `get_preset_manager()` singleton (which rooted at production `presets/characters` and could write PNGs). Added `TestIsolation::test_isolated_manager_writes_only_tmp_assets` — production preset dir file set unchanged by `ensure_assets()`.

### Validation results (REQUIRED sequence)
```
$ certutil -hashfile channels.json SHA256          # BEFORE
dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555

$ python -m pytest -q tests/test_channel_workspace.py tests/test_preset_manager.py   # RUN 1
23 passed, 2 warnings in 2.13s

$ python -m pytest -q tests/test_channel_workspace.py tests/test_preset_manager.py   # RUN 2
23 passed, 2 warnings in 2.14s

$ certutil -hashfile channels.json SHA256          # AFTER
dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555

=> HASH IDENTICAL before/after two targeted runs (isolation proven).
```

### Full non-GPU suite
```
$ python -m pytest -q -m "not gpu and not sam2 and not integration"
140 passed, 6 skipped, 7 deselected, 14 warnings in 11.95s
```

### git diff --check / status
```
$ git diff --check
exit=0  (only CRLF warnings)
$ git status --short
 M app/services/preset_manager.py      (USER change preserved)
 M app/workflow/channel_service.py     (task change)
 M channels.json                       (pre-existing pollution; NOT modified by task)
 M tests/test_channel_workspace.py     (task change)
 M tests/test_preset_manager.py        (task + USER changes preserved)
 ?? docs/... (untracked docs)
 ?? presets/characters/dan_choi_*.png  (USER assets preserved)
```

### Notes
- Root `channels.json` diff vs HEAD grew 196 → 224 lines; the +28 happened during the BASELINE run BEFORE the fix (one last pollution write). After the fix, two consecutive runs left hash unchanged. Cleanup of the already-polluted file is OUT OF SCOPE (task forbids touching channels.json).
- Pydantic serialization warnings (enum 'mode' static_asset) are pre-existing, unrelated to this task.
- No skip/xfail added; no assertion weakened for the isolation change.


## 2026-08-03 — CORRECTION (PM review CHANGES_REQUESTED round 2)

### PM review findings (addressed)
1. Removed ALL `ensure_assets()` calls on the production preset directory from tests.
   - `TestIsolation::test_isolated_manager_writes_only_tmp_assets` no longer constructs
     `CharacterPresetManager(prod_dir)`; it snapshots production preset dir READ-ONLY
     (filename → sha256), runs generation on `isolated_assets_root` (pytest tmp), then
     asserts the production snapshot is unchanged.
   - The only remaining `pm.ensure_assets()` in tests runs on the tmp root (line 290).
2. Isolated the app client across ALL of `tests/test_preset_manager.py`:
   - Removed the local `@pytest.fixture(scope="session") client` that built
     `TestClient(app.main.app)` WITHOUT `_patch_project_root`.
   - Tests now use the conftest `client` fixture (function-scoped) which runs
     `_patch_project_root` → `app.api.deps._config` points at a tmp project root,
     so route-level `get_preset_manager()` resolves to the temp preset dir.
3. Added regression test `TestIsolation::test_endpoint_generates_assets_under_tmp_root`:
   - `GET /api/projects/presets/characters` returns 200 with all sets × 6 poses.
   - Assets are generated/read under `deps._config.project_root / presets/characters`
     (tmp, patched) — verified ≥ 4×6 PNGs exist there.
   - Production `presets/characters` snapshot (file set + sha256) unchanged.
   - Root `channels.json` bytes unchanged.

### Validation results (round 2 — REQUIRED sequence)
Snapshot BEFORE:
```
$ certutil -hashfile channels.json SHA256
dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555
$ sha256sum presets/characters/*.png | sort -k2   → 28 files (saved to
  docs/pm/sessions/S00-T01-baseline-isolation/preset_assets_before.sha256)
```

$ python -m pytest -q tests/test_channel_workspace.py tests/test_preset_manager.py   # RUN 1
24 passed, 2 warnings in 3.19s

$ python -m pytest -q tests/test_channel_workspace.py tests/test_preset_manager.py   # RUN 2
24 passed, 2 warnings in 3.16s

Snapshot AFTER:
```
$ certutil -hashfile channels.json SHA256
dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555   (UNCHANGED)
$ sha256sum presets/characters/*.png | sort -k2 → diff vs BEFORE = EMPTY (28 files UNCHANGED)
```

### Full non-GPU suite (round 2)
```
$ python -m pytest -q -m "not gpu and not sam2 and not integration"
141 passed, 6 skipped, 7 deselected, 14 warnings in 12.94s   (0 failed; +1 new regression test)
```

### git diff --check / status (round 2)
```
$ git diff --check
exit=0  (only CRLF warnings)
$ git status --short
 M app/services/preset_manager.py      (USER change preserved — 7× dan_choi)
 M app/workflow/channel_service.py     (task change — channels_file DI)
 M channels.json                       (pre-existing pollution; NOT modified)
 M tests/test_channel_workspace.py     (task change — isolation fixture + 2 regression tests)
 M tests/test_preset_manager.py        (task change — client isolation + 2 regression tests; USER assertions >= 4 preserved)
 ?? docs/... (untracked docs)
 ?? presets/characters/dan_choi_*.png  (USER assets preserved)
```

### Notes (round 2)
- The earlier implementation had a latent write-capable call on the production
  preset path (`CharacterPresetManager(prod_dir).ensure_assets()`); it was a
  no-op only because all assets already existed. Removed per PM review.
- The previous local session-scoped `client` fixture in test_preset_manager.py
  bypassed `_patch_project_root`, so endpoint tests could reach the production
  singleton path. Removed; conftest `client` is now used everywhere in the module.
- channels.json diff vs HEAD remains 224 lines (pre-existing pollution);
  cleanup is OUT OF SCOPE.
- No skip/xfail; no assertion weakened.
