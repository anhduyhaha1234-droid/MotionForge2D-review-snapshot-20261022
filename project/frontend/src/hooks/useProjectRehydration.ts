"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useProjectStore } from "@/stores/project";

const STORAGE_KEY = "motionforge_session";

interface SessionData {
  projectId: string;
  screen: string;
  activeSceneId: number | null;
  timestamp: number;
}

export function saveSession(data: Omit<SessionData, "timestamp">) {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ ...data, timestamp: Date.now() }),
    );
  } catch {
    // localStorage may be full or unavailable
  }
}

export function clearSession() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
}

export function loadSession(): SessionData | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as SessionData;
    // Expire after 7 days
    if (Date.now() - data.timestamp > 7 * 24 * 60 * 60 * 1000) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return data;
  } catch {
    return null;
  }
}

export function useProjectRehydration() {
  const [isRehydrating, setIsRehydrating] = useState(true);
  const setProject = useProjectStore((s) => s.setProject);
  const setProjectId = useProjectStore((s) => s.setProjectId);
  const setScreen = useProjectStore((s) => s.setScreen);
  const setActiveSceneId = useProjectStore((s) => s.setActiveSceneId);

  useEffect(() => {
    const session = loadSession();
    if (!session?.projectId) {
      // No stored session: nothing to rehydrate. Defer the state flip out of
      // the effect body (React Compiler: no synchronous setState in effects).
      queueMicrotask(() => setIsRehydrating(false));
      return;
    }

    // Rehydrate from localStorage
    api
      .getProject(session.projectId)
      .then((proj) => {
        setProjectId(session.projectId);
        setProject(proj);
        setActiveSceneId(session.activeSceneId);
        setScreen(session.screen as Parameters<typeof setScreen>[0]);
      })
      .catch(() => {
        // Project no longer exists, clear session
        clearSession();
      })
      .finally(() => {
        setIsRehydrating(false);
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return { isRehydrating };
}
