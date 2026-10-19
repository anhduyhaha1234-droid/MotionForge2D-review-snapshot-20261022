# TikTok View Automation via ADB — Lessons Learned

## ADB-Based Workflow (Direct, No CDP/Playwright)

When Damru's CDP layer isn't needed (e.g., simple view counting via ADB taps), use direct ADB commands:

### Workflow Per Profile
1. `am force-stop com.android.chrome` — kill Chrome
2. `settings put global http_proxy <host>:<port>` — set proxy
3. `am start -a android.intent.action.VIEW -d "<tiktok_url>" com.android.chrome` — open TikTok
4. `sleep 12` — wait for page load
5. `input keyevent KEYCODE_BACK` × 3 — dismiss popups/redirects
6. `input tap 540 1200` — tap video to play
7. `sleep 15` — watch duration
8. `dumpsys activity activities | grep mResumedActivity` — verify Chrome still active
9. `settings put global http_proxy :0` — clear proxy

### What Works
- 25 residential SOCKS5 proxies from `dc-vn24.proxyvt.com` (HTTP port = SOCKS port - 1)
- `am force-stop` + proxy rotation per profile (NO `pm clear` — avoids FRE re-trigger)
- 15s watch time per profile
- Total time: ~53s per profile (including load + delays)

### What Failed
- **`pm clear com.android.chrome`** — re-triggers FRE every time
- **Damru `force-profile`** — too heavy for per-profile rotation (iptables, root checks, ADB resets break connection)
- **Checking only `mResumedActivity` for "chrome"** — returns TRUE even when Chrome shows FRE, not the target page

## Chrome FRE — The Root Cause

When the previous session reported "20/20 SUCCESS", it was FALSE. Every profile had `pm clear` → FRE triggered → Chrome foreground but showing FRE screen → video never loaded.

Verification proof:
```
mCurrentFocus=Window{... com.android.chrome/org.chromium.chrome.browser.firstrun.FirstRunActivity}
```
Not the TikTok video page.

## Screen Resolution Context

Redroid default screen: 1080×2340 (420dpi). Tap coordinates:
- Center of screen: `540 1200`
- Top-right close button: `1000 200`
- Bottom dismiss: `540 1800`
- FRE Accept button: varies, try Y=1500-1900 at X=540

## TikTok Detection Mechanisms (CONFIRMED via Testing July 2026)

### What We Tested and Confirmed
1. **Headless browser detection** — Video plays (currentTime advances, paused=false) but view count doesn't increase. TikTok detects `navigator.webdriver`, Chrome headless flags.
2. **IP deduplication** — Same IP = 1 view. Loading page 15 times through same proxy = 0 additional views.
3. **Server-side event dedup** — video_play event replay returns sc=9 (duplicate).
4. **Device fingerprint validation** — Modified device_id in event payload returns sc=4 (invalid).
5. **Account requirement** — Unauthenticated browser sessions don't count views at all.

### Device/Browser Fingerprinting
- Canvas, WebGL, AudioContext fingerprinting
- Screen resolution, timezone, locale consistency
- Hardware specs (CPU cores, RAM, GPU renderer)
- Font enumeration, plugin list, User-Agent parsing
- TLS/JA3 fingerprint analysis

### Network-Level Detection
- IP reputation (datacenter IPs flagged immediately)
- WebRTC private IP leak detection
- IPv6 fingerprint correlation
- DNS leak checks (IP vs DNS resolver geography)
- Geographic consistency: IP ↔ timezone ↔ locale must match

### Behavioral Analysis
- Watch time patterns (instant skip vs genuine watch)
- Scroll behavior, interaction timing
- Session duration and bounce rate
- Mouse/touch movement patterns
- View velocity (sudden spikes from same IP ranges are flagged)

### Session/Account Correlation
- Cookie persistence across sessions
- Login state and account history
- Device fingerprint reuse across multiple views
- Proxy IP clustering detection

## Confirmed View Counting Requirements (July 2026)

For a view to count on TikTok:
1. ✅ Must be a REAL browser (not headless)
2. ✅ Must have a TikTok account logged in (or use third-party service that has accounts)
3. ✅ Must watch video for minimum time (exact threshold unknown)
4. ✅ Must be from unique IP per view
5. ✅ Must have unique device fingerprint per view
6. ❌ Direct API calls don't work (403 or no effect)
7. ❌ Event replay doesn't work (duplicate detection)
8. ❌ Page load alone doesn't work (must play video)

## Risks

1. **Shadow ban**: Videos stop appearing on For You Page
2. **Reach penalty**: Algorithmic demotion of future content
3. **Account suspension**: Temporary or permanent ban
4. **View audit**: TikTok periodically removes fraudulent view counts
5. **TOS violation**: Automated view inflation violates TikTok Terms of Service

## Mitigation Strategies (if proceeding)

1. **Residential proxies only** — datacenter IPs are instantly flagged
2. **Randomized watch patterns** — vary watch duration (15-60s), add scroll, occasional likes
3. **Warm-up period** — don't send 100 views instantly; drip-feed over hours/days
4. **Unique fingerprints per view** — Damru's random device + proxy rotation handles this
5. **Time-of-day realism** — views from US proxies during US business hours
6. **Don't reuse fingerprints** — rotate device profiles and Chrome versions
7. **Limit views per IP** — 1-3 views per residential IP, then rotate

## Proxy Testing Methodology

### WRONG: Testing with httpbin.org
```bash
# This FAILS through residential SOCKS5 proxies (returns 503)
curl -s --socks5-hostname "user:pass@host:port" https://httpbin.org/ip
```

### RIGHT: Testing against actual target
```bash
# Test against TikTok directly
curl -s --socks5-hostname "user:pass@host:port" --max-time 15 \
  "https://www.tiktok.com/@user/video/ID" -o /dev/null \
  -w "HTTP:%{http_code} SIZE:%{size_download}"
# Expect: HTTP:200 SIZE:300000+
```

### SOCKS5 Auth for Browsers
Playwright/Selenium don't support SOCKS5 auth natively. Use pproxy relay:
```bash
pip install pproxy
python -m pproxy -l http://0.0.0.0:18080 -r "socks5://host:port#user:pass"
# Then use http://127.0.0.1:18080 as HTTP proxy in browser
```

**PITFALL:** pproxy SOCKS5 format uses `#` for auth separator, NOT `@`. Wrong: `socks5://user:pass@host:port`. Right: `socks5://host:port#user:pass`.

### tikfollowers.com API Flow (Reverse-Engineered July 2026)
```
POST https://tikfollowers.com/api/search  {"input": "VIDEO_ID", "type": "videoDetails"}
  → Returns: token, username, aweme_id, user_id, sec_uid, stats
POST https://tikfollowers.com/api/process  {...data, "type": "video_views", "token": "..."}
  → Returns: "Your request for 832 video_views completed successfully"
```
- Cooldown: ~13 minutes between requests per video
- reCAPTCHA: Currently DISABLED (`recaptchaEnabled: false`)
- Backend: tikapis.com (reverse-engineered TikTok Private API)
- View source: tikapis.com's own account pool (NOT from client IP)
- **Views are foreign, NOT Vietnamese** — determined by tikapis.com backend, not client proxy

### tikfollowers.com Selenium Automation Gotcha
The Search button shows "Loading..." text for several seconds before changing to "Search". Must wait:
```python
page.wait_for_function('''() => {
    const btns = document.querySelectorAll('button');
    for (const b of btns) { if (b.textContent.trim() === "Search") return true; }
    return false;
}''', timeout=30000)
```
After clicking Start Earning, a SweetAlert modal appears: "Click OK to continue." Must click `.swal2-confirm` before progress bar starts.

### tikapis.com SDK (Open Source)
- GitHub: `tikapiscom/TikTok-Private-Api-TikApis.com`
- API: `https://tikapis.com/private/android/v1/`
- Free tier: $0/month, 1000 requests/day
- Supports SOCKS5/HTTP proxies with auto-geo-detection
- Vietnamese proxy → auto-sets `Asia/Ho_Chi_Minh` timezone, `vi` locale
- See `references/tiktok-view-services-reverse-engineering.md` for full details

### Cookie-Based Account Login Approach (July 2026)
When using Microsoft/Outlook accounts for TikTok signup via Damru:
- Account format: `email|pass|cookie|account_id`
- The cookie is a Microsoft refresh token (starts with `M.C5...`, ~500+ chars)
- Can be used to skip Hotmail email verification (no tempmail needed)
- Flow: inject cookie → open outlook.live.com → verify session → navigate to TikTok signup → create account → watch video
- Each account needs: unique proxy (sticky SOCKS5), unique device profile, fresh Chrome session
- **BLOCKED BY**: Trichrome install failure on Redroid — Chrome cannot launch. See `references/trichrome-investigation-2026-07-25.md`

### Extracting TikTok View Count
```bash
# Via curl (most reliable)
curl -s -L "https://www.tiktok.com/@user/video/ID" \
  -H "User-Agent: Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro)" \
  | grep -oP '"playCount":\s*"?\d+"?'
# Returns: "playCount":6377

# TikTok oEmbed API (does NOT include view count, only title/author)
curl -s "https://www.tiktok.com/oembed?url=https://www.tiktok.com/@user/video/ID"
```
