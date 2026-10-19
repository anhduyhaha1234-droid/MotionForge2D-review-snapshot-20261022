"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api, type DubbingSegment } from "@/lib/api";
import { useProjectStore } from "@/stores/project";

const LANGUAGES = [
  { code: "en", label: "English", voice: "en-US-AriaNeural" },
  { code: "es", label: "Español", voice: "es-ES-ElviraNeural" },
  { code: "fr", label: "Français", voice: "fr-FR-DeniseNeural" },
  { code: "de", label: "Deutsch", voice: "de-DE-KatjaNeural" },
  { code: "ja", label: "日本語", voice: "ja-JP-NanamiNeural" },
  { code: "ko", label: "한국어", voice: "ko-KR-SunHiNeural" },
  { code: "zh", label: "中文", voice: "zh-CN-XiaoxiaoNeural" },
];

export function DubbingPanel() {
  const projectId = useProjectStore((s) => s.projectId);
  const activeSceneId = useProjectStore((s) => s.activeSceneId);

  const [targetLang, setTargetLang] = useState("en");
  const [sourceLang, setSourceLang] = useState("vi");
  const [whisperModel, setWhisperModel] = useState("base");
  const [dubbingMode, setDubbingMode] = useState<"original" | "ai">("ai");
  const [segments, setSegments] = useState<DubbingSegment[]>([]);
  const [step, setStep] = useState<"idle" | "separating" | "transcribing" | "translating" | "tts" | "done">("idle");

  const selectedVoice = LANGUAGES.find((l) => l.code === targetLang)?.voice ?? "en-US-AriaNeural";

  // Full pipeline mutation
  const dubMut = useMutation({
    mutationFn: async () => {
      if (!projectId || activeSceneId === null) return;
      setStep("separating");

      // Step 1: Separate
      await api.separateAudio(projectId, activeSceneId);
      setStep("transcribing");

      // Step 2: Transcribe
      await api.transcribeScene(
        projectId, activeSceneId, sourceLang, whisperModel,
      );

      // Step 3: Translate
      setStep("translating");
      const translateResult = await api.translateSubtitles(
        projectId, activeSceneId, targetLang, sourceLang,
      );
      setSegments(translateResult.segments);

      // Step 4: TTS
      setStep("tts");
      await api.generateTts(projectId, activeSceneId, targetLang, selectedVoice);

      // Step 5: Remux
      const remuxResult = await api.remuxDubbedAudio(projectId, activeSceneId);
      setStep("done");
      return remuxResult;
    },
  });

  if (activeSceneId === null) {
    return (
      <div className="p-3 bg-gray-900 rounded text-gray-500 text-sm text-center">
        Chọn một phân cảnh để lồng tiếng
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 p-3 bg-gray-900 rounded">
      <h4 className="text-sm font-medium text-gray-300">
        🎙️ Lồng tiếng / Dubbing
      </h4>

      {/* Mode selector: Original track vs AI Dubbing */}
      <div className="grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={() => setDubbingMode("original")}
          className={`px-2 py-2 rounded text-xs border transition-colors ${
            dubbingMode === "original"
              ? "bg-blue-700 border-blue-500 text-white"
              : "bg-gray-800 border-gray-700 text-gray-400 hover:bg-gray-700"
          }`}
        >
          🎧 Voice Gốc
          <span className="block text-[10px] opacity-80">Original Track</span>
        </button>
        <button
          type="button"
          onClick={() => setDubbingMode("ai")}
          className={`px-2 py-2 rounded text-xs border transition-colors ${
            dubbingMode === "ai"
              ? "bg-purple-700 border-purple-500 text-white"
              : "bg-gray-800 border-gray-700 text-gray-400 hover:bg-gray-700"
          }`}
        >
          🤖 Voice Dịch AI
          <span className="block text-[10px] opacity-80">AI Dubbing</span>
        </button>
      </div>

      {/* Info when Original track selected */}
      {dubbingMode === "original" && (
        <p className="text-[11px] text-gray-400 bg-gray-800/60 border border-gray-700 rounded p-2">
          🎧 Giữ nguyên giọng gốc của video. Nếu muốn thay bằng giọng đọc AI,
          chọn <strong className="text-purple-300">Voice Dịch AI</strong> bên trên.
        </p>
      )}

      {/* AI-only options */}
      {dubbingMode === "ai" && (
        <>
          {/* Source language */}
      <div>
        <label className="text-xs text-gray-400 block mb-1">
          Ngôn ngữ gốc
        </label>
        <select
          value={sourceLang}
          onChange={(e) => setSourceLang(e.target.value)}
          className="w-full px-2 py-1 bg-gray-800 border border-gray-700
            rounded text-sm"
        >
          <option value="vi">Tiếng Việt</option>
          <option value="en">English</option>
          <option value="ja">日本語</option>
          <option value="ko">한국어</option>
          <option value="zh">中文</option>
        </select>
      </div>

      {/* Target language */}
      <div>
        <label className="text-xs text-gray-400 block mb-1">
          Ngôn ngữ đích
        </label>
        <select
          value={targetLang}
          onChange={(e) => setTargetLang(e.target.value)}
          className="w-full px-2 py-1 bg-gray-800 border border-gray-700
            rounded text-sm"
        >
          {LANGUAGES.map((lang) => (
            <option key={lang.code} value={lang.code}>
              {lang.label}
            </option>
          ))}
        </select>
      </div>

      {/* Whisper model */}
      <div>
        <label className="text-xs text-gray-400 block mb-1">
          Whisper model
        </label>
        <select
          value={whisperModel}
          onChange={(e) => setWhisperModel(e.target.value)}
          className="w-full px-2 py-1 bg-gray-800 border border-gray-700
            rounded text-sm"
        >
          <option value="tiny">Tiny (nhanh, kém chính xác)</option>
          <option value="base">Base (cân bằng)</option>
          <option value="small">Small (chính xác hơn)</option>
          <option value="medium">Medium (chính xác nhất)</option>
        </select>
      </div>
        </>
      )}

      {/* Run button */}
      <button
        onClick={() => dubMut.mutate()}
        disabled={dubMut.isPending}
        className="w-full py-2 bg-orange-600 hover:bg-orange-500
          disabled:bg-gray-700 rounded font-medium text-sm transition-colors"
      >
        {dubMut.isPending ? "Đang xử lý..." : "🎙️ Bắt đầu lồng tiếng"}
      </button>

      {/* Progress */}
      {dubMut.isPending && (
        <div className="text-xs text-gray-400 text-center">
          {step === "separating" && "🔄 Đang tách giọng nói..."}
          {step === "transcribing" && "📝 Đang nhận diện lời thoại..."}
          {step === "translating" && "🌐 Đang dịch phụ đề..."}
          {step === "tts" && "🔊 Đang tạo giọng đọc AI..."}
        </div>
      )}

      {/* Result */}
      {step === "done" && dubMut.data && (
        <div className="p-2 bg-green-900/30 border border-green-700 rounded">
          <p className="text-xs text-green-300 text-center">
            ✅ Lồng tiếng hoàn tất!
          </p>
        </div>
      )}

      {/* Translated segments */}
      {segments.length > 0 && (
        <div className="max-h-40 overflow-y-auto space-y-1">
          <p className="text-xs text-gray-400">Phụ đề đã dịch:</p>
          {segments.map((seg, i) => (
            <div key={i} className="text-xs bg-gray-800 p-1.5 rounded">
              <span className="text-gray-500">
                {seg.start.toFixed(1)}s-{seg.end.toFixed(1)}s
              </span>
              <span className="text-gray-300 ml-2">{seg.text}</span>
              {seg.original && (
                <span className="text-gray-600 ml-2 italic">
                  ({seg.original})
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Error */}
      {dubMut.isError && (
        <div className="p-2 bg-red-900/30 border border-red-700 rounded">
          <p className="text-xs text-red-300 text-center">
            ❌ Lỗi: {(dubMut.error as Error).message}
          </p>
        </div>
      )}
    </div>
  );
}
