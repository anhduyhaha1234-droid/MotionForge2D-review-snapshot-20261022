# ZingProxy Rotating Proxy Pattern

## Proxy Format
```
SOCKS5: socks5://user:pass@host:port
```
- Host stays same, exit IP auto-rotates every ~20s
- Also supports manual rotation via API

## Change-IP API
```
GET https://api.zingproxy.com/open/change-ip/<token>
```

### Success Response
```json
{"status": "success", "newIP": "x.x.x.x"}
```

### Rate Limited Response
```json
{"statusCode": 400, "remainingSeconds": 5, "error": "Vui lòng đợi 1 giây cho lần đổi IP tiếp theo."}
```

### Usage Pattern
```python
import requests, time

def rotate_ip(token):
    """Force IP rotation. Returns new IP or None."""
    r = requests.get(f'https://api.zingproxy.com/open/change-ip/{token}', timeout=15)
    data = r.json()
    if data.get('statusCode') == 400:
        wait = data.get('remainingSeconds', 1) + 3
        time.sleep(wait)
        r = requests.get(f'https://api.zingproxy.com/open/change-ip/{token}', timeout=15)
        data = r.json()
    return data.get('newIP')

# After rotation, wait for new IP to stabilize on SOCKS5 endpoint
rotate_ip(token)
time.sleep(5)  # stabilization period
```

### Key Notes
- Call via plain `requests.get()` (no proxy needed — this hits ZingProxy API, not TikTok)
- Wait `remainingSeconds + 3` before retrying on rate limit
- After successful rotation, wait 3-5s for SOCKS5 endpoint to pick up new IP
- Verify IP changed: `requests.get('https://api.ipify.org?format=json', proxies={'https': f'socks5://u:p@h:p'}).json()['ip']`
- Proxy `host:port:user:pass` stays the same — only exit IP changes

## Bot Integration Pattern
```python
for i in range(count):
    # 1. Rotate IP
    new_ip = rotate_ip(TOKEN)
    time.sleep(3)
    
    # 2. Verify IP
    current_ip = get_ip_through_proxy()
    
    # 3. Send view
    ok, resp = send_view(video_id, profile, proxy=PROXY_URL)
    
    # 4. Report
    print(f"[{i+1}] IP:{current_ip} status={resp.get('status_code')}")
    
    time.sleep(delay)
```

## Tested Proxy Config (2026-07-24)
```
Host: 117.0.113.155
Port: 40917
User: ehzte_duyho
Token: p2r615b8zpn500b9357cbe8cf45ed010a2abe165213e30c8e985d91
IPs seen: 171.236.116.148, 117.5.221.187, 117.1.92.25, 116.98.85.70 (all Vietnamese)
```

## Pitfall: SOCKS5 Connection Refused During Rotation
When IP is rotating, SOCKS5 connections get "0x05: Connection refused" errors. This is normal — the proxy endpoint is temporarily unavailable while switching. Pattern:
1. Call change-IP
2. Wait 3-5s
3. Retry connection
4. If still failing, wait longer (up to 20s)
