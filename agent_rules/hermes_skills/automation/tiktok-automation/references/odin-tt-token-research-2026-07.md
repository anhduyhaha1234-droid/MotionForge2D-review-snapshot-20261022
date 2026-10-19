# odin_tt Token Research — 2026-07-25

## Executive Summary

`odin_tt` is a **client-generated device fingerprint cookie**, NOT server-assigned.
No TikTok API endpoint returns `odin_tt` via Set-Cookie headers.
The native Android SDK generates it client-side; on web, TikTok's Tea SDK JavaScript generates it.

## Live Endpoint Testing Results (2026-07-25)

> **Exhaustive follow-up**: See `references/odin-tt-exhaustive-endpoint-test-2026-07-25.md` for the complete 105-endpoint test across 10 categories. The results below are from initial targeted testing; the exhaustive test confirmed zero endpoints return odin_tt.

### /get_domains/v5/ — 404 on ALL hosts
```
api16-core-useast5.tiktokv.us     → 404 Not Found (Akamai CDN)
api16-normal-c-alisg.tiktokv.com  → 404 Not Found (TLB)
```
This endpoint previously returned `msToken` via Set-Cookie. Currently down on both hosts.
Warmup is non-fatal — views work without msToken.

### /service/2/device_register/ — No Set-Cookie, no odin_tt
```
log-va.tiktokv.com  → {"server_time":1784942879,"device_id":0,"install_id":0}
api.tiktokv.com     → {"server_time":1784942879,"device_id":0,"install_id":0}
```
Response has NO Set-Cookie headers. Only returns `device_id`, `install_id`, `server_time`.
(Returns 0/0 because request wasn't properly signed with unidbg — but the point holds: no Set-Cookie.)

### /passport/web/region_info/ — Sets msToken but no odin_tt
```
HTTP 404 but Set-Cookie: msToken=yYsuWxwy...
```
Alternative msToken source, but no odin_tt.

### Web Page (tiktok.com/discover) — odinId in rehydration JSON
```
Set-Cookie: ttwid=...; tt_csrf_token=...; tt_chain_token=...; msToken=...
```
NO `odin_tt` in any Set-Cookie header.

The page's `__UNIVERSAL_DATA_FOR_REHYDRATION__` JSON contains:
```json
{
  "webapp.app-context": {
    "wid": "7666272713287403024",
    "webIdCreatedTime": "1784943213",
    "odinId": "7666272666043270145",
    "botType": "others"
  }
}
```
- First request (no cookies): `odinId: "0"`
- Subsequent request (with ttwid cookie): `odinId: "7666272666043270145"`
- The `odinId` is a 19-digit numeric server-assigned ID
- JS (Tea SDK) then generates the `odin_tt` cookie client-side from this + device fingerprint

## odin_tt Format Analysis

### Fixture profile (MITM capture from real Android device)
```
odin_tt=a37a4a808da8f2b4252ab4686422b00df7607e1b3430357fedad6b62f5b35a4b3f9eab9a9cc7f57c8baa5efc22763f36ca2aa519abb21478530e93e0959b97c74923179cec4b11be03fdf79837e1def4
```
**Length: 160 hex chars (80 bytes)**
Source: `device_v44_3_1.json` fixture profile (captured 2026-03-23)

### Generated profile (sha512 approximation)
```
odin_tt=b48f6e47de1da3afa74585ef9e8d53c16371b4a97664e8501f2e1293156f15fb30ed3c3002ecf8c4a92e551cc1ffc3364af434800903fdbe7a38fa94103cea4b
```
**Length: 128 hex chars (64 bytes)**
Algorithm: `sha512(f"{device_id}:{openudid}:{cdid}:{timestamp}")[:128]`
Source: `generate_profiles.py` / `batch_generate_profiles.py`

### Does NOT match any standard hash
```python
# Fixture data
did = "7618686830888125966"
openudid = "5aeca2e40e7e5cf2"
cdid = "f8741d6d-78c5-4d95-983c-54ef73e284f7"
ts = 1774269206

raw = f"{did}:{openudid}:{cdid}:{ts}"
sha512_160 = hashlib.sha512(raw.encode()).hexdigest()[:160]
# Result: fb3572d36e00f9d9... ≠ fixture value a37a4a808da8...

sha256 = hashlib.sha256(raw.encode()).hexdigest()
# Result: e83eec03e29b... (64 chars, doesn't match)

md5_did = hashlib.md5(did.encode()).hexdigest()
# Result: 7c5ef78e5251... (32 chars, doesn't match)
```

**Conclusion**: The native SDK algorithm is NOT a simple hash. It's obfuscated in the `.so` libraries.

## Key Takeaway for Implementation

1. **odin_tt is client-generated** — don't waste time looking for a server endpoint
2. **Generated 128-char SHA-512 works** with the complete header stack (`build_headers()`)
3. **Real 160-char native value is better** but requires MITM capture from a real device
4. **The `/get_domains/v5/` warmup endpoint is dead** — msToken can alternatively come from `/passport/web/region_info/`
5. **The critical fix for view counting was the 30+ header set**, not the odin_tt format
