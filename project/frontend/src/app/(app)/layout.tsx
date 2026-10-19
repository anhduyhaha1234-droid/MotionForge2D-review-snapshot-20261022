import type { ReactNode } from "react";
import { AppShell } from "@/components/layout/AppShell";

export default function ApplicationLayout({ children }: { children: ReactNode }) { return <AppShell>{children}</AppShell>; }
