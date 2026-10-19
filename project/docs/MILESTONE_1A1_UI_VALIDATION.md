# Milestone 1A.1 — UI Validation

**MotionForge 2D**
**Date:** 2026-07-30

---

## Screen Overview

MotionForge 2D follows a 5-screen workflow (Screen A → Screen E) with a shared CompositeCanvas component for live preview.

### Screen A — Project Start (`ScreenA.tsx`)

- **Purpose:** Create or load a project.
- **Key UI:** Project name input, "Tạo dự án mới" (Create new project) button, recent projects list.
- **Labels (Vietnamese):** "Tên dự án" (Project name), "Tạo dự án mới" (Create new project).
- **Screenshot:** `docs/screenshots/milestone_1a/01_project_start.png` ✅ captured.

### Screen B — Video Upload & Ingest (`ScreenB.tsx`)

- **Purpose:** Upload source video, trigger frame extraction.
- **Key UI:** Drag-and-drop upload zone, progress bar, metadata display (resolution, fps, frame count).
- **Labels (Vietnamese):** "Tải video lên" (Upload video), "Đang xử lý…" (Processing…), "Kết quả" (Result).

### Screen C — Object Selection & Masking (`ScreenC.tsx`)

- **Purpose:** Select target object on a frame, run SAM2 mask preview, propagate mask across frames.
- **Key UI:** Frame selector, mask overlay preview, "Tạo đối tượng" (Create object) button, propagation progress.
- **Labels (Vietnamese):** "Chọn đối tượng" (Select object), "Xem trước mask" (Preview mask), "Đang lan truyền…" (Propagating…).

### Screen D — Replacement & Settings (`ScreenD.tsx`)

- **Purpose:** Upload replacement asset, configure transform settings, preview composite result.
- **Key UI:** Replacement upload, settings panel (position, scale, rotation, clip mode), live composite preview via `CompositeCanvas`.
- **Labels (Vietnamese):** "Tải ảnh thay thế" (Upload replacement), "Cài đặt" (Settings), "Chế độ cắt" (Clip mode), "Xem trước" (Preview).
- **Rewritten in M1A.1:** now uses real Konva preview (no placeholder).

### Screen E — Render & Export (`ScreenE.tsx`)

- **Purpose:** Trigger preview render and final export.
- **Key UI:** Preview render button, final render button, download link, render progress.
- **Labels (Vietnamese):** "Xem trước kết quả" (Preview result), "Xuất video cuối" (Export final video), "Tải xuống" (Download).

---

## CompositeCanvas Component

`CompositeCanvas.tsx` — real-time Konva-based composite canvas.

### Capabilities
- Layers: background frame, mask overlay, replacement asset.
- Supports all 4 preview modes (see below).
- Responds to transform state changes (position, scale, rotation).
- Uses Konva `Stage`, `Layer`, `Image`, and `Group` nodes.

### Preview Modes

| Mode | Vietnamese Label | Description |
|---|---|---|
| Original | **Ảnh gốc** | Background frame without any overlay |
| Mask | **Mask** | SAM2 mask rendered as colored overlay on frame |
| Result | **Kết quả** | Replacement asset composited onto masked region |
| Compare | **So sánh** | Side-by-side: original frame (left) vs. result (right) |

---

## Transform Controls

The settings panel in Screen D exposes the following controls:

| Control | Vietnamese Label | Type | Default |
|---|---|---|---|
| Position X | Vị trí X | Slider / Number input | 0 |
| Position Y | Vị trí Y | Slider / Number input | 0 |
| Scale | Tỷ lệ | Slider (0.1–5.0) | 1.0 |
| Rotation | Xoay | Slider (0–360°) | 0 |
| Clip Mode | Chế độ cắt | Dropdown select | `asset_alpha` |
| Opacity | Độ trong suốt | Slider (0–100%) | 100% |

### Clip Modes

| Value | Vietnamese Label | Description |
|---|---|---|
| `asset_alpha` | Alpha tài sản | Use replacement asset's alpha channel |
| `original_mask` | Mask gốc | Use original SAM2 mask as clip boundary |
| `intersection` | Giao | Intersection of asset alpha and original mask |

---

## Vietnamese Label Summary

All user-facing labels are in Vietnamese. Key strings:

- Tạo dự án mới — Create new project
- Tải video lên — Upload video
- Chọn đối tượng — Select object
- Xem trước mask — Preview mask
- Tải ảnh thay thế — Upload replacement
- Cài đặt — Settings
- Chế độ cắt — Clip mode
- Xem trước — Preview
- Xem trước kết quả — Preview result
- Xuất video cuối — Export final video
- Tải xuống — Download
- Ảnh gốc — Original image
- Kết quả — Result
- So sánh — Compare
