"use client";

import { useEffect, useState } from "react";
import { useProjectStore } from "@/stores/project";
import { ScreenA } from "@/components/ScreenA";
import { ScreenB } from "@/components/ScreenB";
import { ScreenC } from "@/components/ScreenC";
import { ScreenD } from "@/components/ScreenD";
import { ScreenE } from "@/components/ScreenE";
import { AssemblyModal } from "@/components/AssemblyModal";
import { ChannelDashboard } from "@/components/ChannelDashboard";
import { NavigationHeader } from "@/components/NavigationHeader";
import { api } from "@/lib/api";
import { useProjectRehydration, saveSession, clearSession } from "@/hooks/useProjectRehydration";

function ScreenRouter() {
  const screen = useProjectStore((s) => s.screen);
  switch (screen) { case "start": return <ScreenA />; case "selection": return <ScreenB />; case "review": return <ScreenC />; case "replacement": return <ScreenD />; case "render": return <ScreenE />; default: return <ScreenA />; }
}

async function resumeProject(pid: string) {
  const store = useProjectStore.getState();
  store.setProjectId(pid);
  const project = await api.getProject(pid);
  store.setProject(project);
  const scenes = await api.getSceneDetails(pid);
  store.setScenes(scenes);
  store.setScreen("selection");
}

export function LegacyWorkspace({ onExitEditor }: { onExitEditor?: () => void }) {
  const [showAssembly, setShowAssembly] = useState(false);
  const [showDashboard, setShowDashboard] = useState(false);
  const { isRehydrating } = useProjectRehydration();
  const screen = useProjectStore((s) => s.screen);
  const projectId = useProjectStore((s) => s.projectId);
  const activeSceneId = useProjectStore((s) => s.activeSceneId);
  const setProject = useProjectStore((s) => s.setProject);
  const setScenes = useProjectStore((s) => s.setScenes);
  const resetAll = useProjectStore((s) => s.resetAll);

  useEffect(() => {
    const requestedId = new URLSearchParams(window.location.search).get("project");
    if (requestedId && !projectId) resumeProject(requestedId).catch(console.error);
  }, [projectId]);

  useEffect(() => {
    async function restoreProjectState() { if (!projectId) return; try { setProject(await api.getProject(projectId)); setScenes(await api.getSceneDetails(projectId)); } catch (error) { console.warn("Failed to auto-restore project:", error); resetAll(); } }
    restoreProjectState();
  }, [projectId, setProject, setScenes, resetAll]);

  useEffect(() => { if (projectId) saveSession({ projectId, screen, activeSceneId: activeSceneId ?? null }); else clearSession(); }, [projectId, screen, activeSceneId]);

  if (isRehydrating) return <div className="flex min-h-[60vh] items-center justify-center bg-[#0b0f19]"><div className="animate-pulse text-sm text-gray-400">Đang khôi phục phiên làm việc...</div></div>;

  return <>
    <div className="fixed right-4 top-20 z-40 flex items-center gap-3">
      {onExitEditor && <button onClick={onExitEditor} className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-semibold text-slate-200 shadow-lg transition-all hover:bg-slate-800">🏠 Trang chủ</button>}
      {projectId && <button onClick={resetAll} className="rounded-full border border-purple-800/40 bg-purple-950/60 px-3 py-1.5 text-xs font-medium text-purple-200 transition-all hover:bg-purple-900">✨ Tạo Dự Án Mới</button>}
      <button onClick={() => setShowDashboard(true)} className="rounded-full border border-slate-700 bg-slate-900 px-4 py-1.5 text-xs font-semibold text-slate-200 shadow-lg transition-all hover:bg-slate-800">📁 Quản Lý Kênh & Dự Án</button>
    </div>
    <NavigationHeader onOpenAssembly={() => setShowAssembly(true)} />
    <ScreenRouter />
    <AssemblyModal isOpen={showAssembly} onClose={() => setShowAssembly(false)} />
    <ChannelDashboard isOpen={showDashboard} onClose={() => setShowDashboard(false)} onResumeProject={(pid) => resumeProject(pid).catch(console.error)} />
  </>;
}
