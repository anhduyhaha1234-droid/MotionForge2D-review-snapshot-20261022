# Milestone 1A — UI Flow

**Dự án:** MotionForge 2D
**Milestone:** 1A — Object Extraction Review UI

---

## Tổng quan

MotionForge 2D có 5 màn hình (Screen A–E), điều hướng tuần tự qua Zustand store. Người dùng đi từ upload video → chọn đối tượng → xem kết quả trích xuất → thay thế → render.

---

## Screen A — Project Start

**File:** `frontend/src/components/ScreenA.tsx`
**Chức năng:** Upload video và khởi chạy ingest

### Người dùng thấy:
- Khu vực kéo-thả (drag & drop) để chọn file video
- Nút "Tạo dự án" để bắt đầu
- Thanh tiến trình ingest sau khi upload

### Người dùng thao tác:
1. Kéo file video vào vùng upload (hoặc click để chọn)
2. Nhấn "Tạo dự án" → `POST /api/projects` tạo project mới
3. Video được upload qua `POST /api/projects/{id}/video`
4. Ingest chạy qua `POST /api/projects/{id}/ingest` (returns job)
5. Khi job hoàn tất → tự động chuyển sang Screen B

### API liên quan:
- `POST /api/projects`
- `POST /api/projects/{id}/video`
- `POST /api/projects/{id}/ingest`
- `GET /api/jobs/{id}` (polling)

---

## Screen B — Object Selection

**File:** `frontend/src/components/ScreenB.tsx`
**Chức năng:** Chọn đối tượng trên canvas để trích xuất

### Người dùng thấy:
- Canvas hiển thị frame từ video
- Công cụ chọn: click điểm (point), click điểm âm (negative), vẽ bounding box
- Xem trước mask SAM2 real-time
- Nút "Tạo đối tượng"

### Người dùng thao tác:
1. Click trên canvas để đặt điểm prompt (point/negative/bbox)
2. Mask preview hiển thị qua `POST /api/.../preview-mask` (SAM2 inference)
3. Nhấn "Tạo đối tượng" → `POST /api/.../objects`
4. Propagation chạy qua `POST /api/.../propagate` (SAM2, ~60s cho 180 frames)
5. Khi hoàn tất → chuyển sang Screen C

### API liên quan:
- `GET /api/projects/{id}/scenes`
- `GET /api/projects/{id}/frames/{idx}`
- `POST /api/projects/{id}/objects/preview-mask`
- `POST /api/projects/{id}/objects`
- `POST /api/projects/{id}/objects/{oid}/propagate`
- `GET /api/jobs/{id}`

---

## Screen C — Extraction Review

**File:** `frontend/src/components/ScreenC.tsx`
**Chức năng:** Xem kết quả trích xuất đối tượng (gallery crops)

### Người dùng thấy:
- Gallery hiển thị 20 crop đại diện + thumbnail
- Thông tin tracking: 180/180 frames tracked (100%)
- Nút "Tiếp tục" để sang bước thay thế

### Người dùng thao tác:
1. Xem gallery crops từ `GET /api/.../gallery`
2. Kiểm tra chất lượng mask/tracking
3. Nhấn "Tiếp tục" → chuyển sang Screen D

### API liên quan:
- `GET /api/projects/{id}/objects/{oid}`
- `GET /api/projects/{id}/objects/{oid}/gallery`

---

## Screen D — Replacement Controls

**File:** `frontend/src/components/ScreenD.tsx`
**Chức năng:** Cấu hình thay thế đối tượng

### Người dùng thấy:
- Canvas preview (hiện tại hiển thị placeholder)
- Các điều khiển: anchor, offset, scale, rotation, opacity, fit mode
- Nút upload asset thay thế (static PNG)
- Nút "Preview" và "Render"

### Người dùng thao tác:
1. Upload ảnh PNG thay thế qua `POST /api/.../replacement`
2. Điều chỉnh tham số transform:
   - **Anchor:** vị trí neo (center, top-left, etc.)
   - **Offset:** dịch chuyển X/Y
   - **Scale:** tỷ lệ phóng to/thu nhỏ
   - **Rotation:** góc quay (degrees)
   - **Opacity:** độ trong suốt (0–1)
   - **Fit mode:** cách fit vào mask
3. Nhấn "Lưu cài đặt" → `PATCH /api/.../replacement-settings`
4. Nhấn "Preview" hoặc chuyển sang Screen E

### API liên quan:
- `POST /api/projects/{id}/objects/{oid}/replacement`
- `PATCH /api/projects/{id}/objects/{oid}/replacement-settings`

---

## Screen E — Preview & Render

**File:** `frontend/src/components/ScreenE.tsx`
**Chức năng:** Xem trước và render video cuối cùng

### Người dùng thấy:
- Video player hiển thị kết quả preview/render
- Nút "Preview" (nhanh, chất lượng thấp)
- Nút "Render" (chậm, chất lượng cuối cùng)
- Thanh tiến trình render

### Người dùng thao tác:
1. Nhấn "Preview" → `POST /api/.../preview` (returns job)
2. Poll job status qua `GET /api/jobs/{id}`
3. Khi hoàn tất, video hiển thị trong player
4. Nhấn "Render" → `POST /api/.../render` cho video chất lượng cuối
5. Tải video kết quả

### API liên quan:
- `POST /api/projects/{id}/preview`
- `POST /api/projects/{id}/render`
- `GET /api/jobs/{id}`
- `POST /api/jobs/{id}/cancel`

---

## Luồng điều hướng

```
Screen A → Screen B → Screen C → Screen D → Screen E
(upload)   (select)   (review)   (replace)   (render)
```

Điều hướng được quản lý bởi Zustand store (`frontend/src/stores/project.ts`). Không có routing URL — tất cả nằm trong single page với state-based screen switching.
