/**
 * MotionForge 2D — Zustand Store (Persisted)
 *
 * Global state for the active project with localStorage persistence.
 */

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { isUuid, patchDurableProject } from "@/lib/api";
import type {
  ProjectData,
  TrackedObject,
  SelectionInput,
  ReplacementConfig,
  JobInfo,
  GalleryManifest,
  FrameMotion,
  SceneDetail,
} from "@/lib/api";

type Screen = "start" | "selection" | "review" | "replacement" | "render";

type PreviewMode = "original" | "mask" | "result" | "comparison";

interface ProjectState {
  // Project
  projectId: string | null;
  project: ProjectData | null;
  screen: Screen;

  // Selection
  currentFrame: number;
  selection: SelectionInput | null;
  maskPreview: string | null; // base64 PNG

  // Object
  activeObject: TrackedObject | null;
  gallery: GalleryManifest | null;

  // Replacement
  replacement: ReplacementConfig;

  // Preview
  previewMode: PreviewMode;
  frameMotion: FrameMotion | null;

  // Jobs
  activeJobs: Record<string, JobInfo>;

  // Scenes
  scenes: SceneDetail[];
  activeSceneId: number | null;

  // Channel
  activeChannelId: string | null;

  // Durable resume persistence (revision/CAS token + visible errors)
  durableRevision: number | null;
  resumeError: string | null;
  /** Authoritative current durable resume_step (unique per production stage). */
  resumeStep: string | null;
  /** Last step attempted through persistResumeStep — used by the retry path. */
  lastResumeStep: string | null;
  setDurableRevision: (revision: number | null) => void;
  clearResumeError: () => void;
  setResumeStep: (resumeStep: string | null) => void;
  retryResumeStep: () => Promise<void>;
  persistResumeStep: (projectId: string, resumeStep: string | null) => Promise<void>;

  // Persisted screen for rehydration
  persistedScreen: Screen | null;
  setPersistedScreen: (screen: Screen | null) => void;

  // Actions
  setProjectId: (id: string | null) => void;
  setProject: (data: ProjectData | null) => void;
  setScreen: (screen: Screen) => void;
  setCurrentFrame: (frame: number) => void;
  setSelection: (sel: SelectionInput | null) => void;
  setMaskPreview: (png: string | null) => void;
  setActiveObject: (obj: TrackedObject | null) => void;
  setGallery: (g: GalleryManifest | null) => void;
  setReplacement: (r: Partial<ReplacementConfig>) => void;
  resetReplacement: () => void;
  setPreviewMode: (mode: PreviewMode) => void;
  setFrameMotion: (motion: FrameMotion | null) => void;
  updateJob: (job: JobInfo) => void;
  removeJob: (id: string) => void;
  setScenes: (scenes: SceneDetail[]) => void;
  setActiveSceneId: (id: number | null) => void;
  setActiveChannelId: (id: string | null) => void;
  resetAll: () => void;
}

const DEFAULT_REPLACEMENT: ReplacementConfig = {
  mode: "none",
  asset_path: null,
  anchor: { x: 0.5, y: 0.5 },
  offset: { x: 0, y: 0 },
  scale: 1.0,
  rotation_offset_deg: 0,
  opacity: 1.0,
  fit_mode: "contain",
  clip_mode: "asset_alpha",
};

export const useProjectStore = create<ProjectState>()(
  persist(
    (set, get) => ({
      projectId: null,
      project: null,
      screen: "start",
      currentFrame: 0,
      selection: null,
      maskPreview: null,
      activeObject: null,
      gallery: null,
      replacement: { ...DEFAULT_REPLACEMENT },
      previewMode: "result",
      frameMotion: null,
      activeJobs: {},

      scenes: [],
      activeSceneId: null,

      activeChannelId: null,

      durableRevision: null,
      resumeError: null,
      resumeStep: null,
      lastResumeStep: null,
      setDurableRevision: (revision) => set({ durableRevision: revision }),
      clearResumeError: () => set({ resumeError: null }),
      setResumeStep: (resumeStep) => set({ resumeStep }),
      retryResumeStep: async () => {
        const { projectId, lastResumeStep } = get();
        if (!projectId || lastResumeStep === null) return;
        await get().persistResumeStep(projectId, lastResumeStep);
      },
      persistResumeStep: async (projectId, resumeStep) => {
        // AC6 — legacy/non-UUID project ids are never sent to the durable
        // UUID-constrained endpoint (silent no-op; nothing to persist).
        if (!projectId || !isUuid(projectId)) return;
        set({ lastResumeStep: resumeStep });
        try {
          // AC4/AC5 — typed client PATCH with the required revision; a 409 is
          // refetched+retried inside patchDurableProject. Success keeps the
          // fresh revision, records the authoritative resume_step and clears
          // any prior visible error.
          const fresh = await patchDurableProject(
            projectId,
            { resume_step: resumeStep },
            get().durableRevision,
          );
          set({ durableRevision: fresh.revision, resumeError: null, resumeStep });
        } catch (err) {
          // Never swallow persistence failure silently — surface it visibly.
          const detail = err instanceof Error ? err.message : String(err);
          set({ resumeError: `Không thể lưu bước tiếp tục: ${detail}` });
        }
      },

      persistedScreen: null,
      setPersistedScreen: (screen) => set({ persistedScreen: screen }),

      setProjectId: (id) => set({ projectId: id }),
      setProject: (data) => set({ project: data }),
      setScreen: (screen) => set({ screen }),
      setCurrentFrame: (frame) => set({ currentFrame: frame }),
      setSelection: (sel) => set({ selection: sel }),
      setMaskPreview: (png) => set({ maskPreview: png }),
      setActiveObject: (obj) => set({ activeObject: obj }),
      setGallery: (g) => set({ gallery: g }),
      setReplacement: (r) =>
        set((s) => ({ replacement: { ...s.replacement, ...r } })),
      resetReplacement: () => set({ replacement: { ...DEFAULT_REPLACEMENT } }),
      setPreviewMode: (mode) => set({ previewMode: mode }),
      setFrameMotion: (motion) => set({ frameMotion: motion }),
      updateJob: (job) =>
        set((s) => ({ activeJobs: { ...s.activeJobs, [job.job_id]: job } })),
      removeJob: (id) =>
        set((s) => {
          const jobs = { ...s.activeJobs };
          delete jobs[id];
          return { activeJobs: jobs };
        }),
      setScenes: (scenes) => set({ scenes }),
      setActiveSceneId: (id) => set({ activeSceneId: id }),
      setActiveChannelId: (id) => set({ activeChannelId: id }),

      resetAll: () =>
        set({
          projectId: null,
          project: null,
          screen: "start",
          currentFrame: 0,
          selection: null,
          maskPreview: null,
          activeObject: null,
          gallery: null,
          replacement: { ...DEFAULT_REPLACEMENT },
          previewMode: "result",
          frameMotion: null,
          activeJobs: {},
          scenes: [],
          activeSceneId: null,
          durableRevision: null,
          resumeError: null,
          resumeStep: null,
          lastResumeStep: null,
        }),
    }),
    {
      name: "motionforge-project-storage",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        projectId: state.projectId,
        screen: state.screen,
        activeSceneId: state.activeSceneId,
        activeChannelId: state.activeChannelId,
      }),
    }
  )
);
