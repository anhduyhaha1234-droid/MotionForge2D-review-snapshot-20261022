/**
 * Coordinate Transform Module
 *
 * Single source of truth for coordinate conversion between:
 * - Source video coordinates (pixels)
 * - Canvas coordinates (viewport-scaled)
 * - Normalized coordinates (0-1)
 */

export interface ViewportTransform {
  scale: number;
  offsetX: number;
  offsetY: number;
}

/**
 * Create a viewport transform that fits a source size into a canvas size.
 */
export function createViewportTransform(
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

/** Source video coords → Canvas coords */
export function sourceToCanvas(
  sx: number,
  sy: number,
  vt: ViewportTransform,
): { x: number; y: number } {
  return {
    x: sx * vt.scale + vt.offsetX,
    y: sy * vt.scale + vt.offsetY,
  };
}

/** Canvas coords → Source video coords */
export function canvasToSource(
  cx: number,
  cy: number,
  vt: ViewportTransform,
): { x: number; y: number } {
  return {
    x: (cx - vt.offsetX) / vt.scale,
    y: (cy - vt.offsetY) / vt.scale,
  };
}

/** Source video coords → Normalized coords (0-1) */
export function sourceToNormalized(
  sx: number,
  sy: number,
  sourceW: number,
  sourceH: number,
): { x: number; y: number } {
  return { x: sx / sourceW, y: sy / sourceH };
}

/** Normalized coords → Source video coords */
export function normalizedToSource(
  nx: number,
  ny: number,
  sourceW: number,
  sourceH: number,
): { x: number; y: number } {
  return { x: nx * sourceW, y: ny * sourceH };
}

/** Scale a dimension from source to canvas */
export function scaleToCanvas(size: number, vt: ViewportTransform): number {
  return size * vt.scale;
}

/** Scale a dimension from canvas to source */
export function scaleToSource(size: number, vt: ViewportTransform): number {
  return size / vt.scale;
}
