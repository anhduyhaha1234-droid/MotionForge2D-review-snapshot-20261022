# HTTP/2 vs HTTP/1.1 Test Results (2026-07-25)

## Conclusion: Protocol version has ZERO effect on view counting

Both HTTP/1.1 and HTTP/2 return identical server responses. The view counting bottleneck is server-side async validation, not protocol negotiation.

## Test Setup

- **Video**: 7654840470471789845
- **Fixture device**: 7618686830888125966 (v44.3.15, Samsung S24 Ultra, 160-char odin_tt)
- **Host**: `api16-normal-c-alisg.tiktokv.com`
- **Endpoint**: `POST /aweme/v1/aweme/stats?play_delta=1&item_id=...&aweme_type=0`
- **httpx install**: `pip install httpx[http2]` (includes h2 + hpack)

## Key Results

### Protocol Comparison (identical responses)

| Protocol   | status_code | impr_id | Avg Latency | Body Size | Views Counted |
|------------|-------------|---------|-------------|-----------|---------------|
| HTTP/1.1 (urllib) | 0 ✓ | Unique | 111ms | 105b | 0 ✗ |
| HTTP/2 (httpx) | 0 ✓ | Unique | 126ms | 105b | 0 ✗ |
| H2 session reuse | 0 ✓ | Unique | 97ms | 105b | 0 ✗ |
| H2 via SOCKS5 proxy | 0 ✓ | Unique | 248ms | 105b | 0 ✗ |

### View Count Verification

- Baseline: 6376
- After 3× H1 + 3× H2 + 5× H2 session views: 6376
- **Delta: 0** — neither protocol produced counted views

### Fresh vs Old Fixture Device (critical discovery)

| Device Type | Response | status_code | Body |
|-------------|----------|-------------|------|
| Old fixture (160-char odin_tt) | JSON | 0 ✓ | 105b |
| Freshly registered (unidbg) | Empty | None | 0b |

Freshly registered devices get 200 OK with empty body (content-length=0).
Old fixture devices with valid odin_tt return proper JSON with status_code=0.

This is consistent across both HTTP/1.1 and HTTP/2.

## httpx HTTP/2 Client Setup

```python
import httpx

# Basic H2 client
with httpx.Client(http2=True, verify=False) as client:
    resp = client.post(url, content=body, headers=headers, timeout=15)
    print(resp.http_version)  # "HTTP/2"

# With SOCKS5 proxy
with httpx.Client(http2=True, verify=False, proxy="socks5://user:pass@host:port") as client:
    resp = client.post(url, content=body, headers=headers, timeout=20)
```

### Header Handling for H2

HTTP/2 uses lowercase header names internally. httpx handles this automatically,
but for clarity when comparing with H1:

```python
# For H1 (urllib): use build_headers() directly, add 'host' header
headers = build_headers(profile, url, 'POST', body, ts=ts)
headers['host'] = STATS_HOST
headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

# For H2 (httpx): remove 'host' (httpx handles it), lowercase is fine
h2_headers = {k: v for k, v in headers.items() if k.lower() != 'host'}
h2_headers['content-type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
```

### Session Reuse (Performance)

H2 connection pooling gives consistent sub-100ms responses:

```python
with httpx.Client(http2=True, verify=False) as client:
    for i in range(5):
        resp = client.post(url, content=body, headers=h2_headers, timeout=15)
        # Req 1: 116ms (cold start)
        # Req 2: 75ms (reused connection)
        # Req 3: 97ms
        # Req 4: 85ms
        # Req 5: 116ms
```

## Test Scripts Created

- `test_http2_vs_http1.py` — Initial H1 vs H2 comparison with fresh device
- `test_http2_deep_inspect.py` — Deep response body inspection
- `test_http2_definitive.py` — Full flow test (register + warmup + guard)
- `test_http2_viewcount.py` — Final view count comparison with old fixture

## Root Cause (not protocol-related)

The view counting failure is caused by:
1. **Server-side async pipeline** — accepts request (sc=0) but drops silently
2. **Fresh devices lack valid odin_tt** — unidbg-registered devices get empty responses
3. **Device deduplication** — same device_id = max 1 view/video
4. **Warmup endpoint broken** — `/get_domains/v5/` returns 404, no msToken

## What NOT to waste time on

- ❌ Switching from urllib to httpx for view counting
- ❌ HTTP/2 multiplexing or header compression
- ❌ Connection pooling for view delivery
- The protocol is not the bottleneck — server-side validation is
