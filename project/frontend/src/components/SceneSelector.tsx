"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type SceneDetail } from "@/lib/api";
import { useProjectStore } from "@/stores/project";

const STATUS_CONFIG: Record<
  SceneDetail["status"],
  { label: string; color: string; bg: string; emoji: string }
> = {
  approved: {
    label: "Đã duyệt",
    color: "text-green-300",
    bg: "bg-green-900/50 border-green-700",
    emoji: "🟢",
  },
  draft: {
    label: "Đang sửa",
    color: "text-yellow-300",
    bg: "bg-yellow-900/50 border-yellow-700",
    emoji: "🟡",
  },
  pending: {
    label: "Chưa làm",
    color: "text-gray-400",
    bg: "bg-gray-800/50 border-gray-700",
    emoji: "⚪",
  },
};

export function SceneSelector() {
  const projectId = useProjectStore((s) => s.projectId);
  const activeSceneId = useProjectStore((s) => s.activeSceneId);
  const setActiveSceneId = useProjectStore((s) => s.setActiveSceneId);
  const queryClient = useQueryClient();

  const { data: scenes = [], isLoading } = useQuery({
    queryKey: ["scenes", projectId],
    queryFn: () => api.getSceneDetails(projectId!),
    enabled: !!projectId,
  });

  const chunkMut = useMutation({
    mutationFn: () => api.chunkScenes(projectId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scenes", projectId] });
    },
  });

  const approveMut = useMutation({
    mutationFn: (sceneId: number) =>
      api.updateSceneStatus(projectId!, sceneId, "approved"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scenes", projectId] });
      // Auto-advance to next scene
      if (activeSceneId !== null) {
        const next = scenes.find(
          (s) => s.scene_id > activeSceneId && s.status !== "approved",
        );
        if (next) setActiveSceneId(next.scene_id);
      }
    },
  });

  const approvedCount = scenes.filter((s) => s.status === "approved").length;
  const allApproved = scenes.length > 0 && approvedCount === scenes.length;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-300">
          Phân cảnh ({approvedCount}/{scenes.length} đã duyệt)
        </h3>
        <button
          onClick={() => chunkMut.mutate()}
          disabled={chunkMut.isPending}
          className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-500
            disabled:bg-gray-700 rounded transition-colors"
        >
          {chunkMut.isPending ? "Đang cắt..." : "🔄 Cắt cảnh"}
        </button>
      </div>

      {isLoading && (
        <p className="text-xs text-gray-500">Đang tải...</p>
      )}

      <div className="flex flex-col gap-1 max-h-60 overflow-y-auto">
        {scenes.map((scene) => {
          const cfg = STATUS_CONFIG[scene.status];
          const isActive = scene.scene_id === activeSceneId;
          return (
            <button
              key={scene.scene_id}
              onClick={() => setActiveSceneId(scene.scene_id)}
              className={`flex items-center gap-2 px-3 py-2 rounded border
                text-left text-xs transition-colors
                ${isActive ? "ring-1 ring-blue-500" : ""}
                ${cfg.bg}`}
            >
              <span>{cfg.emoji}</span>
              <span className="flex-1">
                <span className="font-medium">
                  Cảnh {scene.scene_id + 1}
                </span>
                <span className="text-gray-500 ml-2">
                  {scene.duration_sec.toFixed(1)}s • {scene.frame_count} frame
                </span>
              </span>
              <span className={`${cfg.color} text-[10px]`}>
                {cfg.label}
              </span>
              {scene.status !== "approved" && isActive && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    approveMut.mutate(scene.scene_id);
                  }}
                  className="px-2 py-0.5 bg-green-700 hover:bg-green-600
                    rounded text-[10px] text-white"
                >
                  ✅ Duyệt
                </button>
              )}
            </button>
          );
        })}
      </div>

      {allApproved && (
        <div className="mt-2 p-2 bg-green-900/30 border border-green-700 rounded">
          <p className="text-xs text-green-300 text-center">
            ✅ Tất cả cảnh đã duyệt! Sẵn sàng ghép video.
          </p>
        </div>
      )}
    </div>
  );
}
