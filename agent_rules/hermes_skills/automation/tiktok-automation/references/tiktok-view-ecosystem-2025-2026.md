# TikTok View Ecosystem — 2025-2026 Research

Research date: 2026-07-24. Sources: GitHub API search, source code analysis, HTTP probing of live services.

## Critical Finding: No Public Direct API Method Works

Every single public method in 2025-2026 delegates to a **third-party service**. There is:
- **No** new endpoint besides `/aweme/v1/aweme/stats` publicly documented
- **No** method that bypasses `device_register` requirement for direct API calls
- **No** method using TikTok web/embed instead of mobile API for view injection
- **No** method using TikTok Lite or regional variants for view injection

The direct API approach (v44.x signing) returns `status_code=0` but views don't stick without a registered device. Nobody has publicly solved `device_register`.

---

## Method Category 1: Zefoy.com Automation (Most Popular)

**How it works**: Automates zefoy.com website via Selenium/undetected-chromedriver. Submit a TikTok video URL; Zefoy's backend sends views from its own bot network.

**Top GitHub repos (all active as of 2026-07)**:
| Repo | Stars | Tech | Notes |
|------|-------|------|-------|
| xtekky/TikTok-ViewBot | 1848★ | Python/Selenium | Also has Zefoy subdir, paid course at whop.com/reverser-academy |
| kangoka/tiktodv3 | 876★ | Python/Selenium | Dedicated Zefoy automator |
| simonfarah/tiktok-bot | 883★ | Python/Selenium | Followers, hearts, views, shares |
| xtekky/zefoy | 798★ | Python/Selenium | Dedicated Zefoy bot |
| jfadev/bottok | 595★ | Node.js/Puppeteer | Automates BOTH zefoy.com AND freer.es |
| zebbern/Zefoy-Automation | 81★ | Python | "0 user interaction" |
| Sneezedip/Tiktok-Booster | 250★ | Python/Tesseract | CAPTCHA bypass via OCR |

**View rate**: ~500-1000 views per submission, with cooldown timers (varies by service availability).

**Status**: zefoy.com returns HTTP 200 (active). freer.es returns HTTP 502 (down).

**Key**: No device_register needed — Zefoy handles actual view injection on their servers. Views are foreign/global, not geo-targetable.

---

## Method Category 2: Third-Party SMM Panel API (Direct HTTP, No Browser)

### socioblend.com
- **Repo**: RozhakLabs/SocioBlend (8★)
- **Endpoint**: `POST https://socioblend.com/submit-tiktok.php`
- **Data**: `video_url=<tiktok_url>` (form-encoded)
- **Rate**: ~1,000 views per 15 minutes
- **Status**: HTTP 200 confirmed active (Hostinger/Cloudflare/PHP 7.4)

### myinstafollow.com
- **Repo**: RozhakLabs/TikBoostX (6★)
- **Endpoint**: `POST https://myinstafollow.com/themes/vision/part/free-tiktok-views/submitForm.php`
- **Data**: multipart form with fields `postlink`, `service=6397`, `tiktokviewsQuantity=100`, plus an `extended_user_agent` fingerprint blob
- **Rate**: 100 views per 4 hours (very slow)
- **Status**: Likely behind Cloudflare challenge

### freer.es (used by jfadev/bottok)
- **Status**: HTTP 502 — **Currently down**
- Together with Zefoy, provides the two backends for bottok

---

## Method Category 3: Vietnamese Coin-Exchange Platform

### traodoisub.com
- **Repos**: RozhakLabs/TikSub (17★), Snhvn/Tool-Buff-Tiktok (5★), CYooBin10/ToolBuffViewTikTok, raichintui222/Hnt-X, litoufuang/Limbozz-tool
- **How it works**: Earn coins by completing missions (liking/following other users' TikTok), then spend coins to get views
- **Pricing**: 150,000 coins = 1,000 views minimum; 35,000 coins = 50 likes; 140,000 coins = 100 followers
- **Status**: Returns 403 (Cloudflare challenge — still operational, needs browser session)
- **Key advantage**: Vietnamese user base — the only platform targeting Vietnamese views
- **Key disadvantage**: Very slow — must farm coins first (auto-clicker required)
- **Setup**: Typical Vietnamese Termux-based workflow: `bash <(curl -Ls ...tool-install-tiktok.sh)`
- **To reach 20M views**: Would need 3 billion coins — impractical for free users. Must have paid/bulk option.

---

## Method Category 4: Android Device Automation (Physical/Emulated)

- **Repo**: Hormold/tiktok-warmup (53★)
- **Tech**: TypeScript + ADB + vLLM vision AI
- **How it works**: Controls real/emu Android devices via ADB, runs TikTok app, watches videos
- **Architecture**: DeviceManager → AgentManager → Worker, with 3 stages (initiating, learning, working)
- **Rate**: Very slow, scales with number of devices
- **Relevance**: Could produce authentic Vietnamese views if using Vietnamese IPs/devices

---

## Method Category 5: Vietnamese "Buff" Tools (Scripts/Installers)

- **Snhvn/Tool-Buff-Tiktok** (5★): Shell installer for Termux, wraps TTP-Tool and others
- **raichintui222/Hnt-X** / **View**: Buff views tiktok (minimal docs)
- **hhdvippro/tiktok-**: "BUFF VIEW TIKTOK FREE"
- **hoanglong163/BuffViewTik**: Buff view on tiktok
- Most are minimal READMEs wrapping other services. The actual backend is typically traodoisub.com or similar.

---

## Comparison Matrix for Vietnamese Views at Scale

| Method | Vietnamese Views? | Scale | Cost | Complexity |
|--------|-------------------|-------|------|------------|
| Direct API (v44.x signing) | Yes (VN proxies) | Unlimited in theory | Proxy cost | High (device_register unsolved) |
| Zefoy automation | No | ~1K/cycle | Free | Medium (CAPTCHA) |
| socioblend.com | No | ~1K/15min | Free | Low |
| myinstafollow.com | No | 100/4hr | Free | Low |
| traodoisub.com | Yes | 1K/150K coins | Free (farm) or paid | Medium |
| Android device farm | Yes (with VN IPs) | Per-device | Hardware cost | Very High |

## Bottom Line

No public method delivers geo-targeted Vietnamese views at scale for cheap. Options:
1. **traodoisub.com** for Vietnamese views — slow but real Vietnamese audience
2. **Zefoy** for volume — fast but foreign views
3. **tikfollowers.com** (832 views/cycle, foreign) — already working in skill's main flow
4. **SMM panels** as supplementary channels
5. **Direct API** still the holy grail if device_register can be solved
