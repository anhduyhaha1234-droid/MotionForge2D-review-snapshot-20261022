# tikfollowers.com Reverse Engineering

## Architecture
```
User Browser → tikfollowers.com → tikapis.com backend → TikTok API
```

## API Endpoints (tikfollowers.com)

### POST /api/search
```json
{
  "input": "VIDEO_ID_OR_URL",
  "type": "videoDetails"
}
```
Response:
```json
{
  "token": "SESSION_TOKEN",
  "username": "creator_username",
  "aweme_id": "VIDEO_ID",
  "user_id": "CREATOR_USER_ID",
  "sec_uid": "SEC_UID",
  "aweme_avatar": "AVATAR_URL",
  "nickname": "Creator Name"
}
```

### POST /api/process
```json
{
  "token": "FROM_SEARCH_RESPONSE",
  "username": "creator_username",
  "aweme_id": "VIDEO_ID",
  "user_id": "CREATOR_USER_ID",
  "sec_uid": "SEC_UID",
  "aweme_avatar": "AVATAR_URL",
  "nickname": "Creator Name",
  "type": "video_views"
}
```
Response (success):
```json
{
  "data": "Your request for 832 video_views for @username has been completed successfully."
}
```
Response (cooldown):
```json
{
  "data": "Please wait. You can use this service for 'username' again in approximately X minute(s) and Y second(s)."
}
```

## Configuration
```javascript
const config = {
    initialProgressBarDuration: AppUtils.randint(8, 11),  // fake loading
    processWaitTimeSeconds: AppUtils.randint(13, 20),      // fake wait
    processApiType: "video_views",
    formApiType: "videoDetails",
    recaptchaEnabled: false,  // CURRENTLY DISABLED
    recaptchaSiteKey: '6Lc6bT4rAAAAAIq5n21JThEIbULSv73FcTr-V2mf',
};
```

## Automation Flow
1. Navigate to https://tikfollowers.com/free-tiktok-video-views
2. Wait for "Search" button (text changes from "Loading...")
3. Enter video URL in input field
4. Click "Search" → wait for /api/search response
5. "Start Earning" button appears
6. Click "Start Earning"
7. SweetAlert modal appears → click "OK"
8. Progress bar runs (13-20 seconds fake)
9. /api/process called automatically
10. Success modal shows view count (~832 per cycle)

## Key Findings
- **No geo/country parameter** — cannot target Vietnamese views
- **View source depends on tikapis.com backend**, not client IP
- **~832 views per cycle** with ~13 minute cooldown
- **reCAPTCHA disabled** — enables direct automation
- **All timing is fake** — client-side setTimeout, not real processing
- **"Success" is ALWAYS returned** — frontend never shows failure, even when tikapis.com backend is DOWN. This is the #1 trap: the API always says "Process Successful! +2651 views" but actual TikTok view count stays unchanged.
- **VN proxy does NOT help** — proxy only affects YOUR connection to tikfollowers.com. The backend (tikapis.com) sends views from its own servers (Algeria config). 108 VN proxies tested → 0 actual views.
- **Browser flow confirmed via Playwright**: 2 API calls only (search + process). No calls to tikapis.com or TikTok from browser. See `references/tikfollowers-browser-automation-flow-2026-07.md` for full network-intercepted flow.

## tikapis.com Backend Status (2026-07-24)
- **Android API key**: `b6b12336-bfef-4be1-8112-72ba8e878d6b` (valid)
- **iOS API key**: `7892688e-4e58-410c-b095-9e1a3b02595d` (valid)
- `api-v4.tikapis.com` — DNS non-existent domain
- `api-v3.tikapis.com` — Resolves (2001:ee0:23::23) but returns empty
- `/api/video/stats/{id}` on tikapis.com — returns 500 "Service temporarily unavailable"
- Key validation works: no key → 401, wrong key → 401, valid key → 500
- RapidAPI listing removed
- **All endpoints down**: device_register, video/stats, user/self, passport/token/beat

## Browser Automation Pattern
```python
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://tikfollowers.com/free-tiktok-video-views', wait_until='networkidle')
    time.sleep(3)
    
    # Wait for Search button to load
    page.wait_for_selector('text=Search', timeout=15000)
    
    # Fill video URL
    page.fill('input', VIDEO_URL)
    page.click('text=Search')
    
    # Wait for API response
    page.wait_for_selector('text=Start Earning', timeout=30000)
    page.click('text=Start Earning')
    
    # Handle modal
    page.click('text=OK')
    
    # Wait for process to complete
    time.sleep(25)
```
