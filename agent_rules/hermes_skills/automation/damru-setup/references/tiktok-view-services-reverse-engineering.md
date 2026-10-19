# TikTok View Services — Reverse Engineering (July 2026)

## tikfollowers.com Architecture (CONFIRMED WORKING)

### Flow
```
User → tikfollowers.com → tikapis.com API → TikTok Internal API
```
- **Frontend:** Static HTML + inline JS at `tikfollowers.com`
- **Backend:** tikapis.com reverse-engineered TikTok Private API
- **Result:** ~832 views per cycle, ~13 min cooldown

### API Endpoints (Reverse-Engineered)

#### Step 1: Search video
```http
POST https://tikfollowers.com/api/search
Content-Type: application/json
X-Requested-With: XMLHttpRequest

{"input": "VIDEO_ID", "type": "videoDetails"}
```
Response:
```json
{
  "status": "success",
  "token": "...",
  "username": "...",
  "aweme_id": "...",
  "user_id": ...,
  "sec_uid": "...",
  "aweme_avatar": "...",
  "stats": {"play_count": ..., "digg_count": ..., ...}
}
```

#### Step 2: Process views
```http
POST https://tikfollowers.com/api/process
Content-Type: application/json
X-Requested-With: XMLHttpRequest

{
  "username": "...",
  "aweme_id": "...",
  "user_id": ...,
  "sec_uid": "...",
  "aweme_avatar": "...",
  "stats": {...},
  "type": "video_views",
  "token": "..."  // REQUIRED from search response
}
```
Response: `{"status":"success","message":"Your request for 832 video_views for @username has been completed successfully."}`

Error codes:
- `403 InvalidOrExpiredToken` — token missing or expired
- `429 Cooldown` — rate limited, message includes wait time

#### Frontend Config (from inline JS)
```javascript
processApiType: "video_views",
formApiType: "videoDetails",
recaptchaEnabled: false,  // Currently DISABLED
recaptchaSiteKey: '6Lc6bT4rAAAAAIq5n21JThEIbULSv73FcTr-V2mf',
baseUrl: 'https://tikfollowers.com/',
processWaitTimeSeconds: 13-20, // random delay
```

### Puppeteer/Selenium Automation Flow
1. Navigate to `https://tikfollowers.com/free-tiktok-video-views`
2. Wait for Search button text to change from "Loading..." to "Search"
3. Fill `#inputFieldEl` with video URL
4. Click `button:has-text("Search")`
5. Wait for `/api/search` response (200)
6. Wait 2s, click `#startProcessBtnEl`
7. Click `.swal2-confirm` (OK modal)
8. Wait for `/api/process` response (~15-20s)
9. Parse success message for view count

---

## tikapis.com SDK (OPEN SOURCE)

### GitHub Repos
- `tikapiscom/TikTok-Private-Api-TikApis.com` (14★) — Python SDK
- `tikapiscom/tikapis.com` — API client library
- `nullcodss/tiktok-private-api` — X-Gorgon, X-Argus algorithms (1★)

### API Architecture
```
Base: https://tikapis.com/private/android/v1/
Auth: api-key header + x-api-key header
Free tier: $0/month, 1000 requests/day
```

### Key Endpoints
```
POST /service/template       → Device template
POST /service/register       → Device register
POST /mssdk/token            → Get MSSDK token
POST /mssdk/get_seed         → Get MSSDK seed
POST https://api-v4.tikapis.com/video/stats/{id} → Send views
POST https://api-v4.tikapis.com/device_register   → Device registration
```

### Device Registration Flow
```python
from AndroidTikApis import AndroidTikApis

device = {
    "proxy": "username:password@ip:port",  # SOCKS5 or HTTP
    "app_info": {
        "aid": 1233,
        "app_version": "34.0.2",
        "version_code": "340002",
        "manifest_version_code": "2023400020",
    },
    "country_location": {},  # Auto-detected from proxy IP
    "mssdk_parameters": {"lc_sdk_version": 134252544},
}

tik = AndroidTikApis(**device)
tik.device_template()    # Get device template from API
tik.device_register()    # Register device
tik.get_token()          # Get MSSDK token
tik.get_seed()           # Get MSSDK seed
# Now can send views:
result = tik.api_request("video/stats/VIDEO_ID")
```

### Proxy + Geo-Detection
- SDK auto-detects proxy country via `ipinfo.io`
- Sets `tz_name`, `lang_b` (country code), `lang_k` (language) automatically
- Vietnamese proxy → `Asia/Ho_Chi_Minh` timezone, `vi` locale
- **This is how tikfollowers.com gets foreign views** — their backend uses non-VN proxies

### Encryption Algorithms (tikapis.com handles internally)
- X-Argus, X-Ladon, X-Gorgon, X-Khronos, X-Helios, X-Medusa
- MSSDK token/seed system
- Device fingerprint generation
- Protobuf encoding

---

## Other Services Tested

### Vietnamese Services
| Service | Status | Notes |
|---------|--------|-------|
| like.vn | Online | Vietnamese SMM panel, has TikTok views, has API |
| likeqq.vn | Online | Lists "10 web tăng view TikTok miễn phí" |
| 100like.vn | Online | Free Vietnamese view tool |
| freer.es | DEAD (502) | Was alternative to Zefoy |
| zefoy.com | Views service DOWN | CAPTCHA-heavy, services intermittently available |

### Direct API Status (July 2026)
- `/aweme/v1/aweme/stats/` → 403 Access Denied (PATCHED)
- `/aweme/v1/play/` → 200 status_code=0 but NO view increase (telemetry only)
- All internal TikTok API domains block direct access

---

## Vietnamese View Strategy

### Best Approach: tikapis.com SDK + Vietnamese SOCKS5 Proxy
1. Register tikapis.com free account → get API key
2. Clone SDK from GitHub
3. Configure with Vietnamese SOCKS5 proxy
4. SDK auto-detects Vietnam → Vietnamese locale/timezone
5. Register device → send views
6. Each proxy = unique device = unique view

### Proxy Requirements
- Must be residential SOCKS5 (datacenter flagged)
- Vietnamese IP for Vietnamese views
- Format: `socks5://user:pass@host:port`
- Providers: 911.re, Bright Data, Oxylabs, Smartproxy
