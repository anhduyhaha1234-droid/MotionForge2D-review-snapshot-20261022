"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useProjectStore } from "@/stores/project";

interface Props {
  onPresetApplied?: () => void;
}

export function PresetManager({ onPresetApplied }: Props) {
  const projectId = useProjectStore((s) => s.projectId);
  const queryClient = useQueryClient();
  const [presetName, setPresetName] = useState("");
  const [showSave, setShowSave] = useState(false);

  const { data: presets = [] } = useQuery({
    queryKey: ["presets", projectId],
    queryFn: () => api.listPresets(projectId!),
    enabled: !!projectId,
  });

  const saveMut = useMutation({
    mutationFn: () => api.savePreset(projectId!, presetName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["presets", projectId] });
      setPresetName("");
      setShowSave(false);
    },
  });

  const applyMut = useMutation({
    mutationFn: (filename: string) => api.applyPreset(projectId!, filename),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scenes", projectId] });
      onPresetApplied?.();
    },
  });

  return (
    <div className="flex flex-col gap-3 p-3 bg-gray-900 rounded">
      <h4 className="text-sm font-medium text-gray-300">
        📋 Preset Manager
      </h4>

      {/* Load preset */}
      {presets.length > 0 && (
        <div>
          <p className="text-xs text-gray-400 mb-1">Tải Preset:</p>
          <div className="flex flex-col gap-1">
            {presets.map((preset) => (
              <div
                key={preset.filename}
                className="flex items-center justify-between px-2 py-1.5
                  bg-gray-800 rounded text-xs"
              >
                <div>
                  <span className="text-gray-300">{preset.name}</span>
                  <span className="text-gray-500 ml-2">
                    ({preset.mapping_count} mappings)
                  </span>
                </div>
                <button
                  onClick={() => applyMut.mutate(preset.filename)}
                  disabled={applyMut.isPending}
                  className="px-2 py-0.5 bg-blue-600 hover:bg-blue-500
                    rounded text-[10px] disabled:bg-gray-700"
                >
                  Áp dụng
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {presets.length === 0 && (
        <p className="text-xs text-gray-500">Chưa có preset nào</p>
      )}

      {/* Save preset */}
      <div className="border-t border-gray-700 pt-2">
        {!showSave ? (
          <button
            onClick={() => setShowSave(true)}
            className="w-full py-1.5 text-xs bg-gray-700 hover:bg-gray-600
              rounded transition-colors"
          >
            💾 Lưu Preset mới
          </button>
        ) : (
          <div className="flex gap-2">
            <input
              type="text"
              value={presetName}
              onChange={(e) => setPresetName(e.target.value)}
              placeholder="Tên preset..."
              className="flex-1 px-2 py-1 bg-gray-800 border border-gray-700
                rounded text-xs"
            />
            <button
              onClick={() => saveMut.mutate()}
              disabled={!presetName || saveMut.isPending}
              className="px-3 py-1 bg-green-600 hover:bg-green-500
                rounded text-xs disabled:bg-gray-700"
            >
              Lưu
            </button>
            <button
              onClick={() => setShowSave(false)}
              className="px-2 py-1 bg-gray-700 rounded text-xs"
            >
              ✕
            </button>
          </div>
        )}
      </div>

      {/* Status */}
      {applyMut.isSuccess && (
        <p className="text-xs text-green-300">
          ✅ Đã áp dụng! ({applyMut.data.updated_objects} objects updated)
        </p>
      )}
      {saveMut.isSuccess && (
        <p className="text-xs text-green-300">
          ✅ Đã lưu! ({saveMut.data.mapping_count} mappings)
        </p>
      )}
    </div>
  );
}
