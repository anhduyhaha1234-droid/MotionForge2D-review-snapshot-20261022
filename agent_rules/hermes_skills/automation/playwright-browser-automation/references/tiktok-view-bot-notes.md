# TikTok View Bot — Playwright Desktop Automation Notes

## Test Results (July 2026)

**Target video:** `https://www.tiktok.com/@tadgaming0798/video/7547761978786319624`

| Metric | Direct (no proxy) | Via Proxy |
|--------|-------------------|-----------|
| Success rate | 10/10 (100%) | 0/10 (0%) |
| Avg time per view | 10.6s | N/A |
| Total time | 110.7s (1.8 min) | N/A |
| Video element detected | 9/10 | N/A |

**Failure cause:** All 20+ proxies from `dc-vn24.proxyvt.com` returned `net::ERR_EMPTY_RESPONSE` — proxy service completely unresponsive. Not TikTok blocking; proxies didn't even connect.

## Proxy Service: dc-vn24.proxyvt.com

- Format: `dc-vn24.proxyvt.com:PORT:USER:PASS`
- HTTP CONNECT proxy format
- Ports vary (41000-64000 range)
- **Status (July 2026): ALL DEAD** — `ERR_EMPTY_RESPONSE` on all tested ports
- Also failed as SOCKS5 (timeout)
- **Conclusion:** Proxy service needs renewal/replacement before reuse

## TikTok Auto-Play Behavior

- Video auto-plays immediately on page load (no click needed)
- `<video>` element present in DOM after `domcontentloaded`
- 9/10 pages had detectable `<video>` element (1 may have had a different DOM structure)
- Minimum effective wait: ~6s for view registration
- Recommended wait: 8-15s randomized for realism

## Browser Fingerprint Rotation

Per-session randomization applied:
- User-Agent: 7 real UA strings (Chrome 123-125, Firefox 126, Safari 17.5, Edge 123)
- Viewport: 1280-1920 × 720-1080 random
- Locale: en-US, en-GB, en-AU, en-CA
- Timezone: America/New_York, America/Chicago, Europe/London, Asia/Tokyo

## TikTok Anti-Bot Measures

From prior Damru testing (see damru-setup skill):
- IP reputation checking (datacenter IPs flagged)
- Canvas/WebGL/AudioContext fingerprinting
- TLS/JA3 fingerprint analysis
- WebRTC private IP leak detection
- DNS leak checks (IP vs DNS resolver geography mismatch)
- View velocity detection (sudden spikes from same IP ranges)
- Cookie/session persistence tracking

**Bottom line:** Desktop Playwright without anti-detect measures will work for testing/proof-of-concept but won't produce real view counts at scale. TikTok deduplicates views from same IP and fingerprints repeated browser sessions.

## When to Use Desktop Playwright vs Damru

| Scenario | Use |
|----------|-----|
| Quick testing / proof of concept | Desktop Playwright |
| Single-session automation | Desktop Playwright |
| Scale with unique fingerprints | Damru (Android-native, 8-layer stealth) |
| Bypass Cloudflare/DataDome | Damru |
| Residential proxy + unique device profile | Damru |
| Simple scraping of non-protected sites | Desktop Playwright |
