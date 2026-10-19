# TikTok View Services — Reverse Engineering Findings
## Last updated: 2026-07-23

## tikfollowers.com

### Architecture (3 layers)
```
[tikfollowers.com] (PHP + Cloudflare + ci_session cookie)
  → [tikapis.com API v4] ("TikTok Private API & ByteDance Encryption Algorithms")
    → [TikTok Private API] (fake device requests with valid encryption signatures)
```

### API Endpoints (NO AUTH, NO reCAPTCHA)

**Search:**
```
POST https://tikfollowers.com/api/search
Content-Type: application/json
X-Requested-With: XMLHttpRequest
Referer: https://tikfollowers.com/free-tiktok-video-views
Origin: https://tikfollowers.com

Body: {"input": "<19-digit_video_id>", "type": "videoDetails"}
Response: {status, token, username, aweme_id, user_id, sec_uid, stats: {play_count, digg_count, ...}}
```

**Process:**
```
POST https://tikfollowers.com/api/process
(same headers)

Body: {<entire search response>, "type": "video_views"}
Response: {status:"success", message:"Your request for 1141 video_views for @user...", data:{amount_processed:1141}}
```

### Available Service Types
| Page path | processApiType | formApiType | Input format |
|---|---|---|---|
| /free-tiktok-video-views | video_views | videoDetails | 19-digit video ID |
| /free-tiktok-like | like | videoDetails | video URL or ID |
| /free-tiktok-followers | followers | getUserDetails | @username |
| /free-tiktok-shares | video_shares | videoDetails | video URL or ID |

### Rate Limits & Timing
- Cooldown: ~13 min per IP per service per target (observed 2026-07-23, was previously ~5 min)
- Amount per call: ~832-1200 views (varies by service availability)
- Token: short-lived, must be INCLUDED in process body (omit → "InvalidOrExpiredToken" 403)
- Without token: `POST /api/process` returns `{"status":"error","message":"InvalidOrExpiredToken"}`
- With token but on cooldown: returns 429 with `additional_offers` array (upsell)
- reCAPTCHA: currently DISABLED (`recaptchaEnabled: false` in inline config)
- **Fake progress bar:** `AppUtils.randint(8, 11)` seconds before reCAPTCHA check / API call triggers
- **Fake process wait:** `AppUtils.randint(13, 20)` seconds between clicking "Start Earning" and the `/api/process` call fires (purely cosmetic setTimeout)
- **Navigation lock:** `beforeunload` + `visibilitychange` handlers prevent tab-switch during process (irrelevant for headless, but blocks Playwright `page.close()` during automation)
- **Retry config:** max 1 retry on timeout (10s per attempt), 2s delay between retries

### Inline JS Config Pattern
Each service page embeds config in an inline `<script>` block:
```javascript
const config = {
    processApiType: "video_views",
    formApiType: "videoDetails",
    recaptchaEnabled: false,
    recaptchaSiteKey: '6Lc6bT4rAAAAAIq5n21JThEIbULSv73FcTr-V2mf',
    apiTimeoutMilliseconds: 10000,
    maxApiRetries: 1,
    apiRetryDelay: 2000
};
```

### ServiceItems Array
Homepage defines all services in a `const serviceItems = [...]` array with:
- `tryNowLink`: service page path
- `title`, `description`, `relatedSearches`
- Each maps to a processApiType

### Input Validation (Client-Side Regex)
For `type: "videoDetails"`:
```
Full URL: /^https?:\/\/(?:www\.)?tiktok\.com\/@[\w.-]+\/(?:video|photo)\/(\d{19})(?:\S+)?/
Short URL: /^https?:\/\/vm\.tiktok\.com\/([\w-]+)\/?/
Bare ID: /^\d{19}$/
```
If full URL matches, only the 19-digit video ID is sent. If short URL matches, the full short URL is sent. For `type: "getUserDetails"`, `@` prefix is stripped.

### HTML Form Structure
```html
<input id="inputFieldEl" type="text" placeholder="Enter TikTok URL">
<input type="hidden" id="typeFieldEl" value="videoDetails">  <!-- type field -->
<button id="searchBtnEl">Search</button>
<button id="startProcessBtnEl">Start Earning</button>
```

### Translation Keys Reveal API Errors
The `var translations = {...}` object on every page contains all possible error messages including:
- `Invalid request: 'input' or 'username' is required.`
- `Invalid request: 'type' is required.`
- `Invalid google_token.` (reCAPTCHA)
- `CooldownError` with `{target}`, `{minutes}`, `{seconds}` placeholders

---

## tikapis.com (Backend Infrastructure)

### What It Is
- "TikTok Private API & ByteDance Encryption Algorithms"
- Provides reverse-engineered TikTok private API
- Supports: Android, iOS, Web, Windows, Captcha, General
- Telegram: @tikapiscom, Discord available
- Also on RapidAPI: https://rapidapi.com/tikapiscom/api/tiktok-tikapis-com
- GitHub org: github.com/tikapiscom (multiple repos)
- Version: v1.0, Released December 24, 2024
- Behind Cloudflare (104.21.6.23, 172.67.154.149)

### Two API Versions in Codebase

**Version 1 (Older — `tikapis.com/tikapis.com` repo):**
- Base URL: `https://tikapis.com/api/android`
- Auth: `{'api-key': key, 'Content-Type': 'application/json'}`
- Endpoints: `/device_template`, `/device_register`, `/get_token`, `/get_seed`, `/get_sign`, `/get_token_decode`, `/get_seed_decode`
- TikTok domain: `api-va.tiktokv.com`

**Version 2 (Newer — `tikapiscom/TikTok-Private-Api-TikApis.com` repo):**
- Base URL: `https://tikapis.com/private/android/v1/`
- Auth: `{'api-key': key, 'x-api-key': key, 'Content-Type': 'application/json'}`
- Endpoints: `/service/template`, `/service/register`, `/sign/create`, `/mssdk/token`, `/mssdk/get_seed`, `/mssdk/token_decode`, `/mssdk/seed_decode`, `/captcha/solver`
- Additional: `/commit/user/*`, `/message/*`, `/passport/*`
- TikTok domain: `api-boot.tiktokv.com`

**Documentation shows `api-v4.tikapis.com`** but DNS doesn't resolve — likely proxied through main domain or internal routing.

### Complete Device Lifecycle Flow

```
1. device_template()     → Get device fingerprint template for app_version
2. device_register()     → Register virtual device with TikTok (returns method + url for HTTP request)
3. tiktok_auto_request() → Execute the HTTP request TikTok returned (may redirect → re-sign each hop)
4. extract_ids()         → Extract device_id_str, install_id_str from response
5. get_token()           → MSSDK token (two-phase: request→auto-request→decode hex)
6. get_seed()            → MSSDK seed (same two-phase process)
7. [Active device checks]:
   - service/app_alert_check
   - mssdk/ri/report
   - mssdk/ri/did-iid-update
   - mssdk/common_setting
   - mssdk/common_config
   - mssdk/ri/image
8. app_region()          → Detect user's region → get correct TikTok domain + captcha domain
9. account_register()    → Register new TikTok account (email/password via XOR encoding)
10. Login/auth           → Get x-tt-token, x-bd-client-key, cookies
11. get_sign()           → Sign URLs with X-Argus, X-Ladon headers
12. perform_action()     → Execute follow/like/view/etc against TikTok
```

### All api-v4 Endpoints (from docs)

**Device:**
- `POST /device_register` (Android + iOS)

**Algorithm (11 endpoints):**
- `/algorithm/mssdk_encrypt`, `/algorithm/mssdk_decrypt`
- `/algorithm/tt/encrypt`, `/algorithm/tt/decrypt`
- `/algorithm/x-argus/encrypt`, `/algorithm/x-argus/decrypt`
- `/algorithm/x-ladon/encrypt`, `/algorithm/x-ladon/decrypt`
- `/algorithm/x-cylons/encrypt`, `/algorithm/x-cylons/decrypt`
- `/algorithm/sign`

**Passport (9 endpoints):**
- `/passport/login`, `/passport/register`
- `/passport/mobile/login`, `/passport/mobile/login/check_code`
- `/passport/mobile/signup`, `/passport/mobile/signup/check_code`
- `/passport/email/signup`, `/passport/email/signup/check_code`
- `/passport/reset-password-email`, `/passport/reset-by-email-password`
- `/passport/im/reboot/misc`, `/passport/token/beat`

**Manipulations (8 endpoints):**
- `/video/like/{id}`, `/video/unlike/{id}`
- `/video/stats/{id}` ← THE VIEWS ENDPOINT
- `/story/like/{id}`, `/story/unlike/{id}`
- `/save/{id}`
- `/user/follow/{uid}/{sec_uid}`, `/user/unfollow/{uid}/{sec_uid}`

**Comments (4):** publish, like, unlike, delete
**User (5):** self, profile, followers, followings, posts
**Video (2):** multi aweme details, comments by video ID
**Account Edit (4):** biography, nickname, username, profile picture
**Account Reset (2):** reset password email, reset by email password
**Captcha (3):** Whirl, Slide, 3D — all at `/tiktok/captcha/solver`

### Headers Required for Manipulation Endpoints
| Header | Value | Required |
|--------|-------|----------|
| `X-Platform` | `android` or `ios` | Yes |
| `X-App-aid` | `1233` (TikTok) | Yes |
| `x-api-key` | API key from account | Yes |
| `Device Config` | JSON from login response | Yes |

### Views Request Body Structure
```json
{
  "app_info": {"aid": 1233, "app_name": "musical_ly", "app_version": "38.4.3", ...},
  "cookie": "store-idc=alisg; store-country-code=dz; install_id=...; ttreq=...",
  "country_location": {"carrier_region_v2": "603", "mcc_mnc": "60302", "operator": "Djezzy", "tz_name": "Africa/Algiers", ...},
  "device": {"device_id": "7473626842902200000", "install_id": "7473642654652600000", "build.model": "SM-N950F", "openudid": "...", "cdid": "...", "clientudid": "...", ...},
  "domain_selection": {"domain_normal": ["api16-normal-c-alisg.tiktokv.com"], "domain_captcha": ["verification-sg.tiktokv.com"], "domain_mssdk": ["mssdk16-normal-alisg.tiktokv.com"], ...},
  "mssdk_parameters": {"sdk_ver": "v05.01.06-alpha.11-ov-android"},
  "network_data": {"access": "wifi"},
  "proto_data": {"AppUsage": 9, "reportCount": 18, "signCount": 192, ...},
  "proxy": "username:password@ip:port",
  "user": {},
  "x_token": ""
}
```

### ByteDance Encryption Algorithms Implemented
| Algorithm | Purpose |
|-----------|---------|
| X-Argus | Data integrity encryption |
| X-Ladon | Unauthorized access protection |
| X-Gorgon | Cryptographic hash for authentication |
| X-Khronos | Timestamp verification (anti-replay) |
| X-Cylons | Additional encryption layer |
| X-Helios | Data processing |
| X-Medusa | Rapid encryption/decryption |
| TTEncrypt | Transmission encryption |
| MSSDK encrypt/decrypt | Mobile Security SDK encryption |
| MSSDK /ri/report | Device reporting |
| Get seed | Seed data retrieval |
| MSCC Common Setting | MSSDK settings |
| MSToken | Web authentication token |
| _signature | Web API request signature |
| X-Bogus | Web error handling |

### Supported MSSDK Versions (27 total)
v04.02.03 → v04.03.09 → v04.04.00 → v04.09.02 → v05.00.00 through v05.02.06

### Supported Apps

**Android (19):** musical_ly, trill, lite, musically_go, aweme (Douyin), tiktok_studio, tiktok_snail, picovr_assistant_overseas, tiktokspark, tiktok_tv, tiktokseller, TikTok Now, vicut, tiktok_music, Resso, Hypic, beauty_me_oversea, bd_nproject, fans_app

**iOS (7):** (similar subset)

### TikTok Internal Endpoints Targeted
- `aweme/v1/commit/follow/user/` — Follow
- `aweme/v1/commit/item/digg/` — Like
- `lite/v2/relation/follow/` — Follow (Lite app)
- `lite/v2/item/digg/` — Like (Lite app)
- `passport/email/register/v2/` — Account creation
- `passport/app/region/` — Region detection

**TikTok domain pool:**
- api-boot.tiktokv.com (primary)
- api16-normal-c-alisg.tiktokv.com (Singapore)
- api16-normal-c-useast1a.tiktokv.com (US East)
- api16-normal-c-useast2a.tiktokv.com
- api16-normal-useast5.us.tiktokv.com
- mssdk16-normal-alisg.tiktokv.com (MSSDK)
- verification-sg.tiktokv.com (Captcha)
- log16-normal-alisg.tiktokv.com (AppLog)

### HTTP Client Implementation Details
- Custom SSL adapter with specific cipher suite (ECDHE+AESGCM, ECDHE+CHACHA20, etc.)
- Automatic redirect handling with re-signing at each hop (X-Argus headers regenerated)
- Cookie jar management (merges Set-Cookie with existing cookies)
- Proxy support (SOCKS5 and HTTP)
- Bytes → hex conversion for binary payloads

### Registration & API Key Access (tested 2026-07-23)
- Registration: `POST https://tikapis.com/auth/register` with `{username, email, password}` → 302 redirect to `/user/dashboard`, session cookie set
- Login: `POST https://tikapis.com/auth/login` → may return 500 (intermittent)
- Dashboard at `/user/dashboard` shows "API Keys (0)" — NO button/form to generate keys
- `/user/api-keys` page: "No API keys found", no generate option
- **API key MUST be obtained externally:** Contact Telegram @tikapiscom or subscribe via RapidAPI
- Without API key: `GET /api` returns 401 `{"error":"API key is missing"}`; all other paths return 404 HTML
- `api-v4.tikapis.com` does NOT resolve via DNS (nslookup fails) — docs show it but actual API is behind tikapis.com main domain
- SDK repos: `tikapiscom/TikTok-Private-Api-TikApis.com` (v2), `tikapiscom/tikapis.com` (v1)
- SDK auto-detects proxy country via ipinfo.io and sets timezone/locale accordingly

### API Key Testing Results (tested 2026-07-23, key: authenticated)
With a valid API key in `api-key` + `x-api-key` headers:
- **`GET /api`** → 401 "API key is missing" WITHOUT key; with key, the error changes (key is recognized)
- **`POST /api/video`** (no X-App-Aid header) → 400 `{"error":"X-App-Aid is required"}` ← **endpoint EXISTS**
- **`POST /api/user`** (no X-App-Aid header) → 400 `{"error":"X-App-Aid is required"}` ← **endpoint EXISTS**
- **`POST /api/video`** (with `X-App-Aid: 1233` + `X-Platform: android`) → 500 `{"error":"Service temporarily unavailable"}`
- **All other endpoints** (`/api/device_template`, `/api/template`, `/api/register`, `/api/token`, `/api/seed`, etc.) → "Route not found"
- **Conclusion:** The `/api/video` and `/api/user` endpoints are the real API paths. The 500 error suggests the service may be intermittently down or the free tier has limited availability. RapidAPI subscription may provide more reliable access.
- **RapidAPI host:** `tiktok-tikapis-com.p.rapidapi.com` — returns 404 "API doesn't exists" for most endpoints (may need different host name or the API may be listed under a different slug)

### Backend Status: DOWN (as of 2026-07-23 live testing)
**ALL tikapis.com API endpoints return "Service temporarily unavailable"** even with a valid API key. The key validation itself works (different errors for missing/invalid/valid), but the actual TikTok manipulation service is completely down.

**Impact:** tikfollowers.com still returns `status: "success"` with `amount_processed: 2496` but ZERO views are actually added. The frontend is a pass-through that doesn't verify backend delivery.

**Verification method:** Track `play_count` before and after. API claimed +3,637 views across 2 calls. Actual increase: +1 (natural traffic).

See `references/tikfollowers-live-test-results.md` for full test data.

### Pricing Tiers
| Tier | Platform | Fee | Daily | Weekly | Monthly | Rate/min |
|------|----------|-----|-------|--------|---------|----------|
| Free | iOS | $0/mo | 200 | 1,400 | 6,000 | 15 |
| Free | Android | $0/mo | 1,000 | 5,000 | 15,000 | 25 |
| Basic | Captcha | $120/mo | 1,000 | 7,000 | 30,000 | 100 |

---

## Geo-Restriction: Why VN-Locked (and Similar) Content Fails

**The problem:** TikTok checks viewer's geolocation via TWO mechanisms:
1. **IP geolocation** — must be from target country
2. **Device `country_location`** — must match (MCC, carrier, timezone, language)

tikfollowers.com's backend (tikapis.com) defaults to **Algeria** config:
```json
"country_location": {"carrier_region_v2": "603", "lang_b": "DZ", "mcc_mnc": "60302", "tz_name": "Africa/Algiers"},
"cookie": "store-country-code=dz"
```
→ Views from non-VN infrastructure are NOT counted for VN-locked videos.

**Vietnam device config required (MCC 452):**
```json
{
  "carrier_region_v2": "452",
  "lang_b": "VN",
  "mcc_mnc": "45201",
  "operator": "Viettel",
  "timezone": 7,
  "tz_name": "Asia/Ho_Chi_Minh",
  "tz_offset": 25200,
  "gmt": "GMT+07:00"
}
```
Vietnamese carriers: Viettel (45201/04/06), Mobifone (45202), Vinaphone (45203).

**Solution options for geo-locked content:**
1. tikapis.com API with target-country `country_location` + residential proxy from that country
2. Use country-specific SMM panels that already have matching infrastructure

**CRITICAL: Proxy chain mismatch** — Using a VN proxy to CALL tikfollowers.com does NOT make views count as VN. The proxy only affects user→tikfollowers connection. The actual view generation goes through tikapis.com's backend servers (Singapore/Algeria), not through your proxy. To control the proxy for the final TikTok hop, you need direct API access to tikapis.com with a `"proxy"` field in the request body.

**Cooldown is per-TARGET not per-IP:** Different proxies still share the same cooldown for the same video/username. The backend identifies the target, not the caller's IP.

See `references/tikfollowers-live-test-results.md` for live test data confirming these findings.

---

## Vietnamese SMM Panels

### like.vn (Largest VN SMM Panel)
- 5M+ orders, 289K members, 251 servers, 8+ years
- Laravel (Symfony) backend, Cloudflare-protected
- Claims "Hỗ trợ cả TikTok Việt Nam và quốc tế"

**TikTok view servers:**
| Server | Price | Notes |
|---|---|---|
| SV1 | 3.2₫/view | Warranty, fast |
| SV2 | 2.88₫/view | Slow, warranty |
| SV3 | 1.9₫/view | Warranty |
| SV4 | 0.7₫/view | No warranty, often disabled |
| SV5 | FREE ⭐ | Free tier |

- `api-token` meta tag in HTML (empty when logged out — needs auth)
- API at `/api/` behind auth; `/api/v1/services` returns 404 (route not found, confirms Laravel)

### Other VN panels (all Cloudflare-protected, 0 bytes to curl)
- hacklike.vn (Facebook-focused)
- tuongtaccheo.com (cross-platform exchange)
- seeding.vn, likesub.vn
