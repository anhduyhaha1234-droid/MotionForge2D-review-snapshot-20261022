# Edge-TTS + Faster-Whisper: Speech Engine Integration

Reference for building TTS/STT engines integrated with FFmpeg audio pipelines.

## Edge-TTS (Free, No API Key)

### SubMaker API (Current — as of edge-tts ≥ 6.x)

The SubMaker API changed significantly. Old methods (`create_sub()`, `generate_subs()`) are **removed**.

```python
import edge_tts

async def tts_with_srt(text: str, voice: str, audio_path: str, srt_path: str):
    communicate = edge_tts.Communicate(text, voice)
    submaker = edge_tts.SubMaker()

    audio_chunks = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])
        elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
            submaker.feed(chunk)  # ← NOT create_sub()

    with open(audio_path, "wb") as f:
        for chunk in audio_chunks:
            f.write(chunk)

    srt_content = submaker.get_srt()  # ← NOT generate_subs()
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
```

**Critical API facts:**
- `SubMaker.feed(chunk)` — accepts the raw chunk dict from `communicate.stream()`, NOT a tuple
- `SubMaker.get_srt()` — returns SRT-formatted string
- Event types: `SentenceBoundary` (primary), `WordBoundary` (may not fire for some voices)
- Vietnamese voices emit `SentenceBoundary` only, NOT `WordBoundary`
- Always handle both event types with `chunk["type"] in ("WordBoundary", "SentenceBoundary")`

**Pitfall — Empty SRT:** If you only check for `WordBoundary`, Vietnamese and some other languages produce empty SRT files. Always include `SentenceBoundary` in the filter.

### Voice Presets

| Language | Voice ID | Gender |
|----------|----------|--------|
| Vietnamese | vi-VN-HoaiMyNeural | Female |
| Vietnamese | vi-VN-NamMinhNeural | Male |
| English | en-US-AriaNeural | Female |
| English | en-US-GuyNeural | Male |
| English | en-US-JennyNeural | Female |
| Japanese | ja-JP-NanamiNeural | Female |
| Japanese | ja-JP-KeitaNeural | Male |
| Korean | ko-KR-SunHiNeural | Female |
| Chinese | zh-CN-XiaoxiaoNeural | Female |

### Duration Estimation

Edge-TTS doesn't return duration directly. Estimate from file size:
```python
# MP3 at ~128kbps = 16000 bytes/sec
duration = file_size / 16000
```

Or parse the SRT to get actual timestamps from the last entry's end time.

## Faster-Whisper (STT)

### Model Loading with Caching

```python
from faster_whisper import WhisperModel

_model_cache = {}

def get_model(model_size: str = "base") -> WhisperModel:
    if model_size not in _model_cache:
        _model_cache[model_size] = WhisperModel(
            model_size, device="cpu", compute_type="int8"
        )
    return _model_cache[model_size]
```

**Sizes:** `tiny`, `base`, `small`, `medium`, `large-v2`, `large-v3`
- `base` — fast, good for English, ~150MB model
- `small` — better accuracy, ~500MB
- `medium` — best balance, ~1.5GB

### Async Transcription

```python
import asyncio

async def transcribe(input_path: str, model_size: str = "base", language: str = None):
    loop = asyncio.get_event_loop()
    model = get_model(model_size)

    def _run():
        kwargs = {}
        if language:
            kwargs["language"] = language
        segments_gen, info = model.transcribe(input_path, **kwargs)
        segments = []
        for seg in segments_gen:
            segments.append({"start": seg.start, "end": seg.end, "text": seg.text.strip()})
        return segments, info.language, info.duration

    return await loop.run_in_executor(None, _run)
```

**Pitfall:** `model.transcribe()` is a generator — iterating it is the actual work. The `run_in_executor` wraps the entire iteration, which is correct. Don't try to make the generator async.

### Fallback Chain

If faster-whisper is unavailable:
1. Try `openai-whisper` (`import whisper; model = whisper.load_model(size)`)
2. If neither available, extract audio with FFmpeg and return placeholder segments

```python
WHISPER_BACKEND = None
try:
    from faster_whisper import WhisperModel
    WHISPER_BACKEND = "faster-whisper"
except ImportError:
    try:
        import whisper
        WHISPER_BACKEND = "openai-whisper"
    except ImportError:
        WHISPER_BACKEND = None
```

## SRT/ASS Subtitle Generation

### SRT Format

```python
def format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def write_srt(segments: list, path: str):
    with open(path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            f.write(f"{i}\n{format_srt_time(seg['start'])} --> {format_srt_time(seg['end'])}\n{seg['text']}\n\n")
```

### ASS Format (Styled Subtitles)

ASS files need a header with style definitions. Key fields:
- `PlayResX`/`PlayResY` — reference resolution (1920×1080 common)
- Style line: `Fontname,Fontsize,PrimaryColour,...,Outline,Shadow,Alignment,MarginV`
- `PrimaryColour=&H00FFFFFF` = white, `OutlineColour=&H00000000` = black outline

```python
def format_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
```

Dialogue line format: `Dialogue: 0,{start},{end},Default,,0,0,0,,{text}`

## FFmpeg Speed Sync (Clip-to-TTS Timeline)

When synchronizing video clips to match TTS subtitle durations:

```python
speed_factor = actual_duration / target_duration

# Video: setpts filter
video_filter = f"setpts=PTS/{speed_factor}"

# Audio: chain atempo for extreme ranges (atempo only works 0.5-2.0)
audio_filters = []
remaining = speed_factor
while remaining > 2.0:
    audio_filters.append("atempo=2.0")
    remaining /= 2.0
while remaining < 0.5:
    audio_filters.append("atempo=0.5")
    remaining /= 0.5
audio_filters.append(f"atempo={remaining:.4f}")
audio_filter = ",".join(audio_filters)

# Apply
cmd = [ffmpeg, "-i", clip_path,
       "-filter_complex", f"[0:v]{video_filter}[v];[0:a]{audio_filter}[a]",
       "-map", "[v]", "-map", "[a]",
       "-y", output_path]
```

**Pitfall:** `atempo` only accepts values in [0.5, 2.0]. For speed factors outside this range, chain multiple `atempo` filters by repeatedly dividing/multiplying by 2.0.

### Audio Mix (TTS Voice + Original)

```python
# Mix TTS as master voice, original at reduced volume
"-filter_complex",
"[0:a]volume=0.3[bg];[1:a]volume=1.0[voice];[bg][voice]amix=inputs=2:duration=longest[aout]"
```

Use `-shortest` to match the shorter track. Fallback: if mix fails, just replace audio entirely with `-map 0:v -map 1:a`.

## Translation (SRT)

Translation requires an external LLM API. Pattern:
1. Parse SRT into numbered entries
2. Build a prompt with numbered lines
3. Call Gemini/OpenAI API
4. Parse numbered response lines back to SRT entries

**Providers:** Gemini (`gemini-2.0-flash`), OpenAI (`gpt-4o-mini`)
- Both need API keys passed at runtime (not hardcoded)
- Temperature 0.2 for consistent translations
- Parse response with regex: `r"^(\d+)[.\)]\s*(.+)$"`

## Dependencies

```
edge-tts          # Free TTS (Microsoft Edge voices)
faster-whisper    # Fast Whisper STT (CTranslate2 backend)
```

`faster-whisper` pulls in: `ctranslate2`, `av`, `huggingface-hub`, `tokenizers`.
