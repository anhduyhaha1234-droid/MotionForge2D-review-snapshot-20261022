# TikTok Device Profile Schema Contract

## Purpose

Generated profiles (`generate_profiles.py`) must match the schema consumed by:
- `ttk/feed_api_client.py` → `build_headers()`, `build_common_params()`, `load_profile()`
- `ttk/device_guard.py` → `build_guard_headers()`, `build_device_guard_client_data()`
- `api_framework.py` → `build_stats_url()`, `send_view()`
- `ttk/device_register.py` → `TikTokDeviceRegister.build_profile()`
- `ttk/flow.py` → `warmup_device()`

## Required Top-Level Keys

```json
{
  "meta": {...},
  "device": {...},
  "app": {...},
  "network": {...},
  "locale": {...},
  "user_agent": "...",
  "session": {...},
  "guard_keys": {...},
  "guard_headers": {...},
  "passport_headers": {...}
}
```

## Section Schemas

### meta
```json
{
  "version": "44.3.15",            // TikTok app version
  "version_code": "440315",        // Numeric version code
  "manifest_version_code": "2024403150",  // Manifest code (used in User-Agent)
  "update_version_code": "2024403150",
  "ab_version": "44.3.15",
  "build_number": "44.3.15",
  "sig_hash": "194326e82c84a639a52e5c023116f12a",  // APK signature MD5
  "git_hash": "5ae517f",
  "sdk_version": "2.5.14.3",
  "sdk_version_code": 205140390,
  "rom": "UP1A.231005.007",
  "rom_version": "generic/{model}/{model}:{os}/UP1A.231005.007/...",
  "build_id": "UP1A.231005.007",
  "release_build": "b2a796d_20260312",
  "source_capture": "generate_profiles.py",
  "generated_at": 1721849600,       // Unix timestamp
  "generated_date": "2026-07-25T00:00:00Z"
}
```

### device
```json
{
  "device_id": "7618686830888125966",  // 19-digit decimal, unique per profile
  "iid": "7619342647853074190",        // Install ID, 19-digit decimal
  "openudid": "5aeca2e40e7e5cf2",      // 16-char hex
  "cdid": "f8741d6d-78c5-4d95-983c-...", // UUID v4
  "clientudid": "a041f068-1eb3-...",     // UUID v4
  "google_aid": "563177c5-...",          // UUID v4
  "device_type": "SM-S916B",             // Android model name
  "device_brand": "samsung",
  "device_manufacturer": "samsung",
  "os_version": "14",
  "os_api": "34",
  "resolution": "1080*2340",
  "dpi": "420",
  "host_abi": "arm64-v8a",
  "build_fingerprint": "UP1A.231005.007",
  "is_pad": "0"
}
```

### app
```json
{
  "app_name": "musical_ly",
  "package": "com.zhiliaoapp.musically",
  "aid": "1233",
  "channel": "googleplay",
  "ssmix": "a",
  "app_type": "normal",
  "support_webview": "1"
}
```

### network
```json
{
  "ac": "wifi",
  "ac2": "wifi",
  "mcc_mnc": "310260",       // Region-specific (US=310260, VN=45204)
  "carrier_region": "US",     // Same as locale.region
  "carrier_region_v2": "310", // First 3 digits of mcc_mnc
  "sim_region": "us"          // Lowercase region
}
```

### locale
```json
{
  "timezone_name": "America/New_York",
  "timezone_offset": "-18000",
  "language": "en",
  "locale": "en",
  "app_language": "en",
  "sys_region": "US",
  "region": "US",
  "op_region": "US",
  "uoo": "0"
}
```

### session
```json
{
  "cookie": "store-idc=useast5; store-country-code=us; store-country-code-src=did; tt-target-idc=useast5; install_id=7619342647853074190; odin_tt=abc123...",
  "last_install_time": "1774016458",  // Unix timestamp as string
  "x_tt_token": "",
  "session_key": ""
}
```

**Cookie components** (all required for acceptance):
- `store-idc=<idc>` — datacenter: useast5 (US), sg (VN/Asia), eu (Europe), jp (Japan), kr (Korea)
- `store-country-code=<region lowercase>`
- `store-country-code-src=did`
- `tt-target-idc=<idc>`
- `install_id=<install_id>`
- `odin_tt=<sha512_hex_128chars>` — device fingerprint hash (sha512 of device_id:openudid:cdid:timestamp, truncated to 128 chars)

### guard_keys
```json
{
  "private_pem": "-----BEGIN PRIVATE KEY-----\nMIGHAgE...",   // EC P-256 PKCS#8 PEM
  "public_pem": "-----BEGIN PUBLIC KEY-----\nMFkwEwY...",     // EC P-256 SPKI PEM
  "tt_ticket_guard_public_key": "BCL2e3QzeZKG..."             // Base64 uncompressed EC point (65 bytes)
}
```

**Note**: Private key is PKCS#8 format (`-----BEGIN PRIVATE KEY-----`), NOT EC-specific (`-----BEGIN EC PRIVATE KEY-----`). Both `cryptography` and `pycryptodome` handle PKCS#8. The public point (`tt_ticket_guard_public_key`) is the raw 65-byte uncompressed EC point (04 || X || Y) base64-encoded, used in the `tt-ticket-guard-public-key` HTTP header.

### guard_headers
```json
{
  "tt-ticket-guard-public-key": "<base64 EC point>",
  "tt-ticket-guard-iteration-version": "0",
  "tt-ticket-guard-version": "3",
  "tt-device-guard-iteration-version": "1",
  "tt-device-guard-client-data": ""
}
```

`tt-device-guard-client-data` is empty in the static fallback; it gets populated dynamically by `device_guard.build_device_guard_client_data()` at request time using the private key from `guard_keys`.

### passport_headers
```json
{
  "x-tt-dm-status": "login=0;ct=0;rt=7"
}
```

## Supported Device Models (from generate_profiles.py)

| Model | Brand | os_api | os_version | Resolution | DPI |
|-------|-------|--------|------------|------------|-----|
| SM-S928B | samsung | 35 | 15 | 1440*3120 | 560 |
| SM-S926B | samsung | 35 | 15 | 1080*2340 | 420 |
| SM-S921B | samsung | 35 | 15 | 1080*2340 | 420 |
| SM-S918B | samsung | 34 | 14 | 1440*3088 | 560 |
| SM-S916B | samsung | 34 | 14 | 1080*2340 | 420 |
| SM-S911B | samsung | 34 | 14 | 1080*2340 | 420 |
| SM-G991B | samsung | 34 | 14 | 1080*2400 | 420 |
| SM-A556B | samsung | 35 | 15 | 1080*2340 | 420 |
| SM-A546B | samsung | 34 | 14 | 1080*2340 | 420 |
| SM-A536B | samsung | 34 | 14 | 1080*2408 | 450 |
| Pixel 8 Pro | google | 35 | 15 | 1344*2992 | 489 |
| Pixel 8 | google | 35 | 15 | 1080*2400 | 428 |
| Pixel 7 Pro | google | 34 | 14 | 1440*3120 | 512 |
| Pixel 7 | google | 34 | 14 | 1080*2400 | 416 |
| 2311DRK48C | Xiaomi | 34 | 14 | 1440*3200 | 522 |
| M2101K6G | Xiaomi | 34 | 14 | 1080*2400 | 440 |
| 2201116TG | Xiaomi | 34 | 14 | 1080*2400 | 440 |
| CPH2449 | OnePlus | 34 | 14 | 1440*3216 | 526 |
| NE2215 | OnePlus | 34 | 14 | 1080*2400 | 420 |
| CPH2269 | OPPO | 34 | 14 | 1080*2400 | 409 |
| RMX3085 | realme | 34 | 14 | 1080*2400 | 409 |
| V2109 | vivo | 34 | 14 | 1080*2400 | 440 |

## Region Configs

| Region | TZ | Offset | MCC/MNC | IDC |
|--------|-----|--------|---------|-----|
| US | America/New_York | -18000 | 310260 | useast5 |
| VN | Asia/Ho_Chi_Minh | 25200 | 45204 | sg |
| GB | Europe/London | 0 | 23420 | eu |
| JP | Asia/Tokyo | 32400 | 44020 | jp |
| KR | Asia/Seoul | 32400 | 45008 | kr |
| IN | Asia/Kolkata | 19800 | 40415 | sg |
| DE | Europe/Berlin | 3600 | 26207 | eu |
| FR | Europe/Paris | 3600 | 20815 | eu |
| BR | America/Sao_Paulo | -10800 | 72410 | us |
| AU | Australia/Sydney | 39600 | 50501 | sg |
| EG | Africa/Cairo | 7200 | 60201 | eu |
| TR | Europe/Istanbul | 10800 | 28603 | eu |
