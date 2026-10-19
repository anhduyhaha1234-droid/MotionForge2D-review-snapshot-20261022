# 📋 Implementation Plan — Scene Chunking, Character Replacement & User Approval Workflow

Dựa trên chỉ đạo của BA và Stakeholder, kế hoạch phát triển của **MotionForge 2D** được tinh chỉnh nhằm tập trung vào bài toán **chia nhỏ từng đoạn (Scene Chunking)**, **thay nhân vật từng phân cảnh**, **đảm bảo đồng bộ 100% voice & hình ảnh gốc** và **cung cấp UI duyệt từng bước (User Approval Flow)** trước khi ghép video cuối cùng.

---

## 🛠️ User Review Required

> [!IMPORTANT]
> **Điểm mấu chốt của Workflow mới**:
> 1. **Không ghép video tự động 100%**: Người dùng có toàn quyền xem trước, chỉnh sửa và bấm **"Duyệt" (Approve)** từng phân cảnh (Scene/Chunk). Chỉ khi người dùng đồng ý ghép tất cả các đoạn, hệ thống mới tiến hành Render & Stitch video hoàn chỉnh.
> 2. **Đồng bộ Voice & Hình ảnh**: Mỗi phân cảnh cắt ra giữ nguyên 100% timestamp và audio track tương ứng của video gốc đối thủ, đảm bảo nhịp điệu và lời thoại không bị lệch 1 milisecond nào.

---

## 🎯 Giai đoạn triển khai (Phân chia Task cho Hermes Dev Team)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: Hotfix M1A.1 Blocker (2-4h)                                            │
│ - Fix bug pass `mask_data` từ FE ➔ BE để 100% Green E2E Playwright test.       │
└────────────────────────┬────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: Scene Chunking Engine & Multi-Scene Data Schema                        │
│ - PySceneDetect tự động chia video thành N phân cảnh (Scenes).                  │
│ - Cắt riêng Audio + Frames tương ứng cho từng Scene.                            │
└────────────────────────┬────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: Interactive UI — User Approval & Per-Scene Re-Skinning                 │
│ - UI Bước 1: Danh sách & Timeline các Scene (Scene Grid / Selector).           │
│ - UI Bước 2: Tách & Thay thế nhân vật cho Cảnh đang chọn.                      │
│ - UI Bước 3: Xem trước phân cảnh (Preview Scene with Synced Voice).             │
│ - UI Bước 4: Nút "Duyệt Cảnh" (Approve Scene) ➔ Chuyển cảnh tiếp theo.         │
└────────────────────────┬────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: Final Stitching & Audio Alignment (Duyệt ghép Video cuối)              │
│ - Màn hình Tổng hợp: Hiển thị trạng thái (ví dụ: 12/15 Cảnh đã duyệt).          │
│ - Nút bấm: "Ghép Video Hoàn Chỉnh" (Stitch Approved Scenes via FFmpeg).         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📐 Chi tiết thay đổi Code (Proposed Changes)

---

### Component 1: Fix Hotfix M1A.1 (Lỗi Playwright Happy-Path 400)

#### [MODIFY] [projects.py](file:///c:/Users/Admin/MotionForge2D/app/api/routes/projects.py)
- Trong `create_object`, hỗ trợ nhận `mask_data` hoặc lưu `initial_mask.png` dựa trên `frame_index` chuẩn.
- Loại bỏ phụ thuộc vào fallback ngẫu nhiên trong thư mục `debug/`.

#### [MODIFY] [ScreenB.tsx](file:///c:/Users/Admin/MotionForge2D/frontend/src/components/ScreenB.tsx)
- Truyền `mask_data` nhận được từ `preview-mask` API vào payload khi gọi `createObject`.

---

### Component 2: Backend — Scene Chunking & Audio Slicing Service

#### [NEW] [scene_service.py](file:///c:/Users/Admin/MotionForge2D/app/services/scene_service.py)
- Module cắt nhỏ Video thành các Cảnh (Chunks):
  - Dùng `PySceneDetect` lấy timestamps `[start_time, end_time]` cho từng scene.
  - Dùng FFmpeg bóc tách file audio tương ứng từng scene: `scene_001.aac`, `scene_002.aac`...
  - Lưu thông tin `scene_status`: `PENDING`, `DRAFT`, `APPROVED`.

#### [MODIFY] [projects.py](file:///c:/Users/Admin/MotionForge2D/app/api/routes/projects.py)
- Thêm endpoints:
  - `GET /api/projects/{id}/scenes` -> Danh sách tất cả phân cảnh kèm trạng thái (`APPROVED`/`PENDING`).
  - `POST /api/projects/{id}/scenes/{scene_id}/approve` -> Đánh dấu người dùng đã duyệt phân cảnh này.
  - `POST /api/projects/{id}/stitch` -> Ghép tất cả phân cảnh đã `APPROVED` thành Video MP4 hoàn chỉnh.

---

### Component 3: Frontend — User Approval UI & Multi-Scene Workflow

#### [NEW] [SceneSelector.tsx](file:///c:/Users/Admin/MotionForge2D/frontend/src/components/SceneSelector.tsx)
- Thanh danh sách các Cảnh (Scene Grid / Carousel thumbnail):
  - Hiển thị Cảnh 1, Cảnh 2, Cảnh 3... với badge màu sắc: 🟢 **Đã duyệt (Approved)** | 🟡 **Đang chỉnh sửa** | ⚪ **Chưa làm**.
  - Cho phép người dùng chuyển nhanh giữa các cảnh để thao tác.

#### [MODIFY] [ScreenD.tsx](file:///c:/Users/Admin/MotionForge2D/frontend/src/components/ScreenD.tsx)
- Thêm Player Preview riêng cho phân cảnh hiện tại cùng giọng nói (Voice Synced Preview).
- Bổ sung nút bấm rõ ràng:
  - 🔘 **"Xem thử phân cảnh này" (Preview Scene)**
  - ✅ **"Duyệt phân cảnh này" (Approve & Next Scene)** -> Lưu kết quả và tự động chuyển sang Cảnh tiếp theo.

#### [NEW] [StitchReviewModal.tsx](file:///c:/Users/Admin/MotionForge2D/frontend/src/components/StitchReviewModal.tsx)
- Màn hình duyệt tổng thể trước khi ghép video cuối:
  - Hiển thị danh sách 100% các phân cảnh.
  - Cảnh báo nếu còn phân cảnh chưa duyệt.
  - Nút **"Đồng ý ghép Video hoàn chỉnh"**.

---

## 🧪 Verification Plan (Kế hoạch kiểm thử)

### Automated Tests
- `pytest tests/test_scene_chunking.py`: Test tự động cắt video và tách file audio theo đúng milisecond gốc.
- `pytest tests/test_stitch_service.py`: Test ghép 5 phân cảnh đã duyệt lại thành 1 file MP4 không bị mất khớp tiếng/hình.
- `npx playwright test happy-path`: Đảm bảo toàn bộ UI workflow chạy xanh 100%.

### Manual Verification
1. Upload 1 video hoạt hình 1 phút.
2. Kiểm tra danh sách phân cảnh bóc tách ra (ví dụ: 6 Cảnh).
3. Thực hiện thay nhân vật trên Cảnh 1 ➔ Nhấn **"Xem thử"** (Kiểm tra khớp tiếng/hình) ➔ Nhấn **"Duyệt phân cảnh"**.
4. Lặp lại với các Cảnh tiếp theo.
5. Kiểm tra Màn hình Tổng hợp ➔ Bấm **"Đồng ý ghép"** ➔ Tải video cuối và kiểm tra chất lượng.
