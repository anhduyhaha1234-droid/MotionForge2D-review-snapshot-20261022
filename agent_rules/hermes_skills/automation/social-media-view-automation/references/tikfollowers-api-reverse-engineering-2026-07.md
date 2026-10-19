# tikfollowers.com API Reverse Engineering (2026-07-24)

## Complete API Flow

### Endpoint 1: Search Video
```
POST https://tikfollowers.com/api/search
Content-Type: application/json
X-Requested-With: XMLHttpRequest
Origin: https://tikfollowers.com
Referer: https://tikfollowers.com/free-tiktok-video-views

Body: {"input": "7547761978786319624", "type": "videoDetails"}
```

Response (200):
```json
{
  "status": "success",
  "token": "cNOynZ3dd5E2hOUa_4sSM1Okx7s3gl52oe5Ecmmaj_zHRqdlGFo-vWU8XAGxs2Hd",
  "username": "tadgaming0798",
  "aweme_id": "7547761978786319624",
  "user_id": 7358690788635561000,
  "sec_uid": "MS4wLjABAAAAl78V6fbZpRgMIWTpp-KWsx1stYAROpzuVK5sO4jwGPXbOwoNrGwJGHhS5xaqsfG1",
  "aweme_avatar": "https://p19-common-sign.tiktokcdn.com/...",
  "stats": {
    "aweme_id": "7547761978786319624",
    "collect_count": 2,
    "comment_count": 6,
    "digg_count": 27,
    "download_count": 1,
    "forward_count": 0,
    "lose_comment_count": 0,
    "lose_count": 0,
    "play_count": 3624,
    "repost_count": 0,
    "share_count": 5,
    "whatsapp_share_count": 0
  },
  "success": true
}
```

### Endpoint 2: Process Views
```
POST https://tikfollowers.com/api/process
Content-Type: application/json
X-Requested-With: XMLHttpRequest

Body: {
  "username": "tadgaming0798",
  "aweme_id": "7547761978786319624",
  "user_id": 7358690788635561000,
  "sec_uid": "MS4wLjABAAA...",
  "aweme_avatar": "https://...",
  "stats": {...},
  "type": "video_views",
  "token": "FROM_SEARCH_RESPONSE"
}
```

Success Response (200):
```json
{
  "message": "Your request for 832 video_views for @tadgaming0798 has been completed successfully.",
  "status": "success"
}
```

### Error Responses

**403 InvalidOrExpiredToken** (token missing or wrong):
```json
{"status": "error", "message": "InvalidOrExpiredToken", "success": false}
```

**429 Cooldown** (~13 min per target):
```json
{
  "status": "error",
  "message": "Please wait. You can use this service for 'tadgaming0798' again in approximately 12 minute(s) and 40 second(s).",
  "additional_offers": [
    {
      "type": "external_service",
      "icon_svg": "<svg..."
    }
  ]
}
```

**400 Failed to fetch** (video doesn't exist or private):
```json
{"error": "Failed to fetch video details after multiple attempts.", "token": "...", "success": false}
```

## Frontend Config (inline in HTML)
```javascript
const config = {
    processApiType: "video_views",
    formApiType: "videoDetails",
    recaptchaEnabled: false,  // CURRENTLY DISABLED
    recaptchaSiteKey: '6Lc6bT4rAAAAAIq5n21JThEIbULSv73FcTr-V2mf',
    baseUrl: 'https://tikfollowers.com/',
    initialProgressBarDuration: AppUtils.randint(8, 11),  // FAKE delay
    processWaitTimeSeconds: AppUtils.randint(13, 20),      // FAKE delay
};
```

## Process Flow (from frontend JS)
```javascript
async function handleProcess() {
    state.isProcessActive = true;
    // Show "Click OK to continue" modal
    Swal.fire({title: 'Process Starting', text: 'Stay on this page...'});
    // Wait fake timer (13-20s)
    await new Promise(r => setTimeout(r, config.processWaitTimeSeconds * 1000));
    // Call API
    const payload = { ...state.globalData, type: config.processApiType };
    const result = await fetchAPI('api/process', payload);
    // Show result
    Swal.fire({title: result.message});
}
```

## Key Observations
1. **No geo/country parameter** — cannot target Vietnamese views
2. **Backend uses tikapis.com** — tikfollowers.com never contacts TikTok directly
3. **reCAPTCHA disabled** — pure API calls work without browser
4. **~832 views per cycle** — consistent across tests
5. **Token is per-search** — each search generates unique token, expires quickly
6. **Video ID only** — search accepts just the numeric ID, not full URL
