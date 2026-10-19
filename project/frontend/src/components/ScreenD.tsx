"use client";

/**
 * ScreenD — Replacement & Composite Preview
 *
 * 3-column layout:
 * Left:   objects & library (cards + upload + frame slider)
 * Center: Konva composite canvas
 * Right:  4 transform sliders + apply-all action + scene/dubbing panels
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useProjectStore } from "@/stores/project";
import { CompositeCanvas } from "@/components/CompositeCanvas";
import { SceneSelector } from "./SceneSelector";
import { ScenePreview } from "./ScenePreview";
import { DubbingPanel } from "./DubbingPanel";

/* ── Preview mode labels (Vietnamese) ──────────────────────────────────── */

const PREVIEW_MODES = [
  { value: "original" as const, label: "Ảnh gốc" },
  { value: "mask" as const, label: "Mask" },
  { value: "result" as const, label: "Kết quả" },
  { value: "comparison" as const, label: "So sánh" },
];

/* ── Slider helper ─────────────────────────────────────────────────────── */

function Slider({
  label,
  caption,
  value,
  min,
  max,
  step,
  unit,
  onChange,
}: {
  label: string;
  caption?: string;
  value: number;
  min: number;
  max: number;
  step: number;
  unit?: string;
  onChange: (v: number) => void;
}) {
  return (
    <div>
      <div className="flex items-center justify-between">
        <label className="text-xs text-gray-300">{label}</label>
        <span className="text-xs text-gray-500 font-mono">
          {unit === "°"
            ? `${value}${unit}`
            : unit === "x"
              ? `${value.toFixed(2)}${unit}`
              : unit === "%"
                ? `${Math.round(value * 100)}${unit}`
                : value.toFixed(2)}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full"
      />
      {caption && <p className="text-[10px] text-gray-600 -mt-1">{caption}</p>}
    </div>
  );
}

/* ── Main Component ────────────────────────────────────────────────────── */

export function ScreenD() {
  const {
    projectId,
    project,
    activeObject,
    setActiveObject,
    currentFrame,
    setCurrentFrame,
    replacement,
    setReplacement,
    resetReplacement,
    previewMode,
    setPreviewMode,
    frameMotion,
    setFrameMotion,
    setScreen,
  } = useProjectStore();

  const queryClient = useQueryClient();
  const activeSceneId = useProjectStore((s) => s.activeSceneId);

  /* ── Auto-select first object ───────────────────────────────────────── */

  useEffect(() => {
    if (!activeObject && project?.objects?.length) {
      setActiveObject(project.objects[0]);
    }
  }, [activeObject, project, setActiveObject]);

  const approveSceneMut = useMutation({
    mutationFn: () => {
      if (!projectId || activeSceneId === null) return Promise.resolve({ ok: false });
      return api.updateSceneStatus(projectId, activeSceneId, "approved");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scenes", projectId] });
    },
  });

  const objectId = activeObject?.object_id;
  const meta = project?.video_metadata;
  const videoWidth = meta?.width ?? 1920;
  const videoHeight = meta?.height ?? 1080;
  const totalFrames = meta?.total_frames ?? 1;

  const sceneCount =
    project?.scene_details?.length ?? project?.scenes?.length ?? 0;

  /* ── Frame motion data ──────────────────────────────────────────────── */

  // Derive frame motion from activeObject when frame changes
  useEffect(() => {
    if (!activeObject?.motion?.frames) {
      setFrameMotion(null);
      return;
    }
    const frames = activeObject.motion.frames;
    const fm = frames.find((f) => f.frame_index === currentFrame) ?? null;
    setFrameMotion(fm);
  }, [activeObject, currentFrame, setFrameMotion]);

  /* ── Frame URL ──────────────────────────────────────────────────────── */

  const frameUrl = projectId ? api.getFrameUrl(projectId, currentFrame) : null;

  /* ── Mask URL ───────────────────────────────────────────────────────── */

  const maskUrl =
    projectId && objectId
      ? api.getMaskImageUrl(projectId, objectId, currentFrame)
      : null;

  /* ── Replacement image URL ──────────────────────────────────────────── */

  // Cache-bust: append a nonce + asset_path version so the browser never
  // serves a stale replacement image after a new upload. The nonce is bumped
  // after uploads/preset applies (never during render — keeps render pure).
  const [reloadNonce, setReloadNonce] = useState(0);
  const replacementUrl =
    projectId && objectId && replacement.asset_path
      ? `${api.getReplacementImageUrl(projectId, objectId)}?t=${reloadNonce}&v=${encodeURIComponent(replacement.asset_path)}`
      : null;

  // Inpainted (background-cleaned) frame URL — shows the scene with the
  // original character removed as the base layer.
  const inpaintedUrl =
    projectId && objectId
      ? `${api.getInpaintedFrameUrl(projectId, objectId, currentFrame)}?t=${reloadNonce}`
      : null;

  // Preview flow: store file locally, show side-by-side modal, upload only on confirm
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [pendingPreview, setPendingPreview] = useState<string | null>(null);

  // Confirmed replacement state (outer banner feedback)
  const [confirmedReplacement, setConfirmedReplacement] = useState<{
    originalName: string;
    newFileName: string;
    previewUrl: string;
  } | null>(null);

  // Apply processing state & progress modal
  const [isApplying, setIsApplying] = useState(false);
  const [applyProgress, setApplyProgress] = useState(0);
  const [applyMessage, setApplyMessage] = useState("");

  // Character preset library UI state
  const [showCharLibrary, setShowCharLibrary] = useState(false);

  const charPresets = useQuery({
    queryKey: ["character-presets"],
    queryFn: api.listCharacterPresets,
    staleTime: 5 * 60 * 1000,
  });

  const presetMut = useMutation({
    mutationFn: ({ setKey, pose }: { setKey: string; pose: string }) => {
      if (!projectId) throw new Error("No project");
      return api.applyCharacterPreset(projectId, setKey, pose);
    },
    onSuccess: (data) => {
      // Update the replacement state so canvas redraws the new pose asset
      setReplacement({
        mode: "static_asset",
        asset_path: data.asset_path,
      });
      setReloadNonce((n) => n + 1);
      setConfirmedReplacement({
        originalName: activeObject?.name ?? "Nhân vật gốc",
        newFileName: `🎭 ${data.set_key}/${data.pose}`,
        previewUrl: "",
      });
    },
  });

  const handleApplyPreset = (setKey: string, pose: string) => {
    presetMut.mutate({ setKey, pose });
  };

  /* ── Upload mutation ────────────────────────────────────────────────── */

  const uploadMut = useMutation({
    mutationFn: async (file: File) => {
      if (!projectId || !objectId) throw new Error("No project/object");
      const result = await api.uploadReplacement(projectId, objectId, file);
      setReplacement({ mode: "static_asset", asset_path: result.asset_path });
      return result;
    },
    onSuccess: () => {
      // Save confirmation state for outer banner feedback
      if (activeObject && pendingFile && pendingPreview) {
        setConfirmedReplacement({
          originalName: activeObject.name || "Nhân vật gốc",
          newFileName: pendingFile.name,
          previewUrl: pendingPreview,
        });
      }
      // Bump nonce so the new replacement image is fetched fresh (cache-bust)
      setReloadNonce((n) => n + 1);
      // Close modal + clear pending preview
      setPendingFile(null);
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    // Step 1: save file locally + create preview URL (no upload yet)
    setPendingFile(file);
    setPendingPreview(URL.createObjectURL(file));
    // Reset input so selecting the same file again re-triggers
    e.target.value = "";
  };

  const handleCancelPreview = () => {
    if (pendingPreview) URL.revokeObjectURL(pendingPreview);
    setPendingFile(null);
    setPendingPreview(null);
  };

  const handleConfirmReplace = () => {
    if (!pendingFile) return;
    // Close the compare modal IMMEDIATELY (no hanging)
    setPendingPreview(null);
    // Switch canvas to result mode so the new character is drawn
    setPreviewMode("result");
    // Kick off the upload; onSuccess updates replacement + shows banner
    uploadMut.mutate(pendingFile);
    // Keep pendingFile for onSuccess banner (cleared there)
  };

  /* ── Settings mutation & Apply All ──────────────────────────────────── */

  const settingsMut = useMutation({
    mutationFn: async () => {
      if (!projectId || !objectId) throw new Error("No project/object");
      return api.updateReplacementSettings(projectId, objectId, {
        mode: replacement.mode,
        asset_path: replacement.asset_path,
        anchor: replacement.anchor,
        offset: replacement.offset,
        scale: replacement.scale,
        rotation_offset_deg: replacement.rotation_offset_deg,
        opacity: replacement.opacity,
        fit_mode: replacement.fit_mode,
        clip_mode: replacement.clip_mode,
        frameSequenceDir: replacement.frameSequenceDir,
        frameSequenceFps: replacement.frameSequenceFps,
      });
    },
  });

  // ── Auto-save settings on slider change (debounced 500ms) ──────────────
  // Every transform tweak persists to the backend so the config survives
  // reloads; "Áp dụng" then broadcasts the canonical config to all scenes.
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (!projectId || !objectId) return;
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(() => {
      settingsMut.mutate();
    }, 500);
    return () => {
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    replacement.scale,
    replacement.rotation_offset_deg,
    replacement.offset.x,
    replacement.offset.y,
    replacement.opacity,
    projectId,
    objectId,
  ]);

  const handleApplySettings = async () => {
    if (!projectId || !objectId) return;
    try {
      setIsApplying(true);
      setApplyProgress(10);
      setApplyMessage("Đang lưu vị trí và cấu hình nhân vật...");

      await settingsMut.mutateAsync();

      setApplyProgress(40);
      setApplyMessage("Đang tự động khớp & áp dụng nhân vật mới cho tất cả phân cảnh...");

      // Soft try/catch: auto-match may return warnings but should not block
      try {
        const result = await api.autoMatchCharacter(projectId, objectId);
        setApplyMessage(
          `Hoàn tất áp dụng cho ${result.count} phân cảnh! Đang đồng bộ hóa...`,
        );
      } catch (matchErr) {
        // Non-fatal: keep going even if auto-match warns/fails
        setApplyMessage(
          `Đã lưu cấu hình (auto-match: ${(matchErr as Error).message}). Đang hoàn tất...`,
        );
      }

      setApplyProgress(80);
      setApplyMessage("Đang đồng bộ hóa dữ liệu...");

      await new Promise((resolve) => setTimeout(resolve, 600));

      setApplyProgress(100);
      setApplyMessage("Thành công! Nhân vật mới đã sẵn sàng cho bước Render & Xuất Video.");

      await new Promise((resolve) => setTimeout(resolve, 500));
      setIsApplying(false);
    } catch (err) {
      setIsApplying(false);
      alert(`Lỗi khi áp dụng: ${(err as Error).message}`);
    }
  };

  /* ── Sequence frame URL ──────────────────────────────────────────────── */

  const sequenceFrameUrl =
    projectId && objectId && replacement.mode === "frame_sequence"
      ? api.getSequenceFrameUrl(projectId, objectId, currentFrame)
      : null;

  /* ── Frame slider helper ────────────────────────────────────────────── */

  const handleFrameChange = useCallback(
    (val: number) => {
      setCurrentFrame(val);
    },
    [setCurrentFrame],
  );

  /* ── Render ─────────────────────────────────────────────────────────── */

  return (
    <div className="flex flex-col h-screen">
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-900 border-b border-gray-800">
        <h2 className="text-sm font-medium">Thay thế vật thể</h2>
        <div className="flex items-center gap-3">
          {/* Preview mode selector */}
          <div className="flex gap-1">
            {PREVIEW_MODES.map((pm) => (
              <button
                key={pm.value}
                onClick={() => setPreviewMode(pm.value)}
                className={`px-2 py-1 text-xs rounded ${
                  previewMode === pm.value
                    ? "bg-blue-600 text-white"
                    : "bg-gray-800 text-gray-300 hover:bg-gray-700"
                }`}
              >
                {pm.label}
              </button>
            ))}
          </div>
          <button
            onClick={() => setScreen("review")}
            className="text-xs text-gray-400 hover:text-gray-200"
          >
            ← Quay lại kết quả
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* ── Left column: Objects & Library ─────────────────────────────── */}
        <div className="w-64 bg-gray-900 border-r border-gray-800 p-4 space-y-4 overflow-y-auto flex-shrink-0">
          <h3 className="text-xs text-gray-500 uppercase mb-2">
            🎭 Nhân vật đã tách
          </h3>
          <div className="space-y-2">
            {project?.objects?.map((obj) => (
              <button
                key={obj.object_id}
                onClick={() => setActiveObject(obj)}
                className={`w-full text-left p-2 rounded-lg border transition-colors ${
                  activeObject?.object_id === obj.object_id
                    ? "bg-purple-900/40 border-purple-500/50"
                    : "bg-gray-800/80 border-gray-700 hover:bg-gray-700/80"
                }`}
              >
                <div className="flex items-center gap-2">
                  <div className="w-12 h-12 bg-gray-900 rounded overflow-hidden flex-shrink-0">
                    {projectId && (
                      <img
                        src={api.getObjectCropUrl(projectId, obj.object_id)}
                        alt={obj.name}
                        className="w-full h-full object-contain bg-black/80 rounded border border-purple-500/50"
                        onError={(e) => {
                          // Fallback to thumbnail_base64 if available
                          const el = e.target as HTMLImageElement;
                          if (obj.thumbnail_base64) {
                            el.src = obj.thumbnail_base64;
                            el.onerror = null;
                          } else {
                            el.style.display = "none";
                          }
                        }}
                      />
                    )}
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-gray-200 truncate">
                      {obj.name}
                    </p>
                    <p className="text-[10px] text-gray-500">
                      Scene {obj.scene_id}
                    </p>
                  </div>
                </div>
              </button>
            ))}
            {!project?.objects?.length && (
              <p className="text-xs text-gray-600">
                Chưa có nhân vật nào. Vào Màn B để tách nhân vật.
              </p>
            )}
          </div>

          {/* 📸 Confirmed Adjustment Banner */}
          {(confirmedReplacement || replacement.asset_path) && (
            <div className="bg-purple-950/90 border border-purple-500/60 rounded-xl p-3 space-y-2 shadow-lg shadow-purple-950/40">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-purple-300 uppercase tracking-wider flex items-center gap-1">
                  <span>📸</span> ĐÃ XÁC NHẬN ĐIỀU CHỈNH
                </span>
                <button
                  onClick={() => setConfirmedReplacement(null)}
                  className="text-gray-400 hover:text-gray-200 text-xs px-1"
                  title="Đóng"
                >
                  ✕
                </button>
              </div>
              <div className="flex items-center gap-1.5 text-xs bg-purple-900/40 p-2 rounded-lg border border-purple-800/50">
                <span className="text-gray-300 font-medium truncate max-w-[90px]">
                  {confirmedReplacement?.originalName ?? activeObject?.name ?? "Nhân vật gốc"}
                </span>
                <span className="text-purple-400 font-bold">➔</span>
                <span className="text-purple-200 font-semibold truncate max-w-[90px]">
                  {confirmedReplacement?.newFileName ??
                    replacement.asset_path?.split("/").pop() ??
                    "Nhân vật mới"}
                </span>
              </div>
              <p className="text-[10px] text-purple-300/80 leading-tight">
                Nhấn nút <strong className="text-green-400">&quot;Áp dụng&quot;</strong> ở cột bên phải để hoàn tất thay đổi cho tất cả phân cảnh.
              </p>
            </div>
          )}

          <div className="border-t border-gray-700 pt-3 space-y-2">
            <label className="block w-full py-2 text-center text-xs bg-blue-600 hover:bg-blue-500 rounded cursor-pointer font-medium shadow transition-colors">
              📁 Tải Ảnh Nhân Vật Mới (PNG/JPG/WebP)
              <input
                type="file"
                accept="image/*,.png,.jpg,.jpeg,.webp"
                onChange={handleFileChange}
                className="hidden"
              />
            </label>
            {uploadMut.isPending && (
              <p className="text-xs text-yellow-400 text-center animate-pulse">
                ⏳ Đang tải lên & xử lý ảnh...
              </p>
            )}
            <button
              onClick={() => setShowCharLibrary((v) => !v)}
              className="w-full py-2 text-xs bg-purple-700 hover:bg-purple-600 rounded text-white font-medium"
            >
              🎭 Thư Viện Nhân Vật Mẫu Đa Tư Thế
            </button>

            {/* Character preset library */}
            {showCharLibrary && (
              <div className="space-y-3 pt-1">
                {charPresets.isLoading && (
                  <p className="text-xs text-gray-400 animate-pulse">
                    ⏳ Đang tải thư viện...
                  </p>
                )}
                {charPresets.error && (
                  <p className="text-xs text-red-400">
                    Không tải được thư viện: {(charPresets.error as Error).message}
                  </p>
                )}
                {charPresets.data?.characters.map((set) => (
                  <div
                    key={set.id}
                    className="bg-gray-800/70 rounded-lg p-2 border border-gray-700"
                  >
                    <p className="text-xs font-semibold text-purple-300 mb-1.5">
                      {set.label}
                    </p>
                    <div className="grid grid-cols-4 gap-1.5">
                      {set.poses.map((pose) => (
                        <button
                          key={pose.pose}
                          onClick={() => handleApplyPreset(set.id, pose.pose)}
                          disabled={presetMut.isPending}
                          className="flex flex-col items-center gap-0.5 p-1 bg-gray-700/60 hover:bg-purple-600/50 rounded transition-colors disabled:opacity-50"
                          title={pose.label}
                        >
                          <img
                            src={api.getCharacterPresetImageUrl(set.id, pose.pose)}
                            alt={pose.label}
                            className="w-9 h-9 object-contain"
                          />
                          <span className="text-[9px] text-gray-300 leading-none">
                            {pose.label}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Frame slider */}
          <div>
            <h3 className="text-xs text-gray-500 uppercase mb-2">
              Frame ({currentFrame}/{totalFrames - 1})
            </h3>
            <input
              type="range"
              min={0}
              max={totalFrames - 1}
              value={currentFrame}
              onChange={(e) => handleFrameChange(Number(e.target.value))}
              className="w-full"
              data-testid="frame-slider"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>0</span>
              <span>{totalFrames - 1}</span>
            </div>
          </div>
        </div>

        {/* ── Center: Konva canvas ───────────────────────────────────────── */}
        <div className="flex-1 flex items-center justify-center bg-gray-950 min-w-0">
          <CompositeCanvas
            frameUrl={frameUrl}
            maskUrl={maskUrl}
            inpaintedUrl={inpaintedUrl}
            replacementUrl={replacementUrl}
            sequenceFrameUrl={sequenceFrameUrl}
            frameMotion={frameMotion}
            replacement={replacement}
            videoWidth={videoWidth}
            videoHeight={videoHeight}
            previewMode={previewMode}
          />
        </div>

        {/* ── Right column: Transform controls ───────────────────────────── */}
        <div className="w-72 bg-gray-900 border-l border-gray-800 p-4 space-y-4 overflow-y-auto flex-shrink-0">
          <h3 className="text-xs text-gray-500 uppercase font-semibold text-purple-400">
            🎨 Điều chỉnh nhân vật
          </h3>

          {/* Scale */}
          <Slider
            label="🔍 Kích thước"
            caption="Phóng to / Thu nhỏ nhân vật mới"
            value={replacement.scale}
            min={0.1}
            max={3}
            step={0.05}
            unit="x"
            onChange={(v) => setReplacement({ scale: v })}
          />

          {/* Rotation */}
          <Slider
            label="🔄 Góc xoay"
            caption="Xoay nhân vật mới theo góc tùy chỉnh"
            value={replacement.rotation_offset_deg}
            min={-180}
            max={180}
            step={1}
            unit="°"
            onChange={(v) => setReplacement({ rotation_offset_deg: v })}
          />

          {/* Offset X */}
          <Slider
            label="↔️ Vị trí Ngang"
            caption="Dịch chuyển nhân vật sang trái / phải"
            value={replacement.offset.x}
            min={-0.5}
            max={0.5}
            step={0.01}
            onChange={(v) =>
              setReplacement({ offset: { ...replacement.offset, x: v } })
            }
          />

          {/* Offset Y */}
          <Slider
            label="↕️ Vị trí Dọc"
            caption="Dịch chuyển nhân vật lên / xuống"
            value={replacement.offset.y}
            min={-0.5}
            max={0.5}
            step={0.01}
            onChange={(v) =>
              setReplacement({ offset: { ...replacement.offset, y: v } })
            }
          />

          {/* 🚀 Apply to all scenes — save settings then auto-match */}
          <button
            onClick={handleApplySettings}
            disabled={isApplying || settingsMut.isPending}
            className="w-full py-3 text-sm bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-xl shadow-lg shadow-purple-900/40 transition-all disabled:bg-gray-700 disabled:text-gray-400"
            data-testid="apply-all-scenes"
          >
            🚀 Áp Dụng Nhân Vật Mới Cho Tất Cả {sceneCount} Cảnh
          </button>

          {/* Actions */}
          <div className="space-y-1 pt-2 border-t border-gray-800">
            <button
              onClick={handleApplySettings}
              disabled={isApplying || settingsMut.isPending}
              className="w-full py-2.5 text-sm bg-green-600 hover:bg-green-500 font-bold text-white disabled:bg-gray-800 disabled:text-gray-500 rounded transition-all shadow-md shadow-green-950/50 flex items-center justify-center gap-1.5"
              data-testid="apply-settings"
            >
              {isApplying ? (
                <>
                  <span className="animate-spin text-xs">🌀</span>
                  <span>Đang xử lý thay đổi...</span>
                </>
              ) : (
                <>
                  <span>✓</span>
                  <span>Áp dụng</span>
                </>
              )}
            </button>
            <p className="text-[11px] text-gray-400 mt-1">
              Lưu ảnh thay thế + tự động áp dụng nhân vật cho toàn bộ phân cảnh.
            </p>
            <button
              onClick={() => {
                resetReplacement();
                setConfirmedReplacement(null);
              }}
              className="w-full py-2 text-sm bg-gray-800 hover:bg-gray-700 rounded text-gray-300"
            >
              Đặt lại
            </button>
            <p className="text-[11px] text-gray-400 mt-1">
              Xóa ảnh thay thế, quay về ảnh nhân vật gốc.
            </p>
            <button
              onClick={() => setScreen("render")}
              disabled={!replacement.asset_path && !confirmedReplacement}
              className={`w-full py-2.5 text-sm font-semibold text-white rounded transition-colors shadow flex items-center justify-center gap-1 ${
                !replacement.asset_path && !confirmedReplacement
                  ? "bg-gray-700 text-gray-400 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-500"
              }`}
              data-testid="next-render"
            >
              <span>Tiếp: Render Video</span>
              <span>→</span>
            </button>
            <p className="text-[11px] text-gray-400 mt-1">
              Chuyển sang bước ghép voice & render video hoàn chỉnh.
            </p>
          </div>

          {/* Scene selector & preview */}
          <div className="border-t border-gray-700 pt-3 space-y-3">
            <SceneSelector />
            <ScenePreview />
            <button
              onClick={() => approveSceneMut.mutate()}
              disabled={activeSceneId === null || approveSceneMut.isPending}
              className="w-full py-2 bg-green-600 hover:bg-green-500
                disabled:bg-gray-700 disabled:text-gray-500
                rounded font-medium text-sm transition-colors"
            >
              ✅ Duyệt phân cảnh này
            </button>
          </div>

          {/* Dubbing Section */}
          <details className="border-t border-gray-700 pt-3" open>
            <summary className="text-sm font-semibold text-purple-300 cursor-pointer flex items-center gap-1">
              <span>🎙️ Lồng tiếng / Voice Dubbing</span>
            </summary>
            <div className="mt-2">
              <DubbingPanel />
            </div>
          </details>
        </div>
      </div>

      {/* ── Side-by-side comparison modal (preview before upload) ──────── */}
      {pendingPreview && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200"
          onClick={handleCancelPreview}
        >
          <div
            className="bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl w-full max-w-3xl p-6 space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-purple-300 flex items-center gap-1.5">
                <span>👀</span>
                <span>Đối Chiếu Nhân Vật — Xác Nhận Thay Thế</span>
              </h3>
              <button
                onClick={handleCancelPreview}
                className="text-gray-500 hover:text-gray-300 text-lg leading-none"
                title="Đóng"
              >
                ✕
              </button>
            </div>

            {/* Two-column comparison */}
            <div className="grid grid-cols-2 gap-4">
              {/* Left: original object */}
              <div className="space-y-2">
                <p className="text-xs text-gray-400 uppercase tracking-wide font-medium">
                  NHÂN VẬT GỐC (ĐANG CHỌN)
                </p>
                <div className="aspect-square bg-gray-800 rounded-xl overflow-hidden flex items-center justify-center border border-gray-700">
                  {projectId && objectId ? (
                    <img
                      src={api.getObjectCropUrl(projectId, objectId)}
                      alt="Nhân vật gốc"
                      className="w-full h-full object-contain"
                      onError={(e) => {
                        const el = e.target as HTMLImageElement;
                        el.style.display = "none";
                      }}
                    />
                  ) : (
                    <span className="text-gray-600 text-xs">Chưa có ảnh gốc</span>
                  )}
                </div>
                <p className="text-xs text-gray-400 font-medium truncate">
                  {activeObject?.name ?? "Nhân vật gốc"}
                </p>
              </div>

              {/* Right: new file preview */}
              <div className="space-y-2">
                <p className="text-xs text-purple-400 uppercase tracking-wide font-medium">
                  NHÂN VẬT MỚI
                </p>
                <div className="aspect-square bg-blue-950/40 rounded-xl overflow-hidden flex items-center justify-center border border-purple-500/60 shadow-inner">
                  <img
                    src={pendingPreview}
                    alt="Nhân vật mới"
                    className="w-full h-full object-contain"
                  />
                </div>
                <p className="text-xs text-purple-300 font-medium truncate">
                  📄 {pendingFile?.name ?? "File ảnh"}
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end gap-3 pt-2 border-t border-gray-800">
              <button
                onClick={handleCancelPreview}
                disabled={uploadMut.isPending}
                className="px-4 py-2 text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 rounded transition-colors disabled:opacity-50 font-medium"
              >
                Hủy
              </button>
              <button
                onClick={handleConfirmReplace}
                disabled={uploadMut.isPending}
                className="px-4 py-2.5 text-xs bg-purple-600 hover:bg-purple-500 rounded font-semibold text-white transition-colors disabled:opacity-60 disabled:cursor-not-allowed shadow-md shadow-purple-950/60 flex items-center gap-1.5"
                data-testid="confirm-replace"
              >
                {uploadMut.isPending ? (
                  <>
                    <span className="animate-spin">🌀</span>
                    <span>Đang tải lên...</span>
                  </>
                ) : (
                  <>
                    <span>✓</span>
                    <span>Xác Nhận Thay Thế</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Processing Overlay Modal (Loading screen when applying) ─────── */}
      {isApplying && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
          <div className="bg-gray-900 border border-purple-500/50 rounded-2xl shadow-2xl w-full max-w-md p-6 text-center space-y-4">
            <div className="w-16 h-16 mx-auto rounded-full bg-purple-950/80 border border-purple-500/60 flex items-center justify-center text-3xl animate-bounce">
              🎭
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-bold text-white">
                Đang xử lý thay đổi nhân vật
              </h3>
              <p className="text-xs text-purple-300 font-medium min-h-[32px] flex items-center justify-center">
                {applyMessage}
              </p>
            </div>
            <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden border border-gray-700">
              <div
                className="bg-gradient-to-r from-purple-600 via-blue-500 to-green-500 h-full transition-all duration-300 rounded-full"
                style={{ width: `${applyProgress}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-gray-400 font-mono">
              <span>Tiến trình</span>
              <span className="font-bold text-purple-400">{applyProgress}%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
