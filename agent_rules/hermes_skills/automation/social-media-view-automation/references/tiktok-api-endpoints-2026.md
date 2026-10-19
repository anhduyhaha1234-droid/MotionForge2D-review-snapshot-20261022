# TikTok API Endpoints & Tracking (tested 2026-07-23)

## View Tracking Endpoint
```
POST https://mcs-sg.tiktokv.com/v1/list
Content-Type: application/json; charset=UTF-8
Origin: https://www.tiktok.com
Referer: https://www.tiktok.com/
```

### video_play Event Payload Structure
```json
[{
  "events": [{
    "event": "video_play",
    "params": "{\"page_name\":\"video_detail\",\"enter_from\":\"video_detail\",\"time_from_origin\":1704,\"is_landing_page\":1,\"page_url\":\"https://www.tiktok.com/@user/video/ID\",\"userAgent\":\"...\",\"domain_name\":\"www.tiktok.com\",\"page_path\":\"/@user/video/ID\",\"vidab\":\"...\"}"
  }]
}]
```

### Status Codes
- `{"e":0,"sc":1,"tc":1}` — Success (first play from browser)
- `{"e":0,"sc":4,"tc":4}` — Invalid fingerprint (modified device_id)
- `{"e":0,"sc":9,"tc":9}` — Duplicate (same event replayed)

## Other Tracked Events (from mcs-sg.tiktokv.com/v1/list)
- `__bav_page` — page view
- `predefine_pageview` — page view with title/URL
- `video_request` — video data requested
- `video_content_show` — video content rendered
- `request_device_score_time` — device performance
- `cookie_banner_load` / `cookie_banner_cdn_load` — consent
- `consent_init_sdk` — privacy consent
- `login_notify_close` — login prompt dismissed

## Video CDN URL Extraction
From page source, look for:
```
"playAddr":"https:\\u002F\\u002Fv16-webapp-prime.tiktok.com\\u002Fvideo\\u002Ftos..."
```
CDN URLs are obfuscated with `\u002F` encoding. CDN returns 403 on direct fetch.

## AB Test Config
```
POST https://libraweb-sg.tiktok.com/service/2/abtest_config/
```
Sends device info, user_unique_id, app_id=1988

## Web ID Generation
```
POST https://mcs-sg.tiktokv.com/v1/user/webid
```
Multiple calls with different app_id values (1988, 548444, 345918)

## SDK/Resource Fetch
```
GET https://mssdk-sg.tiktok.com/web/resource?eq=...
POST https://mssdk-sg.tiktok.com/web/report?X-Dynosaur=...
```

## Web API (read-only, works without auth)
```
GET https://www.tiktok.com/api/item/detail/?itemId={video_id}
GET https://www.tiktok.com/oembed?url={video_url}
GET https://www.tiktok.com/api/related/item_list/?CategoryType=120&...
```

## Monitor/Analytics
```
POST https://mon.tiktokv.com/monitor_browser/collect/batch/?bid=tiktok_webapp
POST https://mon-sg.tiktokv.com/monitor_browser/collect/batch/?biz_id=tiktok_webapp
GET  https://mon.tiktokv.com/monitor_web/settings/browser-settings?bid=tiktok_webapp
```

## TikTok Internal API Domains (ALL PATCHED - 403)
```
api22-core-c-useast1a.tiktokv.com
api19-core-c-useast1a.tiktokv.com
api16-core-c-useast1a.tiktokv.com
api21-core-c-useast1a.tiktokv.com
api-h2.tiktokv.com
api.tiktokv.com
```
Previously used for: `POST /aweme/v1/aweme/stats/` with `item_id={id}&play_delta=1`

## oembed Response Example
```json
{
  "version": "1.0",
  "type": "video",
  "title": "...",
  "author_url": "https://www.tiktok.com/@user",
  "author_name": "...",
  "html": "<blockquote class=\"tiktok-embed\"..."
}
```
