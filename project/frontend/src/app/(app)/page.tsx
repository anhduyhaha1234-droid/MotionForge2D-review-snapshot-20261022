"use client";

import { useState } from "react";
import { Dashboard } from "@/components/Dashboard";
import { LegacyWorkspace } from "@/components/LegacyWorkspace";
import { StageRail } from "@/components/layout/StageRail";
import { useProjectStore } from "@/stores/project";

export default function HomePage() {
  const projectId = useProjectStore((s) => s.projectId);
  // Landing mode: the real dashboard is mounted at the home route. The
  // existing editor workflow stays reachable — either through an active
  // project (rail + workspace), or through the explicit workspace entry
  // (ScreenA create/upload) from the dashboard.
  const [showWorkspace, setShowWorkspace] = useState(false);
  const inEditor = !!projectId || showWorkspace;

  if (inEditor) {
    return (
      <div className="flex min-h-full flex-col">
        {projectId && <StageRail />}
        <LegacyWorkspace
          onExitEditor={showWorkspace && !projectId ? () => setShowWorkspace(false) : undefined}
        />
      </div>
    );
  }
  return <Dashboard onEnterEditor={() => setShowWorkspace(true)} />;
}
