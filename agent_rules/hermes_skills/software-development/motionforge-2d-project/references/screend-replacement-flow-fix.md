# ScreenD replacement flow — 422 + 404 fixes (M7.5)

Session 2026-08-02. User reported after clicking "Xác Nhận Thay Thế": nothing appears, no success feedback; "Áp dụng" button also dead.

## Root causes (3 independent bugs)

1. **422 on PATCH replacement-settings** — backend `ReplacementSettingsRequest` wraps config:
   ```python
   class ReplacementSettingsRequest(BaseModel):
       replacement_config: ReplacementConfig
   ```
   Frontend sent flat settings → FastAPI 422 `"loc":["body","replacement_config"],"msg":"Field required"`.
   Fix in `frontend/src/lib/api.ts`:
   ```ts
   body: JSON.stringify({ replacement_config: settings })
   ```

2. **replacementUrl hardcoded `http://localhost:8000`** in ScreenD.tsx — backend runs on 8002, so the replacement image never loaded after upload (silent 404 in `<img>`). Fix: use `api.getReplacementImageUrl(projectId, objectId)` which uses `API_BASE`.

3. **GET /objects/{id}/replacement-image did not exist** → 404. Frontend helper pointed at a route the backend never had. Added:
   ```python
   @router.get("/{project_id}/objects/{object_id}/replacement-image")
   @router.get("/{project_id}/objects/{object_id}/replacement-image/")
   def get_replacement_image(project_id, object_id) -> FileResponse:
       # 1. serve objects/<oid>/replacement.* (glob, first match)
       # 2. fallback: asset_path from replacement_config (skip the "/replacements/test.png" placeholder)
       # 3. else 404
   ```

## Also fixed this session

- **gpu-info 404**: `GET /gpu-info` declared AFTER `/{project_id}` → captured as project_id. Moved above parameterized routes (right after `list_all_projects`). `detect_nvenc()` returns `EncoderInfo` **dataclass** (`has_nvenc`, `gpu_name`, `encoder_name`) — not a dict.
- **Dedupe on create_object**: same bbox/scene returns existing object (`duplicate: True`) instead of creating a twin.
- **cv2.imwrite(BytesIO) fails** in tests → use `cv2.imencode(".png", img)` + `.tobytes()`.

## Test recipe (test_replacement_image_served_after_upload)

- Create project via API, write synthetic frame (WHITE bg + dark object) at `deps._config.project_root/projects/{pid}/frames/scene_0/frame_000000.png`
- POST /objects (bounding_box mode) → 201, oid
- Build PNG bytes via `cv2.imencode`, POST `files={"file": ("char.png", png_bytes, "image/png")}` → 200
- GET `/objects/{oid}/replacement-image` and `/` → assert 200, `content-type == image/png`, magic bytes `b"\x89PNG\r\n\x1a\n"`

## Live-verification pattern (do this instead of assuming)

1. `curl /health` — is backend up?
2. `curl -X PATCH .../replacement-settings -d '{"replacement_config":{...}}'` — expect 200
3. `curl -o /dev/null -w "%{http_code} %{content_type}" .../replacement-image` — expect `200 image/png`
4. If a compound `curl` chain exits 23 with `-w`, it's a write-error on the last `-w` line — re-run the failing curl alone before blaming the API.
