# Gumroad API v2 — Session Notes

## File Upload Flow (Hard-Won Knowledge)

### What DOESN'T work:
- `POST /v2/products/:id/files` → 404 (endpoint doesn't exist)
- `PUT /v2/products/:id` with `files={"file": open(f)}` → "file is not an accepted parameter"
- Form-encoded `files[0][url]=...` → "files must be an array of file objects"
- `complete` with form-encoded `parts[0][part_number]=1` → "PartNumber must be >= 1"

### What DOES work:
1. Presign with `filename` + `file_size` (form data)
2. S3 PUT with binary body + Content-Type header
3. Complete with JSON body and `parts` as JSON array
4. Attach with JSON body and `files` as JSON array

## Cover Image Attempts (All Failed Silently)

| Attempt | Result |
|---------|--------|
| `files={"cover": ("cover.jpg", f, "image/jpeg")}` on PUT | API accepts (200) but covers stays [] |
| JSON `{"covers": ["https://s3..."]}` | success:true, covers stays [] |
| JSON `{"cover_url": "https://s3..."}` | success:true, covers stays [] |
| JSON `{"custom_cover_url": "https://s3..."}` | success:true, covers stays [] |
| JSON `{"thumbnail_url": "https://s3..."}` | success:true, thumbnail stays null |
| Presign + attach as file | Attaches as downloadable file, not cover |

## Chrome Profile for Dashboard Upload

Gumroad dashboard upload requires authenticated browser session. Options:
1. Playwright `launch_persistent_context` with Chrome profile — works if Chrome is NOT running
2. Selenium with `--user-data-dir` — same constraint
3. Chrome `--remote-debugging-port=9222` + CDP connect — only way to reuse running session
   - Requires BOTH `--user-data-dir` AND `--profile-directory` flags
   - Cookies encrypted with DPAPI (Windows) — copying profile dir loses auth

## Presign Response Shape

```json
{
  "success": true,
  "upload_id": "i29WqmsQU9bu...",
  "key": "attachments/USER_ID/HASH/original/filename.pdf",
  "file_url": "https://s3.amazonaws.com/gumroad/attachments/...",
  "parts": [{"part_number": 1, "presigned_url": "https://gumroad.s3.amazonaws.com/..."}]
}
```
