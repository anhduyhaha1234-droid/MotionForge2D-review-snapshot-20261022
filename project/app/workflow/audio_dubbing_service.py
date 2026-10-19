"""Audio dubbing service — vocal separation, STT, translation, TTS, remux."""

from __future__ import annotations

import asyncio
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any, TypedDict

from app.services.ffmpeg_utils import find_ffmpeg, find_ffprobe


class SegmentDict(TypedDict):
    """A subtitle/dubbing segment: start, end, and text (seconds)."""

    start: float
    end: float
    text: str


class TranslatedSegmentDict(SegmentDict):
    """A translated segment: original text plus the translation."""

    original: str


try:
    import edge_tts
except ImportError as _exc:  # pragma: no cover - exercised only when edge-tts absent
    raise ImportError(
        "edge-tts is required for audio dubbing (Phase 2 feature). "
        "Install it with: pip install -e \".[dubbing]\""
    ) from _exc


class AudioDubbingService:
    """Full dubbing pipeline: separate → transcribe → translate → TTS → remux."""

    def __init__(self) -> None:
        self._ffmpeg = self._find_ffmpeg()

    # ── 1. Vocal Separation ──

    def separate_vocals(
        self,
        audio_path: Path,
        output_dir: Path,
    ) -> tuple[Path, Path]:
        """Separate audio into vocal and background tracks.

        Uses FFmpeg's center-pan extraction for vocal isolation.
        For production, swap with Demucs for better quality.

        Args:
            audio_path: Input audio file.
            output_dir: Directory to write output files.

        Returns:
            Tuple of (vocal_track.wav, bgm_sfx_track.wav).
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        vocal_path = output_dir / "vocal_track.wav"
        bgm_path = output_dir / "bgm_sfx_track.wav"

        # Extract center-panned vocals (vocals are typically center-panned)
        cmd_vocal = [
            self._ffmpeg, "-y",
            "-i", str(audio_path),
            "-af", "pan=stereo|c0=c0-c1|c1=c0-c1",
            "-ar", "16000",  # Whisper expects 16kHz
            "-ac", "1",
            str(vocal_path),
        ]
        subprocess.run(cmd_vocal, capture_output=True, check=True)

        # Extract side-panned background (everything except center vocals)
        cmd_bgm = [
            self._ffmpeg, "-y",
            "-i", str(audio_path),
            "-af", "pan=stereo|c0=c0+c1|c1=c1-c0",
            str(bgm_path),
        ]
        subprocess.run(cmd_bgm, capture_output=True, check=True)

        return vocal_path, bgm_path

    # ── 2. Speech-to-Text ──

    def transcribe(
        self,
        vocal_path: Path,
        language: str = "vi",
        model_size: str = "base",
    ) -> list[SegmentDict]:
        """Transcribe vocal track using Whisper.

        Args:
            vocal_path: Path to vocal audio file.
            language: Source language code.
            model_size: Whisper model size (tiny/base/small/medium).

        Returns:
            List of segments with start, end, text.
        """
        import whisper  # noqa: PLC0415

        model = whisper.load_model(model_size)
        result = model.transcribe(
            str(vocal_path),
            language=language,
            task="transcribe",
        )

        segments: list[SegmentDict] = []
        for seg in result["segments"]:
            segments.append({
                "start": round(seg["start"], 3),
                "end": round(seg["end"], 3),
                "text": seg["text"].strip(),
            })

        return segments

    def segments_to_srt(
        self,
        segments: Sequence[SegmentDict],
        output_path: Path,
    ) -> Path:
        """Convert segments to SRT subtitle file.

        Args:
            segments: List of {start, end, text} dicts.
            output_path: Where to write .srt file.

        Returns:
            Path to SRT file.
        """
        lines = []
        for i, seg in enumerate(segments, 1):
            start = self._seconds_to_srt_time(seg["start"])
            end = self._seconds_to_srt_time(seg["end"])
            lines.append(f"{i}")
            lines.append(f"{start} --> {end}")
            lines.append(seg["text"])
            lines.append("")

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    # ── 3. Translation ──

    def translate_segments(
        self,
        segments: Sequence[SegmentDict],
        target_lang: str = "en",
        source_lang: str = "auto",
    ) -> list[TranslatedSegmentDict]:
        """Translate segment texts to target language.

        Args:
            segments: List of {start, end, text} dicts.
            target_lang: Target language code (en, es, fr, etc.).
            source_lang: Source language code (auto for auto-detect).

        Returns:
            List of segments with translated text.
        """
        from deep_translator import GoogleTranslator  # noqa: PLC0415

        translator = GoogleTranslator(source=source_lang, target=target_lang)

        translated: list[TranslatedSegmentDict] = []
        # Batch translate for efficiency
        texts = [seg["text"] for seg in segments]
        translated_texts = translator.translate_batch(texts)

        for seg, t_text in zip(segments, translated_texts):
            translated.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": t_text or seg["text"],
                "original": seg["text"],
            })

        return translated

    # ── 4. Text-to-Speech ──

    async def _tts_async(
        self,
        text: str,
        output_path: Path,
        voice: str = "en-US-AriaNeural",
        rate: str = "+0%",
    ) -> Path:
        """Generate TTS audio using edge-tts."""
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(str(output_path))
        return output_path

    def tts(
        self,
        text: str,
        output_path: Path,
        voice: str = "en-US-AriaNeural",
        rate: str = "+0%",
    ) -> Path:
        """Generate TTS audio (sync wrapper).

        Args:
            text: Text to speak.
            output_path: Where to write audio file.
            voice: Edge-TTS voice name.
            rate: Speech rate adjustment.

        Returns:
            Path to generated audio.
        """
        asyncio.run(self._tts_async(text, output_path, voice, rate))
        return output_path

    def tts_segments(
        self,
        segments: Sequence[SegmentDict],
        output_dir: Path,
        voice: str = "en-US-AriaNeural",
    ) -> list[Path]:
        """Generate TTS for each segment with auto lip-sync rate adjustment.

        For each segment:
        1. Generate TTS at normal speed
        2. Measure TTS duration vs original segment duration
        3. If ratio outside 0.85–1.15, regenerate with adjusted rate
        4. Use FFmpeg atempo filter as final fallback if still off

        Args:
            segments: List of {start, end, text} dicts.
            output_dir: Directory to write TTS files.
            voice: Edge-TTS voice name.

        Returns:
            List of paths to TTS audio files.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        paths: list[Path] = []

        for i, seg in enumerate(segments):
            out_path = output_dir / f"tts_{i:04d}.wav"
            mp3_path = output_dir / f"tts_{i:04d}.mp3"
            original_duration = seg["end"] - seg["start"]

            try:
                # Step 1: Generate TTS at normal speed
                self.tts(seg["text"], mp3_path, voice=voice)

                # Step 2: Convert to WAV
                cmd = [
                    self._ffmpeg, "-y",
                    "-i", str(mp3_path),
                    "-ar", "16000",
                    "-ac", "1",
                    str(out_path),
                ]
                subprocess.run(cmd, capture_output=True, check=True)

                # Step 3: Check duration and adjust if needed
                if original_duration > 0:
                    rate = self._calculate_speech_rate(original_duration, out_path)
                    if rate != "+0%":
                        # Regenerate with adjusted rate
                        adjusted_mp3 = output_dir / f"tts_{i:04d}_adj.mp3"
                        self.tts(seg["text"], adjusted_mp3, voice=voice, rate=rate)
                        cmd = [
                            self._ffmpeg, "-y",
                            "-i", str(adjusted_mp3),
                            "-ar", "16000",
                            "-ac", "1",
                            str(out_path),
                        ]
                        subprocess.run(cmd, capture_output=True, check=True)
                        adjusted_mp3.unlink(missing_ok=True)

                    # Step 4: Final fallback — use atempo filter if still off
                    try:
                        ffprobe = self._find_ffprobe()
                        probe_cmd = [
                            ffprobe, "-v", "quiet",
                            "-show_entries", "format=duration",
                            "-of", "csv=p=0",
                            str(out_path),
                        ]
                        probe_result = subprocess.run(
                            probe_cmd, capture_output=True, text=True,
                        )
                        current_duration = float(probe_result.stdout.strip())
                        if current_duration > 0 and original_duration > 0:
                            tempo_ratio = current_duration / original_duration
                            if tempo_ratio < 0.5:
                                tempo_ratio = 0.5
                            elif tempo_ratio > 2.0:
                                tempo_ratio = 2.0
                            # Only apply atempo if significantly off (>5%)
                            if abs(tempo_ratio - 1.0) > 0.05:
                                tmp_path = out_path.with_suffix(".tmp.wav")
                                tempo_cmd = [
                                    self._ffmpeg, "-y",
                                    "-i", str(out_path),
                                    "-af", f"atempo={tempo_ratio}",
                                    "-ar", "16000",
                                    "-ac", "1",
                                    str(tmp_path),
                                ]
                                subprocess.run(
                                    tempo_cmd, capture_output=True, check=True,
                                )
                                tmp_path.replace(out_path)
                    except (ValueError, subprocess.CalledProcessError):
                        pass  # keep original if atempo fails

                mp3_path.unlink(missing_ok=True)
                paths.append(out_path)
            except Exception:
                # Fallback: create silence of same duration
                cmd = [
                    self._ffmpeg, "-y",
                    "-f", "lavfi", "-i",
                    "anullsrc=r=16000:cl=mono",
                    "-t", str(original_duration),
                    str(out_path),
                ]
                subprocess.run(cmd, capture_output=True, check=True)
                paths.append(out_path)

        return paths

    # ── 5. Audio Remuxing ──

    def remux_audio(
        self,
        tts_paths: list[Path],
        segments: Sequence[SegmentDict],
        bgm_path: Path,
        output_path: Path,
        total_duration: float | None = None,
    ) -> Path:
        """Mix TTS segments with background music into final audio.

        Args:
            tts_paths: Paths to TTS audio files (one per segment).
            segments: Segment timing info.
            bgm_path: Background music/SFX track.
            output_path: Where to write final mixed audio.
            total_duration: Total audio duration (auto-detect if None).

        Returns:
            Path to final mixed audio.
        """
        # Build complex FFmpeg filter to place TTS at correct timestamps
        inputs = ["-i", str(bgm_path)]
        filter_parts = []

        for i, (tts_path, seg) in enumerate(zip(tts_paths, segments)):
            inputs.extend(["-i", str(tts_path)])
            delay_ms = int(seg["start"] * 1000)
            filter_parts.append(
                f"[{i + 1}]adelay={delay_ms}|{delay_ms}[tts{i}]"
            )

        # Mix all TTS tracks with background
        if filter_parts:
            mix_inputs = "[0]volume=0.3[bgm]"  # Lower BGM volume
            tts_labels = "".join(f"[tts{i}]" for i in range(len(tts_paths)))
            filter_parts.append(
                f"{mix_inputs}{tts_labels}amix=inputs={len(tts_paths) + 1}:duration=longest[out]"
            )
            filter_str = ";".join(filter_parts)

            cmd = [
                self._ffmpeg, "-y",
                *inputs,
                "-filter_complex", filter_str,
                "-map", "[out]",
                "-ar", "44100",
                "-ac", "2",
                str(output_path),
            ]
        else:
            # No TTS, just use BGM
            cmd = [
                self._ffmpeg, "-y",
                "-i", str(bgm_path),
                "-ar", "44100",
                "-ac", "2",
                str(output_path),
            ]

        subprocess.run(cmd, capture_output=True, check=True)
        return output_path

    # ── 6. Full Pipeline ──

    def dub_scene(
        self,
        audio_path: Path,
        output_dir: Path,
        source_lang: str = "vi",
        target_lang: str = "en",
        whisper_model: str = "base",
        tts_voice: str = "en-US-AriaNeural",
    ) -> dict[str, Any]:
        """Full dubbing pipeline for a scene.

        Args:
            audio_path: Input scene audio.
            output_dir: Output directory.
            source_lang: Source language.
            target_lang: Target language.
            whisper_model: Whisper model size.
            tts_voice: Edge-TTS voice.

        Returns:
            Dict with paths to all generated files.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Separate
        vocal_path, bgm_path = self.separate_vocals(audio_path, output_dir)

        # 2. Transcribe
        segments = self.transcribe(vocal_path, language=source_lang, model_size=whisper_model)
        srt_path = self.segments_to_srt(segments, output_dir / "subtitles_original.srt")

        # 3. Translate
        translated = self.translate_segments(segments, target_lang=target_lang)
        translated_srt_path = self.segments_to_srt(
            translated, output_dir / "subtitles_translated.srt"
        )

        # 4. TTS
        tts_dir = output_dir / "tts_segments"
        tts_paths = self.tts_segments(translated, tts_dir, voice=tts_voice)

        # 5. Remux
        final_path = output_dir / "dubbed_audio.wav"
        self.remux_audio(tts_paths, translated, bgm_path, final_path)

        return {
            "vocal_track": str(vocal_path),
            "bgm_track": str(bgm_path),
            "original_srt": str(srt_path),
            "translated_srt": str(translated_srt_path),
            "tts_segments": [str(p) for p in tts_paths],
            "final_audio": str(final_path),
            "segments": translated,
        }

    def _find_ffmpeg(self) -> str:
        """Find FFmpeg binary via the shared discovery authority."""
        return find_ffmpeg()

    def _find_ffprobe(self) -> str:
        """Find FFprobe binary via the shared discovery authority."""
        return find_ffprobe()

    def _calculate_speech_rate(
        self,
        original_duration: float,
        tts_path: Path,
    ) -> str:
        """Calculate Edge-TTS rate to match original duration.

        Compares original speech duration with TTS output duration.
        Applies safe ratio clamped to 0.85x - 1.15x.

        Args:
            original_duration: Duration of original speech segment in seconds.
            tts_path: Path to generated TTS audio file.

        Returns:
            Edge-TTS rate string (e.g., "+10%", "-5%").
        """
        # Get TTS duration using ffprobe
        ffprobe = self._find_ffprobe()
        cmd = [
            ffprobe, "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            str(tts_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        try:
            tts_duration = float(result.stdout.strip())
        except (ValueError, AttributeError):
            return "+0%"

        if tts_duration <= 0 or original_duration <= 0:
            return "+0%"

        # Calculate speed ratio
        ratio = tts_duration / original_duration

        # Clamp to safe range (0.85x - 1.15x)
        ratio = max(0.85, min(1.15, ratio))

        # Convert to percentage
        # If ratio > 1, TTS is too slow -> speed up (positive %)
        # If ratio < 1, TTS is too fast -> slow down (negative %)
        pct = round((1.0 / ratio - 1.0) * 100)

        # Clamp percentage
        pct = max(-15, min(15, pct))

        return f"{'+' if pct >= 0 else ''}{pct}%"
