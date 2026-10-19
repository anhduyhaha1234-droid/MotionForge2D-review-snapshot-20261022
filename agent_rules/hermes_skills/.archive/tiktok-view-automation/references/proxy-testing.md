# Tested Proxy Formats

## SOCKS5 with Auth (IP:port:user:pass)
```
9.142.194.87:6755:ftrtntvd:vmk0vpwq6u8w
216.170.122.82:6120:ftrtntvd:vmk0vpwq6u8w
```

## curl Testing (CORRECT - use actual target)
```bash
curl -s --socks5-hostname "user:pass@host:port" --max-time 15 \
  "https://www.tiktok.com/@user/video/ID" \
  -w "CODE:%{http_code} SIZE:%{size_download}"
```

## Python requests with SOCKS5
```python
import requests
proxy_url = f'socks5://{user}:{pw}@{host}:{port}'
r = requests.get(url, proxies={'http': proxy_url, 'https': proxy_url}, timeout=20)
```

## pproxy HTTP Relay (for browsers)
```bash
# Install
pip install pproxy

# Start relay (hash # for auth separator)
python -m pproxy -l http://0.0.0.0:18080 -r 'socks5://host:port#user:pass'

# Use in Playwright
browser = p.chromium.launch(proxy={'server': 'http://127.0.0.1:18080'})
```

## WRONG Approaches
- `curl --socks5-hostname ... https://httpbin.org/ip` → httpbin blocked
- Chrome `--proxy-server=socks5://user:pass@host:port` → SOCKS5 auth not supported
- Playwright `proxy={'server': 'socks5://host:port', 'username': user, 'password': pw}` → Error: Browser does not support socks5 proxy auth
