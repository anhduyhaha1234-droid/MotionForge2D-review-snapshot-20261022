"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api, type SelectionInput } from "@/lib/api";
import { useProjectStore } from "@/stores/project";
import {
  createViewportTransform,
  canvasToSource,
  sourceToCanvas,
} from "@/lib/coordinates";

type Tool = "point" | "negative" | "bbox";

export function ScreenB() {
  const {
    projectId,
    project,
    currentFrame,
    setCurrentFrame,
    maskPreview,
    setMaskPreview,
    activeObject,
    setActiveObject,
    setProject,
    setScreen,
  } = useProjectStore();

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [tool, setTool] = useState<Tool>("point");
  const [points, setPoints] = useState<{ x: number; y: number; label: number }[]>([]);
  const [bbox, setBbox] = useState<{ x1: number; y1: number; x2: number; y2: number } | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const maskImageRef = useRef<HTMLImageElement | null>(null);
  const [autoObjects, setAutoObjects] = useState<Array<{
    object_index: number;
    name?: string;
    crop_png_base64?: string;
    bbox: { x: number; y: number; width: number; height: number };
    area: number;
  }>>([]);
  const [isAutoSegmenting, setIsAutoSegmenting] = useState(false);
  const [isClearingObjects, setIsClearingObjects] = useState(false);
  const autoPreviewRef = useRef(false);

  // Clear all tracked objects
  const handleClearObjects = async () => {
    if (!projectId) return;
    if (!confirm("Xóa tất cả nhân vật đã tách? Hành động này không thể hoàn tác.")) return;
    setIsClearingObjects(true);
    try {
      const res = await api.clearObjects(projectId);
      setProject(res.project);
      setActiveObject(null);
      setAutoObjects([]);
    } catch (err) {
      alert(`Lỗi: ${(err as Error).message}`);
    } finally {
      setIsClearingObjects(false);
    }
  };

  // Delete a single tracked object
  const handleDeleteSingleObject = async (objectId: string) => {
    if (!projectId) return;
    if (!confirm("Xóa nhân vật này?")) return;
    try {
      const res = await api.deleteObject(projectId, objectId);
      setProject(res.project);
      if (activeObject?.object_id === objectId) setActiveObject(null);
    } catch (err) {
      alert(`Lỗi: ${(err as Error).message}`);
    }
  };

  // 1-Click select auto-detected object → create TrackedObject + preview mask
  const handleSelectAutoObject = async (obj: {
    object_index: number;
    name?: string;
    crop_png_base64?: string;
    bbox: { x: number; y: number; width: number; height: number };
    area: number;
  }) => {
    if (!projectId) return;
    try {
      // 1. Create the TrackedObject with bbox selection
      const newObj = await api.createObject(projectId, {
        name: obj.name ?? `Vật thể #${obj.object_index + 1}`,
        selection: {
          mode: "bounding_box",
          frame_index: currentFrame,
          x: obj.bbox.x,
          y: obj.bbox.y,
          width: obj.bbox.width,
          height: obj.bbox.height,
        },
        scene_id: 0,
      });
      // 2. Set as active object (find it in returned project)
      const created = newObj.project.objects.find(
        (o) => o.object_id === newObj.object_id,
      );
      if (created) setActiveObject(created);
      // 3. Update project state so new object shows in list
      setProject(newObj.project);
      // 4. Preview mask on canvas
      previewMut.mutate();
    } catch (err) {
      alert(`Lỗi: ${(err as Error).message}`);
    }
  };

  const meta = project?.video_metadata;
  const frameUrl = projectId
    ? api.getFrameUrl(projectId, currentFrame)
    : null;

  // Draw canvas — declared BEFORE the image-loading effects so their
  // onload closures capture the stable, declared reference (React Compiler:
  // no access-before-declaration).
  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    const img = imageRef.current;
    if (!canvas || !container || !img || !meta) return;

    const rect = container.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const vt = createViewportTransform(
      meta.width,
      meta.height,
      canvas.width,
      canvas.height,
    );

    // Clear
    ctx.fillStyle = "#111";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw frame
    const dw = meta.width * vt.scale;
    const dh = meta.height * vt.scale;
    ctx.drawImage(img, vt.offsetX, vt.offsetY, dw, dh);

    // Draw mask overlay
    const maskImg = maskImageRef.current;
    if (maskImg) {
      ctx.globalAlpha = 0.4;
      ctx.drawImage(maskImg, vt.offsetX, vt.offsetY, dw, dh);
      ctx.globalAlpha = 1.0;
    }

    // Draw points
    for (const pt of points) {
      const cp = sourceToCanvas(pt.x, pt.y, vt);
      ctx.beginPath();
      ctx.arc(cp.x, cp.y, 6, 0, Math.PI * 2);
      ctx.fillStyle = pt.label === 1 ? "#22c55e" : "#ef4444";
      ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // Draw bbox
    if (bbox) {
      const tl = sourceToCanvas(bbox.x1, bbox.y1, vt);
      const br = sourceToCanvas(bbox.x2, bbox.y2, vt);
      ctx.strokeStyle = "#3b82f6";
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 3]);
      ctx.strokeRect(tl.x, tl.y, br.x - tl.x, br.y - tl.y);
      ctx.setLineDash([]);
    }
    // NOTE: maskPreview intentionally kept in deps — when the preview is
    // cleared (null), drawCanvas identity must change so the draw effect
    // re-runs and repaints without the stale mask overlay.
  }, [meta, points, bbox, maskPreview]);

  // Load frame image
  useEffect(() => {
    if (!frameUrl) return;
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      imageRef.current = img;
      setImageLoaded(true);
    };
    img.src = frameUrl;
  }, [frameUrl]);

  // Load mask preview
  useEffect(() => {
    if (!maskPreview) {
      maskImageRef.current = null;
      return;
    }
    const img = new Image();
    img.onload = () => {
      maskImageRef.current = img;
      drawCanvas();
    };
    img.src = `data:image/png;base64,${maskPreview}`;
  }, [maskPreview, drawCanvas]);

  useEffect(() => {
    drawCanvas();
  }, [drawCanvas, imageLoaded]);

  // Resize observer
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const ro = new ResizeObserver(() => drawCanvas());
    ro.observe(container);
    return () => ro.disconnect();
  }, [drawCanvas]);

  // Canvas click handler
  const handleCanvasClick = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      const canvas = canvasRef.current;
      if (!canvas || !meta) return;

      const rect = canvas.getBoundingClientRect();
      const cx = e.clientX - rect.left;
      const cy = e.clientY - rect.top;

      const vt = createViewportTransform(
        meta.width,
        meta.height,
        canvas.width,
        canvas.height,
      );
      const src = canvasToSource(cx, cy, vt);

      if (tool === "point") {
        setPoints((prev) => [...prev, { x: src.x, y: src.y, label: 1 }]);
        autoPreviewRef.current = true;
      } else if (tool === "negative") {
        setPoints((prev) => [...prev, { x: src.x, y: src.y, label: 0 }]);
      }
    },
    [meta, tool],
  );

  // Bbox drag
  const handleMouseDown = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (tool !== "bbox") return;
      const canvas = canvasRef.current;
      if (!canvas || !meta) return;
      const rect = canvas.getBoundingClientRect();
      const vt = createViewportTransform(meta.width, meta.height, canvas.width, canvas.height);
      const src = canvasToSource(e.clientX - rect.left, e.clientY - rect.top, vt);
      setBbox({ x1: src.x, y1: src.y, x2: src.x, y2: src.y });
      setIsDragging(true);
    },
    [meta, tool],
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (!isDragging || tool !== "bbox" || !bbox) return;
      const canvas = canvasRef.current;
      if (!canvas || !meta) return;
      const rect = canvas.getBoundingClientRect();
      const vt = createViewportTransform(meta.width, meta.height, canvas.width, canvas.height);
      const src = canvasToSource(e.clientX - rect.left, e.clientY - rect.top, vt);
      setBbox({ ...bbox, x2: src.x, y2: src.y });
    },
    [isDragging, meta, tool, bbox],
  );

  const handleMouseUp = useCallback(() => setIsDragging(false), []);

  // Preview mask mutation
  const previewMut = useMutation({
    mutationFn: async () => {
      if (!projectId) return;
      const sel = buildSelection();
      if (!sel) return;
      const result = await api.previewMask(projectId, {
        frame_index: currentFrame,
        selection: sel,
        backend: "sam2",
      });
      setMaskPreview(result.mask_png_base64);
    },
  });

  // Auto-trigger mask preview after adding a point+ click
  useEffect(() => {
    if (autoPreviewRef.current && points.length > 0) {
      autoPreviewRef.current = false;
      previewMut.mutate();
    }
  }, [points, previewMut]);

  // Accept mask → create object → propagate
  const acceptMut = useMutation({
    mutationFn: async () => {
      if (!projectId) return;
      const sel = buildSelection();
      if (!sel) return;

      // Create object — distinct name based on existing count
      const existingCount = project?.objects?.length ?? 0;
      const obj = await api.createObject(projectId, {
        name: `Nhân vật #${existingCount + 1}`,
        selection: sel,
        scene_id: 0,
      });
      // Find full TrackedObject in returned project
      const created = obj.project.objects.find((o) => o.object_id === obj.object_id);
      if (created) setActiveObject(created);
      setProject(obj.project);

      // Propagate
      const { job_id } = await api.propagateObject(projectId, obj.object_id);

      // Poll
      for (let i = 0; i < 120; i++) {
        await new Promise((r) => setTimeout(r, 1000));
        const job = await api.getJob(job_id);
        if (job.status === "completed") {
          const updated = await api.getObject(projectId, obj.object_id);
          setActiveObject(updated);
          setScreen("review");
          return;
        }
        if (job.status === "failed") throw new Error(job.message);
      }
    },
  });

  function buildSelection(): SelectionInput | null {
    if (tool === "bbox" && bbox) {
      return {
        mode: "bounding_box",
        frame_index: currentFrame,
        x: Math.min(bbox.x1, bbox.x2),
        y: Math.min(bbox.y1, bbox.y2),
        width: Math.abs(bbox.x2 - bbox.x1),
        height: Math.abs(bbox.y2 - bbox.y1),
      };
    }
    if (points.length > 0) {
      const lastPos = points.filter((p) => p.label === 1).pop();
      if (lastPos) {
        return {
          mode: "point",
          frame_index: currentFrame,
          x: lastPos.x,
          y: lastPos.y,
        };
      }
    }
    return null;
  }

  const clearPrompts = () => {
    setPoints([]);
    setBbox(null);
    setMaskPreview(null);
  };

  const handleAutoSegment = async () => {
    if (!projectId) return;
    setIsAutoSegmenting(true);
    try {
      const result = await api.autoSegmentObjects(projectId, 0);
      setAutoObjects(result.objects);
    } catch (err) {
      alert(`Lỗi: ${(err as Error).message}`);
    } finally {
      setIsAutoSegmenting(false);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-900 border-b border-gray-800">
        <h2 className="text-sm font-medium">Chọn vật thể</h2>
        <div className="flex items-center gap-2 text-sm text-gray-400">
          {meta && (
            <span>
              {meta.width}×{meta.height} • {meta.fps}fps • Frame{" "}
              {currentFrame}/{meta.total_frames - 1}
            </span>
          )}
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left: Existing objects + Auto-detected objects */}
        <aside className="w-64 bg-gray-900 border-r border-gray-800 p-4 space-y-3 overflow-y-auto">
          {/* Existing tracked objects with crop thumbnails */}
          {project?.objects && project.objects.length > 0 && (
            <>
              <div className="flex items-center justify-between">
                <h3 className="text-xs text-gray-500 uppercase">🎭 Nhân vật đã tách</h3>
                <button
                  onClick={handleClearObjects}
                  disabled={isClearingObjects}
                  className="px-2 py-0.5 text-[10px] bg-red-900/60 hover:bg-red-800 border border-red-800 rounded text-red-300 transition-colors"
                >
                  {isClearingObjects ? "Đang xóa..." : "🗑️ Xóa Tất Cả Nhân Vật Cũ"}
                </button>
              </div>
              <div className="space-y-1">
                {project.objects.map((obj) => (
                  <div
                    key={obj.object_id}
                    onClick={() => setActiveObject(obj)}
                    className="w-full text-left px-2.5 py-2 bg-gray-800/80 hover:bg-purple-900/40 border border-gray-700 hover:border-purple-500/50 rounded-lg text-xs transition-colors cursor-pointer"
                  >
                    <div className="flex items-center gap-2">
                      <img
                        src={api.getObjectCropUrl(projectId!, obj.object_id)}
                        alt={obj.name}
                        className="w-12 h-12 object-contain bg-black/60 rounded border border-purple-500/50 flex-shrink-0"
                        onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                      />
                      <div className="min-w-0 flex-1">
                        <p className="font-medium text-gray-200 truncate">{obj.name}</p>
                        <p className="text-[10px] text-gray-500">Scene {obj.scene_id}</p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteSingleObject(obj.object_id);
                        }}
                        className="p-1 text-red-400 hover:text-red-200 transition-colors"
                        title="Xóa nhân vật này"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          <h3 className="text-xs text-gray-500 uppercase mb-2">🎯 Vật thể phát hiện</h3>
          {autoObjects.length === 0 ? (
            <p className="text-xs text-gray-600">Chưa quét. Bấm &quot;🪄 Tự Động Bắt&quot; ở bên phải để tìm nhân vật &amp; vật thể.</p>
          ) : (
            <div className="space-y-1">
              {autoObjects.map((obj) => (
                <div
                  key={obj.object_index}
                  className="w-full text-left px-2.5 py-2 bg-gray-800/80 hover:bg-purple-900/40 border border-gray-700 hover:border-purple-500/50 rounded-lg text-xs transition-colors"
                >
                  <div className="flex items-center gap-2">
                    {obj.crop_png_base64 && (
                      <img
                        src={`data:image/png;base64,${obj.crop_png_base64}`}
                        alt={obj.name ?? `Vật thể #${obj.object_index + 1}`}
                        className="w-14 h-14 object-contain bg-black/80 rounded border border-purple-500/50 flex-shrink-0"
                      />
                    )}
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-gray-200 truncate">
                        🎯 {obj.name ?? `Vật thể #${obj.object_index + 1}`}
                      </p>
                      <p className="text-[10px] text-gray-500 mt-0.5">
                        Kích thước {obj.bbox.width}×{obj.bbox.height}px
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleSelectAutoObject(obj)}
                    className="mt-2 w-full py-1.5 text-[11px] bg-green-600 hover:bg-green-500 rounded text-white font-medium transition-colors"
                  >
                    ✅ Chọn & Bắt Nhân Vật Này
                  </button>
                </div>
              ))}
            </div>
          )}
        </aside>

        {/* Center: Canvas */}
        <div ref={containerRef} className="flex-1 relative">
          <canvas
            ref={canvasRef}
            className="absolute inset-0 cursor-crosshair"
            onClick={handleCanvasClick}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
          />
        </div>

        {/* Right: Tools */}
        <div className="w-56 bg-gray-900 border-l border-gray-800 p-3 space-y-4">
          <div>
            <h3 className="text-xs text-gray-500 uppercase mb-2">
              Công cụ chọn
            </h3>
            <div className="space-y-2">
              {(["point", "negative", "bbox"] as Tool[]).map((t) => (
                <div key={t}>
                  <button
                    onClick={() => setTool(t)}
                    className={`w-full px-2 py-1.5 text-xs rounded ${
                      tool === t
                        ? "bg-blue-600 text-white"
                        : "bg-gray-800 text-gray-300 hover:bg-gray-700"
                    }`}
                  >
                    {t === "point"
                      ? "Điểm +"
                      : t === "negative"
                      ? "Điểm −"
                      : "Hộp"}
                  </button>
                  {t === "point" && (
                    <p className="text-[11px] text-gray-400 mt-1">Click 1 điểm màu xanh trên thân nhân vật đối thủ.</p>
                  )}
                  {t === "negative" && (
                    <p className="text-[11px] text-gray-400 mt-1">Click điểm màu đỏ trên phông nền xung quanh để loại trừ.</p>
                  )}
                  {t === "bbox" && (
                    <p className="text-[11px] text-gray-400 mt-1">Kéo ô hình chữ nhật bao trùm toàn thân nhân vật.</p>
                  )}
                </div>
              ))}
              <button
                onClick={clearPrompts}
                className="w-full px-2 py-1.5 text-xs rounded bg-gray-800 text-gray-300 hover:bg-gray-700"
              >
                Xóa
              </button>
              <p className="text-[11px] text-gray-400 mt-1">Xóa hết điểm đã chấm để bắt đầu lại từ đầu.</p>
            </div>
          </div>

          <div className="space-y-1">
            <button
              onClick={() => previewMut.mutate()}
              disabled={previewMut.isPending || points.length === 0 && !bbox}
              className="w-full py-2 text-sm bg-gray-800 hover:bg-gray-700 disabled:bg-gray-900 disabled:text-gray-600 rounded"
            >
              {previewMut.isPending ? "Đang tạo mask..." : "Xem mask"}
            </button>
            <p className="text-[11px] text-gray-400 mt-1">Xem trước đường khoanh màu tím bao quanh nhân vật.</p>

            <button
              onClick={() => acceptMut.mutate()}
              disabled={
                acceptMut.isPending || (!maskPreview && points.length === 0 && !bbox)
              }
              className="w-full py-2 text-sm bg-green-700 hover:bg-green-600 disabled:bg-gray-900 disabled:text-gray-600 rounded"
            >
              {acceptMut.isPending ? "Đang tách object..." : "Chấp nhận & Tách"}
            </button>
            <p className="text-[11px] text-gray-400 mt-1">Xác nhận chọn & AI tự động theo vết (tracking) qua các frame.</p>
          </div>

          {/* Auto-Segment */}
          <div className="space-y-2">
            <button
              onClick={handleAutoSegment}
              disabled={isAutoSegmenting}
              className="w-full px-3 py-2 text-xs bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 rounded transition-colors"
            >
              {isAutoSegmenting ? "Đang quét..." : "🪄 Tự Động Bắt Tất Cả Nhân Vật"}
            </button>
            <p className="text-[11px] text-gray-400 mt-1">AI tự động quét & bóc tách toàn bộ nhân vật, bàn ghế có trong cảnh mà không cần chấm điểm thủ công.</p>
          </div>

          {/* Go to Screen C */}
          <button
            onClick={() => setScreen("replacement")}
            className="w-full py-3 text-sm bg-green-600 hover:bg-green-500 text-white font-bold rounded-xl shadow-lg shadow-green-900/30 transition-all"
          >
            ➡️ CHUYỂN SANG MÀN C THAY THẾ NHÂN VẬT
          </button>
          <p className="text-[11px] text-gray-400 mt-1">Sau khi đã chọn & tách nhân vật, bấm để chuyển sang bước thay ảnh nhân vật mới.</p>

          {/* 3-step guide */}
          <div className="bg-gray-800/60 border border-gray-700 rounded-lg p-3 space-y-2">
            <h4 className="text-xs font-medium text-gray-300">📋 Hướng dẫn 3 bước thay thế:</h4>
            <ol className="text-[11px] text-gray-400 space-y-1.5 list-decimal list-inside">
              <li>Chọn công cụ Điểm + / Hộp để khoanh nhân vật đối thủ.</li>
              <li>Bấm <span className="text-green-400">Chấp nhận & Tách</span> để AI tách & theo vết.</li>
              <li>Bấm <span className="text-green-400">➡️ Chuyển sang Màn C</span> để thay ảnh nhân vật mới.</li>
            </ol>
          </div>

          {/* Frame slider */}
          <div>
            <h3 className="text-xs text-gray-500 uppercase mb-2">
              Frame
            </h3>
            <input
              type="range"
              min={0}
              max={(meta?.total_frames ?? 1) - 1}
              value={currentFrame}
              onChange={(e) => setCurrentFrame(Number(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>0</span>
              <span>{(meta?.total_frames ?? 1) - 1}</span>
            </div>
            <p className="text-[11px] text-gray-400 mt-1">💡 Kéo thanh này để xem trước các giây/khung hình khác nhau trong video. Hãy chọn khung hình có nhân vật hiển thị rõ nhất để chấm điểm.</p>
          </div>

          {/* Points list */}
          {points.length > 0 && (
            <div>
              <h3 className="text-xs text-gray-500 uppercase mb-1">
                Điểm đã chọn ({points.length})
              </h3>
              <div className="max-h-32 overflow-y-auto text-xs text-gray-400 space-y-0.5">
                {points.map((p, i) => (
                  <div key={i} className="flex justify-between">
                    <span className={p.label === 1 ? "text-green-400" : "text-red-400"}>
                      {p.label === 1 ? "+" : "−"}({Math.round(p.x)},{Math.round(p.y)})
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
