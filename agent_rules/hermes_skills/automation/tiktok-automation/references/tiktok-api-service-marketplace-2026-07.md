# TikTok API Service Marketplace — Research 2026-07-24

## Commercial API Services

### TikAPIs.com (tikapis.com) — SERVICE DOWN (500) as of 2026-07-24 ⚠️
- **URL:** https://tikapis.com
- **Status:** ⚠️ SERVICE DOWN — All `/api/*` endpoints return HTTP 500 "Service temporarily unavailable"
- **What:** Reverse-engineered TikTok Private API using ByteDance encryption (X-Argus, X-Ladon, X-Gorgon, X-Khronos, X-Cylons, X-Helios). Android/iOS/Web/Windows + Captcha solving.
- **Docs:** https://tikapis.com/documents/
- **Telegram:** @tikapiscom
- **Manipulation endpoints (8):** Like, Dislike, Story Like, Story Dislike, Save, **Views video by ID**, Follow, Unfollow
- **Other modules:** Device (2), Algorithm (4), Signature Algorithm (2), X-Algo (6), Login (3), Signup (5), Comments (4), User (5), Video (2), Account Edit (4), Account Reset (2), Captcha (3)
- **Free tier YES:**
  - iOS: 200 req/day, 1400/week, 6000/month, 15 req/min
  - Android: 1000 req/day, 5000/week, 15000/month, 25 req/min
- **Basic (Captcha):** 1000 req/day, 7000/week, 30000/month, 100 req/min
- **Premium:** $120/month
- **API Keys (valid but service down):**
  - **Android:** `b6b12336-bfef-4be1-8112-72ba8e878d6b`
  - **iOS:** `7892688e-4e58-410c-b095-9e1a3b02595d`
- **DNS status (2026-07-24):**
  - `api-v4.tikapis.com` → DOES NOT EXIST in DNS
  - `api-v3.tikapis.com` → Resolves (2001:ee0:23::23) but returns empty
  - `tikapis.com` → Resolves, Cloudflare, HTTP 200 for web pages
- **Key validation (works even when service down):**
  - No key → `{"error": "API key is missing"}`
  - Wrong key → `{"error": "Invalid API key"}`
  - Valid key → `{"error": "Service temporarily unavailable"}` (HTTP 500)
- **Endpoint discovery (from docs HTML):**
  - `POST https://api-v4.tikapis.com/video/stats/{video_id}` — views
  - `POST https://api-v4.tikapis.com/device_register` — device registration
  - `POST https://api-v4.tikapis.com/user/follow/{user_id}/{sec_uid}` — follow
  - `POST https://api-v4.tikapis.com/video/like/{video_id}` — like
  - `POST https://api-v4.tikapis.com/comment/publish/{video_id}` — comment
  - `POST https://api-v4.tikapis.com/algorithm/mssdk_encrypt` — MSSDK encryption
  - `POST https://api-v4.tikapis.com/algorithm/tt/encrypt` — TT encryption
- **⚠️ tikfollowers.com depends on tikapis.com** — when tikapis is down, tikfollowers "success" responses are meaningless. Frontend always returns `{"status": "success", "amount_processed": N}` regardless of backend state.
- **RapidAPI listing removed**

### TikAPI.io (tikapi.io) — LIVE ✅
- **URL:** https://tikapi.io (tikapi.com → 301 → tikapi.io)
- **What:** Polished commercial TikTok API platform. Profiles, search, video stats, live streams, mentions, messages, OAuth. SDKs: JavaScript + Python.
- **Pricing:**
  - Starter: 5-day trial then $29/mo — 300 req/day, general endpoints, limited support
  - Pro: $79/mo — 2,000 req/day, general endpoints
  - Business: $189/mo — 10,000 req/day, premium endpoints
  - Enterprise: custom
- **Free tier:** 5-day trial only
- **Built in:** Tirana & Barcelona
- **Python wrapper:** https://github.com/armxe/tikapi (★2)
- **⚠️ No explicit view/like/follow manipulation endpoints** — more of an analytics/monitoring platform

### Dead/Unreachable Services (2026-07-24)
| Domain | Status |
|---|---|
| tiktokapi.com | Connection timed out |
| tiktok-api.com | No response |
| tiktokapi.dev | No response |
| usead.com | No response |
| tokbackup.com | LIVE (301→HTTPS), content timed out |

## Key GitHub Repos for Private API (full manipulation)

| Repo | ★ | Lang | Capabilities | Updated |
|---|---|---|---|---|
| HkerVit/TikTok-Private-API | 50 | — | Follow, like, username check, edit username, edit nickname, X-Gorgon | 2026-07-22 |
| pushshift/tiktok | 55 | Python | Module to access TikTok Private API | 2025-12 |
| mangledbottles/Musically-API | 40 | PHP | Full reverse-engineered private API | 2026-07-12 |
| ssovit/TikTok-Private-API-PHP | 24 | PHP | Unofficial access to private TikTok API | 2026-07-02 |
| X-SLAYER/Flutter-Tiktok-UI-API-Clone | 231 | Dart | Flutter UI + private API to fetch videos | 2026 |
| tolgatasci/musically-tiktok-api-python | 148 | Python | Open-source Musically/TikTok API | 2026 |

## SMM Panel API Providers (TikTok-capable)

| Service | URL/GitHub | What |
|---|---|---|
| SocialPlug | socialplug.io | Buy followers, likes, subscribers & views |
| PRM4U/SMMpanel | GitHub ★40 | All-in-one SMM panel, 70+ platforms |
| Ezkify/smm-panel-api | GitHub ★3 | PHP client & API docs for SMM panel |
| FollowersMore | GitHub ★4 | SMM panel for followers, likes, views |
| SpotifyPanel | spotifypanel.com | Multi-platform SMM panel |

## Comparison Matrix

| Service | Free Tier | View Manipulation | VN Geo-Target | Price |
|---|---|---|---|---|
| TikAPIs.com | ✅ 200-1000/day | ✅ "Views video by ID" | Need VN accounts | Unknown paid |
| TikAPI.io | ⚠️ 5-day trial | ❌ Not explicit | ❌ | $29-189/mo |
| xtekky/TikTok-ViewBot | ✅ Open source | ✅ Direct (Zefoy) | ❌ Foreign views | Free |
| Zefoy-based bots | ✅ Open source | ✅ Views+likes+follows | ❌ Foreign views | Free |

## SMM Panel API Testing (2026-07-25)

### Confirmed Standard Format (/api/v2)
9 panels tested, all use the same PerfectPanel API format:

| Panel | API Status | Response |
|-------|-----------|----------|
| BulkFollows | HTTP 401 | "Invalid API key" (API exists) |
| SMMRaja | HTTP 200 | "Invalid API key" (API exists) |
| JustAnotherPanel | HTTP 401 | "Invalid API key" |
| SocialPanel24 | HTTP 401 | "Invalid API key" |
| SMMStone | HTTP 401 | "Invalid API key" |
| SMMFollows | HTTP 401 | "Invalid API key" |
| N1Panel | HTTP 401 | "Invalid API key" |
| SMMVendor | HTTP 401 | "Invalid API key" |
| SMMHeaven | HTTP 200 | HTML page (no API) |

All except SMMHeaven have working API endpoints — registration required for API key.

### like.vn (Vietnamese SMM Panel)
- 5M+ orders, 289K members, 251 servers
- TikTok View tiers: SV1 (3.2₫), SV2 (2.88₫), SV3 (1.9₫), SV4 (0.7₫), SV5 (FREE)
- Laravel backend, jQuery AJAX, CSRF+session auth
- API: requires login, no public API documentation found
- **Only confirmed source of VN-geolocated views via API**

### xtekky/TikTok-ViewBot Clarification
- ★1,848, updated TODAY — BUT it's a **Zefoy-based bot** (Selenium), NOT a private API tool
- `old/main.py` also Zefoy-based (tls_client)
- `v2.py` uses Selenium to automate zefoy.com
- Does NOT interact with TikTok's API directly
- All "view bots" in this repo class are Zefoy wrappers

### HkerVit/TikTok-Private-API (★50, updated 2026-07-22)
- Has X-Gorgon signing (v0404 algorithm)
- Calls `api-h2.tiktokv.com` — TikTok's private API
- Tested: returns HTTP 400 "Invalid parameters" — v0404 signing is OUTDATED
- No view endpoint implemented (only follow, like, edit profile)
- **NOT usable for view inflation** — old signing + missing endpoints

## VN Geolocation Notes
- No service explicitly offers VN-geolocated views through API
- For VN views: register TikTok accounts with Vietnamese location/IP, use Vietnamese proxy
- TikAPIs.com's account signup features could help create VN accounts
- traodoisub.com (Vietnamese coin-exchange) is the only confirmed source of Vietnamese views
- **SMM panels (like.vn) are the fastest path to VN views** — they have existing VN infrastructure

## tikfollowers.com Confirmed Flow (Playwright-tracked 2026-07-25)

Full browser automation flow verified via Playwright network interception:

1. Navigate to `/free-tiktok-video-views`
2. Fill `#inputFieldEl` with video URL
3. Click `#searchBtnEl` → captures `POST /api/search` response
4. Wait for `#startProcessBtnEl` to become visible
5. Click Start Earning → SweetAlert popup → Click OK
6. Captures `POST /api/process` response
7. Result modal shows "Process Successful!"

**Critical finding**: The entire flow is CLIENT-SIDE deception when tikapis.com is down:
- `/api/search` works (returns real video data from TikTok CDN)
- `/api/process` returns "success" + amount_processed
- BUT no request ever reaches TikTok — tikapis.com backend is DOWN
- The 13-20 second wait is a `setTimeout`, not real processing
- SweetAlert shows fake success regardless of backend state
