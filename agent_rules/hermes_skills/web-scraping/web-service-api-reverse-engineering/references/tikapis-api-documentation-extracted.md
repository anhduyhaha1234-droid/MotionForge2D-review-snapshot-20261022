# tikapis.com API Documentation (Extracted 2026-07-23)

## Overview
- **Base URL:** `https://tikapis.com/api/` (NOT `api-v4.tikapis.com` — that subdomain doesn't resolve in DNS)
- **Auth:** `x-api-key: <UUID>` header (e.g., `b6b12336-bfef-4be1-8112-72ba8e878d6b`)
- **Platform headers:** `X-Platform: android|ios`, `X-App-Aid: 1233`
- **Status (2026-07-23):** HTTP 500 "Service temporarily unavailable" on ALL endpoints (backend down)

## All Discovered Endpoints

### Device Registration
```
POST /api/device_register
Headers: x-api-key, X-Platform, X-App-Aid
Body: {full device config JSON (see below)}
```

### Manipulation Endpoints (8 total)
```
POST /api/video/stats/{aweme_id}         — Views video by ID
POST /api/video/like/{aweme_id}          — Like video by ID
POST /api/video/unlike/{aweme_id}        — Dislike video by ID
POST /api/story/like/{story_id}          — Story Like by ID
POST /api/story/unlike/{story_id}        — Dislike Story by ID
POST /api/save/{aweme_id}                — Save video by ID
POST /api/user/follow/{uid}/{sec_uid}    — Follow user by ID
POST /api/user/unfollow/{uid}/{sec_uid}  — Unfollow user by ID
```

### User Endpoints
```
GET/POST /api/user/self                  — Get logged in user info
GET/POST /api/user/profile               — User profile
GET/POST /api/user/posts                 — User posts
GET/POST /api/user/followers/{uid}       — User followers list
GET/POST /api/user/followings/{uid}      — User following list
```

### Video Endpoints
```
POST /api/post/muilt_aweme_details       — Multi video details
GET/POST /api/post/comments/{aweme_id}   — Comments by video ID
```

### Comment Endpoints
```
POST /api/comment/publish/{aweme_id}     — Publish comment
POST /api/comment/like/{aweme_id}/{cid}  — Like comment
POST /api/comment/unlike/{aweme_id}/{cid}— Unlike comment
POST /api/comment/delete/{cid}           — Delete comment
```

### Account Management
```
POST /api/user/edit-biography
POST /api/user/edit-nickname
POST /api/user/edit-username
POST /api/user/change-your-profile-picture
POST /api/passport/reset-by-email-password
POST /api/passport/reset-password-email
```

### Authentication
```
POST /api/passport/login
POST /api/passport/mobile/login
POST /api/passport/mobile/login/check_code
POST /api/passport/email/signup
POST /api/passport/email/signup/check_code
POST /api/passport/mobile/signup
POST /api/passport/mobile/signup/check_code
POST /api/passport/register
POST /api/passport/token/beat            — Token heartbeat/refresh
POST /api/passport/im/reboot/misc
```

### Algorithm/Signing Endpoints
```
POST /api/algorithm/mssdk_encrypt
POST /api/algorithm/mssdk_decrypt
POST /api/algorithm/tt/encrypt
POST /api/algorithm/tt/decrypt
POST /api/algorithm/x-argus/encrypt
POST /api/algorithm/x-argus/decrypt
POST /api/algorithm/x-ladon/encrypt
POST /api/algorithm/x-ladon/decrypt
POST /api/algorithm/x-cylons/encrypt
POST /api/algorithm/x-cylons/decrypt
POST /api/algorithm/sign
```

### Captcha
```
POST /api/tiktok/captcha/solver
```

### Signature
```
POST /api/algorithm/sign (iOS/Android signature generation)
```

## Views Endpoint — Full Request Body

```json
POST /api/video/stats/{aweme_id}
Headers:
  Content-Type: application/json
  X-Platform: android
  X-App-Aid: 1233
  x-api-key: <API_KEY>

Body:
{
  "app_info": {
    "aid": 1233,
    "app_name": "musical_ly",
    "app_version": "38.4.3",
    "channel": "googleplay",
    "client_mode": 2,
    "client_type": "inhouse",
    "cronet_version": "8f366453_2024-12-24",
    "display_name": "TikTok",
    "git_hash": "80e94eb",
    "manifest_version_code": "2023804030",
    "package_name": "com.zhiliaoapp.musically",
    "passport-sdk-version": "6032090",
    "platform": "android",
    "quic_version": "ef6c341e_2024-11-14",
    "random_bytes": 2181161062,
    "release_build": "3cfedea_20250123_8050547273",
    "sdk_target_version": 29,
    "ttnet_version": "4.2.210.9-tiktok",
    "update_version_code": "2023804030",
    "version_code": "380403",
    "x-vc-bdturing-sdk-version": "2.3.8.i18n",
    "h5_sdk_version": "2.33.9",
    "captcha_sdk_version": "3.10.3-tiktok.4.1"
  },
  "cookie": "store-idc=alisg; store-country-code=<CC>; install_id=<IID>; ttreq=1$<hash>",
  "country_location": {
    "carrier_region_v2": "<MCC>",
    "gmt": "GMT+<offset>",
    "lang_b": "<COUNTRY_CODE>",
    "lang_k": "<LANGUAGE>",
    "mcc_mnc": "<MCC_MNC>",
    "operator": "<CARRIER_NAME>",
    "timezone": <OFFSET_INT>,
    "tz_name": "<TIMEZONE>",
    "tz_offset": <OFFSET_SECONDS>
  },
  "device": {
    "UAinfo": {
      "UA1": "Mozilla/5.0 (Linux; Android <VER>; <MODEL> Build/<BUILD>; wv) ...",
      "UA2": "Mozilla/5.0 (Linux; Android <VER>; <MODEL> Build/<BUILD>; wv) ...",
      "UA3": "Dalvik/2.1.0 (Linux; U; Android <VER>; <MODEL> Build/<BUILD>)"
    },
    "app_alert_check": "{\"message\":\"success\"}",
    "battery_capacity": <mAh>,
    "battery_percentage": "<percent>",
    "build.board": "<board>",
    "build.bootloader": "<bootloader>",
    "build.display": "<display>",
    "build.fingerprint": "<fingerprint>",
    "build.hardware": "<hardware>",
    "build.host": "<host>",
    "build.id": "<build_id>",
    "build.manufacturer": "<manufacturer>",
    "build.model": "<MODEL>",
    "build.product": "<product>",
    "build.tags": "<tags>",
    "build.type": "<type>",
    "density_dpi": <dpi>,
    "device_type": "<type>",
    "resolution": "<WxH>"
  },
  "domain_selection": {},
  "mssdk_parameters": {
    "sdk_ver": "v05.01.06-alpha.11-ov-android"
  },
  "network_data": {},
  "proto_data": {
    "signCount": <N>,
    "reportCount": <N>,
    "settingCount": <N>,
    "reportFailCount": <N>
  },
  "proxy": "<user>:<pass>@<host>:<port>",
  "user": {},
  "x_token": ""
}
```

## Vietnam Device Configuration Template

```json
{
  "country_location": {
    "carrier_region_v2": "452",
    "gmt": "GMT+07:00",
    "lang_b": "VN",
    "lang_k": "vi",
    "mcc_mnc": "45201",
    "operator": "Viettel",
    "timezone": 7,
    "tz_name": "Asia/Ho_Chi_Minh",
    "tz_offset": 25200
  },
  "cookie": "store-idc=sg1; store-country-code=vn; install_id=<GENERATED>",
  "proxy": "<VN_SOCKS5_USER>:<PASS>@<HOST>:<PORT>"
}
```

**Vietnam MCC codes:**
| MCC_MNC | Carrier |
|---------|---------|
| 45201 | Viettel |
| 45202 | Mobifone |
| 45204 | Viettel (alt) |
| 45205 | Vietnamobile |
| 45206 | Vinaphone |
| 45207 | Gmobile |

## Service Tiers

| Tier | Platform | Apps | Price | Daily | Weekly | Monthly | Rate/min |
|------|----------|------|-------|-------|--------|---------|----------|
| Free iOS | iOS | 7 | $0/mo | 200 | 1,400 | 6,000 | 15 |
| Free Android | Android | 19 | $0/mo | 1,000 | 5,000 | 15,000 | 25 |
| Captcha | Captcha | — | Basic | — | — | — | — |
| Premium | All | — | $120/mo | — | — | — | — |

## Response Format (Success)
```json
{
  "extra": {"now": 1740629121000},
  "log_pb": {"impr_id": "2023092609190655D392609190E1E"},
  "status_code": 0
}
```

## Response Format (Error)
```json
{"error": "Service temporarily unavailable"}  // HTTP 500
{"error": "API key is missing"}               // HTTP 401 (no key)
{"error": "Invalid API key"}                  // HTTP 401 (wrong key)
{"error": "X-App-Aid is required"}            // HTTP 400 (missing header)
```

## DNS Verification Results (2026-07-23)
| Domain | Status | Notes |
|--------|--------|-------|
| tikapis.com | Resolves (IPv6: 2001:ee0:23::23) | Main domain, serves web + /api/ |
| api-v3.tikapis.com | Resolves (IPv6 only) | Same IP as main |
| api-v4.tikapis.com | **DOES NOT RESOLVE** | Docs reference this but it doesn't exist |
| api.tikapis.com | Does not resolve | — |
| api-v1.tikapis.com | Does not resolve | — |
| api-v2.tikapis.com | Does not resolve | — |

## Key Contacts
- Telegram: @tikapiscom (channel), @tikapiscom_group (group)
- Email: [email protected] (Cloudflare-protected)
