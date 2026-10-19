---
name: socks5-proxy-automation
description: "Working with SOCKS5 authenticated proxies in automation pipelines. Covers the pproxy HTTP relay pattern for browser automation, proxy testing methodology, and common pitfalls."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [proxy, socks5, automation, browser, pproxy, networking]
    related: [terminal-engineering-discipline]
---

# SOCKS5 Proxy Automation

## The Core Problem

**Browsers (Playwright, Selenium, Chromium) DO NOT support SOCKS5 proxy authentication natively.**

- `curl --socks5-hostname "user:pass@host:port"` ✅ works
- Python `requests` + `pysocks` (`socks5://user:pass@host:port`) ✅ works
- Playwright `proxy: {server: 'socks5://host:port', username, password}` ❌ fails with `ERR_SOCKS_CONNECTION_FAILED`
- Selenium `--proxy-server=socks5://host:port` ❌ fails (no auth support)
- Chromium CDP `Fetch.authRequired` ❌ only handles HTTP auth, not SOCKS5

## Solution: pproxy HTTP→SOCKS5 Relay

Use `pproxy` to create local HTTP proxies that tunnel through authenticated SOCKS5 upstreams.

### Install
```bash
pip install pproxy
```

### Start Relay
```python
import subprocess, sys, time

proxies = [
    (18080, 'socks_host', 1080, 'username', 'password'),
    (18081, 'socks_host2', 1080, 'username', 'password'),
]

procs = []
for lp, sh, sp, su, spw in proxies:
    cmd = [sys.executable, '-m', 'pproxy', 
           '-l', f'http://0.0.0.0:{lp}',
           '-r', f'socks5://{sh}:{sp}#{su}:{spw}']  # NOTE: # separator for auth!
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    procs.append(proc)
    time.sleep(0.3)

time.sleep(3)  # Wait for all relays to start
```

### Use with Playwright
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        proxy={'server': 'http://127.0.0.1:18080'}  # No auth needed!
    )
    page = browser.new_page()
    page.goto('https://target-site.com')
```

### Use with Selenium
```python
from selenium import webdriver

opts = webdriver.ChromeOptions()
opts.add_argument('--proxy-server=http://127.0.0.1:18080')
driver = webdriver.Chrome(options=opts)
```

### Use with requests (alternative to pysocks)
```python
import requests
r = requests.get('https://target.com', 
    proxies={'http': 'http://127.0.0.1:18080', 'https': 'http://127.0.0.1:18080'})
```

## pproxy URI Format

```
socks5://HOST:PORT#USER:PASS
         ↑     ↑    ↑
       host  port  auth (after #)
```

**CRITICAL:** The auth separator is `#`, NOT `@`. Using `socks5://user:pass@host:port` will FAIL silently.

Supported protocols: `http`, `socks4`, `socks5`, `shadowsocks`, `tunnel`

## Proxy Testing Methodology

### Rule: ALWAYS Test with the TARGET Site

Testing with `httpbin.org` is NOT sufficient. Many proxies:
- Block specific sites
- Return different responses per domain
- Have geo-restrictions

```bash
# WRONG - only tests generic connectivity
curl -s --socks5-hostname "user:pass@host:port" https://httpbin.org/ip

# RIGHT - test with actual target
curl -s --socks5-hostname "user:pass@host:port" https://target-site.com -o /dev/null -w "%{http_code} %{size_download}"
```

### Multi-Method Testing Script

```python
import subprocess, socket

def test_proxy_comprehensive(proxy, target_url):
    host, port, user, pw = proxy.split(':')
    
    # Test 1: TCP connect
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((host, int(port)))
        s.close()
        tcp_ok = True
    except:
        tcp_ok = False
    
    # Test 2: SOCKS5 to target
    auth = f'{user}:{pw}@{host}:{port}'
    cmd = f'curl -s --socks5-hostname "{auth}" --max-time 15 -w "CODE:%{{http_code}} SIZE:%{{size_download}}" "{target_url}" | tail -c 60'
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=20)
    
    return {
        'tcp': tcp_ok,
        'socks5_response': r.stdout.strip(),
    }
```

### Pitfall: curl -o /dev/null Reports 0 Bytes

When using `curl -o /dev/null -w "%{size_download}"`, the size may report 0 even when content was received. Use without `-o /dev/null` and pipe to `tail -c N` instead:

```bash
# WRONG - may report 0 bytes
curl -s --socks5-hostname "auth" --max-time 15 -o /dev/null -w "%{size_download}" "URL"

# RIGHT - accurate size
curl -s --socks5-hostname "auth" --max-time 15 -w "CODE:%{http_code} SIZE:%{size_download}" "URL" | tail -c 60
```

### Pitfall: httpbin.org Fails but Target Works (CONFIRMED 2026-07-23)

SOCKS5 residential proxies frequently return 503 or empty responses to httpbin.org, but deliver full 300-378KB responses to actual target sites (e.g., TikTok). User correction: "proxy tôi test vẫn sống" — the proxies were alive, we were testing with the wrong target.

**Lesson:** Never declare proxies dead based on httpbin.org results alone. Always test with the actual target site. If TCP connect succeeds but httpbin fails, test the real target before giving up.

## Proxy Format Conventions

| Provider | Format | Type |
|----------|--------|------|
| Residential | `host:port:user:pass` | SOCKS5 |
| Datacenter | `ip:port:user:pass` | SOCKS5/HTTP |
| Free | `ip:port` | HTTP (no auth) |

Common mistake: Assuming HTTP when provider says SOCKS5. Always verify with the provider or test both:

```bash
# Test as SOCKS5
curl -s --socks5-hostname "user:pass@host:port" https://target.com

# Test as HTTP
curl -s -x "http://user:pass@host:port" https://target.com
```

## Cleanup Pattern

Always terminate relay processes when done:

```python
# Store processes
procs = []
for ... in proxies:
    proc = subprocess.Popen(...)
    procs.append(proc)

# ... do work ...

# Cleanup
for proc in procs:
    proc.terminate()
```

## Support Files

- **`references/tiktok-anti-bot.md`** — TikTok anti-bot detection details, API endpoints, view counting mechanism, Zefoy status, tested approaches
- **`scripts/test_proxies.py`** — Multi-method proxy connectivity test (TCP, SOCKS5, HTTP, target-specific). Tests with ACTUAL TARGET, not just httpbin.
- **`scripts/pproxy_relay.py`** — PPROXY relay manager for batch proxy relay start/test/cleanup

## PySocks + sockshandler Direct Approach (for urllib)

When using `urllib.request` (not `requests`), SOCKS5 auth requires `sockshandler`:

```python
import urllib.request, urllib.parse, ssl, socks, sockshandler

parsed = urllib.parse.urlparse('socks5://user:pass@host:port')
ctx = ssl.create_default_context()

opener = urllib.request.build_opener(
    sockshandler.SocksiPyHandler(
        socks.SOCKS5, parsed.hostname, parsed.port,
        rdns=True, username=parsed.username, password=parsed.password
    ),
    urllib.request.HTTPSHandler(context=ctx)
)

req = urllib.request.Request(url, data=body, headers=headers, method='POST')
resp = opener.open(req, timeout=15)
```

**Install:** `pip install pysocks` (provides both `socks` and `sockshandler` modules)

**Pitfall: Do NOT use `socks.set_default_proxy()` with urllib** — sets a global default that conflicts with `SocksiPyHandler()` and causes `TypeError: SocksiPyConnectionS.__init__() missing 2 required positional arguments`. Always pass proxy params directly to the constructor.

**Pitfall: `urllib.request.ProxyHandler` does NOT support SOCKS5** — only handles HTTP/HTTPS. Using `socks5://` with ProxyHandler causes `407 Proxy Authentication Required` or `Tunnel connection failed`.

### When to use which approach

| Scenario | Approach |
|----------|----------|
| `requests` library | `proxies={'http': 'socks5://user:pass@host:port'}` + pysocks |
| `urllib.request` | `sockshandler.SocksiPyHandler(socks.SOCKS5, host, port, rdns=True, ...)` |
| Playwright/Selenium | pproxy HTTP relay (see above) |
| curl | `--socks5-hostname user:pass@host:port` |

## Pitfall: Python `requests` + SOCKS5 + SSL `SSLEOFError` (2026-07-24)

Some HTTPS sites fail through Python `requests` + `pysocks` SOCKS5 proxies with:
```
SSLError SOCKSHTTPSConnectionPool(host='tikfollowers.com', port=443):
Max retries exceeded (Caused by SSLError(SSLEOFError(8, '[SSL: UNEXPECTED_EOF_WHILE_READING]')))
```

**But `curl` through the same SOCKS5 proxy works perfectly.** The issue is in how `pysocks`/`urllib3` handles TLS over SOCKS5 — it sometimes negotiates TLS incorrectly for certain server/proxy combinations.

**Workarounds (in order of preference):**
1. **Use `curl` subprocess** — most reliable:
   ```python
   import subprocess, json
   proxy = f"user:pass@host:port"
   cmd = ["curl", "-s", "--socks5-hostname", proxy, "-X", "POST", url,
          "-H", "Content-Type: application/json", "-d", json.dumps(payload)]
   result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
   data = json.loads(result.stdout)
   ```
2. **Use pproxy relay** (HTTP→SOCKS5) + `requests` through the HTTP relay — avoids the SOCKS5+TLS issue since `requests` does standard HTTPS through HTTP proxy
3. **Use `urllib3` + `sockshandler`** directly (sometimes works when `requests` wrapper doesn't)

**Sites confirmed affected:** tikfollowers.com, tikapis.com
**Sites NOT affected:** httpbin.org, tiktok.com (work fine through `requests` + SOCKS5)

## Tested Stack (2026-07-23)

Confirmed working on Windows with Python 3.11:
- `pip install pproxy pysocks requests playwright`
- pproxy relay: 15 concurrent relays on ports 18080-18094
- Playwright through relay: 15/15 successful page loads with video auto-play
- SOCKS5 residential proxies: 20/20 working (300-378KB TikTok pages)

## Rotating Residential Proxies with Change-IP API

Some proxy providers (e.g., ZingProxy/zproxy.vn) offer rotating residential proxies with on-demand IP change via HTTP API.

### Pattern: ZingProxy Change-IP
```
Proxy endpoint: socks5://user:pass@host:port  (stays constant)
Exit IP: rotates every ~20s automatically, or on-demand via API
Change-IP API: GET https://api.zingproxy.com/open/change-ip/<token>
```

**Workflow:**
1. Call change-IP API (plain HTTP, no proxy needed)
2. Wait 3-5s for new IP to stabilize on SOCKS5 endpoint
3. Verify new IP via `GET https://api.ipify.org` through the proxy
4. Use proxy for target request

**Response format:**
```json
{"status":"success","newIP":"x.x.x.x"}           // OK
{"statusCode":400,"remainingSeconds":5}            // Too fast, wait N seconds
```

**Pitfall: Don't spam change-IP API.** Rate limit is ~1 request/second. If you get `remainingSeconds`, sleep that long + 1s before retrying.

**Pitfall: Proxy exit IP ≠ device registration IP.** Even if the proxy exits from a Vietnamese IP, services like TikTok may reject requests because the `odin_tt` token was generated on a different IP/network. Rotating proxies are useful for avoiding IP-based rate limits but may NOT help with token validation.
