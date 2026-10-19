# Third-Party TikTok View Services (tested 2026-07-23)

## Working/Dead Services (as of 2026-07-25)

### tikfollowers.com — API WORKS, VIEWS DON'T COUNT ⚠️
- API responds with `success` + `amount_processed` (832-2500 views/cycle)
- Actual TikTok view count does NOT change — confirmed across 3+ sessions
- tikapis.com backend DOWN (HTTP 500) — frontend always lies about success
- Cooldown: ~13 min per TARGET VIDEO (NOT per-IP)
- reCAPTCHA disabled
- Full browser flow confirmed via Playwright: search → Start Earning → SweetAlert → process → fake success
- **VERDICT: WASTE OF TIME when tikapis.com is down**

### Zefoy.com — FREE, WORKS (limited)
- Supports views, likes, shares, followers, comment-hearts, favorites, live-stream, repost
- Each service has independent availability
- CAPTCHA solving: ~0% accuracy via OCR (Tesseract/ddddocr/easyocr all fail)
- tls_client cannot fetch captcha images (loaded via JS `onload`)
- Must use Selenium/Playwright with real browser
- Rate-limited: ~1 view per 45-120 seconds per service
- Shared pool — views compete with every other user

### xtekky/TikTok-ViewBot (★1,848) — ZEFOY BOT, NOT PRIVATE API
- Updated today but it's a **Zefoy wrapper** (Selenium + tls_client)
- `old/main.py` uses tls_client to POST to zefoy.com
- `v2.py` uses Selenium to automate zefoy.com
- Does NOT interact with TikTok API directly
- Common confusion: "TikTok ViewBot" name implies direct API — it's not

### like.vn — PAID, VN VIEWS ✅
- Vietnamese SMM panel, 8+ years, 289K members
- TikTok View: SV1 (3.2₫), SV2 (2.88₫), SV3 (1.9₫), SV5 (FREE)
- Supports VN-geolocated views
- Requires registration + Cloudflare challenge

## Dead/Broken Services

### tikapis.com — DOWN (HTTP 500)
- All `/api/*` endpoints return 500 "Service temporarily unavailable"
- `api-v4.tikapis.com` does NOT exist in DNS
- API keys valid (Android: `b6b12336-...`, iOS: `7892688e-...`)
- This breaks tikfollowers.com and all dependent services

### freer.es — DEAD
- Status: 502 Bad Gateway
- Was similar to Zefoy

### tiktokauto.com — BLOCKED
- Status: 403 Forbidden

### freetiktokviews.com — BLOCKED
- Status: 403 Forbidden

## Proxy Service Notes
- dc-vn24.proxyvt.com (user's proxy provider): 108 SOCKS5 proxies confirmed working
- Format: `dc-vn24.proxyvt.com:PORT:username:password`
- Verified: `curl --socks5-hostname 'user:pass@host:port' https://httpbin.org/ip` → returns VN IPs (14.185.x, 14.165.x)
- **IMPORTANT**: VN proxy only affects client→tikfollowers connection. tikfollowers→tikTok uses their own servers (non-VN).

## Zefoy Services Status (tested 2026-07-23)
| Service | Form Index | Status |
|---------|-----------|--------|
| Followers | 0 | Returns raw HTML (endpoint mismatch) |
| Hearts | 1 | NOT WORKING |
| Comments Hearts | 2 | WORKING (cooldown ~160s) |
| Views | 3 | NOT WORKING |
| Shares | 4 | NOT WORKING |
| Favorites | 5 | WORKING (cooldown ~160s) |
| Live Stream | 6 | Returns raw HTML (endpoint mismatch) |
| Repost | 7 | NOT WORKING |

## Zefoy CAPTCHA Solving (updated 2026-07-23)

**⚠️ ALL OPEN-SOURCE OCR APPROACHES FAILED (0% accuracy in 18+ attempts)**

### Dead CAPTCHA APIs
- **plowsidecaptcha.pythonanywhere.com** — returns "Coming Soon" (DEAD)
- **platipus9999.pythonanywhere.com** — returns "Coming Soon" (DEAD, confirmed 2026-07-23)

### Tested OCR Engines (ALL FAILED)
- **Tesseract OCR** — produces plausible English words ("sunlight", "after", "fighting") but ALL wrong. Best preprocessing: crop 8% margins + invert + Otsu + 3x scale + PSM 7
- **ddddocr 1.6.1** — returns garbage ("回", "u9h"). Designed for Chinese captchas, not English distortion
- **easyocr 1.7.2** — "h a / f" with 56% confidence. Wrong

### Why OCR Fails
Zefoy CAPTCHA uses: colored noise/line overlays, character scaling distortion, variable character spacing, and dictionary words. Classical image preprocessing cannot bridge the gap.

### What's Needed to Solve
1. Custom-trained neural network model specifically for Zefoy's distortion patterns
2. Paid CAPTCHA service (2captcha, anticaptcha) — uncertain if they support this type
3. Manual solving

### Tesseract Setup (for anyone attempting)
- Install: `winget install UB-Mannheim.TesseractOCR` (Windows, path: `C:\Program Files\Tesseract-OCR\tesseract.exe`)
- Config: `--psm 7 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz`
- Captcha is always lowercase letters, 3-10 chars typical
- See `references/zefoy-captcha-ocr-test-results-2026-07.md` for full test data

## Zefoy Selenium + Tesseract Pipeline (reference only — CAPTCHA solving does NOT work reliably)
```bash
pip install selenium pytesseract pillow webdriver-manager
winget install UB-Mannheim.TesseractOCR
```
```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
# Selenium options: --headless=new --window-size=1920,1080
# Notification prefs: MUST ALLOW (pref=1), NOT block (pref=2)!
#   Zefoy detects blocked notifications and throws alert that breaks Selenium
#   prefs={"profile.default_content_setting_values.notifications": 1}
# Dismiss alerts: try/except around driver.switch_to.alert.accept()
```

Key steps:
1. Load zefoy.com, dismiss notification alerts (Zefoy throws alert if notifications blocked)
2. Wait for captcha image + 3s for JS onload
3. **Get fresh image via JS** — Selenium element screenshots can be cached (see pitfall #11)
4. Preprocess: crop 8% margins → grayscale → Otsu threshold → invert → 3x scale
5. Solve with Tesseract (expect ~0% accuracy) or ddddocr (also ~0%)
6. After session, get form actions (base64-encoded service endpoints)
7. **Submit via XHR from browser context** (forms are hidden, Selenium clicks fail)
8. Decode response: `atob(decodeURIComponent(reversed_text))`

## Zefoy Direct API via Selenium XHR
```python
result = driver.execute_script("""
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/' + arguments[2], false);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.send(arguments[1] + '=' + encodeURIComponent(arguments[0]));
    try {
        var t = xhr.responseText.split('').reverse().join('');
        return {decoded: atob(decodeURIComponent(t)).substring(0, 500)};
    } catch(e) { return {raw: xhr.responseText.substring(0, 200)}; }
""", video_url, video_key, form_action)
# Response patterns:
# - "color:green..." = success
# - "not working" (red) = service down
# - "please wait N seconds" = cooldown timer
```

## Sneezedip/Tiktok-Booster Repo (tested 2026-07-23)
- **Requires Python 3.12+** (hard check, exits on 3.11)
- Uses basic `pytesseract.image_to_string()` with NO preprocessing
- Has interactive prompts (history, URL input) — not headless-friendly
- Downloads bundled Tesseract to `./Tesseract/`
- Would face identical CAPTCHA accuracy issues even if it could run
