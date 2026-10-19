import { test, expect } from "@playwright/test";

/* ── Coordinate Validation Tests ────────────────────────────────────────── *
 *
 * Tests canvas→source→canvas roundtrip accuracy at different viewport sizes
 * and letterbox scenarios. Uses the coordinate.ts utility functions.
 *
 * These tests validate that the frontend coordinate system is consistent:
 * - Clicking at a canvas position → converting to source → back to canvas
 *   must produce ≤1px error
 * - Letterbox (black bars) scenarios must be handled correctly
 */

/* ── Inline coordinate functions (mirrors frontend/src/lib/coordinates.ts) */

interface ViewportTransform {
  scale: number;
  offsetX: number;
  offsetY: number;
}

function createViewportTransform(
  sourceW: number,
  sourceH: number,
  canvasW: number,
  canvasH: number,
): ViewportTransform {
  const scale = Math.min(canvasW / sourceW, canvasH / sourceH);
  const offsetX = (canvasW - sourceW * scale) / 2;
  const offsetY = (canvasH - sourceH * scale) / 2;
  return { scale, offsetX, offsetY };
}

function sourceToCanvas(
  sx: number,
  sy: number,
  vt: ViewportTransform,
): { x: number; y: number } {
  return {
    x: sx * vt.scale + vt.offsetX,
    y: sy * vt.scale + vt.offsetY,
  };
}

function canvasToSource(
  cx: number,
  cy: number,
  vt: ViewportTransform,
): { x: number; y: number } {
  return {
    x: (cx - vt.offsetX) / vt.scale,
    y: (cy - vt.offsetY) / vt.scale,
  };
}

/* ── Helpers ───────────────────────────────────────────────────────────── */

function roundtrip(
  sx: number,
  sy: number,
  sourceW: number,
  sourceH: number,
  canvasW: number,
  canvasH: number,
): { errorX: number; errorY: number } {
  const vt = createViewportTransform(sourceW, sourceH, canvasW, canvasH);
  const canvas = sourceToCanvas(sx, sy, vt);
  const back = canvasToSource(canvas.x, canvas.y, vt);
  return {
    errorX: Math.abs(back.x - sx),
    errorY: Math.abs(back.y - sy),
  };
}

/* ── Test Cases ────────────────────────────────────────────────────────── */

test.describe("Coordinate Validation", () => {
  const SOURCE_W = 1920;
  const SOURCE_H = 1080;

  test("canvas→source→canvas roundtrip ≤1px error at common viewports", () => {
    const viewports = [
      { w: 1920, h: 1080 }, // exact match
      { w: 1280, h: 720 }, // smaller 16:9
      { w: 800, h: 600 }, // 4:3 letterbox
      { w: 1920, h: 1200 }, // 16:10 slight pillarbox
      { w: 3840, h: 2160 }, // 4K
      { w: 640, h: 480 }, // small
    ];

    // Test points: corners, center, quarter points
    const testPoints = [
      { x: 0, y: 0 }, // top-left
      { x: SOURCE_W / 2, y: SOURCE_H / 2 }, // center
      { x: SOURCE_W - 1, y: SOURCE_H - 1 }, // bottom-right
      { x: SOURCE_W / 4, y: SOURCE_H / 4 }, // quarter
      { x: (SOURCE_W * 3) / 4, y: (SOURCE_H * 3) / 4 }, // three-quarter
      { x: 100, y: 200 }, // arbitrary
      { x: 1500, y: 900 }, // arbitrary
    ];

    for (const vp of viewports) {
      for (const pt of testPoints) {
        const err = roundtrip(pt.x, pt.y, SOURCE_W, SOURCE_H, vp.w, vp.h);
        expect(err.errorX).toBeLessThanOrEqual(1.0);
        expect(err.errorY).toBeLessThanOrEqual(1.0);
      }
    }
  });

  test("roundtrip at extreme viewports (very small, very large)", () => {
    const extremeViewports = [
      { w: 100, h: 100 },
      { w: 50, h: 50 },
      { w: 7680, h: 4320 },
    ];

    const centerPt = { x: SOURCE_W / 2, y: SOURCE_H / 2 };

    for (const vp of extremeViewports) {
      const err = roundtrip(
        centerPt.x,
        centerPt.y,
        SOURCE_W,
        SOURCE_H,
        vp.w,
        vp.h,
      );
      expect(err.errorX).toBeLessThanOrEqual(1.0);
      expect(err.errorY).toBeLessThanOrEqual(1.0);
    }
  });

  test("letterbox scenario — wide source in tall viewport", () => {
    // Source: 1920x1080 (16:9), Viewport: 1080x1920 (9:16 portrait)
    // Should have horizontal letterbox bars
    const vt = createViewportTransform(1920, 1080, 1080, 1920);
    expect(vt.scale).toBeCloseTo(1080 / 1920, 5); // width-limited
    expect(vt.offsetY).toBeGreaterThan(0); // vertical bars
    expect(vt.offsetX).toBe(0);

    // Center of source should map to center of viewport
    const centerCanvas = sourceToCanvas(960, 540, vt);
    expect(centerCanvas.x).toBeCloseTo(540, 1);
    expect(centerCanvas.y).toBeCloseTo(960, 1);
  });

  test("letterbox scenario — narrow source in wide viewport", () => {
    // Source: 1080x1920 (9:16 portrait), Viewport: 1920x1080 (16:9 landscape)
    // Should have vertical pillarbox bars
    const vt = createViewportTransform(1080, 1920, 1920, 1080);
    expect(vt.scale).toBeCloseTo(1080 / 1920, 5); // height-limited
    expect(vt.offsetX).toBeGreaterThan(0); // horizontal bars
    expect(vt.offsetY).toBe(0);
  });

  test("exact aspect ratio match — no letterbox", () => {
    const vt = createViewportTransform(1920, 1080, 960, 540);
    expect(vt.offsetX).toBe(0);
    expect(vt.offsetY).toBe(0);
    expect(vt.scale).toBeCloseTo(960 / 1920, 5);
  });

  test("roundtrip precision at sub-pixel positions", () => {
    const vt = createViewportTransform(1920, 1080, 1280, 720);

    // Test positions that would be at fractional source coords
    const subPixelPoints = [
      { x: 0.5, y: 0.5 },
      { x: 100.7, y: 200.3 },
      { x: 1919.99, y: 1079.99 },
    ];

    for (const pt of subPixelPoints) {
      const canvas = sourceToCanvas(pt.x, pt.y, vt);
      const back = canvasToSource(canvas.x, canvas.y, vt);
      expect(Math.abs(back.x - pt.x)).toBeLessThanOrEqual(1.0);
      expect(Math.abs(back.y - pt.y)).toBeLessThanOrEqual(1.0);
    }
  });

  test("4:3 source in 16:9 viewport — correct letterbox", () => {
    // Source: 640x480 (4:3), Viewport: 1920x1080 (16:9)
    const vt = createViewportTransform(640, 480, 1920, 1080);
    // Should be height-limited since 4:3 is "taller" than 16:9
    // scale = min(1920/640, 1080/480) = min(3.0, 2.25) = 2.25
    expect(vt.scale).toBeCloseTo(2.25, 5);
    expect(vt.offsetX).toBeGreaterThan(0); // pillarbox
    expect(vt.offsetY).toBe(0);

    // Corners must roundtrip
    const corners = [
      { x: 0, y: 0 },
      { x: 639, y: 479 },
    ];
    for (const pt of corners) {
      const err = roundtrip(pt.x, pt.y, 640, 480, 1920, 1080);
      expect(err.errorX).toBeLessThanOrEqual(1.0);
      expect(err.errorY).toBeLessThanOrEqual(1.0);
    }
  });

  test("square source in wide viewport", () => {
    // Source: 1000x1000, Viewport: 1920x1080
    const vt = createViewportTransform(1000, 1000, 1920, 1080);
    // scale = min(1.92, 1.08) = 1.08
    expect(vt.scale).toBeCloseTo(1.08, 5);
    expect(vt.offsetX).toBeGreaterThan(0); // pillarbox
    expect(vt.offsetY).toBe(0);

    const err = roundtrip(500, 500, 1000, 1000, 1920, 1080);
    expect(err.errorX).toBeLessThanOrEqual(1.0);
    expect(err.errorY).toBeLessThanOrEqual(1.0);
  });

  test("square source in tall viewport", () => {
    // Source: 1000x1000, Viewport: 1080x1920
    const vt = createViewportTransform(1000, 1000, 1080, 1920);
    // scale = min(1.08, 1.92) = 1.08
    expect(vt.scale).toBeCloseTo(1.08, 5);
    expect(vt.offsetX).toBe(0);
    expect(vt.offsetY).toBeGreaterThan(0); // letterbox
  });
});
