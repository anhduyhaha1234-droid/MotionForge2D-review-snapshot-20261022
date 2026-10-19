# TikTok Anti-Bot & View Counting - Technical Reference

## View Counting Mechanism

### What Counts as a View
- Video must **actually play** in a browser (page load alone does NOT count)
- Minimum watch time required (varies, but ~3-5 seconds seems needed)
- Same IP = 1 view (server-side IP deduplication)
- Headless browsers are detected and views are NOT counted

### API Endpoints (as of 2026-07)

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/aweme/v1/aweme/stats/` | POST | 403 PATCHED | Was the main injection point, now blocked |
| `/aweme/v1/play/` | POST | 200 but FAKE | Returns status_code=0 but doesn't increment views |
| `mcs-sg.tiktokv.com/v1/list` | POST | Tracking only | Event collection, not view injection |

### Tracking Event System

TikTok sends tracking events to `https://mcs-sg.tiktokv.com/v1/list`:

Key events captured:
- `video_play` - when video starts playing
- `video_content_show` - when video content renders
- `predefine_pageview` - page view tracking
- `__bav_page` - browser analytics
- `api_request` - API call tracking

### Server Response Codes (mcs-sg events)

| Code | Meaning | When |
|------|---------|------|
| `sc=1` | Success | First submission from valid session |
| `sc=4` | Invalid fingerprint | device_id doesn't match session |
| `sc=9` | Duplicate | Same event submitted again |

### Anti-Bot Detection Layers

1. **Headless browser detection** - navigator.webdriver, Chrome headless markers
2. **Device fingerprint validation** - device_id must match session cookies
3. **Server-side deduplication** - sc=9 for replayed events
4. **IP-based dedup** - Same IP = 1 view
5. **Rate limiting** - "Too many requests" if too fast
6. **CAPTCHA** - on Zefoy and similar services

### Browser Fingerprint Signals
- `navigator.webdriver` (true in headless)
- WebGL renderer string
- Canvas fingerprint
- Screen resolution / timezone consistency
- Mouse/keyboard event presence

## Zefoy.com Status (2026-07)

### Working Services
- Comments Hearts ✅
- Favorites ✅

### Not Working
- Views ❌ ("This service is currently not working")
- Followers - intermittent
- Shares - intermittent

### CAPTCHA System
- Image-based CAPTCHA on login
- External solve APIs:
  - `https://plowsidecaptcha.pythonanywhere.com/captcha` (POST file)
  - `https://platipus9999.pythonanywhere.com/` (POST base64)
- Tesseract OCR works but accuracy varies

## GitHub Repos Tested

| Repo | Stars | Approach | Status |
|------|-------|----------|--------|
| xtekky/TikTok-ViewBot | 1844 | Zefoy + tls_client | Intermittent |
| plowside/Zefoy_TIKTOK_BOT | 110 | Zefoy + requests | CAPTCHA parsing broken |
| Sneezedip/Tiktok-Booster | 251 | Zefoy + Selenium + Tesseract | Works when Zefoy views online |
| kangoka/tiktodv3 | 874 | Zefoy + Playwright + CloakBrowser | Best maintained |
| Wizz1337/TikTokMassBotting | 585 | Direct API | PATCHED (403) |

## Tested Approaches Summary

| Method | Works? | Why |
|--------|--------|-----|
| Direct API (aweme/v1/play/) | ❌ | Server accepts but doesn't count |
| Direct API (aweme/v1/aweme/stats/) | ❌ | HTTP 403, fully patched |
| video_play event replay | ❌ | sc=9 duplicate detection |
| Page load via requests | ❌ | No video play = no view |
| Headless Playwright | ❌ | Detected, views not counted |
| Headless + different IPs | ❌ | Still detected per-session |
| Zefoy automation | ⚠️ | Depends on Zefoy service status |

## Possible Next Steps (Untested)
- `undetected-chromedriver` - patches Chrome to avoid detection
- Non-headless browser (visible, slower but harder to detect)
- Realistic user interactions (mouse, scroll, click)
- TikApis.com reverse-engineered API
- tikfollowers.com free tools (needs reCAPTCHA)
