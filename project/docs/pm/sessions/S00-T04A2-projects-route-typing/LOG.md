# S00-T04A2 - Execution Log

Append-only.

## Baseline (2026-08-03, before any code change)

| Timestamp | Action | Evidence |
|---|---|---|
| 2026-08-03 | PM issued packet | READY |
| 2026-08-03 | Required reading complete | SESSION_PROTOCOL.md, TASK.md, latest mypy log (output/quality-baseline/20260803-134548/Gate_4_-_Python_typing.log), app/api/routes/projects.py (1988 lines), app/schemas/__init__.py, service signatures (job_service, segmentation_service, render_service, replacement_service, object_extraction_service, project_workflow), app/api/helpers.py, app/api/deps.py, targeted tests (test_preset_manager.py, test_api.py, test_trailing_slash.py, test_delete_and_autosegment.py) |
| 2026-08-03 | `git status --short` before change | 23 modified, 14 untracked (user/prior-session changes preserved — see REPORT.md §Protected changes). Real projects on disk: 2dc14177a212 + 4503582811e8 (235 scenes each) — untouched. |
| 2026-08-03 | Baseline `python -m mypy app` | `Found 81 errors in 1 file (checked 41 source files)` — all in app/api/routes/projects.py; matches latest mypy log exactly. |
| 2026-08-03 | Baseline targeted tests run 1 | `python -m pytest -q tests/test_preset_manager.py tests/test_api.py tests/test_trailing_slash.py tests/test_delete_and_autosegment.py tests/test_list_projects.py tests/test_list_objects.py` → `70 passed, 3 warnings in 5.32s`. |
| 2026-08-03 | Baseline `python -m ruff check app tests` | `All checks passed!` (exit 0). |
| 2026-08-03 | Real project snapshot (before) | `2dc14177a212 json_sha256=ad9a44d9b40a5842`; `4503582811e8 json_sha256=e1b9760e5160c06a`. |

## Plan

1. Type-annotate every route helper/closure honestly (`_sort_key`, `worker`, `seg_progress`) and add missing generic args (`dict[str, object]`) matching the service contract (`job_response`/`create_job` signatures).
2. Fix `ReplacementConfig` construction/mutation via the schema contract: `ReplacementMode.STATIC_ASSET` enum, `assetPath` alias (constructor uses `assetPath=`; attribute mutation uses `.asset_path` — both valid because `populate_by_name=True`), no casts.
3. Narrow `SelectionInput`/`BoundingBox`/`VideoMetadata` unions with runtime guards (`is not None`), preserving exact behavior.
4. Fix `sd.status = body.status` via `SceneStatus` enum (validated string → enum), `SceneStatusUpdate.status` stays a plain `str` (payload unchanged).
5. `b64encode` typing via typed intermediate (`buf.tobytes()`), `cv2.boundingRect` ints, `VideoMetadata` non-None guard.
6. Run full validation + targeted tests twice; prove payloads/status codes unchanged via before/after test runs and project-dir snapshot.

## Validation run 1 (baseline, BEFORE edits)

```
$ python -m mypy app
Found 81 errors in 1 file (checked 41 source files)

$ python -m pytest -q tests/test_preset_manager.py tests/test_api.py tests/test_trailing_slash.py tests/test_delete_and_autosegment.py tests/test_list_projects.py tests/test_list_objects.py
70 passed, 3 warnings in 5.32s

$ python -m ruff check app tests
All checks passed!
```

## Implementation (2026-08-03) — app/api/routes/projects.py only

| Timestamp | Action | Evidence |
|---|---|---|
| 2026-08-03 | Annotated helpers/workers + dict generics | `_sort_key(p: Path) -> tuple[int, float]`; `worker`/`seg_progress` typed to `Callable[[float, str], None]`/`Callable[[], bool]` per `job_service.create_job` contract; ~40 route signatures `-> dict[str, object]` / `list[dict[str, object]]`; `results`/`objects`/`matched` annotated. |
| 2026-08-03 | ReplacementConfig via schema contract | `ReplacementMode.STATIC_ASSET` enum + `assetPath=` alias in constructor; attribute mutation `.asset_path`; attribute read unchanged. `apply_character_preset_early`, `auto_match_character` (2 sites each). No casts/ignores. |
| 2026-08-03 | Narrowed unions with runtime guards | `_auto_crop_object` bbox width/height `is not None`; `create_object` dedupe (es_w/es_h/sel_w/sel_h) + name-gen fallback (160,160); `chunk_scenes` `video_metadata is None or not file_path` → same 400; `auto_match` `source_bbox.width/height is not None`; `bbox_x/bbox_y` direct (FrameMotion.bbox is non-optional). |
| 2026-08-03 | SceneStatus enum | `update_scene_status`: `sd.status = SceneStatus(body.status)` after the unchanged string-whitelist validation → serialized value identical. `SceneStatusUpdate.status` stays `str`. |
| 2026-08-03 | b64encode/cv2/gallery | `cv2.imencode` returns `(ok, buf)`; `base64.b64encode(buf.tobytes())`; `get_gallery` guards corrupt manifest (500) — dict payload unchanged for valid manifests. |
| 2026-08-03 | `python -m mypy app` (after edits) | `Success: no issues found in 41 source files` (was 81 errors). |
| 2026-08-03 | Suppression scan | `grep "type: ignore\|cast(\|# type:"` → NONE in projects.py. |

## Validation run 2 (AFTER edits)

```
$ python -m mypy app
Success: no issues found in 41 source files

$ python -m pytest -q tests/test_preset_manager.py tests/test_api.py tests/test_trailing_slash.py tests/test_delete_and_autosegment.py tests/test_list_projects.py tests/test_list_objects.py
70 passed, 1 warning in 5.00s        (run 1 after edits)
70 passed, 1 warning in 5.15s        (run 2 after edits — duplicate run required)

$ python -m pytest -q -m "not gpu and not sam2 and not integration"
160 passed, 8 skipped, 7 deselected, 12 warnings in 12.93s   (run 1)
160 passed, 8 skipped, 7 deselected, 12 warnings in 12.88s   (run 2)

$ python -m ruff check app tests
All checks passed!

$ powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1  (run id 20260803-140338)
Gate 1 Environment/Preflight  PASS exit=0
Gate 2 Python tests           PASS exit=0   (160 passed, 8 skipped, 7 deselected)
Gate 3 Python lint            PASS exit=0
Gate 4 Python typing          PASS exit=0   (mypy — WAS FAIL baseline, now PASS)
Gate 5 Frontend typecheck     PASS exit=0
Gate 6 Frontend lint          FAIL exit=1   (unchanged baseline: gpu-workflow/happy-path require(), AssemblyModal unescaped, CompositeCanvas setState-in-effect)
Gate 7 Frontend build         PASS exit=0
OVERALL: FAIL (exit 1) — identical to documented baseline (only Gate 4 flipped FAIL→PASS)

$ git diff --check
exit 0 (CRLF warnings only — cosmetic, documented baseline)

$ git status --short
Only pre-existing dirty/untracked files + app/api/routes/projects.py added by this task.
Real projects JSON hashes unchanged (after): 2dc14177a212=ad9a44d9b40a5842, 4503582811e8=e1b9760e5160c06a
```

## Notes

- No suppression, no `type: ignore`, no `cast()`, no mypy config change.
- No API path/payload/alias/status/media change: all 70 targeted tests (incl. `assetPath` alias, trailing-slash, auto-match pose) pass identically; full suite matches approved baseline count.
- No test files were added/changed — existing tests already lock the behavior (AC3 evidence).
- `docs/pm/sessions/S00-T04A2-projects-route-typing/` LOG/REPORT updated; PM_REVIEW.md untouched.
