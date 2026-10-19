# TikTok Additional API Endpoints & Toolkit Modules (2026-07-24)

## Feed API Endpoint: `/aweme/v2/feed/`

Discovered in `code-root/tiktok-android-signing-toolkit/ttk/feed_api_client.py`.

**This endpoint returns actual video feed data** (protobuf-encoded). Each video in the feed response is an "impression" — whether this counts as a view is unclear but worth testing.

```
POST https://api16-core-useast5.tiktokv.us/aweme/v2/feed/?{query_params}
Content-Type: application/json
Content-Encoding: gzip
```

### Query Parameters
```python
{
    "os": "android",
    "_rticket": "<unix_ms>",
    "is_pad": "0",
    "last_install_time": "<unix_ts>",
    "host_abi": "arm64-v8a",
    "ts": "<unix_ts>",
    "effect_sdk_version": "21.0.0",
    "req_from": "enter_auto",
    "pull_type": "0",
    "app_version": "<update_version_code>",
    "is_non_personalized": "0",
}
```

### Body (gzip-compressed JSON)
```json
{"count":6,"cursor":0,"type":0,"is_cold_start":1}
```

### Response Format
- **Protobuf wire format** (NOT JSON) — requires protobuf decoder
- Field 1: status_code
- Field 4: has_more
- Field 5: array of video items
- Each video item has: field 1 (id), field 2 (desc), field 4 (author info)

### Complete Header Set (from H2 HPACK capture of real TikTok v44.3.1)
The feed client uses a MUCH richer header set than the stats endpoint:

```python
headers = {
    # Standard
    'User-Agent': '<profile_user_agent>',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cookie': '<session_cookie>',

    # Security signatures (same as stats)
    'X-Argus': sig['X-Argus'],
    'X-Gorgon': sig['X-Gorgon'],
    'X-Khronos': str(sig['X-Khronos']),
    'X-Ladon': sig['X-Ladon'],

    # Required TikTok headers (discovered via H2 HPACK decoding)
    'x-tt-pba-enable': '1',                          # NEW — not in stats endpoint
    'x-tt-dm-status': 'login=0;ct=1;rt=6',
    'X-SS-REQ-TICKET': str(rticket),
    'sdk-version': '2',
    'passport-sdk-version': '1',
    'oec-cs-si-a': '2',                              # NEW — SDK integrity check
    'oec-cs-sdk-version': 'v10.02.02.01-bugfix-ov-android_V31',  # NEW
    'x-vc-bdturing-sdk-version': '2.4.1.i18n',       # NEW — Turing verification SDK
    'oec-vc-sdk-version': '3.2.1.i18n',              # NEW
    'rpc-persist-pns-region-1': 'US|6252001',         # NEW — geolocation pins
    'rpc-persist-pns-region-2': 'US|6252001',
    'rpc-persist-pns-region-3': 'US|6252001',
    'x-tt-request-tag': 'n=0;nr=011;bg=0;rs=100;s=-1;p=0',  # NEW — request routing tag
    'x-tt-store-region': '<region>',
    'x-tt-store-region-src': 'did',
    'rpc-persist-pyxis-policy-state-law-is-ca': '0',  # NEW — California law compliance
    'rpc-persist-pyxis-policy-v-tnc': '1',            # NEW — T&C acceptance
    'x-tt-ttnet-origin-host': 'api16-core-useast5.tiktokv.us',  # NEW
    'x-ss-dp': '<app_aid>',
    'x-common-params-v2': '<url_encoded_common_params>',  # NEW — mega header
    'x-tt-trace-id': '00-<hex_ts>1069b5d83f35b0060ea904d1-<hex_ts>1069b5d8-01',
}
```

### `x-common-params-v2` Header Format
This is a URL-encoded mega-header containing ALL device/app/locale params:
```
ab_version=44.3.15&ac=wifi&ac2=unknown&aid=1233&app_language=vi&
app_name=musical_ly&app_type=normal&build_number=44.3.15&
carrier_region=VN&carrier_region_v2=452&channel=googleplay&
current_region=VN&device_brand=samsung&device_id=7618...&
device_platform=android&device_type=SM-S916B&dpi=393&
iid=7619...&language=vi&locale=vi&manifest_version_code=2024403150&
mcc_mnc=45201&op_region=VN&os_api=34&os_version=14&region=VN&
residence=VN&resolution=1080*2340&ssmix=a&sys_region=VN&
timezone_name=Asia/Ho_Chi_Minh&timezone_offset=25200&uoo=0&
update_version_code=2024403150&version_code=440315&version_name=44.3.15
```

## Device Registration: `/service/2/device_register/`

Discovered in `code-root/tiktok-android-signing-toolkit/ttk/device_register.py`.

### Registration Hosts (8 endpoints, tried in order)
```python
_HOSTS = [
    "log-va.tiktokv.com",        # Primary (Virginia)
    "api.tiktokv.com",           # Generic
    "log.byteoversea.com",       # ByteDance overseas
    "log15.byteoversea.com",     # Regional variant
    "log.isnssdk.com",           # SDK domain
    "log.sgsnssdk.com",          # Singapore SDK
    "log2.musical.ly",           # Legacy domain
    "log.snssdk.com",            # China SDK (works for overseas too)
]
```

### Wire Formats (4 variants, tried in order)
1. **`java`** — `Content-Type: application/octet-stream;tt-data=b` + gzip body. Sign **uncompressed** JSON.
2. **`java_gzip_sig`** — Same wire as java, but sign the **gzip bytes** instead of raw JSON.
3. **`json_gzip`** — `Content-Type: application/json; charset=utf-8` + gzip body.
4. **`json_plain`** — `Content-Type: application/json; charset=utf-8` + raw body.

### Body Format
```json
{
  "magic_tag": "ss_app_log",
  "header": {
    "display_name": "TikTok",
    "update_version_code": "2024403150",
    "manifest_version_code": "2024403150",
    "aid": 1233,
    "channel": "googleplay",
    "os": "Android",
    "os_version": "14",
    "os_api": 34,
    "sdk_version": "2.15.0",
    "sdk_version_code": "2150",
    "sdk_target_version": 29,
    "git_hash": "5ae517f",
    "device_model": "SM-S916B",
    "device_brand": "samsung",
    "device_manufacturer": "samsung",
    "cpu_abi": "arm64-v8a",
    "release_build": "44.3.15",
    "density_dpi": 393,
    "display_density": "xhdpi",
    "resolution": "3120*1440",
    "language": "vi",
    "timezone": 7.0,
    "access": "wifi",
    "package": "com.zhiliaoapp.musically",
    "app_version": "44.3.15",
    "version_code": 440315,
    "openudid": "<16_char_hex>",
    "cdid": "<uuid_v4>",
    "clientudid": "<uuid_v4>",
    "device_id": "0",          // Always 0 for new registration
    "install_id": "0",         // Always 0 for new registration
    "rom_version": "<build_fingerprint>",
    "region": "VN",
    "tz_name": "Asia/Ho_Chi_Minh",
    "tz_offset": 25200,
    "sim_region": "VN",
    "app_language": "vi",
    "sys_language": "vi",
    "sig_hash": "<from_real_apk>",  // CRITICAL — from real APK via MITM
    "new_user_mode": 1
  },
  "_gen_time": 1721836800000,
  "event_filter": 1
}
```

### Key Finding: `sig_hash` is CRITICAL
Without a real `sig_hash` extracted from a TikTok APK (via MITM or jadx), TikTok returns `device_id: 0`. This is the root cause of why direct API view sending doesn't increment playCount — the device was never registered.

**How to extract sig_hash:**
```bash
# From a real TikTok APK via MITM:
# 1. Install TikTok on Android with HTTP Toolkit proxy
# 2. Capture the device_register request
# 3. Extract sig_hash from the JSON body header

# Or from APK file directly:
python3 -m ttk.tiktok_apk_sig /path/to/tiktok.apk
```

## API Hosts: Complete List

### Stats/Feed Hosts (Android mobile API)
```
api16-normal-c-alisg.tiktokv.com   ← Singapore, works from Asia
api19-normal-c-alisg.tiktokv.com   ← Singapore variant
api16.tiktokv.com                   ← Generic
api19.tiktokv.com                   ← Generic
api16-core-useast5.tiktokv.us      ← US East, from toolkit feed client
api21.tiktokv.com                   ← Additional variant
api.tiktokv.com                     ← Generic catch-all
```

### Log/Registration Hosts
```
log-va.tiktokv.com                 ← Virginia, primary for device_register
api.tiktokv.com                    ← Generic
log.byteoversea.com                ← ByteDance overseas
log15.byteoversea.com              ← Regional variant
log.isnssdk.com                    ← SDK
log.sgsnssdk.com                   ← Singapore SDK
log2.musical.ly                    ← Legacy Musical.ly domain
log.snssdk.com                     ← Snack Video SDK domain
```

### Dead/Unreachable Hosts (as of 2026-07)
```
api{16-22}-core-c-useast1a.tiktokv.com  ← All return 403
api-h2.tiktokv.com                       ← 403
api16-normal-c-useast5.tiktokv.com       ← DNS NXDOMAIN from Asia
```

### Web/Monitoring Hosts
```
mcs-sg.tiktokv.com                 ← Event collection (video_play, etc.)
mon.tiktokv.com                    ← Browser monitoring
mon-sg.tiktokv.com                 ← SG monitoring
mssdk-sg.tiktok.com                ← SDK resource/report
libraweb-sg.tiktok.com             ← AB test config
```

## Additional Headers: x-ss-req-ticket Format

The `x-ss-req-ticket` header is a Unix timestamp in **milliseconds** (not seconds):
```python
'x-ss-req-ticket': str(int(time.time() * 1000))  # e.g. "1721836800000"
```

## Trace ID Format
```
x-tt-trace-id: 00-{hex_ts_8chars}1069b5d83f35b0060ea904d1-{hex_ts_8chars}1069b5d8-01
```
Where `hex_ts_8chars` = first 8 hex chars of Unix timestamp.

## Repos Confirmed Dead This Session
- `SebastienWae/tiktok-gorgon-bridge` — 404 (was 104★, Express + Frida bridge)
- `HkerVit/TikTok-Private-API` — 404 (was 50★, full TikTok API wrapper)

## TikTokApi (davidteather) — Read-Only
The popular `davidteather/TikTok-Api` Python library is a **scraping/data-retrieval library only**. It:
- Uses Playwright browser sessions for web rendering
- Extracts data from `SIGI_STATE` JSON in page HTML
- Has no view-sending or engagement-inflation capabilities
- Does NOT implement mobile API signing (X-Gorgon, etc.)
- Useful for: reading video stats, user info, comments — not for view inflation
