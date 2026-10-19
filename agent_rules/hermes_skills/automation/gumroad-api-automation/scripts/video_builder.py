#!/usr/bin/env python3
"""
Video Builder — Short-form vertical video production engine.

Generates 9:16 (1080×1920) short videos suitable for TikTok, Instagram Reels,
YouTube Shorts, and similar platforms. Combines:
  - Text-to-speech voiceover via edge-tts
  - Background video from Pexels (portrait/vertical)
  - Dynamic word-by-word captions overlaid on the video

Usage:
    from video_builder import build_short_video

    result = build_short_video(
        script_text="Automation is the future of productivity.",
        topic_keyword="technology",
        output_path="output/my_video.mp4",
        voice="en-US-GuyNeural",
    )
    print(result)  # {"path": ..., "duration": ..., "size": ...}
"""

import asyncio
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Optional

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PEXELS_API_URL = "https://api.pexels.com/videos/search"
PEXELS_API_KEY_ENV = "PEXELS_API_KEY"  # Environment variable name

# Default video dimensions (9:16 vertical)
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920

# Caption styling defaults
CAPTION_FONT_SIZE = 60
CAPTION_WORDS_PER_GROUP = 1  # 1 word at a time for dynamic captions
CAPTION_DURATION_PER_WORD = 0.35  # seconds each word is shown
CAPTION_FONT_PATH = "C:/Windows/Fonts/arialbd.ttf"  # Bold Arial for captions
CAPTION_STROKE_COLOR = "black"
CAPTION_STROKE_WIDTH = 3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_pexels_api_key() -> Optional[str]:
    """Retrieve the Pexels API key from the environment."""
    return os.environ.get(PEXELS_API_KEY_ENV)


async def _generate_tts(script_text: str, voice: str, output_path: str) -> str:
    """
    Generate speech audio from text using edge-tts.

    Args:
        script_text: The text to convert to speech.
        voice: The edge-tts voice identifier (e.g. 'en-US-GuyNeural').
        output_path: Where to save the .mp3 file.

    Returns:
        Path to the generated audio file.

    Raises:
        RuntimeError: If TTS generation fails.
    """
    import edge_tts

    try:
        communicate = edge_tts.Communicate(script_text, voice)
        await communicate.save(output_path)
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError("TTS produced an empty audio file")
        return output_path
    except Exception as e:
        raise RuntimeError(f"edge-tts failed: {e}") from e


def _fetch_background_video(
    keyword: str,
    api_key: str,
    output_dir: str,
) -> str:
    """
    Download a portrait (9:16) background video from Pexels.

    Args:
        keyword: Search keyword for the video.
        api_key: Pexels API authorization key.
        output_dir: Directory to save the downloaded video.

    Returns:
        Path to the downloaded video file.

    Raises:
        RuntimeError: On network errors, missing API key, or no results.
    """
    if not api_key:
        raise RuntimeError(
            f"Pexels API key not found. Set the {PEXELS_API_KEY_ENV} "
            "environment variable. Get a free key at https://www.pexels.com/api/"
        )

    headers = {"Authorization": api_key}
    params = {
        "query": keyword,
        "per_page": 1,
        "orientation": "portrait",
    }

    try:
        resp = requests.get(PEXELS_API_URL, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Pexels API request failed: {e}") from e

    data = resp.json()
    videos = data.get("videos", [])
    if not videos:
        raise RuntimeError(
            f"No portrait videos found on Pexels for keyword '{keyword}'. "
            "Try a broader or different keyword."
        )

    # Pick the best-quality video file that fits our target dimensions
    video_info = videos[0]
    video_files = video_info.get("video_files", [])

    # Prefer HD files with width ≈ 1080
    best_file = None
    for vf in video_files:
        w = vf.get("width", 0)
        if w == TARGET_WIDTH:
            best_file = vf
            break
    if best_file is None:
        # Fallback: pick the file with the closest width to 1080
        best_file = min(
            video_files,
            key=lambda vf: abs(vf.get("width", 0) - TARGET_WIDTH),
        )

    download_url = best_file.get("link")
    if not download_url:
        raise RuntimeError("No downloadable video link found in Pexels response")

    video_path = os.path.join(output_dir, "bg_video.mp4")
    try:
        vid_resp = requests.get(download_url, stream=True, timeout=120)
        vid_resp.raise_for_status()
        with open(video_path, "wb") as f:
            for chunk in vid_resp.iter_content(chunk_size=8192):
                f.write(chunk)
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to download background video: {e}") from e

    if os.path.getsize(video_path) == 0:
        raise RuntimeError("Downloaded background video is empty")

    return video_path


def _split_into_word_groups(text: str, words_per_group: int = 1) -> list[str]:
    """
    Split text into groups of words for caption display.

    Args:
        text: The full script text.
        words_per_group: How many words to show at once.

    Returns:
        List of word-group strings.
    """
    words = text.split()
    groups = []
    for i in range(0, len(words), words_per_group):
        groups.append(" ".join(words[i : i + words_per_group]))
    return groups


def _build_captions(
    script_text: str,
    total_duration: float,
    video_width: int,
    video_height: int,
) -> list:
    """
    Build a list of TextClip captions timed across the video duration.

    Each word is shown for ~CAPTION_DURATION_PER_WORD seconds, positioned
    at the bottom-center of the frame with dark-mode styling (white text,
    black stroke).

    Args:
        script_text: The narration text.
        total_duration: Total video duration in seconds.
        video_width: Width of the video frame.
        video_height: Height of the video frame.

    Returns:
        List of moviepy TextClip objects with position and timing set.
    """
    from moviepy import TextClip

    word_groups = _split_into_word_groups(script_text, CAPTION_WORDS_PER_GROUP)
    n_groups = len(word_groups)
    if n_groups == 0:
        return []

    # Calculate per-word duration: spread across total video time
    # Leave a small buffer at the end
    usable_duration = max(total_duration - 0.5, total_duration * 0.9)
    per_word = usable_duration / n_groups

    captions = []
    font_path = CAPTION_FONT_PATH
    if not os.path.exists(font_path):
        # Fallback to another available font
        for fallback in [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/calibri.ttf",
        ]:
            if os.path.exists(fallback):
                font_path = fallback
                break

    for idx, group in enumerate(word_groups):
        start_time = idx * per_word
        end_time = (idx + 1) * per_word

        try:
            txt_clip = (
                TextClip(
                    text=group.upper(),
                    font=font_path,
                    font_size=CAPTION_FONT_SIZE,
                    color="white",
                    stroke_color=CAPTION_STROKE_COLOR,
                    stroke_width=CAPTION_STROKE_WIDTH,
                    method="caption",
                    size=(int(video_width * 0.85), None),
                    text_align="center",
                    horizontal_align="center",
                    vertical_align="center",
                )
                .with_duration(per_word)
                .with_start(start_time)
                .with_position(
                    lambda _t, _x=0, _y=video_height - 200: (
                        (video_width - (video_width * 0.85)) // 2,
                        video_height - 200,
                    )
                )
            )
            captions.append(txt_clip)
        except Exception:
            # If a single caption fails (e.g. odd characters), skip it
            # rather than crashing the whole video build
            continue

    return captions


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------

def build_short_video(
    script_text: str,
    topic_keyword: str,
    output_path: Optional[str] = None,
    voice: str = "en-US-GuyNeural",
) -> dict[str, Any]:
    """
    Build a short-form vertical video (9:16) with voiceover and captions.

    Pipeline:
        1. Generate speech audio via edge-tts
        2. Download a matching background video from Pexels
        3. Compose video + audio + word-by-word captions with moviepy
        4. Export final .mp4

    Args:
        script_text: The narration script (plain text, a few sentences).
        topic_keyword: Search keyword for Pexels background video.
        output_path: Where to save the output .mp4. Defaults to
            'short_video.mp4' in the current directory.
        voice: edge-tts voice name. Defaults to 'en-US-GuyNeural'.
            Alternatives: 'en-US-JennyNeural', 'en-GB-SoniaNeural'.

    Returns:
        dict with keys:
            - path (str): Absolute path to the output video.
            - duration (float): Video duration in seconds.
            - size (int): File size in bytes.

    Raises:
        RuntimeError: On any step failure (TTS, download, composition).
        ValueError: If script_text is empty.
    """
    from moviepy import AudioFileClip, CompositeVideoClip, VideoFileClip

    if not script_text or not script_text.strip():
        raise ValueError("script_text must be a non-empty string")

    # Resolve output path
    if output_path is None:
        output_path = "short_video.mp4"
    output_path = str(Path(output_path).resolve())
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    work_dir = tempfile.mkdtemp(prefix="vb_")
    tts_path = os.path.join(work_dir, "voiceover.mp3")
    bg_video_path = os.path.join(work_dir, "bg_video.mp4")

    try:
        # ---- Step 1: Generate TTS audio ----
        print("[video_builder] Step 1/4: Generating voiceover...")
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                _generate_tts(script_text, voice, tts_path)
            )
        finally:
            loop.close()
        print(f"[video_builder]   Audio saved: {tts_path}")

        # ---- Step 2: Fetch background video from Pexels ----
        print("[video_builder] Step 2/4: Fetching background video from Pexels...")
        api_key = _get_pexels_api_key()
        bg_video_path = _fetch_background_video(
            topic_keyword, api_key, work_dir
        )
        print(f"[video_builder]   Background video: {bg_video_path}")

        # ---- Step 3: Compose the final video ----
        print("[video_builder] Step 3/4: Composing video with captions...")

        # Load clips
        video_clip = VideoFileClip(bg_video_path)
        audio_clip = AudioFileClip(tts_path)

        # Use audio duration as the target duration
        target_duration = audio_clip.duration

        # Resize/crop video to target dimensions and trim to audio length
        video_clip = video_clip.with_duration(target_duration)

        # Resize to fit target dimensions while maintaining aspect ratio,
        # then center-crop
        vw, vh = video_clip.size
        if vw == 0 or vh == 0:
            video_clip.close()
            audio_clip.close()
            raise RuntimeError("Background video has zero dimensions")

        # Scale so the shorter side matches target, then crop center
        scale_w = TARGET_WIDTH / vw
        scale_h = TARGET_HEIGHT / vh
        scale_factor = max(scale_w, scale_h)
        video_clip = video_clip.resized(scale_factor)

        # Crop to exact target dimensions from center
        vw, vh = video_clip.size
        x_center = vw // 2
        y_center = vh // 2
        video_clip = video_clip.cropped(
            x1=x_center - TARGET_WIDTH // 2,
            y1=y_center - TARGET_HEIGHT // 2,
            x2=x_center + TARGET_WIDTH // 2,
            y2=y_center + TARGET_HEIGHT // 2,
        )

        # Attach audio
        video_clip = video_clip.with_audio(audio_clip)

        # Build captions
        captions = _build_captions(
            script_text, target_duration, TARGET_WIDTH, TARGET_HEIGHT
        )
        print(f"[video_builder]   Generated {len(captions)} caption segments")

        # Compose all layers
        all_clips = [video_clip] + captions
        final_video = CompositeVideoClip(all_clips, size=(TARGET_WIDTH, TARGET_HEIGHT))

        # ---- Step 4: Export ----
        print("[video_builder] Step 4/4: Rendering final video...")
        final_video.write_videofile(
            output_path,
            fps=30,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            threads=4,
            logger=None,  # Suppress moviepy's verbose logging
        )

        # Cleanup source clips
        final_video.close()
        for c in captions:
            try:
                c.close()
            except Exception:
                pass
        video_clip.close()
        audio_clip.close()

        # Gather result info
        file_size = os.path.getsize(output_path)
        print(
            f"[video_builder] ✓ Video exported: {output_path} "
            f"({target_duration:.1f}s, {file_size / 1024:.0f} KB)"
        )

        return {
            "path": output_path,
            "duration": round(target_duration, 2),
            "size": file_size,
        }

    except Exception as e:
        # Clean up partial output on failure
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass
        raise RuntimeError(f"Video build failed: {e}") from e

    finally:
        # Clean up temp work directory
        import shutil
        try:
            shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build a short vertical video")
    parser.add_argument("script", help="The narration script text")
    parser.add_argument(
        "keyword",
        help="Search keyword for Pexels background video",
    )
    parser.add_argument(
        "-o", "--output",
        default="short_video.mp4",
        help="Output file path (default: short_video.mp4)",
    )
    parser.add_argument(
        "-v", "--voice",
        default="en-US-GuyNeural",
        help="edge-tts voice (default: en-US-GuyNeural)",
    )
    args = parser.parse_args()

    result = build_short_video(
        script_text=args.script,
        topic_keyword=args.keyword,
        output_path=args.output,
        voice=args.voice,
    )
    print(f"\nResult: {result}")
