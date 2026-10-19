# TikTok X-Gorgon API Test Results (2026-07-24)

## Test Setup
- **Repo used**: ssovit/x-gorogn-khronos-argus-ladon (338★)
- **Server**: FastAPI on localhost:8100 (`uvicorn main:app --port 8100`)
- **Endpoints**: POST /x-gorgon (generates X-Gorgon + X-Khronos headers)
- **Video tested**: 7547761978786319624 (@tadgaming0798, baseline: 3624 views)

## Test 1: Basic X-Gorgon (minimal params)
```
Params: device_platform=android&aid=1233&version_code=340002
Headers: {cookie: "sessionid=test", x-ss-stub: "d41d8cd98f00b204e9800998ecf8427e"}

Result: X-Gorgon generated ✅
TikTok response: 200 (empty body)
View change: 0 ❌
```

## Test 2: Full params with as=a1iosdfgh bypass
```
Params (xtekky format):
  app_language=vi&iid={random_19_digits}&device_id={random_19_digits}
  &channel=googleplay&device_type=SM-G9900&ac=wifi&os_version=11
  &version_code=322&app_name=trill&device_brand=samsung&ssmix=a
  &device_platform=android&aid=1180&as=a1iosdfgh&cp=androide1

POST body:
  &manifest_version_code=322&update_version_code=3220
  &play_delta=1&item_id=7547761978786319624&version_code=322&aweme_type=0

Hosts tested: api16.tiktokv.com, api.tiktokv.com, api19.tiktokv.com

Result:
  - X-Gorgon generated ✅
  - TikTok response: 200 ✅
  - Response body: {"extra":{"now":...},"log_pb":{"impr_id":"..."},"status_code": 0} ✅
  - View change: 0 ❌ (tested 30 attempts)
```

## Test 3: Status code analysis
```
status_code: 0 = "accepted" but view NOT counted
Empty body = same as status_code: 0, request accepted but no effect
200 with status_code: 0 everywhere = endpoint PATCHED server-side
```

## Why It Doesn't Work
TikTok's server-side validation now requires:
1. **Registered device** — IID/DID must come from actual `device_register` API call, not random values
2. **Valid session** — `sessionid=test` is rejected silently (no 403, just ignored)
3. **Device fingerprint match** — X-Gorgon must match the device's actual fingerprint

The `as=a1iosdfgh` bypass (credit: @auut) used to skip X-Gorgon signing entirely, but TikTok has since added server-side validation that checks whether the device_id was actually registered.

## What Would Work
To send views via this endpoint, you need:
1. Call `device_template` → get device config
2. Call `device_register` → get real device_id + install_id
3. Call `get_token` → get MSSDK token
4. Call `get_seed` → get MSSDK seed
5. Login with TikTok account → get sessionid
6. Generate X-Gorgon with all the above
7. Send to `/aweme/v1/aweme/stats`

This is exactly what tikapis.com automates — but their backend is currently down.

## tikapis.com API Investigation

### Status (2026-07-24)
- **API Key**: Works (tested with provided key)
- **Endpoints that EXIST**: `/api/video`, `/api/user` (return 400 without X-App-Aid header)
- **With proper headers**: 500 "Service temporarily unavailable"
- **Root cause**: `api-v4.tikapis.com` DNS does NOT exist (nslookup: "Non-existent domain")
- **tikapis.com proxies** /api/* to api-v4 → api-v4 doesn't resolve → 500
- **RapidAPI**: Page returns 404 (API removed from platform)
- **Registration**: POST /auth/register works (creates account, returns session cookie)
- **Dashboard**: Shows "API Keys (0)" — no way to generate keys from UI
- **Contact**: Telegram @tikapiscom

### Architecture
```
User → tikfollowers.com → tikapis.com/api/video → api-v4.tikapis.com (DEAD)
                                                          ↑
                                              DNS: Non-existent domain
```

### Available on tikapis.com (when working)
```
POST /device_register       — Register Android device
POST /passport/login        — Login TikTok account
POST /video/stats/{id}      — Send views
POST /user/follow/{id}      — Follow user
POST /video/like/{id}       — Like video
POST /comment/publish/{id}  — Post comment
+ X-Argus, X-Ladon, X-Gorgon encryption endpoints
```

### Pricing (from docs)
- Free tier: $0/month, 1000 requests/day (Android), 200/day (iOS)
- Captcha Basic: $120/month
- Also on RapidAPI (currently removed)

## Recommendation
The only currently working path for automated TikTok views is **tikfollowers.com** (which somehow still works despite tikapis.com being down — likely has cached tokens or alternative backend). For Vietnamese views specifically, there is no working automated method as of 2026-07-24.
