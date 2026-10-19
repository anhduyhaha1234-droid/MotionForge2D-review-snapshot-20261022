# tikfollowers.com Browser Automation Flow (2026-07-24)

## Complete Browser Flow (Playwright/Captured)

### Step 1: Navigate
```
GET https://tikfollowers.com/free-tiktok-video-views
```
Page loads with input field `#inputFieldEl`, search button `#searchBtnEl`.

### Step 2: Fill Input + Click Search
- Fill `#inputFieldEl` with video URL or ID
- Click `#searchBtnEl`
- Page shows SweetAlert info popup ("Please wait...") with 3-second timer

### Step 3: API Search (auto-triggered)
```
POST https://tikfollowers.com/api/search
Content-Type: application/json
X-Requested-With: XMLHttpRequest
Referer: https://tikfollowers.com/free-tiktok-video-views

Body: {"input": "7547761978786319624", "type": "videoDetails"}
```

Response:
```json
{
  "status": "success",
  "token": "7yFcuusAoFeiQUPz5w4o...",
  "username": "tadgaming0798",
  "aweme_id": "7547761978786319624",
  "user_id": 7358690788635561000,
  "sec_uid": "MS4wLjABAAAAl78V6fbZpRgMIWTpp-...",
  "aweme_avatar": "https://p16-common-sign.tiktokcdn.com/...",
  "stats": {
    "play_count": 3626,
    "digg_count": 27,
    "share_count": 5,
    "comment_count": 6
  },
  "success": true
}
```

### Step 4: UI Updates
- User info section shows (avatar, username, stats)
- `#startProcessBtnEl` becomes visible (display: block)
- Stats display: play_count, share_count, digg_count

### Step 5: Click Start Earning
- Click `#startProcessBtnEl`
- SweetAlert confirmation popup appears
- Click `.swal2-confirm` (OK button)

### Step 6: API Process (auto-triggered after SweetAlert OK)
```
POST https://tikfollowers.com/api/process
Content-Type: application/json
X-Requested-With: XMLHttpRequest
Referer: https://tikfollowers.com/free-tiktok-video-views

Body: {<entire search response>, "type": "video_views"}
```

Response:
```json
{
  "status": "success",
  "title": "Process Successful!",
  "message": "Your request for 2651 video_views for @tadgaming0798 has been completed successfully.",
  "data": {
    "status": "success",
    "token": "...",
    "amount_processed": 2651,
    "service_type": "video_views"
  },
  "additional_offers": [...],
  "timestamp": 1784893954,
  "success": true
}
```

### Step 7: Result Modal
- SweetAlert shows success message with amount
- Auto-reloads page after delay

## Key Observations

1. **Only 2 API calls total**: `/api/search` and `/api/process`. No calls to tikapis.com or TikTok from browser.
2. **"Success" is ALWAYS returned**: The frontend never shows failure from the process endpoint. Even when tikapis.com backend is DOWN.
3. **The 13-20 second wait is fake**: `processWaitTimeSeconds: AppUtils.randint(13, 20)` is a client-side `setTimeout`, not real processing.
4. **reCAPTCHA is disabled**: `recaptchaEnabled: false` in the config.
5. **Token is mandatory**: Without the token from search, process returns 403.

## Config Structure (inline in HTML)

```javascript
const config = {
    navigationWarningEnabled: true,
    initialProgressBarDuration: AppUtils.randint(8, 11),
    processWaitTimeSeconds: AppUtils.randint(13, 20),
    baseUrl: 'https://tikfollowers.com/',
    processApiType: "video_views",      // or "like", "followers", "video_shares"
    isFindUserIDPage: false,
    pageName: "Free TikTok Video Views",
    formApiType: "videoDetails",        // or "getUserDetails"
    recaptchaEnabled: false,
    recaptchaSiteKey: '6Lc6bT4rAAAAAIq5n21JThEIbULSv73FcTr-V2mf',
    apiTimeoutMilliseconds: 10000,
    maxApiRetries: 1,
    apiRetryDelay: 2000
};
```

## VN Proxy Behavior

**CRITICAL FINDING**: Using VN proxies to call tikfollowers.com does NOT produce VN views.

```
You --[VN proxy]--> tikfollowers.com --[tikapis.com server (non-VN)]--> TikTok
```

- The proxy only affects YOUR connection to tikfollowers.com
- The actual view generation happens server-side: tikfollowers → tikapis.com → TikTok
- tikapis.com uses THEIR OWN proxies/devices (Algeria config), not yours
- **Result**: 108 VN proxies tested → views claimed (2,496) but actual count: +0

## Playwright Automation Script

See `C:\Users\Admin\tmp\tiktok_tracker2.py` for a complete working Playwright script that:
1. Navigates to the views page
2. Fills the video URL
3. Captures the /api/search response
4. Waits for Start Earning button
5. Clicks Start Earning → SweetAlert OK
6. Captures the /api/process response
7. Monitors progress for 20 seconds
