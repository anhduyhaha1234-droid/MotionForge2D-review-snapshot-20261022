"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api, type SceneDetail } from "@/lib/api";
import { useProjectStore } from "@/stores/project";
import { Film, CheckCircle2, AlertCircle, X, Clapperboard, HelpCircle } from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

const STATUS_LABEL: Record<SceneDetail["status"], { text: string; bg: string; color: string }> = {
  approved: { text: "🟢 Đã duyệt", bg: "bg-emerald-500/10 border-emerald-500/30", color: "text-emerald-400" },
  draft: { text: "🟡 Đang chỉnh sửa", bg: "bg-amber-500/10 border-amber-500/30", color: "text-amber-400" },
  pending: { text: "⚪ Chưa xử lý", bg: "bg-slate-800/80 border-slate-700", color: "text-slate-400" },
};

export function AssemblyModal({ isOpen, onClose }: Props) {
  const projectId = useProjectStore((s) => s.projectId);
  const [resultPath, setResultPath] = useState<string | null>(null);

  const { data: scenes = [] } = useQuery({
    queryKey: ["scenes", projectId],
    queryFn: () => api.getSceneDetails(projectId!),
    enabled: !!projectId && isOpen,
  });

  const stitchMut = useMutation({
    mutationFn: () => api.stitchScenes(projectId!),
    onSuccess: (data) => {
      setResultPath(data.output_path);
    },
  });

  if (!isOpen) return null;

  const approvedCount = scenes.filter((s) => s.status === "approved").length;
  const allApproved = scenes.length > 0 && approvedCount === scenes.length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6 shadow-2xl shadow-purple-950/50 text-slate-100 relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white rounded-full hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
          <div className="w-10 h-10 rounded-xl bg-purple-600/20 border border-purple-500/30 text-purple-400 flex items-center justify-center">
            <Clapperboard className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">
              🎬 Bảng Tổng Hợp & Ghép Video Thành Phẩm
            </h2>
            <p className="text-xs text-slate-400">
              Kiểm tra trạng thái duyệt từng cảnh trước khi nối video hoàn chỉnh
            </p>
          </div>
        </div>

        {/* Scene List or Empty Info */}
        {scenes.length === 0 ? (
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-6 text-center space-y-2">
            <HelpCircle className="w-8 h-8 text-slate-500 mx-auto" />
            <p className="text-sm font-semibold text-slate-300">
              Chưa có phân cảnh nào trong dự án
            </p>
            <p className="text-xs text-slate-400">
              Vui lòng tải video lên và thực hiện bóc tách phân cảnh trước khi truy cập bảng ghép video.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs font-semibold uppercase text-slate-400 px-1">
              <span>Danh sách phân cảnh ({scenes.length})</span>
              <span className="text-purple-400">
                Đã duyệt: {approvedCount}/{scenes.length} Cảnh
              </span>
            </div>

            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {scenes.map((scene) => {
                const statusInfo = STATUS_LABEL[scene.status] || STATUS_LABEL.pending;
                return (
                  <div
                    key={scene.scene_id}
                    className={`flex items-center justify-between px-4 py-3 border rounded-xl text-xs font-medium transition-all ${statusInfo.bg}`}
                  >
                    <span className="text-slate-200 font-semibold">
                      Cảnh #{scene.scene_id + 1} ({scene.duration_sec.toFixed(1)}s)
                    </span>
                    <span className={`font-bold ${statusInfo.color}`}>
                      {statusInfo.text}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Instructions */}
        <div className="bg-purple-950/20 border border-purple-800/30 rounded-xl p-3 text-xs text-purple-200 space-y-1">
          <p className="font-semibold text-purple-300">💡 Hướng dẫn nút ghép video:</p>
          <p className="text-slate-300">
            Nút <strong className="text-emerald-400">&quot;Đồng ý ghép Video hoàn chỉnh&quot;</strong> chỉ sáng khi bạn đã bấm <strong className="text-emerald-400">&quot;Duyệt Cảnh&quot;</strong> cho 100% các phân cảnh trên giao diện.
          </p>
        </div>

        {/* Result Success Banner */}
        {resultPath && (
          <div className="p-4 bg-emerald-950/40 border border-emerald-500/40 rounded-xl space-y-2 text-xs">
            <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
              <CheckCircle2 className="w-5 h-5" /> Video đã ghép hoàn chỉnh thành công!
            </div>
            <p className="text-slate-300 break-all bg-slate-950/60 p-2 rounded border border-slate-800 font-mono">
              {resultPath}
            </p>
          </div>
        )}

        {/* Error Banner */}
        {stitchMut.isError && (
          <div className="p-4 bg-rose-950/40 border border-rose-500/40 rounded-xl flex items-start gap-3 text-xs text-rose-200">
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-rose-300">Không thể ghép video:</p>
              <p className="text-slate-300">{(stitchMut.error as Error).message}</p>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center gap-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 py-3 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-xl text-xs transition-colors"
          >
            Đóng Bảng
          </button>
          <button
            type="button"
            onClick={() => stitchMut.mutate()}
            disabled={!allApproved || stitchMut.isPending}
            className="flex-1 py-3 px-4 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold rounded-xl text-xs shadow-lg shadow-emerald-600/20 transition-all flex items-center justify-center gap-2"
          >
            {stitchMut.isPending ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Đang ghép video...
              </>
            ) : (
              <>
                <Film className="w-4 h-4" /> Đồng Ý Ghép Video Hoàn Chỉnh
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
