# Multi-Channel Workspace Dashboard — Implementation Reference

## Overview
Channel-based project organization UI. Each channel maps to a target language; projects are grouped under channels with task_status tracking.

## Backend Implementation

### Schema additions (`app/schemas/__init__.py`)
- `TaskStatus(str, Enum)`: DRAFT, IN_PROGRESS, READY_TO_STITCH, COMPLETED — added before ProjectData
- `ChannelWorkspace(BaseModel)`: channel_id, name, target_lang, default_preset_id, created_at
- `ProjectData` gained: `channel_id: str = ""`, `task_status: str = "draft"`

### Service (`app/workflow/channel_service.py`)
- `ChannelService(config: AppConfig)` — CRUD for channel workspaces
- Persistence: `channels.json` in project_root
- IDs: `uuid.uuid4().hex[:12]`, timestamps: `datetime.now(UTC).isoformat()`
- `get_projects_for_channel()` scans `projects/*/project.json` for matching channel_id

### API endpoints (`app/api/routes/projects.py`)
- POST `/channels` — create channel
- GET `/channels` — list channels
- GET `/channels/{id}/projects` — list projects in channel
- DELETE `/channels/{id}` — delete channel
- PATCH `/{id}/task-status` — update project task status (validates against set)
- PATCH `/{id}/assign-channel` — assign project to channel
- All service imports are lazy (inside endpoint functions) with `# noqa: PLC0415`

### Tests (`tests/test_channel_workspace.py`)
- TestChannelCRUD: create, list, get, get-missing, delete, delete-missing
- TestTaskStatus: enum values
- TestChannelWorkspace: default values

## Frontend Implementation

### Files Modified/Created
- `frontend/src/lib/api.ts` — added `ChannelWorkspace`, `ChannelProject` interfaces + 6 API methods
- `frontend/src/stores/project.ts` — added `activeChannelId` state + `setActiveChannelId` action
- `frontend/src/components/ChannelDashboard.tsx` — new full-screen modal component
- `frontend/src/app/page.tsx` — integrated dashboard with floating button + ChannelDashboard overlay
- `frontend/src/components/ScreenA.tsx` — auto-update task status to "in_progress" after ingest

## API Types

```ts
interface ChannelWorkspace {
  channel_id: string;
  name: string;
  target_lang: string;
  default_preset_id: string;
  created_at: string;
}

interface ChannelProject {
  project_id: string;
  name: string;
  task_status: "draft" | "in_progress" | "ready_to_stitch" | "completed";
  created_at: string;
  scene_count: number;
  object_count: number;
}
```

## API Methods (added to `api` object in api.ts)
- `createChannel(name, targetLang?)` → POST `/api/projects/channels`
- `listChannels()` → GET `/api/projects/channels`
- `getChannelProjects(channelId)` → GET `/api/projects/channels/{id}/projects`
- `deleteChannel(channelId)` → DELETE `/api/projects/channels/{id}`
- `updateTaskStatus(projectId, taskStatus)` → PATCH `/api/projects/{id}/task-status`
- `assignChannel(projectId, channelId)` → PATCH `/api/projects/{id}/assign-channel?channel_id=...`

## Task Status Enum
| Status | Label (VI) | Emoji | Color |
|--------|-----------|-------|-------|
| `draft` | Bản Nháp | ⚪ | gray-400 |
| `in_progress` | Đang Xử Lý | 🟡 | yellow-300 |
| `ready_to_stitch` | Sẵn sàng ghép | 🔵 | blue-300 |
| `completed` | Hoàn thành | 🟢 | green-300 |

## Component Architecture

### ChannelDashboard (full-screen modal)
- **Left sidebar (w-64)**: Channel list with active selection highlight (blue ring), create channel form with name input + language select, delete button
- **Main area**: Project grid (responsive 1/2/3 columns) with status-colored cards, progress bars, "Tiếp tục làm việc" (continue working) button per project
- **React Query**: `queryKey: ["channels"]` for channel list, `queryKey: ["channel-projects", activeChannelId]` for projects
- **Mutations**: createMut (invalidates channels, selects new), deleteMut (invalidates channels, clears selection)

### Integration in page.tsx
- Floating button at `fixed top-4 right-4` opens dashboard
- `onResumeProject` callback uses `useProjectStore.getState()` to access store outside render context
- Pattern: `api.getProject(pid).then(proj => { store.setProject(proj); store.setScreen("selection") })`

## Pattern: Extending Zustand Store with New State Slice
When adding new domain state (e.g., `activeChannelId`):
1. Add field to `ProjectState` interface: `activeChannelId: string | null;`
2. Add setter to interface: `setActiveChannelId: (id: string | null) => void;`
3. Add initial value in `create()`: `activeChannelId: null,`
4. Add setter implementation: `setActiveChannelId: (id) => set({ activeChannelId: id }),`
5. Keep the new field grouped with its domain (e.g., after `// Channel` comment)

## Pattern: Accessing Zustand Store Outside React
When passing callbacks to non-React contexts (e.g., `onResumeProject` prop), use `useProjectStore.getState()`:
```tsx
onResumeProject={(pid) => {
  const store = useProjectStore.getState();
  store.setProjectId(pid);
  api.getProject(pid).then((proj) => {
    store.setProject(proj);
    store.setScreen("selection");
  });
}}
```
This avoids stale closures and works correctly in event handlers.
