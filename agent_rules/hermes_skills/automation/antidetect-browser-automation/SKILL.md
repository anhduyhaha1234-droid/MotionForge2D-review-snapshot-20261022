---
name: antidetect-browser-automation
description: "Automate antidetect browsers (GPM Login Global, etc.) via their local REST APIs. Covers profile creation, browser launching, Selenium/Playwright connection, fingerprint config, and proxy assignment. Use when working with antidetect browsers for multi-account management, scraping, or social media automation."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [automation, antidetect, browser, gpm, fingerprint, multi-account]
    related: [playwright-browser-automation, socks5-proxy-automation, social-media-view-automation]
---

# Antidetect Browser Automation

## Overview

Antidetect browsers (GPM Login, Multilogin, GoLogin, etc.) run isolated browser profiles with unique fingerprints. Each profile has its own cookies, localStorage, canvas/webgl noise, user-agent, and proxy. The local REST API lets you programmatically create profiles, launch browsers, and connect via Selenium/Playwright for automation.

## When to Use

- Multi-account management (social media, e-commerce)
- Automation that needs unique fingerprints per session
- Scraping with proxy rotation per browser profile
- TikTok/social media view automation (each profile = unique identity)

## General Workflow

```
1. Create profile via API (set proxy, fingerprint, browser version)
2. Start browser → get debug_port
3. Connect Selenium/Playwright to debugger_address = 127.0.0.1:{debug_port}
4. Automate (navigate, fill forms, extract data)
5. Stop browser via API
6. (Optional) Delete or reuse profile
```

## Key Principles

### Selenium Connection Pattern
```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.debugger_address = f'127.0.0.1:{debug_port}'  # from start API response
driver = webdriver.Chrome(options=options)
# OR with custom service (GPM provides its own driver):
service = Service(executable_path=gpmdriver_path)
driver = webdriver.Chrome(service=service, options=options)
```

### CDP Direct Connection — AVOID
Direct Chrome DevTools Protocol WebSocket connections get **403 Forbidden** due to `--remote-allow-origins` restriction. Always use Selenium or Playwright instead of raw CDP websocket.

### navigator.webdriver Detection
Antidetect browsers patch `navigator.webdriver` to return `false`. Verify after connecting:
```python
assert driver.execute_script('return navigator.webdriver') == False
```

### Profile Lifecycle
- **Create** → returns profile_id + fingerprint data
- **Start** → returns debug_port + driver_path + process_id
- **Connect** → use debug_port with Selenium/Playwright
- **Stop** → kills the browser process (does NOT delete the profile)
- **Delete** → soft-deletes (may still appear in list; check is_deleted flag)

### Proxy Assignment
Set proxy at profile creation time:
```json
{"name": "...", "raw_proxy": "socks5://user:pass@host:port"}
```
Supported formats: `http://`, `socks5://`, `socks5://user:pass@host:port`

### Fingerprint Settings
All fingerprint modes accept integer enums or string names:
- canvas_mode: 1=Noise, 2=Real, 3=Block
- webgl_image_mode: 1=Noise, 2=Real
- webgl_metadata_mode: 1=Masked, 2=Real
- audio_mode: 1=Noise, 2=Real
- webrtc_mode: 1=BasedOnIP, 2=Fixed, 3=Real, 4=Disabled
- font_mode: 1=Masked, 2=Real
- os_type: 1=Windows, 2=macOS Intel, 3=macOS ARM, 4=Linux, 5=Android

## Pitfalls

1. **API port ≠ config port.** The config file may show one port but the API listens on another. Check the docs for the default (e.g., GPM defaults to 9495). Use `netstat -ano | grep LISTENING` to find the real port.

2. **WebSocket ports ≠ REST API ports.** Antidetect browsers often have a WebSocket port for UI communication and a separate HTTP port for the API. Don't confuse them.

3. **CDP 403 Forbidden.** Direct WebSocket connections to Chrome's debug port are blocked by origin restrictions. Use Selenium/Playwright instead.

4. **driver.quit() ≠ browser close.** Calling `driver.quit()` in Selenium may close the WebDriver session but leave the browser running. Use the API's stop endpoint to properly close.

5. **Soft delete.** Profile deletion via API may be soft-delete (sets is_deleted flag). The profile may still appear in list endpoints. Filter by `is_deleted` field.

6. **Debug port is per-profile.** Each profile start gets a random debug port (typically in 50000-65000 range). Always read it from the start response.

7. **Browser version download.** First use of a browser version may trigger download. Allow extra time on first profile start with a new version.

8. **Port protection.** GPM auto-sets port_protect to block scanning of common ports (3389, 5900, 9495, 9496). This is normal fingerprint protection.

9. **Chrome Cookies DB locked while running.** Copying `Network/Cookies` while Chrome is open produces an empty SQLite file (no tables). Use `History` and `Login Data` instead — they copy fine. Cookies are only queryable when the browser is fully closed. See `references/chrome-profile-inspection.md`.

## Browser-Specific References

- GPM Login Global: See `references/gpm-login-api.md` for complete API endpoints and examples
- Chrome/Chromium Profile Inspection: See `references/chrome-profile-inspection.md` for finding profiles on disk, querying cookies/history/login data with Python sqlite3, and working around Chrome's Cookie DB locking

## Inspection: Finding Existing Profiles & Sessions

When you need to check if a site is already logged in across browser profiles on the machine:
1. Enumerate profiles under Chrome User Data, GPM install path, Edge, etc.
2. Copy `History` DB (not Cookies — it's locked while browser runs) and query for authenticated URLs
3. Check `Login Data` for saved credentials (note: OAuth logins won't have saved passwords)
4. See `references/chrome-profile-inspection.md` for the full workflow and Python code

### P10: Chrome Profile Lock Blocks Selenium/Playwright/CDP

When trying to automate an **existing Chrome profile** (Profile 3, Default, etc.) that already has logged-in sessions:

**Problem:** Selenium, Playwright, and CDP all fail to connect to the default Chrome User Data directory because:
1. Chrome's `--remote-debugging-port` requires `--user-data-dir` to be explicitly specified
2. Using the default `C:\Users\<user>\AppData\Local\Google\Chrome\User Data` as `--user-data-dir` conflicts with Chrome's profile locking
3. Selenium/Playwright launch Chrome as a child process, but Chrome detects the existing profile lock and crashes with `DevToolsActivePort file doesn't exist`
4. Force-killing Chrome leaves `SingletonLock`, `SingletonSocket`, `SingletonCookie` files that prevent new launches
5. Copying the profile directory does NOT preserve cookies — they're encrypted with Windows DPAPI tied to the original profile path

**Failed approaches:**
- `launch_persistent_context(user_data_dir=..., profile_directory="Profile 3")` → TargetClosedError
- `webdriver.Chrome(options.add_argument('--user-data-dir=...'))` → SessionNotCreatedException
- `chrome --remote-debugging-port=9222 --user-data-dir=<default>` → port never opens
- Copy profile to temp dir → cookies are empty (DPAPI encryption)
- Connect via CDP to existing Chrome → port not available without `--remote-debugging-port`

**What works:**
1. **Use GPM Login API** — launch profile via REST API, get debug_port, connect Selenium/Playwright
2. **Use the Gumroad/similar API directly** — if the platform has an API with access tokens, use that instead of browser automation
3. **Manual login + automation** — ask user to open Chrome and log in, then use `pyautogui` or `win32com` for desktop automation (not browser automation)
4. **Clean restart approach:**
   ```python
   # 1. Kill all Chrome
   # 2. Remove lock files
   import os
   for f in ['SingletonLock', 'SingletonSocket', 'SingletonCookie']:
       try: os.remove(f'C:/Users/Admin/AppData/Local/Google/Chrome/User Data/Profile 3/{f}')
       except: pass
   # 3. Launch Chrome with Selenium (fresh start, no existing lock)
   driver = webdriver.Chrome(options=opts)
   ```
   This works IF Chrome was fully closed first AND lock files are cleaned.

**Best practice:** For platforms with APIs (Gumroad, Shopify, etc.), always prefer the API over browser automation. Reserve browser automation for platforms without APIs.

## Integration with Other Skills

- **socks5-proxy-automation**: Use for proxy pool management before assigning to profiles
- **playwright-browser-automation**: Can connect Playwright to antidetect browser debug ports
- **social-media-view-automation**: Each profile = unique viewer identity
