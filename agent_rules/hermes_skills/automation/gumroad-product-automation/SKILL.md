---
name: gumroad-product-automation
description: "Automate Gumroad product creation, file upload, and publishing via Gumroad API v2. Covers the 3-step presign→S3→complete file upload flow, product management, and known API limitations. Use when user wants to create, update, or publish products on Gumroad programmatically."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [automation, gumroad, e-commerce, api, product-management]
    related: [web-service-api-reverse-engineering, antidetect-browser-automation]
---

# Gumroad Product Automation

## When to Use
- Creating and publishing digital products on Gumroad via API
- End-to-end workflow: content creation → PDF → images → QA → publish
- Batch product launches (multiple products in sequence)
- **User requires review folder** — always save output to Desktop for inspection

> **API mechanics** (endpoints, auth, presign flow, pitfalls) live in `gumroad-api-automation`.
> This skill owns the **workflow**: what to do, in what order, and how to structure output.

## Prerequisites
- Gumroad access token (from https://app.gumroad.com/developer or OAuth)
- `pip install requests Pillow reportlab` (for image/PDF generation + API calls)

## API Authentication

Two methods:
```python
# Method 1: Bearer header (preferred)
headers = {"Authorization": f"Bearer {TOKEN}"}

# Method 2: Form data
data = {"access_token": TOKEN}
```

Verify token works:
```python
resp = requests.get(f"{BASE}/user", params={"access_token": TOKEN})
# Returns: {"success": true, "user": {"name": "...", "id": "...", "url": "https://username.gumroad.com"}}
```

## Core Workflow: Create → Render → QA → Review Folder → Publish

### Step 1: Create Content Module
Write a Python file (e.g., `product_name.py`) with:
- `TITLE`, `SUBTITLE`, `DESCRIPTION` (AIDA sales copy, 200+ words)
- `PROMPTS` — list of dicts with keys: `title`, `prompt`, `category`, `tip`, `variables`
- `CSV_ROWS` — derived from PROMPTS for CSV export

### Step 2: Generate Assets
Call the scripts from `gumroad-api-automation/scripts/`:
- `pdf_template.py` → `generate_prompt_pack_pdf()` → dark mode A4 PDF
- `mockup_generator.py` → `create_card_from_text()` → cover (1280×720) + thumbnail (600×600)

### Step 3: Self-QA Check
Run `qa_checker.py` → `check_product()` before uploading. Fix any failures.

### Step 4: Save to Review Folder (REQUIRED)
**User preference: ALWAYS save all output to a Desktop folder for review before/after publishing.**

```python
import shutil, os
REVIEW_DIR = os.path.expanduser(r"~\Desktop\gumroad_products\<product_slug>")
os.makedirs(REVIEW_DIR, exist_ok=True)
for f in ["product.pdf", "cover.jpg", "thumbnail.jpg", "prompts.csv"]:
    shutil.copy2(os.path.join(output_dir, f), os.path.join(REVIEW_DIR, f))
```

Structure:
```
Desktop/gumroad_products/
├── README.md                    ← links + QA status
├── product1_slug/
│   ├── product.pdf
│   ├── cover.jpg
│   ├── thumbnail.jpg
│   ├── prompts.csv
│   └── source.py               ← the content module
├── product2_slug/
│   └── ...
```

### Step 5: Publish to Gumroad
Call `gumroad_publish.py` → `publish_product()` with token, title, prompts, price=0.

### Step 6: Verify
Check `result["product_url"]` and `result["qa_results"]["overall_valid"]`.

## API Base URL
```python
BASE = "https://api.gumroad.com/v2"
```

## Product ID vs Permalink
- **Product ID**: base64-encoded string like `gg0xJfFTJqGgjkBKPPiD4w==` — used in API calls
- **Permalink**: short string like `ewshm` — used in URLs (`https://username.gumroad.com/l/ewshm`)
- API endpoints use the **Product ID**, not the permalink
- The ID contains `=` characters that need URL-encoding in path segments

## Pitfalls

### P1: `file_size` not `size`, `filename` not `name`
The presign endpoint uses specific parameter names:
- `filename` (not `name`) — the file's display name
- `file_size` (not `size`) — file size in bytes as string
Getting these wrong returns `400: "filename is required"` or `400: "file_size is required"`

### P2: Complete endpoint requires JSON body
The `/files/complete` endpoint returns `400: "PartNumber must be >= 1"` when using form-encoded data. Must use `json=` parameter with `parts` as an array of objects:
```python
# WRONG (form data)
requests.post(url, data={"parts[0][part_number]": "1", "parts[0][etag]": etag})

# CORRECT (JSON body)
requests.post(url, json={"parts": [{"part_number": 1, "etag": etag}]})
```

### P3: File attachment requires JSON body
The PUT `/products/:id` endpoint rejects form-encoded `files[0][url]` with `"files must be an array of file objects"`. Must use JSON body:
```python
# WRONG
requests.put(url, data={"files[0][url]" : file_url})

# CORRECT
requests.put(url, json={"files": [{"url": file_url}]}, headers={"Authorization": ..., "Content-Type": "application/json"})
```

### P4: `published` may return false even when set to true
The API accepts `published: true` but may return `published: false` in the response. This happens when:
- Product has no files attached yet
- Product needs cover image (API limitation)
- The product IS accessible via its URL even when API reports published=false

Check actual accessibility with: `curl -sI "https://username.gumroad.com/l/PERMALINK"` — HTTP 200 means it's live.

### P5: Cover/thumbnail CAN be set via API (Rails Active Storage)
Cover/thumbnail upload works via the Rails Active Storage signed_blob_id flow. See Step 4 above for the full code. Key endpoints:
- **Cover**: `POST /v2/products/:id/covers` (PLURAL — `/cover` returns 404)
- **Thumbnail**: `POST /v2/products/:id/thumbnail` (singular)
- Both require a `signed_blob_id` from the Rails direct_uploads endpoint
- XSRF token from Gumroad page cookies is REQUIRED (422 without it)

### P6: URL-encode product IDs with special characters
Product IDs contain `=` (e.g., `gg0xJfFTJqGgjkBKPPiD4w==`). In URL paths, these must be URL-encoded:
```python
import urllib.parse
encoded_id = urllib.parse.quote(PRODUCT_ID, safe='')
requests.put(f"{BASE}/products/{encoded_id}", ...)
```
Or use `requests` which handles this automatically for path parameters.

### P7: Description HTML entities
Gumroad API returns `&amp;` in descriptions. When building descriptions programmatically, use plain `&` — the API handles encoding.

## Image Generation for Gumroad Products

Standard sizes:
- **Cover**: 1280×720px (16:9, shown on product page)
- **Thumbnail**: 600×600px (1:1, shown in discover/search)

Pillow template for professional product images:
```python
from PIL import Image, ImageDraw, ImageFont

def get_font(names, size):
    for name in names:
        try: return ImageFont.truetype(name, size)
        except: continue
    return ImageFont.load_default()

def draw_gradient(draw, w, h, c1, c2):
    for y in range(h):
        r = int(c1[0] + (c2[0]-c1[0]) * y/h)
        g = int(c1[1] + (c2[1]-c1[1]) * y/h)
        b = int(c1[2] + (c2[2]-c1[2]) * y/h)
        draw.line([(0,y),(w,y)], fill=(r,g,b))
```

Windows font fallback chain:
```python
font = get_font([
    "C:/Windows/Fonts/impact.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
], 68)
```

## Product Description Template
```
[Hook - pain point or desire]

[What's Inside - bullet list of categories]

[Each prompt includes - value proposition]

[Call to action - "Pay What You Want — download free or support with any amount!"]
```

### v2 Pipeline Features
- **Auto Permalink:** `slugify(title)` generates SEO-friendly URL slug
- **Force Live:** `PUT /v2/products/{id}/enable` + `published: "true"` ensures Live status
- **PDF Clickable TOC:** Sections have `id` anchors, TOC uses `<a href>` links
- **Category Badges:** Auto-maps to [TIKTOK], [REELS], [B2B], etc.
- See `references/gumroad-api-complete-flow.md` for the full API discovery process, error messages, and working code
- API mechanics, pitfalls, and endpoint details → `gumroad-api-automation` skill

## Overlap Note
This skill overlaps significantly with `gumroad-api-automation`. Division of ownership:
- **This skill** (`gumroad-product-automation`): workflow orchestration, content structure, review folder, batch pattern
- **`gumroad-api-automation`**: API endpoints, auth, presign flow, cover/thumbnail upload, pitfalls table, scripts/ directory
If a future session needs both, load `gumroad-api-automation` for API details and this one for workflow steps.
