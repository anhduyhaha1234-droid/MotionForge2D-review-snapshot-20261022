---
name: gumroad-product-automation
description: "Automate Gumroad product creation, file upload, and publishing via Gumroad API v2. Covers the undocumented presign→S3→complete file upload flow, product metadata management, and known API limitations (no cover/thumbnail upload). Use when creating, updating, or publishing digital products on Gumroad programmatically."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [automation, gumroad, api, digital-products, ecommerce, publishing]
    related: [web-service-api-reverse-engineering, playwright-browser-automation]
---

# Gumroad Product Automation

## When to Use

- Creating and publishing digital products on Gumroad via API
- Uploading PDF, images, or other files to Gumroad products
- Automating product listings for prompt packs, ebooks, templates, etc.
- Managing Gumroad product metadata (price, description, tags)

## Prerequisites

- Gumroad API access token (OAuth or personal token from gumroad.com/developer)
- Python with `requests` library
- Files to upload (PDF, images, etc.)

## API Base

```
BASE = "https://api.gumroad.com/v2"
TOKEN = "<your_access_token>"
```

Auth: Pass `access_token` as form data parameter, OR `Authorization: Bearer <token>` header.

## Step 1: Create Product

```python
import requests, json

resp = requests.post(f"{BASE}/products", data={
    "access_token": TOKEN,
    "name": "Product Title",
    "description": "Product description (HTML entities auto-escaped)",
    "price": 0,                    # 0 for free / pay-what-you-want
    "currency": "usd",
    "customizable_price": True,    # Enable "pay what you want"
    "published": True,             # May not take effect immediately
})
result = resp.json()
product_id = result["product"]["id"]      # e.g. "gg0xJfFTJqGgjkBKPPiD4w=="
short_url = result["product"]["short_url"] # e.g. "https://username.gumroad.com/l/xxxxx"
```

**PITFALL:** The `published` field in the create response often shows `false` even when set to `true`. The product may still be accessible via its URL. Verify by checking the URL with `curl -sI <short_url>` — a 200 response means it's live.

## Step 2: Upload Files (Presign → S3 → Complete)

**CRITICAL:** Gumroad API does NOT have a simple file upload endpoint. The `POST /v2/products/:id/files` endpoint does NOT exist (returns 404). Files must be uploaded via a3-step presign flow:

### 2a. Presign — Get S3 upload URL

```python
resp = requests.post(f"{BASE}/files/presign", data={
    "access_token": TOKEN,
    "filename": "product.pdf",
    "content_type": "application/pdf",
    "file_size": str(os.path.getsize("product.pdf")),
})
presign = resp.json()
# Returns: upload_id, key, file_url, parts[{part_number, presigned_url}]
```

**PITFALL:** Parameter names matter:
- Use `filename` NOT `name`
- Use `file_size` NOT `size`
- Both are required or you get 400 errors

### 2b. Upload to S3

```python
with open("product.pdf", "rb") as f:
    data = f.read()

s3_resp = requests.put(
    presign["parts"][0]["presigned_url"],
    data=data,
    headers={"Content-Type": "application/pdf"}
)
etag = s3_resp.headers.get("ETag", "")
```

### 2c. Complete upload

```python
complete = requests.post(f"{BASE}/files/complete", json={
    "access_token": TOKEN,
    "upload_id": presign["upload_id"],
    "key": presign["key"],
    "parts": [{"part_number": 1, "etag": etag}],
})
# Returns: {success: true, file_url: "https://s3.amazonaws.com/gumroad/..."}
```

**PITFALL:** The `complete` endpoint requires JSON body (`json=`), NOT form data (`data=`). The `parts` must be a JSON array of objects with integer `part_number` — form-encoded arrays like `parts[0][part_number]=1` will fail with "PartNumber must be >= 1".

## Step 3: Attach Files to Product

```python
file_url = complete.json()["file_url"]

resp = requests.put(f"{BASE}/products/{product_id}",
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    json={
        "published": True,
        "files": [{"url": file_url}],
    })
```

**PITFALL:** The `files` parameter MUST be sent as a JSON array via `json=` body. Form-encoded `files[0][url]=...` returns "files must be an array of file objects". This is the #1 gotcha.

**PITFALL:** `files` is a FULL REPLACEMENT — to keep existing files, include their IDs. Files missing from the array are REMOVED.

## Step 4: Set Cover/Thumbnail Images

**LIMITATION:** Gumroad API v2 does NOT support setting cover images or thumbnails programmatically. The following approaches all fail silently (API returns success: true but covers stay empty):

- PUT with multipart `files={"cover": ...}` — ignored
- JSON body with `covers`, `cover_url`, `custom_cover_url`, `thumbnail_url` — all ignored
- Presign + attach as file — attaches as downloadable file, not cover

**Workaround:** Upload cover/thumbnail via the Gumroad web dashboard (app.gumroad.com/products → Edit). To automate this, use Playwright/Selenium with a Chrome profile that has an active Gumroad session (see `playwright-browser-automation` skill for Chrome profile lock pitfalls).

## Verify Product State

```python
resp = requests.get(f"{BASE}/products/{product_id}", params={"access_token": TOKEN})
p = resp.json()["product"]
print(f"Published: {p['published']}")
print(f"URL: {p['short_url']}")
print(f"Price: {p['formatted_price']}")
print(f"Files: {len(p['files'])}")
print(f"Covers: {p['covers']}")
```

## Full Working Script

See `templates/gumroad_publish.py` for a complete end-to-end script.

## Common Pitfalls Summary

1. **No simple file upload** — Must use presign→S3→complete 3-step flow
2. **Form data vs JSON** — `files` array requires JSON body; presign/complete steps use form data
3. **Parameter naming** — `filename` not `name`, `file_size` not `size`
4. **Complete needs JSON** — `parts` array must be JSON, not form-encoded
5. **Cover/thumbnail impossible via API** — Must use web dashboard
6. **Published field unreliable** — Check URL with HTTP HEAD, not API response
7. **Files is full replacement** — Missing file IDs get removed on update
8. **Product ID encoding** — IDs contain `==` (base64); URL-encode in paths or use JSON body

## References

- `references/gumroad-api-notes.md` — Detailed API quirks and error messages discovered
