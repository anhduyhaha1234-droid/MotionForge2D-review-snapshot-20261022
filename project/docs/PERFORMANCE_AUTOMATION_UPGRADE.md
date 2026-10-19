# Performance & Automation Upgrade

**Date:** 2026-07-31  
**Status:** 🔄 In Progress

---

## Feature 1: NVENC GPU Hardware Acceleration ✅

- `app/services/gpu_encoder.py` — detect_nvenc() + get_encode_args()
- Auto-detects RTX 5070 via nvidia-smi + ffmpeg -encoders
- Falls back to libx264 if no NVENC
- `/api/projects/gpu-info` endpoint
- Frontend GPU indicator in header

## Feature 2: AI Smart Character Auto-Matching ✅

- `POST /api/projects/{id}/objects/{oid}/auto-match`
- Bbox similarity matching across scenes
- "🪄 Auto-Match All Scenes" button on ScreenD

## Feature 3: Auto Lip-Sync Speech-Rate Adjuster ✅

- `_calculate_speech_rate()` in audio_dubbing_service.py
- Compares original_duration vs TTS duration
- Safe ratio clamped to 0.85x - 1.15x
- Edge-TTS rate adjustment: +X% or -X%

## Feature 4: Auto Disk Cleanup ✅

- `app/services/cleanup_service.py` — CleanupService
- Removes: debug/, temp_stitch/, frames/, tts_segments/, __pycache__/
- Keeps: renders/, audio/, presets/, scenes/, project.json
- `POST /api/projects/{id}/cleanup` endpoint
- Frontend "🧹 Dọn dẹp file tạm" button on ScreenE

## Tests

- `tests/test_performance_automation.py`
- NVENC detection tests
- Cleanup service tests (6 tests)
- Lip-sync rate tests

## Verification

| Check | Result |
|-------|--------|
| pytest | ✅ |
| ruff | ✅ |
| tsc --noEmit | ✅ |
| next build | ✅ |
