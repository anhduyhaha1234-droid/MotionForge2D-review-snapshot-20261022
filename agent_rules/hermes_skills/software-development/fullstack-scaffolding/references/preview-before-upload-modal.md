# Preview-Before-Upload / Confirm-Before-Mutate Modal Pattern

Frontend interaction pattern for any "upload a file to replace an entity" flow
(character replacement, avatar swap, cover image, etc.). User selects a file →
sees a side-by-side comparison → only on explicit confirm does the upload/mutate
fire. Solves two recurring complaints: "the upload happened before I was sure"
and "I couldn't tell which object I picked".

Full working example: MotionForge2D `ScreenD.tsx` (thay thế nhân vật).

## Flow

1. **Select** — input change stores the File in state + builds a preview URL via
   `URL.createObjectURL(file)`. NO upload yet. Reset `e.target.value = ""` so
   re-selecting the same file re-triggers `onChange`.
2. **Compare** — modal shows two `aspect-square` frames side by side:
   - Left: the ORIGINAL entity (server-served crop URL, e.g. `getObjectCropUrl`).
   - Right: the pending file preview (`<img src={previewUrl}>`) + filename.
3. **Act** — "Hủy" revokes the object URL and clears state; "Xác Nhận" calls the
   upload mutation, shows loading on the button, and `onSuccess` closes the modal
   + clears state.

## Code skeleton

```tsx
const uploadMut = useMutation({
  mutationFn: async (file: File) => {
    const result = await api.uploadReplacement(projectId, objectId, file);
    setReplacement({ mode: "static_asset", asset_path: result.asset_path });
    return result;
  },
  onSuccess: () => { setPendingFile(null); setPendingPreview(null); },
});

const [pendingFile, setPendingFile] = useState<File | null>(null);
const [pendingPreview, setPendingPreview] = useState<string | null>(null);

const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0];
  if (!file) return;
  setPendingFile(file);
  setPendingPreview(URL.createObjectURL(file));
  e.target.value = ""; // allow re-selecting the same file
};

const handleCancelPreview = () => {
  if (pendingPreview) URL.revokeObjectURL(pendingPreview);
  setPendingFile(null);
  setPendingPreview(null);
};
```

Modal key points:
- Overlay: `fixed inset-0 z-50 bg-black/70 backdrop-blur-sm`; inner card
  `bg-gray-900 border-gray-700 rounded-2xl max-w-3xl`, `onClick={e => e.stopPropagation()}`
  so clicking inside doesn't cancel.
- Both images `w-full h-full object-contain` inside `aspect-square` boxes —
  preserves original aspect ratio, never distorts.
- Confirm button: `disabled={uploadMut.isPending}` + label swap
  `{uploadMut.isPending ? "Đang tải lên..." : "✅ Xác Nhận Thay Thế"}`.
- Add `data-testid="confirm-replace"` for E2E.

## File input accept

Never restrict to one format unless the backend truly requires it. Common set:
```tsx
accept="image/*,.png,.jpg,.jpeg,.webp"
```
Update the button label to advertise the formats
(`📁 Tải Ảnh Nhân Vật Mới (PNG/JPG/WebP)`).

## Pitfalls

- **Object URL leak:** always `URL.revokeObjectURL(previewUrl)` on cancel — each
  `createObjectURL` holds the blob in memory until revoked or page unload.
- **Missing `useState` import:** adding a modal/state to a component that only
  imported `useCallback/useEffect` fails `tsc` with TS2304-style "Cannot find
  name 'useState'". Check the React import line after adding state.
- **Mutation already wired to old handler:** if the component previously uploaded
  immediately in `handleFileChange`, keep the mutation but move the trigger into
  the confirm handler — otherwise both fire and you upload twice.
- **Stale backend 405 after UI wiring:** the modal is frontend-only, but if the
  upload endpoint was recently added, verify the RUNNING backend has the route
  (restart uvicorn + curl the endpoint) — see `fastapi-backend-patterns` pitfall 9.
