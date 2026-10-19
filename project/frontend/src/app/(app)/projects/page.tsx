"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AlertCircle, FolderOpen, RefreshCw } from "lucide-react";
import { api, isUuid, type ProjectSummary } from "@/lib/api";
import { ContextInspector } from "@/components/layout/ContextInspector";

const date = (value: string) => {
  // Defensive: legacy filesystem projects can carry an empty created_at ("");
  // `new Date("")` is Invalid Date and `.format()` throws RangeError, which
  // crashed the whole /projects page. Empty/invalid timestamps render "—".
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "—";
  return new Intl.DateTimeFormat("vi-VN", { dateStyle: "medium", timeStyle: "short" }).format(parsed);
};
const status: Record<string, { label: string; className: string }> = {
  draft: { label: "Nháp", className: "bg-[var(--surface-800)] text-[var(--text-secondary)]" },
  in_progress: { label: "Đang thực hiện", className: "bg-[color-mix(in_srgb,var(--primary-600)_22%,transparent)] text-[var(--primary-300)]" },
  ready_to_stitch: { label: "Sẵn sàng ghép", className: "bg-cyan-950 text-[var(--accent-300)]" },
  completed: { label: "Hoàn tất", className: "bg-emerald-950 text-[var(--success)]" },
};
const guidance = (value: string) => value === "completed" ? "Dự án đã hoàn tất và sẵn sàng xuất bản." : value === "ready_to_stitch" ? "Kiểm tra các cảnh rồi ghép video hoàn chỉnh." : value === "in_progress" ? "Tiếp tục chọn đối tượng và tạo demo thay thế." : "Nhập video nguồn để bắt đầu sản xuất.";

export default function ProjectsPage() {
  const query = useQuery({ queryKey: ["projects"], queryFn: () => api.listAllProjects() });
  const [selected, setSelected] = useState<ProjectSummary | null>(null);
  const sections = selected ? [{ title: "Thông tin dự án", rows: [{ label: "Tên", value: selected.name }, { label: "Mã dự án", value: <span className="font-mono">{selected.project_id}</span> }, { label: "Trạng thái", value: status[selected.task_status]?.label ?? selected.task_status }, { label: "Số cảnh", value: selected.scenes_count }, { label: "Video nguồn", value: selected.source_video }, { label: "Cập nhật", value: date(selected.updated_at) }, { label: "Ngày tạo", value: date(selected.created_at) }] }, { title: "Bước tiếp theo", rows: [{ label: "Đề xuất", value: guidance(selected.task_status) }] }] : [];
  const selectRow = (event: React.KeyboardEvent, project: ProjectSummary) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); setSelected(project); } };

  return <div className="flex min-h-[calc(100vh-4rem)]"><div className="min-w-0 flex-1 p-6 lg:p-8"><div className="mb-6"><h2 className="font-display text-2xl font-semibold">Dự án</h2><p className="mt-1 text-sm text-[var(--text-muted)]">Tất cả dự án đang sản xuất.</p></div>
    {query.isLoading && <div className="space-y-2">{[1,2,3,4].map((n) => <div key={n} className="h-16 animate-pulse rounded-lg bg-[var(--surface-850)]" />)}</div>}
    {query.isError && <div className="rounded-xl border border-[var(--danger)] bg-[var(--surface-900)] p-6 text-center"><AlertCircle className="mx-auto text-[var(--danger)]" /><p className="mt-3 text-[var(--text-secondary)]">Không thể tải danh sách dự án.</p><button onClick={() => query.refetch()} className="mx-auto mt-4 flex min-h-10 items-center gap-2 rounded-lg bg-[var(--surface-800)] px-4 text-sm"><RefreshCw size={16} />Thử lại</button></div>}
    {query.data?.length === 0 && <div className="rounded-xl border border-dashed border-[var(--surface-700)] bg-[var(--surface-900)] p-10 text-center"><FolderOpen className="mx-auto text-[var(--primary-300)]" size={32} /><h3 className="mt-4 font-display text-lg font-semibold">Chưa có dự án</h3><p className="mt-2 text-sm text-[var(--text-muted)]">Tạo dự án và nhập video nguồn để bắt đầu quy trình sản xuất.</p><Link href="/" className="mt-5 inline-flex min-h-10 items-center rounded-lg bg-[var(--primary-700)] px-4 text-sm font-semibold text-white">Tạo dự án mới</Link></div>}
    {query.data && query.data.length > 0 && <div className="overflow-x-auto rounded-xl border border-[var(--surface-800)] bg-[var(--surface-900)]"><table className="w-full min-w-[760px] text-left text-sm"><thead className="border-b border-[var(--surface-800)] text-xs uppercase tracking-wide text-[var(--text-muted)]"><tr><th className="px-4 py-3">Tên dự án</th><th className="px-4 py-3">Trạng thái</th><th className="px-4 py-3">Số cảnh</th><th className="px-4 py-3">Cập nhật</th><th className="px-4 py-3">Thao tác</th></tr></thead><tbody>{query.data.map((project) => { const badge = status[project.task_status]; return <tr key={project.project_id} tabIndex={0} aria-selected={selected?.project_id === project.project_id} onClick={() => setSelected(project)} onKeyDown={(event) => selectRow(event, project)} className="cursor-pointer border-b border-[var(--surface-800)] transition-colors last:border-0 hover:bg-[var(--surface-850)] aria-selected:bg-[var(--surface-850)]"><td className="px-4 py-4"><p className="font-medium text-[var(--text-primary)]">{project.name}</p><p className="mt-1 font-mono text-xs text-[var(--text-muted)]">{project.project_id}</p></td><td className="px-4 py-4"><span className={`rounded-full px-2.5 py-1 text-xs ${badge?.className ?? "bg-[var(--surface-800)] text-[var(--text-secondary)]"}`}>{badge?.label ?? project.task_status}</span></td><td className="px-4 py-4 text-[var(--text-secondary)]">{project.scenes_count}</td><td className="px-4 py-4 text-[var(--text-muted)]">{date(project.updated_at)}</td><td className="px-4 py-4"><Link href={isUuid(project.project_id) ? `/projects/${project.project_id}` : `/?project=${encodeURIComponent(project.project_id)}`} onClick={(event) => event.stopPropagation()} className="inline-flex min-h-9 items-center rounded-lg border border-[var(--surface-700)] px-3 text-xs font-semibold text-[var(--primary-300)] hover:bg-[var(--surface-800)]" title={isUuid(project.project_id) ? "Mở trang chi tiết dự án" : "Mở dự án trong trình làm việc"}>{isUuid(project.project_id) ? "Chi tiết" : "Mở dự án"}</Link></td></tr>; })}</tbody></table></div>}
  </div><ContextInspector title={selected?.name ?? "Chi tiết dự án"} sections={sections} /></div>;
}
