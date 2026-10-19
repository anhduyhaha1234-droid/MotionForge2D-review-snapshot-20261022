"use client";

import type { LucideIcon } from "lucide-react";
import { AlertTriangle, Check, CheckCircle2, Clapperboard, Layers, Play, Upload, Wand2, X } from "lucide-react";
import { useProjectStore } from "@/stores/project";

/**
 * App screens owned by the legacy workspace (ScreenA→E). StageRail maps each
 * production stage to one of these screen/domain states (AC2).
 */
export type StageScreen = "start" | "selection" | "review" | "replacement" | "render";

export interface Stage {
  /** Unique display id (AC2 — duplicated screen mappings keep unique keys). */
  key: string;
  label: string;
  icon: LucideIcon;
  /** Existing application screen this stage drives (null = no screen yet). */
  screen: StageScreen | null;
  /** Durable domain state persisted as the project `resume_step` (AC4/AC5). */
  resumeStep: string;
  /** Accessible reason/tool-tip shown while the stage is not reachable (AC3). */
  disabledReason: string;
}

/**
 * The exact six production stages (UI_UX_DESIGN_STANDARD §Product intent).
 *
 * `demo` and `apply` both drive the `replacement` screen — duplicated screen
 * mapping, so they keep unique display ids (`key`) and unique resume_step
 * domain states (`demo_approved` / `applying_reskin`).
 */
export const PRODUCTION_STAGES: Stage[] = [
  {
    key: "import",
    label: "Nhập video",
    icon: Upload,
    screen: "start",
    resumeStep: "imported",
    disabledReason: "Tạo dự án và thêm video nguồn để bắt đầu.",
  },
  {
    key: "objects",
    label: "Đối tượng",
    icon: Layers,
    screen: "selection",
    resumeStep: "objects_ready",
    disabledReason: "Hoàn thành bước Nhập video để chọn đối tượng.",
  },
  {
    key: "demo",
    label: "Demo thay thế",
    icon: Wand2,
    screen: "replacement",
    resumeStep: "demo_approved",
    disabledReason: "Chọn đối tượng trước khi tạo demo thay thế.",
  },
  {
    key: "apply",
    label: "Áp dụng",
    icon: Play,
    screen: "replacement",
    resumeStep: "applying_reskin",
    disabledReason: "Duyệt demo thay thế trước khi áp dụng toàn video.",
  },
  {
    key: "review",
    label: "Kiểm tra",
    icon: CheckCircle2,
    screen: "review",
    resumeStep: "needs_review",
    disabledReason: "Áp dụng thay thế trước khi kiểm tra kết quả.",
  },
  {
    key: "export",
    label: "Xuất 4K",
    icon: Clapperboard,
    screen: "render",
    resumeStep: "ready_to_export",
    disabledReason: "Hoàn tất kiểm tra trước khi xuất video 4K.",
  },
];

/**
 * AUTHORITATIVE current-stage mapping keyed by the durable `resume_step`.
 *
 * Each production stage carries a unique `resumeStep`, so this mapping is
 * one-to-one and can never conflate the duplicated `replacement` screen
 * mapping (`demo` → `demo_approved`, `apply` → `applying_reskin`). The rail
 * uses this as its primary resolution so every stage — including
 * `Áp dụng` — becomes current/reachable exactly when the durable workflow
 * reaches its resume_step.
 */
export function stageIndexForResumeStep(resumeStep: string | null): number | null {
  if (!resumeStep) return null;
  const index = PRODUCTION_STAGES.findIndex((stage) => stage.resumeStep === resumeStep);
  return index === -1 ? null : index;
}

/**
 * Legacy fallback: screen → stage mapping (AC2). Returns the FIRST stage
 * driving the given screen. Because `demo` and `apply` share the
 * `replacement` screen, this cannot distinguish them — it is only used when
 * no authoritative durable resume_step is known.
 */
export function stageIndexForScreen(screen: StageScreen | null): number {
  if (!screen) return 0;
  const index = PRODUCTION_STAGES.findIndex((stage) => stage.screen === screen);
  return index === -1 ? 0 : index;
}

export function StageRail({
  currentIndex,
  stages = PRODUCTION_STAGES,
  dense = false,
}: {
  currentIndex?: number;
  stages?: Stage[];
  dense?: boolean;
}) {
  const projectId = useProjectStore((s) => s.projectId);
  const screen = useProjectStore((s) => s.screen);
  const setScreen = useProjectStore((s) => s.setScreen);
  const persistResumeStep = useProjectStore((s) => s.persistResumeStep);
  const resumeStep = useProjectStore((s) => s.resumeStep);
  const resumeError = useProjectStore((s) => s.resumeError);
  const retryResumeStep = useProjectStore((s) => s.retryResumeStep);
  const clearResumeError = useProjectStore((s) => s.clearResumeError);

  // Resolution order: an explicit prop (legacy call site) wins; otherwise the
  // AUTHORITATIVE durable resume_step mapping (unique per stage — so
  // `Áp dụng`/applying_reskin can become current); screen inference is the
  // last-resort fallback when no durable position is known.
  const activeIndex =
    currentIndex ?? stageIndexForResumeStep(resumeStep) ?? stageIndexForScreen(screen);

  const navigateToStage = (stage: Stage, index: number) => {
    // AC3 — users may navigate only to the current or completed stages.
    if (index > activeIndex || !projectId) return;
    if (stage.screen) setScreen(stage.screen);
    // AC4/AC5/AC6 — durable resume position through the typed client;
    // legacy/non-UUID ids are guarded inside the store action.
    void persistResumeStep(projectId, stage.resumeStep);
  };

  return (
    <>
      <ol
        role="list"
        aria-label="Tiến trình sản xuất"
        className="flex min-h-14 items-center overflow-x-auto border-b border-[var(--surface-800)] bg-[var(--surface-850)] px-4 py-2"
      >
        {stages.map(({ key, label, icon: Icon }, index) => {
          const done = index < activeIndex;
          const current = index === activeIndex;
          const reachable = index <= activeIndex && !!projectId;
          const stageLabel = reachable ? `Đi tới bước ${label}` : `${label} — chưa mở: ${stages[index].disabledReason}`;
          return (
            <li
              key={key}
              aria-current={current ? "step" : undefined}
              className="flex min-w-0 flex-1 items-center last:flex-none"
            >
              <button
                type="button"
                onClick={() => navigateToStage(stages[index], index)}
                aria-disabled={!reachable}
                aria-label={stageLabel}
                title={reachable ? `Đi tới bước ${label}` : stages[index].disabledReason}
                className={`flex min-h-11 shrink-0 cursor-pointer items-center gap-2 rounded-full border-0 bg-transparent px-3 text-xs font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary-300)] ${
                  current
                    ? "bg-[var(--primary-700)] text-white shadow-glow ring-1 ring-[var(--primary-300)]"
                    : done
                      ? "text-[var(--text-primary)] hover:bg-[var(--surface-800)]"
                      : "cursor-not-allowed text-[var(--text-faint)]"
                }`}
              >
                {done ? <Check size={17} className="text-[var(--primary-300)]" /> : <Icon size={17} />}
                {!dense && <span className="whitespace-nowrap">{label}</span>}
              </button>
              {index < stages.length - 1 && (
                <span
                  aria-hidden="true"
                  className={`mx-2 h-px min-w-4 flex-1 ${done ? "bg-[var(--primary-500)]" : "bg-[var(--surface-700)]"}`}
                />
              )}
            </li>
          );
        })}
      </ol>
      {/* Visible persistence failure — accessible live alert with retry/clear
          (never store-only). Rendered right below the rail in the shell. */}
      {resumeError && (
        <div
          role="alert"
          className="flex flex-wrap items-center gap-3 border-b border-[var(--surface-700)] bg-[var(--surface-800)] px-4 py-2 text-xs"
        >
          <AlertTriangle size={16} className="shrink-0 text-[var(--danger)]" aria-hidden="true" />
          <span className="min-w-0 flex-1 text-[var(--text-secondary)]">{resumeError}</span>
          <button
            type="button"
            onClick={() => void retryResumeStep()}
            className="min-h-8 rounded-lg bg-[var(--surface-700)] px-3 font-medium text-[var(--text-primary)] hover:bg-[var(--primary-700)] hover:text-white"
          >
            Thử lại
          </button>
          <button
            type="button"
            onClick={clearResumeError}
            aria-label="Đóng cảnh báo lưu bước tiếp tục"
            className="grid size-8 place-items-center rounded-lg text-[var(--text-muted)] hover:bg-[var(--surface-700)] hover:text-[var(--text-primary)]"
          >
            <X size={15} aria-hidden="true" />
          </button>
        </div>
      )}
    </>
  );
}
