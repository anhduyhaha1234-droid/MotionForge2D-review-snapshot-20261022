# douyin-sign Library & TikTok Constants Extraction Attempt
## Date: 2026-07-25

## douyin-sign Library (7452323/douyin-sign)

### What It Is
- **Repo**: github.com/7452323/douyin-sign (10★, updated 2026-07-23)
- **Description**: "TikTok/Douyin all-in-one HTTP signing algorithms"
- **Pure Python** implementation, no native dependencies
- **Nightly CI** for automatic constant extraction from APK

### Installation
```bash
pip install pycryptodome gmssl httpx
git clone https://github.com/7452323/douyin-sign.git
```

### Key Files
```
sign/__init__.py    — Main module: sign_all(), sign_mobile_request(), Device
sign/gorgon.py      — X-Gorgon signing (2KB, compact)
sign/argus.py       — X-Argus signing (8.5KB)
sign/ladon.py       — X-Ladon signing (4.4KB)
sign/khronos.py     — X-Khronos timestamp
sign/ssstub.py      — X-SS-STUB (MD5 digest)
sign/device.py      — Device class + register_device()
sign/ttencrypt.py   — TTEncrypt (79KB)
sign/protobuf.py    — Protobuf handling
proxy.py            — FastAPI proxy server (auto device registration)
update.py           — APK constant extraction script
constants/current/  — sign_key.b64, gorgon_table.hex, protobuf_fields.json
```

### Usage
```python
from sign import sign_all, Device, make_seed_device

d = make_seed_device()
headers = sign_all(
    method='GET',
    url='https://api-h2.tiktokv.com/aweme/v1/play/?video_id=...',
    body=b'',
    cookies=d.to_cookie(),
    device=d,
)
# Returns: X-Khronos, X-SS-STUB, X-Gorgon, X-Argus
```

### sign_mobile_request() — Full API call
```python
from sign import sign_mobile_request
result = sign_mobile_request(
    'GET', '/aweme/v1/play/',
    params={'video_id': '...', 'line': '0', ...},
    device=d,
)
```
**Default base URL**: `api.douyin.com` (Douyin, NOT TikTok)
**Monkey-patch for TikTok**: `import sign; sign.MOBILE_API_BASE = "https://api-h2.tiktokv.com"`

### Device Class
```python
d = Device(
    device_id="7412345678901234567",
    install_id="1234567890123456",
    device_type="SM-S928B",
    os_version="33",
    app_version="38.5.0",
)
```
- `d.to_cookie()` → `"install_id=...; odin_tt=000...000; sessionid=; iid=..."`
- `d.to_headers()` → User-Agent, Cookie, X-Requested-With
- `d.user_agent` → `"com.ss.android.ugc.aweme/38.5.0 (Android 33; SM-S928B)"`

### Device Registration
```python
from sign import register_device
d = await register_device()  # Calls log.snssdk.com/service/2/device_register/
```
Registration endpoint: `https://log.snssdk.com/service/2/device_register/`
Uses X-Gorgon + X-Khronos + X-SS-STUB signing (no X-Argus needed for registration)

### FastAPI Proxy Server (proxy.py)
```python
# Runs signing server on port 8800
# GET /api/douyin/mobile/{path}?param1=val1 → signed API call
# GET /api/douyin/web/{path}?param1=val1 → X-Bogus signed web call
```

---

## CRITICAL: Constants Are Douyin-Specific

### Test Results
| Test | Target | Result |
|------|--------|--------|
| sign_all() with Douyin constants → api-h2.tiktokv.com | TikTok play endpoint | HTTP 400 `{"status_code":5,"status_msg":"Invalid parameters"}` |
| sign_all() with Douyin constants → api.douyin.com | Douyin endpoints | Connection refused (geo-blocked from VN) |
| sign_mobile_request() → api-h2.tiktokv.com | TikTok | HTTP 400 |
| register_device() → log.snssdk.com | Device register | HTTP 200 but `device_id:0` (soft failure) |

### Root Cause
The `constants/current/` directory contains:
- `sign_key.b64`: Base64-encoded signing key — extracted from DOUYIN APK
- `gorgon_table.hex`: `ce7c47e421ff095cc9da81690147cba1ed6cc4b1` — Douyin-specific

TikTok international (musical_ly) uses DIFFERENT constants. The X-Gorgon algorithm structure is identical but the key values differ.

### Why Device Registration Returns device_id: 0
HTTP 200 + `{"server_time":..., "device_id":0, "install_id":0}` means:
- Signing is accepted (no 401/403)
- But TikTok refuses to register the device
- Likely: signing constants don't match the app (aweme vs musical_ly)
- Or: seed device parameters look suspicious

---

## TikTok APK Constants Extraction Attempt

### Process
1. Downloaded latest TikTok APK from apkpure.com (581MB)
2. Extracted `lib/arm64-v8a/libmetasec_ov.so` (2,049,056 bytes)
3. Note: file is `libmetasec_ov.so` NOT `libmetasec.so` (different from Douyin)

### Extraction Results
```
Base64 candidates (44-char pattern): 1 match
  → "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrs" (45 chars)
  → Clearly NOT a signing key (just alphabet string)

Hex candidates (40-char pattern): 0 matches
  → No gorgon_table candidates found
```

### Why Extraction Failed
- TikTok's `libmetasec_ov.so` uses **obfuscation** beyond simple regex
- Constants may be: split across memory, XOR-encoded, computed at runtime, or stored in different format
- The `update.py` script's regex patterns (`[A-Za-z0-9+/]{44,44}` and `[0-9a-f]{40,40}`) don't match
- Need: Ghidra/IDA Pro binary analysis OR Frida hooking on real device

### What tikapis.com Likely Did
tikapis.com had working TikTok signing constants. They likely:
1. Used Frida to hook `libmetasec_ov.so` on a real Android device
2. Intercepted the signing key and gorgon table at runtime
3. Extracted the constants from memory dumps
4. This requires: rooted Android device + Frida server + custom script

---

## Comparison: douyin-sign vs code-root/tiktok-android-signing-toolkit

| Feature | douyin-sign (7452323) | code-root (28★) |
|---------|----------------------|------------------|
| Language | Python | Python + Java (unidbg.jar) |
| X-Gorgon version | Current (from Douyin) | v44.x (from TikTok) |
| Constants | Douyin-specific | TikTok-specific |
| Device register | Returns device_id: 0 | Returns real device_id (via unidbg) |
| TikTok compatibility | ❌ HTTP 400 | ✅ status_code: 0 |
| Dependencies | pycryptodome, gmssl | Java JDK 21+ |
| Architecture | Clean Python | Hybrid (JNI bridge) |

**Bottom line**: douyin-sign is better architecture/code quality but wrong constants for TikTok. code-root works for TikTok but requires Java.

---

## Recommendations for Self-Build

1. **Use douyin-sign as architecture reference** — clean Python, well-structured
2. **Get TikTok constants** via:
   - Frida hooking on rooted Android (most reliable)
   - Ghidra reverse engineering of libmetasec_ov.so (complex)
   - Capture from code-root/tiktok-android-signing-toolkit's device profiles
3. **For production**: Use code-root's v44.x signing + unidbg.jar for device registration
4. **The blocker**: odin_tt cookie is IP-bound — valid signing + proxy = still fails
