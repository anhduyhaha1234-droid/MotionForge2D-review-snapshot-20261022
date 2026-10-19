# M5: Master Performance & Auto-Segment

## Delete Project Endpoint

`DELETE /api/projects/{project_id}` — Deletes project and purges all files from disk.

```python
@router.delete("/{project_id}")
def delete_project(project_id: str) -> dict:
    pwf = get_project_workflow()
    try:
        pwf.get_project(project_id)
    except FileNotFoundError as err:
        raise HTTPException(404, "Project not found") from err

    proj_dir = pwf._project_dir(project_id)
    if proj_dir.exists():
        shutil.rmtree(proj_dir)

    return {"ok": True, "deleted": project_id}
```

**Key points:**
- Must be defined BEFORE `GET /{project_id}` in the route file (FastAPI route ordering)
- Uses `shutil.rmtree` for recursive deletion
- Returns `{"ok": True, "deleted": project_id}` on success
- Returns 404 if project doesn't exist

## Auto-Segment Objects Endpoint

`POST /api/projects/{project_id}/auto-segment-objects?scene_id=0&min_area=500&max_objects=20`

Auto-detects objects in a frame using OpenCV contour detection with Otsu thresholding.

**Algorithm:**
1. Find first frame in scene (try `find_frame_path`, then extract from clip)
2. Downsample to 50% for speed (`scale = 0.5`)
3. Convert to grayscale → GaussianBlur(5,5) → Otsu threshold (BINARY_INV)
4. `findContours` with `RETR_EXTERNAL` + `CHAIN_APPROX_SIMPLE`
5. Filter by `min_area`, limit to `max_objects`
6. Scale bounding boxes back to original resolution
7. Sort by area (largest first)

**Response:**
```json
{
  "scene_id": 0,
  "frame_path": "projects/{id}/frames/scene_0/frame_000000.jpg",
  "objects_found": 3,
  "objects": [
    {
      "object_index": 0,
      "bbox": {"x": 100, "y": 200, "width": 300, "height": 400},
      "area": 120000,
      "centroid": {"x": 250, "y": 400}
    }
  ]
}
```

**Frame fallback chain:**
1. `frames/scene_{id}/frame_000000.{jpg,jpeg,png}` via `find_frame_path`
2. If not found, try extracting from `scenes/scene_{id:03d}.mp4` using `SceneChunkingService.extract_frames_on_demand`
3. If still no frames, return 404

**Dependencies:**
- `cv2` (OpenCV) — contour detection, thresholding, bounding rect
- `numpy` — array operations
- `SceneChunkingService` — on-demand frame extraction from scene clips

## cv2 Thread Optimization

In `app/main.py`, set OpenCV thread count at module level:

```python
import cv2
cv2.setNumThreads(8)
```

This must be set BEFORE importing the FastAPI app to ensure thread pool is configured before any cv2 operations. The value `8` is tuned for the target machine (Windows, multi-core).

## Test Patterns

Tests use the standard fixture pattern (see SKILL.md pitfalls section). Key tests:

1. **Delete nonexistent** → 404
2. **Delete existing** → 200 + verify GET returns 404
3. **Auto-segment no frames** → 404
4. **Auto-segment nonexistent project** → 404

Test file: `tests/test_delete_and_autosegment.py`

## Frontend Implementation

### API Client (`frontend/src/lib/api.ts`)

Added two new methods to the `api` object:

```typescript
deleteProject: (projectId: string) =>
  apiFetch<{ ok: boolean; deleted: string }>(
    `/api/projects/${projectId}`,
    { method: "DELETE" },
  ),

autoSegmentObjects: (projectId: string, sceneId = 0) =>
  apiFetch<{
    scene_id: number;
    objects_found: number;
    objects: Array<{
      object_index: number;
      bbox: { x: number; y: number; width: number; height: number };
      area: number;
      centroid: { x: number; y: number };
    }>;
  }>(
    `/api/projects/${projectId}/auto-segment-objects?scene_id=${sceneId}`,
    { method: "POST" },
  ),
```

### ScreenA Changes

1. **Faster polling**: Changed `setTimeout(r, 1000)` → `setTimeout(r, 300)` and `maxAttempts` 300 → 1000 (total still ~300s)
2. **Delete button on project cards**: Added after the "Mở Lại Dự Án Đang Làm" button with `confirm()` dialog → `api.deleteProject()` → `refetchProjects()`

### ScreenB Changes

1. **State**: `autoObjects` array + `isAutoSegmenting` boolean
2. **Handler**: `handleAutoSegment()` calls `api.autoSegmentObjects(projectId, 0)`, sets `autoObjects` from result
3. **Button**: Purple accent, "🪄 Tự Động Bắt Tất Cả Nhân Vật", disabled while loading
4. **Results list**: Scrollable `max-h-40`, each object clickable to set selection bbox

### ChannelDashboard Changes

Added delete button on each project card: `confirm()` → `api.deleteProject()` → `queryClient.invalidateQueries({ queryKey: ["channel-projects", activeChannelId] })`

### Verification

Both `npx tsc --noEmit` and `npx next build` pass cleanly after all changes.
