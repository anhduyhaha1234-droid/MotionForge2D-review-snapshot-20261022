"use client";

import { useMemo } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  ArrowRight,
  FolderOpen,
  Play,
  Plus,
  Radio,
  RefreshCw,
  Users,
  Wrench,
} from "lucide-react";
import { api, isUuid, type ProjectSummaryData } from "@/lib/api";

// Durable project statuses (ProjectStatus enum from the summary DTO).
const PROJECT_STATUS: Record<string, { label: string; className: string }> = {
  draft: { label: "Bản nháp", className: "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20" },
  active: { label: "Đang hoạt động", className: "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20" },
  needs_review: { label: "Cần xem lại", className: "bg-amber-500/10 text-amber-400 border border-amber-500/20" },
  rendering: { label: "Đang xuất", className: "bg-purple-500/10 text-purple-400 border border-purple-500/20" },
  completed: { label: "Hoàn tất", className: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" },
  archived: { label: "Đã lưu trữ", className: "bg-zinc-500/10 text-zinc-400 border border-zinc-500/20" },
};

// Backend returns stable next_action codes; the UI owns the Vietnamese labels.
const NEXT_ACTION_LABEL: Record<string, string> = {
  none: "Không có bước kế tiếp",
  analyze_video: "Phân tích video",
  map_objects: "Ánh xạ đối tượng",
  create_demo: "Tạo demo thay thế",
  apply_reskin: "Áp dụng thay thế",
  review_work: "Kiểm tra kết quả",
  export_video: "Xuất video",
  retry_failed: "Thử lại video lỗi",
};

const BLOCKER_LABEL: Record<string, string> = {
  qc_unavailable: "Kiểm tra (QC) chưa sẵn sàng",
  output_unavailable: "Kênh xuất chưa sẵn sàng",
  capability_unavailable: "Tính năng đang phát triển",
};

function StatCard({
  label,
  value,
  icon,
  tone,
  busy,
  unavailable,
  unavailableHint,
  onRetry,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  tone: string;
  busy: boolean;
  unavailable?: boolean;
  unavailableHint?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="rounded-xl border border-[var(--surface-800)] bg-[var(--surface-900)] p-5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-[var(--text-muted)]">{label}</span>
        <span className={`grid size-9 place-items-center rounded-lg ${tone}`}>{icon}</span>
      </div>
      <p className="mt-2 text-3xl font-bold text-[var(--text-primary)]" aria-busy={busy}>
        {busy ? "..." : unavailable ? "—" : value}
      </p>
      {/* Independent unavailable state — a failed sub-request is NEVER
          rendered as a real zero; the stat shows "—" + retry instead. */}
      {unavailable && (
        <div
          role="status"
          aria-live="polite"
          className="mt-3 space-y-2 border-t border-[var(--surface-800)] pt-3"
        >
          <p className="text-xs text-[var(--text-secondary)]">
            {unavailableHint ?? "Không khả dụng — không thể tải dữ liệu."}
          </p>
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="inline-flex min-h-8 items-center gap-1.5 rounded-lg bg-[var(--surface-800)] px-3 text-xs font-medium text-[var(--text-primary)] hover:bg-[var(--surface-700)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary-300)]"
              title="Tải lại riêng số liệu thư viện nhân vật"
            >
              <RefreshCw size={13} aria-hidden="true" />
              Thử lại
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function NextActionChip({ project }: { project: ProjectSummaryData }) {
  const next = project.next_action;
  const label = NEXT_ACTION_LABEL[next.code] ?? next.code;
  if (!next.enabled) {
    return (
      <span
        title={next.blocker ? BLOCKER_LABEL[next.blocker] ?? next.blocker : undefined}
        className="inline-flex items-center gap-1.5 rounded-md bg-[var(--surface-800)] px-2.5 py-1 text-xs text-[var(--text-muted)]"
      >
        <Wrench size={13} aria-hidden="true" />
        {label} · {next.blocker ? BLOCKER_LABEL[next.blocker] ?? next.blocker : "chưa sẵn sàng"}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-md bg-[color-mix(in_srgb,var(--primary-600)_22%,transparent)] px-2.5 py-1 text-xs font-medium text-[var(--primary-300)]">
      <Play size={13} aria-hidden="true" />
      {label}
    </span>
  );
}

export function Dashboard({ onEnterEditor }: { onEnterEditor: () => void }) {
  const summariesQuery = useQuery({
    queryKey: ["project-summaries"],
    queryFn: () => api.listProjectSummaries({ limit: 200 }),
    retry: 1,
  });
  const presetsQuery = useQuery({
    queryKey: ["character-presets"],
    queryFn: () => api.listCharacterPresets(),
    retry: 1,
  });

  const summaries = useMemo(() => summariesQuery.data?.summaries ?? [], [summariesQuery.data]);
  const loading = summariesQuery.isLoading;
  const error = summariesQuery.isError;

  // Real stat derivation — every number comes from the approved contracts.
  const totalProjects = summariesQuery.data?.total ?? summaries.length;
  const activeJobs = useMemo(
    () => summaries.reduce((acc, project) => acc + project.active_job_count, 0),
    [summaries],
  );
  const productionChannels = useMemo(
    () => new Set(summaries.map((project) => project.production_channel?.channel_id).filter(Boolean)).size,
    [summaries],
  );
  const presetCount = presetsQuery.data?.characters.length ?? 0;

  const retryPresets = () => {
    // Independent retry — only the character-preset request is refetched so a
    // failed library call never blocks the project summaries below.
    void presetsQuery.refetch();
  };

  // Active jobs come from the per-project summary read model — the real
  // dashboard contract (no fake /api/v2/jobs?state=running call).
  const runningJobs = useMemo(
    () => summaries.flatMap((project) => project.active_jobs.map((job) => ({ project, job }))),
    [summaries],
  );

  const retryAll = () => {
    void summariesQuery.refetch();
    void presetsQuery.refetch();
  };

  return (
    <div className="min-h-full bg-[var(--surface-950)] p-6 text-[var(--text-primary)] lg:p-8">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Header */}
        <div className="flex flex-col gap-4 border-b border-[var(--surface-800)] pb-6 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="font-display text-2xl font-bold tracking-tight">Bảng Điều Khiển MotionForge 2D</h1>
            <p className="mt-1 text-sm text-[var(--text-muted)]">
              Tổng quan dự án, tiến trình xử lý tự động và kênh xuất bản.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/channels"
              className="inline-flex min-h-10 items-center gap-2 rounded-lg bg-[var(--surface-800)] px-4 text-sm font-medium text-[var(--text-primary)] transition-colors hover:bg-[var(--surface-700)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary-300)]"
              title="Tạo kênh nguồn hoặc kênh sản xuất mới"
            >
              <Radio size={17} aria-hidden="true" />
              Quản lý Kênh
            </Link>
            <button
              type="button"
              onClick={onEnterEditor}
              className="inline-flex min-h-10 items-center gap-2 rounded-lg bg-[var(--primary-700)] px-4 text-sm font-semibold text-white transition-colors hover:bg-[var(--primary-600)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary-300)]"
              title="Mở trình làm việc để tạo dự án mới và nhập video nguồn"
            >
              <Plus size={17} aria-hidden="true" />
              Tạo Dự Án Mới
            </button>
          </div>
        </div>

        {/* Error banner — visible, with retry */}
        {error && (
          <div
            role="alert"
            className="flex flex-wrap items-center gap-3 rounded-xl border border-[var(--danger)] bg-[var(--surface-900)] p-4 text-sm text-[var(--danger)]"
          >
            <AlertCircle size={18} aria-hidden="true" />
            <span className="min-w-0 flex-1">Không thể tải dữ liệu bảng điều khiển từ backend durable.</span>
            <button
              type="button"
              onClick={retryAll}
              className="inline-flex min-h-9 items-center gap-2 rounded-lg bg-[var(--surface-800)] px-3 text-xs font-medium text-[var(--text-primary)] hover:bg-[var(--surface-700)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary-300)]"
            >
              <RefreshCw size={14} aria-hidden="true" />
              Thử lại
            </button>
          </div>
        )}

        {/* Summary cards — real numbers only */}
        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Tổng Dự Án"
            value={String(totalProjects)}
            busy={loading}
            tone="bg-[color-mix(in_srgb,var(--primary-600)_20%,transparent)] text-[var(--primary-300)]"
            icon={<FolderOpen size={20} aria-hidden="true" />}
          />
          <StatCard
            label="Tiến Trình Đang Chạy"
            value={String(activeJobs)}
            busy={loading}
            tone="bg-[color-mix(in_srgb,var(--accent-500)_20%,transparent)] text-[var(--accent-300)]"
            icon={<Play size={20} aria-hidden="true" />}
          />
          <StatCard
            label="Kênh Sản Xuất"
            value={String(productionChannels)}
            busy={loading}
            tone="bg-[color-mix(in_srgb,var(--success)_18%,transparent)] text-[var(--success)]"
            icon={<Radio size={20} aria-hidden="true" />}
          />
          <StatCard
            label="Thư Viện Nhân Vật"
            value={String(presetCount)}
            busy={presetsQuery.isLoading}
            unavailable={presetsQuery.isError}
            unavailableHint="Không thể tải thư viện nhân vật — kiểm tra backend rồi thử lại."
            onRetry={retryPresets}
            tone="bg-purple-500/10 text-purple-400"
            icon={<Users size={20} aria-hidden="true" />}
          />
        </dl>

        {/* Active jobs — from the real summary read model */}
        {runningJobs.length > 0 && (
          <section aria-label="Tiến trình đang xử lý tự động" className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-display text-lg font-semibold">
                Tiến Trình Đang Xử Lý Tự Động ({runningJobs.length})
              </h2>
            </div>
            <div className="space-y-3">
              {runningJobs.map(({ project, job }) => (
                <div
                  key={job.job_id}
                  className="rounded-xl border border-[var(--surface-800)] bg-[var(--surface-900)] p-4"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
                    <span className="font-medium text-[var(--text-primary)]">{job.job_type}</span>
                    <span className="text-xs text-[var(--text-muted)]">
                      Dự án: {project.name} · Trạng thái: {job.state}
                    </span>
                  </div>
                  <div
                    role="progressbar"
                    aria-valuenow={Math.round(job.progress)}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label={`Tiến trình ${job.job_type}`}
                    className="mt-2 h-2 w-full overflow-hidden rounded-full bg-[var(--surface-800)]"
                  >
                    <div
                      className="h-2 rounded-full bg-[var(--accent-500)] transition-all duration-300"
                      style={{ width: `${job.progress}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Projects list */}
        <section aria-label="Dự án gần đây" className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-display text-lg font-semibold">Dự Án Gần Đây</h2>
              <p className="text-xs text-[var(--text-muted)]">Danh sách các dự án animation 2D hiện có</p>
            </div>
            <Link href="/projects" className="text-xs text-[var(--primary-300)] hover:text-[var(--primary-200)]">
              Xem tất cả dự án &rarr;
            </Link>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3" aria-busy="true" aria-label="Đang tải dự án">
              {[1, 2, 3].map((n) => (
                <div key={n} className="h-48 animate-pulse rounded-xl bg-[var(--surface-850)]" />
              ))}
            </div>
          ) : error ? (
            <div className="rounded-xl border border-[var(--surface-800)] bg-[var(--surface-900)] p-10 text-center">
              <p className="text-sm text-[var(--text-secondary)]">Không thể tải danh sách dự án.</p>
              <button
                type="button"
                onClick={retryAll}
                className="mx-auto mt-4 inline-flex min-h-10 items-center gap-2 rounded-lg bg-[var(--surface-800)] px-4 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary-300)]"
              >
                <RefreshCw size={16} aria-hidden="true" />
                Thử lại
              </button>
            </div>
          ) : summaries.length === 0 ? (
            <div className="rounded-xl border border-dashed border-[var(--surface-700)] bg-[var(--surface-900)] p-12 text-center">
              <FolderOpen size={32} className="mx-auto text-[var(--primary-300)]" aria-hidden="true" />
              <h3 className="mt-4 font-display text-lg font-semibold">Chưa có dự án nào</h3>
              <p className="mx-auto mt-2 max-w-lg text-sm text-[var(--text-muted)]">
                Bắt đầu bằng cách tạo dự án mới trong trình làm việc, hoặc nhập video nguồn để trích xuất chuyển động 2D.
              </p>
              <div className="mt-5 flex flex-wrap justify-center gap-3">
                <button
                  type="button"
                  onClick={onEnterEditor}
                  className="inline-flex min-h-10 items-center gap-2 rounded-lg bg-[var(--primary-700)] px-4 text-sm font-semibold text-white hover:bg-[var(--primary-600)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary-300)]"
                >
                  <Plus size={16} aria-hidden="true" />
                  Tạo Dự Án Mới Ngay
                </button>
                <button
                  type="button"
                  onClick={onEnterEditor}
                  className="inline-flex min-h-10 items-center gap-2 rounded-lg bg-[var(--surface-800)] px-4 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--surface-700)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary-300)]"
                >
                  Vào Trình Làm Việc
                </button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {summaries.map((project) => {
                const badge = PROJECT_STATUS[project.status];
                const durable = isUuid(project.project_id);
                return (
                  <article
                    key={project.project_id}
                    className="flex flex-col justify-between rounded-xl border border-[var(--surface-800)] bg-[var(--surface-900)] p-5 transition-colors hover:border-[var(--surface-700)]"
                  >
                    <div className="space-y-3">
                      <div className="flex items-start justify-between gap-2">
                        <h3 className="line-clamp-1 font-display font-semibold text-[var(--text-primary)]">
                          {project.name}
                        </h3>
                        <span
                          className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                            badge?.className ?? "bg-[var(--surface-800)] text-[var(--text-secondary)]"
                          }`}
                        >
                          {badge?.label ?? project.status}
                        </span>
                      </div>
                      {project.description && (
                        <p className="line-clamp-2 text-xs text-[var(--text-muted)]">{project.description}</p>
                      )}
                      <div className="flex flex-wrap gap-2 text-xs">
                        {project.source_channel?.name && (
                          <span className="rounded bg-[var(--surface-800)] px-2 py-0.5 text-[var(--text-secondary)]">
                            Nguồn: {project.source_channel.name}
                          </span>
                        )}
                        {project.production_channel?.name && (
                          <span className="rounded bg-[var(--surface-800)] px-2 py-0.5 text-[var(--text-secondary)]">
                            Sản xuất: {project.production_channel.name}
                          </span>
                        )}
                      </div>
                      <NextActionChip project={project} />
                    </div>

                    <div className="mt-4 flex items-center justify-between border-t border-[var(--surface-800)] pt-4 text-xs text-[var(--text-muted)]">
                      <span>
                        {project.video_counts.active} video · {project.video_counts.completed} hoàn tất
                      </span>
                      <Link
                        href={durable ? `/projects/${project.project_id}` : `/?project=${encodeURIComponent(project.project_id)}`}
                        className="inline-flex items-center gap-1 font-medium text-[var(--primary-300)] hover:text-[var(--primary-200)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary-300)]"
                        title={durable ? "Mở trang chi tiết dự án" : "Mở dự án trong trình làm việc"}
                      >
                        {durable ? "Chi tiết" : "Mở trong trình làm việc"}
                        <ArrowRight size={13} aria-hidden="true" />
                      </Link>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
