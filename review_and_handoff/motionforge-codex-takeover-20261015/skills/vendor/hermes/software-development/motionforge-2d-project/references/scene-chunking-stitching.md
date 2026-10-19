# Scene Chunking & Stitching Architecture

## Services
- `app/workflow/scene_chunking_service.py` — `SceneChunkingService(config)` detects scenes via PySceneDetect, extracts per-scene audio with FFmpeg
- `app/workflow/scene_stitch_service.py` — `SceneStitchService(config)` concatenates rendered scene videos with optional per-scene audio re-mux

## Schema additions (app/schemas/__init__.py)
- `SceneStatus` enum: `PENDING`, `DRAFT`, `APPROVED`
- `SceneDetail` model: extends `SceneInfo` with `status`, `audio_path`, `notes`
- `ProjectData.scene_details: list[SceneDetail]` field

## API endpoints (app/api/routes/projects.py)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/{project_id}/scenes/chunk` | Re-chunk video, extract audio per scene |
| GET | `/{project_id}/scenes/details` | Get scene details with status |
| PATCH | `/{project_id}/scenes/{scene_id}/status` | Update scene status |
| GET | `/{project_id}/scenes/{scene_id}/audio` | Serve scene audio file |
| POST | `/{project_id}/scenes/stitch` | Stitch approved scenes into final video |

## Audio extraction flow
1. `chunk_video()` calls `detect_scenes()` → `list[SceneInfo]`
2. Checks for audio stream via `ffprobe -select_streams a`
3. For each scene: `ffmpeg -ss START -t DURATION -vn -acodec copy scene_NNN.aac`
4. Audio files written to `project_dir/audio/scene_NNN.aac`
5. `SceneDetail.audio_path` stores relative path

## Stitching flow
1. `stitch_with_audio()` iterates sorted scenes
2. Looks for rendered video at `renders/scene_{id}_final.mp4` (fallback: `_preview.mp4`)
3. If scene audio exists, merges video+audio with `-c:v copy -c:a aac -shortest`
4. Writes concat list, runs `ffmpeg -f concat -safe 0 -c copy`
5. Cleans up temp directory

## Frontend components
- `SceneSelector.tsx` — scene list with status badges (🟢🟡⚪), chunk button, approve per scene
- `ScenePreview.tsx` — `<audio>` element that auto-loads scene audio when `activeSceneId` changes
- `AssemblyModal.tsx` — modal showing all scenes + status, stitch button (enabled only when all APPROVED)
- `ScreenD.tsx` — 3-column layout: scene sidebar | canvas | controls, with approve button
- `page.tsx` — floating "🎬 Ghép video" FAB that opens AssemblyModal

## Frontend API additions (api.ts)
```
chunkScenes(projectId, threshold?) → {scene_count, scenes[]}
getSceneDetails(projectId) → SceneDetail[]
updateSceneStatus(projectId, sceneId, status, notes?) → {ok}
getSceneAudioUrl(projectId, sceneId) → string (direct URL)
stitchScenes(projectId) → {ok, output_path}
```

## Zustand store additions (project.ts)
```
scenes: SceneDetail[]
activeSceneId: number | null
setScenes(scenes)
setActiveSceneId(id)
```

## Test pattern
- Tests use `fixture_b/input.mp4` if available, otherwise `pytest.skip`
- Test `tmp_path` for audio output directory
- Stitch tests verify `FileNotFoundError` when no videos exist
- 7 tests total: 5 chunking + 2 stitching
