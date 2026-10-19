# Gumroad API v2 — Session Notes & Error Transcripts

## File Upload Flow (Hard-Won Knowledge)

The Gumroad API docs don't clearly explain file upload. Through trial and error:

### What DOESN'T work:
- `POST /v2/products/:id/files` → 404 (endpoint doesn't exist)
- `PUT /v2/products/:id` with `files={"file": open(f)}` → "file is not an accepted parameter"
- Form-encoded `files[0][url]=...` → "files must be an array of file objects"
- `complete` with form-encoded `parts[0][part_number]=1` → "PartNumber must be >= 1"

### What DOES work:
- Presign with `filename` + `file_size` (form data)
- S3 PUT with binary body + Content-Type header
- Complete with JSON body and `parts` as JSON array
- Attach with JSON body and `files` as JSON array

## Presign Response Shape

```json
{
  "success": true,
  "upload_id": "i29WqmsQU9bu...",
  "key": "attachments/USER_ID/HASH/original/filename.pdf",
  "file_url": "https://s3.amazonaws.com/gumroad/attachments/...",
  "parts": [{
    "part_number": 1,
    "presigned_url": "https://gumroad.s3.amazonaws.com/...?partNumber=1&uploadId=..."
  }]
}
```

## Complete Response Shape

```json
{
  "success": true,
  "file_url": "https://s3.amazonaws.com/gumroad/attachments/.../original/filename.pdf"
}
```

## Product Response Shape (relevant fields)

```json
{
  "success": true,
  "product": {
    "id": "gg0xJfFTJqGgjkBKPPiD4w==",
    "name": "Product Name",
    "short_url": "https://username.gumroad.com/l/xxxxx",
    "published": false,
    "formatted_price": "$0+",
    "customizable_price": true,
    "files": [{"id": "xxx", "name": null, "size": 22224, "url": "...", "filetype": "pdf"}],
    "file_info": {"Size": "21.7 KB", "Length": "11 pages"},
    "covers": [],
    "thumbnail_url": null
  }
}
```

## Cover Image Attempts (All Failed)

| Attempt | Result |
|---------|--------|
| `files={"cover": ("cover.jpg", f, "image/jpeg")}` on PUT | API accepts (200) but covers stays [] |
| JSON `{"covers": ["https://s3..."]}` | success:true, covers stays [] |
| JSON `{"cover_url": "https://s3..."}` | success:true, covers stays [] |
| JSON `{"custom_cover_url": "https://s3..."}` | success:true, covers stays [] |
| JSON `{"thumbnail_url": "https://s3..."}` | success:true, thumbnail stays null |
| Presign + attach as file | Attaches as downloadable file, not cover |

**Conclusion:** Cover/thumbnail must be set via web dashboard.

## User Account Details (for reference)

- Gumroad username: duyhoivu.gumroad.com
- Display name: Anh Duy Trịnh
- Email: duyhoivu.hn@gmail.com
- User ID: 5142874753538
- OAuth login via Google
