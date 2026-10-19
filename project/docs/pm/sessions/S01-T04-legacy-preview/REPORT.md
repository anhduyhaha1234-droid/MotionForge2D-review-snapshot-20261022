# S01-T04 - Implementation Report

**Status:** SUBMITTED
**Started:** 2026-08-03 17:25 +07:00
**Submitted:** 2026-08-03 17:34 +07:00
**Resubmitted (after PM CHANGES_REQUESTED):** 2026-08-03 17:44 +07:00

## Outcome delivered

A read-only, deterministic legacy JSON inventory + import preview, used
exclusively through explicit input paths (never repo-root data by default):

- `app/persistence/legacy_preview.py` — `LegacyPreviewer`:
  - Explicit `legacy_root` (required); `channels_file`/`projects_root`
    default **inside** the supplied legacy root. Missing/invalid input raises
    `LegacyPreviewError`; data problems are issues, never exceptions.
  - Defensive parsing: corrupt channels file / project JSON / missing
    `project.json` / non-object entries / duplicate IDs / invalid scene
    ranges become stable issues (blocker vs warning) while inventory
    continues.
  - Containment: every referenced path is resolved against the legacy root
    (`os.path.commonpath`); absolute, traversal, drive/UNC and
    symlink/junction escapes are blockers and **never followed**. Source
    files themselves (`channels.json`, `project.json`) and the **projects
    root itself** are containment-checked before any read/enumeration
    (PM corrections 1–2).
  - Deterministic identity mapping: `uuid5` over a stable namespace per kind
    (`channel`/`project`/`object`); same legacy ID → same proposed ID.
    **Object identity is project-scoped** (`object:{project_id}:{object_id}`)
    and exposed non-lossily via `object_id_mapping` (PM correction 4).
  - Defensive parsing: null/scalar/object `scenes`/`objects` collections
    never crash; they produce warnings with zero counts (PM correction 3).
  - Audit data for S01-T05: unknown channel/project/object fields collected
    (never discarded), SHA-256 + size + mtime per source before/after,
    referenced-file records with `inside_root`/`exists`.
  - DTO `LegacyPreview` with `to_dict()`/`to_json()` (caller-controlled,
    deterministic: `sort_keys=True`, `ensure_ascii=False`, no wall-clock
    field → repeated preview is byte-identical).
- `app/persistence/__init__.py` — exports the new API (no engine/ORM imports
  added).
- `docs/architecture/LEGACY_IMPORT_PREVIEW.md` — contract doc (containment,
  defensive parsing, deterministic mapping, DTO, issue-code table).
- `tests/fixtures/legacy_import/` — synthetic fixtures only
  (`valid/`, `corrupt/`, `channels_only/`).
- `tests/test_legacy_import_preview.py` — 28 targeted tests.

No database created, no ORM/engine/session touched, no migration revision, no
backup/cutover/import, no API/workflow/service/frontend change, no commits,
`channels.json` user diff preserved byte-identical.

## PM review corrections (CHANGES_REQUESTED round)

| # | Correction | Resolution |
|---|---|---|
| 1 | `_inventory_channels()` reads `channels_file` even after `_checksum_sources()` finds it resolves outside `legacy_root`; prove no open/read occurs | Added `_channels_source_safe()`; `_inventory_channels()` now returns before any read when the source is outside. Regression test `test_symlinked_channels_is_blocker_and_never_opened` chmod-000s the symlink target so any attempted read would raise `PermissionError` — preview completes with blocker, no PathCheck for the source |
| 2 | Validate `projects_root` itself before `is_dir()`/`iterdir()`; outside/symlinked root must be a blocker and never enumerated | Added `_projects_root_safe()` (is_dir + containment); `_checksum_sources()`/`_inventory_projects()` skip enumeration and emit new blocker `PROJECTS_ROOT_UNSAFE`. Tests: `test_explicit_outside_projects_root_is_blocker_and_never_enumerated` (only channels.json checksummed, no secret project seen), `test_symlinked_projects_root_is_blocker_and_never_enumerated`, `test_default_projects_root_missing_is_not_an_issue` |
| 3 | Defensive parsing must not crash when `scenes`/`objects` are null/scalar/object | `scene_count`/`object_count` computed only for list types (`isinstance` guard); non-list collections produce `SCENE_RANGE`/`SCHEMA` warnings and zero counts. Tests: `test_null_scenes_and_objects_do_not_crash`, `test_scalar_scenes_and_objects_do_not_crash`, `test_object_scenes_and_objects_do_not_crash` |
| 4 | Proposed object identity must be project-scoped; mapping must not silently overwrite | Object proposed_id now `uuid5(NS, "object:{project_id}:{object_id}")`; new non-lossy DTO field `object_id_mapping` (`{project_id: {object_id: proposed_id}}`) serialized in `to_dict()`/`to_json()`. Test: `test_identical_object_ids_in_different_projects_get_distinct_ids` (both entries present, no overwrite) |
| 5 | Re-run targeted tests, Ruff, mypy, full seven-gate baseline and diff check; append LOG, update REPORT, resubmit | All re-run green (see Tests and validation); LOG appended; REPORT resubmitted |

## Acceptance criteria evidence

| AC | Status | Evidence |
|---|---|---|
| AC1 Valid fixture inventory produces deterministic entity/file counts and ID mapping | PASS | `test_valid_inventory_counts_and_mapping`: 2 channels/1 project/2 objects, `proposed_id == uuid5(NS, "kind:legacy_id")` for channel/project/object (object key is project-scoped: `proj_001:obj_a`); `object_id_mapping` exposed non-lossily; `test_valid_inventory_referenced_files`: source relationship + referenced files recorded with exists/inside_root; `test_valid_inventory_checksums_cover_all_sources` |
| AC2 Corrupt JSON/schema/reference/path cases produce stable actionable issues without source mutation | PASS | `test_corrupt_channels_json_is_blocker`, `test_corrupt_project_json_is_blocker`, `test_dir_without_project_json_is_warning`, `test_missing_source_video_is_warning`, `test_duplicate_object_and_scene_ids_are_warnings`, `test_unknown_channel_reference_is_warning`, `test_sources_never_mutated_by_preview` (byte+mtime snapshot before/after two runs), plus PM correction 3 null/scalar/object collection tests |
| AC3 Unsafe absolute/traversal/symlink references are blockers and never followed outside the supplied legacy root | PASS | `test_absolute_source_video_is_blocker`, `test_traversal_and_absolute_object_refs_are_blockers` (`../outside.png`, `C:/Windows/evil.png` → blocker, exists=False), `test_symlinked_source_is_blocker_and_not_read`, `test_symlinked_channels_is_blocker_and_never_opened` (chmod-000 read-proof), `test_symlinked_reference_escape_is_blocker` (link.png → outside secret never read), plus PM correction 2 projects-root containment tests |
| AC4 Unknown fields and checksums are recorded for S01-T05 audit/import | PASS | `test_unknown_fields_recorded` (project: `extra_top_level`, `future_field`; object: `novel_object_field`), `test_valid_fixture_has_no_unknown_fields`, `test_checksums_recorded_and_stable` (before==after, sha256 64-hex, size/mtime recorded) |
| AC5 Repeated preview is byte-identical and leaves all source bytes/mtime unchanged; no DB is created | PASS | `test_repeated_preview_is_byte_identical` (+corrupt variant), `test_preview_leaves_source_bytes_and_mtime_unchanged`, `test_no_database_created` (no *.db/sqlite in fixture root), `test_no_database_created_in_repo` (module source contains no sqlalchemy/engine/session) |
| AC6 Targeted tests and all seven quality gates PASS | PASS | 35/35 targeted (twice); full suite 266 passed, 8 skipped; ruff clean; mypy clean (47 files); quality baseline OVERALL: PASS (all 7 gates, exit 0); `git diff --check` exit 0 |

## Files changed

- `app/persistence/legacy_preview.py` (new; inventory/preview module; PM corrections 1–4)
- `app/persistence/__init__.py` (exports added)
- `docs/architecture/LEGACY_IMPORT_PREVIEW.md` (new; contract doc; sections 4/6/8/10 updated)
- `tests/fixtures/legacy_import/` (new; synthetic fixtures: valid, corrupt, channels_only)
- `tests/test_legacy_import_preview.py` (new; 35 tests)
- `docs/pm/sessions/S01-T04-legacy-preview/LOG.md` (appended)
- `docs/pm/sessions/S01-T04-legacy-preview/REPORT.md` (this file)

## Tests and validation

| Command | Result | Notes |
|---|---|---|
| `python -m pytest -q tests/test_legacy_import_preview.py` | PASS | 35 passed in 0.51s (run twice) |
| `python -m pytest -q tests/test_legacy_import_preview.py tests/test_managed_artifacts.py tests/test_persistence_bootstrap.py` | PASS | 99 passed in 2.38s |
| `python -m ruff check app tests` | PASS | All checks passed (SIM103, I001 fixed) |
| `python -m mypy app` | PASS | Success: no issues found in 47 source files |
| `python -m pytest -q --cache-clear` | PASS | 266 passed, 8 skipped, 12 warnings (full suite) |
| `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1` | PASS | OVERALL: PASS, all 7 gates, exit 0 (run id 20260803-174323) |
| `git diff --check` | PASS | exit 0 (only LF→CRLF advisory on Windows) |
| `certutil -hashfile channels.json SHA256` | UNCHANGED | dd7aae26096902eff74986b36554957d87eb8e60c5e8ff8048064c31655eb555 identical before/after; user diff preserved |
| DB creation scan | NONE | No *.db/sqlite created anywhere (only pre-existing `.mypy_cache` artifacts) |

## Architecture/domain impact

- Additive read-only layer: `legacy_preview.py` imports only stdlib
  (`hashlib`, `json`, `os`, `dataclasses`, `pathlib`, `uuid`) — no
  engine/ORM/models/repositories/services. Serialization is caller-controlled;
  the module never writes files and never creates a database (domain contract
  §7: "Inventory/preview is read-only and never mutates source JSON or
  assets").
- Proposed IDs follow domain contract §2: legacy IDs retained as `legacy_id`,
  never reused as primary keys; public IDs are UUID strings.
- No schema, migration, API, cleanup-service, workflow or frontend change.
- Production directories untouched (only read-only format probes earlier in
  this session; never used as test target).

## Known limitations/risks

- Scenes/objects are reported with counts + validity issues; full structural
  validation (e.g. `scene_details` vs `scenes` consistency, video_metadata
  coherence) is intentionally left to S01-T05 import validation.
- `legacy_root` is resolved once at construction; the previewer must be
  constructed after the final root location is known.
- Unknown fields are aggregated per kind (channel/project/object names); the
  exact per-record location of each unknown field is preserved implicitly by
  the issue model but not as a separate field-level index.

## Recommended PM decision

`PENDING` — awaiting PM review.
