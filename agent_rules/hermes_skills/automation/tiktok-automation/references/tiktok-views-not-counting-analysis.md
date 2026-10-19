# WHY TikTok /aweme/v1/aweme/stats Returns status_code=0 But Views Don't Count

## Root Cause

**status_code=0 means "request format accepted" NOT "view was counted."**

TikTok's architecture uses an async pipeline:

```
1. API Gateway validates request format + signing → returns status_code=0 immediately
2. Async: view event goes to analytics/counting pipeline
3. Counting service validates: registered device? valid session? dedup? rate limit?
4. If ANY check fails → view silently dropped (no error returned to client)
```

This explains ALL observed behavior:
- Same device + same IP → eventually +1 view (dedup eventually allows 1)
- Random device + proxy → 0 views (unregistered devices silently rejected)
- Same device + different IP → 0 views (device session doesn't match new IP)

## Evidence from GitHub Repos

### xtekky/TikTok-View-Bot (★1848) — PATCHED since Oct 2022
- README: "patched !! buy a fast unpatched viewbot here"
- Requires REAL device_id captured from real TikTok install via MITM
- NO signing (old v0404 method)
- Closed issues #4 "views is patched", #5 "This script Work not"

### Wizz1337/TikTokMassBotting (★586) — ADMITS views don't count
- Source code contains: `print("Hits are not counted")`
- Uses aid=1988 (TikTok Web), no signing, no device_register
- Random device IDs per request

### code-root/tiktok-android-signing-toolkit (★28) — Our toolkit
- device_register.py: Full implementation with multiple wire formats
- flow.py: Correct flow = register → warmup → login → API calls
- feed_api_client.py: Shows COMPLETE required header set
- device_guard.py: ECDSA P-256 guard header builder

## What TikTok Validates (from MITM analysis + toolkit source)

### Layer 1: Device Registration (REQUIRED)
POST /service/2/device_register/ → returns real device_id + install_id
Must pass emulator detection (TLS fingerprint, hardware props, telemetry history)

### Layer 2: Session Cookies (REQUIRED)
After registration, warm-up via GET /get_domains/v5/ → acquires:
- msToken (session token)
- store-country-sign
- install_id, odin_tt, ttreq (device token hash)
- store-idc, tt-target-idc (data center routing)

### Layer 3: Complete Header Set (REQUIRED)
From H2 HPACK capture of real TikTok v44.3.1:
```
X-Argus, X-Gorgon, X-Khronos, X-Ladon  (signing engine)
X-SS-STUB                                (MD5 of body)
x-tt-dm-status: login=0;ct=1;rt=6
sdk-version: 2
passport-sdk-version: 1
oec-cs-sdk-version: v10.02.02.01-bugfix-ov-android_V31
x-vc-bdturing-sdk-version: 2.4.1.i18n
oec-vc-sdk-version: 3.2.1.i18n
rpc-persist-pns-region-1/2/3: US|6252001
x-tt-request-tag: n=0;nr=011;bg=0;rs=100;s=-1;p=0
x-tt-store-region, x-tt-store-region-src: did
x-tt-ttnet-origin-host: api16-core-useast5.tiktokv.us
x-ss-dp: 1233
x-common-params-v2: <url-encoded all device params>
x-tt-trace-id: 00-<hex>...-01
```

### Layer 4: Device Guard Headers (REQUIRED for registered devices)
```
tt-ticket-guard-version: 3
tt-ticket-guard-public-key: <EC P-256 uncompressed point base64>
tt-device-guard-iteration-version: 1
tt-device-guard-client-data: <base64 JSON with ECDSA P-256 signatures>
```
Uses ECDSA P-256 signing with device's private key from registration.
Cannot be faked without the key pair.

### Layer 5: View Deduplication (server-side)
- device_id: same device can't count multiple views quickly
- IP address: same IP + different device_id = heavily rate-limited
- Time window: ~5-10 min cooldown per device per video
- Behavioral signals: watch duration, engagement patterns

## Correct Flow (from flow.py)
1. POST /service/2/device_register/ → get real device_id + install_id
2. GET /get_domains/v5/ → warm-up, get msToken + session cookies
3. (Optional) Login with credentials
4. POST /aweme/v1/aweme/stats?play_delta=1 → VIEW COUNTS (with valid device)

## tikfollowers.com/tikapis.com Status (2026-07)
- tikfollowers.com frontend: ALIVE, returns "success" regardless
- tikapis.com backend: DOWN (HTTP 500, api-v4 DNS fails)
- Flow: user → tikfollowers → tikapis → TikTok — broken at step 3
- tikfollowers "success" is a LIE when backend is down

## Alternative View Counting Methods

### CDN/embed/WebView
- TikTok CDN loads do NOT count as views
- iframe embed player MAY generate telemetry but no confirmed counter increment
- WebView loads MAY count IF proper telemetry is sent with registered device
- No documented guarantee for any non-app view method

### log.tiktokv.com telemetry
- Receives telemetry but "receiving is distinct from trusting and counting"
- Not a public view-increment API
- TikTok's internal pipeline decides which events to trust

## SMM Panel Infrastructure (how real view services work)
1. **API-based**: mass device_register + signing engine (cheap, detected quickly)
2. **Device farm**: rooted phones/emulators with real TikTok app (quality)
3. **Web player bots**: headless browsers on tiktok.com (cheaper, higher detection)
4. **Reseller chain**: most panels buy from upstream at $0.20-0.50/1K views
