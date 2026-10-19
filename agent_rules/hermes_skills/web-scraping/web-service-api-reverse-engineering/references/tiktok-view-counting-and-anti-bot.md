# TikTok View Counting Mechanism & Anti-Bot Research
## Last updated: 2026-07-25

## How TikTok Counts a View

### Core Rule
- **~1 second of playback** = 1 view for videos under 3 minutes
- For videos 3+ minutes, threshold is ~3 seconds
- **Muted plays count. Paused plays count. Autoplayed counts.**
- Your own views on your own videos do NOT count
- **Replays/loops DO count** — each loop adds a new view (no official cap)
- Rapid consecutive replays from same user may be discounted (anecdotal)
- Views from external links/embeds count as long as video actually plays
- View counts update in near real-time

### Key Implication
The ~1 second threshold means TikTok is inherently more vulnerable than YouTube (30 sec) or Instagram (3 sec). The view count increments **client-side** when video playback begins.

## 5 Anti-Bot Detection Layers

### Layer 1: VM-Based Request Signing
- TikTok uses a **stack-based JavaScript Virtual Machine with 77 opcodes** for request signing
- VM generates signed parameters (`as`, `cp`, `mas`) that must accompany API requests
- Bytecode and obfuscation are regularly updated (every few weeks)
- Similar to Google's BotGuard system
- **You CANNOT simply replay HTTP requests** — must either reverse-engineer the VM or run actual browser/app instances

### Layer 2: Device Fingerprinting
Required device parameters:
```
device_id, install_id, openudid, cdid (UUID), device_brand, device_type,
os_api, os_version, resolution, dpi, carrier_region_v2, mcc_mnc, host_abi
```
Required headers:
```
User-Agent: com.zhiliaoapp.musically/<version> (Linux; U; Android <ver>; ...)
passport-sdk-version: 19
sdk-version: 2
x-ss-req-ticket: <timestamp>
x-tt-store-region: <country>
x-vc-bdturing-sdk-version: 2.2.1.i18n
Cookie: install_id=<iid>; store-country-code=<cc>; store-idc=<idc>; ttreq=1$<hash>
```
Emulated devices and headless browsers produce detectable fingerprints.

### Layer 3: Behavioral Analysis
- Real users have complex viewing patterns (scroll, pause, rewatch, skip)
- Bot traffic shows mechanically uniform patterns
- Session duration, scroll behavior, interaction sequences analyzed

### Layer 4: IP Reputation Scoring
- TikTok maintains databases of IPs associated with bot traffic, VPNs, datacenter proxies
- Even residential proxies get flagged when single IP generates unusual volume
- Rate limiting per IP exists but exact thresholds unknown

### Layer 5: Engagement Correlation
- Views must correlate with other engagement signals
- 50K views with zero comments/shares and 0.5 sec avg watch time = anomalous
- TikTok removed 348+ million fake accounts in Q3 2024

## What Won't Work
1. **Simple HTTP requests to TikTok endpoints** — blocked by VM-based signing
2. **Headless browser automation from datacenter IPs** — fingerprinting + IP reputation detect it
3. **Datacenter proxies** — IP reputation scoring blocks them
4. **Replaying captured requests** — signatures change frequently
5. **Calling play endpoint without proper signing** — returns HTTP 400 "Invalid parameters"

## What Might Work (with limitations)
1. **Residential SOCKS5 proxies + real device emulation** — better than datacenter but still detectable
2. **Third-party services like Zefoy** — they handle anti-bot bypass, but rate-limited
3. **Mobile emulators with good fingerprinting** — requires passing TikTok's device fingerprint checks
4. **tls_client library** — can mimic mobile app TLS fingerprint (got HTTP 200 on video page)
5. **Real device farms with actual TikTok app** — most effective but requires physical hardware

## Minimum Requirements for a View to Count
1. Valid TikTok request with proper signing (VM-generated `as`, `cp`, `mas` parameters)
2. Unique device fingerprint (device_id + install_id combination)
3. Request from an IP that isn't flagged
4. Video actually "playing" (client reports playback event)
5. ~1 second of reported playback time

## Rate Limits (estimated)
- Zefoy enforces ~60-120 second cooldowns between sends
- Rapid repeated views from same device/IP likely get filtered
- Residential proxies help but don't guarantee success

---

## Zefoy.com Mechanism

### How Zefoy Works
Zefoy is an intermediary — it does NOT call TikTok's API from the user's machine:
1. User solves image captcha on zefoy.com
2. User provides video URL
3. Zefoy's servers handle the actual view sending (unknown method)
4. Communication uses base64-encoded, reversed string responses
5. Rate limited: ~every 60-120 seconds per submission

### Response Decoding (from xtekky bot source)
```javascript
// Response is base64 encoded and reversed
$("#" + hrefaction).html(atob(decodeURIComponent(response.split("").reverse().join(""))));
```

### Captcha
- Image-based captcha (not reCAPTCHA)
- Served at `/<hash>.php?_CAPTCHA=<token>&t=<timestamp>`
- Hidden input: `captcha_encoded` (encrypted JSON with `ct` field)
- Input name: `captchalogin`
- ddddocr (Chinese OCR library) returns empty or wrong characters — captcha is too distorted
- platipus9999.pythonanywhere.com (captcha solver from xtekky bot) is DOWN ("Coming Soon")

### Service Buttons (XPath from xtekky bot)
```
followers:      /html/body/div[6]/div/div[2]/div/div/div[2]/div/button
hearts:         /html/body/div[6]/div/div[2]/div/div/div[3]/div/button
comment_hearts: /html/body/div[6]/div/div[2]/div/div/div[4]/div/button
views:          /html/body/div[6]/div/div[2]/div/div/div[5]/div/button
shares:         /html/body/div[6]/div/div[2]/div/div/div[6]/div/button
favorites:      /html/body/div[6]/div/div[2]/div/div/div[7]/div/button
```

---

## Signing Libraries & Constants

### douyin-sign (GitHub: 7452323/douyin-sign)
- Pure Python, updated 2026-07-23, ★10
- Supports: X-Gorgon, X-Argus, X-Ladon, X-Khronos, X-SS-STUB, X-Bogus, TTEncrypt
- Has `proxy.py` (FastAPI signing proxy server)
- Has `device.py` (Device class + register_device)
- Has `update.py` (auto-extract constants from APK)
- **WORKS for Douyin (api.douyin.com)**
- **DOES NOT WORK for TikTok (api-h2.tiktokv.com)** — signing constants are different

### Why Constants Differ
- Douyin (Chinese app, aid=1128) and TikTok (international, aid=1233) use same ALGORITHM but different SIGNING KEYS
- Constants are stored in `constants/current/`:
  - `sign_key.b64` — Base64-encoded signing key (44 bytes)
  - `gorgon_table.hex` — Hex lookup table (20 bytes)
  - `protobuf_fields.json` — Protobuf field mapping
- Current constants are from Douyin APK (not TikTok)

### TikTok APK Constants Extraction Attempt
- Downloaded TikTok APK (581MB) from apkpure
- Extracted `lib/arm64-v8a/libmetasec_ov.so` (2MB)
- **Constants are OBFUSCATED** — no 44-char base64 or 40-char hex patterns found
- Found X-Gorgon/X-Argus/X-Ladon header names in `classes10.dex` but not the signing keys
- The keys are likely embedded in the native library with custom encoding
- Would need Ghidra/IDA Pro reverse engineering or Frida hooking on real device

### X-Gorgon Algorithm (from douyin-sign)
```
1. MD5 hash of query params → 32 hex chars
2. MD5 hash of request body → 32 hex chars (or 0*32 if empty)
3. MD5 hash of cookies → 32 hex chars (or 0*32 if empty)
4. Append 0*32
5. Concatenate → 128 hex char gorgon string
6. Extract 16 bytes from gorgon (4 groups of 8 hex chars → 4 bytes each)
7. Append [0x0, 0x6, 0xB, 0x1C] + 4 timestamp bytes
8. XOR with 20-byte key from constants
9. Custom bit manipulation (reverse, rbit, XOR with length)
10. Result: "0404b0d30000" + 40 hex chars
```

### tls_client for TLS Fingerprint Mimicry
```python
import tls_client
session = tls_client.Session(client_identifier='tiktok_android_38', random_tls_extension_order=True)
resp = session.get('https://www.tiktok.com/@user/video/123', headers={...})
# Returns HTTP 200 with 371KB (SSR page with __UNIVERSAL_DATA_FOR_REHYDRATION__ JSON)
```
- Successfully gets TikTok video pages with proper TLS fingerprint
- SSR data contains `webapp.app-context`, `webapp.biz-context`, strategy configs
- Does NOT contain video stats (loaded dynamically via JS)
- SOCKS5 proxy not supported by tls_client
- Does NOT trigger view counting (just fetches HTML)

---

## GitHub Repos for TikTok Reverse Engineering

| Repo | Stars | What it does | Status |
|------|-------|-------------|--------|
| 7452323/douyin-sign | 10 | All-in-one signing (X-Gorgon/Argus/Ladon/Bogus) | Works for Douyin, not TikTok |
| notemrovsky/tiktok-reverse-engineering | ? | VM reverse engineering (77 opcodes mapped) | Research only |
| scrapguru/tiktok-device-registration | ? | Device parameter generation | Reference |
| SebastienWae/tiktok-register | ? | Device registration + device list | Reference |
| szdc/tiktok-api | 1,291 | Older TikTok API wrapper (Node.js) | Deprecated |
| davidteather/TikTok-Api | 6,513 | Python TikTok API wrapper (Playwright-based) | Data API, not manipulation |
| HkerVit/TikTok-Private-API | 50 | Follow, like, X-Gorgon support | Old signing (v19.1.3) |
| xtekky/TikTok-ViewBot | 1,848 | Zefoy-based Selenium bot | Works but needs captcha |
| tikapiscom/TikTok-Private-Api-TikApis.com | 15 | tikapis.com SDK | Service DOWN |
