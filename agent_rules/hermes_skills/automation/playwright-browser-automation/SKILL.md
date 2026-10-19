---
name: playwright-browser-automation
description: "Desktop Playwright browser automation with proxy rotation, fingerprint randomization, and multi-session workflows. Covers setup, proxy testing patterns, browser context isolation, and common failure modes. Use when user wants headless browser automation, web scraping with rotating proxies, view simulation, or multi-session browser workflows on Windows/Linux/Mac."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [automation, browser, playwright, selenium, proxy, scraping, headless]
    related: [damru-setup, terminal-engineering-discipline]
---

# Playwright Desktop Browser Automation

## When to Use

- Headless browser automation with proxy rotation
- Multi-session workflows requiring unique fingerprints per session
- Web scraping that needs JS rendering (SPA sites, video platforms)
- View/traffic simulation with proxy rotation
- Any task needing isolated browser contexts with randomized fingerprints

## Setup (Windows)

```bash
pip install playwright
python -m playwright install chromium
```

Verify:
```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page()
    page.goto("https://example.com")
    print(page.title())
    b.close()
```

**PITFALL:** `playwright install chromium` downloads browser binaries to `%LOCALAPPDATA%\ms-playwright\`. On Windows this is `C:\Users\<user>\AppData\Local\ms-playwright\`. Disk space required: ~300MB.

## Core Pattern: Proxy Rotation with Fingerprint Randomization

```python
from playwright.sync_api import sync_playwright
import random, time

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

LOCALES = ["en-US", "en-GB", "en-AU", "en-CA", "de-DE", "fr-FR"]
TIMEZONES = ["America/New_York", "America/Chicago", "Europe/London", "Asia/Tokyo", "Australia/Sydney"]

def run_session(pw, target_url, proxy=None):
    """Single browser session with randomized fingerprint."""
    launch_args = {"headless": True}
    if proxy:
        launch_args["proxy"] = {
            "server": proxy["server"],      # "http://host:port"
            "username": proxy["username"],
            "password": proxy["password"],
        }

    browser = pw.chromium.launch(**launch_args)
    context = browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        viewport={"width": random.randint(1280, 1920), "height": random.randint(720, 1080)},
        locale=random.choice(LOCALES),
        timezone_id=random.choice(TIMEZONES),
    )
    page = context.new_page()
    page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
    # ... do work ...
    browser.close()
```

**Key design decisions:**
- **Fresh browser per session** (not just new page) — prevents cookie/state leakage
- **Context-level fingerprint** — UA, viewport, locale, timezone set per context, not per page
- **`domcontentloaded`** not `networkidle` — faster, works for JS-heavy sites that keep connections open

## Proxy Handling

### Proxy Format

Playwright expects HTTP CONNECT proxies in this format:
```python
{"server": "http://host:port", "username": "user", "password": "pass"}
```

SOCKS5 proxies:
```python
{"server": "socks5://host:port", "username": "user", "password": "pass"}
```

**PITFALL:** Playwright does NOT support SOCKS4. Use SOCKS5 or HTTP CONNECT only.

### Loading Proxies from File

Common format: `host:port:username:password` (one per line):
```python
def load_proxies(filepath):
    proxies = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(":")
            if len(parts) == 4:
                host, port, user, pwd = parts
                proxies.append({
                    "server": f"http://{host}:{port}",
                    "username": user,
                    "password": pwd,
                    "label": f"{host}:{port}",  # for logging
                })
    return proxies
```

### ALWAYS Test Proxies First

**CRITICAL:** Never assume proxies work. Always run a connectivity test before the main loop:

```python
def test_proxies(pw, proxies, test_url="https://httpbin.org/ip"):
    working = []
    for proxy in proxies[:5]:  # Test first 5
        try:
            browser = pw.chromium.launch(headless=True, proxy={
                "server": proxy["server"],
                "username": proxy["username"],
                "password": proxy["password"],
            })
            page = browser.new_page()
            page.goto(test_url, timeout=10000)
            time.sleep(1)
            browser.close()
            working.append(proxy)
        except Exception as e:
            try: browser.close()
            except: pass
            print(f"Proxy {proxy['label']} failed: {str(e)[:80]}")
    return working
```

**PITFALL:** Dead proxies return `net::ERR_EMPTY_RESPONSE` (instant failure), not timeouts. If all proxies fail with this error, they are completely unresponsive — the proxy service is down, not just slow.

**PITFALL:** Even if proxies pass connectivity test with httpbin, they may still be blocked by target sites (TikTok, Cloudflare, etc.). Always have a fallback plan for direct connections.

## Error Handling Pattern

```python
def safe_session(pw, url, proxy):
    browser = None
    try:
        browser = pw.chromium.launch(headless=True, proxy=proxy)
        context = browser.new_context(...)
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # ... work ...
        return True, None
    except Exception as e:
        return False, str(e)[:150]
    finally:
        if browser:
            try: browser.close()
            except: pass
```

**PITFALL:** Always close browser in `finally` block. Orphaned Chromium processes accumulate and consume memory. Each headless Chromium uses ~100-200MB.

## TikTok Video Auto-Play

TikTok auto-plays videos on page load. Workflow:
1. `page.goto(video_url, wait_until="domcontentloaded")`
2. Wait 5-15s for video buffer + playback
3. Verify with `page.query_selector("video")` — returns element if video player loaded
4. Optional: simulate mouse movement for engagement signal

```python
# TikTok view verification
page.goto(tiktok_url, wait_until="domcontentloaded", timeout=30000)
time.sleep(random.uniform(6, 15))  # let video play
video_el = page.query_selector("video")
view_registered = video_el is not None
```

## Anti-Detection Tips

| Technique | Implementation |
|-----------|---------------|
| Randomize viewport | `viewport={"width": rand(1280,1920), "height": rand(720,1080)}` |
| Rotate user agents | Pick from a pool of real, current UA strings |
| Match locale/timezone to proxy geo | US proxy → en-US + America/New_York |
| Random wait times | `time.sleep(random.uniform(min, max))` |
| Mouse movements | `page.mouse.move(rand_x, rand_y)` before closing |
| Fresh browser per session | Prevents cookie/state fingerprinting |
| Block heavy resources | Use `page.route("**/*.{png,jpg,gif,woff,woff2}", lambda route: route.abort())` to speed up |

## Common Pitfalls

1. **Proxy format wrong** — Must be `http://host:port` or `socks5://host:port`, not bare `host:port`
2. **Not testing proxies first** — Always run connectivity test before main loop
3. **Reusing browser across sessions** — Cookies/fingerprints leak; use fresh browser per session
4. **Using `networkidle` wait** — Hangs on sites with persistent connections; use `domcontentloaded`
5. **Not closing browsers** — Orphaned Chromium processes consume memory
6. **Same IP = deduplicated views** — Without unique IPs per session, target sites deduplicate
7. **Datacenter proxies flagged** — Major platforms (TikTok, Google) flag datacenter IPs; residential proxies needed for real view counting
8. **View velocity detection** — Sending too many views too fast from same IP range triggers rate limiting
9. **Playwright `timeout` default is 30s** — Set explicitly for slow connections: `page.goto(url, timeout=60000)`
10. **Windows path handling** — Use forward slashes or raw strings for file paths in Playwright on Windows
11. **Chrome profile lock conflict** — `launch_persistent_context` with `channel="chrome"` and an existing Chrome User Data dir will crash if Chrome is already running with that profile. The profile directory is locked by the running Chrome process. Workarounds:
    - `taskkill -F -IM chrome.exe` BEFORE launching Playwright (kill ALL Chrome processes)
    - Copy the profile to a temp dir — BUT cookies encrypted with DPAPI (Windows) won't decrypt in the copy, so authenticated sessions are lost
    - Use `--remote-debugging-port=9222` on the running Chrome (requires BOTH `--user-data-dir` AND `--profile-directory` flags), then connect via `p.chromium.connect_over_cdp("http://localhost:9222")` — this is the only way to reuse an existing authenticated session
    - **Selenium alternative:** `webdriver.Chrome(options=opts)` with `--user-data-dir` also hits the same lock. Same kill-first-or-use-CDP constraint applies.
12. **DPAPI cookie encryption on Windows** — Chrome cookies in `Profile N/Network/Cookies` are encrypted with Windows DPAPI. Copying the SQLite DB to another machine or a temp dir produces empty values. The only way to use authenticated cookies is to launch Chrome with the original profile (kill first or CDP).

## References

- `references/tiktok-view-bot-notes.md` — TikTok-specific automation details and results
- `templates/tiktok_view_bot.py` — Working Playwright view bot template with proxy rotation
