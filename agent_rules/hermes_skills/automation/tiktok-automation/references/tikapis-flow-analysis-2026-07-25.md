# TikFollowers.com + TikAPIs.com Flow Analysis (2026-07-25)

## Architecture
```
[User Browser] → [tikfollowers.com] (PHP + Cloudflare) → [tikapis.com API] → [TikTok]
```

## tikfollowers.com API (NO AUTH REQUIRED)

### Search Endpoint
```
POST https://tikfollowers.com/api/search
Body: {"input": "VIDEO_ID", "type": "videoDetails"}
Response: {status, token, username, aweme_id, user_id, sec_uid, stats, success}
```

### Process Endpoint
```
POST https://tikfollowers.com/api/process
Body: {<entire search response>, "type": "video_views"}
Response: {status, message: "Your request for N video_views...", data: {amount_processed}, success}
```

### Available Service Types
| Page | processApiType | formApiType |
|------|---------------|-------------|
| /free-tiktok-video-views | video_views | videoDetails |
| /free-tiktok-like | like | videoDetails |
| /free-tiktok-followers | followers | getUserDetails |
| /free-tiktok-shares | video_shares | videoDetails |

### Config (inline in HTML)
- `recaptchaEnabled: false` (reCAPTCHA DISABLED)
- `recaptchaSiteKey: '6Lc6bT4rAAAAAIq5n21JThEIbULSv73FcTr-V2mf'`
- `processWaitTimeSeconds: 13-20` (client-side setTimeout, NOT real processing)
- `cooldown: ~13 min per TARGET video (NOT per-IP)`

## tikapis.com API (BACKEND)

### Status: DOWN (HTTP 500) as of 2026-07-25
- All `/api/*` endpoints return "Service temporarily unavailable"
- `api-v4.tikapis.com` does NOT exist in DNS
- Key validation works: no key → 401, wrong key → 401, valid key → 500

### API Keys (valid)
- Android: `b6b12336-bfef-4be1-8112-72ba8e878d6b`
- iOS: `7892688e-4e58-410c-b095-9e1a3b02595d`

### Endpoints (from docs)
- POST /api/device_register
- POST /api/video/stats/{video_id} ← views
- POST /api/user/follow/{user_id}/{sec_uid}
- POST /api/video/like/{video_id}
- POST /api/algorithm/mssdk_encrypt

### Device Config Template (VN)
```json
{
  "country_location": {
    "carrier_region_v2": "452",
    "mcc_mnc": "45201",
    "lang_b": "VN",
    "operator": "Viettel",
    "timezone": 7,
    "tz_name": "Asia/Ho_Chi_Minh"
  },
  "proxy": "user:pass@host:port",
  "cookie": "store-country-code=vn"
}
```

## Test Results (2026-07-25)

| Test | Method | Views Claimed | Views Actual |
|------|--------|--------------|-------------|
| tikfollowers direct | curl | +1,141 | +0 |
| tikfollowers via VN proxy | curl | +2,496 | +0 |
| tikfollowers via Playwright | browser | +2,651 | +0 |
| tikapis Android key | API | N/A (500) | N/A |
| tikapis iOS key | API | N/A (500) | N/A |

**Conclusion: tikfollowers.com ALWAYS returns "success" but views DON'T COUNT.**
Root cause: tikapis.com backend is DOWN. Frontend is a LIE.

## VN Proxy Behavior
- VN proxy only affects client→tikfollowers connection
- tikfollowers→tikTok uses their own servers (Algeria config)
- No geo/country parameters in API
- Cooldown is per-TARGET, NOT per-IP
