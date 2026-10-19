# TikTok View Manipulation — API Research Findings

> Captured 2026-07-23 from GitHub landscape research. Treat as starting points — endpoints may be patched.

## Approach 1: Direct TikTok Internal API

**Source:** Wizz1337/TikTokMassBotting (585 stars, last push 2026-07-07, marked "Patched")

### Endpoints
```
POST https://{api_domain}/aweme/v1/aweme/stats/?channel={channel}&device_type={device}&device_id={id}&os_version={ver}&version_code=220400&app_name={app}&device_platform={platform}&aid=1988
```

**API Domains (rotate):**
- `api22-core-c-useast1a.tiktokv.com`
- `api19-core-c-useast1a.tiktokv.com`
- `api16-core-c-useast1a.tiktokv.com`
- `api21-core-c-useast1a.tiktokv.com`

### Payloads
- View: `item_id={video_id}&play_delta=1`
- Share: `item_id={video_id}&share_delta=1`

### Headers
```
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
User-Agent: <random from pool>
```

### Randomization Parameters
- **Platforms:** `android`, `windows`, `iphone`, `web`
- **Channels:** `tiktok_web`, `googleplay`, `App%20Store`
- **App names:** `tiktok_web`, `musically_go`
- **Device types:** iPhone1,1 through iPhone14,5, iPad variants, Samsung SM-* models
- **Device ID:** Random 19-digit integer
- **OS version:** Random 1-12

### Status
**PATCHED as of 2026-07.** The specific endpoint/auth mechanism no longer works. The approach pattern (mobile API + device spoofing + proxy rotation) may still be viable with updated endpoints. Would need mitmproxy interception of current TikTok app traffic to discover new endpoints.

---

## Approach 2: Zefoy.com Intermediary (Third-Party Service)

**Source:** Multiple repos (xtekky/TikTok-ViewBot 1844★, plowside/Zefoy_TIKTOK_BOT 110★, Sneezedip/Tiktok-Booster 251★, and 5+ more)

### How Zefoy Works
1. Bot visits `https://zefoy.com`
2. Gets CAPTCHA image + hidden form tokens
3. Solves CAPTCHA (OCR via Tesseract, external API, or manual)
4. Submits CAPTCHA answer to get session (PHPSESSID)
5. Posts video URL to Zefoy's service endpoint
6. Zefoy's servers send views to the TikTok video

### Key Implementation Details
- **Session management:** PHPSESSID cookie, can be saved/reused
- **Endpoints on Zefoy:** Dynamic paths per service (views, likes, shares, etc.), base64-encoded
- **Response encoding:** Responses are reversed + base64-encoded: `base64(decode(unquote(response[::-1])))`
- **Rate limiting:** ~60-120s cooldown between sends; IP ban after too many requests
- **CAPTCHA solving options:**
  - Tesseract OCR (local, free, ~60% accuracy)
  - External API (platipus9999.pythonanywhere.com or plowsidecaptcha.pythonanywhere.com)
  - Manual input
- **TLS fingerprinting:** Best repos use `tls_client` library to match Chrome TLS fingerprint

### Dependencies
```
pip install tls_client requests colorama pillow
```

### Current Status (2026-07)
**WORKING** — repos actively updated. But Zefoy can go down/blocked anytime. Some countries blocked. Cloudflare protection sometimes enabled.

---

## Approach 3: Live Stream Play Endpoint (Direct API)

**Source:** Fahad-Jameel/TikTok-Live-Stream-Viewer-Simulator (24★, updated 2026-07-21)

### Endpoint
```
GET https://api16-core-c-useast1a.tiktokv.com/aweme/v1/play/?video_id={stream_id}&line=0&file_type=mp4&data_size=0&data_rate=0&live_stream=1&ac=WIFI&device_id={random_16char}&iid=0&os_version=11.4&app_name=musical_ly&version_code=16.4.0&device_type=iPhone10,4&is_play_url=1&resolution=1080*1920&is_support_h265=1&source=PackSourceEnum_LIVE_STREAMING&ab_version=16.4.0.1&channel=App%20Store&mcc_mnc=
```

### Key Details
- Device ID: Random 16-char alphanumeric string
- IP spoofing via `X-Real-IP` header (not SOCKS5 proxy)
- App identifier: `musical_ly` version `16.4.0`
- **Live streams only** — not regular video views
- Very basic (~50 lines), no signing, no proper device registration
- **Status: Likely patched** given the old version code, but the endpoint pattern (`aweme/v1/play/`) is a useful discovery — different from the `aweme/v1/aweme/stats/` endpoint used by Wizz1337.

---

## Approach 4: SMM Panel Integration (Not Direct API)

**Source:** codedByCan/Tiktok_Free_Viewing_Sender (12★), codedByCan/Tiktok_Free_Viewing_Sender_v2 (12★)

- Web app (Node.js/Express) that proxies requests to SMM panels (e.g., `igresellers.com/api/v2`)
- Users earn coins via ad links, spend coins to send views
- The actual view delivery is outsourced to paid SMM services
- **No direct TikTok API interaction** — just a frontend for SMM panels

---

## Approach 5: Browser Automation (Slowest, Most Reliable)

**Source:** l-portet/tiktok-warmup-bot (663★), simonfarah/tiktok-bot (882★), rowanchanner/tiktok-automation-tool (1★)

- Open TikTok video in headless browser (Selenium/Playwright/Puppeteer)
- Each browser instance = 1 view
- Rotate proxies per instance
- Most resource-intensive but hardest to detect
- **rowanchanner/tiktok-automation-tool** has the best proxy architecture: supports proxy file loading, rotation, headless mode toggle, multi-threading — good reference for proxy patterns even though it's Selenium-based

---

## Private API Libraries (Read-Only, No View Sending)

| Repo | Stars | Lang | Proxy | Notes |
|------|-------|------|-------|-------|
| davidteather/TikTok-Api | 6513 | Python | Yes | Most maintained, Playwright-based signing |
| szdc/tiktok-api | 1291 | Node.js | No | Unmaintained (TikTok 9.1.0), best device registration reference |
| ssovit/TikTok-Private-API-PHP | 24 | PHP | Yes (HTTP) | Requires paid signing server subscription |

These are useful for understanding API structure but none sends views.

---

## Video ID Extraction
All approaches need the video ID (`aweme_id`). From TikTok URL:
- `https://www.tiktok.com/@user/video/1234567890` → `1234567890`
- Short URLs (`vm.tiktok.com/xxx`, `vt.tiktok.com/xxx`) → follow redirects first

## Research Notes (2026-07-24 Session)
- GitHub web UI rate-limits aggressively; switch to `api.github.com/search/repositories` REST API when browser hits 429
- Most "TikTok view bot" repos are Zefoy wrappers — to find truly API-based tools, search for specific endpoint patterns (`tiktokv.com`, `aweme`, `device_id`) rather than generic terms
- `F-Society-Freaks/TikTok-Viewbot` (88★) claims to "send views" but actually automates vipto.de (another Zefoy-like intermediary)
- No open-source tool combines all of: private API + SOCKS5 proxy + device registration + geo-targeting
