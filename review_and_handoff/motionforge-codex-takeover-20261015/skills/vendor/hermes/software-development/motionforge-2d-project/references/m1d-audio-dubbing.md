# M1D: Audio Dubbing Service — Patterns & Architecture

## Service: `app/workflow/audio_dubbing_service.py`

Full dubbing pipeline: separate → transcribe → translate → TTS → remux.

### Pipeline stages:
1. **Vocal separation** — FFmpeg center-pan extraction (`pan=stereo|c0=c0-c1|c1=c0-c1` for vocals, inverse for BGM). Outputs 16kHz mono WAV for Whisper compatibility.
2. **STT** — openai-whisper (`whisper.load_model(size)`, `model.transcribe()`). Returns `[{start, end, text}]` segments.
3. **SRT generation** — `segments_to_srt()` converts segments to SRT subtitle format (`HH:MM:SS,mmm`).
4. **Translation** — deep-translator `GoogleTranslator.translate_batch()` for batch efficiency.
5. **TTS** — edge-tts `Communicate.save()` wrapped in `asyncio.run()` for sync callers. Generates MP3, then FFmpeg converts to 16kHz mono WAV.
6. **Remux** — FFmpeg `adelay` filter places TTS at correct timestamps, `amix` combines with BGM at 0.3 volume.

### Key patterns:
- **asyncio.run() sync wrapper**: edge-tts is async-only; wrap with `asyncio.run(self._tts_async(...))` for sync API.
- **TTS fallback**: On failure, generate silence with `anullsrc` filter matching segment duration.
- **FFmpeg filter_complex for mixing**: `[1]adelay=1000|1000[tts0];[0]volume=0.3[bgm];[bgm][tts0]amix=inputs=2:duration=longest[out]`

### Schemas (`app/schemas/__init__.py`):
- `DubbingConfig` — source_lang, target_lang, whisper_model, tts_voice
- `DubbingResult` — vocal_track, bgm_track, original_srt, translated_srt, final_audio, segments

### API endpoints (`app/api/routes/projects.py`):
- `POST /{project_id}/dubbing/separate` — separate audio into vocal + BGM
- `POST /{project_id}/dubbing/transcribe` — STT on vocal track
- `POST /{project_id}/dubbing/translate` — translate subtitles
- `POST /{project_id}/dubbing/tts` — generate TTS for translated text
- `POST /{project_id}/dubbing/remux` — mix TTS with BGM
- `POST /{project_id}/dubbing/full` — run entire pipeline

### Dubbing files stored at:
`{project_dir}/dubbing/scene_{id:03d}/` containing:
- `vocal_track.wav`, `bgm_sfx_track.wav`
- `subtitles_original.srt`, `subtitles_translated.srt`
- `tts_segments/tts_{i:04d}.wav`
- `dubbed_audio.wav`

### Tests: `tests/test_audio_dubbing.py`
- SRT generation and time format tests (pure logic, no network)
- Vocal separation test (FFmpeg sine wave → separate → verify files exist)
- TTS test (edge-tts with `pytest.skip` on network failure)

### Pitfall: E501 on path string concatenation
`self.segments_to_srt(translated, output_dir / "subtitles_translated.srt")` exceeds 100 chars. Break into multi-line:
```python
self.segments_to_srt(
    translated, output_dir / "subtitles_translated.srt"
)
```
