#!/usr/bin/env python3
"""
Product Mockup Generator — Pillow-based
========================================
Generates professional product mockups for e-commerce (Gumroad, Etsy, etc.)
Supports: 3D book cover, tablet/e-reader frame, card preview, framed wall art.

Dependencies: pip install Pillow

Usage:
    python product_mockup_generator.py cover.png --style book3d --output mockups/
    python product_mockup_generator.py cover.png --style all --output mockups/
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)


# ─────────────────────────────────────────────
# 1. 3D BOOK COVER MOCKUP
# ─────────────────────────────────────────────
def create_3d_book_mockup(
    cover_path: str,
    output_path: str = "mockup_book3d.png",
    canvas_size: tuple = (1200, 900),
    book_height: int = 700,
    perspective_shear: float = 0.12,
    shadow_blur: int = 25,
    shadow_offset: tuple = (15, 20),
    spine_width: int = 40,
    bg_color: tuple = (245, 245, 250),
):
    """
    Create a 3D book cover mockup with perspective, spine, shadow.

    Args:
        cover_path: Path to the cover image
        output_path: Where to save the result
        canvas_size: (width, height) of output canvas
        book_height: Height of the book in pixels
        perspective_shear: How much to shear for 3D perspective (0.0-0.3)
        shadow_blur: Gaussian blur radius for shadow
        shadow_offset: (x, y) shadow offset
        spine_width: Width of the book spine in pixels
        bg_color: Background color RGB tuple
    """
    cover = Image.open(cover_path).convert("RGBA")

    # Scale cover to target height, maintain aspect ratio
    aspect = cover.width / cover.height
    new_h = book_height
    new_w = int(new_h * aspect)
    cover_resized = cover.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # --- Create spine ---
    spine = Image.new("RGBA", (spine_width, new_h), (0, 0, 0, 60))
    spine_draw = ImageDraw.Draw(spine)
    for x in range(spine_width):
        alpha = int(80 * (1 - x / spine_width))
        spine_draw.line([(x, 0), (x, new_h)], fill=(0, 0, 0, alpha))

    # --- Apply perspective transform via horizontal strip mesh ---
    shear_pixels = int(new_h * perspective_shear)
    num_strips = 20
    strip_h = new_h // num_strips
    mesh_quads = []

    for i in range(num_strips):
        y0 = i * strip_h
        y1 = min((i + 1) * strip_h, new_h)
        t0 = y0 / new_h
        t1 = y1 / new_h

        shear0 = int(shear_pixels * (1 - t0))
        shear1 = int(shear_pixels * (1 - t1))

        dst_box = (0, y0, new_w, y1)
        src_quad = (
            shear0, y0,
            new_w + shear0, y0,
            new_w + shear1, y1,
            shear1, y1,
        )
        mesh_quads.append((dst_box, src_quad))

    cover_3d = cover_resized.transform(
        (new_w, new_h),
        Image.Transform.MESH,
        mesh_quads,
        Image.Resampling.BILINEAR,
    )

    # --- Create shadow ---
    shadow_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    book_total_w = new_w + spine_width
    shadow_x = (canvas_size[0] - book_total_w) // 2 + shadow_offset[0]
    shadow_y = (canvas_size[1] - new_h) // 2 + shadow_offset[1]
    shadow_draw.rectangle(
        [shadow_x, shadow_y, shadow_x + book_total_w, shadow_y + new_h],
        fill=(0, 0, 0, 80),
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))

    # --- Compose final image ---
    canvas = Image.new("RGBA", canvas_size, bg_color + (255,))
    canvas = Image.alpha_composite(canvas, shadow_layer)

    book_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    book_x = (canvas_size[0] - book_total_w) // 2
    book_y = (canvas_size[1] - new_h) // 2

    book_layer.paste(spine, (book_x, book_y))
    book_layer.paste(cover_3d, (book_x + spine_width, book_y), cover_3d)

    # Edge highlight
    highlight = ImageDraw.Draw(book_layer)
    right_x = book_x + spine_width + new_w - 2
    highlight.line(
        [(right_x, book_y + 5), (right_x, book_y + new_h - 5)],
        fill=(255, 255, 255, 40), width=2,
    )

    canvas = Image.alpha_composite(canvas, book_layer)
    final = canvas.convert("RGB")
    final.save(output_path, quality=95)
    print(f"✅ 3D Book mockup saved: {output_path}")
    return output_path


# ─────────────────────────────────────────────
# 2. TABLET / E-READER MOCKUP
# ─────────────────────────────────────────────
def create_tablet_mockup(
    cover_path: str,
    output_path: str = "mockup_tablet.png",
    canvas_size: tuple = (1200, 900),
    tablet_width: int = 500,
    screen_margin: int = 30,
    bezel_width: int = 20,
    bezel_color: tuple = (40, 40, 45),
    bg_color: tuple = (240, 240, 245),
    shadow_blur: int = 20,
    corner_radius: int = 25,
):
    """Create a tablet/e-reader device mockup with the cover on screen."""
    cover = Image.open(cover_path).convert("RGBA")

    aspect = cover.width / cover.height
    screen_w = tablet_width - (bezel_width + screen_margin) * 2
    screen_h = int(screen_w / aspect)
    tablet_h = screen_h + (bezel_width + screen_margin) * 2

    cover_resized = cover.resize((screen_w, screen_h), Image.Resampling.LANCZOS)

    # Tablet body
    tablet = Image.new("RGBA", (tablet_width, tablet_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(tablet)
    draw.rounded_rectangle(
        [(0, 0), (tablet_width - 1, tablet_h - 1)],
        radius=corner_radius, fill=bezel_color,
    )
    screen_x = bezel_width
    screen_y = bezel_width
    draw.rounded_rectangle(
        [(screen_x, screen_y),
         (screen_x + screen_w + screen_margin * 2,
          screen_y + screen_h + screen_margin * 2)],
        radius=corner_radius // 2, fill=(20, 20, 22),
    )

    # Shadow
    shadow_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    sx = (canvas_size[0] - tablet_width) // 2 + 10
    sy = (canvas_size[1] - tablet_h) // 2 + 15
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_draw.rounded_rectangle(
        [(sx, sy), (sx + tablet_width, sy + tablet_h)],
        radius=corner_radius, fill=(0, 0, 0, 60),
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))

    canvas = Image.new("RGBA", canvas_size, bg_color + (255,))
    canvas = Image.alpha_composite(canvas, shadow_layer)

    tx = (canvas_size[0] - tablet_width) // 2
    ty = (canvas_size[1] - tablet_h) // 2

    tablet.paste(cover_resized, (screen_x + screen_margin, screen_y + screen_margin))
    canvas.paste(tablet, (tx, ty), tablet)

    final = canvas.convert("RGB")
    final.save(output_path, quality=95)
    print(f"✅ Tablet mockup saved: {output_path}")
    return output_path


# ─────────────────────────────────────────────
# 3. CARD / DIGITAL PRODUCT PREVIEW
# ─────────────────────────────────────────────
def create_card_mockup(
    cover_path: str,
    output_path: str = "mockup_card.png",
    canvas_size: tuple = (1200, 900),
    card_height: int = 650,
    shadow_blur: int = 18,
    border_width: int = 8,
    border_color: tuple = (255, 255, 255),
    bg_gradient_start: tuple = (230, 235, 245),
    bg_gradient_end: tuple = (200, 210, 225),
    angle: float = -3.0,
):
    """Create a floating card preview mockup — great for Gumroad product images."""
    cover = Image.open(cover_path).convert("RGBA")

    aspect = cover.width / cover.height
    new_h = card_height
    new_w = int(new_h * aspect)
    cover_resized = cover.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # White border
    bordered_w = new_w + border_width * 2
    bordered_h = new_h + border_width * 2
    bordered = Image.new("RGBA", (bordered_w, bordered_h), border_color + (255,))
    bordered.paste(cover_resized, (border_width, border_width))

    # Rotate slightly
    rotated = bordered.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)

    # Shadow
    shadow_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    sx = (canvas_size[0] - rotated.width) // 2 + 8
    sy = (canvas_size[1] - rotated.height) // 2 + 12
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_draw.rectangle(
        [(sx, sy), (sx + rotated.width, sy + rotated.height)],
        fill=(0, 0, 0, 50),
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))

    # Gradient background
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(canvas)
    for y in range(canvas_size[1]):
        t = y / canvas_size[1]
        r = int(bg_gradient_start[0] * (1-t) + bg_gradient_end[0] * t)
        g = int(bg_gradient_start[1] * (1-t) + bg_gradient_end[1] * t)
        b = int(bg_gradient_start[2] * (1-t) + bg_gradient_end[2] * t)
        grad_draw.line([(0, y), (canvas_size[0], y)], fill=(r, g, b, 255))

    canvas = Image.alpha_composite(canvas, shadow_layer)

    cx = (canvas_size[0] - rotated.width) // 2
    cy = (canvas_size[1] - rotated.height) // 2
    canvas.paste(rotated, (cx, cy), rotated)

    final = canvas.convert("RGB")
    final.save(output_path, quality=95)
    print(f"✅ Card mockup saved: {output_path}")
    return output_path


# ─────────────────────────────────────────────
# 4. FRAMED WALL ART
# ─────────────────────────────────────────────
def create_framed_art_mockup(
    cover_path: str,
    output_path: str = "mockup_framed.png",
    canvas_size: tuple = (1200, 900),
    art_height: int = 500,
    mat_width_pct: float = 0.08,
    frame_width_px: int = 18,
    frame_color: tuple = (30, 30, 30),
    mat_color: tuple = (255, 255, 255),
    bg_color: tuple = (245, 242, 238),
    shadow_blur: int = 20,
):
    """Create a framed wall-art mockup with white mat and dark frame."""
    cover = Image.open(cover_path).convert("RGBA")

    aspect = cover.width / cover.height
    art_h = art_height
    art_w = int(art_h * aspect)
    artwork = cover.resize((art_w, art_h), Image.Resampling.LANCZOS)

    mat_w = int(art_w * mat_width_pct)
    total_w = art_w + mat_w * 2 + frame_width_px * 2
    total_h = art_h + mat_w * 2 + frame_width_px * 2

    framed = Image.new("RGBA", (total_w, total_h), mat_color + (255,))
    draw = ImageDraw.Draw(framed)
    draw.rectangle(
        [(0, 0), (total_w - 1, total_h - 1)],
        outline=frame_color + (255,), width=frame_width_px,
    )

    paste_x = frame_width_px + mat_w
    paste_y = frame_width_px + mat_w
    bg_art = Image.new("RGBA", artwork.size, mat_color + (255,))
    bg_art.paste(artwork, (0, 0), artwork)
    framed.paste(bg_art, (paste_x, paste_y))

    shadow_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    sx = (canvas_size[0] - total_w) // 2 + 10
    sy = (canvas_size[1] - total_h) // 2 + 15
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_draw.rectangle(
        [(sx, sy), (sx + total_w, sy + total_h)], fill=(0, 0, 0, 45),
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))

    canvas = Image.new("RGBA", canvas_size, bg_color + (255,))
    canvas = Image.alpha_composite(canvas, shadow_layer)

    fx = (canvas_size[0] - total_w) // 2
    fy = (canvas_size[1] - total_h) // 2
    canvas.paste(framed, (fx, fy), framed)

    final = canvas.convert("RGB")
    final.save(output_path, quality=95)
    print(f"✅ Framed art mockup saved: {output_path}")
    return output_path


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Generate professional product mockups from a cover image"
    )
    parser.add_argument("cover", help="Path to cover/product image")
    parser.add_argument(
        "--style",
        choices=["book3d", "tablet", "card", "framed", "all"],
        default="book3d",
        help="Mockup style to generate",
    )
    parser.add_argument("--output", "-o", default="mockups", help="Output directory")
    parser.add_argument("--bg", default=None, help="Background color as R,G,B")

    args = parser.parse_args()

    if not os.path.exists(args.cover):
        print(f"❌ Cover image not found: {args.cover}")
        sys.exit(1)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    cover_name = Path(args.cover).stem
    bg = tuple(int(x) for x in args.bg.split(",")) if args.bg else (245, 245, 250)

    styles = {
        "book3d": lambda: create_3d_book_mockup(
            args.cover, str(out_dir / f"{cover_name}_book3d.png"), bg_color=bg
        ),
        "tablet": lambda: create_tablet_mockup(
            args.cover, str(out_dir / f"{cover_name}_tablet.png"), bg_color=bg
        ),
        "card": lambda: create_card_mockup(
            args.cover, str(out_dir / f"{cover_name}_card.png")
        ),
        "framed": lambda: create_framed_art_mockup(
            args.cover, str(out_dir / f"{cover_name}_framed.png"), bg_color=bg
        ),
    }

    if args.style == "all":
        for fn in styles.values():
            fn()
    else:
        styles[args.style]()

    print(f"\n🎉 Done! Mockups saved to: {out_dir}/")


if __name__ == "__main__":
    main()
