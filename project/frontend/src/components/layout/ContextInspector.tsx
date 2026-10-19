"use client";

import type { ReactNode } from "react";
import { PanelRight } from "lucide-react";

export interface InspectorSection { title: string; rows: { label: string; value: ReactNode }[] }
export function ContextInspector({ title = "Chi tiết", sections }: { title?: string; sections: InspectorSection[] }) {
  return <aside aria-label="Bảng ngữ cảnh" className="hidden w-72 shrink-0 overflow-y-auto border-l border-[var(--surface-800)] bg-[var(--surface-900)] p-4 xl:block">
    <h2 className="font-display text-base font-semibold">{title}</h2>
    {sections.length === 0 ? <div className="mt-8 text-center text-sm text-[var(--text-muted)]"><PanelRight className="mx-auto mb-3" size={24} /><p>Chọn một mục để xem chi tiết.</p></div> : <div className="mt-5 space-y-6">{sections.map((section) => <section key={section.title}><h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">{section.title}</h3><dl className="space-y-3">{section.rows.map((row) => <div key={row.label}><dt className="text-xs text-[var(--text-muted)]">{row.label}</dt><dd className="mt-0.5 break-words text-sm text-[var(--text-secondary)]">{row.value}</dd></div>)}</dl></section>)}</div>}
  </aside>;
}
