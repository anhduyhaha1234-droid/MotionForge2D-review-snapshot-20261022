---
name: tiktok-view-automation
description: "Automate TikTok view counting. Covers what works, what's patched, API reverse-engineering, proxy testing, and third-party services. Tested July 2026."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [tiktok, automation, views, social-media, smm]
    related: [damru-setup]
---

# TikTok View Automation — Battle-Tested Knowledge

## CRITICAL FINDING: TikTok Requires Authentication to Count Views

After exhaustive testing (July 2026), confirmed: **TikTok does NOT count views from unauthenticated sessions**. Every method that loads the page without a logged-in account (direct API, Selenium, Playwright, curl) fails to increment playCount. The video plays in the browser but the counter stays unchanged.

## What Works (Confirmed)

### 1. Third-Party Free View Services ✅
These maintain their own TikTok account pools and dispatch views server-side.

| Service | Status | Notes |
|---------|--------|-------|
| **tikfollowers.com** | ✅ CONFIRMED WORKING | Free views, requires reCAPTCHA. Tested: 547→3624 views. Built on TikApis.com reverse-engineered API. Has `/api/process` endpoint requiring `google_token`. |
| **zefoy.com** | ⚠️ Views service intermittent | CAPTCHA hardened against OCR. External solve APIs (plowsidecaptcha, platipus9999) are down. |
| **like.vn** | Active SMM panel | Vietnamese. API at `/api/mua-view-tiktok/order`. Paid service. |

### 2. SMM Panel APIs (Paid)
Most view-selling services are SMM panel resellers. They connect to upstream providers via standardized APIs. Key repos:
- `prm4u/SMMpanel` (40★) — All-in-one SMM panel for 70+ platforms

### 3. Android Device Automation (Accounts Required)
| Repo | Stars | Approach |
|------|-------|----------|
| tikmatrix/tikmatrix-desktop | 356 | ADB + real Android, 8 accounts/phone |
| masterFuf/taktik-bot | 61 | uiautomator2 + ADB |
| Hormold/tiktok-warmup | 53 | ADB + AI Vision |

## What's PATCHED / Dead

### Direct TikTok Internal API ❌
- `POST https://api{16-22}-core-c-useast1a.tiktokv.com/aweme/v1/aweme/stats/` → **HTTP 403 Access Denied**
- `POST https://api{16-22}-core-c-useast1a.tiktokv.com/aweme/v1/play/` → HTTP 200, status_code=0, but **view count does NOT increase**
- `POST https://api22-normal-c-useast1a.tiktokv.com/aweme/v1/play/` → Same, accepted but no view increment
- All `core` domains blocked. `normal` domains accept requests but don't count views.

### TikTok Web Endpoints ❌
| Endpoint | Result |
|----------|--------|
| `/oembed?url=...` | 200, read-only metadata |
| `/embed/v2/{id}` | 200/503, no view count |
| CDN direct fetch (.mp4) | 403 Forbidden |
| `/api/item/detail/` | 200, read-only |
| `/api/share/item/` | 200, no effect |

### Headless Browser Automation ❌
- Playwright/Selenium loads TikTok page, video auto-plays (currentTime advancing)
- But playCount does NOT increase — TikTok detects headless browsers
- Even with different IPs, user-agents, viewports, locales per session

### Video Play Event Replay ❌
- Captured `video_play` event from `mcs-sg.tiktokv.com/v1/list`
- Replaying same payload: `sc=9` (duplicate detection)
- Modifying device_id: `sc=4` (invalid fingerprint)
- TikTok validates session + device_id + timestamp server-side

## TikTok Tracking Architecture

### Event Tracking Endpoint
```
POST https://mcs-sg.tiktokv.com/v1/list
Content-Type: application/json; charset=UTF-8
```
Sends batched events including: `video_play`, `predefine_pageview`, `video_request`, `video_content_show`, `api_request`, etc.

### Key Status Codes from MCS
- `sc=1` — Success (first time from browser session)
- `sc=4` — Invalid fingerprint (modified device_id)
- `sc=9` — Duplicate (replayed event)

### API Domains (from TikTokMassBotting)
```
api22-core-c-useast1a.tiktokv.com
api19-core-c-useast1a.tiktokv.com
api16-core-c-useast1a.tiktokv.com
api21-core-c-useast1a.tiktokv.com
api22-normal-c-useast1a.tiktokv.com
```

### Signing (Not Yet Tested)
- X-Bogus signature: `5ime/Tiktok_Signature` (316★)
- msToken + ttwid cookies required for web API
- X-Gnarly 5.1.2 signing

## SOCKS5 Proxy Testing Methodology

### What DOESN'T Work for Testing
- `curl --socks5-hostname ... https://httpbin.org/ip` → Often blocked/rejected
- Chrome `--proxy-server=socks5://user:pass@host:port` → **SOCKS5 auth not supported**

### What DOES Work
```bash
# Test with actual target site, not httpbin
curl -s --socks5-hostname "user:pass@host:port" --max-time 15 "https://www.tiktok.com/@user/video/ID" -w "CODE:%{http_code} SIZE:%{size_download}"
```
Expected: HTTP 200, 300-378KB for full TikTok page.

### HTTP->SOCKS5 Relay for Browsers
Use `pproxy` to create local HTTP proxy that tunnels to SOCKS5:
```bash
pip install pproxy
python -m pproxy -l http://0.0.0.0:18080 -r 'socks5://host:port#user:pass'
# Then use in Playwright: proxy={'server': 'http://127.0.0.1:18080'}
```
Note: `#` separator for auth in pproxy, NOT `@`.

## GitHub Repos (Sorted by Relevance)

### View Bots (Zefoy-based, most are wrappers)
| Repo | Stars | Approach |
|------|-------|----------|
| xtekky/TikTok-ViewBot | 1844 | tls_client + Zefoy, auto CAPTCHA |
| useragents/Zefoy-TikTok-Automator | 1250 | Selenium + Zefoy |
| simonfarah/tiktok-bot | 882 | Selenium + Zefoy |
| kangoka/tiktodv3 | 874 | Playwright + CloakBrowser + Tesseract OCR |
| xtekky/zefoy | 796 | requests + Zefoy |
| jfadev/bottok | 594 | Node.js + Puppeteer + Zefoy/Freer |
| Sneezedip/Tiktok-Booster | 251 | Selenium + Tesseract OCR |

### Direct API (All Patched)
| Repo | Stars | Status |
|------|-------|--------|
| Wizz1337/TikTokMassBotting | 585 | PATCHED |
| xtekky/TikTok-View-Bot (old) | 108 | PATCHED |

### API/Signing Tools
| Repo | Stars | Purpose |
|------|-------|---------|
| 5ime/Tiktok_Signature | 316 | X-Bogus, msToken, ttwid |
| Evil0ctal/Douyin_TikTok_Download_API | N/A | TikTok API wrapper |

## Pitfalls Encountered

1. **httpbin.org blocked by SOCKS5 proxies** — Always test with actual target site, not httpbin
2. **Playwright doesn't support SOCKS5 auth** — Use pproxy relay or Python requests with pysocks
3. **Chrome `--proxy-server` doesn't support SOCKS5 auth** — Must use HTTP proxy relay
4. **Zefoy CAPTCHA is OCR-hardened** — Tesseract, ddddocr, EasyOCR all get 0% accuracy
5. **External CAPTCHA APIs down** — plowsidecaptcha.pythonanywhere.com and platipus9999.pythonanywhere.com both return "Coming Soon"
6. **View count regex may return 0/-1 intermittently** — TikTok sometimes serves different page versions; retry with different User-Agent
7. **pproxy auth format** — Use `socks5://host:port#user:pass` (hash separator), NOT `socks5://user:pass@host:port`
