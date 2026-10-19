# odin_tt Exhaustive Endpoint Test Results (2026-07-25)

## Summary
- **Total tests**: 105 (83 Phase 1 + 22 Phase 2)
- **Endpoints that returned odin_tt**: 0
- **Conclusion**: odin_tt is client-side generated, NOT server-issued

## Test Categories

### 1. POST /service/2/device_register/ (32 tests)
**8 hosts × 4 wire formats** — all returned device_id/install_id with ZERO Set-Cookie headers.

| Host | Wire Format | HTTP | Set-Cookie | odin_tt |
|------|------------|------|------------|---------|
| log-va.tiktokv.com | java | 200 | 0 | ✗ |
| log-va.tiktokv.com | java_gzip_sig | 200 | 0 | ✗ |
| log-va.tiktokv.com | json_gzip | 200 | 0 | ✗ |
| log-va.tiktokv.com | json_plain | 200 | 0 | ✗ |
| api.tiktokv.com | java | 200 | 0 | ✗ |
| log.byteoversea.com | java | 200 | 0 | ✗ |
| log15.byteoversea.com | java | 200 | 0 | ✗ |
| log.isnssdk.com | java | 200 | 0 | ✗ |
| log.sgsnssdk.com | java | 200 | 0 | ✗ |
| log2.musical.ly | java | 200 | 0 | ✗ |
| log.snssdk.com | java | 200 | 0 | ✗ |

Response body: `{"server_time": ..., "device_id": ..., "install_id": ...}` — no cookie fields.

### 2. GET /get_domains/v5/ — Warmup (6 tests)
All hosts return **HTTP 404**. No Set-Cookie headers.

| Host | HTTP | Set-Cookie |
|------|------|------------|
| api16-core-useast5.tiktokv.us | 404 | 0 |
| api16-normal-c-alisg.tiktokv.com | 404 | 0 |
| api16-normal-c-useast5.tiktokv.com | DNS fail | — |
| api19-core-useast5.tiktokv.us | 404 | 0 |
| api19-normal-c-useast5.tiktokv.com | DNS fail | — |
| api22-normal-c-useast5.tiktokv.com | DNS fail | — |

### 3. TikTok Web Pages (6 tests)
Returns web cookies but NO odin_tt.

| Endpoint | HTTP | Cookies Returned |
|----------|------|------------------|
| www.tiktok.com/ | 200 | tt_csrf_token, ttwid, tt_chain_token |
| www.tiktok.com/discover | 200 | tt_csrf_token, ttwid, tt_chain_token, msToken |
| www.tiktok.com/login | 200 | tt_csrf_token, ttwid |
| www.tiktok.com/signup | 200 | tt_csrf_token, ttwid |
| m.tiktok.com/ | 200 | tt_csrf_token, ttwid, tt_chain_token |
| m.tiktok.com/discover | 404 | 0 |

### 4. Passport Endpoints (24 tests)
4 hosts × 6 endpoints. Returns msToken on some, but no odin_tt.

| Host | Endpoint | HTTP | Cookies |
|------|----------|------|---------|
| api16-normal-c-alisg | /passport/web/region_info/ | 404 | msToken |
| api16-normal-c-alisg | /passport/web/get_region_info/ | 404 | msToken |
| api16-normal-c-alisg | /passport/web/create_captcha/ | 404 | msToken |
| api16-normal-c-alisg | /passport/web/login/ | 404 | msToken |
| api16-normal-c-alisg | /passport/app/region/ | 200 | reg-store-region |
| api16-normal-c-alisg | /passport/web/login/qrcode/create/ | 404 | msToken |
| api16-core-useast5 | all 6 endpoints | 404 | 0 |
| passport.tiktokv.com | all 6 endpoints | DNS fail | — |
| ib.tiktokv.com | all 6 endpoints | DNS fail | — |

### 5. Passport Step1/Step2 (2 tests)

| Step | Endpoint | HTTP | Cookies |
|------|----------|------|---------|
| Step1 | /passport/user/check_login_name_registered/ | 404 | 0 |
| Step2 | /passport/user/login/pre_check/ | 200 | store-idc, tt-target-idc, msToken, reg-store-region (cleared) |

### 6. Web Passport Endpoints (5 tests)

| Endpoint | Method | HTTP | Cookies |
|----------|--------|------|---------|
| /passport/web/login/ | GET | 404 | msToken |
| /passport/web/login/ | POST | 404 | msToken |
| /passport/web/create_captcha/ | POST | 404 | msToken |
| /passport/web/csidk/get/ | GET | 404 | msToken |
| /passport/web/get_token/ | POST | 404 | msToken |

### 7. App API Endpoints (21 tests)
3 hosts × 7 endpoints. No Set-Cookie from any.

| Host | Endpoint | HTTP | Cookies |
|------|----------|------|---------|
| api16-normal-c-alisg | /aweme/v1/hot/search/list/ | 200 | 0 |
| api16-normal-c-alisg | /aweme/v1/tab/feed/ | 200 | 0 |
| api16-normal-c-alisg | /aweme/v1/discover/search/ | 403 | 0 |
| api16-normal-c-alisg | /aweme/v1/user/profile/self/ | 403 | 0 |
| api16-normal-c-alisg | /aweme/v1/notice/count/ | 403→200 | 0 |
| api16-normal-c-alisg | /aweme/v1/message/unread/count/ | 403 | 0 |
| api16-normal-c-alisg | /aweme/v1/message/inbox/list/ | 200 | 0 |
| api16-core-useast5 | all 7 endpoints | 200/404 | 0 |

### 8. Auth Broadcast (2 tests)
Noted in code as "triggers odin_tt + msToken refresh" — actually returns only msToken + clears reg-store-region.

| Host | HTTP | Cookies |
|------|------|---------|
| api16-normal-c-alisg | 200 | reg-store-region (cleared), msToken |
| api16-normal-c-useast5 | DNS fail | — |

### 9. ByteDance CDN/Edge (5 tests)

| Endpoint | HTTP | Cookies |
|----------|------|---------|
| www.tiktok.com/ | 200 | tt_csrf_token, ttwid, tt_chain_token |
| sf16-scmcdn-va.ibytedtos.com (cookie.js) | 412 | 0 |
| analytics.tiktok.com (pixel.js) | 404 | 0 |
| mon.tiktokv.com (monitoring) | 404 | 0 |
| log.byteoversea.com/ (device_register) | 200 | 0 |

### 10. TikTok Lite / Musical.ly (3 tests)

| Host | Endpoint | HTTP | Cookies |
|------|----------|------|---------|
| log2.musical.ly | /service/2/device_register/ | 200 | 0 |
| log.byteoversea.com | /service/2/device_register/ | 200 | 0 |
| api-h2.amemv.com | /service/2/device_register/ | DNS fail | — |

### 11. Response Body Scan (7 tests)
Searched ALL response bodies for "odin_tt" string, long hex strings, and token patterns.

| URL | Bytes | odin_tt in body | Long hex tokens |
|-----|-------|-----------------|-----------------|
| www.tiktok.com/ | 1,462 | ✗ | ✗ |
| www.tiktok.com/discover | 367,537 | ✗ | ✗ |
| www.tiktok.com/login/phone_or_email | 63,025 | ✗ | ✗ |
| www.tiktok.com/api/config/ | 108 | ✗ | ✗ |
| www.tiktok.com/@tiktok | 1,462 | ✗ | ✗ |
| m.tiktok.com/ | 1,462 | ✗ | ✗ |
| www.tiktok.com/robots.txt | 1,288 | ✗ | ✗ |

### 12. Empty/Minimal Cookie Registration (2 tests)
Tested device_register with empty cookie and minimal cookie to see if server issues new odin_tt.

| Cookie | HTTP | Set-Cookie | device_id |
|--------|------|------------|-----------|
| Minimal (store-idc + install_id) | 200 | 0 | 0 |
| Empty | 200 | 0 | 0 |

## Complete Cookie Inventory

| Cookie Name | Where Issued | Purpose |
|-------------|-------------|---------|
| `ttwid` | www.tiktok.com (web pages) | Web session identifier |
| `tt_csrf_token` | www.tiktok.com (web pages) | CSRF protection |
| `tt_chain_token` | www.tiktok.com (web pages) | Chain validation |
| `msToken` | www.tiktok.com, passport endpoints | Session token |
| `reg-store-region` | /passport/app/region/ | Region detection (cleared after use) |
| `store-idc` | /passport/user/login/pre_check/ | Datacenter routing |
| `tt-target-idc` | /passport/user/login/pre_check/ | Target datacenter |
| `odin_tt` | **NOWHERE** | Client-generated by native SDK |

## Key Findings

1. **device_register returns NO cookies at all** — not even session cookies. Response is just `device_id`, `install_id`, `server_time`.
2. **auth_broadcast does NOT trigger odin_tt** — despite code comment in `login_client.py:1360`. Only returns msToken.
3. **Warmup endpoint is dead** — `/get_domains/v5/` returns 404 on all tested hosts.
4. **Web pages return ttwid/msToken but NOT odin_tt** — the Tea SDK JS generates odin_tt client-side after page load.
5. **App API endpoints return no Set-Cookie at all** — they expect cookies in the request, not issue new ones.
6. **passport.tiktokv.com and ib.tiktokv.com don't resolve in DNS** from this network.

## Implications

To obtain valid odin_tt, you MUST use one of:
1. **MITM capture** from a real TikTok app running on a device/emulator (gold standard)
2. **Reverse-engineer** the generation algorithm in the native `.so` libraries
3. **Frida hooks** to extract the token from the app's memory at runtime

No amount of API endpoint testing will yield odin_tt — it never crosses the wire as a server response.

## Test Scripts
- `test_odin_tt_endpoints.py` — Phase 1 (83 tests, all categories)
- `test_odin_tt_phase2.py` — Phase 2 (22 tests, deep-dive)
- `odin_tt_endpoint_results.json` — Phase 1 raw results
- `odin_tt_phase2_results.json` — Phase 2 raw results
