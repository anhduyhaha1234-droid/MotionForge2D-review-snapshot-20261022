# M2 Frontend: Multi-Object Display, Preset Manager, Multi-Format Render, Export ZIP

## API Client Extensions (`frontend/src/lib/api.ts`)

### New Types
- `CharacterMapping` — original_name, replacement_asset, voice_config, replacement_config
- `ProjectPreset` — name, description, version, mappings[], dubbing_config
- `PresetInfo` — filename, name, description, mapping_count (for list endpoint)

### New Methods on `api` object
- `getSceneObjects(projectId, sceneId)` → `TrackedObject[]` — GET `/scenes/{id}/objects`
- `savePreset(projectId, name, description?)` → `{ok, path, mapping_count}` — POST `/presets/save`
- `listPresets(projectId)` → `PresetInfo[]` — GET `/presets`
- `applyPreset(projectId, presetFilename)` → `{ok, updated_objects}` — POST `/presets/{filename}/apply`
- `renderWithFormat(projectId, format)` → `{job_id}` — POST `/render?format={fmt}`
- `exportProjectZip(projectId)` → `string` (URL, not fetch) — used as `<a href download>`

**Pattern:** URL-returning helpers (like `exportProjectZip`) return strings for `<a href>` use, not fetch calls.

## Multi-Object Canvas (`CompositeCanvas.tsx`)

### New exported interface
```ts
export interface CompositeObjectConfig {
  objectId: string;
  motion: FrameMotion | null;
  replacementUrl: string | null;
  replacement: ReplacementConfig | null;
}
```

### New prop: `allObjects?: CompositeObjectConfig[]`
When provided, renders all objects instead of the single `replacementUrl`/`frameMotion` pair.

### Implementation pattern
1. `multiObjImgs` state: `Map<string, HTMLImageElement>` — keyed by objectId
2. Single loading effect iterates allObjects, loads each replacementUrl, accumulates into local map, sets state once when all loaded
3. Render effect checks: if `allObjects?.length > 0`, iterate and draw each object (replacement image + bbox + centroid + label), then `return` early (skip single-object path)
4. Dependency array includes both `allObjects` and `multiObjImgs`

### Pitfall: batch image loading
Don't `setMultiObjImgs` per-image — causes N re-renders. Accumulate in local `newMap`, set once when `loaded === total`.

## PresetManager Component (`components/PresetManager.tsx`)

- Standalone component, takes optional `onPresetApplied` callback
- Uses TanStack Query: `queryKey: ["presets", projectId]`
- Two sections: load existing presets (list with "Áp dụng" buttons), save new preset (expandable form)
- Mutations: `saveMut` → invalidate presets query; `applyMut` → invalidate scenes query + call onPresetApplied
- All labels in Vietnamese

## ScreenE Updates

### Format selector
- `renderFormat` state (default "mp4")
- `<select>` dropdown: MP4 (H.264), WebM (VP9), GIF
- Render mutation calls `api.renderWithFormat(projectId, renderFormat)` instead of `api.triggerRender`

### Export ZIP button
- Shows when `renderJob?.status === "completed"`
- `<a href={api.exportProjectZip(projectId)} download>` — direct link, no mutation needed
- Styled with `bg-indigo-600`

## ScreenA Integration
- PresetManager shown conditionally: `{projectId && <PresetManager />}`
- Appears after project creation form, before the component's closing tags

## Verification
- `npx tsc --noEmit` — must pass (TypeScript strict, no `any`)
- `npx next build` — must pass (Next.js 16.x Turbopack)
