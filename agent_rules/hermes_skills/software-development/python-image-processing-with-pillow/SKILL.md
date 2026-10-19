---
name: python-image-processing-with-pillow
description: >
  Generate product mockups, apply perspective transforms, and composite images
  using Python Pillow. Covers 3D book covers, tablet/device frames, floating
  card previews, framed wall art, and multi-composite canvases. Also covers
  PIL MESH transform gotchas, shadow generation, and gradient backgrounds.
triggers:
  - "product mockup"
  - "3D book cover"
  - "tablet mockup"
  - "card preview"
  - "ebook cover mockup"
  - "framed art mockup"
  - "pillow perspective transform"
  - "pillow compositing"
  - "image mockup generator"
  - "gumroad product image"
---

# Python Image Processing with Pillow

Generate professional product mockups and apply image transforms using pure Pillow (PIL).

## Dependencies

```bash
pip install Pillow
```

No other dependencies required — all mockup styles use only Pillow.

## Quick Start: Standalone Mockup Generator

The session produced a complete working script at `product_mockup_generator.py` (see `templates/product_mockup_generator.py`). It supports 5 mockup styles:

```bash
python product_mockup_generator.py cover.png --style book3d --output mockups/
python product_mockup_generator.py cover.png --style all --output mockups/
python product_mockup_generator.py cover.png --style card --bg 200,210,230 --output mockups/
```

Styles: `book3d`, `tablet`, `card`, `framed`, `multi`, `all`

## Core Techniques

### 1. PIL MESH Transform for Perspective (CRITICAL — see pitfalls)

PIL's `Image.transform()` with `MESH` mode requires a list of `(dst_bbox, src_quad)` tuples:

```python
# dst_bbox = (x0, y0, x1, y1) — axis-aligned rectangle in output
# src_quad = (x0,y0, x1,y1, x2,y2, x3,y3) — four corners in source image
mesh_quads.append((dst_box, src_quad))

cover.transform(
    (width, height),
    Image.Transform.MESH,
    mesh_quads,
    Image.Resampling.BILINEAR,
)
```

For perspective/shear effects, split the image into horizontal strips (20 strips works well) and vary the source quad corners progressively:

```python
num_strips = 20
strip_h = new_h // num_strips
for i in range(num_strips):
    y0 = i * strip_h
    y1 = min((i + 1) * strip_h, new_h)
    t0, t1 = y0 / new_h, y1 / new_h
    shear0 = int(shear_pixels * (1 - t0))
    shear1 = int(shear_pixels * (1 - t1))
    dst_box = (0, y0, new_w, y1)
    src_quad = (shear0, y0, new_w + shear0, y0,
                new_w + shear1, y1, shear1, y1)
    mesh_quads.append((dst_box, src_quad))
```

### 2. Shadow Generation Pattern

Every mockup uses this compositing stack:

```python
# 1. Create transparent shadow layer at canvas size
shadow_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
draw = ImageDraw.Draw(shadow_layer)
draw.rectangle([(sx, sy), (sx+w, sy+h)], fill=(0, 0, 0, 50-80))
shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(15-25))

# 2. Start canvas with background
canvas = Image.new("RGBA", canvas_size, bg_color + (255,))

# 3. Alpha-composite shadow onto canvas
canvas = Image.alpha_composite(canvas, shadow_layer)

# 4. Paste content (with alpha mask for transparency)
canvas.paste(content, (x, y), content)
```

### 3. Gradient Backgrounds

```python
canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
draw = ImageDraw.Draw(canvas)
for y in range(canvas_size[1]):
    t = y / canvas_size[1]
    r = int(start_color[0] * (1-t) + end_color[0] * t)
    g = int(start_color[1] * (1-t) + end_color[1] * t)
    b = int(start_color[2] * (1-t) + end_color[2] * t)
    draw.line([(0, y), (canvas_size[0], y)], fill=(r, g, b, 255))
```

### 4. Framed Artwork with Mat Border

```python
mat_w = int(art_w * mat_width_pct)  # e.g. 0.08
total_w = art_w + mat_w*2 + frame_width_px*2
total_h = art_h + mat_w*2 + frame_width_px*2
canvas = Image.new("RGBA", (total_w, total_h), mat_color + (255,))
draw = ImageDraw.Draw(canvas)
draw.rectangle([(0,0), (total_w-1, total_h-1)],
               outline=frame_color + (255,), width=frame_width_px)
canvas.paste(artwork, (frame_width_px + mat_w, frame_width_px + mat_w))
```

### 5. Tablet/Device Bezel

```python
tablet = Image.new("RGBA", (tablet_w, tablet_h), (0,0,0,0))
draw = ImageDraw.Draw(tablet)
draw.rounded_rectangle([(0,0), (tablet_w-1, tablet_h-1)],
                       radius=corner_radius, fill=bezel_color)
draw.rounded_rectangle([(bezel, bezel), (screen_r, screen_b)],
                       radius=corner_radius//2, fill=(20,20,22))
tablet.paste(cover_resized, (bezel + margin, bezel + margin))
```

## Reference Repositories

| Repo | Stars | Focus |
|------|-------|-------|
| `CTDave001/automated_mockups` | 68 | Template-based compositing with colored placeholder detection, rotation, alignment/scale modes |
| `kashifulhaque/product-mockup-node-python` | 46 | Mask-based compositing with ImageMagick |
| `devonjhills/etsy-digital-mockup-tools` | 10 | Full Etsy automation: mockups + AI content + listing upload |
| `jjshay/mockup-generator` | 2 | Mat+frame compositing onto lifestyle room-scene templates |

## Pitfalls

### PIL MESH Transform Format (HIGH)
`Image.transform(size, MESH, data)` expects `data` as a list of `(dst_bbox, src_quad)` tuples where:
- `dst_bbox` is a 4-tuple `(x0, y0, x1, y1)` — an axis-aligned rectangle
- `src_quad` is an 8-tuple `(x0,y0, x1,y1, x2,y2, x3,y3)` — four arbitrary corners

**WRONG:** `[(dst_quad, src_quad)]` with 8-tuples for both — causes `IndexError: tuple index out of range` at `box[2]`.
**RIGHT:** `[(dst_bbox, src_quad)]` with 4-tuple bbox and 8-tuple quad.

For perspective effects, use horizontal strip meshing (20 strips) with progressive coordinate variation — a single quad cannot represent perspective.

### RGBA vs RGB
- Always work in RGBA mode during compositing
- Convert to RGB only for final save (JPEG requires RGB; PNG supports RGBA)
- Use alpha mask when pasting: `canvas.paste(img, pos, img)` — the third arg enables transparency

### Image.Resampling
Use `LANCZOS` for downscaling, `BILINEAR` for transforms (faster, sufficient for mesh warps).

## Support Files

- `templates/product_mockup_generator.py` — Complete working CLI script with 4 mockup styles (book3d, tablet, card, framed). Copy and modify.
- `references/github-repos-mockup-generators.md` — Research findings: 4 repos with architecture notes, star counts, search queries, and ecosystem gap analysis.

## Verified Output

All 5 mockup styles tested and verified (PIL `Image.verify()`) with sizes 27KB–115KB for a 600×900 input cover at 1200×900 canvas.
