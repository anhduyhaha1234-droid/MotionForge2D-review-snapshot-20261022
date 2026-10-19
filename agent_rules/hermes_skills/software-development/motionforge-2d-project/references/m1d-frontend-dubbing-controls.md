# M1D: Frontend Dubbing Controls — Patterns & Implementation

## Component: `frontend/src/components/DubbingPanel.tsx`

Self-contained dubbing UI panel with step-by-step pipeline progress.

### Architecture:
- **Single mutation, sequential steps**: One `useMutation` runs all 5 pipeline stages in order, updating a `step` state variable at each boundary.
- **Step state machine**: `"idle" | "separating" | "transcribing" | "translating" | "tts" | "done"` — drives progress text and completion indicator.
- **Standalone component**: Reads `projectId` and `activeSceneId` from Zustand store; no props needed.

### API client additions (`frontend/src/lib/api.ts`):
```typescript
export interface DubbingConfig { scene_id; source_lang; target_lang; whisper_model; tts_voice }
export interface DubbingResult { vocal_track; bgm_track; original_srt; translated_srt; final_audio; segments }
export interface DubbingSegment { start; end; text; original? }
```

Methods added to `api` object:
- `separateAudio(projectId, sceneId)` — POST, returns `{ vocal_track, bgm_track }`
- `transcribeScene(projectId, sceneId, sourceLang?, whisperModel?)` — POST, returns `{ segments, srt_path }`
- `translateSubtitles(projectId, sceneId, targetLang, sourceLang?)` — POST, returns `{ segments, srt_path }`
- `generateTts(projectId, sceneId, targetLang?, ttsVoice?)` — POST, returns `{ tts_count, tts_dir }`
- `remuxDubbedAudio(projectId, sceneId)` — POST, returns `{ final_audio }`
- `fullDubbingPipeline(projectId, config)` — POST JSON body, returns `DubbingResult`

### Integration into ScreenD.tsx:
- Imported as `<DubbingPanel />`
- Wrapped in `<details>` element for collapsible section at bottom of right sidebar
- Placed after the "Bulk Character Mapping" section

### UI controls (all Vietnamese labels):
- **Ngôn ngữ gốc** (source language): select — vi, en, ja, ko, zh
- **Ngôn ngữ đích** (target language): select — 7 languages with auto-selected Edge TTS voice
- **Whisper model**: select — tiny, base, small, medium (with speed/accuracy hints)
- **Run button**: orange, disabled while pending
- **Progress indicators**: emoji + Vietnamese text per step
- **Result**: green success banner when done
- **Segments list**: scrollable list showing translated subtitles with timestamps
- **Error**: red error banner with message

### Language-to-voice mapping:
```typescript
const LANGUAGES = [
  { code: "en", label: "English", voice: "en-US-AriaNeural" },
  { code: "es", label: "Español", voice: "es-ES-ElviraNeural" },
  { code: "fr", label: "Français", voice: "fr-FR-DeniseNeural" },
  { code: "de", label: "Deutsch", voice: "de-DE-KatjaNeural" },
  { code: "ja", label: "日本語", voice: "ja-JP-NanamiNeural" },
  { code: "ko", label: "한국어", voice: "ko-KR-SunHiNeural" },
  { code: "zh", label: "中文", voice: "zh-CN-XiaoxiaoNeural" },
];
```

### Pattern: Step-by-step pipeline progress in a single mutation
When a feature requires sequential API calls (separate → transcribe → translate → TTS → remux):
1. Define a union type for steps: `"idle" | "step1" | "step2" | ... | "done"`
2. Use a single `useMutation` that calls each API in sequence
3. Update step state between each `await` call
4. Display step-specific progress text while `isPending`
5. Show success banner only when `step === "done" && data`

This avoids multiple mutations and keeps the pipeline state machine clean.

### Pattern: Collapsible feature section in existing sidebar
To add a new feature block to an existing sidebar panel without restructuring the layout:
```tsx
<details className="border-t border-gray-700 pt-3">
  <summary className="text-sm font-medium text-gray-300 cursor-pointer">
    🎙️ Feature Name
  </summary>
  <div className="mt-2">
    <FeatureComponent />
  </div>
</details>
```
- Uses native HTML `<details>` — no JS state needed for expand/collapse
- Border-top visually separates from preceding content
- Component is self-contained, reads its own state from store
