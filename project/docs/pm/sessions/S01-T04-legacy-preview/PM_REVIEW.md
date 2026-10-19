# S01-T04 - PM Review

**Decision:** APPROVED  
**Reviewed:** 2026-08-03  
**Reviewer:** PM/Codex

## Required corrections

1. `_inventory_channels()` reads `channels_file` even after `_checksum_sources()` finds it resolves outside `legacy_root`. Reject it before any read. The existing symlink test only proves the parsed result is empty, not that outside bytes were never opened; add a test that makes any attempted read fail or otherwise proves no open/read occurs.
2. Validate `projects_root` itself is contained before `is_dir()`/`iterdir()`. An explicit path or symlink outside the legacy root must produce a blocker and must never enumerate/read the outside directory. Add regression tests for explicit outside and symlinked projects roots.
3. Defensive parsing must not crash when `scenes`, `objects` or other counted collections are `null`, scalar or object. Replace unsafe `len(data.get(...))` calls and add malformed-schema continuation tests.
4. Proposed object identity must be project-scoped. Two projects can both contain legacy `object_id="object_1"`; they must receive different deterministic IDs and the serialized mapping must not silently overwrite one. Include the project legacy ID in the UUID key and expose a non-lossy mapping shape/test.
5. Re-run targeted tests, Ruff, mypy, full seven-gate baseline and diff check. Append LOG, update REPORT and resubmit in the same session.

## Final review

Correction round 1 prevents all channel/projects root reads outside the explicit legacy root, handles malformed collection types without aborting inventory, and makes object identity project-scoped with a non-lossy mapping. PM independently reran 35 targeted tests, Ruff and mypy; all passed. Quality run `20260803-174323` records 7/7 gates PASS. S01-T04 is approved and releases S01-T05.
