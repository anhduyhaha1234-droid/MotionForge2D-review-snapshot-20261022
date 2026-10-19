"use client";

import { useCallback, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, type ProjectSummary } from "@/lib/api";
import { useProjectStore } from "@/stores/project";
import { PresetManager } from "@/components/PresetManager";
import {
  Film,
  Upload,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  FolderOpen,
  Layers,
  Wand2,
  Play,
  Clock,
  Clapperboard,
} from "lucide-react";

export function ScreenA() {
  const { projectId, setProjectId, setProject, setScreen, setScenes } = useProjectStore();
  const [projectName, setProjectName] = useState("Dự án MotionForge 01");
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progressPercent, setProgressPercent] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showHelp, setShowHelp] = useState(false);

  // Recent projects query
  const { data: recentProjects = [], refetch: refetchProjects } = useQuery({
    queryKey: ["recent-projects"],
    queryFn: () => api.listAllProjects(),
    staleTime: 5000,
  });

  // File Selection
  const handleFileSelect = (file: File | null) => {
    if (!file) return;
    if (!file.name.match(/\.(mp4|mov|avi|mkv)$/i)) {
      setErrorMessage("Vui lòng chọn file video đúng định dạng MP4.");
      return;
    }
    setVideoFile(file);
    setErrorMessage(null);
  };

  // Drag & Drop Handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  // Resume Existing Project Handler
  const handleResumeProject = async (projId: string) => {
    try {
      setIsProcessing(true);
      setStatusMessage("Đang tải dữ liệu dự án...");
      setProjectId(projId);

      const projData = await api.getProject(projId);
      setProject(projData);

      const sceneDetails = await api.getSceneDetails(projId);
      setScenes(sceneDetails);

      // Determine appropriate screen
      if (sceneDetails.length > 0) {
        setScreen("selection");
      } else {
        setScreen("start");
      }
    } catch (err) {
      setErrorMessage(`Không thể mở lại dự án: ${(err as Error).message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  // Main Workflow Async Handler
  const handleStartWorkflow = useCallback(async () => {
    if (!videoFile) return;

    setIsProcessing(true);
    setErrorMessage(null);
    setProgressPercent(10);
    setStatusMessage("Đang tạo dự án mới...");

    try {
      // Step 1: Create Project
      const projRes = await api.createProject(projectName);
      const newProjId = projRes.project_id;
      setProjectId(newProjId);
      setProgressPercent(30);

      // Step 2: Upload Video
      setStatusMessage("Đang tải video lên hệ thống...");
      await api.uploadVideo(newProjId, videoFile);
      setProgressPercent(50);

      // Step 3: Trigger Ingest & Scene Chunking
      setStatusMessage("Đang khởi chạy AI bóc tách phân cảnh & âm thanh...");
      const ingestRes = await api.triggerIngest(newProjId);
      setProgressPercent(60);

      // Step 4: Poll Job Status until Completion
      const maxAttempts = 1000;
      for (let i = 0; i < maxAttempts; i++) {
        await new Promise((r) => setTimeout(r, 300));
        const job = await api.getJob(ingestRes.job_id);

        const currentProg = 60 + Math.round((job.progress || 0) * 0.35);
        setProgressPercent(Math.min(currentProg, 95));
        setStatusMessage(job.message || "Đang phân tích video...");

        if (job.status === "completed") {
          setProgressPercent(100);
          setStatusMessage("Phân tích hoàn tất! Đang chuyển sang bước tiếp theo...");
          const updatedProj = await api.getProject(newProjId);
          setProject(updatedProj);
          const sceneDetails = await api.getSceneDetails(newProjId);
          setScenes(sceneDetails);
          await api.updateTaskStatus(newProjId, "in_progress");
          refetchProjects();
          setTimeout(() => setScreen("selection"), 600);
          return;
        }

        if (job.status === "failed") {
          throw new Error(job.message || "Quá trình phân tích video bị thất bại.");
        }
      }

      throw new Error("Quá trình xử lý bị quá thời gian. Vui lòng thử lại.");
    } catch (err) {
      setErrorMessage((err as Error).message || "Đã xảy ra lỗi không xác định.");
      setIsProcessing(false);
    }
  }, [videoFile, projectName, setProjectId, setProject, setScenes, setScreen, refetchProjects]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between p-4 sm:p-8">
      {/* Header Bar */}
      <header className="max-w-5xl w-full mx-auto flex items-center justify-between py-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-purple-600 flex items-center justify-center shadow-lg shadow-purple-900/40">
            <Film className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">
              MotionForge 2D
            </h1>
            <p className="text-xs text-slate-400">
              Nền tảng Tái tạo & Lồng tiếng Video Hoạt hình 2D Đa Ngôn Ngữ
            </p>
          </div>
        </div>

        {/* Step Indicator */}
        <div className="hidden md:flex items-center gap-2 text-xs text-slate-400 bg-slate-900/80 px-4 py-2 rounded-full border border-slate-800">
          <span className="font-semibold text-blue-400">Bước 1: Khởi Tạo Dự Án</span>
          <span>➔</span>
          <span>Chọn Nhân Vật</span>
          <span>➔</span>
          <span>Thay Thế & Lồng Tiếng</span>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-5xl w-full mx-auto my-8 space-y-8">
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6 shadow-2xl backdrop-blur-sm">
          {/* Top Explanatory Header */}
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-blue-400" /> Tải Lên Video Hoạt Hình Đối Thủ
              </h2>
              <p className="text-xs text-slate-400">
                Nhập tên dự án và chọn file video MP4 dài để AI tự động bóc tách phân cảnh & âm thanh
              </p>
            </div>
            <button
              onClick={() => setShowHelp(!showHelp)}
              className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 font-medium bg-blue-950/40 hover:bg-blue-900/40 px-3 py-1.5 rounded-lg border border-blue-800/40 transition-colors"
            >
              <HelpCircle className="w-3.5 h-3.5" /> {showHelp ? "Ẩn Hướng Dẫn" : "Hướng Dẫn Nút Bấm"}
            </button>
          </div>

          {/* Project Name Input */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Tên Dự Án Mục Tiêu:
            </label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              disabled={isProcessing}
              placeholder="VD: Dự án Hoạt Hình Kênh 1..."
              className="w-full bg-slate-950 border border-slate-800 focus:border-blue-500 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-600 focus:outline-none transition-colors"
            />
          </div>

          {/* Video Dropzone */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              File Video Đối Thủ (MP4):
            </label>
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${
                isDragging
                  ? "border-blue-500 bg-blue-950/20"
                  : videoFile
                  ? "border-emerald-500/50 bg-emerald-950/10"
                  : "border-slate-800 hover:border-slate-700 bg-slate-950/40"
              }`}
              onClick={() => {
                const el = document.getElementById("video-input-file");
                if (el) el.click();
              }}
            >
              <input
                id="video-input-file"
                type="file"
                accept="video/mp4,video/quicktime,video/x-msvideo"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleFileSelect(e.target.files[0]);
                  }
                }}
                className="hidden"
              />

              {videoFile ? (
                <div className="flex flex-col items-center gap-2">
                  <div className="w-12 h-12 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
                    <CheckCircle2 className="w-6 h-6" />
                  </div>
                  <p className="text-sm font-semibold text-emerald-300">
                    {videoFile.name}
                  </p>
                  <p className="text-xs text-slate-400">
                    {(videoFile.size / (1024 * 1024)).toFixed(1)} MB • Bấm để chọn file khác
                  </p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-400">
                    <Upload className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-200">
                      Kéo & thả file video MP4 vào đây
                    </p>
                    <p className="text-xs text-slate-400 mt-1">
                      Hoặc <span className="text-blue-400 font-semibold underline">duyệt tìm file</span> từ máy tính của bạn
                    </p>
                  </div>
                  <div className="flex items-center gap-3 text-[11px] text-slate-500">
                    <span>Hỗ trợ: MP4, MOV, AVI</span>
                    <span>•</span>
                    <span>Tốc độ tối ưu trên GPU RTX</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Help Explanation Card */}
          {showHelp && (
            <div className="bg-blue-950/40 border border-blue-800/40 rounded-xl p-4 text-xs space-y-2 text-blue-200">
              <h4 className="font-semibold text-blue-300 flex items-center gap-1.5 text-sm">
                <HelpCircle className="w-4 h-4" /> Hướng dẫn chức năng từng nút bấm:
              </h4>
              <ul className="space-y-1.5 list-disc list-inside text-slate-300">
                <li>
                  <strong className="text-blue-400">Nút &quot;Bắt đầu Phân tích&quot;</strong>: Tự động cắt clip MP4 từng phân cảnh siêu tốc.
                </li>
                <li>
                  <strong className="text-blue-400">Nút &quot;▶️ Tiếp Tục&quot; ở danh sách bên dưới</strong>: Mở lại dự án cũ dở dang để làm tiếp.
                </li>
              </ul>
            </div>
          )}

          {/* Error Banner */}
          {errorMessage && (
            <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 flex items-start gap-3 text-rose-300 text-xs">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <p className="font-semibold text-rose-200">Không thể thực hiện:</p>
                <p className="text-slate-300">{errorMessage}</p>
              </div>
            </div>
          )}

          {/* Progress Bar Area */}
          {isProcessing && (
            <div className="space-y-2 bg-slate-950/60 border border-slate-800 p-4 rounded-xl">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-blue-400 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-blue-500 animate-ping" />
                  {statusMessage}
                </span>
                <span className="font-bold text-slate-200">{progressPercent}%</span>
              </div>
              <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden p-0.5">
                <div
                  className="h-full bg-gradient-to-r from-blue-600 via-indigo-500 to-purple-500 rounded-full transition-all duration-300 shadow-sm shadow-blue-500/50"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>
          )}

          {/* Action Button */}
          <button
            type="button"
            onClick={handleStartWorkflow}
            disabled={!videoFile || isProcessing}
            className="w-full py-4 px-6 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold rounded-xl shadow-lg shadow-blue-600/25 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none transition-all flex items-center justify-center gap-2 text-sm uppercase tracking-wider"
          >
            {isProcessing ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Đang xử lý phân tích...
              </>
            ) : (
              <>
                <Wand2 className="w-4 h-4" /> Bắt Đầu Phân Tích Video
              </>
            )}
          </button>
        </div>

        {/* Recent Projects Section */}
        {recentProjects.length > 0 && (
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <FolderOpen className="w-5 h-5 text-purple-400" /> Danh Sách Dự Án Đã Làm ({recentProjects.length})
              </h3>
              <span className="text-xs text-slate-400">
                Bấm nút &quot;▶️ Tiếp tục&quot; để mở lại dự án dở dang
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-96 overflow-y-auto pr-1">
              {recentProjects.map((p: ProjectSummary) => (
                <div
                  key={p.project_id}
                  className="bg-slate-950/80 border border-slate-800 hover:border-purple-500/50 rounded-xl p-4 flex flex-col justify-between gap-3 transition-all group"
                >
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono text-purple-400 bg-purple-950/60 px-2 py-0.5 rounded border border-purple-800/40">
                        ID: {p.project_id}
                      </span>
                      <span className="text-[11px] text-slate-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {p.updated_at ? new Date(p.updated_at).toLocaleTimeString("vi-VN") : "Gần đây"}
                      </span>
                    </div>
                    <h4 className="text-sm font-bold text-slate-100 truncate group-hover:text-purple-300 transition-colors">
                      {p.name || "Dự án MotionForge"}
                    </h4>
                    <p className="text-xs text-slate-400 flex items-center gap-1.5">
                      <Clapperboard className="w-3.5 h-3.5 text-blue-400" />
                      {p.scenes_count} Phân Cảnh Bóc Tách
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleResumeProject(p.project_id)}
                    className="w-full py-2.5 px-4 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold rounded-lg text-xs transition-all flex items-center justify-center gap-2 shadow-md shadow-purple-600/20"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" /> Mở Lại Dự Án Đang Làm
                  </button>

                  <button
                    onClick={async () => {
                      if (!confirm(`Xóa dự án "${p.name}"? Toàn bộ dữ liệu sẽ bị xóa vĩnh viễn.`)) return;
                      try {
                        await api.deleteProject(p.project_id);
                        refetchProjects();
                      } catch (err) {
                        alert(`Lỗi: ${(err as Error).message}`);
                      }
                    }}
                    className="ml-1 px-2 py-1.5 text-xs bg-red-900/50 hover:bg-red-800 rounded transition-colors text-red-300"
                    title="Xóa dự án"
                  >
                    🗑️
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Preset Manager Integration */}
        {projectId && (
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 shadow-lg">
            <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
              <Layers className="w-4 h-4 text-purple-400" /> Quản Lý 1-Click Preset Cấu Hình
            </h3>
            <PresetManager />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="text-center text-xs text-slate-600 py-4 border-t border-slate-900">
        MotionForge 2D Platform • 100% Local GPU Processing • Local-First Execution
      </footer>
    </div>
  );
}
