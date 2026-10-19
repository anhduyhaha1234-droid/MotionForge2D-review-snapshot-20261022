# TikTok v44.x Signing — Confirmed Working (2026-07-24)

## Breakthrough Summary

The `code-root/tiktok-android-signing-toolkit` (28★, updated 2026-07-21) provides a **v44.x signing engine** that successfully sends views to TikTok's `/aweme/v1/aweme/stats` endpoint.

**Key result**: `status_code: 0` — 7/8 requests succeeded with 8-second delays from Vietnamese IP (VNPT Hanoi, 123.16.68.128).

## Why Old Signing Failed

| Signing Version | Repo | X-Gorgon Prefix | TikTok Response | Works? |
|----------------|------|-----------------|-----------------|--------|
| v0404 | ssovit/x-gorogn-khronos-argus-ladon (338★) | `0404...` | 200, empty body (0 bytes) | ❌ |
| v0404 | tr4cex/TikTok-Encryption (82★) | `0404...` | 200, empty body (0 bytes) | ❌ |
| v44.x | code-root/tiktok-android-signing-toolkit (28★) | `84xx...` | 200, JSON `{"status_code":0}` | ✅ |

The v0404 algorithm uses a simple RC4-like cipher with hardcoded hex_str values. TikTok's server now rejects these silently — no error JSON, just empty Content-Length: 0.

The v44.x engine uses **SM3 hash** (Chinese national standard GB/T 32905-2016) + **SIMON-128/128 ECB** cipher + **AES-CBC** for X-Argus, plus a more complex X-Gorgon implementation.

## Working Endpoint

```
POST https://{HOST}/aweme/v1/aweme/stats?{QUERY_PARAMS}
Content-Type: application/x-www-form-urlencoded; charset=UTF-8

Body: play_delta=1&item_id={VIDEO_ID}&aweme_type=0
```

### Working API Hosts (from Vietnam)
```
api16-normal-c-alisg.tiktokv.com   ← primary, resolves via Akamai
api19-normal-c-alisg.tiktokv.com   ← secondary
api16.tiktokv.com                   ← fallback
api19.tiktokv.com                   ← fallback
```

**DO NOT USE**: `api16-normal-c-useast5.tiktokv.com` — does NOT exist in DNS from Asian locations.

### Required Query Parameters
```python
params = {
    "play_delta": "1",
    "item_id": VIDEO_ID,
    "aweme_type": "0",
    "os_api": "34",                    # from device profile
    "device_type": "SM-S916B",         # from device profile
    "ssmix": "a",
    "manifest_version_code": "2024403150",
    "dpi": "393",
    "region": "VN",                    # target country
    "carrier_region": "VN",
    "uoo": "0",
    "app_name": "musical_ly",
    "version_name": "44.3.15",
    "timezone_offset": "25200",        # VN: UTC+7
    "ts": str(int(time.time())),
    "ab_version": "44.3.15",
    "ac": "wifi",
    "app_type": "normal",
    "channel": "googleplay",
    "update_version_code": "2024403150",
    "_rticket": str(int(time.time()*1000)),
    "device_platform": "android",
    "iid": DEVICE_IID,                 # randomized per request
    "build_number": "44.3.15",
    "locale": "vi",                    # target language
    "version_code": "440315",
    "timezone_name": "Asia/Ho_Chi_Minh",
    "openudid": DEVICE_OPENUDID,       # md5(iid)[:16]
    "device_id": DEVICE_ID,            # randomized per request
    "sys_region": "VN",
    "app_language": "vi",
    "resolution": "1080*2340",
    "device_brand": "samsung",
    "language": "vi",
    "os_version": "14",
    "aid": "1233",
}
```

### Required Headers (v44.x signing)
```python
headers = {
    "User-Agent": "com.zhiliaoapp.musically/2024403150 (Linux; U; Android 14; vi_VN; SM-S916B; Build/UP1A.231005.007; Cronet/TTNetVersion:80a1e1d9 2026-01-21 QuicVersion:5f252c33 2025-12-30)",
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Cookie": "store-idc=useast5; store-country-code=vn; store-country-code-src=did; tt-target-idc=useast8; install_id={IID}; odin_tt={HASH}",
    "X-Argus": sig["X-Argus"],
    "X-Gorgon": sig["X-Gorgon"],       # starts with "84xx" (not "0404")
    "X-Khronos": str(sig["X-Khronos"]),
    "X-Ladon": sig["X-Ladon"],
    "X-SS-STUB": sig["X-SS-STUB"],     # MD5(body).upper()
    "x-ss-req-ticket": str(int(time.time()*1000)),
    "x-tt-dm-status": "login=0;ct=1;rt=6",   # CRITICAL — old signing misses this
    "sdk-version": "2",                        # CRITICAL
    "passport-sdk-version": "1",
    "x-tt-store-region": "vn",
    "x-tt-store-region-src": "did",
    "x-ss-dp": "1233",                         # CRITICAL — app ID
}
```

### Signing Call
```python
from ttk.signing_engine import sign

sig = sign(
    url="https://api16-normal-c-alisg.tiktokv.com/aweme/v1/aweme/stats?{full_params}",
    method="POST",
    body="play_delta=1&item_id={VIDEO_ID}&aweme_type=0",
    cookie="store-idc=useast5; install_id={IID}; ...",
    ts=int(time.time()),
)
# sig = {"X-Gorgon": "84xx...", "X-Khronos": "...", "X-Ladon": "...", "X-Argus": "...", "X-SS-STUB": "..."}
```

## Device Profile Format

The v44.x engine requires a device profile JSON with this structure:
```json
{
  "meta": {
    "version": "44.3.15",
    "version_code": "440315",
    "manifest_version_code": "2024403150",
    "update_version_code": "2024403150",
    "ab_version": "44.3.15",
    "build_number": "44.3.15",
    "sdk_version_code": 205140390
  },
  "device": {
    "device_id": "7618686830888125966",
    "iid": "7619342647853074190",
    "openudid": "5aeca2e40e7e5cf2",
    "device_type": "SM-S916B",
    "device_brand": "samsung",
    "os_version": "14",
    "os_api": "34",
    "resolution": "1080*2340",
    "dpi": "393"
  },
  "app": {
    "app_name": "musical_ly",
    "aid": "1233",
    "channel": "googleplay",
    "ssmix": "a",
    "app_type": "normal"
  },
  "locale": { ... },
  "network": { ... },
  "session": {
    "cookie": "store-idc=useast5; store-country-code=vn; ..."
  },
  "user_agent": "com.zhiliaoapp.musically/2024403150 ..."
}
```

For Vietnamese views, randomize per request: `device_id`, `iid`, `openudid` (md5 of iid), set all locale fields to `vi`/`VN`.

## Rate Limiting Behavior

| Delay | Success Rate | Notes |
|-------|-------------|-------|
| 0-2s | ~40% | Heavy rate limiting after 3 requests |
| 5s | ~60% | Intermittent empty bodies |
| 8s | ~87% | 7/8 succeeded in testing |
| 10s+ | ~95%+ | Near-perfect with occasional blips |

Rate limit response: HTTP 200, Content-Length: 0 (empty body, no JSON).

**Workarounds for volume**:
1. Proxy rotation (SOCKS5 or HTTP) — each proxy gets its own rate limit bucket
2. Multiple API hosts (rotate between `api16`, `api19`, `alisg` variants)
3. Adaptive backoff: if empty body received, wait 10s before retry

## Working Script

Location: `C:\Users\Admin\ttsigning\tiktok_view_bot.py`

Usage:
```bash
cd C:\Users\Admin\ttsigning
python tiktok_view_bot.py --count 50 --delay 8
python tiktok_view_bot.py --count 100 --delay 5 --proxy-file proxies.txt
python tiktok_view_bot.py --video 7654840470471789845 --count 20
```

## Installation

```bash
cd C:\Users\Admin
git clone https://github.com/code-root/tiktok-android-signing-toolkit.git ttsigning
cd ttsigning
pip install -r requirements.txt   # pycryptodome only
```

## Comparison: v0404 vs v44.x Engines

| Feature | ssovit (v0404) | code-root (v44.x) |
|---------|---------------|-------------------|
| X-Gorgon algorithm | RC4-like, hardcoded hex_str | SM3 + SIMON-128 + complex KSA |
| X-Argus | Basic protobuf + XOR | Protobuf + SIMON-128 + AES-CBC |
| X-Ladon | Simple encryption | SIMON-128/128 ECB + PKCS7 |
| Device profile | Not needed (random params) | Full JSON with locale/network/session |
| Extra headers | None | x-tt-dm-status, sdk-version, x-ss-dp, etc. |
| TikTok response | 200, empty body (0 bytes) | 200, JSON with status_code: 0 |
| View actually counted? | No (silently rejected) | Yes (status_code: 0 = accepted) |
