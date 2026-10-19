# Trichrome Library Install Investigation (2026-07-25)

## Problem
Chrome on Redroid requires the trichrome library package (`com.google.android.trichromelibrary`) which contains `libmonochrome_64.so` (~220-240MB). Without it, Chrome activities fail with "Activity class does not exist".

## All Methods Tried (ALL FAILED)

| Method | Result |
|--------|--------|
| `adb install -r -d google_trichrome_library.apk` | Broken pipe (32) |
| `adb install-multiple -r -d ...` | Broken pipe (32) |
| `pm install-create` + `pm install-write` + `pm install-commit` | StorageManager NullPointerException |
| `python -m damru bake-image --chrome-apk 148.0.7778.217` | Broken pipe (32) during `install_chrome()` |
| `python -m damru install-image --download` (fresh) | Image loaded but trichrome NOT present |
| Push `.so` files to Chrome's `lib/x86_64/` | Invisible — `extractNativeLibs=false` means linker reads from APK only |

## Root Cause
Redroid's PackageManager has a ~200MB buffer limit for APK installation. The trichrome library APK is 213-255MB across all Chrome versions (143-148). This is a Redroid bug, not a Damru bug.

## Trichrome Sizes
| Chrome Version | google_trichrome_library.apk |
|---------------|------------------------------|
| 143.0.7499.52 | 213 MB |
| 144-148 | 213-237 MB |
| vanadium (143) | 243 MB |

## Fallback Options
1. **Desktop Playwright** — Chromium runs natively, no trichrome needed. Loses Android fingerprint but works for web automation.
2. **Real Android device via ADB** — Chrome pre-installed, no trichrome issue. Use `adb -s <device-ip:port>` to connect.
3. **Native Ubuntu VPS** — Damru on bare metal may handle bake-image differently (not Docker-in-WSL).

## Account-Based TikTok View Approach
When Chrome works, the flow for account-based views:
1. Each Damru session = unique proxy + device profile + fresh Chrome
2. Inject cookies via CDP (Playwright `context.add_cookies()`) for Hotmail/Outlook login
3. Navigate to TikTok, dismiss FRE + popups via uiautomator
4. Watch video 30+ seconds with human-like interactions (tap, scroll, mouse move)
5. Verify view count change via curl to TikTok page (extract `playCount` from HTML)

## ProxyVT SOCKS5 Configuration
Format: `socks5://u_USER_RNHC3R:EUZI7ZHGNnvm@dc-vn24.proxyvt.com:PORT`
Each port = unique sticky IP. 108 ports available. Works with TikTok (HTTP 200, 300KB+ response).
Note: httpbin.org returns 503 through these proxies — always test against actual target.
