# State Rehydration & Persistent Session Pattern

## Problem
When user presses F5 or reopens the app, all Zustand state is lost — they return to the start screen. No way to resume work without re-uploading.

## Solution: localStorage Session + API Rehydration

### Backend: List All Projects Endpoint
`GET /api/projects` returns all projects on disk with summary info (project_id, name, task_status, scenes_count, updated_at, created_at).

**CRITICAL**: This endpoint must be defined BEFORE `/{project_id}` in the router file. FastAPI matches routes in definition order — if `/{project_id}` is defined first, `GET ""` is captured as a valid project_id.

```python
@router.get("")  # ← MUST come before /{project_id}
def list_all_projects() -> list[dict]: ...

@router.get("/{project_id}")
def get_project(project_id: str) -> ProjectData: ...
```

### Frontend: useProjectRehydration Hook
Custom hook at `frontend/src/hooks/useProjectRehydration.ts`:

```ts
const STORAGE_KEY = "motionforge_session";

interface SessionData {
  projectId: string;
  screen: string;
  activeSceneId: number | null;
  timestamp: number;
}

export function saveSession(data: Omit<SessionData, "timestamp">) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...data, timestamp: Date.now() }));
}

export function loadSession(): SessionData | null {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  const data = JSON.parse(raw) as SessionData;
  if (Date.now() - data.timestamp > 7 * 24 * 60 * 60 * 1000) {
    localStorage.removeItem(STORAGE_KEY);
    return null;  // expire after 7 days
  }
  return data;
}

export function clearSession() {
  localStorage.removeItem(STORAGE_KEY);
}
```

### Integration in page.tsx
```tsx
const { isRehydrating } = useProjectRehydration();

// Save session on every state change:
useEffect(() => {
  if (projectId) {
    saveSession({ projectId, screen, activeSceneId: activeSceneId ?? null });
  } else {
    clearSession();
  }
}, [projectId, screen, activeSceneId]);

// Show loading while rehydrating:
if (isRehydrating) {
  return <div>Đang khôi phục phiên làm việc...</div>;
}
```

### Recent Projects List in ScreenA
ScreenA shows "📂 Dự án gần đây" with:
- `useQuery({ queryKey: ["recent-projects"], queryFn: () => api.listAllProjects() })`
- Each project card: name, status badge (⚪🟡🔵🟢), scene count, "▶️ Tiếp tục" button
- Resume logic: determine screen based on project state (completed→preview, has objects→replacement, has scenes→selection)

### Patterns
- **7-day expiry** on localStorage session data
- **try/catch** around localStorage access (may be unavailable in some environments)
- **TanStack Query** for recent projects list (staleTime: 30s)
- **Auto-navigate** based on project task_status when resuming
- **`created_at` / `updated_at`** timestamps on ProjectData for sorting and display
