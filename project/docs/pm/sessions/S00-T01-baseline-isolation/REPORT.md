# S00-T01 Report — Isolate test data from production-root storage

**Status:** SUBMITTED
**Session:** `docs/pm/sessions/S00-T01-baseline-isolation`
**Date:** 2026-08-03 (updated after PM review round 2)

## 1. Summary

Tests previously wrote channel/preset data into production-root storage:
`tests/test_channel_workspace.py` created channels in the root `channels.json`
(95× "Test Channel", 95× "Channel A/B", 95× "Find Me" pollution records),
and preset endpoint tests in `tests/test_preset_manager.py` could reach the
production `get_preset_manager()` singleton rooted at
`deps._config.project_root / presets/characters`.

This task (including PM-review round 2 fixes) provides:

- `ChannelService` accepts an optional `channels_file` path (constructor DI);
  channel workspace tests use a function-scoped `tmp_path`-based
  `channels.json` — every test gets its own file, no order dependency.
- ALL of `tests/test_preset_manager.py` now uses the conftest `client`
  fixture (which applies `_patch_project_root`), so route-level
  `get_preset_manager()` resolves to a temporary project root.
- No test calls `ensure_assets()` on the production preset directory; the
  production preset dir is only snapshotted read-only.
- Regression tests prove: endpoint works under temp root, temp assets are
  generated/read under temp root, production preset file set/content unchanged,
  root `channels.json` unchanged.

## 2. Files changed

| File | Change | Scope |
|---|---|---|
| `app/workflow/channel_service.py` | Added optional `channels_file: Path \| None = None` param; default = production path (behavior preserved) | Allowed (minimal DI in app/) |
| `tests/test_channel_workspace.py` | `svc` fixture uses tmp isolated `channels.json`; added `TestIsolation` (2 tests) | Allowed (tests/) |
| `tests/test_preset_manager.py` | Removed local unpatched session `client`; uses conftest isolated `client`; `test_reference_packs_endpoint` uses isolated assets root; rewrote `TestIsolation` (read-only production snapshot + tmp generation); added `TestIsolation::test_endpoint_generates_assets_under_tmp_root`; user changes preserved | Allowed (tests/) |
| `docs/pm/sessions/S00-T01-baseline-isolation/LOG.md` | Full session log + round-2 correction (append-only) | Allowed |
| `docs/pm/sessions/S00-T01-baseline-isolation/REPORT.md` | This report | Allowed |

**Preserved (untouched):** `channels.json` (read-only per task; not modified by
this task — its working-copy diff is pre-existing pollution), all
`presets/characters/*.png` assets (28 files, sha256-verified unchanged),
`app/services/preset_manager.py` user changes (`dan_choi` set), existing test
assertions (`>= 4`).

## 3. Isolation mechanism

1. **Channel storage**: `ChannelService.__init__(config, channels_file=None)`
   — when `channels_file` is provided, `_channels_file` points at the injected
   temp file; otherwise it falls back to `config.project_root / "channels.json"`
   (exact production behavior). Tests inject `tmp_path / "channels.json"` via a
   function-scoped fixture, so each test starts from an empty isolated store.
2. **Preset endpoints**: all tests use the conftest `client` fixture whose
   `_patch_project_root` replaces `app.api.deps._config` with a temp-root
   `AppConfig` and rebuilds `_project_wf`/`_job_service` against it. Route-level
   `get_preset_manager()` therefore resolves to
   `tmp_root / presets/characters`; `ensure_assets()` (if triggered by an
   endpoint) writes only under that temp root.
3. **Preset manager unit tests**: construct `CharacterPresetManager(tmp_root)`
   directly; generation runs only under pytest temp paths.
4. **No global machine path hard-coding; no global monkeypatch of paths**
   (per implementation constraints) — injection is constructor/config-level,
   so parallel/order-free execution cannot contend on a shared global.

## 4. Validation evidence

### AC1 — All channel/preset tests use isolated storage (no root writes)
- `tests/test_channel_workspace.py::TestIsolation::test_service_writes_isolated_file_only`
  — root `channels.json` bytes identical before/after service CRUD. **PASS**.
- `tests/test_channel_workspace.py::TestIsolation::test_isolated_file_is_temporary`
  — injected file path lives under the OS temp dir. **PASS**.
- `tests/test_preset_manager.py::TestIsolation::test_isolated_manager_writes_only_tmp_assets`
  — production `presets/characters` snapshot (file set + sha256) unchanged
  after full asset generation on a tmp root. **PASS**.
- `tests/test_preset_manager.py::TestIsolation::test_endpoint_generates_assets_under_tmp_root`
  — `GET /api/projects/presets/characters` returns 200; assets generated under
  the patched tmp project root; production preset snapshot unchanged; root
  `channels.json` bytes unchanged. **PASS**.
- `grep ensure_assets tests/` — the only call is on the tmp root
  (`CharacterPresetManager(isolated_assets_root).ensure_assets()`); no test
  constructs a manager rooted at the production dir. **PASS**.
- All 24 targeted tests **PASS**.

### AC2 — Two-run regression evidence: root channels.json hash unchanged
```
$ certutil -hashfile channels.json SHA256          # BEFORE
dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555

$ python -m pytest -q tests/test_channel_workspace.py tests/test_preset_manager.py   # RUN 1
24 passed, 2 warnings in 3.19s

$ python -m pytest -q tests/test_channel_workspace.py tests/test_preset_manager.py   # RUN 2
24 passed, 2 warnings in 3.16s

$ certutil -hashfile channels.json SHA256          # AFTER
dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555
```
Hash **identical** before/after. Production preset assets snapshot (28 files,
sha256 each, saved in `preset_assets_before.sha256`) also **identical**
(`diff` empty) across the runs.

### AC3 — Targeted channel/preset tests pass
`24 passed, 2 warnings in 3.19s` and `24 passed, 2 warnings in 3.16s` (both runs).

### AC4 — Full non-GPU Python suite
```
$ python -m pytest -q -m "not gpu and not sam2 and not integration"
141 passed, 6 skipped, 7 deselected, 14 warnings in 12.94s
```
**0 failed** — no regression attributable to this task. (6 skipped are
pre-existing skips; 7 deselected are gpu/sam2/integration markers; 14 warnings
are pre-existing Pydantic enum-serialization warnings.)

### AC5 — Existing user changes preserved
`git status --short` before task: `M app/services/preset_manager.py`,
`M tests/test_preset_manager.py`, `M channels.json`, 6 untracked
`dan_choi_*.png`. After task, all still present; user diffs verified intact
(`dan_choi` set — 7 occurrences in `preset_manager.py`; `>= 4` assertions in
`test_preset_manager.py`). **PASS**.

### AC6 — Report lists files, commands, results, out-of-scope issues
This report (Section 2 files, Section 4 commands/results, Section 5
out-of-scope findings). **PASS**.

## 5. Out-of-scope findings (not acted on)

1. **Root `channels.json` is polluted**: 382 records — 95× "Test Channel",
   95× "Channel A", 95× "Channel B", 95× "Find Me", 2× "test". Cleaning this
   file is explicitly out of scope (task forbids modifying `channels.json`);
   recommend a follow-up task to purge test records.
2. **`get_preset_manager()` singleton** still roots at the production preset
   dir at runtime — fine for production, but any future test that calls it
   without `_patch_project_root` can still write assets. Tests now always go
   through the isolated client or an explicit tmp-root manager; a runtime
   config injection would be a larger refactor (out of scope).
3. **Pydantic serializer warning** (enum `mode` = `static_asset`) in unrelated
   routes — pre-existing, not caused by this task.
4. **`test_integration.py`** (excluded by marker) is known to hit a pre-existing
   SAM2 issue; not related to this task.

## 6. Deviations / limitations

- No deviations from the task contract. Implementation constraints honored:
  no machine paths hard-coded, pytest temp dirs used, no global monkeypatch,
  no user data deleted/rewritten, no skip/xfail added.
- The required PowerShell hash command `Get-FileHash channels.json -Algorithm SHA256`
  is equivalent to `certutil -hashfile channels.json SHA256` used here (both
  produce the SHA256 of the file; results recorded verbatim).
- Production preset assets were additionally verified by per-file SHA256
  snapshot before/after (`preset_assets_before.sha256`), per PM review
  requirement 4.
- Targeted test paths (determined after inventory):
  `tests/test_channel_workspace.py` (channel storage tests) +
  `tests/test_preset_manager.py` (preset tests).

## 7. Status

**SUBMITTED** — awaiting PM review. No commit/push performed.
