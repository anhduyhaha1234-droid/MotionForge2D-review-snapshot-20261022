#!/usr/bin/env python3
"""
Carousel Builder — Dark-mode infographic / carousel image generator.

Creates professional-looking carousel slides (1080×1350 px) suitable for
Instagram, LinkedIn, and other social platforms. Each slide features:
  - Solid dark background (#0f172a)
  - Bold title with accent underline
  - Content bullets in light gray
  - Page indicator (e.g. "3/5")
  - Brand watermark ("AI Prompt Studio")
  - Decorative accent-colored shapes

Usage:
    from carousel_builder import build_carousel

    slides = [
        {"title": "What is N8N?", "bullets": ["Open-source", "No-code"], "icon": "⚡"},
        {"title": "Benefits", "bullets": ["Save time", "Reduce errors"], "icon": "🚀"},
    ]
    result = build_carousel(slides, output_dir="output/slides")
    print(result)  # {"paths": [...], "count": 2, "total_size": ...}
"""

import os
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Design constants
# ---------------------------------------------------------------------------

# Canvas size (Instagram/LinkedIn portrait)
SLIDE_WIDTH = 1080
SLIDE_HEIGHT = 1350

# Colors (RGB)
BG_COLOR = (15, 23, 42)          # #0f172a — dark slate
TEXT_WHITE = (255, 255, 255)     # Pure white for titles
TEXT_GRAY = (226, 232, 240)      # #e2e8f0 — light gray for bullets
TEXT_DIM = (102, 102, 102)       # #666666 — brand watermark
DEFAULT_ACCENT = (99, 102, 241)  # #6366f1 — indigo accent

# Typography
FONT_PATHS = {
    "bold": "C:/Windows/Fonts/arialbd.ttf",
    "regular": "C:/Windows/Fonts/arial.ttf",
}
TITLE_FONT_SIZE = 42
BULLET_FONT_SIZE = 24
PAGE_FONT_SIZE = 14
BRAND_FONT_SIZE = 12
ICON_FONT_SIZE = 56

# Layout
TITLE_Y = 80
ACCENT_LINE_Y = TITLE_Y + 65  # 4px bar below title area
BULLETS_START_Y = ACCENT_LINE_Y + 50
BULLET_LINE_HEIGHT = 52
SIDE_PADDING = 80
BOTTOM_Y = SLIDE_HEIGHT - 80
ACCENT_BAR_HEIGHT = 4


# ---------------------------------------------------------------------------
# Font helpers
# ---------------------------------------------------------------------------

def _load_font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    """
    Load a TrueType font by weight and size.

    Falls back to the default PIL font if the requested file isn't found.

    Args:
        weight: 'bold' or 'regular'.
        size: Font size in points.

    Returns:
        A FreeTypeFont object.
    """
    path = FONT_PATHS.get(weight, FONT_PATHS["regular"])
    try:
        return ImageFont.truetype(path, size)
    except (OSError, IOError):
        # Try common fallbacks
        for fallback in [
            f"C:/Windows/Fonts/arial.ttf",
            f"C:/Windows/Fonts/segoeui.ttf",
            "arial.ttf",
        ]:
            try:
                return ImageFont.truetype(fallback, size)
            except (OSError, IOError):
                continue
        # Last resort: default bitmap font
        return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Decorative helpers
# ---------------------------------------------------------------------------

def _draw_decorative_shapes(
    draw: ImageDraw.ImageDraw,
    accent_color: tuple[int, int, int],
) -> None:
    """
    Draw subtle decorative accent-colored shapes on the slide background.

    Adds a few semi-transparent geometric elements:
      - A large accent circle (top-right, faded)
      - A small diamond (bottom-left area)
      - Thin horizontal accent lines

    Args:
        draw: PIL ImageDraw instance.
        accent_color: RGB accent color tuple.
    """
    # Large faded circle — top right corner
    circle_r = 200
    circle_color = tuple(list(accent_color) + [25])  # very low alpha
    # Since PIL doesn't support alpha on RGB images, draw with a very
    # dim version of the accent color blended against the dark background
    dim_accent = tuple(
        int(BG_COLOR[i] + (accent_color[i] - BG_COLOR[i]) * 0.08)
        for i in range(3)
    )
    draw.ellipse(
        [SLIDE_WIDTH - circle_r * 2, -circle_r, SLIDE_WIDTH + circle_r, circle_r],
        fill=dim_accent,
    )

    # Small diamond — bottom-left area
    dim_accent2 = tuple(
        int(BG_COLOR[i] + (accent_color[i] - BG_COLOR[i]) * 0.12)
        for i in range(3)
    )
    cx, cy = 120, SLIDE_HEIGHT - 350
    size = 30
    draw.polygon(
        [(cx, cy - size), (cx + size, cy), (cx, cy + size), (cx - size, cy)],
        fill=dim_accent2,
    )

    # Subtle horizontal line across the middle
    line_color = tuple(
        int(BG_COLOR[i] + (accent_color[i] - BG_COLOR[i]) * 0.06)
        for i in range(3)
    )
    mid_y = SLIDE_HEIGHT // 2
    draw.line(
        [(SIDE_PADDING, mid_y), (SLIDE_WIDTH - SIDE_PADDING, mid_y)],
        fill=line_color,
        width=1,
    )


def _draw_accent_bar(
    draw: ImageDraw.ImageDraw,
    accent_color: tuple[int, int, int],
) -> None:
    """Draw the accent-colored horizontal bar under the title."""
    bar_x1 = SIDE_PADDING
    bar_x2 = SIDE_PADDING + 120  # Short accent bar
    draw.rectangle(
        [bar_x1, ACCENT_LINE_Y, bar_x2, ACCENT_LINE_Y + ACCENT_BAR_HEIGHT],
        fill=accent_color,
    )


# ---------------------------------------------------------------------------
# Slide rendering
# ---------------------------------------------------------------------------

def _render_slide(
    index: int,
    total: int,
    slide_data: dict,
    accent_color: tuple[int, int, int],
) -> Image.Image:
    """
    Render a single carousel slide.

    Args:
        index: Zero-based slide index.
        total: Total number of slides.
        slide_data: Dict with keys 'title' (str), 'bullets' (list[str]),
                     'icon' (str, optional emoji).
        accent_color: RGB accent color.

    Returns:
        PIL Image of the rendered slide (1080×1350).
    """
    # Create canvas
    img = Image.new("RGB", (SLIDE_WIDTH, SLIDE_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # ---- Decorative background shapes ----
    _draw_decorative_shapes(draw, accent_color)

    # ---- Icon (emoji) at top ----
    icon = slide_data.get("icon", "")
    if icon:
        icon_font = _load_font("regular", ICON_FONT_SIZE)
        icon_bbox = draw.textbbox((0, 0), icon, font=icon_font)
        icon_w = icon_bbox[2] - icon_bbox[0]
        draw.text(
            ((SLIDE_WIDTH - icon_w) // 2, TITLE_Y - 70),
            icon,
            font=icon_font,
            fill=TEXT_WHITE,
        )

    # ---- Title ----
    title = slide_data.get("title", f"Slide {index + 1}")
    title_font = _load_font("bold", TITLE_FONT_SIZE)
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    # Center title horizontally
    title_x = (SLIDE_WIDTH - title_w) // 2
    draw.text(
        (title_x, TITLE_Y),
        title,
        font=title_font,
        fill=TEXT_WHITE,
    )

    # ---- Accent bar under title ----
    _draw_accent_bar(draw, accent_color)

    # ---- Bullets ----
    bullet_font = _load_font("regular", BULLET_FONT_SIZE)
    y = BULLETS_START_Y
    bullets = slide_data.get("bullets", [])
    for bullet in bullets:
        # Bullet prefix
        bullet_text = f"  •  {bullet}"
        # Word-wrap long bullets
        lines = _wrap_text(bullet_text, bullet_font, SLIDE_WIDTH - SIDE_PADDING * 2)
        for line in lines:
            draw.text(
                (SIDE_PADDING, y),
                line,
                font=bullet_font,
                fill=TEXT_GRAY,
            )
            y += BULLET_LINE_HEIGHT
        y += 10  # Extra spacing between bullet items

    # ---- Page indicator (bottom right) ----
    page_text = f"{index + 1}/{total}"
    page_font = _load_font("regular", PAGE_FONT_SIZE)
    page_bbox = draw.textbbox((0, 0), page_text, font=page_font)
    page_w = page_bbox[2] - page_bbox[0]
    draw.text(
        (SLIDE_WIDTH - SIDE_PADDING - page_w, BOTTOM_Y),
        page_text,
        font=page_font,
        fill=TEXT_DIM,
    )

    # ---- Brand watermark (bottom left) ----
    brand_text = "AI Prompt Studio"
    brand_font = _load_font("regular", BRAND_FONT_SIZE)
    draw.text(
        (SIDE_PADDING, BOTTOM_Y),
        brand_text,
        font=brand_font,
        fill=TEXT_DIM,
    )

    return img


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """
    Simple word-wrap that breaks text to fit within max_width pixels.

    Args:
        text: The text to wrap.
        font: The PIL font to measure with.
        max_width: Maximum pixel width per line.

    Returns:
        List of wrapped line strings.
    """
    # Use a temporary draw context for text measurement
    temp_img = Image.new("RGB", (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = temp_draw.textbbox((0, 0), test_line, font=font)
        line_w = bbox[2] - bbox[0]
        if line_w <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines or [text]


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------

def build_carousel(
    slides_data: list[dict[str, Any]],
    output_dir: str = "carousel_output",
    accent_color: tuple[int, int, int] = DEFAULT_ACCENT,
) -> dict[str, Any]:
    """
    Build a set of carousel/infographic slides.

    Each slide is 1080×1350 px (Instagram/LinkedIn portrait format) with
    a dark-mode design featuring titles, bullets, and decorative elements.

    Args:
        slides_data: List of dicts, each with:
            - title (str): Slide heading.
            - bullets (list[str]): Content bullet points.
            - icon (str, optional): Emoji displayed above the title.
        output_dir: Directory to save the generated PNG files.
        accent_color: RGB tuple for the accent color (default: indigo).

    Returns:
        dict with keys:
            - paths (list[str]): Absolute paths to each saved PNG.
            - count (int): Number of slides generated.
            - total_size (int): Combined file size in bytes.

    Raises:
        ValueError: If slides_data is empty or has invalid structure.
    """
    if not slides_data:
        raise ValueError("slides_data must be a non-empty list of slide dicts")

    # Validate slide data
    for i, slide in enumerate(slides_data):
        if not isinstance(slide, dict):
            raise ValueError(f"Slide {i} must be a dict, got {type(slide).__name__}")
        if "title" not in slide:
            raise ValueError(f"Slide {i} is missing required 'title' key")
        if "bullets" not in slide or not isinstance(slide["bullets"], list):
            raise ValueError(f"Slide {i} is missing required 'bullets' list")

    # Resolve output directory
    output_dir = str(Path(output_dir).resolve())
    os.makedirs(output_dir, exist_ok=True)

    total = len(slides_data)
    paths = []
    total_size = 0

    print(f"[carousel_builder] Generating {total} slides...")

    for idx, slide in enumerate(slides_data):
        img = _render_slide(idx, total, slide, accent_color)

        # Build filename
        safe_title = slide["title"].lower().replace(" ", "_")
        safe_title = "".join(c for c in safe_title if c.isalnum() or c == "_")
        safe_title = safe_title[:40]  # Truncate long titles
        filename = f"slide_{idx + 1:02d}_{safe_title}.png"
        filepath = os.path.join(output_dir, filename)

        img.save(filepath, "PNG", optimize=True)
        file_size = os.path.getsize(filepath)
        total_size += file_size
        paths.append(filepath)
        print(
            f"  [{idx + 1}/{total}] {filename} "
            f"({file_size / 1024:.0f} KB)"
        )

    print(
        f"[carousel_builder] ✓ Done! {total} slides, "
        f"{total_size / 1024:.0f} KB total → {output_dir}"
    )

    return {
        "paths": paths,
        "count": total,
        "total_size": total_size,
    }


# ---------------------------------------------------------------------------
# CLI / Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Demo carousel about "N8N Automation"
    sample_slides = [
        {
            "title": "What is N8N?",
            "bullets": [
                "Open-source workflow automation tool",
                "Self-hosted or cloud deployment",
                "Visual drag-and-drop interface",
                "400+ integrations out of the box",
            ],
            "icon": "⚡",
        },
        {
            "title": "Why Automate?",
            "bullets": [
                "Save 10+ hours per week on repetitive tasks",
                "Eliminate human error in data entry",
                "Scale operations without hiring more people",
                "Focus on creative, high-value work",
            ],
            "icon": "🚀",
        },
        {
            "title": "Top N8N Workflows",
            "bullets": [
                "Lead capture → CRM → Email sequence",
                "Social media scheduling across platforms",
                "Invoice processing & approval chains",
                "Customer support ticket routing",
            ],
            "icon": "🔧",
        },
        {
            "title": "Getting Started",
            "bullets": [
                "Install via Docker or npm",
                "Connect your first API credential",
                "Use templates as a starting point",
                "Test with sample data before going live",
            ],
            "icon": "🎯",
        },
        {
            "title": "Pro Tips",
            "bullets": [
                "Use error workflows for resilience",
                "Version control your workflows as JSON",
                "Set up webhooks for real-time triggers",
                "Monitor execution logs regularly",
            ],
            "icon": "💡",
        },
    ]

    result = build_carousel(
        slides_data=sample_slides,
        output_dir="carousel_output/n8n_automation",
        accent_color=(99, 102, 241),  # Indigo
    )

    print(f"\n{'='*50}")
    print(f"Result summary:")
    print(f"  Slides:  {result['count']}")
    print(f"  Total:   {result['total_size'] / 1024:.0f} KB")
    print(f"  Output:  {os.path.dirname(result['paths'][0])}")
    for p in result["paths"]:
        print(f"    → {p}")
