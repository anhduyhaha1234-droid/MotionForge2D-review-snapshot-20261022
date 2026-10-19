# Return-Shape Discipline: create returns {id, project}, deletes return {status, project}

Session detail from MotionForge2D (Milestone "delete object / 1-click select" work).

## The failure

Backend `POST /api/projects/{id}/objects` returns:

```python
return {"object_id": obj_id, "project": data.model_dump()}
```

Frontend `api.ts` declared it as `apiFetch<TrackedObject>`. Two bugs followed:

1. `tsc` failed: `Argument of type '{ object_id, project }' is not assignable to parameter of type 'TrackedObject'` wherever the caller did `setActiveObject(obj)`.
2. Even if it compiled, the caller had NO `name`/`kind`/`selection`/`scene_id` — the store's `activeObject` was half-populated.

## The fix (pattern)

Declare the real return type, then locate the full entity inside the returned project:

```ts
// api.ts
createObject: (projectId, obj) =>
  apiFetch<{ object_id: string; project: ProjectData }>(
    `/api/projects/${projectId}/objects`, { method: "POST", ... }
  ),
```

```tsx
// caller
const res = await api.createObject(projectId, {...});
const created = res.project.objects.find((o) => o.object_id === res.object_id);
if (created) setActiveObject(created);
setProject(res.project);          // update list state from the SAME response
```

Never re-fetch `GET /project` after a create — the create response already carries the updated project; an extra round-trip is slower and can race the write.

## DELETE endpoints should return the full updated project too

So the UI can rehydrate from one response:

```python
@router.delete("/{project_id}/objects")           # + trailing-slash alias
@router.delete("/{project_id}/objects/")
def clear_objects(project_id):
    proj.objects = []
    pwf._save_project(project_id, proj)
    shutil.rmtree(proj_dir / "objects", ignore_errors=True)
    return {"status": "ok", "project": proj.model_dump()}   # ← not just {"status"}

@router.delete("/{project_id}/objects/{object_id}")          # + trailing-slash alias
@router.delete("/{project_id}/objects/{object_id}/")
def delete_single_object(project_id, object_id):
    proj.objects = [o for o in proj.objects if o.object_id != object_id]
    pwf._save_project(project_id, proj)
    shutil.rmtree(proj_dir / "objects" / object_id, ignore_errors=True)
    return {"status": "ok", "project": proj.model_dump()}
```

Frontend side:

```ts
const res = await api.deleteObject(projectId, objectId);
setProject(res.project);                       // objects list now correct
if (activeObject?.object_id === objectId) setActiveObject(null);
```

Rule: any mutation endpoint (create/delete/update) that the UI immediately reflects should return the **complete updated aggregate** (`project`), not a bare `{ok}`/`{status}`. One response = one `setProject` = no refetch race.

## Trailing-slash twin on DELETE, same as POST

`router.delete("/{project_id}/objects/{object_id}")` + `router.delete("/{project_id}/objects/{object_id}/")` — mirror the POST alias rule (skill pitfall 13). Test both variants.

## Test coverage that caught the behavior

- `test_delete_single_object`: create 2 objects → DELETE one → assert `resp.json()["project"]["objects"]` keeps the other, drops the deleted id; repeat for trailing slash.
- `test_clear_all_objects`: DELETE all → assert `resp.json()["project"]["objects"] == []` AND `GET /objects` returns `[]`.
- `test_auto_segment_returns_crop_b64`: decode `crop_png_base64`, assert PNG magic bytes `\x89PNG\r\n\x1a\n`.

## Synthetic-frame test helper (no real video needed)

To exercise create/crop/delete without a real upload, write a frame directly into the isolated test root before POSTing:

```python
from app.api import deps
frame_dir = deps._config.project_root / "projects" / pid / "frames" / "scene_0"
frame_dir.mkdir(parents=True, exist_ok=True)
frame = np.full((200, 200, 3), 255, dtype=np.uint8)      # WHITE bg (Otsu+INV on black bg
frame[50:150, 50:150] = (0, 0, 0)                        # yields one full-frame contour)
cv2.imwrite(str(frame_dir / "frame_000000.png"), frame)
```

White background + dark object is the reliable synthetic frame for contour tests; black-bg + bright object merges into one giant contour under `THRESH_BINARY_INV + Otsu`.

## Patch-tool hazard when editing import blocks

A `patch` replace on a two-line import (`"import shutil\nimport uuid\n"` → dropped newline) produced `import uuidfrom pathlib import Path` — a syntax error that then had to be repaired. When editing import blocks with `patch`, include the FULL block (all lines + the blank line) in `old_string`, or use a Python script. After any import edit, immediately `python -c "import <module>"` to prove the file parses before proceeding.
