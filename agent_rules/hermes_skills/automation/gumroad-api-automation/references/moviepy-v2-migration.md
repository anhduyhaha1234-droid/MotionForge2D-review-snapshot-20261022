# MoviePy v2 API Migration Notes

MoviePy 2.x broke backward compatibility with v1.x. These notes cover the
migration path discovered during video_builder.py implementation.

## Import Changes

```python
# v1 (BROKEN in v2)
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip

# v2 (CORRECT)
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
```

`moviepy.editor` module no longer exists in v2.

## Parameter Name Changes

### TextClip
| v1 (broken) | v2 (correct) |
|---|---|
| `fontsize=42` | `font_size=42` |
| `font="Arial"` | `font="C:/Windows/Fonts/arial.ttf"` (full path required on Windows) |
| `col="white"` | `color="white"` |
| `stroke_col="black"` | `stroke_color="black"` |
| `stroke_width=3` | `stroke_width=3` (unchanged) |
| `method="caption"` | `method="caption"` (unchanged) |
| `txt="Hello"` | `text="Hello"` |
| `align="center"` | `text_align="center"` or `horizontal_align="center"` |
| `size=(w, None)` | `size=(w, None)` (unchanged) |

### Method Name Changes (all clips)
| v1 | v2 |
|---|---|
| `.set_position(...)` | `.with_position(...)` |
| `.set_duration(...)` | `.with_duration(...)` |
| `.set_start(...)` | `.with_start(...)` |
| `.set_audio(...)` | `.with_audio(...)` |
| `.resize(factor)` | `.resized(factor)` |
| `.crop(x1, y1, x2, y2)` | `.cropped(x1=..., y1=..., x2=..., y2=...)` (keyword args) |

### CompositeVideoClip
```python
# v1
CompositeVideoClip(clips, size=(w, h))

# v2 — same signature, but clips must use .with_position() etc.
CompositeVideoClip(clips, size=(w, h))
```

## Font Handling on Windows

**Pitfall:** `TextClip(font="Arial", ...)` raises `OSError: cannot open resource`.
MoviePy/Pillow tries to open the font string as a file path. On Windows,
you MUST pass the full path:

```python
font_path = "C:/Windows/Fonts/arialbd.ttf"  # Bold
font_path = "C:/Windows/Fonts/arial.ttf"    # Regular
```

**Fallback chain:** If the primary font isn't found, try:
```
C:/Windows/Fonts/arialbd.ttf
C:/Windows/Fonts/arial.ttf
C:/Windows/Fonts/segoeui.ttf
C:/Windows/Fonts/calibri.ttf
```

## write_videofile Changes

```python
# v1
clip.write_videofile(output, fps=30, codec="libx264", audio_codec="aac",
                     preset="medium", threads=4)

# v2 — same keyword args, but logger behavior differs
clip.write_videofile(output, fps=30, codec="libx264", audio_codec="aac",
                     preset="medium", threads=4, logger=None)
```

`logger=None` suppresses moviepy's verbose progress output.

## Crop Method in v2

```python
# v1
clip.crop(x1=0, y1=0, x2=1080, y2=1920)

# v2 — uses keyword args
clip.cropped(x1=0, y1=0, x2=1080, y2=1920)
```

Positional args may work but keyword args are safer and explicit.

## Verification

After migration, verify with:
```python
from moviepy import TextClip, VideoFileClip, AudioFileClip, CompositeVideoClip
clip = TextClip(text="Test", font="C:/Windows/Fonts/arial.ttf", font_size=42, color="white")
print(clip.size)  # Should return (width, height) tuple
clip.close()
```
