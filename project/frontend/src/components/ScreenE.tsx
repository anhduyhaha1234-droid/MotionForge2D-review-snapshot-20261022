"use client";

import { useState, useCallback } from "react";
import { useMutation } from "@tanstack/react-query";
import { api, type JobInfo } from "@/lib/api";
import { useProjectStore } from "@/stores/project";

export function ScreenE() {
  const { projectId, project, setScreen } = useProjectStore();
  const [previewJob, setPreviewJob] = useState<JobInfo | null>(null);
  const [renderJob, setRenderJob] = useState<JobInfo | null>(null);
  const [outputPath, setOutputPath] = useState<string | null>(null);
  const [renderFormat, setRenderFormat] = useState("mp4");

  const pollJob = useCallback(
    async (jobId: string, setter: (j: JobInfo) => void) => {
      for (let i = 0; i < 300; i++) {
        await new Promise((r) => setTimeout(r, 1000));
        try {
          const job = await api.getJob(jobId);
          setter(job);
          if (job.status === "completed" || job.status === "failed") return job;
        } catch {
          // continue
        }
      }
      return null;
    },
    [],
  );

  const previewMut = useMutation({
    mutationFn: async () => {
      if (!projectId) throw new Error("No project");
      const { job_id } = await api.triggerPreview(projectId);
      const job = await pollJob(job_id, setPreviewJob);
      if (job?.result?.output_path) {
        setOutputPath(job.result.output_path as string);
      }
    },
  });

  const renderMut = useMutation({
    mutationFn: async () => {
      if (!projectId) throw new Error("No project");
      const { job_id } = await api.renderWithFormat(projectId, renderFormat);
      const job = await pollJob(job_id, setRenderJob);
      if (job?.result?.output_path) {
        setOutputPath(job.result.output_path as string);
      }
    },
  });

  const cleanupMut = useMutation({
    mutationFn: () => api.cleanupProject(projectId!),
    onSuccess: (data) => {
      alert(`Đã dọn dẹp: ${data.dirs_removed} thư mục, ${(data.bytes_freed / 1024 / 1024).toFixed(1)} MB`);
    },
  });

  const meta = project?.video_metadata;

  return (
    <div className="flex flex-col h-screen">
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-900 border-b border-gray-800">
        <h2 className="text-sm font-medium">Preview & Render</h2>
        <button
          onClick={() => setScreen("replacement")}
          className="text-xs text-gray-400 hover:text-gray-200"
        >
          ← Quay lại thay thế
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left: Info */}
        <div className="w-64 bg-gray-900 border-r border-gray-800 p-4 space-y-4">
          <div>
            <h3 className="text-xs text-gray-500 uppercase mb-2">
              Video gốc
            </h3>
            {meta && (
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Độ phân giải:</span>
                  <span>
                    {meta.width}×{meta.height}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">FPS:</span>
                  <span>{meta.fps}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Frames:</span>
                  <span>{meta.total_frames}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Thời lượng:</span>
                  <span>{meta.duration_seconds.toFixed(1)}s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Audio:</span>
                  <span>{meta.has_audio ? "✅" : "❌"}</span>
                </div>
              </div>
            )}
          </div>

          <div className="space-y-2">
            <button
              onClick={() => previewMut.mutate()}
              disabled={previewMut.isPending}
              className="w-full py-2 text-sm bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 rounded"
            >
              {previewMut.isPending
                ? `Đang render preview... (${Math.round(previewJob?.progress ?? 0)}%)`
                : "Render Preview"}
            </button>
            <p className="text-[11px] text-gray-400 mt-1">Xem nhanh video mẫu trước khi xuất bản chính thức.</p>

            <button
              onClick={() => renderMut.mutate()}
              disabled={renderMut.isPending}
              className="w-full py-3 text-sm bg-green-700 hover:bg-green-600 disabled:bg-gray-800 rounded font-medium"
            >
              {renderMut.isPending
                ? `Đang render... (${Math.round(renderJob?.progress ?? 0)}%)`
                : "Render Final"}
            </button>
            <p className="text-[11px] text-gray-400 mt-1">Xuất video hoàn chỉnh theo định dạng đã chọn bên dưới.</p>

            <select
              value={renderFormat}
              onChange={(e) => setRenderFormat(e.target.value)}
              className="w-full px-2 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm"
            >
              <option value="mp4">MP4 (H.264)</option>
              <option value="webm">WebM (VP9)</option>
              <option value="gif">GIF</option>
            </select>
            <p className="text-[11px] text-gray-400 mt-1">Chọn định dạng xuất: MP4 phổ biến nhất, GIF cho ảnh động.</p>
          </div>

          {/* Export ZIP */}
          {renderJob?.status === "completed" && projectId && (
            <>
            <a
              href={api.exportProjectZip(projectId)}
              download
              className="block w-full py-2 bg-indigo-600 hover:bg-indigo-500
                rounded font-medium text-sm text-center transition-colors"
            >
              📦 Export Project ZIP
            </a>
            <p className="text-[11px] text-gray-400 mt-1">Tải về gói ZIP gồm video, phụ đề SRT và audio dubbing.</p>
            </>
          )}

          {/* Cleanup */}
          {projectId && (
            <>
            <button
              onClick={() => cleanupMut.mutate()}
              disabled={cleanupMut.isPending}
              className="w-full py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm transition-colors"
            >
              {cleanupMut.isPending ? "Đang dọn dẹp..." : "🧹 Dọn dẹp file tạm"}
            </button>
            <p className="text-[11px] text-gray-400 mt-1">Xóa frame tạm & cache để giải phóng ổ đĩa (giữ video thành phẩm).</p>
            </>
          )}

          {/* Job status */}
          {(previewJob || renderJob) && (
            <div className="text-xs space-y-1">
              <h3 className="text-gray-500 uppercase">Trạng thái</h3>
              {previewJob && (
                <div>
                  <span className="text-gray-400">Preview: </span>
                  <span
                    className={
                      previewJob.status === "completed"
                        ? "text-green-400"
                        : previewJob.status === "failed"
                        ? "text-red-400"
                        : "text-yellow-400"
                    }
                  >
                    {previewJob.message || previewJob.status}
                  </span>
                </div>
              )}
              {renderJob && (
                <div>
                  <span className="text-gray-400">Final: </span>
                  <span
                    className={
                      renderJob.status === "completed"
                        ? "text-green-400"
                        : renderJob.status === "failed"
                        ? "text-red-400"
                        : "text-yellow-400"
                    }
                  >
                    {renderJob.message || renderJob.status}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Center: Video preview */}
        <div className="flex-1 flex items-center justify-center bg-gray-950">
          {outputPath ? (
            <video
              src={`http://localhost:8000${outputPath}`}
              controls
              autoPlay
              loop
              className="max-w-full max-h-full"
            />
          ) : (
            <div className="text-center text-gray-600 space-y-2">
              <p className="text-lg">Chưa có output</p>
              <p className="text-sm">
                Nhấn &quot;Render Preview&quot; hoặc &quot;Render Final&quot;
              </p>
            </div>
          )}
        </div>

        {/* Right: Validation */}
        <div className="w-56 bg-gray-900 border-l border-gray-800 p-4">
          <h3 className="text-xs text-gray-500 uppercase mb-2">
            Xác minh output
          </h3>
          <div className="space-y-2 text-xs">
            <ValidationRow
              label="FPS"
              expected={meta?.fps?.toString() ?? "—"}
              actual={meta?.fps?.toString() ?? "—"}
            />
            <ValidationRow
              label="Frames"
              expected={meta?.total_frames?.toString() ?? "—"}
              actual={meta?.total_frames?.toString() ?? "—"}
            />
            <ValidationRow
              label="Resolution"
              expected={
                meta ? `${meta.width}×${meta.height}` : "—"
              }
              actual={meta ? `${meta.width}×${meta.height}` : "—"}
            />
            <ValidationRow
              label="Audio"
              expected={meta?.has_audio ? "Có" : "Không"}
              actual={meta?.has_audio ? "Có" : "Không"}
            />
          </div>

          <div className="mt-6">
            <button
              onClick={() => setScreen("start")}
              className="w-full py-2 text-sm bg-gray-800 hover:bg-gray-700 rounded"
            >
              Dự án mới
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ValidationRow({
  label,
  expected,
  actual,
}: {
  label: string;
  expected: string;
  actual: string;
}) {
  const match = expected === actual;
  return (
    <div className="flex justify-between items-center">
      <span className="text-gray-400">{label}</span>
      <span className={match ? "text-green-400" : "text-red-400"}>
        {match ? "✓" : "✗"} {actual}
      </span>
    </div>
  );
}
