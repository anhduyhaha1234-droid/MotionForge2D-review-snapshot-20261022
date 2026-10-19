# Preview-Before-Upload Modal (ScreenD character replacement flow)

Pattern from MotionForge2D ScreenD: a file-upload flow that must NOT upload
immediately on file selection. The user wants to see the new asset side-by-side
with the original before committing. Also covers the apply-with-progress flow.

## Why

- Immediate upload on `<input type="file">` change gives the user no chance to
  cancel or compare — every pick is destructive.
- The BA/PM spec explicitly moved from "Upload ngay khi chọn file" to
  "Xem trước → Đối chiếu → Xác nhận thay thế".

## State (React)

```tsx
const [pendingFile, setPendingFile] = useState<File | null>(null);
const [pendingPreview, setPendingPreview] = useState<string | null>(null);
const [confirmedReplacement, setConfirmedReplacement] = useState<{
  originalName: string;
  newFileName: string;
  previewUrl: string;
} | null>(null);

const [isApplying, setIsApplying] = useState(false);
const [applyProgress, setApplyProgress] = useState(0);
const [applyMessage, setApplyMessage] = useState("");
```

## File-change handler — NO upload

```tsx
const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0];
  if (!file) return;
  setPendingFile(file);
  setPendingPreview(URL.createObjectURL(file));
  e.target.value = ""; // reset so re-selecting the same file re-fires
};

const handleCancelPreview = () => {
  if (pendingPreview) URL.revokeObjectURL(pendingPreview);
  setPendingFile(null);
  setPendingPreview(null);
};

const handleConfirmReplace = () => {
  if (pendingFile) uploadMut.mutate(pendingFile);
};
```

The upload mutation is only triggered by the confirm button:

```tsx
const uploadMut = useMutation({
  mutationFn: async (file: File) => {
    const result = await api.uploadReplacement(projectId, objectId, file);
    setReplacement({ mode: "static_asset", asset_path: result.asset_path });
    return result;
  },
  onSuccess: () => {
    setConfirmedReplacement({
      originalName: activeObject?.name ?? "Nhân vật gốc",
      newFileName: pendingFile?.name ?? "",
      previewUrl: pendingPreview ?? "",
    });
    setPendingFile(null);  // modal closes on success
  },
});
```

## Modal markup essentials

- Overlay: `fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4`
  with `onClick={handleCancelPreview}` — but inner card calls `e.stopPropagation()`.
- Two columns: `grid grid-cols-2 gap-4`.
  - Left (original): `api.getObjectCropUrl(projectId, objectId)` with
    `<img className="w-full h-full object-contain">` — object-contain keeps
    aspect ratio, never distorts.
  - Right (new): `<img src={pendingPreview} className="w-full h-full object-contain">`
    + file name `<p>{pendingFile?.name}</p>`.
- Frame boxes: `aspect-square bg-gray-800 rounded-xl overflow-hidden ... border` so
  both columns render identical balanced frames regardless of source dimensions.
- Actions: Hủy (gray) + Xác Nhận Thay Thế (purple), disabled while `uploadMut.isPending`,
  button text swaps to "Đang tải lên...".
- `onError` on the ORIGINAL image: `(e.target as HTMLImageElement).style.display = "none"`
  so a missing crop degrades to an empty box, not a broken-image icon.

## Apply-with-progress flow

```tsx
const handleApplySettings = async () => {
  setIsApplying(true);
  setApplyProgress(10);
  await settingsMut.mutateAsync();
  setApplyProgress(40);
  try {
    const result = await api.autoMatchCharacter(projectId, objectId);
    setApplyMessage(`Hoàn tất áp dụng cho ${result.count} phân cảnh...`);
  } catch (matchErr) {
    // NON-FATAL — keep going
    setApplyMessage(`Đã lưu cấu hình (auto-match: ${(matchErr as Error).message})...`);
  }
  setApplyProgress(80);
  await new Promise((r) => setTimeout(r, 600));
  setApplyProgress(100);
  await new Promise((r) => setTimeout(r, 500));
  setIsApplying(false);
};
```

Progress overlay:

```tsx
{isApplying && (
  <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center">
    <div className="bg-gray-900 border border-purple-500/40 p-6 rounded-xl w-96 text-center space-y-4 shadow-2xl">
      <h3>🎭 Đang xử lý thay đổi nhân vật...</h3>
      <div className="w-full bg-gray-800 h-3 rounded-full overflow-hidden">
        <div className="bg-gradient-to-r from-purple-500 to-blue-500 h-full transition-all duration-300"
             style={{ width: `${applyProgress}%` }} />
      </div>
      <p>{applyProgress}% hoàn thành</p>
    </div>
  </div>
)}
```

## Confirmation banner

A banner that appears once `replacement.asset_path` is set (or a confirmed
replacement state exists). Show original name ➔ new file name and a hint that
the "Áp dụng" button commits the change across scenes. Guard the `.split("/").pop()`
filename access with optional chaining (`replacement.asset_path?.split("/").pop() ?? "..."`)
or TypeScript errors on possibly-null `asset_path`.

## Backend counterpart

- `POST /objects/{id}/replacement` returns `{"status":"ok","asset_path":...}`.
- `GET /objects/{id}/replacement-image` serves the uploaded file:
  glob `objects/<id>/replacement.*` first, fall back to the stored `asset_path`,
  404 only if neither exists. Both trailing-slash variants.
- `PATCH /objects/{id}/replacement-settings` expects the WRAPPED body
  `{"replacement_config": {...}}` (see fastapi-backend-patterns pitfall 18).

## Test pattern for the served image

```python
ok, enc = cv2.imencode(".png", np.full((64, 64, 3), 200, dtype=np.uint8))
assert ok
png_bytes = enc.tobytes()
up = client.post(f"/api/projects/{pid}/objects/{oid}/replacement",
                 files={"file": ("char.png", png_bytes, "image/png")})
assert up.status_code == 200
img = client.get(f"/api/projects/{pid}/objects/{oid}/replacement-image")
assert img.status_code == 200
assert img.headers["content-type"] == "image/png"
assert img.content[:8] == b"\x89PNG\r\n\x1a\n"
```
