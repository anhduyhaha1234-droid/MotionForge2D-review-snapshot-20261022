# TikTok device_register — Deep Technical Reference

## Endpoint

```
POST https://log-va.tiktokv.com/service/2/device_register/
Content-Type: application/octet-stream;tt-data=b
```

Body is **gzip-compressed** JSON. X-SS-STUB is MD5 of **uncompressed** body.

## Request Body Structure

```json
{
    "magic_tag": "ss_app_log",
    "header": {
        "display_name": "TikTok",
        "update_version_code": "440315",
        "manifest_version_code": "440315",
        "app_version_minor": "",
        "aid": 1233,
        "channel": "googleplay",
        "package": "com.zhiliaoapp.musically",
        "app_version": "44.3.15",
        "version_code": 440315,
        "sdk_version": "2.12.1-rc.6",
        "git_hash": "<from APK>",
        "os": "Android",
        "os_version": "11",
        "os_api": 30,
        "device_model": "SM-G991B",
        "device_brand": "samsung",
        "cpu_abi": "arm64-v8a",
        "release_build": "<from APK>",
        "density_dpi": 420,
        "display_density": "xxhdpi",
        "resolution": "1080x2400",
        "language": "vi",
        "timezone": 7,
        "access": "wifi",
        "carrier": "Android",
        "mcc_mnc": "45204",
        "rom": "<random>",
        "rom_version": "...",
        "cdid": "<random UUID-like>",
        "sig_hash": "<MD5 of APK signature block>",
        "gaid_limited": 0,
        "google_aid": "<random>",
        "openudid": "<random hex>",
        "clientudid": "<random UUID>",
        "region": "VN",
        "tz_name": "Asia/Ho_Chi_Minh",
        "tz_offset": 25200,
        "sim_region": "VN"
    },
    "_gen_time": 1721800000000
}
```

## sig_hash Extraction

**Location in code**: `ttk/tiktok_apk_sig.py` (code-root/tiktok-android-signing-toolkit)

**Algorithm** (from JADX class `C938760aXG.LIZLLL`):
1. Open APK as zip
2. Find first file matching `META-INF/*.RSA` or `*.DSA` or `*.EC`
3. Read raw PKCS#7 signature block bytes
4. `sig_hash = md5(raw_bytes).hexdigest()` → 32-char hex

**For .apkm files** (APKMirror bundles): extract `base.apk` from inside, then compute. Do NOT use outer `META-INF/APKMIRRO.RSA` — that's the installer's signature, not the app's.

**Can also be extracted from APK directly**:
```bash
# Python
python3 -c "
import zipfile, hashlib
with zipfile.ZipFile('tiktok.apk') as z:
    for n in sorted(z.namelist()):
        if n.startswith('META-INF/') and n.endswith(('.RSA','.DSA','.EC')):
            print(hashlib.md5(z.read(n)).hexdigest())
            break
"
```

## git_hash + release_build Extraction

These come from the APK's `AndroidManifest.xml` or Java constants (JADX classes `C938760aXG` and `C938780aXI`). In practice:
- `git_hash`: 10-char hex string from the manifest metadata
- `release_build`: formatted as `{git_hash}_{timestamp}` or similar

**Best approach**: Use JADX to decompile the APK and search for the hardcoded values.

## TTEncrypt (Post-2024 Requirement)

TikTok added ttEncrypt encryption to the device_register POST body. The raw JSON above must be encrypted with this algorithm before sending.

**Status**: Algorithm is NOT public. Sold privately via Telegram `@xtekky`.

**Bypass**: The **unidbg approach** handles this natively — it runs the actual TikTok native `.so` library which contains the encryption code. No need to reverse-engineer TTEncrypt.

## Approaches (Ranked)

### 1. unidbg — Batch Device Registration (BEST)

**Repo**: `code-root/TikTokDeviceGenerator` (9★)

- Uses Java/unidbg to emulate the TikTok native signing library
- Generates `device_id` + `install_id` + `openudid` + `cdid` per device
- Sends to `/service/2/device_register/` with proper headers and content-type
- **Batch mode** with Python threading
- **Proxy support** (HTTP/SOCKS5)
- Platform: win64, linux64, osx64 native libs bundled

**Setup**:
```bash
git clone https://github.com/code-root/TikTokDeviceGenerator.git
cd TikTokDeviceGenerator
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Ensure Java JDK/JRE 64-bit installed
python DeviceGenerator.py
```

### 2. Python Pure Signing (without TTEncrypt)

**Repo**: `code-root/tiktok-android-signing-toolkit` (28★)

- `signing_engine.py`: Local X-Gorgon, X-Khronos, X-Argus, X-Ladon, X-SS-STUB
- `device_register.py`: Register new device (requires raw JSON, may not work without TTEncrypt)
- `mitm_raw.py`: Parse MITM captures, diff device fingerprints
- `tiktok_apk_sig.py`: Extract sig_hash from APK

**Usage**:
```bash
git clone https://github.com/code-root/tiktok-android-signing-toolkit.git
cd tiktok-android-signing-toolkit
pip install pycryptodome
python device_register.py --apk /path/to/tiktok.apk --verbose
```

### 3. Frida Bridge (Real Device Signing)

**Repo**: `SebastienWae/tiktok-gorgon-bridge` (104★, archived 2020)

**Pattern** (still valid, needs updating for v44.x):
1. Run TikTok on rooted Android device
2. Inject Frida script that hooks signing function
3. Express server exposes signing as HTTP API
4. Send `{url, query, body, headers}` → get `{X-Gorgon, X-Khronos}` back

```bash
frida -U com.zhiliaoapp.musically -l compiled.js --runtime=v8
curl -X POST http://device-ip:4000/ -H 'content-type: application/json' \
  -d '{"url":"https://api2.musical.ly/aweme/v1/...","query":"...","body":"...","headers":{}}'
```

**Modern variant**: `CoderNamaste/Tiktok_Tls_Fingerprint` (14★) — Frida for TLS fingerprinting.

### 4. MITM Capture + Replay

- Set up mitmproxy/Charles on same network as real Android device
- Open TikTok app → triggers device_register
- Capture full request + response
- Use `mitm_raw.py` to parse and diff
- Replay with modified device fields

## Signing Headers Reference

| Header | Purpose | Notes |
|--------|---------|-------|
| X-Gorgon | Main request signature | v44.x produces `84xx` prefix (old `0404` is PATCHED) |
| X-Khronos | Unix timestamp | Must be within ~5s of real time |
| X-Argus | Secondary signature (AES-CBC) | Requires pycryptodome |
| X-Ladon | Tertiary signature | |
| X-SS-STUB | MD5 of uncompressed request body | Even if wire body is gzip'd |

## SMM Panel Infrastructure (How They Actually Do It)

### Tier 1: Device Farms (upstream providers)
- Hundreds to thousands of rooted Android phones or emulators
- Each runs real TikTok APK with real fingerprints
- Residential proxies per device (IP diversity)
- Appium/ADB automation for UI interactions
- Cost: $0.10-0.30 per 1K views (wholesale)
- Vietnamese providers specifically: found on Telegram groups

### Tier 2: API Operators
- Mass device_id generation via device_register
- Send view completion events via internal APIs
- Cheaper but faster detection/filtering by TikTok

### Tier 3: Web Player Bots
- Headless browser (Puppeteer/Playwright) on tiktok.com
- Cheapest but highest detection rate

### Tier 4: Resellers (most SMM panels)
- Buy from upstream at $0.20-0.50/1K
- Sell at $0.50-2.00/1K
- No actual infrastructure — just an API proxy/marketplace

## Appium/Emulator Automation Pattern

**Repos**: `dibbiennee/tiktok-bot`, `fox16crypter162/tiktok-engagement-bot`

```
Pipeline: Google Drive → Python Orchestrator → LDPlayer (ADB + Appium) → TikTok
```

- **LDPlayer** / **Genymotion** / **BlueStacks** for emulator instances
- **Appium + uiautomator2** for UI automation
- Each emulator = one device with unique fingerprint
- Scale: 5-10 emulators per cloud VM, 50-100 views/day per emulator
- **Anti-detection**: Genymotion SaaS provides clean device fingerprints

## Pitfalls

1. **v44.x sig_hash must match APK version in User-Agent** — mismatch causes rejection
2. **TTEncrypt blocks pure-Python device_register** — use unidbg or Frida instead
3. **device_register rate limits per IP** — rotate proxies for bulk generation
4. **Old Gorgon `0404` prefix is dead** — v44.x produces `84xx`
5. **unidbg requires 64-bit Java matching platform** — 32-bit Java on 64-bit OS = crash
