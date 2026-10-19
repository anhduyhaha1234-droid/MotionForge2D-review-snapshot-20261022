---
name: web-service-api-reverse-engineering
description: "Reverse-engineer web service APIs by analyzing frontend JavaScript, intercepting network requests, and automating flows. For SMM panels, view/like/follow services, and any web app with hidden APIs."
version: 1.5.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: ["reverse-engineering", "api", "automation", "web-scraping", "smm"]
    related: ["terminal-engineering-discipline"]
---

# Web Service API Reverse Engineering

## When to Use
- User wants to automate a web service (SMM panel, view/like bot, etc.)
- Need to find hidden API endpoints in a web application
- Need to understand how a service processes orders/requests
- Automating multi-step web flows (search → confirm → process)
- Automating digital marketplace product management (Gumroad, Shopify, etc.)
- Uploading files/images to platforms with incomplete API docs (Rails Active Storage)

## The 5-Step Reverse Engineering Pipeline

### Step 1: MAP THE SURFACE
Fetch the target page and extract:
- Form elements (input names, types, IDs)
- Button text and IDs
- JavaScript files (especially custom ones, not CDN)
- Inline scripts with API-related code
- CSRF tokens, API tokens in meta tags

```bash
curl -sL "https://target.com/page" | grep -oP 'action="[^"]*"|id="[^"]*"|name="[^"]*"|src="[^"]*\.js[^"]*"'
```

### Step 2: INTERCEPT NETWORK TRAFFIC
Use Playwright to capture ALL requests/responses during user interaction:

```python
from playwright.sync_api import sync_playwright

api_calls = []
def on_resp(response):
    if 'target.com/api/' in response.url:
        try:
            body = response.json()
            api_calls.append({'url': response.url, 'status': response.status, 'body': body})
        except: pass

page.on('response', on_resp)
```

**Key filter pattern:** Match on domain + `/api/` path, NOT just `api` in URL (avoids false positives from Google Ads URLs containing `api` in query strings).

### Step 3: EXTRACT API STRUCTURE FROM JS
Look for inline scripts containing:
- `fetch(` calls with endpoint paths
- Config objects with API types, timeouts, feature flags
- `processApiType`, `formApiType` patterns
- reCAPTCHA site keys
- Error messages that reveal parameter names

**Common inline config block (PHP-rendered SMM panels):**
```javascript
const config = {
    processApiType: "video_views",  // the service type for /api/process
    formApiType: "videoDetails",    // the search input type for /api/search
    recaptchaEnabled: false,        // is reCAPTCHA active?
    recaptchaSiteKey: '...',
    apiTimeoutMilliseconds: 10000,
    maxApiRetries: 1,
    apiRetryDelay: 2000
};
```
Extract this with: `grep -n 'processApiType\|formApiType\|recaptchaEnabled' page.html`

**Common fetchAPI pattern:**
```javascript
async function fetchAPI(endpoint, method, bodyData, timeout) {
    fetch(config.baseUrl + endpoint, {
        method: method,
        headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify(bodyData)
    })
}
```

**Translation keys leak all error messages.** The `var translations = {...}` object on every page contains every possible error string including parameter requirements, cooldown format strings, and reCAPTCHA errors. Extract with:
```bash
grep -oP 'var translations = \{[^}]+\}' page.html
```

**serviceItems array** defines all available services. Look for `const serviceItems = [...]` in inline scripts — it reveals every service page, its link, and description even if not linked from the current page.

### Step 4: REPLAY API CALLS
Once endpoints are mapped, replay with `requests`:
- Copy session cookies from browser
- Set proper headers (Content-Type, X-Requested-With, Origin, Referer)
- Handle CSRF tokens (rotate per request)

### Step 5: AUTOMATE THE FULL FLOW
Build the complete automation with proper error handling:
- Loading states (buttons may show "Loading..." before ready)
- Modal dialogs (SweetAlert2 common - need to click OK/Confirm)
- Progress bars (real-time feedback)
- Cooldowns (rate limiting between requests)
- Success/error detection

## Common Pitfalls

### P1: Button Not Ready
Web apps often show "Loading..." while JS initializes. **Must wait for button text to change** before clicking:
```python
page.wait_for_function('''() => {
    const btns = document.querySelectorAll('button');
    for (const b of btns) { if (b.textContent.trim() === 'Search') return true; }
    return false;
}''', timeout=30000)
```

### P2: SweetAlert2 Modals
Many web services use SweetAlert2 for confirmations. After clicking a button, check for `.swal2-confirm` and `.swal2-modal`:
```python
page.click('#actionButton')
time.sleep(2)
ok_btn = page.locator('.swal2-confirm')
if ok_btn.count() > 0:
    modal_text = page.locator('.swal2-modal').inner_text()
    ok_btn.click()
```

### P3: Use `expect_response` Not Event Listeners
Playwright's `page.expect_response()` is more reliable than `page.on('response')` for capturing specific API calls:
```python
with page.expect_response(lambda r: 'target.com/api/search' in r.url, timeout=20000) as resp_info:
    page.click('button:has-text("Search")')
response = resp_info.value
body = response.json()
```

### P4: Keep Browser Open for Async Processes
Many web services process requests asynchronously. **Closing the browser kills the process.** Must wait for completion:
- Watch for progress bar to reach 100%
- Wait for success/error modal to appear
- Then close browser

### P5: `response.json()` Fails on Non-JSON Responses
Always wrap in try/except:
```python
try:
    body = response.json()
except:
    body = response.text[:500]
```

### P6: Google Ads URL False Positives
Filter responses by domain path, not just keyword. `'api' in url` matches Google Ads URLs like `googleads.g.doubleclick.net/pagead/ads?...&api=...`. Use `'target.com/api/' in url` instead.

### P7: curl Returns 200 with 0 Bytes (Cloudflare)
When `curl -sL URL` returns HTTP 200 but 0 bytes body, the site is behind Cloudflare and blocking curl's default UA. Fix: add a full browser User-Agent header. If that still fails, the page may require JavaScript (use Playwright instead).

### P8: Geo-Restriction Kills View/Like Inflation for Locked Content
When a TikTok video (or similar) has geo-restricted view counting (e.g., "khóa view VN"), the service MUST match the target country in TWO places:
1. **IP geolocation** — proxy must be from the target country
2. **Device `country_location`** — the API request must carry matching MCC, carrier, timezone, language

If the SMM service's backend uses devices registered in country X but the video only counts views from country Y, **zero views are added** — the API call succeeds but TikTok silently discards the view.

**Detection:** Views return `amount_processed > 0` in the response but the actual `play_count` doesn't increase when checked later.

**Fix:** Either use the API directly with target-country device config + residential proxy from that country, or use an SMM panel based in the target country (they already have matching infrastructure).

### P9: Frontend "Success" ≠ Backend Actually Delivered
SMM panel frontends (like tikfollowers.com) may return `status: "success"` with `amount_processed: 2496` even when the **backend is completely down**. The frontend just passes through whatever the backend returns, but some frontends add a fake success layer.

**Detection method:** Track the actual metric (view count, follower count) BEFORE and AFTER calling the API. If the API says +2496 views but `play_count` hasn't changed after 5+ minutes, the backend didn't deliver.

```python
# Before
views_before = get_view_count(video_id)
call_process_api(video_id)
time.sleep(300)  # wait for TikTok to update
views_after = get_view_count(video_id)
assert views_after > views_before, f"Backend didn't deliver: {views_before} → {views_after}"
```

**Also check backend availability directly** — if the service has a separate backend domain, test it independently. In this session, tikfollowers.com always returned success, but tikapis.com (the backend) returned "Service temporarily unavailable" for every endpoint.

### P10: Proxy Chain Mismatch (User→Service≠Service→Target)
When using proxies with SMM services, the proxy only affects YOUR connection to the service. The service's backend uses its OWN infrastructure to reach the target platform.

```
You --[VN proxy]--> smm-frontend.com --[their non-VN proxy]--> TikTok
                                         ↑
                              Views come from THEIR infrastructure
```

This means:
- Using a VN proxy to call tikfollowers.com does NOT make views count for VN-locked content
- The cooldown is typically per-target (username/video), NOT per-IP — different proxies still share the same cooldown
- To actually control the proxy used for the final hop, you need direct API access to the backend with a `proxy` field in the request body

### P16: API Error Messages Often Reveal Undocumented Endpoints
When an API rejects a parameter, the error message frequently tells you the CORRECT endpoint or format. Examples:
- Gumroad: `"'thumbnail' is not an accepted parameter. Use POST /v2/products/:id/thumbnail with a signed_blob_id"` — reveals the actual endpoint
- Gumroad: `"'file' is not an accepted parameter. Upload files with the presign flow (POST /v2/files/presign)"` — reveals the upload mechanism

**Always read the full error response.** Don't just retry with different params — the error IS the documentation for undocumented APIs. Parse it, extract endpoint paths and parameter names, then try those.

### P17: Windows/MSYS Path Issues with curl -o
On Windows with git-bash/MSYS, `curl -o /tmp/file.html` may silently fail because `/tmp` doesn't map to `C:\tmp`. Use POSIX paths under `/c/Users/<user>/` or create the directory first:
```bash
mkdir -p /c/tmp && curl ... -o /c/tmp/file.html
```

## SOCKS5 Proxy with Authentication

### Playwright Limitation
Playwright does NOT support SOCKS5 proxy authentication via `proxy={'server': 'socks5://user:pass@host:port'}`. Chrome's `--proxy-server` flag also doesn't support SOCKS5 auth.

### Workarounds
1. **pproxy relay** (Python): `pproxy -l http://0.0.0.0:18080 -r socks5://host:port#user:pass` — converts SOCKS5+auth to local HTTP proxy. Works but has edge cases.
2. **requests + pysocks**: Works perfectly for API-only calls (no browser needed).
3. **Local HTTP proxy relay**: Write custom Python HTTP CONNECT proxy that tunnels through SOCKS5. Complex but reliable.
4. **Use HTTP proxies instead**: If available, HTTP proxies work directly with Playwright/Selenium.

### Testing Proxy Connectivity
Don't use httpbin.org to test (often blocked by proxy providers). Test against the actual target:
```bash
curl -s --socks5-hostname "user:pass@host:port" --max-time 15 "https://actual-target.com" -o /dev/null -w "HTTP:%{http_code} SIZE:%{size_download}"
```

## Two-Step Search→Process Flow (Common in SMM Panels)

Many SMM panels use a 2-step API flow. Understanding this pattern lets you automate any of them:

**Step 1 — Search/Identify:** Client sends URL/username, gets back a token + metadata
```
POST /api/search  →  {input: "video_url_or_id", type: "videoDetails"}
Response: {status, token, aweme_id, user_id, stats: {...}, ...}
```

**Step 2 — Process/Execute:** Client sends the full search response + action type
```
POST /api/process  →  {<entire search response>, type: "video_views"}
Response: {status:"success", data:{amount_processed: 1141}, ...}
```

**Key observations:**
- Token is short-lived — must use from same search response, cannot reuse
- Cooldown is typically per-IP and per-target (username/video), ~3-10 minutes
- Amount per call varies (~500-5000 depending on service and tier)
- Error responses often include `additional_offers` array (upsell other services)

**To discover service types:** grep for `processApiType` in all page HTML files. Each service page has a different value.

## Discovering Backend Infrastructure

SMM panels often hide their actual backend behind a frontend. To find it:

1. **Check footer/credits:** Look for "Powered by", "Built using infrastructure from", partner links
2. **Check JS for external API domains:** grep for different domains in fetch calls, config objects
3. **Check `serviceItems` and navigation** for partner sites (same codebase, different frontend)
4. **Look for `/documents/` or `/docs/`** on any discovered API domain — these often have full API specs
5. **WHOIS/DNS** can reveal related domains

Example: tikfollowers.com credits tikapis.com in its HTML footer. tikapis.com has full documentation revealing the actual TikTok private API endpoints, encryption algorithms, and device registration.

## Cloudflare + PHP Session Pattern

When a site uses Cloudflare + PHP backend:
- `ci_session` cookie in Set-Cookie header confirms PHP
- `Server: cloudflare` in headers (proxied through CF)
- curl may return HTTP 200 with 0 bytes if CF blocks — use full User-Agent header
- `Transfer-Encoding: chunked` common with CF
- The actual API endpoints are NOT blocked by CF (only HTML pages get challenge-gated)

```bash
# Fetch with proper UA to avoid CF blocks
curl -sL -A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36' 'https://target.com/' > page.html
```

## Technique: GitHub Source Code Mining for Service APIs

When reverse-engineering a commercial API service, **check GitHub for their official repos**. Many API providers publish example clients, SDKs, or even partial source. This is far more informative than scraping docs alone:

```bash
# Search for the service's GitHub org
curl -sL "https://api.github.com/search/repositories?q=<service_name>&sort=stars&per_page=10"

# Look for repos owned by the service
curl -sL "https://api.github.com/repos/<service_org>/<repo>/contents"

# Read the actual client code
curl -sL "https://raw.githubusercontent.com/<org>/<repo>/main/<file>.py"
```

**What to extract from GitHub source:**
1. **Actual API base URLs** — often different from what the docs show (docs may show versioned/vanity URLs)
2. **Authentication headers** — `api-key`, `x-api-key`, `Authorization` patterns
3. **Request/response lifecycle** — the ORDER of calls matters (e.g., template → register → token → seed → execute)
4. **Signing/encryption flow** — how requests are signed before sending to the target platform
5. **Device fingerprint generation** — what fields are needed and their format
6. **Error handling patterns** — what error codes trigger captcha, retries, etc.
7. **Proxy integration** — how proxies are configured (SOCKS5 vs HTTP, format)

**Key files to look for:** `utilities.py` (helper functions), `HTTPRequester.py` (HTTP client), `*.py` main classes, `README.md` (overview), config files.

**Pitfall:** Don't assume docs are authoritative. In this session, the docs showed `api-v4.tikapis.com` endpoints but DNS doesn't resolve for that subdomain — the actual working URLs use `tikapis.com/api/android` or `tikapis.com/private/android/v1/`. Only the source code revealed the real endpoints.

## Technique: DNS Verification of Documentation URLs

When docs show API subdomains, verify they actually resolve before building around them:
```bash
nslookup api-v4.example.com
curl -sI "https://api-v4.example.com"
```
If a documented API domain doesn't resolve, the actual API is likely at a different path on the main domain, or the subdomain requires special routing (VPN, internal DNS, or header-based routing through the main domain's Cloudflare).

### P12: DATA APIs vs MANIPULATION APIs — Don't Confuse Them
When searching for "TikTok API" or "TikTok view API", most results are **DATA APIs** (read-only):
- tikapi.com, tikhub.io, RapidAPI TikTok APIs — let you READ video data, user profiles, comments
- They CANNOT inflate views, likes, or followers

**MANIPULATION APIs** (write/inflate) are rare and usually:
- Sold as SMM panel backend services (like tikapis.com)
- Accessed through SMM panel frontends (like tikfollowers.com, like.vn)
- Use reverse-engineered TikTok private APIs with device registration + encryption signing

**How to tell the difference:** If the docs mention OAuth, reading data, "get video details", "search users" — it's a DATA API. If they mention device registration, MSSDK encryption, X-Argus/X-Ladon signing, "manipulations" endpoints — it's a MANIPULATION API.

## Technique: Playwright Full-Flow Automation with expect_response Chaining

When tracking a multi-step web flow (search → display → process → result), chain `expect_response` calls to capture each API response in sequence:

```python
from playwright.sync_api import sync_playwright
import json, time

api_log = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_context(user_agent='Mozilla/5.0 ...').new_page()

    # Capture all API traffic for debugging
    def on_resp(resp):
        if 'target.com/api/' in resp.url:
            api_log.append({'url': resp.url, 'status': resp.status,
                           'body': resp.json() if resp.ok else resp.text[:300]})
    page.on('response', on_resp)

    page.goto('https://target.com/service-page')

    # Step 1: Fill form + capture search response
    page.fill('#inputField', VIDEO_URL)
    with page.expect_response(lambda r: 'api/search' in r.url, timeout=20000) as resp_info:
        page.click('#searchBtn')
    search_data = resp_info.value.json()

    # Wait for UI to update (buttons appear after search completes)
    time.sleep(5)
    page.wait_for_function("document.getElementById('startBtn').style.display !== 'none'", timeout=15000)

    # Step 2: Click action button + capture process response
    with page.expect_response(lambda r: 'api/process' in r.url, timeout=60000) as resp_info:
        page.click('#startBtn')
        time.sleep(3)
        # Handle SweetAlert2 confirmation popup
        swal = page.locator('.swal2-confirm')
        if swal.count() > 0 and swal.is_visible():
            swal.click()
    process_data = resp_info.value.json()

    # Save full API log
    with open('api_log.json', 'w') as f:
        json.dump(api_log, f, indent=2, default=str)
```

**Key patterns:**
- `expect_response` blocks until matching response — use for request/response pairs
- `page.on('response', callback)` captures ALL traffic — use for debugging
- Both can coexist — `on('response')` for logging + `expect_response` for critical flows
- Always `time.sleep(3-5)` after search to let UI render before checking button visibility
- SweetAlert2 popups (`.swal2-confirm`) often appear between steps — check after each click
- If `expect_response` times out, the API call may have failed silently — check `on('response')` log

### P13: Headless Browser Visits Don't Count as Views
When trying to inflate views by automating browser visits (Playwright/Selenium), TikTok detects and discards visits from:
- **Datacenter IPs** — even with residential UA strings
- **Headless browser fingerprints** — `navigator.webdriver`, missing plugins, uniform viewport
- **No real user interaction** — just loading the page isn't enough

Tested: 5 Playwright visits to a TikTok video page (8-second watch each, proper UA, locale vi-VN). Zero views added. TikTok's JavaScript on the page performs fingerprinting BEFORE reporting playback — headless browsers fail this check.

**What DOES work for view counting:** Real browser on real device with residential IP. The TikTok page JavaScript must execute fully, pass fingerprint checks, and report playback to TikTok's servers.

### P14: Signing Constants Are App-Specific (Douyin ≠ TikTok)
When using signing libraries for TikTok/Douyin API calls, the **algorithm is the same but the signing constants differ** between apps:
- Douyin (Chinese app, aid=1128) uses one set of constants
- TikTok international (musical_ly, aid=1233) uses different constants
- TikTok lite, trill, etc. may have yet another set

The constants (`sign_key.b64`, `gorgon_table.hex`) are extracted from the app's native library (`libmetasec_ov.so`). In newer TikTok versions, these constants are **obfuscated** — simple regex extraction fails. Would need Ghidra/IDA Pro reverse engineering or Frida hooking on a real device.

**Impact:** A signing library that works for Douyin will return HTTP 400 "Invalid parameters" when used against TikTok endpoints. Don't assume cross-app compatibility.

### P15: Zefoy Captcha Is Image-Based (Not OCR-Solvable)
Zefoy uses a custom image captcha (not reCAPTCHA/hCaptcha):
- Served at `/<hash>.php?_CAPTCHA=<token>&t=<timestamp>`
- Hidden input `captcha_encoded` contains encrypted JSON
- Input field: `name="captchalogin"`
- ddddocr (Chinese OCR library) returns empty or wrong characters
- The captcha solver at platipus9999.pythonanywhere.com (used by xtekky bot) is DOWN

Automating Zefoy requires either: manual captcha solving, a working captcha solving service, or bypassing the captcha entirely (which may require session cookies from a prior manual solve).

### P16: TikTok's VM-Based Signing (77 Opcodes)
TikTok's client-side protection uses a **stack-based JavaScript Virtual Machine** with 77 opcodes for request signing. The VM generates signed parameters (`as`, `cp`, `mas`) that must accompany API requests. Without valid signatures, requests get 403'd.

The bytecode and obfuscation are regularly updated (every few weeks). This is similar to Google's BotGuard system. You cannot simply replay HTTP requests — you must either reverse-engineer the VM or run actual browser/app instances that execute the signing code natively.

**Reference:** `notemrovsky/tiktok-reverse-engineering` (GitHub) — 77 opcodes mapped, string deobfuscation, bytecode disassembly.

## Technique: tls_client for TLS Fingerprint Mimicry
When standard HTTP clients get blocked, `tls_client` can mimic specific TLS fingerprints:
```python
import tls_client
session = tls_client.Session(client_identifier='tiktok_android_38', random_tls_extension_order=True)
resp = session.get('https://www.tiktok.com/@user/video/123', headers={...})
```
- Successfully gets TikTok video pages (HTTP 200, 371KB) when standard requests get blocked
- SSR data contains `__UNIVERSAL_DATA_FOR_REHYDRATION__` JSON with app context, biz context, strategy configs
- Does NOT contain video stats (loaded dynamically via JS)
- **Limitation:** SOCKS5 proxy not supported by tls_client (only HTTP proxies)
- **Limitation:** Does NOT trigger view counting — just fetches HTML, doesn't execute JS

**Client identifiers:** `tiktok_android_38`, `chrome_120`, `chrome_131`, etc. Each mimics a specific browser/app TLS fingerprint.

## Technique: Rails Active Storage Direct Upload

Many Rails apps (Gumroad, Shopify, Basecamp, etc.) use Active Storage for file uploads. The flow is NOT a simple multipart POST — it's a 3-step process:

1. **POST /rails/active_storage/direct_uploads** with blob metadata → returns `signed_id` + presigned S3 URL + headers
2. **PUT presigned_url** with raw binary bytes and the returned headers
3. **Use `signed_id`** in the parent model's attachment endpoint

**Getting CSRF:** Rails apps use XSRF-TOKEN cookie. Extract it via `session.cookies.get("XSRF-TOKEN")` after a GET to any page.

**Blob metadata format:**
```json
{"blob": {
    "filename": "image.jpg",
    "content_type": "image/jpeg",
    "byte_size": 12345,
    "checksum": "<base64-encoded MD5>"
}}
```

**Checksum:** `base64(md5(file_bytes))` — NOT hex-encoded.

**Error signal:** If you get 422 "Unprocessable Content", the CSRF token is missing or wrong.

**Reference:** `references/gumroad-api-v2-complete-flow.md` — complete working example with all endpoints.

## Technique: TikTok APK Constant Extraction
To extract signing constants from TikTok APK for use with signing libraries:
1. Download APK from apkpure.com/apkcombo.com
2. Extract `lib/arm64-v8a/libmetasec_ov.so` (not `libmetasec.so` — the filename changed)
3. Search for 44-char base64 strings (sign_key) and 40-hex-char strings (gorgon_table)
4. In newer versions (v38+), constants are **obfuscated** — regex extraction fails
5. Would need Ghidra/IDA Pro analysis or Frida hooking on real device

The `douyin-sign` repo (7452323/douyin-sign) has `update.py` that automates this, but currently only works for Douyin APK constants.

## References
- See `references/gumroad-api-v2-complete-flow.md` for complete Gumroad API v2 product lifecycle: create, file upload (presign flow), cover/thumbnail (Rails Active Storage), publishing, and all undocumented endpoints
- See `references/tiktok-view-counting-and-anti-bot.md` for TikTok view counting mechanism, 5 anti-bot detection layers, Zefoy internals, signing libraries, and GitHub repos
- See `references/tiktok-view-services.md` for detailed findings on TikTok view inflation (tikfollowers.com, tikapis.com API docs, complete automation flow)
- See `references/tikfollowers-live-test-results.md` for live test data: proxy behavior, backend status, view count verification, geo-restriction root cause analysis
- See `references/tikfollowers-playwright-automation-flow.md` for complete Playwright + direct API automation code
- See `references/tikapis-sdk-repos.md` for GitHub SDK repos, device lifecycle flow, Python SDK usage
- See `references/alternative-api-services.md` for alternative API providers (tikhub.io, tikapi.com), standard SMM panel API format, and other SMM panels
- See `references/tikapis-api-documentation-extracted.md` for complete tikapis.com API docs: all endpoints, request bodies, VN device config template, service tiers, DNS verification results
- See `references/douyin-sign-library-and-constants-extraction-2026-07.md` for douyin-sign Python signing library analysis, TikTok constants extraction attempt from APK, and comparison with code-root/tiktok-android-signing-toolkit
- See `references/tikfollowers-live-test-results.md` for live test data: proxy behavior, backend status, view count verification, geo-restriction root cause analysis
- See `references/tikfollowers-playwright-automation-flow.md` for complete Playwright + direct API automation code
- See `references/tikapis-sdk-repos.md` for GitHub SDK repos, device lifecycle flow, Python SDK usage
- See `references/alternative-api-services.md` for alternative API providers (tikhub.io, tikapi.com), standard SMM panel API format, and other SMM panels
- See `references/tikapis-api-documentation-extracted.md` for complete tikapis.com API docs: all endpoints, request bodies, VN device config template, service tiers, DNS verification results
- See `references/douyin-sign-library-and-constants-extraction-2026-07.md` for douyin-sign Python signing library analysis, TikTok constants extraction attempt from APK, and comparison with code-root/tiktok-android-signing-toolkit
