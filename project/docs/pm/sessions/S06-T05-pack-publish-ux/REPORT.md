# Task S06-T05 Implementation Report

- **Task ID:** `S06-T05`
- **Status:** `SUBMITTED`
- **Owner:** Hermes (main worktree `C:\Users\Admin\MotionForge2D`)
- **Depends On:** `S06-T04` (APPROVED, `20260804-115618`)
- **Quality Run ID:** local run `2026-08-05` (gates executed individually, see evidence below)

## Acceptance Criteria — Evidence

### AC1. Preview of 6 core pose slots
- `frontend/src/app/(app)/characters/page.tsx` renders the 6 core pose slot grid
  (`front`, `three_quarter`, `side`, `back`, `sitting`, `walking`) with real
  pose preview images served by the new read-only endpoint
  `GET /api/v2/characters/{id}/versions/{v}/assets/{pose_slot}/image`
  (serves the managed artifact file; 404 when character/version/slot/artifact/file
  is missing). Missing slots show a dashed "Chưa có asset" placeholder + badge.
- **Evidence:** `tests/test_pack_publish_ux.py::test_pose_preview_image_serves_managed_file`
  — 404 before attach, 200 `image/png` with `\x89PNG` bytes after attaching a
  real managed file, 404 for unknown slot.
- **Evidence:** `tests/test_pack_publish_ux.py::test_pose_preview_unknown_character_404`.

### AC2. Pose completeness validation indicator banner
- Page computes missing slots from the real `assets` list of the active
  `PackVersionData` (fetched via `GET /api/v2/characters/{id}/versions`) and
  renders:
  - green `Publish Ready — pack version đạt đủ 6 pose slot.` when complete,
  - amber `Missing N pose slots — <slots>` otherwise.
- **Evidence:** completeness banner logic in page.tsx (`missingSlots` / `isComplete`);
  server-side gate is exercised by
  `tests/test_pack_publish_ux.py::test_nested_publish_rejects_missing_slots`
  (422 with all 6 `missing_slots`).

### AC3. "Publish Pack Version v1" action button with confirmation dialog and CAS revision handling
- Button `Xuất Bản Pack Version v{version}` opens a confirmation dialog
  (immutability warning). Confirming POSTs
  `/api/v2/characters/{id}/versions/{v}/publish` with body
  `{"revision": <version.revision>}` (CAS).
- Backend nested endpoint added (append-only) to `app/api/routes/durable_characters.py`:
  `POST /api/v2/characters/{character_id:uuid}/versions/{version_number:int}/publish`
  — resolves version number → version UUID, delegates to the same
  CAS-protected `repo.publish_pack_version`; error mapping: 404 character/version
  missing, 409 CAS mismatch, 422 publish-gate with `missing_slots`.
- Frontend handles 409 (reloads fresh state with message), 422 (shows missing
  slots), success (reloads versions, shows immutable badge).
- **Evidence:** `test_nested_publish_success_and_immutability`,
  `test_nested_publish_cas_conflict` (stale revision → 409),
  `test_nested_publish_not_found` (404s).

### AC4. Immutable published version badge preventing further asset mutations
- When `version.status === "published"` the page shows a locked badge
  `Version vN đã xuất bản (Immutable)` (Lock icon), hides the publish button,
  and disables the per-slot attach control.
- Server enforces immutability: `repo.attach_asset` raises
  `PackVersionImmutableError` → 409 on any asset mutation of a published
  version; re-publish is idempotent with the bumped revision.
- **Evidence:** `test_nested_publish_success_and_immutability` — attach to
  published version → 409; republish with new revision → 200 published.

## Validation — real command output

| Gate | Command | Result |
|---|---|---|
| Targeted pytest | `python -m pytest tests/test_pack_publish_ux.py tests/test_character_domain.py -q --cache-clear` | `9 passed, 1 warning in 4.82s` |
| Full pytest | `python -m pytest -q -m "not gpu and not sam2 and not integration" --cache-clear` | `604 passed, 8 skipped, 7 deselected, 6 warnings in 319.38s (0:05:19)` |
| Ruff | `python -m ruff check app/api/routes/durable_characters.py tests/test_pack_publish_ux.py` | `All checks passed!` |
| Mypy | `python -m mypy app/api/routes/durable_characters.py` | `Success: no issues found in 1 source file` |
| TypeScript | `npx tsc --noEmit` (frontend) | exit 0 |
| ESLint | `npm run lint` (frontend) | `9 problems (0 errors, 9 warnings)` — 1 new `<img>` warning on page.tsx, consistent with pre-existing ScreenB/C/D warnings; 0 errors |
| Next build | `npm run build` (frontend) | `✓ Compiled successfully` — `/characters` route generated (static) |

## Changed files

- `app/api/routes/durable_characters.py` — APPENDED 2 endpoints (nested publish,
  pose preview image); all pre-existing routes untouched (user file preserved).
- `frontend/src/app/(app)/characters/page.tsx` — rewritten from legacy preset
  page to durable Character Library Pack Review & Publish UX (real API, no mock data).
- `tests/test_pack_publish_ux.py` — NEW (6 tests).
- `docs/pm/sessions/S06-T05-pack-publish-ux/LOG.md` — appended baseline + progress.

## Protected user changes — preservation proof

SHA256 before vs after (identical, unchanged):
- `app/persistence/characters.py` `cd5a9468…` (unchanged)
- `app/schemas/characters.py` `d741780d…` (unchanged)
- `app/workflow/character_validator.py` `3ae90b75…` (unchanged)
- `app/workflow/character_preset_importer.py` `c3377f5b…` (unchanged)
- `tests/test_character_domain.py` `b9336421…` (unchanged)
- `tests/test_character_validator.py` `a7a6604f…` (unchanged)
- `migrations/versions/d5e6f7a8b9c0_character_library_schema.py` `2aeee6ba…` (unchanged)
- All other pre-existing modified/untracked files (channels/projects/dashboard/
  api.ts, automation, channels.json, S04 session docs, data/, e2e spec, fixtures)
  untouched — `git status` shows no new modifications beyond LOG.md/page.tsx and
  the new test file.

## Deviations / limitations

- No mock or fallback data anywhere (per user requirement); page shows a real
  error state with retry when the API is unavailable.
- Pose preview requires the artifact file to exist on disk under the managed
  root; a registered Artifact row without its file yields 404 (honest state).
- `<img>` element used for pose previews (same convention as existing
  ScreenB/C/D pages); ESLint reports the same `no-img-element` warning, 0 errors.
- Not run: GPU/SAM2/integration-marked tests (excluded by the project's quality
  gate marker `-m "not gpu and not sam2 and not integration"`), 7 deselected.

## Out-of-scope findings (not fixed)

- s06-t01 worktree's APPROVED S06-T05 reference page called the nested publish
  URL without a `revision` body and with hardcoded `versions/1`, and contained a
  hardcoded fallback character (mock). This worktree implements the correct
  CAS body, dynamic version number, and no mock fallback instead.
- `run-hermes.ps1` in the session dir points at the `s06-t01` worktree repo root,
  not the current worktree; not part of task scope, left untouched.
