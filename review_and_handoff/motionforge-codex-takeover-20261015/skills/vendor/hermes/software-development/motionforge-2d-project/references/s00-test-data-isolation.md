# S00-T01 — Test-data isolation from production-root storage (run-through)

Session: `docs/pm/sessions/S00-T01-baseline-isolation` (Epic E00, sprint S00).

## Problem

- Root `channels.json` had 382 records: 95× "Test Channel", 95× "Channel A",
  95× "Channel B", 95× "Find Me", 2× "test" — direct evidence that
  `tests/test_channel_workspace.py` was writing to the production file.
- `tests/test_preset_manager.py::test_reference_packs_endpoint` called
  `get_preset_manager()` singleton → rooted at `deps._config.project_root /
  presets/characters` → `ensure_assets()` could write PNGs into the real
  preset dir.

## Pollution proof (baseline, BEFORE any code change)

```
$ certutil -hashfile channels.json SHA256 | sed -n '2p'
0c1accfbe3edf93567aee81eb9d356bf6886dec72df9c525523df36d511eebb3
$ python -m pytest -q tests/test_channel_workspace.py tests/test_preset_manager.py
20 passed, 2 warnings in 2.00s
$ certutil -hashfile channels.json SHA256 | sed -n '2p'
dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555
```
Hash changed after ONE run → tests wrote to root storage.

## Fix (minimal DI)

1. `app/workflow/channel_service.py`:
```python
def __init__(self, config: AppConfig, channels_file: Path | None = None) -> None:
    self._config = config
    self._channels_file = channels_file or (config.project_root / "channels.json")
```
2. `tests/test_channel_workspace.py`:
```python
@pytest.fixture
def isolated_channels_file(tmp_path) -> Path:
    return tmp_path / "channels.json"

@pytest.fixture
def svc(isolated_channels_file) -> ChannelService:
    return ChannelService(
        AppConfig(project_root=isolated_channels_file.parent),
        channels_file=isolated_channels_file,
    )
```
3. `tests/test_preset_manager.py`: `CharacterPresetManager(isolated_assets_root)`
   (session tmp via `tmp_path_factory`) instead of `get_preset_manager()`.

## Pitfall hit: session-scoped shared tmp file → order-dependent tests

First version used `tmp_path_factory` session-scoped for `isolated_channels_file`.
Result: every test passed ALONE, but the full file run failed
(`test_service_writes_isolated_file_only` asserting `len == 2` broke because
earlier CRUD tests had already written to the SAME shared file). Fix: function-
scoped `tmp_path` per test → each test starts from an empty store.

## Regression tests added

- `TestIsolation::test_service_writes_isolated_file_only` — byte-compare root
  `channels.json` before/after service CRUD.
- `TestIsolation::test_isolated_file_is_temporary` — injected file lives under
  the OS temp dir.
- `TestIsolation::test_isolated_manager_writes_only_tmp_assets` — production
  `presets/characters` file set unchanged after `ensure_assets()` on an
  isolated root.

## Required validation (final, after fix)

```
$ certutil -hashfile channels.json SHA256          # BEFORE
dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555
$ python -m pytest -q tests/test_channel_workspace.py tests/test_preset_manager.py   # RUN 1
23 passed, 2 warnings in 2.13s
$ python -m pytest -q tests/test_channel_workspace.py tests/test_preset_manager.py   # RUN 2
23 passed, 2 warnings in 2.14s
$ certutil -hashfile channels.json SHA256          # AFTER
dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555
$ python -m pytest -q -m "not gpu and not sam2 and not integration"
140 passed, 6 skipped, 7 deselected, 14 warnings in 11.95s
$ git diff --check        # exit 0 (only CRLF warnings)
```

## Round 2 — PM review CHANGES_REQUESTED (what got caught)

Reviewer found two write-capable paths despite round-1 fixes:

1. **Local session `client` fixture bypassed `_patch_project_root`.**
   `tests/test_preset_manager.py` had its own
   `@pytest.fixture(scope="session") def client()` building
   `TestClient(app.main.app)` — it never depended on `_patch_project_root`, so
   route-level `get_preset_manager()` used the REAL `deps._config` →
   `ensure_assets()` could write the production preset dir. The local fixture
   OVERRIDES the conftest one silently. Fix: delete the local fixture; the
   module now uses conftest's `client` everywhere.
   Grep check: `grep -n "def client(" tests/` must only match conftest.py.

2. **"No-op" `ensure_assets()` on the production dir is still a write-capable
   call.** Original `TestIsolation::test_isolated_manager_writes_only_tmp_assets`
   ended with:
   ```python
   pm2 = CharacterPresetManager(prod_dir)
   pm2.ensure_assets()  # "no-op for existing assets"
   assert after == before
   ```
   Passed only because all 28 assets already existed — a missing asset would
   have been CREATED before the assertion ran (pass-by-machine-state, not
   by contract). Rewritten contract:
   - snapshot production dir READ-ONLY before: `{name: sha256}` via helper
   - run full generation on `isolated_assets_root` (tmp)
   - assert `_snapshot_preset_dir(prod_dir) == prod_before`
   - no `CharacterPresetManager(prod_dir)` ever constructed in tests

3. **Endpoint-level regression test** (`test_endpoint_generates_assets_under_tmp_root`):
   with conftest `client`, `GET /api/projects/presets/characters` → 200, all
   sets × 6 poses; assets exist under `deps._config.project_root / "presets" /
   "characters"` (tmp, patched); production preset snapshot unchanged; root
   `channels.json` bytes unchanged.

Round-2 validation (REQUIRED sequence):
```
$ certutil -hashfile channels.json SHA256          # BEFORE
dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555
$ sha256sum presets/characters/*.png | sort -k2 > before.sha256   # 28 files
$ python -m pytest -q tests/test_channel_workspace.py tests/test_preset_manager.py   # RUN 1
24 passed, 2 warnings in 3.19s
$ python -m pytest -q tests/test_channel_workspace.py tests/test_preset_manager.py   # RUN 2
24 passed, 2 warnings in 3.16s
$ certutil -hashfile channels.json SHA256          # AFTER — identical
dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555
$ sha256sum presets/characters/*.png | sort -k2 | diff - before.sha256   # EMPTY
$ python -m pytest -q -m "not gpu and not sam2 and not integration"
141 passed, 6 skipped, 7 deselected, 14 warnings in 12.94s   # 140→141 (new regression test)
$ git diff --check        # exit 0
```

## Notes / out-of-scope findings

- The +28-line growth of `channels.json` (196→224 vs HEAD) happened during the
  BASELINE run before the fix — after the fix the hash froze. Cleaning the
  polluted file is a separate task (this task forbids touching `channels.json`).
- `test_integration.py` remains excluded (pre-existing SAM2 segfault).
- Pydantic enum-serialization warnings pre-existing, unrelated.
