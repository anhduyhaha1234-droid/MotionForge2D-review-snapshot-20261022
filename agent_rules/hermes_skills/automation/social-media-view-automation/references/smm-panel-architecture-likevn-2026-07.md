# SMM Panel Architecture Analysis: like.vn (July 2026)

## Overview
like.vn is a Vietnamese SMM (Social Media Marketing) panel — a web frontend + order management system that resells social media engagement (views, likes, followers, shares) across TikTok, Facebook, Instagram, YouTube, Shopee, Lazada, X/Twitter, and Google Maps. Claims 8+ years in operation.

## Framework & Stack
- **Backend**: Laravel (PHP) — confirmed by CSRF token pattern (`meta name="csrf-token"`), blade templating, session-based auth
- **Frontend**: jQuery + AdminLTE theme + Bootstrap + SweetAlert2 (Swal) for modals
- **Bot protection**: Cloudflare Turnstile
- **Analytics**: Google Analytics (G-PVY0H7ZJP0) + Google Ads (AW-11455244301)
- **Live chat**: s1.what-on.com widget (`widget/service-v2.js?key=cazOr6X`)
- **Keywords meta**: `smm panel vietnam, hệ thống mxh, like, like vn`

## Discovered API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `POST /api/{service-slug}/order` | POST | Create order for any service (e.g. `/api/mua-view-tiktok/order`) |
| `POST /api/get-uid` | POST | Resolve external URL (TikTok, FB, etc.) to internal `objectId`. Params: `link`, `type` |
| `POST /notify/noti-bank` | POST | Bank payment notification polling (client calls every 10s when on `/recharge/balance`) |
| `POST /api/upload/image` | POST | Image upload, returns `{status: "success", data: {url: "..."}}` |

## Authentication & Security
- **CSRF token** required on all POST requests (Laravel standard `X-CSRF-TOKEN` header)
- **api-token** meta tag — empty for logged-out users, populated when authenticated
- **Session-based auth** — must be logged in to create orders
- **Cloudflare Turnstile** CAPTCHA on registration/login forms
- Free tier requires account creation

## TikTok View Order Flow
1. User pastes TikTok video URL → frontend calls `POST /api/get-uid` with `{link: url, type: undefined}` → returns `objectId` (internal representation)
2. User selects server (radio buttons: sv1-sv5), enters quantity, optional giftcode
3. Form submits `POST /api/mua-view-tiktok/order` with: `objectId`, `server_order`, `amount`, `reaction`, `free`, `giftcode`
4. For free tier (`free=1`): client shows a 120-second countdown timer before submitting (anti-abuse rate limiting)
5. Response: JSON `{status, message, html, data}`

## Server Tier Architecture (TikTok Views)

The multi-server pattern is **the key indicator that like.vn is a reseller, not a generator**. Each "server" is a different upstream provider with its own pricing, speed, and quality characteristics.

| Server | Price (VND/view) | Min Order | Max/Order | Max/Video | Speed | Warranty |
|--------|-----------------|-----------|-----------|-----------|-------|----------|
| SV1 | 3.2 | 1,000 | 500K | 10M | ~500K/day | 10 days |
| SV2 | 2.88 | 3,000 | 500K | 100M | Not specified | 20 days |
| SV3 | 1.9 | 1,000 | 500K | 10M | ~100K/day | 10 days |
| SV4 | 0.7 | 1,000 | 500K | 10M | ~100K/day | None |
| SV5 (free) | 0 | 100 | 100 | — | — | None |

**Price range**: 0.03-0.1 VND/view (~$0.000004/view at 25,000 VND/USD)

## Multi-Order (Bulk) Feature
- Supports ordering for up to 100 links at once
- Form action URL uses `multi-order` pattern: `action.split('multi-order')[0] + "order"`
- Orders sent sequentially via AJAX with progress tracking (success/fail counts)
- UI shows live progress textarea with per-link results

## How Views Are Actually Generated (Inference)

like.vn does NOT generate views directly. Evidence:
1. **Multiple "servers"** = multiple upstream providers (each with different quality/pricing)
2. **"Không yêu cầu mật khẩu"** — no TikTok password needed (only video URL)
3. **Views can "drop" (tụt view)** — indicates sources TikTok can detect/remove
4. **Warranty/refill system** — standard in SMM reselling to cover upstream quality variance
5. **Claim "không sử dụng bot ảo"** — "no fake bots" is marketing; the cheaper tiers almost certainly use automated sources

### Upstream Provider Methods (most likely)
- **Android device farms** (real phones or emulators) running real TikTok app with logged-in accounts
- **Rotating residential/mobile proxies** to distribute requests across IP ranges
- **Account pools** that cycle through viewing videos
- Premium tiers (SV1/SV2): higher-quality traffic, possibly real user incentive networks
- Cheapest tiers (SV4): automated/bot traffic, higher drop rate

## Reseller vs. Provider Model

```
[Customer] → [SMM Panel (like.vn)] → [Upstream Provider A] → [Device Farm / API]
                                   → [Upstream Provider B] → [Account Pool]
                                   → [Upstream Provider C] → [Proxy Network]
```

The panel's value is: UI + payment processing + order management + customer support + SEO. The actual view generation is outsourced.

## Service URL Pattern
All services follow `/mua-{metric}-{platform}` or `/tang-{metric}-{platform}`:
- `/mua-view-tiktok`, `/mua-like-tiktok`, `/mua-follow-tiktok`
- `/tang-comment-tiktok`, `/tang-share-tiktok`, `/tang-yeu-thich-tiktok`
- `/mua-view-facebook`, `/mua-view-youtube`, `/mua-view-x-twitter`
- etc.

## JavaScript Architecture

### Core JS Files
- `assets/js/function.js` — AJAX wrapper (`curl()` function), order submission, image upload, UID resolution
- `theme/likevn/js/main.js` — UI interactions, service browser widget, sidebar navigation
- `theme/likevn/js/traffic.js` — Google referral detection, gift code system for SEO traffic

### AJAX Pattern
```javascript
// All API calls go through this wrapper:
function curl(body, callback) {
    $.ajax({
        type: body.method,  // typically POST
        url: body.url,
        data: body.data,
        contentType: "application/x-www-form-urlencoded;charset=utf-8",
        beforeSend: function(request) {
            request.setRequestHeader("api-token", $('meta[name="api-token"]').attr("content"));
        },
        // ... loading indicator + button disable logic
    });
}
```

### Traffic/Gift Code System
- Detects if visitor came from Google search (referral check)
- Shows "LẤY MÃ QUÀ TẶNG" (Get Gift Code) button only for Google-referred visitors
- Implements cooldown timer before revealing code (60-90 second random delay)
- SEO conversion funnel: organic search → free gift code → account creation → paid orders

## Key Technical Signals to Look For in Other SMM Panels
1. Multiple server/provider radio buttons with different pricing tiers
2. CSRF token + session-based auth (Laravel/PHP is most common)
3. `/api/get-uid` or similar URL resolver endpoint
4. "Server description" HTML embedded in radio button `description` attribute
5. `price`, `min`, `max` attributes on server selection elements
6. Free tier with rate limiting (timer-based anti-abuse)
7. Warranty/refill language tied to specific servers
