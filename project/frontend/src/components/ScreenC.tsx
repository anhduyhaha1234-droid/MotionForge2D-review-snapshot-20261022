"use client";

import { useEffect } from "react";
import { api, type GalleryFrame } from "@/lib/api";
import { useProjectStore } from "@/stores/project";

export function ScreenC() {
  const {
    projectId,
    project,
    activeObject,
    gallery,
    setGallery,
    setScreen,
    setActiveObject,
  } = useProjectStore();

  const objectId = activeObject?.object_id;
  const motion = activeObject?.motion;
  const frames = motion?.frames ?? [];
  const totalFrames = frames.length;
  const trackedFrames = frames.filter((f) => f.visibility && f.area > 0).length;
  const trackedRatio = totalFrames > 0 ? trackedFrames / totalFrames : 0;

  // Load gallery
  useEffect(() => {
    if (!projectId || !objectId) return;
    api.getGallery(projectId, objectId).then(setGallery).catch(console.error);
  }, [projectId, objectId, setGallery]);

  const representativeFrames = gallery?.crops ?? [];

  return (
    <div className="flex flex-col h-screen">
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-900 border-b border-gray-800">
        <h2 className="text-sm font-medium">Kết quả tách object</h2>
        <button
          onClick={() => setScreen("selection")}
          className="text-xs text-gray-400 hover:text-gray-200"
        >
          ← Quay lại chọn
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left: Object info */}
        <div className="w-64 bg-gray-900 border-r border-gray-800 p-4 space-y-4">
          <div>
            <h3 className="text-xs text-gray-500 uppercase mb-1">
              Thông tin object
            </h3>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Tên:</span>
                <span>{activeObject?.name ?? "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Scene:</span>
                <span>{activeObject?.scene_id ?? 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Backend:</span>
                <span>{motion?.tracking_backend ?? "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Frame range:</span>
                <span>
                  {frames.length > 0
                    ? `${frames[0].frame_index}–${frames[frames.length - 1].frame_index}`
                    : "—"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Tỷ lệ tracked:</span>
                <span
                  className={
                    trackedRatio >= 0.9
                      ? "text-green-400"
                      : trackedRatio >= 0.7
                      ? "text-yellow-400"
                      : "text-red-400"
                  }
                >
                  {(trackedRatio * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          <div className="space-y-1">
            <button
              onClick={() => {
                // Auto-select first object if none active, then go to replacement
                if (!activeObject && project?.objects?.length) {
                  setActiveObject(project.objects[0]);
                }
                setScreen("replacement");
              }}
              className="w-full py-2 text-sm bg-blue-700 hover:bg-blue-600 rounded"
            >
              Thay ảnh →
            </button>
            <p className="text-[11px] text-gray-400 mt-1">Chuyển sang bước thay nhân vật bằng ảnh PNG mới.</p>
            <button
              onClick={() => setScreen("selection")}
              className="w-full py-2 text-sm bg-gray-800 hover:bg-gray-700 rounded"
            >
              Sửa vùng chọn
            </button>
            <p className="text-[11px] text-gray-400 mt-1">Quay lại chấm điểm lại vùng nhân vật nếu chưa ưng.</p>
            <button
              className="w-full py-2 text-sm bg-gray-800 hover:bg-gray-700 rounded text-red-400"
            >
              Xóa object
            </button>
            <p className="text-[11px] text-gray-400 mt-1">Xóa nhân vật đã tách khỏi dự án này.</p>
          </div>
        </div>

        {/* Center: Gallery */}
        <div className="flex-1 overflow-auto p-4">
          <h3 className="text-xs text-gray-500 uppercase mb-3">
            Gallery frame đại diện ({representativeFrames.length} frames)
          </h3>
          <div className="grid grid-cols-4 gap-3">
            {representativeFrames.map((frame) => (
              <GalleryCard
                key={frame.frame_index}
                frame={frame}
                projectId={projectId!}
                objectId={objectId!}
              />
            ))}
          </div>

          {representativeFrames.length === 0 && (
            <div className="flex items-center justify-center h-64 text-gray-600">
              Đang tải gallery...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function GalleryCard({
  frame,
  projectId,
  objectId,
}: {
  frame: GalleryFrame;
  projectId: string;
  objectId: string;
}) {
  const cropUrl = `http://localhost:8000/api/projects/${projectId}/objects/${objectId}/crops/${frame.frame_index}`;

  return (
    <div className="bg-gray-800 rounded overflow-hidden">
      <div className="aspect-square bg-gray-900 relative">
        {/* Checkerboard background for transparency */}
        <div
          className="absolute inset-0"
          style={{
            backgroundImage:
              "linear-gradient(45deg, #222 25%, transparent 25%), linear-gradient(-45deg, #222 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #222 75%), linear-gradient(-45deg, transparent 75%, #222 75%)",
            backgroundSize: "16px 16px",
            backgroundPosition: "0 0, 0 8px, 8px -8px, -8px 0px",
          }}
        />
        <img
          src={cropUrl}
          alt={`Frame ${frame.frame_index}`}
          className="absolute inset-0 w-full h-full object-contain"
          onError={(e) => {
            (e.target as HTMLImageElement).style.display = "none";
          }}
        />
      </div>
      <div className="p-1.5">
        <div className="flex justify-between text-xs">
          <span className="text-gray-300">F{frame.frame_index}</span>
          <span className="text-gray-500">{frame.reason}</span>
        </div>
      </div>
    </div>
  );
}
