# Fresh Video + Fresh IP Test Results (2026-07-25)

## Objective
Test whether using a completely NEW video (different from the rate-limited one) with a fresh proxy IP would bypass the view-counting failure.

## Setup
- **Fresh IP:** 117.5.227.159 (via ZingProxy change-IP, rotated from 171.229.225.238)
- **Fresh video:** `7654840470471773461` (Croatia vs Panama, @thethaovtvofficial, ~10,700 plays)
  - Found via Snowflake bit manipulation of known valid `7654840470471789845`
  - Different video, same creator
- **Overused video:** `7654840470471789845` (Ronaldo goal, rate-limited, 6,376 plays)
- **Device:** Fixture profile `device_v44_3_1.json` (real MITM capture, 160-char odin_tt)
- **Full header set:** 37 headers via `build_headers()` + ECDSA P-256 guard headers

## Key Findings

### Finding 1: Freshly registered devices are REJECTED
- All views sent with `fresh_device_id` via unidbg → HTTP 200, Content-Length: 0 (empty body)
- Same fixture profile → HTTP 200, Content-Length: 105 (JSON with sc=0 + impr_id)
- **Implication:** Device registration via unidbg produces IDs that TikTok server does not recognize

### Finding 2: API accepts views but views DON'T count publicly
- 5/5 views to fresh video returned `status_code: 0` with unique `impr_id`
- Play count: 10,700 → 10,700 (no change after 210 seconds)
- Even the overused video also returned sc=0 with impr_id
- **Implication:** TikTok backend has anti-fraud filtering beyond the API acceptance layer

### Finding 3: Proxy does NOT block views
- Both direct AND proxy connections return `status_code=0` with fixture profile
- Proxy IP confirmed working: 117.5.227.159 (different from direct IP)
- **Implication:** Previous "proxy breaks views" hypothesis was wrong

### Finding 4: Fresh vs overused video gets same result
- Fresh video: sc=0, impr_id present, play count unchanged
- Overused video: sc=0, impr_id present, play count unchanged
- **Implication:** Issue is NOT video-specific rate limiting

## HTTP Response Analysis
```
HTTP Status: 200
Content-Type: application/json
Content-Length: 0  (for fresh device) / 105 (for fixture profile)
tt_stable: 1
tt_orcas_res: 1
Server: TLB
X-Cache: TCP_MISS from AkamaiGHost
```

## Conclusion
The TikTok API `/aweme/v1/aweme/stats` endpoint accepts view requests and returns `status_code=0` with `impr_id`, but the backend filtering system prevents these views from being counted in the public play count. This is likely an anti-fraud measure checking:
1. Device fingerprint validity (fixture device may be flagged)
2. IP reputation (datacenter/proxy IPs vs residential)
3. Request pattern (no actual video playback detected)
4. Session authenticity (no real app session history)

## Video Discovery Method
The fresh video was discovered using **Snowflake bit manipulation**: TikTok video IDs are Snowflake-based, so modifying the lower bits (±500 range) of a known valid ID yields other valid videos from the same user/timestamp. The oembed API ignores the username parameter, enabling systematic validation.
