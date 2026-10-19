"use client";

import { useRef, useEffect } from "react";
import { useProjectStore } from "@/stores/project";
import { api } from "@/lib/api";

export function ScenePreview() {
  const projectId = useProjectStore((s) => s.projectId);
  const activeSceneId = useProjectStore((s) => s.activeSceneId);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    if (projectId !== null && activeSceneId !== null && audioRef.current) {
      audioRef.current.src = api.getSceneAudioUrl(projectId, activeSceneId);
      audioRef.current.load();
    }
  }, [projectId, activeSceneId]);

  if (activeSceneId === null) {
    return (
      <div className="flex items-center justify-center h-32
        bg-gray-900 rounded text-gray-500 text-sm">
        Chọn một phân cảnh để preview
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2 p-3 bg-gray-900 rounded">
      <h4 className="text-sm font-medium text-gray-300">
        🎧 Preview Cảnh {activeSceneId + 1}
      </h4>
      <audio
        ref={audioRef}
        controls
        className="w-full h-8"
        preload="metadata"
      >
        Trình duyệt không hỗ trợ audio
      </audio>
      <p className="text-[10px] text-gray-500">
        Nghe giọng nói gốc để kiểm tra đồng bộ trước khi duyệt
      </p>
    </div>
  );
}
