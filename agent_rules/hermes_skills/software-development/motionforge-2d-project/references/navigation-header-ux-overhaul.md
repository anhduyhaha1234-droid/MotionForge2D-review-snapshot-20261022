# NavigationHeader & Frontend UX Overhaul

## NavigationHeader Component

Sticky top navigation bar shown on all screens except "start". Provides:
- **Back button**: Returns to start screen via `setScreen("start")`
- **Project info**: Project name, truncated project ID (8 chars), scene counter
- **Scene navigation**: Prev/Next scene buttons with disabled states

### Store dependencies
```tsx
const { projectId, project, screen, setScreen, activeSceneId, setActiveSceneId } = useProjectStore();
```

### Rendering logic
- Returns `null` if no `projectId` or `screen === "start"`
- Scene counter shows `Cảnh #{activeSceneId + 1} / {scenes.length}` (1-indexed for display)
- Prev/Next buttons disabled at boundaries (`currentSceneIdx <= 0` / `>= scenes.length - 1`)

### Styling
- `sticky top-0 z-40` — stays at top, above content but below modals
- `bg-slate-950/95 backdrop-blur` — semi-transparent dark with blur
- `border-b border-slate-800` — subtle bottom border

### Integration in page.tsx
Place `<NavigationHeader />` before `<ScreenRouter />` in the JSX:
```tsx
<NavigationHeader />
<ScreenRouter />
```

## Auto-Mask Preview on Point+ Click

When user clicks canvas in Point+ mode, automatically trigger mask preview API call instead of requiring separate "Xem mask" button click.

### Pattern: Ref flag + useEffect
1. `autoPreviewRef = useRef(false)` — flag set in click handler
2. `setPoints(...)` in click handler + `autoPreviewRef.current = true`
3. `useEffect` on `[points, previewMut]` checks flag, calls `previewMut.mutate()`, resets flag

### Why this works
- React batches state updates — `points` in the useEffect has the new point
- `useMutation` re-renders with latest `mutationFn` closure
- Ref flag ensures only Point+ clicks trigger auto-preview (not negative points or other state changes)

## Button Micro-Descriptions

Small gray text under action buttons explaining what each tool does. Convention:
- `text-[10px] text-gray-500 mt-1` — consistent styling
- Vietnamese, action-oriented, 1 line max
- Switch tool grids from `grid grid-cols-2` to `space-y-2` when adding descriptions

### Example descriptions
| Button | Description |
|--------|-------------|
| Điểm + | Click 1 điểm màu xanh trên thân nhân vật đối thủ. |
| Điểm − | Click điểm màu đỏ trên phông nền xung quanh để loại trừ. |
| Hộp | Kéo ô hình chữ nhật bao trùm toàn thân nhân vật. |
| Xem mask | Xem trước đường khoanh màu tím bao quanh nhân vật. |
| Chấp nhận & Tách | Xác nhận chọn & AI tự động theo vết (tracking) qua các frame. |
| 🪄 Tự Động Bắt Tất Cả Nhân Vật | AI tự động quét & bóc tách toàn bộ nhân vật, bàn ghế có trong cảnh mà không cần chấm điểm thủ công. |
