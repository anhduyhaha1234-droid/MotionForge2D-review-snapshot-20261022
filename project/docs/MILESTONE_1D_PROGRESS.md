# Milestone 1D — Progress Report

**Ngày:** 31/07/2026  
**Trạng thái:** ✅ Complete  
**Commit:** *(pending)*

---

## 1. Feature 1: Vocal & Background Music Separation ✅

- ✅ `app/workflow/audio_dubbing_service.py`
- ✅ `separate_vocals()` — FFmpeg center-pan extraction
- ✅ Output: `vocal_track.wav` (16kHz mono) + `bgm_sfx_track.wav`

## 2. Feature 2: STT & Translation ✅

- ✅ `transcribe()` — Whisper AI local (tiny/base/small/medium)
- ✅ `segments_to_srt()` — SRT export with HH:MM:SS,mmm timestamps
- ✅ `translate_segments()` — deep-translator (Google Translate)
- ✅ Support: vi, en, es, fr, de, ja, ko, zh

## 3. Feature 3: TTS & Audio Remuxing ✅

- ✅ `tts()` — Edge-TTS local (no API key needed)
- ✅ `tts_segments()` — per-segment TTS with FFmpeg WAV conversion
- ✅ `remux_audio()` — FFmpeg filter_complex mixing (TTS + BGM at correct timestamps)
- ✅ BGM volume lowered to 30% during speech

## 4. Feature 4: Frontend Dubbing Controls ✅

- ✅ `frontend/src/components/DubbingPanel.tsx`
- ✅ Source language selector (vi, en, ja, ko, zh)
- ✅ Target language selector (en, es, fr, de, ja, ko, zh)
- ✅ Whisper model selector (tiny/base/small/medium)
- ✅ Progress indicator (5 steps with Vietnamese labels)
- ✅ Translated segments display with timestamps
- ✅ ScreenD integration (collapsible section)

## 5. API Endpoints (6 new)

| Endpoint | Description |
|----------|-------------|
| `POST /dubbing/separate` | Separate vocal + BGM |
| `POST /dubbing/transcribe` | Whisper STT → segments |
| `POST /dubbing/translate` | Translate subtitles |
| `POST /dubbing/tts` | Generate TTS audio |
| `POST /dubbing/remux` | Mix TTS + BGM |
| `POST /dubbing/full` | Full pipeline |

## 6. Testing ✅

- ✅ `tests/test_audio_dubbing.py` — 4 tests
  - SRT generation (content verification)
  - SRT time format (0, 61.5, 3661.123 seconds)
  - Vocal separation (FFmpeg creates files)
  - TTS generation (edge-tts creates audio)
- ✅ **84 tests pass** (80 + 4 new)

## 7. Verification ✅

| Check | Result |
|-------|--------|
| `pytest tests/ -q` | **84 passed** |
| `ruff check app/ tests/` | ✅ Clean |
| `npx tsc --noEmit` | ✅ 0 errors |
| `npx next build` | ✅ OK |

## 8. Files Created/Modified

### New (3)
| File | Description |
|------|-------------|
| `app/workflow/audio_dubbing_service.py` | Full dubbing pipeline (385 lines) |
| `tests/test_audio_dubbing.py` | 4 tests |
| `frontend/src/components/DubbingPanel.tsx` | Dubbing UI |

### Modified (3)
| File | Changes |
|------|---------|
| `app/schemas/__init__.py` | DubbingConfig, DubbingResult |
| `app/api/routes/projects.py` | 6 dubbing endpoints |
| `frontend/src/lib/api.ts` | Dubbing types + 6 API methods |
| `frontend/src/components/ScreenD.tsx` | DubbingPanel integration |
