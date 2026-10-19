# proxyvt.com VN Residential Proxies (2026-07-25)

## Proxy Format

```
dc-vn24.proxyvt.com:PORT:u_USER_RNHC3R:EUZI7ZHGNnvm
```

- Host: `dc-vn24.proxyvt.com` (all proxies share same host)
- Ports: 40123-64145 (unique per proxy)
- Auth: `u_USER_RNHC3R:EUZI7ZHGNnvm` (same for all)
- Protocol: SOCKS5 authenticated
- Location: Vietnam residential IPs

## File Location

`C:\Users\Admin\Desktop\tiktok auto\order_15_proxies.txt` — 108 proxies, one per line

## Python Usage

```python
import socks, sockshandler, ssl, urllib.request

# Parse proxies
PROXIES = []
with open(r'C:\Users\Admin\Desktop\tiktok auto\order_15_proxies.txt') as f:
    for line in f:
        line = line.strip()
        if not line: continue
        parts = line.split(':')
        if len(parts) == 4:
            host, port, user, pw = parts
            PROXIES.append({'host': host, 'port': int(port), 'user': user, 'pass': pw})

def make_opener(proxy):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return urllib.request.build_opener(
        sockshandler.SocksiPyHandler(socks.SOCKS5, proxy['host'], proxy['port'],
                                    rdns=True, username=proxy['user'], password=proxy['pass']),
        urllib.request.HTTPSHandler(context=ctx))
```

## Verified Results (2026-07-25)

Test: 108 requests to `/aweme/v1/aweme/stats?play_delta=1` with fixture profile

| Metric | Value |
|--------|-------|
| ✅ sc=0 + impr_id | 81/108 (75%) |
| ⚪ EMPTY (rate-limited) | 26/108 (24%) |
| 🔴 SOCKS5 error | 1/108 (1%) |
| Views increase | 0 (6377→6377) |

**Conclusion:** proxyvt proxies WORK for API delivery (75% success rate) but views don't increase because TikTok deduplicates by device_id, not IP. The same fixture profile's device_id = max 1 view regardless of how many different IPs are used.

## Comparison with ZingProxy

| Feature | proxyvt.com | ZingProxy |
|---------|------------|-----------|
| Type | SOCKS5 authenticated | SOCKS5 authenticated |
| IP rotation | Fixed IP per port (108 ports) | Auto-rotate or change-IP API |
| Location | VN residential | VN datacenter |
| Cost | Paid subscription | Paid subscription |
| Status (2026-07) | ✅ Active | ❌ Expired |

## Working Bot

`C:\Users\Admin\ttsigning\view_bot_v9_proxyvt.py` — 108 VN proxies, fixture profile, gzip body, full signing headers
