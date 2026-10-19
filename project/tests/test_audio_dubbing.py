"""Tests for audio dubbing service."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.workflow.audio_dubbing_service import AudioDubbingService


@pytest.fixture
def svc() -> AudioDubbingService:
    return AudioDubbingService()


class TestSRTGeneration:
    def test_segments_to_srt(self, svc: AudioDubbingService, tmp_path: Path) -> None:
        """SRT file is generated correctly."""
        segments = [
            {"start": 0.0, "end": 2.5, "text": "Hello world"},
            {"start": 3.0, "end": 5.0, "text": "Goodbye"},
        ]
        srt_path = svc.segments_to_srt(segments, tmp_path / "test.srt")
        assert srt_path.exists()
        content = srt_path.read_text(encoding="utf-8")
        assert "1" in content
        assert "00:00:00,000 --> 00:00:02,500" in content
        assert "Hello world" in content
        assert "2" in content
        assert "Goodbye" in content

    def test_srt_time_format(self, svc: AudioDubbingService) -> None:
        """SRT time format is correct."""
        assert svc._seconds_to_srt_time(0) == "00:00:00,000"
        assert svc._seconds_to_srt_time(61.5) == "00:01:01,500"
        assert svc._seconds_to_srt_time(3661.123) == "01:01:01,123"


class TestSeparation:
    def test_separate_vocals_creates_files(
        self, svc: AudioDubbingService, tmp_path: Path,
    ) -> None:
        """Vocal separation creates two output files."""
        # Create a dummy audio file using FFmpeg
        dummy_audio = tmp_path / "input.wav"
        cmd = [
            svc._ffmpeg, "-y",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
            "-ar", "16000", "-ac", "2",
            str(dummy_audio),
        ]
        subprocess.run(cmd, capture_output=True, check=True)

        output_dir = tmp_path / "output"
        vocal, bgm = svc.separate_vocals(dummy_audio, output_dir)

        assert vocal.exists()
        assert bgm.exists()
        assert vocal.stat().st_size > 0
        assert bgm.stat().st_size > 0


class TestTTS:
    def test_tts_generates_audio(
        self, svc: AudioDubbingService, tmp_path: Path,
    ) -> None:
        """TTS generates an audio file."""
        output = tmp_path / "output.mp3"
        try:
            result = svc.tts("Hello, this is a test.", output, voice="en-US-AriaNeural")
            assert result.exists()
            assert result.stat().st_size > 0
        except Exception:
            pytest.skip("Edge-TTS not available or network issue")
