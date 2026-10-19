"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type ChannelProject } from "@/lib/api";
import { useProjectStore } from "@/stores/project";

const STATUS_CONFIG: Record<
  ChannelProject["task_status"],
  { label: string; emoji: string; color: string; bg: string }
> = {
  draft: {
    label: "Bản Nháp",
    emoji: "⚪",
    color: "text-gray-400",
    bg: "bg-gray-800/50 border-gray-700",
  },
  in_progress: {
    label: "Đang Xử Lý",
    emoji: "🟡",
    color: "text-yellow-300",
    bg: "bg-yellow-900/30 border-yellow-700",
  },
  ready_to_stitch: {
    label: "Sẵn sàng ghép",
    emoji: "🔵",
    color: "text-blue-300",
    bg: "bg-blue-900/30 border-blue-700",
  },
  completed: {
    label: "Hoàn thành",
    emoji: "🟢",
    color: "text-green-300",
    bg: "bg-green-900/30 border-green-700",
  },
};

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onResumeProject: (projectId: string) => void;
}

export function ChannelDashboard({ isOpen, onClose, onResumeProject }: Props) {
  const queryClient = useQueryClient();
  const activeChannelId = useProjectStore((s) => s.activeChannelId);
  const setActiveChannelId = useProjectStore((s) => s.setActiveChannelId);

  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newLang, setNewLang] = useState("en");

  // Channels query
  const { data: channels = [] } = useQuery({
    queryKey: ["channels"],
    queryFn: () => api.listChannels(),
    enabled: isOpen,
  });

  // Projects for selected channel
  const { data: projects = [] } = useQuery({
    queryKey: ["channel-projects", activeChannelId],
    queryFn: () => api.getChannelProjects(activeChannelId!),
    enabled: !!activeChannelId && isOpen,
  });

  // Create channel mutation
  const createMut = useMutation({
    mutationFn: () => api.createChannel(newName, newLang),
    onSuccess: (ch) => {
      queryClient.invalidateQueries({ queryKey: ["channels"] });
      setActiveChannelId(ch.channel_id);
      setNewName("");
      setShowCreate(false);
    },
  });

  // Delete channel mutation
  const deleteMut = useMutation({
    mutationFn: (channelId: string) => api.deleteChannel(channelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["channels"] });
      setActiveChannelId(null);
    },
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex bg-black/70 backdrop-blur-sm">
      <div className="flex w-full max-w-6xl mx-auto my-4 bg-gray-950 border border-gray-800 rounded-2xl overflow-hidden">
        {/* Sidebar: Channel list */}
        <div className="w-64 border-r border-gray-800 p-4 flex flex-col">
          <h3 className="text-sm font-bold text-gray-300 mb-4">
            📺 Kênh Mục Tiêu
          </h3>

          <div className="flex-1 space-y-1 overflow-y-auto">
            {channels.map((ch) => (
              <button
                key={ch.channel_id}
                onClick={() => setActiveChannelId(ch.channel_id)}
                className={`w-full text-left px-3 py-2 rounded text-xs transition-colors ${
                  activeChannelId === ch.channel_id
                    ? "bg-blue-600/30 text-blue-300 ring-1 ring-blue-500"
                    : "text-gray-400 hover:bg-gray-800"
                }`}
              >
                <div className="font-medium">{ch.name}</div>
                <div className="text-[10px] text-gray-500">
                  {ch.target_lang.toUpperCase()}
                </div>
              </button>
            ))}
          </div>

          {/* Create channel */}
          {!showCreate ? (
            <button
              onClick={() => setShowCreate(true)}
              className="w-full py-2 text-xs bg-blue-600 hover:bg-blue-500 rounded mt-2"
            >
              + Tạo Kênh Mới
            </button>
          ) : (
            <div className="space-y-2 mt-2">
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Tên kênh..."
                className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs"
              />
              <select
                value={newLang}
                onChange={(e) => setNewLang(e.target.value)}
                className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs"
              >
                <option value="en">English</option>
                <option value="es">Español</option>
                <option value="fr">Français</option>
                <option value="de">Deutsch</option>
                <option value="ja">日本語</option>
                <option value="ko">한국어</option>
                <option value="zh">中文</option>
              </select>
              <div className="flex gap-2">
                <button
                  onClick={() => createMut.mutate()}
                  disabled={!newName || createMut.isPending}
                  className="flex-1 py-1 bg-green-600 rounded text-xs disabled:bg-gray-700"
                >
                  Tạo
                </button>
                <button
                  onClick={() => setShowCreate(false)}
                  className="px-2 py-1 bg-gray-700 rounded text-xs"
                >
                  ✕
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Main: Project grid */}
        <div className="flex-1 p-6 overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold">
              {activeChannelId
                ? channels.find((c) => c.channel_id === activeChannelId)?.name ?? "Kênh"
                : "Chọn một kênh"}
            </h2>
            <div className="flex gap-2">
              {activeChannelId && (
                <button
                  onClick={() => deleteMut.mutate(activeChannelId)}
                  className="px-3 py-1 text-xs bg-red-900/50 hover:bg-red-800 rounded"
                >
                  🗑 Xóa kênh
                </button>
              )}
              <button
                onClick={onClose}
                className="px-3 py-1 text-xs bg-gray-800 hover:bg-gray-700 rounded"
              >
                Đóng
              </button>
            </div>
          </div>

          {!activeChannelId && (
            <p className="text-gray-500 text-sm text-center mt-20">
              Chọn một kênh ở bên trái hoặc tạo kênh mới
            </p>
          )}

          {activeChannelId && projects.length === 0 && (
            <p className="text-gray-500 text-sm text-center mt-20">
              Chưa có dự án nào trong kênh này.
              <br />
              Tạo dự án mới từ màn hình chính và gán vào kênh.
            </p>
          )}

          {activeChannelId && projects.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {projects.map((proj) => {
                const cfg = STATUS_CONFIG[proj.task_status];
                return (
                  <div
                    key={proj.project_id}
                    className={`p-4 rounded-xl border ${cfg.bg} space-y-2`}
                  >
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-medium text-gray-200 truncate">
                        {proj.name}
                      </h4>
                      <span className="text-[10px]">
                        {cfg.emoji}{" "}
                        <span className={cfg.color}>{cfg.label}</span>
                      </span>
                    </div>

                    <div className="text-xs text-gray-500">
                      {proj.scene_count} cảnh • {proj.object_count} vật thể
                    </div>

                    <div className="w-full bg-gray-800 rounded-full h-1.5">
                      <div
                        className="h-1.5 rounded-full bg-blue-500"
                        style={{
                          width:
                            proj.task_status === "completed"
                              ? "100%"
                              : proj.task_status === "ready_to_stitch"
                                ? "80%"
                                : proj.task_status === "in_progress"
                                  ? "50%"
                                  : "10%",
                        }}
                      />
                    </div>

                    <button
                      onClick={() => {
                        onResumeProject(proj.project_id);
                        onClose();
                      }}
                      className="w-full py-1.5 text-xs bg-blue-600 hover:bg-blue-500 rounded transition-colors"
                    >
                      ▶️ Tiếp tục làm việc
                    </button>

                    <button
                      onClick={async () => {
                        if (!confirm(`Xóa dự án "${proj.name}"?`)) return;
                        await api.deleteProject(proj.project_id);
                        queryClient.invalidateQueries({ queryKey: ["channel-projects", activeChannelId] });
                      }}
                      className="px-2 py-1 text-[10px] bg-red-900/50 hover:bg-red-800 rounded text-red-300"
                    >
                      🗑️
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
