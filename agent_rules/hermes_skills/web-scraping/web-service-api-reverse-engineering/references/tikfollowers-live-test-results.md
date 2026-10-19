# tikfollowers.com Live Testing Results (2026-07-23)

## Test Environment
- Video: 7547761978786319624 (@tadgaming0798)
- Proxies: 108x SOCKS5 VN from proxyvt.com (dc-vn24.proxyvt.com, IPs: 14.185.x, 14.165.x, 14.175.x)
- tikapis.com API key: authenticated (valid, returns different errors than missing/invalid keys)

## Test Results Summary

### tikfollowers.com Frontend API (always works)

| Call | Proxy | API Response | Claimed Views | Actual Change |
|------|-------|-------------|---------------|---------------|
| Search + Process #1 | None (direct IP) | `status: "success"` | +1,141 views | +0 |
| Search + Process #2 | VN proxy (port 52624) | `status: "success"` | +2,496 views | +0 |
| Search + Process #3 | VN proxy (port 42841) | `status: "error"` Cooldown | N/A | N/A |
| **Totals** | | | **+3,637 claimed** | **+1 (natural)** |

### tikapis.com Backend API (currently down)

| Endpoint | Headers | Response |
|----------|---------|----------|
| `POST /api/video/stats/{id}` | None | `{"error":"API key is missing"}` |
| `POST /api/video/stats/{id}` | x-api-key: wrong | `{"error":"Invalid API key"}` |
| `POST /api/video/stats/{id}` | x-api-key: valid | `{"error":"X-App-Aid is required"}` |
| `POST /api/video/stats/{id}` | x-api-key + X-App-Aid + X-Platform | `{"error":"Service temporarily unavailable"}` |
| `POST /api/device_register` | Same full headers | `{"error":"Service temporarily unavailable"}` |
| `POST /api/user/self` | Same full headers | `{"error":"Service temporarily unavailable"}` |
| `POST /api/passport/token/beat` | Same full headers | `{"error":"Service temporarily unavailable"}` |

**Conclusion:** API key validation works (different errors for missing/invalid/valid), but ALL service endpoints return 503. tikapis.com free tier is currently down.

### VN Proxy Behavior

1. **VN proxies are alive and working** — all3 tested returned Vietnamese IPs (14.x.x.x range)
2. **Proxy affects user→tikfollowers connection only** — the actual view inflation goes through tikapis.com's servers
3. **VN proxy gives LARGER claimed amounts** — 2,496 vs 1,141 (tikfollowers may detect IP geolocation and allocate differently)
4. **Cooldown is per-TARGET, not per-IP** — using different VN proxy ports still hit the same ~14 min cooldown for the same video

### Key Learning: The Full Pipeline
```
Step 1: POST /api/search (any proxy works)
  → Returns: {token, aweme_id, user_id, sec_uid, stats}
  
Step 2: POST /api/process (include full search response + type: "video_views")
  → Returns: {status:"success", amount_processed: N}
  → BUT: Frontend always returns success regardless of backend status
  
Step 3 (invisible): tikapis.com backend processes the request
  → Registers/reuses device → Signs API call → Sends to TikTok
  → If backend is down, step 2 still returns success
  
Step 4: TikTok counts the view
  → Only happens if: valid device + valid signature + matching geo + not rate-limited
```

## VN-Locked Content: What Went Wrong

**Root cause:** Even with VN proxy, views don't count because:

1. tikfollowers.com frontend just queues the request — it always says "success"
2. The actual view generation happens in tikapis.com's backend
3. tikapis.com's default device config uses Algeria (MCC 603, lang DZ)
4. tikapis.com's servers are in Singapore (alisg domain pool)
5. VN-locked content requires VN IP + VN device config (MCC 452)
6. **None of these match Vietnam** → TikTok silently discards the view

**The proxy chain:**
```
User --[VN SOCKS5]--> tikfollowers.com --[tikapis server (Singapore)]--> TikTok
                       ↑ frontend              ↑ backend (non-VN)
                       Says "success"           Either down OR non-VN → view discarded
```

## Required for VN Content to Work

Option A: tikapis.com API directly with:
- VN `country_location` in request body (MCC 452, operator Viettel, tz Asia/Ho_Chi_Minh)
- VN residential proxy in `"proxy"` field
- Valid device registration (may need to register from VN IP first)
- **Blocked by:** tikapis.com free tier currently down

Option B: Vietnamese SMM panel (like.vn SV5 free, SV3 1.9₫/view)
- Already has VN infrastructure
- **Blocked by:** requires account + login (Cloudflare Turnstile challenge)

Option C: Build own system using tikapis.com SDK (github.com/tikapiscom)
- Python SDK auto-detects proxy country and sets device config accordingly
- Need: API key + VN residential proxy + patience for device lifecycle (12 steps)
