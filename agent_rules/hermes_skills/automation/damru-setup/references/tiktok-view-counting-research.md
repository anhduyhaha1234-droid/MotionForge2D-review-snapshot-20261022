# TikTok View Counting — Deep Research (July 2026)

## How TikTok Counts Views

### What Counts as a View
- **Video must actually PLAY** in a browser/app context — page load alone does NOT count
- **Account login required** — unauthenticated browser sessions don't increment view counter
- **Minimum watch time** — video must play for several seconds (exact threshold unknown)
- **Server-side deduplication** — same IP + same device fingerprint = 1 view max

### Anti-Bot Detection Layers (Confirmed)
1. **navigator.webdriver flag** — headless browsers expose `navigator.webdriver=true`
2. **Chrome headless markers** — specific JavaScript properties leaked in headless mode
3. **Canvas/WebGL fingerprinting** — detects automation tools
4. **IP deduplication** — same IP = 1 view regardless of sessions
5. **Device fingerprint validation** — video_play event must match session's device_id
6. **Server-side event dedup** — replaying same event payload returns sc=9 (duplicate)

## TikTok Internal API Endpoints (Tested)

### `/aweme/v1/aweme/stats/` — PATCHED
- All domains return HTTP 403 Access Denied
- Domains tested: api22-core-c, api19-core-c, api16-core-c, api21-core-c, api-h2, api.tiktokv.com
- Even with status_code=0 responses, view count doesn't increase

### `/aweme/v1/play/` — Non-functional
- Returns HTTP 200 with status_code=0
- BUT view count doesn't actually increase
- This is a telemetry endpoint, not a view counter

### `mcs-sg.tiktokv.com/v1/list` — Event Tracking
- TikTok sends `video_play` events here from browser
- First send from browser: `{"e":0,"sc":1}` (success)
- Replay same payload: `{"e":0,"sc":9}` (duplicate detected)
- Modified device_id: `{"e":0,"sc":4}` (invalid fingerprint)
- **Conclusion:** Cannot replay events to inflate views

### TikTok Web Embed/CDN — Non-functional
- oembed API: read-only metadata
- Embed page: loads but doesn't count views
- CDN video fetch: 403 Forbidden
- Share/report API: no view effect

## tikfollowers.com API (REVERSE-ENGINEERED)

### Flow
1. `POST https://tikfollowers.com/api/search`
   - Body: `{"input": "<video_id>", "type": "videoDetails"}`
   - Response: `{"status":"success","username":"...","aweme_id":"...","user_id":...,...}`
   - reCAPTCHA currently DISABLED (`recaptchaEnabled: false` in page config)

2. `POST https://tikfollowers.com/api/process`
   - Body: `{...search_response_data, "type": "video_views"}`
   - Response: `{"status":"success","message":"Your request for 832 video_views for @user has been completed successfully."}`

### Key Config (from page JavaScript)
```
processApiType: "video_views"
formApiType: "videoDetails"
recaptchaEnabled: false
recaptchaSiteKey: '6Lc6bT4rAAAAAIq5n21JThEIbULSv73FcTr-V2mf'
processWaitTimeSeconds: 13-20 (random)
baseUrl: 'https://tikfollowers.com/'
apiTimeoutMilliseconds: 10000
maxApiRetries: 1
```

### How It Works
- Backend: tikapis.com (reverse-engineered TikTok Private API)
- tikapis.com implements ByteDance encryption: X-Argus, X-Ladon, X-Gorgon, X-Khronos
- Maintains pool of TikTok accounts for sending views
- Each cycle: ~832 views, ~20s process time
- Cooldown: ~70 seconds between cycles for same video
- Rate: ~37,000 views/hour if continuously running

### Browser Automation Flow
1. Navigate to `https://tikfollowers.com/free-tiktok-video-views`
2. Wait for Search button (page loads with "Loading..." first)
3. Fill `#inputFieldEl` with video URL
4. Click Search button → wait for `/api/search` response
5. `#startProcessBtnEl` becomes visible
6. Click Start → modal appears → click `.swal2-confirm` (OK)
7. Progress bar runs 13-20 seconds
8. `/api/process` API called → success modal

### Important Notes
- Page uses `serviceItems` JavaScript array for service configuration
- API calls are XHR, not fetch — use Playwright `response.on` to capture
- Button text changes from "Loading..." to "Search" after page fully initializes
- Must wait for button to be "Search" before interacting

## Proxy Testing Lessons

### httpbin.org is Unreliable for SOCKS5 Testing
- Returns 503 "Service Temporarily Unavailable" through residential SOCKS5 proxies
- **Always test proxies against the actual target** (e.g., TikTok)
- Test command: `curl -s --socks5-hostname "user:pass@host:port" --max-time 15 "https://www.tiktok.com" -o /dev/null -w "%{http_code} %{size_download}"`

### Playwright/Selenium SOCKS5 Auth
- Neither Playwright nor Selenium support SOCKS5 proxy authentication natively
- Chrome `--proxy-server=socks5://host:port` doesn't support auth
- **Solution:** Use pproxy to create local HTTP proxy relays:
  ```bash
  pip install pproxy
  python -m pproxy -l http://0.0.0.0:18080 -r "socks5://host:port#user:pass"
  ```
  Then use `http://127.0.0.1:18080` as HTTP proxy in Playwright/Selenium

### Vietnamese View Services Found
- like.vn — Vietnamese SMM panel with free tier
- likeqq.vn — Lists free view websites
- 100like.vn — Free Vietnamese view tool
- All require browser interaction (reCAPTCHA or similar)

## Damru/Redroid for TikTok Views (Architecture)

### Best Approach: Redroid + Vietnamese Proxy
1. Start Redroid container with Chrome installed
2. Push Chrome native libs (see damru-setup pitfalls)
3. Dismiss Chrome FRE (First Run Experience)
4. Set Vietnamese SOCKS5 proxy via iptables or Damru's proxy bridge
5. Open TikTok video via ADB intent
6. Wait for video to play (15-30 seconds)
7. Rotate proxy, repeat

### Why This Works
- Real Android device fingerprint (not headless browser)
- Each proxy = unique IP = unique view
- Vietnamese proxy = Vietnamese view count
- TikTok can't detect automation (real Chrome on real Android)

### Limitations
- Need Vietnamese SOCKS5 proxies (current proxies are international)
- ~53 seconds per view (including load + play + rotate)
- ADB connection unstable with Redroid (reconnect frequently)
- Chrome native libs must be pushed after each container recreation
