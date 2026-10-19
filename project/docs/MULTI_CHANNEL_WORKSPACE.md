# Multi-Channel Workspace Dashboard

**Date:** 2026-07-31  
**Status:** 🔄 In Progress

---

## Architecture

```
🏢 WORKSPACE DASHBOARD
 ├── 📺 Channel 1: "Hoạt Hình Tiếng Anh (US/UK)"
 │    ├─ 📄 Project 1: "Tập 1..." → 🟢 Hoàn thành
 │    └─ 📄 Project 2: "Tập 2..." → 🟡 Đang Xử Lý
 │
 ├── 📺 Channel 2: "Hoạt Hình Tây Ban Nha (ES)"
 │    ├─ 📄 Project 3: "Episode 10..." → 🔵 Sẵn sàng ghép
 │    └─ 📄 Project 4: "Episode 11..." → ⚪ Bản Nháp
```

## Features

### 1. Channel Workspaces
- CRUD: create, list, get, delete
- Each channel: name, target_lang, default_preset_id
- Projects assigned to channels via channel_id

### 2. Task Status Board
- ⚪ `draft` — Bản Nháp (new upload/ingest)
- 🟡 `in_progress` — Đang Xử Lý
- 🔵 `ready_to_stitch` — Sẵn sàng ghép
- 🟢 `completed` — Hoàn thành

### 3. 1-Click Resume
- Auto-save to project.json
- "▶️ Tiếp tục làm việc" button loads project and opens correct screen

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/projects/channels | Create channel |
| GET | /api/projects/channels | List channels |
| GET | /api/projects/channels/{id}/projects | List channel projects |
| DELETE | /api/projects/channels/{id} | Delete channel |
| PATCH | /api/projects/{id}/task-status | Update task status |
| PATCH | /api/projects/{id}/assign-channel | Assign project to channel |

## Files

### Backend
- `app/schemas/__init__.py` — TaskStatus, ChannelWorkspace
- `app/workflow/channel_service.py` — ChannelService CRUD
- `app/api/routes/projects.py` — 6 new endpoints
- `tests/test_channel_workspace.py` — 8 tests

### Frontend
- `frontend/src/components/ChannelDashboard.tsx` — Dashboard UI
- `frontend/src/lib/api.ts` — Channel types + methods
- `frontend/src/stores/project.ts` — activeChannelId
- `frontend/src/app/page.tsx` — Dashboard button
- `frontend/src/components/ScreenA.tsx` — Auto task-status update
