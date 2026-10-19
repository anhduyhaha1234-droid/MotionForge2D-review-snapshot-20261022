"use client";

/**
 * CompositeCanvas — Konva-based composite preview
 *
 * Renders: original frame → mask overlay → replacement image → bbox → centroid → anchor
 * All transforms use source video coordinates; Konva scales to viewport.
 */

import { useEffect, useRef, useState, useCallback } from "react";
import Konva from "konva";
import { createViewportTransform } from "@/lib/coordinates";
import type { FrameMotion, ReplacementConfig } from "@/lib/api";

/* ── Types ─────────────────────────────────────────────────────────────── */

export interface CompositeObjectConfig {
  objectId: string;
  motion: FrameMotion | null;
  replacementUrl: string | null;
  replacement: ReplacementConfig | null;
}

interface CompositeCanvasProps {
  frameUrl: string | null;
  maskUrl: string | null;
  inpaintedUrl?: string | null;
  replacementUrl: string | null;
  sequenceFrameUrl: string | null;
  frameMotion: FrameMotion | null;
  replacement: ReplacementConfig;
  videoWidth: number;
  videoHeight: number;
  previewMode: "original" | "mask" | "result" | "comparison";
  allObjects?: CompositeObjectConfig[];
}

interface TransformResult {
  x: number;
  y: number;
  width: number;
  height: number;
  rotation: number;
  opacity: number;
}

/** A loaded image paired with the URL that produced it. */
interface LoadedImage {
  url: string;
  img: HTMLImageElement;
}

/**
 * Derive the effective image for a prop URL.
 *
 * The loaded record is only usable while it was produced by the exact URL
 * currently passed as a prop. If the URL changed, became empty, or no image
 * has loaded yet, the result is null — so a stale image can never be drawn
 * for a URL that no longer matches (immediate null semantics, no timing
 * dependence and no setState-in-effect).
 */
function effectiveImage(
  loaded: { url: string; img: HTMLImageElement } | null,
  currentUrl: string | null | undefined,
): HTMLImageElement | null {
  if (!currentUrl) return null;
  if (!loaded || loaded.url !== currentUrl) return null;
  return loaded.img;
}

/* ── Transform math ────────────────────────────────────────────────────── */

function computeReplacementTransform(
  motion: FrameMotion,
  rep: ReplacementConfig,
  assetNaturalW: number,
  assetNaturalH: number,
  frameW: number,
  frameH: number,
): TransformResult {
  // 1. Tracked centroid
  const cx = motion.centroid_x;
  const cy = motion.centroid_y;

  // 2. Bbox scaled by tracked scale
  const bboxW = motion.bbox.width * motion.scale_x;
  const bboxH = motion.bbox.height * motion.scale_y;

  // 3. Target size based on fit_mode
  let targetW: number;
  let targetH: number;
  if (rep.fit_mode === "contain") {
    const ratio = Math.min(bboxW / assetNaturalW, bboxH / assetNaturalH);
    targetW = assetNaturalW * ratio;
    targetH = assetNaturalH * ratio;
  } else if (rep.fit_mode === "cover") {
    const ratio = Math.max(bboxW / assetNaturalW, bboxH / assetNaturalH);
    targetW = assetNaturalW * ratio;
    targetH = assetNaturalH * ratio;
  } else {
    // stretch
    targetW = bboxW;
    targetH = bboxH;
  }

  // 4. Apply scale multiplier
  const finalW = targetW * rep.scale;
  const finalH = targetH * rep.scale;

  // 4b. Auto-anchor: default to bottom-center (0.5, 1.0) so the character's
  // feet/hips sit exactly on the original surface. The stored default is
  // center (0.5, 0.5); we lift it to the bottom anchor automatically unless
  // the user has explicitly set a different anchor.
  const autoBottom =
    rep.anchor.x === 0.5 && (rep.anchor.y === 0.5 || rep.anchor.y === 1.0);
  const anchorX = rep.anchor.x;
  const anchorY = autoBottom ? 1.0 : rep.anchor.y;
  const anchorPxX = finalW * anchorX;
  const anchorPxY = finalH * anchorY;

  // 6. Position — actual coords = (centroid + offset), anchor at bottom
  const posX = cx - anchorPxX + rep.offset.x * frameW;
  const posY = cy - anchorPxY + rep.offset.y * frameH;

  // 7. Rotation
  const totalRotation = motion.rotation_deg + rep.rotation_offset_deg;

  return {
    x: posX,
    y: posY,
    width: finalW,
    height: finalH,
    rotation: totalRotation,
    opacity: rep.opacity,
  };
}

/* ── Component ─────────────────────────────────────────────────────────── */

export function CompositeCanvas({
  frameUrl,
  maskUrl,
  inpaintedUrl,
  replacementUrl,
  sequenceFrameUrl,
  frameMotion,
  replacement,
  videoWidth,
  videoHeight,
  previewMode,
  allObjects,
}: CompositeCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<Konva.Stage | null>(null);
  const layerRef = useRef<Konva.Layer | null>(null);

  const [frameImg, setFrameImg] = useState<LoadedImage | null>(null);
  const [maskImg, setMaskImg] = useState<LoadedImage | null>(null);
  const [inpaintedImg, setInpaintedImg] = useState<LoadedImage | null>(null);
  const [repImg, setRepImg] = useState<LoadedImage | null>(null);
  const [sequenceFrameImg, setSequenceFrameImg] = useState<LoadedImage | null>(null);
  const [multiObjImgs, setMultiObjImgs] = useState<Map<string, LoadedImage>>(new Map());

  // Effective images derived from the URL-paired loaded records. A null or
  // changed URL immediately yields null (see effectiveImage), so stale assets
  // are never drawn — no synchronous setState in effect bodies required.
  const effFrameImg = effectiveImage(frameImg, frameUrl);
  const effMaskImg = effectiveImage(maskImg, maskUrl);
  const effInpaintedImg = effectiveImage(inpaintedImg, inpaintedUrl);
  const effRepImg = effectiveImage(repImg, replacementUrl);
  const effSequenceFrameImg = effectiveImage(sequenceFrameImg, sequenceFrameUrl);

  /* ── Load images ─────────────────────────────────────────────────────── */
  // Each effect only kicks off an async image load. Loaded records are
  // associated with the exact URL that produced them; the effective-image
  // derivation above guards rendering against URL changes/empties.

  useEffect(() => {
    if (!frameUrl) return;
    const img = new window.Image();
    img.crossOrigin = "anonymous";
    img.onload = () => setFrameImg({ url: frameUrl, img });
    img.onerror = () => setFrameImg(null);
    img.src = frameUrl;
  }, [frameUrl]);

  useEffect(() => {
    if (!maskUrl) return;
    const img = new window.Image();
    img.crossOrigin = "anonymous";
    img.onload = () => setMaskImg({ url: maskUrl, img });
    img.onerror = () => setMaskImg(null);
    img.src = maskUrl;
  }, [maskUrl]);

  useEffect(() => {
    if (!inpaintedUrl) return;
    const img = new window.Image();
    img.crossOrigin = "anonymous";
    img.onload = () => setInpaintedImg({ url: inpaintedUrl, img });
    img.onerror = () => setInpaintedImg(null);
    img.src = inpaintedUrl;
  }, [inpaintedUrl]);

  useEffect(() => {
    if (!replacementUrl) return;
    const img = new window.Image();
    img.crossOrigin = "anonymous";
    img.onload = () => setRepImg({ url: replacementUrl, img });
    img.onerror = () => setRepImg(null);
    img.src = replacementUrl;
  }, [replacementUrl]);

  useEffect(() => {
    if (!sequenceFrameUrl) return;
    const img = new window.Image();
    img.crossOrigin = "anonymous";
    img.onload = () => setSequenceFrameImg({ url: sequenceFrameUrl, img });
    img.onerror = () => setSequenceFrameImg(null);
    img.src = sequenceFrameUrl;
  }, [sequenceFrameUrl]);

  /* ── Load multi-object images ─────────────────────────────────────────── */

  useEffect(() => {
    if (!allObjects || allObjects.length === 0) return;

    const newMap = new Map<string, LoadedImage>();
    let loaded = 0;
    const total = allObjects.filter((o) => o.replacementUrl).length;

    if (total === 0) return;

    for (const obj of allObjects) {
      if (!obj.replacementUrl) continue;
      const img = new window.Image();
      img.crossOrigin = "anonymous";
      img.onload = () => {
        newMap.set(obj.objectId, { url: obj.replacementUrl!, img });
        loaded++;
        if (loaded === total) {
          setMultiObjImgs(new Map(newMap));
        }
      };
      img.onerror = () => {
        loaded++;
        if (loaded === total) {
          setMultiObjImgs(new Map(newMap));
        }
      };
      img.src = obj.replacementUrl;
    }
  }, [allObjects]);

  /* ── Stage setup & resize ────────────────────────────────────────────── */

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

  /* ── Render scene ────────────────────────────────────────────────────── */

  useEffect(() => {
    const layer = layerRef.current;
    const stage = stageRef.current;
    if (!layer || !stage) return;

    layer.destroyChildren();

    const stageW = stage.width();
    const stageH = stage.height();
    const vt = createViewportTransform(videoWidth, videoHeight, stageW, stageH);
    const dw = videoWidth * vt.scale;
    const dh = videoHeight * vt.scale;
    const ox = vt.offsetX;
    const oy = vt.offsetY;

    // Choose active replacement image based on mode
    const activeRepImg =
      replacement.mode === "frame_sequence" ? effSequenceFrameImg : effRepImg;

    // Checkerboard background
    const bgGroup = new Konva.Group({ x: ox, y: oy, width: dw, height: dh });
    const CHECK = 12;
    const cols = Math.ceil(dw / CHECK);
    const rows = Math.ceil(dh / CHECK);
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        bgGroup.add(
          new Konva.Rect({
            x: c * CHECK,
            y: r * CHECK,
            width: CHECK,
            height: CHECK,
            fill: (r + c) % 2 === 0 ? "#1a1a2e" : "#16162a",
          }),
        );
      }
    }
    layer.add(bgGroup);

    // Helper: draw frame image scaled to viewport
    const drawFrame = () => {
      if (!effFrameImg) return;
      const konvaImg = new Konva.Image({
        x: ox,
        y: oy,
        image: effFrameImg,
        width: dw,
        height: dh,
      });
      layer.add(konvaImg);
    };

    if (previewMode === "original") {
      drawFrame();
      layer.batchDraw();
      return;
    }

    if (previewMode === "mask") {
      drawFrame();
      if (effMaskImg) {
        const m = new Konva.Image({
          x: ox,
          y: oy,
          image: effMaskImg,
          width: dw,
          height: dh,
          opacity: 0.5,
          // green tint via globalCompositeOperation workaround:
          // Konva doesn't support composite ops directly, so use opacity
        });
        layer.add(m);
      }
      layer.batchDraw();
      return;
    }

    // "result" or "comparison" — draw composite
    const drawComposite = (offsetX: number) => {
      // Background layer: inpainted frame (original character removed) when
      // available, else the plain frame.
      const bgImg = effInpaintedImg ?? effFrameImg;
      if (bgImg) {
        layer.add(
          new Konva.Image({
            x: offsetX + ox,
            y: oy,
            image: bgImg,
            width: dw,
            height: dh,
          }),
        );
      }

      // Mask overlay (semi-transparent green)
      if (effMaskImg) {
        // We'll tint green by drawing a green rect then the mask on top
        // Actually, just show the mask at low opacity
        layer.add(
          new Konva.Image({
            x: offsetX + ox,
            y: oy,
            image: effMaskImg,
            width: dw,
            height: dh,
            opacity: 0.35,
          }),
        );
      }

      // Multi-object mode: render all objects when allObjects is provided
      if (allObjects && allObjects.length > 0) {
        for (const obj of allObjects) {
          // Only render the object's replacement while its entry was loaded
          // from the exact URL currently configured for it. Removed objects,
          // or objects whose replacement URL changed/emptied, never render a
          // stale asset.
          const entry = multiObjImgs.get(obj.objectId);
          const objImg =
            entry && obj.replacementUrl && entry.url === obj.replacementUrl
              ? entry.img
              : null;
          if (!objImg || !obj.motion || !obj.replacement) continue;

          const tf = computeReplacementTransform(
            obj.motion,
            obj.replacement,
            objImg.naturalWidth,
            objImg.naturalHeight,
            videoWidth,
            videoHeight,
          );

          const scaledX = tf.x * vt.scale + offsetX + ox;
          const scaledY = tf.y * vt.scale + oy;
          const scaledW = tf.width * vt.scale;
          const scaledH = tf.height * vt.scale;
          const centerX = scaledX + scaledW / 2;
          const centerY = scaledY + scaledH / 2;

          const repNode = new Konva.Image({
            x: centerX,
            y: centerY,
            width: scaledW,
            height: scaledH,
            image: objImg,
            opacity: tf.opacity,
            rotation: tf.rotation,
            offsetX: scaledW / 2,
            offsetY: scaledH / 2,
          });
          layer.add(repNode);

          // Bbox for each object
          const bbox = obj.motion.bbox;
          const bx = bbox.x * vt.scale + offsetX + ox;
          const by = bbox.y * vt.scale + oy;
          const bw = bbox.width * vt.scale;
          const bh = bbox.height * vt.scale;
          layer.add(
            new Konva.Rect({
              x: bx,
              y: by,
              width: bw,
              height: bh,
              stroke: "#3b82f6",
              strokeWidth: 1.5,
              dash: [5, 3],
              listening: false,
            }),
          );

          // Centroid dot
          const cDotX = obj.motion.centroid_x * vt.scale + offsetX + ox;
          const cDotY = obj.motion.centroid_y * vt.scale + oy;
          layer.add(
            new Konva.Circle({
              x: cDotX,
              y: cDotY,
              radius: 4,
              fill: "#22c55e",
              stroke: "#fff",
              strokeWidth: 1,
            }),
          );

          // Label
          layer.add(
            new Konva.Text({
              x: bx,
              y: by - 14,
              text: obj.objectId,
              fontSize: 10,
              fill: "#3b82f6",
              fontFamily: "sans-serif",
            }),
          );
        }
        return;
      }

      // Single-object mode (original behavior)
      // Fallback motion: when frameMotion is missing (e.g. bbox-created object
      // without tracking), build one from a fixed bbox so the replacement
      // image still draws over the original character area.
      const fallbackMotion: FrameMotion | null = frameMotion
        ? frameMotion
        : null;
      const effMotion = fallbackMotion;

      if (activeRepImg && (effMotion || true)) {
        let tf: TransformResult;
        // Fallback placement variables (used for bbox when no motion)
        let fallbackW = 0;
        let fallbackH = 0;
        const cx = videoWidth / 2;
        const cy = videoHeight / 2;
        if (effMotion) {
          tf = computeReplacementTransform(
            effMotion,
            replacement,
            activeRepImg.naturalWidth,
            activeRepImg.naturalHeight,
            videoWidth,
            videoHeight,
          );
        } else {
          // No motion data: place at video center with a sensible size.
          // Use the replacement's natural size scaled to 30% of frame height.
          fallbackH = videoHeight * 0.3;
          fallbackW =
            (activeRepImg.naturalWidth / activeRepImg.naturalHeight) * fallbackH;
          const anchorPxX = fallbackW * replacement.anchor.x;
          const anchorPxY = fallbackH * (replacement.anchor.y === 0.5 ? 1.0 : replacement.anchor.y);
          tf = {
            x: cx - anchorPxX + replacement.offset.x * videoWidth,
            y: cy - anchorPxY + replacement.offset.y * videoHeight,
            width: fallbackW * replacement.scale,
            height: fallbackH * replacement.scale,
            rotation: replacement.rotation_offset_deg,
            opacity: replacement.opacity,
          };
        }

        // Scale from source coords to viewport coords
        const scaledX = tf.x * vt.scale + offsetX + ox;
        const scaledY = tf.y * vt.scale + oy;
        const scaledW = tf.width * vt.scale;
        const scaledH = tf.height * vt.scale;

        // Center of the replacement for rotation
        const centerX = scaledX + scaledW / 2;
        const centerY = scaledY + scaledH / 2;

        const repNode = new Konva.Image({
          x: scaledX,
          y: scaledY,
          width: scaledW,
          height: scaledH,
          image: activeRepImg,
          opacity: tf.opacity,
          rotation: tf.rotation,
          offsetX: scaledW / 2,
          offsetY: scaledH / 2,
        });
        // Fix: position at center
        repNode.x(centerX);
        repNode.y(centerY);
        layer.add(repNode);

        // Bounding box rectangle (from motion if available, else fallback area)
        const bbox = effMotion
          ? frameMotion!.bbox
          : { x: cx - fallbackW / 2, y: cy - fallbackH / 2, width: fallbackW, height: fallbackH };
        const bx = bbox.x * vt.scale + offsetX + ox;
        const by = bbox.y * vt.scale + oy;
        const bw = bbox.width * vt.scale;
        const bh = bbox.height * vt.scale;
        layer.add(
          new Konva.Rect({
            x: bx,
            y: by,
            width: bw,
            height: bh,
            stroke: "#3b82f6",
            strokeWidth: 1.5,
            dash: [5, 3],
            listening: false,
          }),
        );

        // Centroid dot
        const cDotX = (effMotion ? effMotion.centroid_x : cx) * vt.scale + offsetX + ox;
        const cDotY = (effMotion ? effMotion.centroid_y : cy) * vt.scale + oy;
        layer.add(
          new Konva.Circle({
            x: cDotX,
            y: cDotY,
            radius: 4,
            fill: "#22c55e",
            stroke: "#fff",
            strokeWidth: 1,
          }),
        );

        // The anchor point is at the centroid in source coords.
        // (anchorAbsX/anchorAbsY were computed but never rendered — removed.)
        const anchorOnScreenX = (effMotion ? effMotion.centroid_x : cx) * vt.scale + offsetX + ox;
        const anchorOnScreenY = (effMotion ? effMotion.centroid_y : cy) * vt.scale + oy;
        layer.add(
          new Konva.Star({
            x: anchorOnScreenX,
            y: anchorOnScreenY,
            numPoints: 4,
            innerRadius: 3,
            outerRadius: 7,
            fill: "#f59e0b",
            stroke: "#fff",
            strokeWidth: 0.5,
          }),
        );

        // Replacement outline (dashed green rect showing placement area)
        layer.add(
          new Konva.Rect({
            x: centerX,
            y: centerY,
            width: scaledW,
            height: scaledH,
            offsetX: scaledW / 2,
            offsetY: scaledH / 2,
            stroke: "#22c55e",
            strokeWidth: 1,
            dash: [3, 3],
            rotation: tf.rotation,
            listening: false,
          }),
        );
      }
    };

    if (previewMode === "comparison") {
      // Split 50/50: left = original frame, right = composite result
      const halfW = stageW / 2;

      // ── Left half: original (no overlay) ──
      if (effFrameImg) {
        layer.add(
          new Konva.Image({
            x: ox,
            y: oy,
            image: effFrameImg,
            width: halfW - ox,
            height: dh,
            crop: { x: 0, y: 0, width: videoWidth / 2, height: videoHeight },
          }),
        );
      }

      // Divider line
      layer.add(
        new Konva.Line({
          points: [halfW, oy, halfW, oy + dh],
          stroke: "#888",
          strokeWidth: 2,
          dash: [6, 4],
        }),
      );

      // ── Right half: composite result (full draw at offset) ──
      drawComposite(halfW);

      // Labels
      layer.add(
        new Konva.Text({
          x: ox + 8,
          y: oy + 8,
          text: "📷 Ảnh Gốc (Gốc ban đầu)",
          fontSize: 14,
          fill: "#94a3b8",
          fontFamily: "sans-serif",
          fontStyle: "bold",
        }),
      );
      layer.add(
        new Konva.Rect({
          x: ox,
          y: oy,
          width: halfW - ox,
          height: 32,
          fill: "rgba(0,0,0,0.45)",
          listening: false,
        }),
      );
      layer.add(
        new Konva.Text({
          x: halfW + ox + 8,
          y: oy + 8,
          text: "🎨 Kết Quả Thay Thế (Sau khi đổi)",
          fontSize: 14,
          fill: "#c084fc",
          fontFamily: "sans-serif",
          fontStyle: "bold",
        }),
      );
      layer.add(
        new Konva.Rect({
          x: halfW + ox,
          y: oy,
          width: halfW - ox,
          height: 32,
          fill: "rgba(0,0,0,0.45)",
          listening: false,
        }),
      );
    } else {
      // "result"
      drawComposite(0);
    }

    layer.batchDraw();
  }, [
    effFrameImg,
    effMaskImg,
    effInpaintedImg,
    effRepImg,
    effSequenceFrameImg,
    frameMotion,
    replacement,
    videoWidth,
    videoHeight,
    previewMode,
    allObjects,
    multiObjImgs,
  ]);

  return (
    <div
      ref={containerRef}
      className="w-full h-full bg-gray-950"
      data-testid="composite-canvas"
    />
  );
}
