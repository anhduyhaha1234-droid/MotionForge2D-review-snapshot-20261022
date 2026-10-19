# TikTok X-Gorgon & Mobile API Signing Repos (2026-07-23, updated 2026-07-24)

## Confirmed Alive X-Gorgon/X-Argus/X-Ladon Signing Repos

These repos implement the proprietary signing algorithms TikTok requires for mobile API endpoints like `/aweme/v1/aweme/stats`. Without valid signatures, requests return 403 or empty body.

### ⭐ WORKING: v44.x Signing (confirmed 2026-07-24)

| Repo | Stars | Description | Status |
|------|-------|-------------|--------|
| **code-root/tiktok-android-signing-toolkit** | 28 | v44.x signing (X-Gorgon/Argus/Ladon), device_register, login client, MITM helpers, feed API client | **CONFIRMED WORKING** — updated 2026-07-21, v44.3.15 signing engine |

This repo produces X-Gorgon headers with `84xx` prefix (not `0404` from older repos). Uses SM3 hash + SIMON-128 cipher + AES-CBC. Returns actual JSON responses with `status_code: 0` from `/aweme/v1/aweme/stats`. See `references/tiktok-v44x-signing-working-2026-07.md` for full details.

### Old/Outdated Signing (v0404) — returns empty bodies as of 2026-07-24

| Repo | Stars | Description | Status |
|------|-------|-------------|--------|
| SyntaxSparkk/TikTok | 732 | TikTok reverse engineering documentation | Alive |
| ssovit/x-gorogn-khronos-argus-ladon | 338 | Full source: X-Argus, X-Ladon, X-Gorgon, TTEncrypt, XLog | Alive but OUTDATED (v0404, empty responses) |
| xgxkxaxl/X-Ladon-X-Argus-X-Gorgon-X-Khronos-X-Medusa-X-Helios | 130 | 抖音播放量/刷量 algorithms, device register | Alive |
| SebastienWae/tiktok-gorgon-bridge | 104 | Express server with Frida bridge to sign TikTok API requests | Alive (Frida approach stays current) |
| tr4cex/TikTok-Encryption | 82 | Free/open-source signing algorithms | Alive but OUTDATED (v0404 base) |
| HkerVit/TikTok-Private-API | 50 | Full TikTok API wrapper | Alive |
| douyinX-all/tiktok-X-Ladon-X-Argus-X-Gorgon-... | 40 | Chinese Douyin/TikTok API + signing | Alive |
| reverse4free4/TikTok4free | 36 | Commercial signing service | Alive |
| tiktokmate/X-Gorgon-X-Khronos-Tik-Tok | 35 | X-Gorgon + X-Khronos generation | Alive |
| scrapguru/TikTok-Mobile-Security | 7 | X-Argus/X-Ladon/X-Gorgon/X-Khronos | **404, DMCA'd** |

## How the Signing Works

TikTok mobile API requires cryptographic headers on every request:
- **X-Gorgon** — Main request signature (RC4-like in v0404, SM3+SIMON in v44.x)
- **X-Argus** — Data integrity signing (SIMON-128 + AES-CBC in v44.x)
- **X-Ladon** — Anti-unauthorized-access layer (SIMON-128/128 ECB + PKCS7 in v44.x)
- **X-Khronos** — Unix timestamp (anti-replay)
- **X-SS-STUB** — MD5 of POST body (uppercase hex)

### Version Progression
- **v0404** (2022-2024): Simple RC4-like cipher, hardcoded seed values. TikTok now silently rejects (empty 200 response).
- **v44.x** (2025-2026): SM3 hash + SIMON-128 + AES-CBC stack. Currently working (status_code: 0).

### Additional Required Headers (v44.x)
Beyond signing, v44.x requires these headers that old repos omit:
- `x-tt-dm-status: login=0;ct=1;rt=6`
- `sdk-version: 2`
- `x-ss-dp: 1233` (app ID)
- `x-tt-store-region: vn` (target region)
- `passport-sdk-version: 1`
- Full device profile JSON with locale/network/session structure

### Bypass: `as=a1iosdfgh` Parameter

The xtekky/TikTok-View-Bot uses a bypass parameter `as=a1iosdfgh` (credit: @auut). Status: may no longer work alone — the v44.x signing approach is more reliable.

## DMCA Takedowns

TikTok actively DMCA-takes-down signing repos:
- scrapguru/TikTok-Mobile-Security (★7) — **404**
- apisTikTok/TikTok-API (★6) — **404**

**Lesson:** Always fork/star critical signing repos when you find them. They may disappear.

## Third-Party Signing Services

- **tikapis.com** — Backend DEAD as of 2026-07-24 (api-v4.tikapis.com not in DNS). API key works but all endpoints return 500.
- **reverse4free4/TikTok4free** ★36 — Commercial service, 24/7 support

## Web Signing (X-Bogus — separate from mobile)

X-Bogus is for TikTok's **web** API only, not the mobile stats endpoint:
- 5ime/Tiktok_Signature ★316 — X-Bogus + msToken + ttwid (Vercel deployable)
- RUSOCIAL-SU/TiktokWebSigner ★10 — X-Bogus + X-Gnarly 5.1.2
- DudeGeorgesTG/tiktok-web-signer ★10 — X-Bogus + X-Gnarly + device fingerprint
- hiddenexee/Tiktok-Web-Signature ★2 — X-Bogus + X-Gnarly + mssdk-info + strData + edata
