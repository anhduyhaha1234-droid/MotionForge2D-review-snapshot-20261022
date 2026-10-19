"use client";

import { usePathname, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { useProjectStore } from "@/stores/project";

const titles: Record<string, string> = { "/": "Trang chủ", "/channels": "Kênh", "/projects": "Dự án", "/characters": "Thư viện nhân vật" };

export function AppHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const projectId = useProjectStore((s) => s.projectId);
  const project = useProjectStore((s) => s.project);
  const resetAll = useProjectStore((s) => s.resetAll);
  const { data: gpu } = useQuery({ queryKey: ["gpu-info"], queryFn: () => api.getGpuInfo(), staleTime: 60_000 });
  const title = Object.entries(titles).find(([path]) => path === "/" ? pathname === "/" : pathname.startsWith(path))?.[1] ?? "MotionForge 2D";

  return <header className="sticky top-0 z-40 flex min-h-16 items-center justify-between gap-4 border-b border-[var(--surface-800)] bg-[color-mix(in_srgb,var(--surface-900)_90%,transparent)] px-4 backdrop-blur md:px-6">
    <div className="min-w-0"><h1 className="font-display text-lg font-semibold">{title}</h1>{projectId && project && <p className="truncate text-xs text-[var(--text-muted)]">{project.name} · {projectId.slice(0, 8)} · {project.scenes.length} cảnh</p>}</div>
    <div className="flex items-center gap-2">
      <span className="hidden items-center gap-2 rounded-full bg-[var(--surface-850)] px-3 py-1.5 text-xs text-[var(--text-secondary)] sm:flex"><span className="size-2 rounded-full bg-[var(--success)]" />Đã lưu cục bộ</span>
      {gpu && <span className="hidden rounded-full border border-[var(--surface-700)] px-3 py-1.5 text-xs text-[var(--text-secondary)] lg:block">{gpu.has_nvenc ? `GPU · ${gpu.gpu_name}` : "CPU Mode"}</span>}
      {projectId && <button type="button" onClick={() => { resetAll(); router.push("/"); }} className="flex min-h-9 items-center gap-1.5 rounded-lg bg-[var(--primary-700)] px-3 text-xs font-semibold text-white transition-colors hover:bg-[var(--primary-600)]"><Sparkles size={15} />Dự án mới</button>}
    </div>
  </header>;
}
