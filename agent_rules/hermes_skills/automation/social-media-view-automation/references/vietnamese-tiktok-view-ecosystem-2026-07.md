# Vietnamese TikTok View Ecosystem (2026-07)

## Vietnamese View Service Websites

These are Vietnamese-language platforms for boosting TikTok views, organized by type.

### SMM Panels (Paid, with free tiers)
- **likeqq.vn** — Full SMM panel: views, shares, favorites, comments, livestream viewers. Free trial available. Supports Facebook, TikTok, Instagram, YouTube. URLs: `/dich-vu-tiktok/`, `/mua-view-tiktok/`, `/tang-share-tiktok/`, `/tang-yeu-thich-tiktok/`, `/tang-comment-tiktok/`, `/tang-mat-livestream-tiktok/`
- **like.vn** — SMM panel with 5 server tiers for TikTok views. Vietnamese 🇻🇳 sources. Laravel stack, jQuery AJAX, CSRF+session auth. **API:** `POST /api/mua-view-tiktok/order` (requires auth + CSRF token). Has free buff guide. Also supports Facebook, Instagram, YouTube, Shopee, Lazada, X/Twitter, Google. **Pricing (2026-07-24):**
  - SV1: 3.2₫/View (with warranty, standard speed)
  - SV2: 2.88₫/View (slow speed, with warranty)
  - SV3: 1.9₫/View (with warranty)
  - SV4: 0.7₫/View (no warranty, currently disabled)
  - SV5: Free (free tier)
  - Article text claims range of 0.03-0.1 VNĐ/view for bulk orders (different tiers)
  - Supports both Vietnamese and international TikTok accounts
  - Bulk order support (100 links simultaneously)
  - **Cost for 20M views:** SV3 @ 1.9₫ = 38,000,000 VND ≈ $1,520 USD
- **thatim.vn** — Vietnamese SMM panel ("Top 1 Seeding Việt Nam"). Supports TikTok, YouTube, Instagram, Facebook, and more. **Has API documentation** ("Tài liệu API" link). Vietnamese phonefarm accounts 🇻🇳. **Pricing (2026-07-24):**
  - SV1: 2.2₫/View (phonefarm, no drop, max 10M/day, Vietnamese 🇻🇳)
  - SV2: 1.3₫/View (fast, cheap, Vietnamese 🇻🇳)
  - SV3: 1.1₫/View (slow, cheap, 30-day warranty, Vietnamese 🇻🇳)
  - SV4: 1.5₫/View (phonefarm, 30-day warranty, Vietnamese 🇻🇳)
  - SV5: 17₫/View (trend views, 30-second watch, Vietnamese 🇻🇳)
  - Min order: 200 views, Max: 1,000,000,000 views
  - **Cost for 20M views:** SV3 @ 1.1₫ = 22,000,000 VND ≈ $880 USD
  - Contact: Telegram @zetteth, Zalo, Facebook Messenger
- **like3s.vn** — Vietnamese SMM panel. Claims from 0.5₫/View for TikTok views. URL: `/dich-vu/tang-luot-xem-video-tiktok`
  - **Cost for 20M views:** 0.5₫ × 20M = 10,000,000 VND ≈ $400 USD (cheapest found)
- **vinafabo.com / vinafabo.net** — Vietnamese SMM panels for TikTok view services. Pricing not confirmed.
- **autosocial.vn** — Vietnamese SMM panel, TikTok view services at `/tang-view-tiktok`
- **100like.vn** — Vietnamese SMM panel primarily for Facebook (likes, follows). Pricing: 38₫/like (Facebook). Limited TikTok support. Has iOS/Android app + web. Free daily Facebook like trials.
- **bufflikes.com** — Domain does NOT resolve (2026-07-24). Dead/defunct.

### Guides / Aggregators (list tools, don't provide services directly)
- **sapo.vn** — "Top 3 web tăng view TikTok nhanh chóng và uy tín"
- **vnick.vn** — "Top 12 Tool tăng view TikTok miễn phí an toàn 2025"
- **mktsoftware.vn** — "Top 11+ app tăng view TikTok free hiệu quả nhất năm 2026"
- **beobeomarketing.net** — "20+ Cách tăng view tiktok free hiệu quả 2026"
- **like.vn** (blog) — "Khám Phá 10 App Tăng View TikTok Miễn Phí" + "Cách Buff View TikTok Miễn Phí và Trả Phí"
- **ghn.vn** — "Tổng hợp tool/app buff view TikTok hiệu quả"
- **flive.vn** — "Cách Tăng View TikTok Miễn Phí"
- **hidemium.io** — "15 cách tăng view TikTok miễn phí" (antidetect browser — useful for multi-account ops)

### Free Web-Based View Tools
- **Likesin.app**, **Mytoolstown**, **ViewsExpert**, **TikFame**

## Vietnamese-Specific GitHub Repos

- **DauDau432/ViewTiktok** — "Buff view ảo tiktok bằng proxy" — Vietnamese-made view bot using proxy rotation. Config: `use-proxy`, `proxy-type` ("http"), `auth`, `credential` (user:pass), `proxyscrape` (auto-collect). Uses `proxies.txt`.

## Vietnamese Proxy Providers (updated 2026-07-23)

For building self-hosted view systems with Vietnamese IPs:

| Provider | Type | Pricing | Notes |
|----------|------|---------|-------|
| IPRoyal (pawns.app) | Residential | ~$1.75/GB | City targeting. Referenced in xtekky viewbot (`geo.iproyal.com:12323`) |
| Bright Data (Luminati) | Res+DC+Mobile | Premium | Largest pool, Vietnam included |
| Smartproxy | Residential | Mid-range | Vietnamese IPs available |
| Soax | Residential | Mid-range | Clean pool, Vietnamese residential |
| IPIDEA | ISP | Budget | ISP-level = more stable than residential |
| Proxy-Seller | DC/Mobile/ISP | Budget | Vietnamese datacenter/mobile/ISP |
| Proxy-Cheap | Residential | Budget | Vietnam support, cheapest option |

**Best for views:** Residential proxies (IPRoyal, Bright Data) — appear as real Vietnamese home users. Datacenter IPs cheaper but more likely flagged.

**For Damru/Redroid:** Route all container traffic through Vietnamese SOCKS5. Configure at Android WiFi proxy level or with iptables DNAT rules.

## Damru/Redroid Integration for Vietnamese Views

**Damru** (akwin1234/damru ★247) — Android-native stealth browser (Redroid + Playwright + CDP):
- Each Redroid container = real Android environment with unique device fingerprint
- Install TikTok APK natively inside container
- Proxy at OS/Android level → all traffic through Vietnamese proxy
- Playwright/CDP for automation, Frida for API interception
- Scores 100% on CreepJS — extremely stealthy
- **Resource cost:** ~2GB RAM per container
- **Architecture:** Vietnamese SOCKS5 → Redroid → TikTok APK → logged-in account → authentic view
- See `damru-setup` skill for setup details

## Vietnamese Search Queries
- `buff view tiktok free`, `tăng view tiktok miễn phí`, `tool tăng view tiktok việt nam`
- `seeding tiktok free`, `web tăng view tiktok`, `app tăng view tiktok free`, `mua view tiktok`

## Key Insight: Vietnamese vs International Approaches

For Vietnamese-IP views specifically, ranked by authenticity:
1. **Damru/Redroid** + Vietnamese residential SOCKS5 + logged-in accounts (most authentic, resource-heavy)
2. Vietnamese SMM panels with geo-targeting (like.vn, likeqq.vn)
3. DauDau432/ViewTiktok with Vietnamese proxies (simpler, less control)
4. Bulk Vietnamese SOCKS5 + `/aweme/v1/aweme/stats` API with X-Gorgon signing (needs signing from `ssovit/x-gorogn-khronos-argus-ladon` ★338 or tikapis.com)
