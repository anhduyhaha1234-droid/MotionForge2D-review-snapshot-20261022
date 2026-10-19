# Milestone 1A — API Inventory

**Dự án:** MotionForge 2D
**Milestone:** 1A — Object Extraction Review UI
**Tổng số endpoints:** 18
**OpenAPI spec:** `artifacts/milestone_1a/openapi.json`

---

## Danh sách API Endpoints

| # | Method | Endpoint | Request Body | Response | Returns Job? | Has Test? | UI Consumer |
|---|--------|----------|--------------|----------|:------------:|:---------:|-------------|
| 1 | `GET` | `/health` | — | `{"status": "ok"}` | No | ✅ | — |
| 2 | `POST` | `/api/projects` | `{}` | `201` Project object | No | ✅ | Screen A |
| 3 | `POST` | `/api/projects/{id}/video` | multipart file | `200` | No | ✅ | Screen A |
| 4 | `POST` | `/api/projects/{id}/ingest` | — | `200` JobInfo | **Yes** | ✅ | Screen A |
| 5 | `GET` | `/api/projects/{id}` | — | `200` Project detail | No | ✅ | Screen A |
| 6 | `GET` | `/api/projects/{id}/scenes` | — | `200` Scene list | No | ✅ | Screen B |
| 7 | `GET` | `/api/projects/{id}/frames/{idx}` | — | `200` FileResponse (image/png) | No | ✅ | Screen B |
| 8 | `POST` | `/api/projects/{id}/objects/preview-mask` | points, bbox | `200` mask data | No | ✅ | Screen B |
| 9 | `POST` | `/api/projects/{id}/objects` | prompt points/bbox | `201` TrackedObject | No | ✅ | Screen B |
| 10 | `POST` | `/api/projects/{id}/objects/{oid}/propagate` | — | `200` JobInfo | **Yes** | ✅ | Screen B |
| 11 | `GET` | `/api/projects/{id}/objects/{oid}` | — | `200` Object detail | No | ✅ | Screen C |
| 12 | `GET` | `/api/projects/{id}/objects/{oid}/gallery` | — | `200` CropManifest | No | ✅ | Screen C |
| 13 | `POST` | `/api/projects/{id}/objects/{oid}/replacement` | multipart file | `200` | No | ✅ | Screen D |
| 14 | `PATCH` | `/api/projects/{id}/objects/{oid}/replacement-settings` | ReplacementConfig | `200` | No | ✅ | Screen D |
| 15 | `POST` | `/api/projects/{id}/preview` | — | `200` JobInfo | **Yes** | ✅ | Screen E |
| 16 | `POST` | `/api/projects/{id}/render` | — | `200` JobInfo | **Yes** | ✅ | Screen E |
| 17 | `GET` | `/api/jobs/{id}` | — | `200` JobInfo | No | ✅ | All (polling) |
| 18 | `POST` | `/api/jobs/{id}/cancel` | — | `200` | No | ✅ | Screen E |

---

## Phân loại theo tính năng

### Project Management (5 endpoints)
- `POST /api/projects` — Tạo dự án mới
- `POST /api/projects/{id}/video` — Upload video nguồn
- `POST /api/projects/{id}/ingest` — Phân tích video (trích frame, detect scene) → **Job**
- `GET /api/projects/{id}` — Lấy thông tin dự án
- `GET /api/projects/{id}/scenes` — Danh sách scene

### Frame Access (1 endpoint)
- `GET /api/projects/{id}/frames/{idx}` — Lấy frame theo index (PNG)

### Object Segmentation (3 endpoints)
- `POST /api/.../objects/preview-mask` — Xem trước mask SAM2
- `POST /api/.../objects` — Tạo tracked object
- `POST /api/.../objects/{oid}/propagate` — Chạy SAM2 propagation → **Job**

### Object Info & Gallery (2 endpoints)
- `GET /api/.../objects/{oid}` — Chi tiết object (tracking status)
- `GET /api/.../objects/{oid}/gallery` — Gallery crop đại diện

### Replacement (2 endpoints)
- `POST /api/.../objects/{oid}/replacement` — Upload asset thay thế
- `PATCH /api/.../objects/{oid}/replacement-settings` — Cập nhật transform

### Rendering (2 endpoints)
- `POST /api/.../preview` — Render preview nhanh → **Job**
- `POST /api/.../render` — Render chất lượng cuối → **Job**

### Job Management (2 endpoints)
- `GET /api/jobs/{id}` — Kiểm tra trạng thái job
- `POST /api/jobs/{id}/cancel` — Hủy job đang chạy

### Health (1 endpoint)
- `GET /health` — Health check

---

## Async Job Pattern

4 endpoints trả về `JobInfo` (async jobs):
1. `POST /api/projects/{id}/ingest`
2. `POST /api/.../objects/{oid}/propagate`
3. `POST /api/.../preview`
4. `POST /api/.../render`

Client poll `GET /api/jobs/{id}` để theo dõi tiến trình. Job states: `queued → running → completed | failed | cancelled`.
