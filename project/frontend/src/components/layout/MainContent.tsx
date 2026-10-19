"use client";

import type { ReactNode } from "react";

export function MainContent({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <main id="main-content" tabIndex={-1} className={`min-w-0 flex-1 focus-visible:outline-none ${className}`}>{children}</main>;
}
