# State Rehydration & Persistent Session Fix

**Date:** 2026-07-31  
**Status:** 🔄 In Progress

---

## Problem

When user presses F5 or reopens the app, all state is lost — they return to the start screen. No way to resume work on a project without re-uploading.

## Solution

### 1. Backend: List All Projects
- `GET /api/projects` — returns all projects on disk with summary info
- Each project: project_id, name, task_status, scenes_count, updated_at

### 2. Frontend: useProjectRehydration Hook
- Saves `projectId`, `screen`, `activeSceneId` to localStorage
- On mount: reads localStorage → calls `GET /api/projects/{id}` → restores Zustand store
- User stays on the screen they were working on
- 7-day expiry on session data

### 3. Recent Projects UI
- "📂 Dự án gần đây" card list on ScreenA
- Shows: name, status badge, scene count, "▶️ Tiếp tục" button
- Auto-navigates to appropriate screen based on project status

### 4. Session Persistence
- `saveSession()` called on every projectId/screen/activeSceneId change
- `clearSession()` called when project is cleared
- `loadSession()` on app mount with 7-day expiry

## Files

### Backend
- `app/api/routes/projects.py` — `GET /api/projects` endpoint
- `tests/test_list_projects.py` — unit tests

### Frontend
- `frontend/src/hooks/useProjectRehydration.ts` — NEW: session hook
- `frontend/src/lib/api.ts` — listAllProjects + ProjectSummary
- `frontend/src/app/page.tsx` — rehydration + session saving
- `frontend/src/components/ScreenA.tsx` — recent projects list
