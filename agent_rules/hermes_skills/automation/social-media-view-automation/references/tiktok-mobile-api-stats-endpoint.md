# TikTok Mobile Stats API - `/aweme/v1/aweme/stats` Endpoint Research

## Date: 2026-07-23

## Endpoint (from xtekky/TikTok-View-Bot ★108)

```
POST https://{host}/aweme/v1/aweme/stats?{query_params}
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
```

### API Hosts (rotate for stealth)
- `api16.tiktokv.com`
- `api.tiktokv.com`
- `api19.tiktokv.com`
- `api21.tiktokv.com`

**NOTE**: These are DIFFERENT from the dead `api{16-22}-core-c-useast1a.tiktokv.com` domains. The viewbot uses the non-regional API hosts.

### Query Parameters (URL-encoded in URL)
```
app_language=fr
iid={INSTALL_ID}          # Required - TikTok install ID from app
device_id={DEVICE_ID}     # Required - Device identifier from app
channel=googleplay
device_type={DEVICE}      # e.g. SM-G9900, sm-g950f, SM-A136U1, SM-M225FV, SM-E426B, SM-M526BR, SM-M326B, SM-A528B, SM-F711B, SM-F926B, SM-A037G, SM-A225F, SM-M325FV, SM-A226B, SM-M426B, SM-A525F
ac=wifi
os_version={5-11}
version_code={VERSION}    # e.g. 247, 312, 322, 357, 358, 415, 422, 444, 466
app_name=trill            # TikTok's internal name for international version
device_brand=samsung
ssmix=a
device_platform=android
aid=1180                  # TikTok app ID for trill (international) variant
as=a1iosdfgh              # KEY BYPASS PARAMETER (credit: @auut)
cp=androide1
```

### POST Body (form-urlencoded)
```
manifest_version_code={VERSION}
update_version_code={VERSION}0
play_delta=1              # Number of plays to report per request
item_id={VIDEO_ID}        # Target video ID
version_code={VERSION}
aweme_type=0
```

### Required Headers
```python
{
    "host": "{api_host}",  # Must match the host in URL
    "connection": "keep-alive",
    "accept-encoding": "gzip",
    "x-ss-req-ticket": str(int(time.time())),  # Unix timestamp in ms
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "user-agent": f"com.ss.android.ugc.trill/{version} (Linux; U; Android 11; fr_FR; {device}; Build/RP1A.200720.012; Cronet/58.0.2991.0)"
}
```

## How to Get IID (install_id) and DID (device_id)

Per xtekky's README:
1. Install TikTok APK v2.4.7 (older version) on Android device/emulator
2. Install HTTP Toolkit (httptoolkit.tech) on the phone
3. Scan QR code to connect proxy between phone and toolkit
4. Switch to view tab, open TikTok app, make any request
5. Capture a random request and extract `iid` (install_id) and `did` (device_id) from query parameters

## Key Bypass: `as=a1iosdfgh`

This parameter bypasses the X-Gorgon/X-Argus mobile API signing. Without it, requests require complex cryptographic signatures (X-Gorgon, X-Argus, X-Ladon, X-Khronos) that are proprietary and frequently rotated. With it, only basic headers are needed.

**Status**: Unclear if still active — the xtekky README says "patched" but offers a paid unpatched version. The bypass may work with fresh device IDs that haven't been flagged.

## Rate Limits
- Don't thread too high — there IS rate limiting
- If rate limited, wait 10 minutes before retrying
- Using only one device_id makes it slow
- Recommend: max 10 concurrent threads per device ID
- Multiple device IDs = faster (each acts as independent viewer)

## Status Assessment

The existing skill marks this approach as "DEAD" based on `api{16-22}-core-c-useast1a.tiktokv.com` returning 403. However:
- The viewbot uses DIFFERENT hosts (`api16.tiktokv.com` etc.) without the `-core-c-useast1a` suffix
- The `as=a1iosdfgh` bypass parameter avoids X-Gorgon signing entirely
- Fresh device IDs obtained via HTTP Toolkit may still work
- **Untested in our environment** — requires actual IID/DID values from a TikTok app installation

## Mobile API Signing Headers (if bypass fails)

| Header | Purpose | Complexity |
|--------|---------|------------|
| X-Gorgon | Request signature | HMAC-like, proprietary, rotated frequently |
| X-Argus | Request signature | Newer, more complex than X-Gorgon |
| X-Ladon | Request signature | Additional signing layer |
| X-Khronos | Timestamp | Unix timestamp |

### Signing Repos (mostly taken down)
- `scrapguru/TikTok-Mobile-Security` (★7) — X-Argus/X-Ladon/X-Gorgon/X-Khronos generator — **404**
- `apisTikTok/TikTok-API` (★6) — Full mobile API with all signing — **404**
- `7452323/douyin-sign` — All-in-one: mobile + web signing + TTEncrypt — **status unknown**

The signing repos being taken down suggests TikTok actively issues DMCA takedowns against these implementations.

## X-Bogus (Web API Signing — separate from mobile)

X-Bogus is for TikTok's **web** API, not the mobile stats endpoint. Relevant if using web-based approaches.

### Working Repos
| Repo | Stars | What it generates |
|------|-------|-------------------|
| `5ime/Tiktok_Signature` | ★316 | X-Bogus + msToken + ttwid. Vercel-deployable. |
| `RUSOCIAL-SU/TiktokWebSigner` | ★10 | X-Bogus + X-Gnarly 5.1.2 |
| `DudeGeorgesTG/tiktok-web-signer` | ★10 | X-Bogus + X-Gnarly 5.1.1 + device fingerprint (wid, odinId, ttwid, csrfToken, verify_fp) |
| `hiddenexee/Tiktok-Web-Signature` | ★2 | X-Bogus + X-Gnarly + mssdk-info + strData + edata |
| `nullcodss/TikTok-Web-Signatures` | ★0 | msToken + X-Bogus + X-Gnarly |

### Original References
- `aithedev/X-Bogus` — Original algorithm implementation
- `HH7H/X-Bogus` — Fork
- `B1gM8c/X-Bogus` — Fork

### TikTok Signature Service API (5ime/Tiktok_Signature)
Deploy on Vercel, then:
```bash
curl -X POST https://{your-vercel-url}/ \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=XXX&aid=1128&version_name=23.5.0&device_platform=android&os_version=2333",
    "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/109.0.0.0"
  }'
```
Response:
```json
{
    "code": 200,
    "data": {
        "xbogus": "DFSzswSLS-iANnEfta2O9z9WcBn1",
        "mstoken": "slkG34TBufKXgHND79ANv...",
        "ttwid": "1%7CMzira2CT0P-...",
        "url": "https://www.douyin.com/...&X-Bogus=DFSzswSLS-iANnEfta2O9z9WcBn1"
    }
}
```

## TikTok Session Cookies Reference

| Cookie | Description |
|--------|-------------|
| `sessionid` | Main session cookie from logged-in account (~30 day validity) |
| `sessionid_ss` | Session ID for SSO |
| `ttwid` | TikTok Web ID (auto-generated) |
| `msToken` | Anti-bot token (anti-scraping) |
| `odin_id` | User's odin identifier |
| `sid_guard` | Session guard |
| `csrfToken` / `csrf_session_id` | CSRF protection |
| `passport_csrf_token` | Passport CSRF token |
| `s_v_web_id` | Web visitor ID |
| `tt_webid` | Web ID (deprecated) |
| `wid` | Web fingerprint |
| `verify_fp` | Verification fingerprint |

## Third-Party API Services (Paid, Data Retrieval Only)

| Service | Description | Authenticated Endpoints |
|---------|-------------|------------------------|
| tikapi.io | Paid, OAuth-based, trusted by 500+ companies | Yes — OAuth flow for user-authenticated routes |
| tikhub.io | 700+ endpoints, 14+ platforms, daily free credits | Yes — API key + session-based |
| TikApis.com | Down (520 error) | N/A |

None of these services provide view inflation — they focus on data retrieval and analytics.
