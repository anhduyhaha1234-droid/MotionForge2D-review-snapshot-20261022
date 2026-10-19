# MITM Capture System Architecture

**Location:** `C:\Users\Admin\ttsigning\mitm_capture\`  
**Built:** 2026-07-25  
**Purpose:** Automated capture of real TikTok device profiles via mitmproxy traffic interception.

## Problem It Solves

Locally-generated profiles (`generate_profiles.py`) produce 128-char odin_tt via `sha512(...)[:128]`. These work with the full header stack but are not identical to the 160-char native SDK value. The mitm_capture system intercepts real TikTok traffic to extract genuine server-validated profiles.

## Architecture

```
Android Device/Emulator
  → HTTP proxy (settings put global http_proxy HOST:PORT)
    → mitmproxy (port 8080, with ttk_interceptor.py addon)
      → HTTPS decrypted (CA cert trusted on device)
        → Interceptor extracts: device_id, install_id, odin_tt, cookies, headers, params
          → Auto-exports JSON profiles to captured/
            → profile_converter.py validates + converts to api_framework.py format
```

## Key Design Decisions

1. **mitmproxy addon pattern** (not standalone script): The addon runs inside mitmproxy's event loop, getting `request()` and `response()` callbacks for every intercepted flow. This avoids reimplementing TLS/proxy handling.

2. **Per-connection state**: Each device's traffic is tracked separately via `id(flow.connection)`. This associates device_register responses with subsequent API requests from the same device.

3. **odin_tt extraction priority**: Set-Cookie headers from responses > Cookie headers from requests. The interceptor checks both.

4. **Auto-export with dedup**: Profiles are exported when sufficient data is accumulated (confidence >= 3). Dedup by device_id prevents duplicate exports for the same connection.

5. **Template deep-merge**: `profile_converter.py` deep-merges captured data with the reference template (`device_v44_3_1.json`) to fill any fields that weren't present in the captured traffic (e.g., guard_keys if no guard headers were observed).

## Profile Validation Rules

The converter checks:
- All 9 required sections present (meta, device, app, network, locale, session, user_agent, guard_keys, guard_headers)
- device_id is numeric and >= 10 digits
- odin_tt present in cookie string
- odin_tt length >= 128 chars (real server values are 128-160)
- user_agent contains "musically"
- EC P-256 guard keys exist (generates if missing)

## Common Pitfalls

1. **HTTPS interception requires CA cert**: Without `android_setup.py --install-cert`, mitmproxy can only see CONNECT tunnel headers, not decrypted content. The test with plain `urllib` through the proxy got 200 OK but no intercepted data because the client didn't trust the mitmproxy CA.

2. **Android 14+ cert install is manual**: The `am start` intent approach may not work on Android 14+. Users must navigate to Settings > Security > Install certificate manually, or use the `android.credentials.INSTALL` intent which opens a dialog.

3. **Emulator proxy host is 10.0.2.2**: Android emulators use NAT networking. The host machine's loopback is `10.0.2.2` from inside the emulator. Physical devices need the host's LAN IP.

4. **mitmproxy stdout doesn't show addon logs by default**: The interceptor's `ctx.log.info()` messages appear in mitmproxy's console but may be filtered. Use `--set verbose=true` and check the `captured/capture_summary.json` file for statistics.

5. **TikTok certificate pinning**: On some versions, TikTok uses certificate pinning that prevents mitmproxy interception even with CA cert installed. The MITM approach works best with older TikTok versions or when pinning is not enforced. If pinning is active, Frida/objection bypass is needed first.

## Tested Configuration

- mitmproxy 11.0.2 (pip install mitmproxy)
- Python 3.11.9 on Windows 10
- TikTok v44.3.15 Android
- JDK 21 (Eclipse Adoptium Temurin) for device registration
- ADB from Android SDK Platform Tools
