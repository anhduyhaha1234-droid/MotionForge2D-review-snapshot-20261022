# tikapis.com SDK GitHub Repos
## Last updated: 2026-07-23

## Official Repos (tikapiscom org)

### tikapiscom/TikTok-Private-Api-TikApis.com (14★)
- **Purpose:** Python SDK for tikapis.com API v2
- **Files:** AndroidTikApis.py, HTTPRequester.py, account_create.py, account_login.py, captcha.py, device_create.py, sms_login.py, utilities.py
- **API URL:** `https://tikapis.com/private/android/v1/`
- **Auth:** `{'api-key': key, 'x-api-key': key, 'Content-Type': 'application/json'}`
- **Key flow:** device_template → device_register → get_token → get_seed → api_request
- **Proxy format:** `username:password@ip:port` (supports SOCKS5 and HTTP)
- **Auto geo-detect:** Uses ipinfo.io to detect proxy country, sets timezone/locale automatically

### tikapiscom/tikapis.com (older SDK)
- **Purpose:** Python SDK for tikapis.com API v1
- **Files:** TikApis.py, HTTPRequester.py, Solver.py, utilities.py
- **API URL:** `https://tikapis.com/api/android`
- **Auth:** `{'api-key': key, 'Content-Type': 'application/json'}`
- **Has:** account_register(), follow(), digg() methods
- **PITFALL:** TikApis.py has module-level code that runs device registration on import — must subclass or modify before importing

### tikapiscom/x-argus-x-ladon (3★)
- **Purpose:** X-Argus and X-Ladon encryption algorithms

## Third-Party SDKs

### nullcodss/tiktok-private-api (1★)
- **Purpose:** X-Gorgon, X-Argus, X-Ladon, TTEncrypt, MSSDK, device fingerprint, SM3 hash, Simon cipher, protobuf

## Device Registration Flow (from SDK source)

```python
from AndroidTikApis import AndroidTikApis

device = {
    "proxy": "username:password@ip:port",  # Optional
    "app_info": {
        "aid": 1233,
        "app_version": "34.0.2",
        "version_code": "340002",
        "manifest_version_code": "2023400020",
        "update_version_code": "2023400020",
    },
    "country_location": {},  # Auto-detected from proxy
    "mssdk_parameters": {"lc_sdk_version": 134252544},
}

tik = AndroidTikApis(**device)
tik.device_template()     # Get fingerprint template
tik.device_register()     # Register virtual device
tik.get_token()           # Get MSSDK token
tik.get_seed()            # Get MSSDK seed
# Then: tik.api_request("video/stats/{video_id}")
```

## Key Observations

1. **API key required** — Register at tikapis.com (free tier: $0/month, 1000 requests/day for Android, 200/day for iOS)
2. **api-v4.tikapis.com doesn't resolve via DNS** — docs show this URL but actual API is at `tikapis.com/private/android/v1/` or `tikapis.com/api/android`
3. **Proxy auto-geo** — SDK calls ipinfo.io through proxy to detect country, then sets `country_location` config automatically
4. **Two-phase token process** — `get_token()` returns a TikTok HTTP request → SDK executes it → decodes hex response → extracts actual token
5. **tikfollowers.com uses this backend** — tikfollowers.com's `/api/process` calls tikapis.com internally with the full device config
6. **Views endpoint:** `POST /video/stats/{video_id}` with full device config in body + headers: X-Platform, X-App-aid, x-api-key
