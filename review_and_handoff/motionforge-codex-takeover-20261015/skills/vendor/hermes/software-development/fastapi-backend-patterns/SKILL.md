---
name: fastapi-backend-patterns
description: "Scaffold FastAPI modular backends with SSE streaming, async config management, and real-time log broadcasting. Covers project structure, asyncio.Queue-based SSE, Pydantic v2 config, CORS, and common pitfalls."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [fastapi, sse, backend, python, async, scaffolding]
    related_skills: [terminal-engineering-discipline, subagent-orchestration]
---

# FastAPI Backend Patterns

Reusable patterns for building modular FastAPI backends with real-time streaming capabilities.

## When to Use

- Scaffolding a new FastAPI project with modular routers
- Implementing Server-Sent Events (SSE) for real-time log/status streaming
- Setting up async config read/write with Pydantic v2
- Building API backends for desktop/web frontends that need live updates
- **Adding a new feature domain** (channels, workspaces, tags, etc.) to an existing backend

## Project Structure (Standard)

```
project/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1.py              # All v1 routers in one file (small projects)
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # Settings read/write
│   │   │   └── logger.py           # SSE log broadcaster
│   │   └── main.py                 # FastAPI app entry point
│   ├── data/
│   │   └── settings.json           # Persisted config
│   └── requirements.txt
```

For larger projects, split `api/v1.py` into `api/v1/health.py`, `api/v1/settings.py`, etc.

## SSE Streaming Pattern (asyncio.Queue)

The critical pattern: use a list of `asyncio.Queue` objects so multiple SSE clients each get their own queue. When a log is added, push to all queues. When a client disconnects, remove its queue.

See `references/sse-logger-pattern.py` for the complete implementation.

Key invariants:
1. Each SSE client gets its own `asyncio.Queue(maxsize=100)` on connect
2. `add_log()` iterates all registered queues and puts the message (non-blocking with `put_nowait`)
3. SSE generator yields `data: {json}\n\n` format, removes queue on disconnect
4. Use `asyncio.Queue`, NOT `collections.deque` — deque is not async-aware and will block
5. Set `maxsize` to prevent memory leaks from slow consumers — drop oldest or log a warning

## Config Management Pattern

See `references/config-pattern.py` for the implementation.

Key invariants:
1. Use `pydantic.BaseSettings` or plain `BaseModel` for config schema
2. Read from `data/settings.json` on startup, create with defaults if missing
3. POST merges partial updates (don't clobber fields not in the request)
4. Always write back to disk after POST — config must survive restart
5. Use `model.model_dump()` (Pydantic v2) not `.dict()` (Pydantic v1)

## FastAPI App Setup (main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import router as v1_router
from app.core.logger import add_log

app = FastAPI(title="Project Name")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    await add_log("Server started", "info")
```

## Adding Feature Modules to Existing Backends

When extending an existing FastAPI backend with a new feature domain (e.g., channels, workspaces, tags), follow this 4-layer pattern:

### Layer 1: Schema (`schemas/__init__.py`)
- Add enums and Pydantic models BEFORE the main project model they relate to
- Use `(str, Enum)` base for string enums (serializes cleanly to JSON)
- Add new fields to the main `ProjectData` model with safe defaults

### Layer 2: Service (`workflow/` or `services/`)
- Single class with CRUD operations
- Constructor takes `AppConfig` (or equivalent) for path resolution
- Private `_load_all()` / `_save_all()` for JSON file persistence
- Use `uuid.uuid4().hex[:12]` for short IDs
- Use `datetime.now(UTC).isoformat()` for timestamps (NOT `timezone.utc` — ruff UP017)
- Return Pydantic models, accept primitives

### Layer 3: Routes (append to existing router file)
- **Use lazy imports** inside route functions to avoid circular imports and keep startup fast
- Add `# noqa: PLC0415` to satisfy ruff's in-function-import lint
- Define request/response `BaseModel` classes at the top of the new section
- Raise `HTTPException(404)` for not-found, `HTTPException(400)` for validation

### Layer 4: Tests (`tests/test_<feature>.py`)
- `from __future__ import annotations` in every file
- Use `@pytest.fixture` for service instance (don't duplicate construction)
- Test CRUD: create, list, get, get-missing, delete, delete-missing
- Test enum values and model defaults
- **Never break existing tests** — run full suite after changes

### Verification (mandatory)
```bash
python -m ruff check app/ tests/    # must pass
python -m pytest tests/ -q          # ALL tests must pass (existing + new)
```

See `references/feature-module-example.md` for a complete concrete example (Channel Workspace from MotionForge2D).

## Auto-Generated Media Asset Endpoints (crop / thumbnail)

When the UI needs a cropped image or thumbnail per entity (e.g. a cut-out of a tracked object), don't make the client upload or compute it — **generate it server-side at creation, serve it with lazy regeneration, and batch it into list responses.**

Pattern (from MotionForge2D object crops):
1. **Schema:** add a path field with safe default: `crop_path: str | None = None` on the entity model.
2. **At creation:** crop the region from the source frame with OpenCV, save to disk, store the path:
   ```python
   def _auto_crop_object(proj_dir, object_id, selection, pad=10) -> Path | None:
       frame_path = find_frame_path(scene_dir, selection.frame_index)  # jpg/png aware
       frame = cv2.imread(str(frame_path))
       if selection.mode == "bounding_box":
           x, y = int(selection.x) - pad, int(selection.y) - pad
           bw, bh = int(selection.width) + 2*pad, int(selection.height) + 2*pad
       else:  # point mode: fixed window centered on click
           cx, cy = int(selection.x), int(selection.y)
           x, y, bw, bh = cx-80, cy-80, 160, 160
       # clamp to frame bounds, then:
       crop = frame[y:y+bh, x:x+bw]
       cv2.imwrite(str(obj_dir / "crop.png"), crop)
   ```
   Bbox mode uses the selection box (+pad); point mode uses a fixed window around the click.
3. **Serve endpoint** with BOTH trailing-slash variants (same rule as pitfall 13):
   ```python
   @router.get("/{project_id}/objects/{object_id}/crop")
   @router.get("/{project_id}/objects/{object_id}/crop/")
   def get_object_crop(...) -> FileResponse:
       # if crop.png missing → call _auto_crop_object(...) to regenerate,
       # then FileResponse(crop_file, media_type="image/png")
   ```
   **Lazy regeneration is the key:** objects created before the feature existed (or whose frames were wiped by test isolation) still render — regenerate from the stored selection instead of 404ing.
4. **List endpoints:** attach a `thumbnail_base64` data URL to each item so the UI renders N thumbnails in ONE request instead of N image fetches:
   ```python
   item["thumbnail_base64"] = "data:image/png;base64," + base64.b64encode(data).decode()
   ```
5. **Frontend:** helper `getObjectCropUrl(projectId, objectId)` returns the endpoint URL; render with `<img onError={e => (e.target as HTMLImageElement).style.display = "none"}>` so missing crops degrade to an empty box, not a broken-image icon.
6. **Tests:** write a synthetic frame directly into the test project's frames dir (`cv2.imwrite(...)`) before creating the object, then assert `GET .../crop` → `200` + `content-type` starts with `image/png` — and repeat for the trailing-slash variant.

See `references/media-asset-endpoints.md` for the full MotionForge2D implementation (helper + endpoint + test).

## Mutation Endpoints Must Return the Complete Updated Aggregate

Any create/delete/update endpoint the UI reflects immediately should return the **full updated `project`** (or equivalent aggregate), not a bare `{ok}`/`{status}`. Create endpoints return `{object_id, project}`; DELETE-all / DELETE-one return `{status, project}`. Frontend types must match this EXACTLY (`apiFetch<{ object_id: string; project: ProjectData }>`) — a mismatch (`apiFetch<TrackedObject>` vs `{object_id, project}`) fails `tsc` and half-populates the store. After a create, locate the full entity in the returned project (`res.project.objects.find(o => o.object_id === res.object_id)`) and call `setProject(res.project)` — do NOT re-fetch `GET /project` (slower, racy). After a delete, `setProject(res.project)` immediately updates the list.

See `references/return-shape-discipline.md` for the full pattern: exact code, synthetic-frame test helper (white bg + dark object for contour tests), the three tests (delete-single, clear-all, crop-b64), and the patch-tool import-block hazard.

## Generated Character Preset Library (multi-pose PNGs + pose matching)

For "character library / preset templates" features with zero shipped binary assets: generate transparent pose PNGs server-side with OpenCV, expose a schema-validated reference-pack API (`CharacterReferencePack` with 6 poses), and let an "auto-match" endpoint pick poses from bbox geometry (aspect ratio + centroid offset). Full pattern — schema, cv2 alpha-channel generation, pose heuristic, endpoint ordering, apply-to-all-scenes flow, boundary-test gotchas — in `references/character-preset-library.md`.

Browser cache-buster for replacement/regenerated images: append `?t=${Date.now()}&v=${encodeURIComponent(asset_path)}` — the `v` param changes when the asset changes, so React effects keyed on the URL re-run and the canvas redraws immediately (plain `?t=` alone does NOT force a redraw when the asset_path is unchanged).

## Common Pitfalls

1. **SSE endpoint must return `StreamingResponse` with `media_type="text/event-stream"`** — without this, the browser EventSource won't connect. Also set `Cache-Control: no-cache` header.

2. **Don't use `time.sleep()` in SSE generators** — use `await asyncio.sleep()` or `await queue.get()`. Blocking the event loop kills all concurrent connections.

3. **CORS must be configured BEFORE including routers** — middleware order matters in Starlette.

4. **`__init__.py` files are required** in every package directory — Python won't find modules without them.

5. **Background process startup on Windows** — don't use `&` in terminal foreground commands. Use `terminal(background=true)` instead. The shell will reject `&` in foreground mode.

6. **Pydantic v2 migration**: `.dict()` → `.model_dump()`, `.parse_obj()` → `.model_validate()`, `Config` class → `model_config`.

7. **StaticFiles mount at "/" can shadow API routes:** When mounting `StaticFiles(directory=..., html=True)` at `/`, it sits in the middleware chain alongside your API router. If the static mount is defined BEFORE the API router include, POST/PUT/DELETE requests to API routes may be intercepted by StaticFiles (which only handles GET/HEAD). Always `include_router` BEFORE `mount("/", StaticFiles(...))`. The router is checked first in Starlette's routing order.

8. **Server subprocess port conflicts in testing:** When testing, a previously started server may still hold the port. On Windows, use `taskkill /PID <pid> /F`. On Linux/macOS, `lsof -ti:<port> | xargs kill -9`. Always check for existing listeners (`netstat -ano | grep <port>`) before starting a test server.

9. **Stale code after editing routes:** Uvicorn imports modules at startup. If you add new routes to `v1.py` (or any router) while the server is running, the old process keeps the old code. New endpoints return `405 Method Not Allowed`. **Always restart uvicorn after adding/removing routes.** Diagnose by checking `/openapi.json` — if the new endpoint isn't listed, the server has stale code. On Windows, find and kill the listener: `python -c "import subprocess,os,signal; r=subprocess.run(['netstat','-ano'],capture_output=True,text=True); [os.kill(int(l.split()[-1]),signal.SIGTERM) for l in r.stdout.split('\n') if ':8000' in l and 'LISTENING' in l]"`.
   **Verifying a fix actually took effect:** After committing a 405 (or any route) fix, the RUNNING server may still be old code — a fix on disk does not change a live process. Before declaring success: (a) compare the process start time against when the fix was committed (`process(action='list')` shows uptime; a server started before the commit is stale), (b) check the live uvicorn access log for the failing status code from the running process, (c) restart uvicorn, then (d) re-run the EXACT failing request (`curl -X DELETE ...`) and confirm the new status code. Failure mode seen in the field: code fixed + tests green, but the user still hit 405 because the backend had been started before the fix landed.

14. **List endpoints with caps/sort can hide real data — verify disk before declaring data loss:** A list endpoint that truncates (`if len(results) >= N: break`) or sorts only by recency pushes real records out of the response when a flood of small/junk records exists (e.g. 30 test projects with 0 scenes created recently drown out a real 235-scene project created earlier). The user then panics "my project is lost". Fix: remove arbitrary caps, sort by a meaningfulness key (`scenes_count` desc first, then mtime) so real projects float to the top. **When a user reports missing data, always verify the filesystem directly first** (`ls projects/*/project.json` and read the actual JSON) — the API summary can be wrong (cap, filter, sort) while the data is fully intact on disk. Never conclude "data lost" from an API list response alone.

15. **Test-suite junk projects pollute the real data dir — patch project_root in tests:** Every test that hits project endpoints must isolate its project root via an autouse `_patch_project_root` fixture (monkeypatch the deps `_config`, `_project_wf`, `_job_service`, `_replacement_service`, `_seg_service`). Without it, tests write real dirs named "Test"/"Clip Test"/"Debug" into the production projects/ dir. Over months these accumulate into 1000+ junk projects and gigabytes — and can hide the user's real project in list endpoints (see pitfall 14). When cleaning up accumulated junk, identify by project.json `name` (whitelist real names like "Dự án..."), purge with `shutil.rmtree` in a script (faster than 1000 API DELETEs), then verify with `ls projects/` + the list API.
    **Centralize the fixture in conftest.py, don't duplicate per-file:** The robust pattern is ONE `_patch_project_root` + ONE `client` fixture in `tests/conftest.py` that patches the deps singletons. Per-file `client` fixtures that only do `TestClient(app)` (or only set an env var) silently OVERRIDE the conftest one and re-pollute the real dir — delete them and let tests inherit the conftest fixture. Fixtures that need real video/ingest may now skip because the isolated root has no pre-extracted frames: guard with `if r.status_code != 200: pytest.skip("...")` in the fixture rather than letting dependent tests fail with 404.
    **Verify after the fix:** run the full suite, then `ls projects/` — the count must be unchanged (only real projects remain). Zero new junk dirs proves the isolation works.

10. **`model_dump(by_alias=True)` converts ALL fields — not just one:** When you need a specific field renamed in JSON (e.g., `state` → `status`), `model.model_dump(by_alias=True)` renames ALL aliased fields to camelCase, breaking other consumers that expect snake_case. **Instead**, create a helper that does `model_dump()` then renames specific keys:
```python
def job_response(info: JobInfo) -> dict:
    data = info.model_dump()
    data["status"] = data.pop("state")
    return data
```
Only use `by_alias=True` when you genuinely want ALL fields in camelCase (e.g., a dedicated frontend-facing endpoint with `populate_by_name=True`).

11. **405 on `/api/projects` can mean wrong server, not wrong method:** If the frontend calls `POST /api/projects` and gets `405 Method Not Allowed`, check `/openapi.json` — if the listed routes are from a DIFFERENT app (e.g., "Goha MMO Clone" instead of your app), another server is occupying the port. Kill all uvicorn processes and restart. On Windows: `netstat -ano | grep ":PORT.*LISTENING"` → get PID → `wmic process where "PID=X" get CommandLine` → verify it's your app.

12. **Ruff UP017 + import sorting on Python 3.11+:** Use `datetime.UTC` not `datetime.timezone.utc` (UP017 auto-fixer). When importing multiple names from `datetime`, ruff enforces alphabetical order: `from datetime import UTC, datetime` — NOT `from datetime import datetime, UTC`. If ruff reports `I001` on an import block, run `ruff check --fix` or reorder manually. These two issues appear together on nearly every new file that uses timestamps.

13. **FastAPI trailing slash causes 405 on POST/DELETE:** Default `redirect_slashes=True` redirects `POST /api/foo/` → `GET /api/foo` (301), changing the method to GET → 405. Fix: `FastAPI(redirect_slashes=False)` + add trailing slash aliases for EVERY POST/DELETE endpoint the frontend calls — not just the one you're debugging. The frontend URLs have NO trailing slash, so aliases make both `/path` and `/path/` work:
```python
@router.delete("/{project_id}")
@router.delete("/{project_id}/")   # ← alias prevents 405
def delete_project(project_id: str) -> dict: ...
```
When adding the aliases, enumerate ALL `@router.post(`/`@router.delete(` lines (grep them), and add a `@router.X(".../")` twin for each — a script loop over `patch(old, old + "\n" + alias)` works well (22 endpoints done in one pass on MotionForge2D). Test both variants (see `tests/test_trailing_slash.py` pattern):
```python
def test_delete_without_slash(client): assert client.delete(f"/api/projects/{pid}").status_code == 200
def test_delete_with_slash(client): assert client.delete(f"/api/projects/{pid}/").status_code == 200
```

16. **Static routes AFTER dynamic `/{param}` routes get shadowed → 404, not 405:** FastAPI matches routes in declaration order. If `@router.get("/gpu-info")` is declared AFTER `@router.get("/{project_id}")` (and friends like `/{project_id}/objects`), then `GET /api/projects/gpu-info` matches `{project_id}="gpu-info"` first → the dynamic handler runs → 404 (project not found). The symptom is a 404 that the frontend fires repeatedly. Fix: declare static literal paths (`/gpu-info`, `/health`, `/stats`) BEFORE any dynamic `/{param}` route in the same router — or put them in a separate router. After moving the route, kill + restart uvicorn and re-run the exact request (see pitfall 9 — a live server keeps the old route order). Also verify the handler's return shape matches the real service return (e.g. a dataclass `EncoderInfo` needs `.gpu_name` attribute access, not `.get("gpu_name")` — a `.get()` on a dataclass raises AttributeError at request time).

17. **Dedupe-on-create: return the existing entity instead of creating duplicates.** When users repeatedly click the same region (point/bbox selection), each click creates a new entity. Add a proximity check at the top of the create handler: same scene + near-identical selection (e.g. `abs(dx)<20, abs(dy)<20, abs(dw)<30, abs(dh)<30, |Δframe|<3` for bbox; `|dx|<30, |dy|<30` for point mode) → return the existing entity with `{"duplicate": True, "object_id": existing.id, "project": ...}` (201, same shape as a normal create). Frontend treats it transparently since it uses the returned project anyway.
    **Test interaction hazard:** once dedupe lands, existing tests that create TWO objects with the same selection point will silently get 1 object back and fail on `assert len(objects) == 2`. Fix the test helper to take `x/y` params and create the second object at a different coordinate. Add a dedicated test: create with payload → create SAME payload again → assert `duplicate is True` and `object_id` equal → assert only 1 object in list.

18. **Frontend↔backend contract mismatches: 422 "Field required" ≠ missing field, 404 ≠ missing route.** Three distinct failure modes that look like other problems:
    - **Nested request-body wrapper.** If the backend Pydantic request model wraps config in a named field (`class ReplacementSettingsRequest(BaseModel): replacement_config: ReplacementConfig`), the frontend MUST send `{"replacement_config": {...}}`. Sending the fields flat yields `422` with `"msg": "Field required", "loc": ["body", "replacement_config"]` — reads like "missing field" but actually means "wrong nesting". Reproduce with curl BEFORE touching code to see the exact `loc` path, then fix the API client: `body: JSON.stringify({ replacement_config: settings })`.
    - **Frontend URL helper referencing a route that doesn't exist.** A URL-builder helper (`getReplacementImageUrl`) can point at an endpoint nobody implemented → silent 404 in the UI (image never loads, no error surfaced to the user). Before wiring a helper, grep the backend for the route; if missing, add the endpoint — for uploaded asset files, serve with `FileResponse`, glob `replacement.*` in the object dir + fall back to the stored `asset_path`, and raise 404 only if neither exists. Then verify live with curl (`-o /dev/null -w "%{http_code} %{content_type}"`).
    - **Hardcoded API port in component URLs.** `http://localhost:8000${asset_path}` breaks the moment the backend runs on a different port (8002 on this machine). Never hardcode — route through the `API_BASE`-aware helper (`api.getReplacementImageUrl(...)`). `tsc` won't catch it; only a live image fetch reveals it.

19. **cv2.imwrite cannot write to a BytesIO — tests uploading generated images must use `cv2.imencode`.** `cv2.imwrite(buf, img)` raises `cv2.error: Bad argument` when `buf` is a `BytesIO` (OpenCV 5 accepts only a filename/path). To build an in-memory upload payload in a test: `ok, enc = cv2.imencode(".png", img)` then `png_bytes = enc.tobytes()` and pass `files={"file": ("char.png", png_bytes, "image/png")}`. Same trick for any test that needs a generated image body without touching disk.

20. **Failing-fast endpoints (auto-match / bulk-apply) that must never 400 on missing data.** When an endpoint's purpose is "apply this everywhere", treating "source object lacks optional data" (motion frames, etc.) as a hard 400 makes the UI show a blocker for a non-fatal condition. Instead: compute a best-effort fallback (selection bbox when motion is None), apply the config to all candidates, return `{"status": "ok", "count": N, "warning": "..."}`. The frontend should wrap the call in a soft try/catch so a warning never interrupts the progress flow. Test: create two objects in different scenes with NO motion data → `POST .../auto-match` must return 200 with `status=ok` and the other object in `matched`.
    **Ruff F841 on spec-mandated "assigned but unused" locals:** a spec may require computing a fallback variable (`source_bbox`) that the new behavior doesn't actually consume — ruff flags it `F841 Local variable is assigned to but never used`. Don't delete the spec code; keep the computation and add `_ = source_bbox` (with a comment explaining it's retained for future similarity matching). That satisfies the spec AND ruff.

21. **Verification evidence: run each gate command in isolation, not one chained command.** `pytest && ruff && tsc && curl ...` in a single compound command reports the LAST command's exit code — a trailing `curl -w` write-error (exit 23) makes the whole result look failed even though pytest passed. When reporting verification, run each required command separately (`python -m pytest tests/ -q` alone, `python -m ruff check ...` alone, `npx tsc --noEmit` alone) so each exit code is clean evidence. Curl `-w` with output truncation (`head -c`) can itself exit 23 — that's a write error, not an HTTP error; re-run the curl alone when you see it.

22. **Nested-resource route missing the parent `{project_id}` segment → 404 that looks like route-order shadowing.** When adding `POST /{project_id}/presets/characters/{set}/{pose}/apply`, writing the decorator as `@router.post("/presets/characters/{set}/{pose}/apply")` while the function signature declares `project_id: str` makes the route match `/api/projects/presets/characters/...` — NOT `/api/projects/<pid>/presets/...` — so every real call 404s even though the route is listed BEFORE dynamic routes. Every path param in the function signature MUST appear in the decorator path. Diagnose by dumping the router's actual paths: `python -c "from app.api.routes import projects; [print(repr(r.path)) for r in projects.router.routes]"` — you'll see the route is missing the `{project_id}` segment. (Also: nested apply routes should target the FIRST object as "active object" since the ScreenD-style UI auto-selects objects[0].)

23. **Mutating enum-typed Pydantic fields with raw strings triggers serializer warnings.** Assigning `obj.replacement_config.mode = "static_asset"` when the field is `mode: ReplacementMode` (a str Enum) works at assignment time (pydantic v2 doesn't validate by default) but the serializer emits `PydanticSerializationUnexpectedValue(Expected enum ... input_type=str)` warnings on every save and the JSON can serialize oddly. Assign the enum member instead: `obj.replacement_config.mode = ReplacementMode.STATIC_ASSET`. Construction still coerces the string fine (`ReplacementConfig(mode="static_asset")` via `populate_by_name`); only mutation does not. Check server logs for the warning after applying config updates.

24. **Threshold-heuristic tests: use values clearly past the boundary, and check the math before "fixing" the code.** `auto_pose_for_bbox(220, 200)` fails `width > height * 1.1` because `220 > 220` is False — the TEST expectation was wrong, not the implementation. When a boundary-value test fails, compute the comparison by hand first; adjust the test input to be clearly past the threshold (e.g. `250, 200`), don't weaken the production heuristic. Same discipline for any ratio/percent threshold in tests.

25. **Script-based multi-line edits can silently truncate files — verify with git diff + syntax check.** Deleting a "duplicate block" via a Python script that computes line ranges (e.g. `lines[1684:1759]`) is dangerous: line numbers drift after earlier patches, and a stale range cuts off the REST of the file mid-function. Symptoms: `IndentationError: expected an indented block` at import time, or `tail` shows the file ending mid-`else:`. Recovery: `git checkout HEAD -- <file>` restores the last commit, then re-apply the intended changes as small controlled `patch` calls with unique context. Prevention: (a) before any line-range deletion, print the exact lines you're about to remove and eyeball them; (b) after ANY script-based edit to a Python file, immediately run `python -c "import ast; ast.parse(open('<file>').read())"` — the syntax check catches truncation instantly; (c) prefer `patch` with unique surrounding context over raw line arithmetic; (d) when you suspect a bad edit, `git diff --stat` against HEAD shows whether the tail of the file vanished.

See `references/preview-before-upload-modal.md` for the full ScreenD upload-flow pattern (preview-before-upload modal + progress overlay), `references/media-asset-endpoints.md` for serving generated asset files with lazy regeneration, and `references/character-preset-library.md` for the multi-pose preset library pattern.

## Verification Checklist

After scaffolding, verify ALL of these with actual curl commands:
- [ ] `GET /api/v1/health` returns 200 with status and timestamp
- [ ] `GET /api/v1/settings` returns persisted config
- [ ] `POST /api/v1/settings` merges and persists partial updates
- [ ] `GET /api/v1/logs/stream` returns `text/event-stream` content type
- [ ] Server starts without import errors
- [ ] All `__init__.py` files present

## Frontend Template

For the SPA frontend paired with this backend, use `templates/glassmorphism-dark.css` as the visual foundation. It provides the dark glass card aesthetic with sidebar, header, modal, terminal console, and responsive breakpoints. Copy and customize accent colors and sidebar width.

## Requirements

```
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
pydantic>=2.0
```
