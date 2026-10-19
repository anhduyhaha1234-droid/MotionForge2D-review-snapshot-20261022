
"""
Product Mockup Generator using Pillow
Creates professional 3D-style product mockups for Gumroad listings.

Supports:
- Book/ebook cover mockup (3D perspective with shadow)
- Tablet/screen mockup (device frame)
- Card/preview mockup (rounded card with gradient bg)

Usage:
    from mockup_generator import create_book_mockup, create_card_mockup
    create_book_mockup("cover.jpg", "mockup_book.png")
    create_card_mockup("cover.jpg", "mockup_card.png", title="My Product")
"""

import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def get_font(names, size):
    """Try multiple font paths, fallback to default."""
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def draw_gradient(draw, w, h, c1, c2):
    """Draw vertical linear gradient."""
    for y in range(h):
        r = int(c1[0] + (c2[0] - c1[0]) * y / h)
        g = int(c1[1] + (c2[1] - c1[1]) * y / h)
        b = int(c1[2] + (c2[2] - c1[2]) * y / h)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def add_shadow(img, offset=10, blur=15, shadow_color=(0, 0, 0, 80)):
    """Add drop shadow behind an RGBA image."""
    shadow = Image.new("RGBA", (img.width + offset * 2 + blur * 2,
                                 img.height + offset * 2 + blur * 2), (0, 0, 0, 0))
    shadow_layer = Image.new("RGBA", img.size, shadow_color)
    shadow.paste(shadow_layer, (blur, blur))
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    result = Image.new("RGBA", shadow.size, (0, 0, 0, 0))
    result.paste(shadow, (0, 0))
    result.paste(img, (blur - offset // 2, blur - offset // 2), img if img.mode == "RGBA" else None)
    return result


def create_book_mockup(cover_path, output_path, width=800, height=600,
                       bg_colors=((15, 10, 40), (5, 5, 20)), spine_width=30):
    """
    Create a 3D book/ebook mockup from a cover image.
    
    Args:
        cover_path: path to the cover image (any size)
        output_path: where to save the mockup PNG
        width: output width
        height: output height
        bg_colors: tuple of (top_color, bottom_color) for gradient
        spine_width: width of the book spine in pixels
    
    Returns:
        dict with path, size
    """
    # Load and resize cover
    cover = Image.open(cover_path).convert("RGBA")
    # Scale cover to fit in the mockup (leave room for shadow)
    max_h = int(height * 0.75)
    max_w = int(width * 0.45)
    ratio = min(max_w / cover.width, max_h / cover.height)
    new_w = int(cover.width * ratio)
    new_h = int(cover.height * ratio)
    cover = cover.resize((new_w, new_h), Image.LANCZOS)
    
    # Create background
    bg = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(bg)
    draw_gradient(draw, width, height, bg_colors[0], bg_colors[1])
    
    # Create book with spine
    book_w = new_w + spine_width
    book = Image.new("RGBA", (book_w, new_h), (0, 0, 0, 0))
    
    # Draw spine (dark strip on left)
    spine = Image.new("RGBA", (spine_width, new_h), (30, 30, 50, 255))
    book.paste(spine, (0, 0))
    
    # Draw cover on the right
    book.paste(cover, (spine_width, 0))
    
    # Add subtle border
    book_draw = ImageDraw.Draw(book)
    book_draw.rectangle([0, 0, book_w - 1, new_h - 1], outline=(255, 255, 255, 30), width=1)
    book_draw.line([(spine_width, 0), (spine_width, new_h)], fill=(60, 60, 80, 200), width=2)
    
    # Add perspective transform (slight 3D effect)
    # Skew the book slightly
    coeffs = [
        1.0, 0.05, 0,  # x transform
        0.02, 1.0, 0,  # y transform
    ]
    book = book.transform((book_w, new_h), Image.AFFINE, coeffs, Image.BICUBIC)
    
    # Add shadow
    book_with_shadow = add_shadow(book, offset=8, blur=20, shadow_color=(0, 0, 0, 100))
    
    # Center on background
    x = (width - book_with_shadow.width) // 2
    y = (height - book_with_shadow.height) // 2
    bg.paste(book_with_shadow, (x, y), book_with_shadow)
    
    bg.convert("RGB").save(output_path, "PNG", quality=95)
    return {"path": output_path, "size": os.path.getsize(output_path),
            "dimensions": f"{width}x{height}"}


def create_card_from_text(output_path, title="AI Prompt Pack", subtitle="The Ultimate Collection",
                          badge_text=None, width=1280, height=720,
                          bg_colors=((15, 10, 40), (5, 5, 20)),
                          accent_color=(108, 99, 255)):
    """
    Create a product card from text only (no cover image needed).
    Useful when you only have a PDF and need a cover image.
    """
    bg = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(bg)
    draw_gradient(draw, width, height, bg_colors[0], bg_colors[1])
    
    # Bokeh
    import random
    random.seed(42)
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for _ in range(30):
        x = random.randint(0, width)
        y = random.randint(0, height)
        r = random.randint(15, 50)
        a = random.randint(15, 35)
        od.ellipse([x - r, y - r, x + r, y + r], fill=(*accent_color, a))
    bg = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(bg)
    
    # Accent bars
    draw.rectangle([80, 240, 1200, 244], fill=(*accent_color, 180))
    draw.rectangle([80, 480, 1200, 484], fill=(*accent_color, 180))
    
    # Title
    font_big = get_font(["C:/Windows/Fonts/impact.ttf", "C:/Windows/Fonts/arialbd.ttf"], 68)
    font_sub = get_font(["C:/Windows/Fonts/arial.ttf"], 30)
    font_badge = get_font(["C:/Windows/Fonts/arialbd.ttf"], 22)
    font_small = get_font(["C:/Windows/Fonts/arial.ttf"], 18)
    
    if title:
        bbox = draw.textbbox((0, 0), title, font=font_big)
        tw = bbox[2] - bbox[0]
        x = min((width - tw) // 2, width - tw - 20)
        draw.text((x + 2, 262), title, fill=(0, 0, 0, 100), font=font_big)
        draw.text((x, 260), title, fill=(255, 255, 255), font=font_big)
    
    if subtitle:
        bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
        sw = bbox[2] - bbox[0]
        draw.text(((width - sw) // 2, 340), subtitle, fill=(*accent_color, 220), font=font_sub)
    
    if badge_text:
        bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
        bw = bbox[2] - bbox[0]
        bx = (width - bw) // 2
        draw.rounded_rectangle([bx - 25, 395, bx + bw + 25, 435], radius=10, fill=(*accent_color, 220))
        draw.text((bx, 399), badge_text, fill=(255, 255, 255), font=font_badge)
    
    # Bottom text
    keywords = "Cinematic  |  Viral  |  Professional  |  Copy-Paste Ready"
    bbox = draw.textbbox((0, 0), keywords, font=font_small)
    kw = bbox[2] - bbox[0]
    draw.text(((width - kw) // 2, 510), keywords, fill=(136, 136, 136), font=font_small)
    
    bg.convert("RGB").save(output_path, "JPEG", quality=95)
    return {"path": output_path, "size": os.path.getsize(output_path),
            "dimensions": f"{width}x{height}"}


def create_card_mockup(cover_path, output_path, title=None, subtitle=None,
                       width=1280, height=720, bg_colors=((15, 10, 40), (5, 5, 20)),
                       accent_color=(108, 99, 255)):
    """
    Create a product card mockup with cover image and text.
    
    Args:
        cover_path: path to the cover image
        output_path: where to save
        title: optional title text
        subtitle: optional subtitle text
        width: output width (1280 for Gumroad cover)
        height: output height (720 for Gumroad cover)
        bg_colors: gradient colors
        accent_color: accent RGB tuple
    
    Returns:
        dict with path, size
    """
    bg = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(bg)
    draw_gradient(draw, width, height, bg_colors[0], bg_colors[1])
    
    # Add bokeh circles
    import random
    random.seed(42)
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for _ in range(25):
        x = random.randint(0, width)
        y = random.randint(0, height)
        r = random.randint(15, 50)
        a = random.randint(15, 35)
        od.ellipse([x - r, y - r, x + r, y + r],
                   fill=(*accent_color, a))
    bg = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(bg)
    
    # Load cover image
    cover = Image.open(cover_path).convert("RGBA")
    # Scale to fit left side
    max_h = int(height * 0.7)
    max_w = int(width * 0.4)
    ratio = min(max_w / cover.width, max_h / cover.height)
    cw = int(cover.width * ratio)
    ch = int(cover.height * ratio)
    cover = cover.resize((cw, ch), Image.LANCZOS)
    
    # Add shadow to cover
    cover_shadow = add_shadow(cover, offset=6, blur=15, shadow_color=(0, 0, 0, 90))
    
    # Place cover on left
    cx = int(width * 0.08)
    cy = (height - cover_shadow.height) // 2
    bg.paste(cover_shadow, (cx, cy), cover_shadow)
    
    # Add text on right side
    if title or subtitle:
        text_x = int(width * 0.55)
        font_title = get_font(["C:/Windows/Fonts/impact.ttf", "C:/Windows/Fonts/arialbd.ttf"], 42)
        font_sub = get_font(["C:/Windows/Fonts/arial.ttf"], 22)
        
        if title:
            draw.text((text_x, height // 2 - 60), title, fill=(255, 255, 255), font=font_title)
        if subtitle:
            draw.text((text_x, height // 2 + 10), subtitle, fill=(*accent_color, 200), font=font_sub)
        
        # Accent line
        draw.rectangle([text_x, height // 2 - 10, text_x + 80, height // 2 - 8],
                       fill=(*accent_color, 180))
    
    # Accent borders
    draw.rectangle([40, 40, width - 40, 42], fill=(*accent_color, 40))
    draw.rectangle([40, height - 42, width - 40, height - 40], fill=(*accent_color, 40))
    
    bg.convert("RGB").save(output_path, "PNG", quality=95)
    return {"path": output_path, "size": os.path.getsize(output_path),
            "dimensions": f"{width}x{height}"}


def create_thumbnail(cover_path, output_path, size=600, badge_text=None,
                     bg_colors=((15, 10, 40), (5, 5, 20)),
                     accent_color=(108, 99, 255)):
    """
    Create a square thumbnail from a cover image.
    
    Args:
        cover_path: source cover image
        output_path: where to save (600x600 for Gumroad)
        size: output dimensions (square)
        badge_text: optional badge text (e.g., "40 PROMPTS")
    
    Returns:
        dict with path, size
    """
    bg = Image.new("RGBA", (size, size))
    draw = ImageDraw.Draw(bg)
    draw_gradient(draw, size, size, bg_colors[0], bg_colors[1])
    
    # Bokeh
    import random
    random.seed(99)
    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for _ in range(15):
        x = random.randint(0, size)
        y = random.randint(0, size)
        r = random.randint(10, 35)
        a = random.randint(15, 30)
        od.ellipse([x - r, y - r, x + r, y + r], fill=(*accent_color, a))
    bg = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(bg)
    
    # Center circle accent
    cx, cy = size // 2, size // 2
    draw.ellipse([cx - 150, cy - 150, cx + 150, cy + 150],
                 outline=(*accent_color, 60), width=2)
    
    # Load and center cover
    cover = Image.open(cover_path).convert("RGBA")
    max_dim = int(size * 0.5)
    ratio = min(max_dim / cover.width, max_dim / cover.height)
    cw = int(cover.width * ratio)
    ch = int(cover.height * ratio)
    cover = cover.resize((cw, ch), Image.LANCZOS)
    cover_s = add_shadow(cover, offset=4, blur=10, shadow_color=(0, 0, 0, 80))
    bg.paste(cover_s, (cx - cover_s.width // 2, cy - cover_s.height // 2 - 20), cover_s)
    
    # Badge
    if badge_text:
        font_badge = get_font(["C:/Windows/Fonts/arialbd.ttf"], 22)
        bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
        bw = bbox[2] - bbox[0]
        bx = (size - bw) // 2
        draw.rounded_rectangle([bx - 20, size - 80, bx + bw + 20, size - 48],
                               radius=8, fill=(*accent_color, 220))
        draw.text((bx, size - 76), badge_text, fill=(255, 255, 255), font=font_badge)
    
    bg.convert("RGB").save(output_path, "JPEG", quality=95)
    return {"path": output_path, "size": os.path.getsize(output_path),
            "dimensions": f"{size}x{size}"}


if __name__ == "__main__":
    # Quick test with a dummy image
    test_img = Image.new("RGB", (400, 560), (30, 30, 60))
    test_img.save("test_cover.jpg")
    
    r1 = create_book_mockup("test_cover.jpg", "test_book.png")
    r2 = create_card_mockup("test_cover.jpg", "test_card.png", title="TEST", subtitle="Demo")
    r3 = create_thumbnail("test_cover.jpg", "test_thumb.jpg", badge_text="40 PROMPTS")
    
    print(f"Book: {r1}")
    print(f"Card: {r2}")
    print(f"Thumb: {r3}")
    
    # Cleanup
    for f in ["test_cover.jpg", "test_book.png", "test_card.png", "test_thumb.jpg"]:
        if os.path.exists(f):
            os.remove(f)
    print("All tests passed!")
