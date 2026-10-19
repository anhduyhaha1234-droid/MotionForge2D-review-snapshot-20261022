---
name: react-konva-canvas-preview
description: "Build interactive Konva.js canvas preview/compositor components in React/Next.js apps. Covers Stage/Layer setup, async image loading, viewport transforms, transform pipelines (anchor/scale/rotation/offset), canvas compositing modes, resize observers, and Playwright E2E testing for canvas-heavy UIs. Use when building visual preview, image compositing, or interactive canvas editors in React."
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: software-development
    tags: [konva, react-konva, canvas, nextjs, zustand, playwright, compositing, preview, typescript, react]
    related_skills: [python-video-processing-pipeline, terminal-engineering-discipline, bom-verified-implementation]
---

# React Konva Canvas Preview

Build interactive canvas-based preview and compositing UIs in React/Next.js using Konva.js. Covers the full pattern from Stage setup through transform math to E2E testing.

## When to Use

- Building visual preview/compositor UIs for video or image processing apps
- Canvas-based editors with real-time parameter feedback
- Overlaying images with transform controls (position, scale, rotation, opacity)
- Viewport coordinate mapping (source coords ↔ canvas coords)
- Testing canvas-heavy UIs with Playwright

## Architecture Pattern

```
┌─────────────────────────────────────────────────────┐
│ Screen Component (layout, controls, state)           │
│  ├── Left Panel: asset thumbnails, upload            │
│  ├── Center: <CanvasComponent> (Konva preview)       │
│  └── Right Panel: sliders, buttons, mode selectors   │
└─────────────────────────────────────────────────────┘
         │ Zustand store (shared state)
         ▼
┌─────────────────────────────────────────────────────┐
│ Canvas Component (Konva Stage + Layers)              │
│  ├── ResizeObserver → auto-resize Stage              │
│  ├── Async image loading (crossOrigin="anonymous")   │
│  ├── Viewport transform (source → canvas coords)     │
│  ├── Transform pipeline (centroid, anchor, scale...) │
│  └── Layer composition (bg → frame → mask → overlay) │
└─────────────────────────────────────────────────────┘
```

## Step-by-Step Implementation

### 1. Konva Stage Setup with Resize Observer

**Critical: Konva runs in the browser, not SSR.** All Konva code must be in a `"use client"` component. Never import Konva at module level in SSR contexts.

```tsx
"use client";
import { useEffect, useRef, useCallback } from "react";
import Konva from "konva";

export function CanvasPreview() {
  const containerRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<Konva.Stage | null>(null);
  const layerRef = useRef<Konva.Layer | null>(null);

  const getContainerSize = useCallback(() => {
    const el = containerRef.current;
    if (!el) return { w: 640, h: 480 };
    const rect = el.getBoundingClientRect();
    return { w: Math.floor(rect.width), h: Math.floor(rect.height) };
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const { w, h } = getContainerSize();
    const stage = new Konva.Stage({ container: el, width: w, height: h });
    const layer = new Konva.Layer();
    stage.add(layer);
    stageRef.current = stage;
    layerRef.current = layer;

    const ro = new ResizeObserver(() => {
      const { w: nw, h: nh } = getContainerSize();
      stage.width(nw);
      stage.height(nh);
    });
    ro.observe(el);

    return () => {
      ro.disconnect();
      stage.destroy();
      stageRef.current = null;
      layerRef.current = null;
    };
  }, [getContainerSize]);

  return <div ref={containerRef} className="w-full h-full" />;
}
```

**Pitfall:** Always `stage.destroy()` in cleanup. Leaked stages cause memory leaks and duplicate event listeners.

**Pitfall:** `getContainerSize()` returns `{w, h}` with `Math.floor()` — fractional pixel sizes cause canvas blur.

### 2. Async Image Loading

Load images outside Konva, then create Konva.Image nodes when ready:

```tsx
const [frameImg, setFrameImg] = useState<HTMLImageElement | null>(null);

useEffect(() => {
  if (!frameUrl) { setFrameImg(null); return; }
  const img = new window.Image();
  img.crossOrigin = "anonymous";  // Required for canvas export
  img.onload = () => setFrameImg(img);
  img.onerror = () => setFrameImg(null);
  img.src = frameUrl;
}, [frameUrl]);
```

**Pitfall:** Use `new window.Image()`, not `new Image()` — in some TypeScript configs `Image` resolves to a type, not the constructor.

**Pitfall:** Always set `crossOrigin = "anonymous"` BEFORE setting `src`. Setting it after has no effect. Without it, `stage.toDataURL()` throws a tainted canvas error.

**Pitfall:** Handle `onerror` — a missing image URL shouldn't crash the component.

### 3. Viewport Transform (Source ↔ Canvas)

Maps between source coordinates (e.g. video frame pixels) and canvas coordinates:

```typescript
interface ViewportTransform {
  scale: number;
  offsetX: number;
  offsetY: number;
}

function createViewportTransform(
  sourceW: number, sourceH: number,
  canvasW: number, canvasH: number,
): ViewportTransform {
  const scale = Math.min(canvasW / sourceW, canvasH / sourceH);
  const offsetX = (canvasW - sourceW * scale) / 2;
  const offsetY = (canvasH - sourceH * scale) / 2;
  return { scale, offsetX, offsetY };
}

function sourceToCanvas(sx: number, sy: number, vt: ViewportTransform) {
  return { x: sx * vt.scale + vt.offsetX, y: sy * vt.scale + vt.offsetY };
}

function canvasToSource(cx: number, cy: number, vt: ViewportTransform) {
  return { x: (cx - vt.offsetX) / vt.scale, y: (cy - vt.offsetY) / vt.scale };
}
```

This handles letterbox/pillarbox automatically. The `offsetX`/`offsetY` represent the black bars.

**Roundtrip guarantee:** `canvasToSource(sourceToCanvas(x))` must produce ≤1px error. Verified by coordinate validation tests.

### 4. Transform Pipeline (Replacement Compositing)

When compositing a replacement image onto a tracked object, apply transforms in this exact order:

```
1. Get tracked centroid (cx, cy) from motion data
2. Get replacement natural size (rw, rh)
3. Compute target size based on fit_mode and tracked bbox
4. Apply scale multiplier
5. Compute anchor pixel offset
6. Position: centroid - anchor + offset
7. Apply rotation around center
8. Apply opacity
```

```typescript
function computeTransform(motion, replacement, assetW, assetH, frameW, frameH) {
  const { centroid_x: cx, centroid_y: cy, bbox, scale_x, scale_y, rotation_deg } = motion;
  const { anchor, offset, scale, rotation_offset_deg, opacity, fit_mode } = replacement;

  // Target size from fit mode
  const bboxW = bbox.width * scale_x;
  const bboxH = bbox.height * scale_y;
  let targetW: number, targetH: number;

  if (fit_mode === "contain") {
    const ratio = Math.min(bboxW / assetW, bboxH / assetH);
    targetW = assetW * ratio; targetH = assetH * ratio;
  } else if (fit_mode === "cover") {
    const ratio = Math.max(bboxW / assetW, bboxH / assetH);
    targetW = assetW * ratio; targetH = assetH * ratio;
  } else { // stretch
    targetW = bboxW; targetH = bboxH;
  }

  const finalW = targetW * scale;
  const finalH = targetH * scale;
  const anchorPxX = finalW * anchor.x;
  const anchorPxY = finalH * anchor.y;
  const posX = cx - anchorPxX + offset.x * frameW;
  const posY = cy - anchorPxY + offset.y * frameH;
  const totalRot = rotation_deg + rotation_offset_deg;

  return { x: posX, y: posY, width: finalW, height: finalH, rotation: totalRot, opacity };
}
```

**Konva rotation:** Set the node's `x, y` to the CENTER of the image, then use `offsetX: width/2, offsetY: height/2` to rotate around center. Konva rotates around `(x - offsetX, y - offsetY)`.

```tsx
const centerX = scaledX + scaledW / 2;
const centerY = scaledY + scaledH / 2;
const node = new Konva.Image({
  x: centerX, y: centerY,
  width: scaledW, height: scaledH,
  offsetX: scaledW / 2, offsetY: scaledH / 2,
  rotation: transform.rotation,
  image: replacementImg,
  opacity: transform.opacity,
});
```

### 4b. Fallback Placement When Motion Data Is Missing

Objects created from a raw bbox/point selection may have **no motion/tracking data** (`frameMotion === null`). The classic guard `if (activeRepImg && frameMotion)` then draws NOTHING — user sees only the background frame and reports "the new character doesn't appear on canvas". Fix: always draw the replacement; when motion is missing, fall back to a sensible placement:

```tsx
let fallbackW = 0, fallbackH = 0;
let cx = videoWidth / 2, cy = videoHeight / 2;
let tf: TransformResult;
if (effMotion) {
  tf = computeReplacementTransform(effMotion, replacement, imgW, imgH, videoWidth, videoHeight);
} else {
  // No motion: center of frame, 30% of frame height, keep natural aspect
  fallbackH = videoHeight * 0.3;
  fallbackW = (imgW / imgH) * fallbackH;
  tf = {
    x: cx - fallbackW * replacement.anchor.x + replacement.offset.x * videoWidth,
    y: cy - fallbackH * replacement.anchor.y + replacement.offset.y * videoHeight,
    width: fallbackW * replacement.scale,
    height: fallbackH * replacement.scale,
    rotation: replacement.rotation_offset_deg,
    opacity: replacement.opacity,
  };
}
```

Every overlay marker (bbox rect, centroid dot, anchor star) must ALSO use the fallback coords when motion is null — `effMotion ? effMotion.centroid_x : cx`, etc. Do not leave `frameMotion.centroid_x` references behind; they'll both throw TS null errors and draw at the wrong place.

### 4c. TS Null-Narrowing Does NOT Propagate Through an Alias Variable

```tsx
const effMotion = frameMotion ? frameMotion : null;
if (activeRepImg && (effMotion || true)) { ... }
```

TypeScript narrows `effMotion` inside the branch but **does not narrow the original `frameMotion`** — every later `frameMotion.centroid_x` still errors `TS18047 'frameMotion' is possibly 'null'`. You must replace ALL uses inside the branch with the narrowed alias (`effMotion.centroid_x`) or a ternary (`effMotion ? effMotion.centroid_x : fallback`). `frameMotion!` non-null assertions pile up and lie when the fallback path runs — use the alias.

### 4d. Close Confirm Modals IMMEDIATELY — Don't Await the Async in onSuccess

When a confirm button (e.g. "Xác Nhận Thay Thế") kicks off an upload/apply, close the modal **synchronously in the click handler** and let the mutation run in the background:

```tsx
const handleConfirm = () => {
  if (!pendingFile) return;
  setPendingPreview(null);        // close modal NOW — no hang
  setPreviewMode("result");       // switch canvas so result becomes visible
  uploadMut.mutate(pendingFile);  // async in background; onSuccess updates state
};
```

Closing only in `onSuccess` means the modal hangs while the request is slow/failing — users report "button does nothing" / "modal stuck". Keep the pending file in state (cleared in `onSuccess`) so the confirmation banner still shows the file name after the upload lands.

Render layers bottom-to-top:

```
1. Checkerboard background (transparency indicator)
2. Original frame image
3. Mask overlay (semi-transparent, opacity ~0.35)
4. Replacement image (with full transform pipeline)
5. Bounding box rectangle (dashed stroke)
6. Centroid dot (filled circle)
7. Anchor point marker (star shape)
8. Replacement outline (dashed, shows placement area)
```

**Checkerboard pattern:** Use a grid of small Konva.Rect nodes:

```tsx
const CHECK = 12;
const cols = Math.ceil(width / CHECK);
const rows = Math.ceil(height / CHECK);
for (let r = 0; r < rows; r++) {
  for (let c = 0; c < cols; c++) {
    layer.add(new Konva.Rect({
      x: c * CHECK, y: r * CHECK,
      width: CHECK, height: CHECK,
      fill: (r + c) % 2 === 0 ? "#1a1a2e" : "#16162a",
    }));
  }
}
```

### 6. Clip Modes

Three modes for how replacement alpha interacts with the original mask:

| Mode | Frontend (Canvas 2D) | Backend (NumPy) |
|------|---------------------|-----------------|
| `asset_alpha` | Draw normally (`source-over`) | `alpha = rep_alpha * opacity` |
| `original_mask` | `destination-in` composite | `alpha = mask * opacity` |
| `intersection` | `source-in` composite | `alpha = min(rep_alpha, mask) * opacity` |

### 7. Zustand Store Pattern for Preview State

Extend existing store with preview-specific fields:

```typescript
type PreviewMode = "original" | "mask" | "result" | "comparison";

interface ProjectState {
  // ... existing fields ...
  previewMode: PreviewMode;
  frameMotion: FrameMotion | null;
  setPreviewMode: (mode: PreviewMode) => void;
  setFrameMotion: (motion: FrameMotion | null) => void;
}
```

**Derive frame motion from object data** — don't store it redundantly:

```tsx
useEffect(() => {
  if (!activeObject?.motion?.frames) { setFrameMotion(null); return; }
  const fm = activeObject.motion.frames.find(f => f.frame_index === currentFrame) ?? null;
  setFrameMotion(fm);
}, [activeObject, currentFrame, setFrameMotion]);
```

### 8. API Client URL Helpers

Add pure URL-returning helpers (no fetch) for direct image linking:

```typescript
// In api.ts
getMaskImageUrl: (projectId: string, objectId: string, frameIndex: number) =>
  `${API_BASE}/api/projects/${projectId}/objects/${objectId}/masks/${frameIndex}`,

getCropImageUrl: (projectId: string, objectId: string, frameIndex: number) =>
  `${API_BASE}/api/projects/${projectId}/objects/${objectId}/crops/${frameIndex}`,
```

These return URLs for use in `<img src>` and Konva `image.src` — not fetch calls.

## Playwright E2E Testing for Canvas UIs

### Playwright Config for Next.js

```typescript
// playwright.config.ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  timeout: 120_000,
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  // Do NOT auto-start web server — tests expect dev server + backend running
});
```

### Test Fixture Generation

Create fixture videos with FFmpeg in `beforeAll`:

```typescript
import { execSync } from "child_process";

test.beforeAll(() => {
  const fs = require("fs");
  if (!fs.existsSync(FIXTURE_DIR)) fs.mkdirSync(FIXTURE_DIR, { recursive: true });
  if (!fs.existsSync(VIDEO_PATH)) {
    execSync(
      `ffmpeg -y -f lavfi -i "color=c=blue:s=320x240:d=2" -c:v libx264 -pix_fmt yuv420p "${VIDEO_PATH}"`,
      { stdio: "ignore" },
    );
  }
});
```

### Coordinate Validation Tests

Test canvas→source→canvas roundtrip as pure logic tests (no server needed):

```typescript
test("roundtrip ≤1px error at common viewports", () => {
  const viewports = [
    { w: 1920, h: 1080 }, // exact match
    { w: 800, h: 600 },   // 4:3 letterbox
    { w: 1080, h: 1920 }, // portrait pillarbox
  ];
  for (const vp of viewports) {
    for (const pt of testPoints) {
      const vt = createViewportTransform(sourceW, sourceH, vp.w, vp.h);
      const canvas = sourceToCanvas(pt.x, pt.y, vt);
      const back = canvasToSource(canvas.x, canvas.y, vt);
      expect(Math.abs(back.x - pt.x)).toBeLessThanOrEqual(1.0);
      expect(Math.abs(back.y - pt.y)).toBeLessThanOrEqual(1.0);
    }
  }
});
```

These tests run instantly (no browser needed) and validate the core math.

### E2E Workflow Tests

Mark slow GPU tests with `@slow` tag. Structure tests as step-by-step workflows:

```typescript
test("full workflow: create → select → replace → render", async ({ page }) => {
  await page.goto("/");
  // ... fill name, upload video, wait for ingest ...
  // ... click canvas, preview mask, accept ...
  // ... upload replacement, adjust sliders ...
  // Verify canvas updates: expect(page.locator('[data-testid="composite-canvas"]')).toBeVisible();
});
```

Use `data-testid` attributes on interactive elements for reliable selection.

## Pitfalls

1. **Konva in SSR:** Konva accesses `window`/`document`. Always use `"use client"` and dynamic import if needed. Next.js will crash with "window is not defined" if Konva is imported in a server component.

2. **Stage resize vs re-render:** When React state changes trigger a re-render, the Konva stage DOM element persists. Don't recreate the stage on every render — update layer children instead. Only recreate on mount/unmount.

3. **Image loading race conditions:** If `frameUrl` changes while an image is loading, the old `onload` callback still fires. Use a cleanup flag or check if the URL is still current:

```tsx
useEffect(() => {
  let cancelled = false;
  const img = new window.Image();
  img.onload = () => { if (!cancelled) setFrameImg(img); };
  img.src = frameUrl;
  return () => { cancelled = true; };
}, [frameUrl]);
```

4. **Konva.Text for labels:** Use `fontFamily: "sans-serif"` — Konva doesn't inherit CSS fonts. Labels need explicit font settings.

5. **Layer batchDraw:** After adding all nodes, call `layer.batchDraw()` once. Don't call `layer.draw()` in a loop — it's synchronous and slow.

6. **Comparison mode (side-by-side 50/50):** Split the stage in half: left = original frame (no overlay), right = composite at `drawComposite(halfW)` offset, with a dashed divider line. Give each half a label bar — a semi-transparent `Konva.Rect` behind a `Konva.Text` so titles stay readable over bright frames (e.g. `📷 Ảnh Gốc` left, `🎨 Kết Quả Thay Thế` right). The label bars must be added AFTER the composite draw so they sit on top. Don't crop the right half — draw the full composite shifted by `halfW` so the replacement + bbox + overlays all render at their real positions.

7. **Slider input type="range" with fill():** Playwright's `fill()` works on range inputs but may not trigger React's `onChange`. Use `page.locator('input[type="range"]').evaluate(el => { el.value = '1.5'; el.dispatchEvent(new Event('input', { bubbles: true })) })` for reliable slider interaction.

8. **Checkerboard performance:** For large canvases, the checkerboard grid creates many Konva.Rect nodes. If performance is an issue, use a single Konva.Image with a pre-rendered checkerboard pattern instead.

9. **No `any` types:** Use `as HTMLImageElement` for event targets, explicit type parameters for `Konva.Image`, `Konva.Rect`, etc. Konva's type definitions are thorough — lean on them.

10. **dark theme convention:** Use Tailwind `bg-gray-950` for canvas background, `bg-gray-900` for panels, `bg-gray-800` for controls. Matches standard dark theme in creative tools.

11. **Multi-mode image source selection:** When a canvas component supports multiple replacement modes (e.g., static PNG vs frame sequence), load all possible image sources independently, then select the active one in the render effect:
    ```tsx
    const [repImg, setRepImg] = useState<HTMLImageElement | null>(null);
    const [sequenceImg, setSequenceImg] = useState<HTMLImageElement | null>(null);
    // Each loaded via its own useEffect with its own URL dependency

    // In the render effect:
    const activeRepImg = mode === "frame_sequence" ? sequenceImg : repImg;
    ```
    Add ALL image states to the render effect's dependency array. Don't conditionally load — load all and select, so switching modes is instant (images are already cached).

12. **Multi-object rendering:** When extending a single-object canvas to render N objects simultaneously, use a `Map<string, HTMLImageElement>` keyed by objectId. Load all replacement images in a single effect that iterates the objects array, then in the render effect iterate the map to draw each object's replacement + bbox + centroid + label. Add the map state AND the allObjects array to the render effect's dependency array. Per-object labels use `Konva.Text` positioned above the bbox.
    ```tsx
    // State
    const [multiObjImgs, setMultiObjImgs] = useState<Map<string, HTMLImageElement>>(new Map());

    // Loading effect — load all, update map once all are ready
    useEffect(() => {
      if (!allObjects?.length) { setMultiObjImgs(new Map()); return; }
      const newMap = new Map<string, HTMLImageElement>();
      let loaded = 0;
      const total = allObjects.filter(o => o.replacementUrl).length;
      if (total === 0) { setMultiObjImgs(new Map()); return; }
      for (const obj of allObjects) {
        if (!obj.replacementUrl) continue;
        const img = new window.Image();
        img.crossOrigin = "anonymous";
        img.onload = () => { newMap.set(obj.objectId, img); if (++loaded === total) setMultiObjImgs(new Map(newMap)); };
        img.onerror = () => { if (++loaded === total) setMultiObjImgs(new Map(newMap)); };
        img.src = obj.replacementUrl;
      }
    }, [allObjects]);

    // In render effect — iterate and draw each object
    for (const obj of allObjects) {
      const objImg = multiObjImgs.get(obj.objectId);
      if (!objImg || !obj.motion || !obj.replacement) continue;
      const tf = computeReplacementTransform(obj.motion, obj.replacement, ...);
      // ... create Konva.Image, Konva.Rect (bbox), Konva.Circle (centroid), Konva.Text (label)
    }
    ```
    13. **Gate the "next step" button on the prerequisite state.** A "Tiếp: Render Video →" button that always fires `setScreen("render")` lets users advance without having applied a replacement. Disable + grey it until the prerequisite exists: `disabled={!replacement.asset_path && !confirmedReplacement}` with conditional classes (`bg-gray-700 text-gray-400 cursor-not-allowed` vs `bg-blue-600 hover:bg-blue-500`). Users then see exactly when the step is ready — no clicking a dead button.

    14. **`(effMotion || true)` and similar always-true conditions are code smells — be explicit.** `if (activeRepImg && (effMotion || true))` compiles and "works" but hides intent. When the fallback path is intentional, write the branches explicitly (see §4b) and keep the guard `if (activeRepImg)`. This also avoids TS narrowing confusion (see §4c).
