# MITM Capture System for TikTok Session Tokens

## Overview

Automated system for capturing TikTok session tokens (odin_tt, session_key, x_tt_token, device_id, install_id, msToken, guard keys) from real TikTok app instances.

## Architecture

```
mitm_capture/
├── ttk_interceptor.py      # mitmproxy addon - intercepts TikTok traffic
├── batch_capture.py        # Batch capture from multiple devices
├── profile_converter.py    # Convert captured data → profile JSON
├── emulator_quickstart.py  # Redroid emulator setup
└── captured/               # Output directory for captured sessions
```

## Components

### 1. ttk_interceptor.py (mitmproxy addon)
- Intercepts TikTok API traffic
- Extracts session tokens from Set-Cookie headers
- Parses device_register responses
- Saves captured sessions as JSON

### 2. batch_capture.py
- Orchestrates multiple capture sessions
- Manages proxy rotation
- Deduplicates captured profiles

### 3. profile_converter.py
- Converts captured data to api_framework.py compatible format
- Validates all required fields
- Merges with fixture profile template

## Usage

```bash
# Start mitmproxy with interceptor
mitmdump -s ttk_interceptor.py -p 8099

# Configure device proxy
# Android: Settings → WiFi → Proxy → Manual → host: 8099

# Capture sessions
# Open TikTok app → browse → interceptor saves tokens

# Convert to profile
python profile_converter.py captured/session.json
```

## Key Findings

1. **odin_tt is client-generated** — NOT in Set-Cookie headers
2. **ttwid + msToken ARE in Set-Cookie** — from web endpoints
3. **Certificate pinning blocks HTTPS** — need Frida/objection bypass
4. **Device registration returns device_id + install_id** — but odin_tt must come from app

## Blockers

- **TikTok certificate pinning** — mitmproxy can't decrypt TLS without bypass
- **Frida required** — must hook SSL context on rooted device/emulator
- **Redroid needs Linux** — binder_linux kernel module required

## Verified Results

- mitmproxy addon: 7/7 unit tests passed
- Cookie parsing: ttwid, msToken, odin_tt extraction working
- Profile conversion: schema validation passing
