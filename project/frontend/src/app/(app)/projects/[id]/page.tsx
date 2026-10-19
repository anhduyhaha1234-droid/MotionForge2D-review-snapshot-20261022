"use client";

import React, { useCallback, useEffect, useMemo, useState, use } from "react";
import Link from "next/link";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  Archive,
  ArrowDown,
  ArrowUp,
  CheckCircle2,
  Pencil,
  Plus,
  RefreshCw,
  X,
} from "lucide-react";
import {
  api,
  isUuid,
  patchDurableProject,
  patchDurableVideo,
  type DurableProjectData,
  type DurableVideoItem,
} from "@/lib/api";
import { useProjectStore } from "@/stores/project";

function formatDuration(durationMs: number | null | undefined): string {
  if (durationMs === null || durationMs === undefined) return "N/A";
  const seconds = durationMs / 1000;
  return seconds >= 60 ? `${(seconds / 60).toFixed(1)} phút` : `${seconds.toFixed(1)}s`;
}

function errDetail(err: unknown): string {
  if (err instanceof Error) return err.message;
  return String(err);
}

function isConflict(err: unknown): boolean {
  return err instanceof Error && /^API 409/.test(err.message);
}

const VIDEO_STATUS_BADGE: Record<string, { label: string; className: string }> = {
  imported: { label: "Đã nhập", className: "bg-zinc-500/10 text-zinc-400 border border-zinc-500/20" },
  analyzing: { label: "Đang phân tích", className: "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20" },
  objects_ready: { label: "Sẵn sàng đối tượng", className: "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20" },
  mapping_required: { label: "Cần ánh xạ", className: "bg-amber-500/10 text-amber-400 border border-amber-500/20" },
  demo_required: { label: "Cần demo", className: "bg-amber-500/10 text-amber-400 border border-amber-500/20" },
  demo_approved: { label: "Demo đã duyệt", className: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" },
  applying_reskin: { label: "Đang áp dụng", className: "bg-purple-500/10 text-purple-400 border border-purple-500/20" },
  needs_review: { label: "Cần kiểm tra", className: "bg-amber-500/10 text-amber-400 border border-amber-500/20" },
  ready_to_export: { label: "Sẵn sàng xuất", className: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" },
  rendering: { label: "Đang xuất", className: "bg-purple-500/10 text-purple-400 border border-purple-500/20" },
  completed: { label: "Hoàn tất", className: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" },
  failed: { label: "Lỗi", className: "bg-red-500/10 text-red-400 border border-red-500/20" },
  archived: { label: "Đã lưu trữ", className: "bg-zinc-500/10 text-zinc-400 border border-zinc-500/20" },
};

const PROJECT_STATUS_BADGE: Record<string, { label: string; className: string }> = {
  draft: { label: "Bản nháp", className: "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20" },
  active: { label: "Đang hoạt động", className: "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20" },
  needs_review: { label: "Cần xem lại", className: "bg-amber-500/10 text-amber-400 border border-amber-500/20" },
  rendering: { label: "Đang xuất", className: "bg-purple-500/10 text-purple-400 border border-purple-500/20" },
  completed: { label: "Hoàn tất", className: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" },
  archived: { label: "Đã lưu trữ", className: "bg-zinc-500/10 text-zinc-400 border border-zinc-500/20" },
};

export default function ProjectDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const projectId = resolvedParams.id;
  const isDurable = isUuid(projectId);
  const setDurableRevision = useProjectStore((s) => s.setDurableRevision);
  const setResumeStep = useProjectStore((s) => s.setResumeStep);

  const [project, setProject] = useState<DurableProjectData | null>(null);
  const [videoItems, setVideoItems] = useState<DurableVideoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Add Video Item form
  const [showAdd, setShowAdd] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newSourceChannel, setNewSourceChannel] = useState("");
  const [addValidation, setAddValidation] = useState("");

  // Inline title edit
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  const channelsQuery = useQuery({
    queryKey: ["durable-channels"],
    queryFn: () => api.listDurableChannels(),
  });
  const sourceChannels = useMemo(
    () => (channelsQuery.data?.channels ?? []).filter((c) => c.role === "source" && c.status === "active"),
    [channelsQuery.data],
  );
  const productionChannels = useMemo(
    () => (channelsQuery.data?.channels ?? []).filter((c) => c.role === "production" && c.status === "active"),
    [channelsQuery.data],
  );

  const refresh = useCallback(async () => {
    const [data, items] = await Promise.all([
      api.getDurableProject(projectId),
      api.listDurableProjectVideos(projectId),
    ]);
    setProject(data);
    setVideoItems(items.videos);
    setDurableRevision(data.revision);
    setResumeStep(data.resume_step);
    setLoadError(null);
    setNotFound(false);
  }, [projectId, setDurableRevision, setResumeStep]);

  useEffect(() => {
    // AC6 — legacy/non-UUID ids are never sent to the durable UUID endpoint.
    if (!isDurable) {
      // Defer the state flip out of the effect body (React Compiler rule).
      queueMicrotask(() => setLoading(false));
      return;
    }
    let cancelled = false;
    async function loadProjectDetail() {
      try {
        setLoading(true);
        await refresh();
      } catch (err: unknown) {
        if (cancelled) return;
        const message = errDetail(err);
        setLoadError(message);
        setNotFound(/^API 404/.test(message));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadProjectDetail();
    return () => {
      cancelled = true;
    };
  }, [projectId, isDurable, refresh]);

  const retryLoad = () => {
    setLoading(true);
    setLoadError(null);
    setNotFound(false);
    refresh()
      .catch((err: unknown) => {
        const message = errDetail(err);
        setLoadError(message);
        setNotFound(/^API 404/.test(message));
      })
      .finally(() => setLoading(false));
  };

  const addMut = useMutation({
    mutationFn: () =>
      api.createDurableVideo(projectId, {
        title: newTitle.trim(),
        source_channel_id: newSourceChannel || null,
      }),
    onSuccess: async () => {
      await refresh();
      setShowAdd(false);
      setNewTitle("");
      setNewSourceChannel("");
      setAddValidation("");
    },
    onError: (err: unknown) => setActionError(`Không thể thêm Video Item: ${errDetail(err)}`),
  });

  const titleMut = useMutation({
    mutationFn: (input: { videoId: string; title: string; revision: number }) =>
      patchDurableVideo(projectId, input.videoId, { title: input.title.trim() }, input.revision),
    onSuccess: async () => {
      await refresh();
      setEditingId(null);
    },
    onError: (err: unknown) => setActionError(`Không thể đổi tên Video Item: ${errDetail(err)}`),
  });

  const archiveMut = useMutation({
    mutationFn: (item: DurableVideoItem) => api.archiveDurableVideo(projectId, item.video_item_id, item.revision),
    onSuccess: async () => {
      await refresh();
    },
    onError: (err: unknown) => setActionError(`Không thể lưu trữ Video Item: ${errDetail(err)}`),
  });

  const reorderMut = useMutation({
    mutationFn: (ids: string[]) => api.reorderDurableVideos(projectId, project?.revision ?? 1, ids),
    onSuccess: async () => {
      await refresh();
    },
    onError: (err: unknown) => {
      if (isConflict(err)) {
        void refresh().catch(() => {});
        setActionError(
          "Xung đột thứ tự: dự án đã thay đổi ở nơi khác. Đã tải lại dữ liệu mới nhất — vui lòng thử lại thao tác sắp xếp.",
        );
      } else {
        setActionError(`Không thể sắp xếp Video Item: ${errDetail(err)}`);
      }
    },
  });

  const bindMut = useMutation({
    mutationFn: (patch: { source_channel_id?: string | null; production_channel_id?: string | null }) =>
      patchDurableProject(projectId, patch, project?.revision ?? null),
    onSuccess: async (data) => {
      setProject(data);
      setDurableRevision(data.revision);
      setResumeStep(data.resume_step);
    },
    onError: (err: unknown) => setActionError(`Không thể gắn kênh cho dự án: ${errDetail(err)}`),
  });

  const submitAdd = (event: React.FormEvent) => {
    event.preventDefault();
    if (!newTitle.trim()) {
      setAddValidation("Vui lòng nhập tiêu đề Video Item (1–240 ký tự).");
      return;
    }
    setAddValidation("");
    addMut.mutate();
  };

  const startEdit = (item: DurableVideoItem) => {
    setEditingId(item.video_item_id);
    setEditTitle(item.title);
  };

  const saveEdit = (item: DurableVideoItem) => {
    if (!editTitle.trim()) {
      setActionError("Tiêu đề không được để trống.");
      return;
    }
    titleMut.mutate({ videoId: item.video_item_id, title: editTitle, revision: item.revision });
  };

  const requestArchive = (item: DurableVideoItem) => {
    if (!confirm(`Lưu trữ Video Item "${item.title}"? Video Item đã lưu trữ không còn xuất hiện trong danh sách hoạt động.`)) return;
    archiveMut.mutate(item);
  };

  const moveItem = (index: number, dir: -1 | 1) => {
    const target = index + dir;
    if (target < 0 || target >= videoItems.length) return;
    const next = [...videoItems];
    [next[index], next[target]] = [next[target], next[index]];
    reorderMut.mutate(next.map((item) => item.video_item_id));
  };

  const channelName = (channelId: string | null) => {
    if (!channelId) return "Chưa liên kết";
    return channelsQuery.data?.channels.find((c) => c.channel_id === channelId)?.name ?? channelId;
  };

  const busy = addMut.isPending || titleMut.isPending || archiveMut.isPending || reorderMut.isPending || bindMut.isPending;

  if (!isDurable) {
    return (
      <div className="min-h-full bg-zinc-950 text-zinc-100 p-6 space-y-6 max-w-6xl mx-auto">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
          <div className="flex items-center gap-2 text-sm text-zinc-400">
            <Link href="/projects" className="hover:text-zinc-200 transition">
              &larr; Tất cả dự án
            </Link>
          </div>
        </div>
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-6 space-y-3">
          <h1 className="text-xl font-bold text-zinc-100">Dự án quy trình cũ (legacy)</h1>
          <p className="text-sm text-zinc-300 font-mono">ID: {projectId}</p>
          <p className="text-sm text-zinc-400">
            Dự án này không có bản ghi durable (không phải UUID) nên không mở được ở trang chi tiết v2. Mở trong trình làm
            việc để tiếp tục xử lý.
          </p>
          <Link
            href={`/?project=${encodeURIComponent(projectId)}`}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition shadow-lg shadow-indigo-600/20"
          >
            Mở trong trình làm việc &rarr;
          </Link>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-8 text-center text-zinc-400 max-w-5xl mx-auto space-y-4" aria-busy="true" aria-label="Đang tải dự án">
        <div className="h-8 w-48 bg-zinc-800 animate-pulse rounded mx-auto" />
        <div className="h-32 bg-zinc-900 animate-pulse rounded-xl" />
      </div>
    );
  }

  if (notFound) {
    return (
      <div className="min-h-full bg-zinc-950 text-zinc-100 p-6 space-y-6 max-w-6xl mx-auto">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
          <div className="flex items-center gap-2 text-sm text-zinc-400">
            <Link href="/projects" className="hover:text-zinc-200 transition">
              &larr; Tất cả dự án
            </Link>
            <span>/</span>
            <span className="text-zinc-200 font-medium">{projectId}</span>
          </div>
        </div>
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-6 space-y-3" role="alert">
          <h1 className="text-lg font-bold text-amber-300">Không tìm thấy dự án</h1>
          <p className="text-sm text-zinc-300 font-mono">ID: {projectId}</p>
          <p className="text-sm text-zinc-400">
            Dự án không tồn tại trong workspace này (hoặc đã bị xóa khỏi cơ sở dữ liệu durable). Không hiển thị dữ liệu tạm.
          </p>
          <Link
            href="/projects"
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition"
          >
            Về danh sách dự án
          </Link>
        </div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="min-h-full bg-zinc-950 text-zinc-100 p-6 space-y-6 max-w-6xl mx-auto">
        <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
          <div className="flex items-center gap-2 text-sm text-zinc-400">
            <Link href="/projects" className="hover:text-zinc-200 transition">
              &larr; Tất cả dự án
            </Link>
            <span>/</span>
            <span className="text-zinc-200 font-medium">{projectId}</span>
          </div>
        </div>
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-6 space-y-3" role="alert">
          <h1 className="text-lg font-bold text-red-300">Không thể tải dự án</h1>
          <p className="text-sm text-zinc-300">Lỗi: {loadError}</p>
          <p className="text-xs text-zinc-400">
            Kiểm tra backend durable đang chạy và thử lại sau. Không có dữ liệu tạm được hiển thị.
          </p>
          <button
            onClick={retryLoad}
            className="inline-flex items-center gap-2 rounded-lg bg-zinc-800 px-4 py-2 text-xs font-medium text-zinc-200 hover:bg-zinc-700 transition"
          >
            <RefreshCw size={14} aria-hidden="true" />
            Thử lại
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-full bg-zinc-950 text-zinc-100 p-6 space-y-6 max-w-6xl mx-auto">
      {/* Top Breadcrumb & Actions */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
        <div className="flex items-center gap-2 text-sm text-zinc-400">
          <Link href="/projects" className="hover:text-zinc-200 transition">
            &larr; Tất cả dự án
          </Link>
          <span>/</span>
          <span className="text-zinc-200 font-medium">{project?.name}</span>
        </div>
        <Link
          href={`/?project=${encodeURIComponent(projectId)}`}
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition shadow-lg shadow-indigo-600/20"
          title="Tiếp tục quy trình xử lý video tại bước lưu tạm"
        >
          Tiếp tục xử lý{project?.resume_step ? ` (${project.resume_step})` : ""} &rarr;
        </Link>
      </div>

      {/* Action errors — visible, never silent */}
      {actionError && (
        <div
          role="alert"
          className="flex flex-wrap items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300"
        >
          <AlertCircle size={18} aria-hidden="true" />
          <span className="min-w-0 flex-1">{actionError}</span>
          <button
            type="button"
            onClick={() => setActionError(null)}
            aria-label="Đóng cảnh báo"
            className="grid size-8 place-items-center rounded-lg hover:bg-zinc-800"
          >
            <X size={15} aria-hidden="true" />
          </button>
        </div>
      )}

      {/* Project Overview Card */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 space-y-4 backdrop-blur-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h1 className="text-xl font-bold text-zinc-100">{project?.name}</h1>
            <p className="text-xs text-zinc-400 font-mono mt-0.5">ID: {project?.project_id}</p>
          </div>
          <span
            className={`self-start sm:self-auto rounded-full px-3 py-1 text-xs font-medium ${
              PROJECT_STATUS_BADGE[project?.status ?? ""]?.className ?? "bg-zinc-800 text-zinc-300"
            }`}
          >
            Trạng thái: {PROJECT_STATUS_BADGE[project?.status ?? ""]?.label ?? project?.status}
          </span>
        </div>

        {project?.description && <p className="text-sm text-zinc-300">{project.description}</p>}

        {/* Channel binding — real durable PATCH with revision/CAS */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 border-t border-zinc-800/80 pt-4 text-xs">
          <label className="block">
            <span className="text-zinc-500 block mb-1">Kênh Nguồn (Source Channel)</span>
            <select
              value={project?.source_channel_id ?? ""}
              onChange={(e) => bindMut.mutate({ source_channel_id: e.target.value || null })}
              disabled={busy}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-200 disabled:opacity-60"
            >
              <option value="">Chưa liên kết</option>
              {sourceChannels.map((channel) => (
                <option key={channel.channel_id} value={channel.channel_id}>
                  {channel.name}
                </option>
              ))}
            </select>
            <span className="mt-1 block text-zinc-500">Chỉ liệt kê kênh vai trò source đang hoạt động.</span>
          </label>
          <label className="block">
            <span className="text-zinc-500 block mb-1">Kênh Sản Xuất (Production Channel)</span>
            <select
              value={project?.production_channel_id ?? ""}
              onChange={(e) => bindMut.mutate({ production_channel_id: e.target.value || null })}
              disabled={busy}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-200 disabled:opacity-60"
            >
              <option value="">Chưa liên kết</option>
              {productionChannels.map((channel) => (
                <option key={channel.channel_id} value={channel.channel_id}>
                  {channel.name}
                </option>
              ))}
            </select>
            <span className="mt-1 block text-zinc-500">Chỉ liệt kê kênh vai trò production đang hoạt động.</span>
          </label>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 border-t border-zinc-800/80 pt-4 text-xs">
          <div>
            <span className="text-zinc-500 block">Bước làm việc tiếp theo</span>
            <span className="text-indigo-400 font-medium uppercase">{project?.resume_step || "Start"}</span>
          </div>
          <div>
            <span className="text-zinc-500 block">Phiên bản (revision)</span>
            <span className="text-zinc-200 font-medium">#{project?.revision}</span>
          </div>
          <div>
            <span className="text-zinc-500 block">Cập nhật gần nhất</span>
            <span className="text-zinc-200 font-medium">
              {project?.updated_at ? new Date(project.updated_at).toLocaleString("vi-VN") : "—"}
            </span>
          </div>
        </div>
      </div>

      {/* Video Items Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-zinc-100">Danh Sách Video Items ({videoItems.length})</h2>
            <p className="text-xs text-zinc-400">
              Các đoạn video nguồn và dữ liệu trích xuất chuyển động trong dự án này — thứ tự = vị trí phát hành.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setShowAdd((v) => !v)}
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition disabled:opacity-60 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
            title="Thêm Video Item mới vào cuối danh sách"
          >
            <Plus size={15} aria-hidden="true" />
            Thêm Video Item
          </button>
        </div>

        {showAdd && (
          <form onSubmit={submitAdd} className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-zinc-200">Video Item mới</h3>
              <button
                type="button"
                aria-label="Đóng biểu mẫu thêm"
                onClick={() => setShowAdd(false)}
                className="grid size-8 place-items-center rounded-lg hover:bg-zinc-800"
              >
                <X size={15} aria-hidden="true" />
              </button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-[1fr_14rem] gap-3">
              <label className="block text-xs text-zinc-400">
                Tiêu đề
                <input
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  maxLength={240}
                  className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-200"
                  placeholder="Ví dụ: Tập 1 — Cảnh mở đầu"
                />
              </label>
              <label className="block text-xs text-zinc-400">
                Kênh nguồn (tùy chọn)
                <select
                  value={newSourceChannel}
                  onChange={(e) => setNewSourceChannel(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-200"
                >
                  <option value="">Chưa liên kết</option>
                  {sourceChannels.map((channel) => (
                    <option key={channel.channel_id} value={channel.channel_id}>
                      {channel.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {addValidation && <p className="text-sm text-red-400">{addValidation}</p>}
            <div className="flex items-center justify-end gap-2">
              <button
                type="submit"
                disabled={addMut.isPending}
                className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition disabled:opacity-60"
              >
                {addMut.isPending ? "Đang thêm..." : "Thêm vào cuối danh sách"}
              </button>
            </div>
            <p className="text-[11px] text-zinc-500">
              Vị trí được cấp tự động (cuối danh sách). Thời lượng và dữ liệu probe được backend điền ở bước nhập video (S05).
            </p>
          </form>
        )}

        {videoItems.length === 0 ? (
          <div className="rounded-xl border border-dashed border-zinc-800 p-8 text-center text-xs text-zinc-500">
            Chưa có Video Item nào trong dự án này. Dùng &quot;Thêm Video Item&quot; để tạo mục đầu tiên.
          </div>
        ) : (
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 divide-y divide-zinc-800/80">
            {videoItems.map((item, index) => {
              const badge = VIDEO_STATUS_BADGE[item.status] ?? { label: item.status, className: "bg-zinc-800 text-zinc-300" };
              return (
                <div key={item.video_item_id} className="p-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="w-6 h-6 rounded-full bg-zinc-800 text-zinc-400 text-xs font-mono flex items-center justify-center shrink-0">
                      #{item.position}
                    </span>
                    <div className="min-w-0">
                      {editingId === item.video_item_id ? (
                        <div className="flex items-center gap-2">
                          <input
                            value={editTitle}
                            onChange={(e) => setEditTitle(e.target.value)}
                            maxLength={240}
                            autoFocus
                            className="rounded-lg border border-indigo-500/50 bg-zinc-950 px-2 py-1 text-sm text-zinc-200"
                          />
                          <button
                            type="button"
                            onClick={() => saveEdit(item)}
                            disabled={titleMut.isPending}
                            className="rounded-lg bg-indigo-600 px-2 py-1 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-60"
                          >
                            Lưu
                          </button>
                          <button
                            type="button"
                            onClick={() => setEditingId(null)}
                            className="rounded-lg bg-zinc-800 px-2 py-1 text-xs text-zinc-300 hover:bg-zinc-700"
                          >
                            Hủy
                          </button>
                        </div>
                      ) : (
                        <h3 className="text-sm font-medium text-zinc-200">{item.title}</h3>
                      )}
                      <span className="text-xs text-zinc-500">
                        Thời lượng: {formatDuration(item.duration_ms)} · Kênh nguồn: {channelName(item.source_channel_id)}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-xs">
                    <span className={`rounded px-2.5 py-1 ${badge.className}`}>{badge.label}</span>
                    <div className="flex items-center gap-1" role="group" aria-label={`Sắp xếp Video Item ${item.title}`}>
                      <button
                        type="button"
                        onClick={() => moveItem(index, -1)}
                        disabled={index === 0 || busy}
                        aria-label="Di chuyển lên"
                        className="grid size-8 place-items-center rounded-lg bg-zinc-800 text-zinc-300 hover:bg-zinc-700 disabled:opacity-40"
                      >
                        <ArrowUp size={14} aria-hidden="true" />
                      </button>
                      <button
                        type="button"
                        onClick={() => moveItem(index, 1)}
                        disabled={index === videoItems.length - 1 || busy}
                        aria-label="Di chuyển xuống"
                        className="grid size-8 place-items-center rounded-lg bg-zinc-800 text-zinc-300 hover:bg-zinc-700 disabled:opacity-40"
                      >
                        <ArrowDown size={14} aria-hidden="true" />
                      </button>
                    </div>
                    <button
                      type="button"
                      onClick={() => startEdit(item)}
                      disabled={item.status === "archived" || busy}
                      className="inline-flex items-center gap-1 rounded-lg bg-zinc-800 px-2.5 py-1.5 text-zinc-300 hover:bg-zinc-700 disabled:opacity-40"
                      title={item.status === "archived" ? "Video Item đã lưu trữ không thể sửa" : "Đổi tên Video Item"}
                    >
                      <Pencil size={13} aria-hidden="true" />
                      Sửa
                    </button>
                    <button
                      type="button"
                      onClick={() => requestArchive(item)}
                      disabled={item.status === "archived" || busy}
                      className="inline-flex items-center gap-1 rounded-lg bg-zinc-800 px-2.5 py-1.5 text-red-300 hover:bg-zinc-700 disabled:opacity-40"
                      title={item.status === "archived" ? "Đã lưu trữ" : "Lưu trữ Video Item (không xóa hẳn)"}
                    >
                      <Archive size={13} aria-hidden="true" />
                      {item.status === "archived" ? "Đã lưu trữ" : "Lưu trữ"}
                    </button>
                    {item.status === "completed" && <CheckCircle2 size={15} className="text-emerald-400" aria-label="Hoàn tất" />}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
