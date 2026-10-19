# Gumroad API v2 — Complete Product Lifecycle

## Overview

Gumroad's public API v2 supports full product CRUD, file uploads, cover/thumbnail setting, and publishing. The documentation is incomplete — several critical endpoints are undocumented and were discovered through error message analysis and Rails Active Storage reverse engineering.

**Base URL:** `https://api.gumroad.com/v2`
**Auth:** `Authorization: Bearer <access_token>` or `access_token=<token>` in body/params
**Product ID format:** Base64-encoded string, e.g. `gg0xJfFTJqGgjkBKPPiD4w==`

## Complete Flow: Create → Upload → Publish

### 1. Create Product

```python
resp = requests.post(f"{BASE}/products", data={
    "access_token": TOKEN,
    "name": "Product Name",
    "description": "Description with HTML entities (&amp; etc.)",
    "price": 0,                    # 0 for free / pay-what-you-want
    "currency": "usd",
    "customizable_price": True,    # enables "pay what you want"
    "published": True,
})
product_id = resp.json()["product"]["id"]
short_url = resp.json()["product"]["short_url"]
```

**PITFALL:** `published: true` in create may return `published: false` in response. The URL still works (HTTP 200) even when API reports unpublished. This is normal — publishing may require a file to be attached first.

### 2. Upload File (PDF/content) — 3-Step Presign Flow

```python
# Step 1: Presign
presign = requests.post(f"{BASE}/files/presign", data={
    "access_token": TOKEN,
    "filename": "product.pdf",
    "content_type": "application/pdf",
    "file_size": str(os.path.getsize(pdf_path)),
}).json()

upload_id = presign["upload_id"]
key = presign["key"]
file_url = presign["file_url"]
part_url = presign["parts"][0]["presigned_url"]

# Step 2: Upload to S3
with open(pdf_path, "rb") as f:
    pdf_data = f.read()
s3_resp = requests.put(part_url, data=pdf_data, headers={"Content-Type": "application/pdf"})
etag = s3_resp.headers.get("ETag", "")

# Step 3: Complete (MUST use JSON body, not form data!)
complete = requests.post(f"{BASE}/files/complete", json={
    "access_token": TOKEN,
    "upload_id": upload_id,
    "key": key,
    "parts": [{"part_number": 1, "etag": etag}],
}).json()
file_url = complete["file_url"]
```

**PITFALL:** Step 3 `complete` MUST use `json=` (JSON body), not `data=` (form data). Form data returns `"PartNumber must be >= 1"` or `"key is required"` errors.

**PITFALL:** The presign endpoint requires `file_size` (not `size`) and `filename` (not `name`). Wrong field names return 400 errors.

### 3. Attach File to Product

```python
# MUST use JSON body with Authorization header (not access_token in body)
resp = requests.put(f"{BASE}/products/{PRODUCT_ID}",
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    json={
        "published": True,
        "files": [{"url": file_url}],
    })
```

**PITFALL:** `files` is a FULL REPLACEMENT — to keep existing files, include their IDs. Files missing from the array are REMOVED.

**PITFALL:** PUT with `data=` form params and `files=` multipart does NOT work for setting cover. The API returns `"'file' is not an accepted parameter"`.

### 4. Set Cover Image — Rails Active Storage Flow

Cover and thumbnail use a DIFFERENT upload mechanism than product files. They require Rails Active Storage's `signed_blob_id`.

```python
import hashlib, base64

# Step 1: Get XSRF token from Gumroad page
session = requests.Session()
session.get("https://duyhoivu.gumroad.com/l/ewshm")
xsrf = session.cookies.get("XSRF-TOKEN", "")

# Step 2: Direct upload to get signed_blob_id
with open("cover.jpg", "rb") as f:
    data = f.read()
checksum = base64.b64encode(hashlib.md5(data).digest()).decode()

direct = session.post(
    "https://app.gumroad.com/rails/active_storage/direct_uploads",
    headers={
        "X-CSRF-Token": xsrf,
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
    json={"blob": {
        "filename": "cover.jpg",
        "content_type": "image/jpeg",
        "byte_size": len(data),
        "checksum": checksum,
    }}
).json()

signed_id = direct["signed_id"]
upload_url = direct["direct_upload"]["url"]
upload_headers = direct["direct_upload"]["headers"]

# Step 3: Upload bytes to presigned URL
requests.put(upload_url, data=data, headers=upload_headers)

# Step 4: Set as cover on product
requests.post(f"{BASE}/products/{PRODUCT_ID}/covers",
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    json={"signed_blob_id": signed_id})
```

### 5. Set Thumbnail — Same Rails Flow, Different Endpoint

```python
# Same steps 1-3 as cover, then:
requests.post(f"{BASE}/products/{PRODUCT_ID}/thumbnail",
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    json={"signed_blob_id": signed_id})
```

**PITFALL:** The cover endpoint is `/covers` (plural), NOT `/cover` (singular returns 404).

**PITFALL:** The thumbnail endpoint is `/thumbnail` (singular). Do NOT try to set it via PUT with multipart `thumbnail=` field — the API explicitly rejects it and tells you to use `POST /v2/products/:id/thumbnail with a signed_blob_id`.

### 6. Verify Product State

```python
resp = requests.get(f"{BASE}/products/{PRODUCT_ID}", params={"access_token": TOKEN}).json()
p = resp["product"]
# p["published"] — True/False
# p["short_url"] — "https://seller.gumroad.com/l/permalink"
# p["covers"] — array of cover objects with url, width, height
# p["thumbnail_url"] — direct URL to thumbnail
# p["files"] — array of attached files
```

## Undocumented Endpoints Discovered

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `/v2/products/:id/covers` | POST | Set cover image | Bearer token + signed_blob_id |
| `/v2/products/:id/thumbnail` | POST | Set thumbnail | Bearer token + signed_blob_id |
| `/v2/files/presign` | POST | Get S3 presigned URL for file upload | access_token in body |
| `/v2/files/complete` | POST | Complete multipart upload | access_token in body (JSON) |
| `/rails/active_storage/direct_uploads` | POST | Get signed_blob_id for images | XSRF-TOKEN cookie |

## Key Patterns

### JSON Body vs Form Data
- **Product creation:** Use `data=` (form params)
- **Product update (PUT):** Use `json=` with `Authorization` header
- **File complete:** Use `json=` (NOT form data)
- **Presign:** Use `data=` (form params)

### Error Messages Are Documentation
Gumroad's API error messages reveal undocumented endpoints:
- `"Use POST /v2/products/:id/thumbnail with a signed_blob_id"` — from PUT with thumbnail field
- `"files must be an array of file objects"` — from wrong files format

Always read the full error response — it often tells you the correct approach.

### Rails Active Storage Pattern (General)
Any Rails app using Active Storage follows this flow:
1. `POST /rails/active_storage/direct_uploads` with blob metadata → returns `signed_id` + presigned S3 URL
2. `PUT <presigned_url>` with raw bytes
3. Use `signed_id` in the parent model's attachment field

This pattern is used by Gumroad, Shopify, Basecamp, and many Rails apps. The CSRF token comes from the session cookie (XSRF-TOKEN).

## Files Created During This Session
- `product.pdf` — 11-page Veo 3 prompt pack (40 prompts, 22KB)
- `cover.jpg` — 1280×720 product cover image
- `thumbnail.jpg` — 600×600 product thumbnail
