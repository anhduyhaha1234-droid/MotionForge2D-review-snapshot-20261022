
# Gumroad API v2 — Complete Flow Reference

## Discovery Process (July 2025)
The Gumroad API v2 documentation does NOT clearly document the file upload flow. This was discovered through trial and error.

## Working Endpoints

### GET /v2/user — Verify token
```bash
curl -s "https://api.gumroad.com/v2/user" -H "Authorization: Bearer TOKEN"
```
Returns: user name, id, email, profile URL, Gumroad URL.

### POST /v2/products — Create product
```bash
curl -X POST "https://api.gumroad.com/v2/products" \
  -d "access_token=TOKEN" \
  -d "name=Product Name" \
  -d "description=Description..." \
  -d "price=0" \
  -d "customizable_price=true" \
  -d "published=true"
```
Returns: product object with `id` (base64), `short_url`, `formatted_price`.

### POST /v2/files/presign — Get S3 upload URL
```bash
curl -X POST "https://api.gumroad.com/v2/files/presign" \
  -d "access_token=TOKEN" \
  -d "filename=product.pdf" \
  -d "content_type=application/pdf" \
  -d "file_size=22224"
```
Returns:
```json
{
  "success": true,
  "upload_id": "i29WqmsQU9bulsu...",
  "key": "attachments/USER_ID/HASH/original/filename.pdf",
  "file_url": "https://s3.amazonaws.com/gumroad/attachments/...",
  "parts": [{"part_number": 1, "presigned_url": "https://gumroad.s3.amazonaws.com/..."}]
}
```

### PUT to S3 presigned URL — Upload file data
```bash
curl -X PUT "PRESIGNED_URL" \
  -H "Content-Type: application/pdf" \
  --data-binary @product.pdf
```
Returns: HTTP 200 with `ETag` header.

### POST /v2/files/complete — Finalize upload
**MUST use JSON body:**
```bash
curl -X POST "https://api.gumroad.com/v2/files/complete" \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "TOKEN",
    "upload_id": "UPLOAD_ID",
    "key": "attachments/...",
    "parts": [{"part_number": 1, "etag": "ETAG_VALUE"}]
  }'
```
Returns: `{"success": true, "file_url": "https://s3.amazonaws.com/gumroad/..."}`

### PUT /v2/products/:id — Attach files and update
**MUST use JSON body with Authorization header:**
```bash
curl -X PUT "https://api.gumroad.com/v2/products/PRODUCT_ID" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "published": true,
    "files": [{"url": "https://s3.amazonaws.com/gumroad/attachments/.../file.pdf"}]
  }'
```

### GET /v2/products/:id — Check product state
```bash
curl -s "https://api.gumroad.com/v2/products/PRODUCT_ID?access_token=TOKEN"
```
Returns full product object including `files`, `covers`, `thumbnail_url`, `published`.

## Error Messages Encountered

| Error | Cause | Fix |
|-------|-------|-----|
| `"filename is required"` | Used `name` instead of `filename` in presign | Change to `filename` |
| `"file_size is required"` | Used `size` instead of `file_size` in presign | Change to `file_size` |
| `"PartNumber must be >= 1"` | Used form data for complete endpoint | Use JSON body with `parts` array |
| `"key is required"` | Missing `key` in complete request | Include `key` from presign response |
| `"'file' is not an accepted parameter"` | Tried multipart file upload on PUT | Use presign flow instead |
| `"files must be an array of file objects"` | Used form-encoded `files[0][url]` | Use JSON body `{"files": [{"url": "..."}]}` |
| Page not found (404) on `/files` | File upload endpoint doesn't exist as POST to product | Use presign flow |

## Complete Python Script (Working)

```python
import requests, json, os

TOKEN = "YOUR_TOKEN"
BASE = "https://api.gumroad.com/v2"

def upload_file(filepath, filename, content_type):
    file_size = os.path.getsize(filepath)
    
    # Presign
    presign = requests.post(f"{BASE}/files/presign", data={
        "access_token": TOKEN,
        "filename": filename,
        "content_type": content_type,
        "file_size": str(file_size),
    }).json()
    
    upload_id = presign["upload_id"]
    key = presign["key"]
    file_url = presign["file_url"]
    part_url = presign["parts"][0]["presigned_url"]
    
    # Upload to S3
    with open(filepath, "rb") as f:
        data = f.read()
    s3_resp = requests.put(part_url, data=data, headers={"Content-Type": content_type})
    etag = s3_resp.headers.get("ETag", "")
    
    # Complete
    requests.post(f"{BASE}/files/complete", json={
        "access_token": TOKEN,
        "upload_id": upload_id,
        "key": key,
        "parts": [{"part_number": 1, "etag": etag}],
    }).json()
    
    return file_url

def create_product(name, description, price=0):
    resp = requests.post(f"{BASE}/products", data={
        "access_token": TOKEN,
        "name": name,
        "description": description,
        "price": price,
        "customizable_price": True,
        "published": True,
    })
    return resp.json()["product"]

def attach_file(product_id, file_url):
    resp = requests.put(f"{BASE}/products/{product_id}",
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        json={"published": True, "files": [{"url": file_url}]})
    return resp.json()
```

## Gumroad Account Details (User: Duy)
- Gumroad URL: https://duyhoivu.gumroad.com
- Display name: Anh Duy Trịnh
- Email: duyhoivu.hn@gmail.com
- User ID: 5142874753538
- Currency: USD
