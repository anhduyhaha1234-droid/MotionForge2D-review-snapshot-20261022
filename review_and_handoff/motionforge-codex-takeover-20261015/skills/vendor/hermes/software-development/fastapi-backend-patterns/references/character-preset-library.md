# Character Preset Library Pattern (MotionForge2D)

Session-derived pattern for "character library / multi-pose template" features
with zero shipped binary assets: generate pose PNGs server-side with OpenCV,
expose a schema-validated reference-pack API, and let an "auto-match" endpoint
pick poses from bbox geometry.

## 1. Schema — reference pack (`app/schemas/__init__.py`)

```python
class CharacterPosePaths(BaseModel):
    sitting: str = "sitting.png"
    standing: str = "standing.png"
    three_quarter: str = "three_quarter.png"
    walking: str = "walking.png"
    talking: str = "talking.png"
    back: str = "back.png"

class CharacterReferencePack(BaseModel):
    character_id: str
    name: str
    poses: CharacterPosePaths
```

## 2. Asset generation — transparent PNGs with cv2

Define packs as dicts `id -> {label, poses: {pose: filename}}`. Generate on
first access (`ensure_assets`): draw colored shapes on an RGB `body` canvas,
then build the alpha channel from nonzero pixels:

```python
canvas = np.zeros((h, w, 4), dtype=np.uint8)
body = np.zeros((h, w, 3), dtype=np.uint8)
_draw_character(body, color, pose)                 # pose-specific rectangles/ellipses
canvas[:, :, :3] = body
canvas[:, :, 3] = np.where(np.any(body > 0, axis=2), 255, 0).astype(np.uint8)
cv2.imwrite(str(self.assets_root / filename), canvas)
```

Canvas size per pose: tall poses (standing/walking/three_quarter) 512x768,
sitting 768x512, balanced (talking/back) 640x640.

## 3. Pose heuristic (`auto_pose_for_bbox`)

```python
if width <= 0 or height <= 0:
    return "talking"
if width > height * 1.1:
    return "sitting"
if height > width * 1.3:
    return "standing"
# centroid far from bbox center -> looking away
if centroid_x is not None and bbox_x is not None and width > 0:
    if abs(centroid_x - (bbox_x + width / 2.0)) > width * 0.3:
        return "back"
return "talking"
```

BOUNDARY GOTCHA: `auto_pose_for_bbox(220, 200)` does NOT return "sitting"
(`220 > 220` is False). Test with values clearly past the threshold
(e.g. `250, 200`), and check the math before "fixing" the production code.

## 4. Endpoint ordering + full path params

- Static list route `GET /presets/characters` MUST be declared before any
  dynamic `/{project_id}` route (same shadowing rule as pitfall 16).
- Nested apply route MUST include the parent param in the decorator path:
  `@router.post("/{project_id}/presets/characters/{set_key}/{pose}/apply")`.
  Omitting `{project_id}` while the signature declares it -> every real call
  404s even though the route is listed first. Verify with a route dump:
  `python -c "from app.api.routes import projects; [print(repr(r.path)) for r in projects.router.routes]"`.
- Add BOTH trailing-slash variants for POST endpoints (`redirect_slashes=False`).

## 5. Apply endpoint

Copy the pose PNG into the object's replacement slot, set/refresh
`replacement_config.mode = ReplacementMode.STATIC_ASSET` (enum member, NOT
raw string — see pitfall 23), save project, return `{status, object_id,
asset_path, pose, set_key}`. Target `proj.objects[0]` as the "active object".

## 6. `auto_match_character` (apply pose to ALL scenes)

- Extract source bbox: selection bbox, else first motion frame with
  `centroid_x > 0`.
- Collect centroid + bbox coords and pass to `auto_pose_for_bbox`.
- Copy the matched pose PNG to every other-scene object's
  `objects/<id>/replacement.png` and set static_asset config.
- NEVER hard-400 when motion is missing (pitfall 20): fall back to selection
  bbox, still apply config to all scenes, return `{status: ok, matched,
  count, pose, warning}`.
- Assign enum-typed fields with the enum member to avoid
  `PydanticSerializationUnexpectedValue` warnings on every save.

## 7. Frontend cache-buster

```typescript
const replacementUrl = projectId && objectId && replacement.asset_path
  ? `${api.getReplacementImageUrl(projectId, objectId)}?t=${Date.now()}&v=${encodeURIComponent(replacement.asset_path)}`
  : null;
```

`v=asset_path` is the key: when the uploaded asset changes, the URL changes,
the React effect re-runs, and the canvas redraws the new image immediately.

## 8. Tests (`tests/test_preset_manager.py`)

- heuristic: wide -> sitting, tall -> standing, balanced -> talking,
  centroid-offset -> back, zero-size -> talking (no crash)
- pack structure: exactly 3 packs, each with the 6 pose keys
- schema: `CharacterReferencePack` round-trips; `poses.model_dump()` has 6 keys
- endpoints: list returns 3 packs x 6 poses; image endpoint 200 image/png for
  every set+pose (loop); apply endpoint 200 + `object_id` + `asset_path`
- auto-match returns `pose` in body when motion exists, `status=ok` when not
