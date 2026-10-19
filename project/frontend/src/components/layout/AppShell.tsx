"use client";

import type { ReactNode } from "react";
import { AppHeader } from "@/components/layout/AppHeader";
import { AppNav } from "@/components/layout/AppNav";
import { MainContent } from "@/components/layout/MainContent";

export function AppShell({ children, inspector }: { children: ReactNode; inspector?: ReactNode }) {
  return <div className="min-h-screen bg-[var(--surface-950)] text-[var(--text-primary)]">
    <a href="#main-content" className="sr-only focus:fixed focus:left-3 focus:top-3 focus:z-[100] focus:not-sr-only focus:rounded-lg focus:bg-[var(--primary-700)] focus:px-4 focus:py-2 focus:text-sm focus:text-white">Bỏ qua điều hướng chính</a>
    <div className="flex min-h-screen"><AppNav /><div className="flex min-w-0 flex-1 flex-col"><AppHeader /><MainContent className="pb-16 md:pb-0">{children}</MainContent></div>{inspector ? <div className="hidden w-72 shrink-0 xl:block">{inspector}</div> : null}</div>
  </div>;
}
