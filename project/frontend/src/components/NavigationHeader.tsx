"use client";

import { useProjectStore } from "@/stores/project";

interface Props {
  onOpenAssembly?: () => void;
}

export function NavigationHeader({ onOpenAssembly }: Props) {
  const { projectId, project, screen, setScreen, activeSceneId, setActiveSceneId } = useProjectStore();

  if (!projectId || screen === "start") return null;

  const scenes = project?.scenes ?? [];
  const currentSceneIdx = activeSceneId !== null
    ? scenes.findIndex((s) => s.scene_id === activeSceneId)
    : -1;

  const handlePrevScene = () => {
    if (currentSceneIdx > 0) {
      setActiveSceneId(scenes[currentSceneIdx - 1].scene_id);
    }
  };

  const handleNextScene = () => {
    if (currentSceneIdx < scenes.length - 1) {
      setActiveSceneId(scenes[currentSceneIdx + 1].scene_id);
    }
  };

  return (
    <div className="sticky top-0 z-40 bg-slate-950/95 backdrop-blur border-b border-slate-800 px-4 py-2 flex items-center justify-between gap-4">
      {/* Left: Back button */}
      <button
        onClick={() => setScreen("start")}
        className="px-3 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg transition-colors flex items-center gap-1.5"
      >
        ⬅️ Quay Lại Trang Chủ
      </button>

      {/* Center: Project info */}
      <div className="flex items-center gap-3 text-xs text-gray-400">
        <span className="font-medium text-gray-300">
          {project?.name || "Dự án"}
        </span>
        <span className="text-gray-600">|</span>
        <span className="font-mono text-purple-400 bg-purple-950/60 px-2 py-0.5 rounded">
          {projectId.slice(0, 8)}
        </span>
        {activeSceneId !== null && scenes.length > 0 && (
          <>
            <span className="text-gray-600">|</span>
            <span className="text-blue-400">
              Cảnh #{activeSceneId + 1} / {scenes.length}
            </span>
          </>
        )}
      </div>

      {/* Right: Scene navigation + Assembly */}
      <div className="flex items-center gap-2">
        <button
          onClick={onOpenAssembly}
          className="px-3 py-1.5 text-xs bg-purple-600 hover:bg-purple-500 rounded-lg font-medium text-white shadow-lg shadow-purple-900/40 transition-colors"
        >
          🔮 Ghép Video Hoàn Chỉnh
        </button>
        {scenes.length > 0 && (
          <>
            <button
              onClick={handlePrevScene}
              disabled={currentSceneIdx <= 0}
              className="px-2 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed border border-gray-700 rounded transition-colors"
            >
              ◀️ Cảnh Trước
            </button>
            <button
              onClick={handleNextScene}
              disabled={currentSceneIdx >= scenes.length - 1}
              className="px-2 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed border border-gray-700 rounded transition-colors"
            >
              Cảnh Sau ▶️
            </button>
          </>
        )}
      </div>
    </div>
  );
}
