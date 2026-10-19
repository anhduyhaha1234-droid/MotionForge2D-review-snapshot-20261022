---
name: gumroad-api-automation
description: "Automate Gumroad product creation, file upload, and publishing via Gumroad API v2. Covers the multi-step presign→S3→complete file upload flow, product management, cover image upload, pricing, and the content module pattern for structuring product definitions. Use when creating, updating, or managing Gumroad products programmatically."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [automation, gumroad, ecommerce, digital-products, api]
    related: []
---

# Gumroad API v2 Automation

## When to Use
- Creating and publishing digital products on Gumroad
- Structuring product content as Python modules (PROMPTS/TITLE/DESCRIPTION/CSV_ROWS pattern)
- Uploading PDF/files to Gumroad products
- Managing product pricing, descriptions, covers
- Batch product management workflows

## Prerequisites
- Gumroad access token (from https://app.gumroad.com/developer)
- Python with `requests` library
- Product files (PDF, images) ready to upload

## API Base
```
BASE = "https://api.gumroad.com/v2"
TOKEN = "<your_access_token>"
```

Auth: either `data={"access_token": TOKEN}` or `headers={"Authorization": f"Bearer {TOKEN}"}`.

---

## Step 1: Verify Credentials

```python
resp = requests.get(f"{BASE}/user", params={"access_token": TOKEN})
user = resp.json()["user"]
# Returns: name, email, id, url (e.g. "https://username.gumroad.com")
```

## Step 2: Create Product

Use **form data** (NOT JSON) for creation:

```python
resp = requests.post(f"{BASE}/products", data={
    "access_token": TOKEN,
    "name": "Product Title",
    "description": "Long description with HTML entities escaped...",
    "price": 0,                    # cents for paid, 0 for free/pay-what-you-want
    "currency": "usd",
    "customizable_price": True,    # enables "pay what you want"
    "published": True,             # NOTE: see pitfall below
})
product_id = resp.json()["product"]["id"]       # e.g. "gg0xJfFTJqGgjkBKPPiD4w=="
short_url = resp.json()["product"]["short_url"]  # e.g. "https://user.gumroad.com/l/xxxxx"
```

**PITFALL: `published` flag via API is unreliable.** The API returns `success: true` but `published: false` in the response. The product IS still accessible via `short_url` (returns HTTP 200), but may not appear in Gumroad Discover/search. To fully publish, either:
- Use the Gumroad web dashboard, OR
- Accept that direct-link access works even without "published" status

## Step 3: Upload File (Multi-Step Presign Flow)

This is the most complex part. Gumroad API does NOT accept file uploads directly via `POST /products/:id/files` (returns 404). Instead, use the **presign → S3 → complete** flow:

### 3a: Get Presigned Upload URL

```python
resp = requests.post(f"{BASE}/files/presign", data={
    "access_token": TOKEN,
    "filename": "MyProduct.pdf",          # NOT "name" — will error
    "content_type": "application/pdf",
    "file_size": str(os.path.getsize(PDF_PATH)),  # NOT "size" — will error
})
presign = resp.json()
# Returns: upload_id, key, file_url, parts[{part_number, presigned_url}]
```

**PITFALL: Parameter names are specific:**
- Must be `filename`, NOT `name` → error: "filename is required"
- Must be `file_size`, NOT `size` → error: "file_size is required"

### 3b: Upload to S3

```python
with open(PDF_PATH, "rb") as f:
    file_data = f.read()

s3_resp = requests.put(
    presign["parts"][0]["presigned_url"],
    data=file_data,
    headers={"Content-Type": "application/pdf"}
)
etag = s3_resp.headers.get("ETag", "")
```

### 3c: Complete Upload

**PITFALL: Must use JSON body, NOT form data.** Form data causes "PartNumber must be >= 1" error.

```python
complete_resp = requests.post(f"{BASE}/files/complete",
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    json={
        "upload_id": presign["upload_id"],
        "key": presign["key"],
        "parts": [{"part_number": 1, "etag": etag}],
    }
)
file_url = complete_resp.json()["file_url"]
```

**PITFALL: `parts` must be an array of objects with integer `part_number`, NOT form-encoded `parts[0][part_number]=1`.**

### 3d: Attach File to Product

**PITFALL: Must use JSON body with `files` array.** Form data causes "files must be an array of file objects" error.

```python
resp = requests.put(f"{BASE}/products/{PRODUCT_ID}",
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    json={
        "published": True,
        "files": [{"url": file_url}],
    }
)
```

**PITFALL: `files` is a FULL REPLACEMENT** — to keep existing files, include their IDs. Files missing from the array are removed.

## Step 4: Upload Cover Image & Thumbnail

Cover/thumbnail CAN be set via API using Rails Active Storage signed_blob_id flow:

### 4a: Get XSRF Token
```python
session = requests.Session()
page = session.get(f"https://duyhoivu.gumroad.com/l/{PERMALINK}")
xsrf = session.cookies.get("XSRF-TOKEN", "")
```

### 4b: Direct Upload (get signed_blob_id)
```python
with open(COVER_PATH, "rb") as f:
    data = f.read()
checksum = base64.b64encode(hashlib.md5(data).digest()).decode()

direct = session.post(
    "https://app.gumroad.com/rails/active_storage/direct_uploads",
    headers={"X-CSRF-Token": xsrf, "Content-Type": "application/json", "Accept": "application/json"},
    json={"blob": {"filename": "cover.jpg", "content_type": "image/jpeg",
                   "byte_size": len(data), "checksum": checksum}}
).json()
signed_id = direct["signed_id"]
```

### 4c: Upload to S3
```python
requests.put(direct["direct_upload"]["url"], data=data,
             headers=direct["direct_upload"]["headers"])
```

### 4d: Set on Product
```python
# Cover (use /covers PLURAL — /cover returns 404!)
requests.post(f"{BASE}/products/{PRODUCT_ID}/covers",
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    json={"signed_blob_id": signed_id})

# Thumbnail
requests.post(f"{BASE}/products/{PRODUCT_ID}/thumbnail",
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    json={"signed_blob_id": signed_id})
```

**PITFALL:** XSRF token from Gumroad page cookies is REQUIRED (422 without it).
**PITFALL:** Endpoint is `/covers` (plural), NOT `/cover` (404).

## Step 5: Verify Product

```python
resp = requests.get(f"{BASE}/products/{PRODUCT_ID}", params={"access_token": TOKEN})
product = resp.json()["product"]
print(f"Published: {product['published']}")
print(f"Files: {product['files']}")       # [{id, name, size, url, filetype}]
print(f"File info: {product['file_info']}")  # {Size, Length} for PDFs
print(f"URL: {product['short_url']}")
```

---

## Common Pitfalls Summary

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Wrong param name in presign | "filename is required" / "file_size is required" | Use `filename` and `file_size`, not `name`/`size` |
| Form data for complete upload | "PartNumber must be >= 1" | Use JSON body with `parts` array |
| Form data for file attachment | "files must be an array of file objects" | Use JSON body with `files` array |
| `published: true` via API | API says success but `published: false` | Direct URL still works; use dashboard for full publish |
| URL-encoding product IDs with `==` | 404 errors | The `==` in base64 IDs works fine in URLs; don't over-encode |
| Replacing files accidentally | Old files disappear | `files` array is full replacement; include existing file IDs to keep them |
| PDF path as image input | `UnidentifiedImageError` from Pillow | Use `create_card_from_text()` instead of `create_card_mockup()` when no standalone image exists |
| Subagent network failure | Content module file not created | Write content directly in parent session, then retry publish |
| `exec()` scope collision | Wrong product data uploaded | Use separate scripts per product, or clear variables between runs |

## Scripts (Full Automation Suite v2)

Located in `scripts/` directory:

### Core Pipeline
| Script | Purpose | Key Functions |
|--------|---------|---------------|
| `pdf_template.py` | Dark mode PDF with **clickable TOC** + **category badges** | `generate_html()`, `generate_prompt_pack_pdf()` |
| `mockup_generator.py` | Cover (1280×720) + Thumbnail (600×600) | `create_card_from_text()`, `create_thumbnail()` |
| `qa_checker.py` | Self-QA: PDF validity, image size/dimensions | `check_product()`, `print_report()` |
| `gumroad_publish.py` | Full pipeline with **auto permalink** + **/enable** | `publish_product()`, `slugify()`, `_force_publish()` |

### Media Production ($0 Cost)
| Script | Purpose | Key Functions |
|--------|---------|---------------|
| `video_builder.py` | Short-form video: edge-tts + Pexels BG + moviepy | `build_short_video()` |
| `carousel_builder.py` | Instagram/LinkedIn carousel (1080×1350, dark mode) | `build_carousel()` |

### Distribution & Notification
| Script | Purpose | Key Functions |
|--------|---------|---------------|
| `reddit_poster.py` | Reddit auto-post (PRAW) with value-first templates | `post_to_reddit()`, `post_to_subreddits()`, `TEMPLATES` |
| `telegram_notifier.py` | Telegram alerts: files, images, videos, status | `notify()`, `notify_product_published()`, `notify_batch_complete()` |

### v2 Features

**Auto Permalink:** `slugify(title)` → SEO-friendly URL slug, passed to Gumroad API as `permalink` param.
**Force Live:** After creation, calls `PUT /v2/products/{id}/enable` + `published: "true"` to ensure Live status.
**PDF Clickable TOC:** Each section has `id="section-{slug}"`, TOC uses `<a href="#section-{slug}">` links.
**Category Badges:** Auto-maps categories to colored badges: [TIKTOK], [REELS], [B2B], [PHOTO], [CINEMA], [FASHION], [CHATGPT], etc.

### Quick Start
```python
from scripts.gumroad_publish import publish_product, slugify

print(slugify("ChatGPT Solopreneur Pack"))  # → "chatgpt-solopreneur-pack"

result = publish_product(
    token="YOUR_TOKEN", title="ChatGPT Solopreneur Pack",
    subtitle="37 System Prompts", description="...",
    prompts=[...], price=0,
)
print(result["product_url"])   # https://duyhoivu.gumroad.com/l/xxx
print(result["permalink"])     # chatgpt-solopreneur-pack
print(result["published"])     # True
```

## MoviePy v2 API Migration (PITFALL)

`video_builder.py` uses MoviePy for composition. Version 2.x broke backward compatibility with v1.x. See `references/moviepy-v2-migration.md` for full migration table. Key changes:

- **Import:** `from moviepy.editor import ...` → `from moviepy import ...` (the `.editor` module was removed in v2)
- **TextClip params:** `fontsize` → `font_size`, `txt` → `text`, `col` → `color`
- **Methods:** `.set_position()` → `.with_position()`, `.set_duration()` → `.with_duration()`, `.resize()` → `.resized()`, `.crop()` → `.cropped()` (with keyword args)
- **Windows fonts:** `TextClip(font="Arial")` raises `OSError: cannot open resource`. Must use full path like `"C:/Windows/Fonts/arialbd.ttf"`. Include a fallback chain.

Verify after install:
```python
from moviepy import TextClip  # NOT from moviepy.editor
clip = TextClip(text="Test", font="C:/Windows/Fonts/arial.ttf", font_size=42, color="white")
```

## GitHub References

| Repo | Features |
|------|----------|
| `vaultmetric-cell/gumroad-publisher` | Full CLI: version→ZIP→upload→publish |
| `SamyPesse/gumroad-api` (npm) | JS client for Gumroad API |
| `WarenGonzaga/gumroad.js` (npm) | TypeScript SDK for Gumroad API v2 |
| `devonjhills/etsy-digital-mockup-tools` | Digital product mockup automation |

## Content Module Pattern (Product Definition Files)

Before uploading to Gumroad, structure product content as a Python module. This is the standard pattern used across all Gumroad product automation sessions:

```python
TITLE = "Product Title"
SUBTITLE = "One-line subtitle for the listing"
DESCRIPTION = """AIDA-formatted sales copy (200+ words)..."""
PROMPTS = [
    {
        "title": "Prompt Name",
        "prompt": "The actual template with [VARIABLE] placeholders...",
        "category": "Category Name",
        "tip": "Why this works (psychology/mechanism)...",
        "variables": ["VARIABLE1", "VARIABLE2"],
    },
    # ... 50+ prompts
]
CSV_ROWS = [
    (p["category"], p["title"], p["prompt"], " | ".join(p["variables"]))
    for p in PROMPTS
]
```

### Key fields per prompt dict
| Key | Purpose |
|-----|---------|
| `title` | Human-readable name for the prompt/template |
| `prompt` | The actual content with `[VARIABLE]` placeholders |
| `category` | Grouping for organization and CSV filtering |
| `tip` | Explanation of why it works (value-add for buyer) |
| `variables` | List of placeholder names for customization |

### DESCRIPTION structure (AIDA)
- **Attention**: Hook about the pain point (e.g., "You have 3 seconds before a viewer scrolls past")
- **Interest**: What's included — bullet list of categories, count of items
- **Desire**: Benefits — what changes when they use it (watch time, algorithm boost, etc.)
- **Action**: CTA with pricing (e.g., "Pay What You Want")

### CSV export
Generate CSV with headers: `Category, Title, Prompt/Script, Variables`. Pipe-delimit variables for readability.

### PITFALL: Bracket-quote collision in prompt strings
When prompts contain `[TAG]` placeholders followed by quoted text (e.g., `[CTA] "Save this"`), the closing bracket `]` can collide with string delimiters in multi-line Python strings. This causes `SyntaxError: invalid syntax` at the exact line.

**Symptom:** `SyntaxError` pointing to a prompt line with mixed brackets and quotes.

**Fix:** After writing the file, ALWAYS run `python <file>.py` to validate syntax. If it fails, check prompt strings for `[TAG":` or `[TAG]` followed by unescaped quotes inside the string literal. Use `content.replace('[TAG":', '[TAG]')` for targeted fix, or rewrite the line with proper escaping.

**Prevention:** When generating prompt strings with `[HOOK]`, `[CONTENT]`, `[CTA]` sections:
- Use `\\\"` for quotes inside double-quoted Python strings
- Or use triple-quoted strings (`"""..."""`) for prompts with mixed quotes
- Always validate with `python file.py` immediately after `write_file`

## Batch Multi-Product Publishing

When publishing multiple products in sequence (e.g., 3 prompt packs), use this pattern:

1. **Delegate content creation** — dispatch N subagents in parallel, each writing a Python module file (`.py`) with `PROMPTS`, `TITLE`, `SUBTITLE`, `DESCRIPTION`, `CSV_ROWS` at a temp path.
2. **Publish sequentially** — write a small Python script per product that loads the module via `exec(open(path, encoding="utf-8").read())` and calls `publish_product()`.
3. **Verify each** — check `result["product_url"]` and `result["qa_results"]["overall_valid"]` before moving to next.

```python
# Load product data from arbitrary path
exec(open(r"C:\Users\Admin\AppData\Local\Temp\product1.py", encoding="utf-8").read())
# Now TITLE, SUBTITLE, DESCRIPTION, PROMPTS, CSV_ROWS are in scope
result = publish_product(token=TOKEN, title=TITLE, subtitle=SUBTITLE,
                         description=DESCRIPTION, prompts=PROMPTS, price=0)
```

**PITFALL: `exec(open(...).read())` pollutes global scope.** When running multiple products sequentially in the same script, each `exec()` overwrites the previous `PROMPTS`, `TITLE`, etc. Use separate scripts per product or clear variables between runs.

**PITFALL: Don't pass PDF path as image input.** `create_card_mockup(cover_path, ...)` opens `cover_path` with Pillow — passing a `.pdf` path raises `UnidentifiedImageError`. Use `create_card_from_text(output_path, title=..., subtitle=...)` instead when you don't have a standalone cover image.

## CSV Export Pattern

Always export a `.csv` alongside the PDF for buyers who want to import prompts into spreadsheets:

```python
import csv
with open("prompts.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Category", "Title", "Prompt", "Variables"])
    for row in CSV_ROWS:
        w.writerow(row)
```

The `CSV_ROWS` list is generated from `PROMPTS` in the content module:
```python
CSV_ROWS = [(p["category"], p["title"], p["prompt"], ", ".join(p["variables"])) for p in PROMPTS]
```

## Subagent Content Delegation Pattern

For batch product creation, dispatch one subagent per product to write the content module file:

```python
delegate_task(tasks=[
    {"goal": "Write product data to C:/Users/Admin/AppData/Local/Temp/product1.py with PROMPTS, TITLE, etc.", "role": "leaf"},
    {"goal": "Write product data to C:/Users/Admin/AppData/Local/Temp/product2.py ...", "role": "leaf"},
    {"goal": "Write product data to C:/Users/Admin/AppData/Local/Temp/product3.py ...", "role": "leaf"},
])
```

Then publish each sequentially from the parent. If a subagent fails (network error), write the content directly and retry.

## Quick Reference: Full Upload Flow

See also: `references/session-notes.md` — error transcripts, cover image attempts, Chrome profile notes.

```python
import requests, os

TOKEN = "your_token"
BASE = "https://api.gumroad.com/v2"
PRODUCT_ID = "your_product_id"
PDF_PATH = "./product.pdf"

# 1. Presign
r = requests.post(f"{BASE}/files/presign", data={
    "access_token": TOKEN,
    "filename": os.path.basename(PDF_PATH),
    "content_type": "application/pdf",
    "file_size": str(os.path.getsize(PDF_PATH)),
})
p = r.json()

# 2. Upload to S3
with open(PDF_PATH, "rb") as f:
    s3 = requests.put(p["parts"][0]["presigned_url"], data=f.read(),
                      headers={"Content-Type": "application/pdf"})

# 3. Complete
c = requests.post(f"{BASE}/files/complete",
    json={"upload_id": p["upload_id"], "key": p["key"],
          "parts": [{"part_number": 1, "etag": s3.headers["ETag"]}]})

# 4. Attach
requests.put(f"{BASE}/products/{PRODUCT_ID}",
    json={"files": [{"url": c.json()["file_url"]}]})
```
