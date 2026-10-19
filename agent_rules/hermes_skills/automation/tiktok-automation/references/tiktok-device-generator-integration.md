# TikTokDeviceGenerator Integration

## Two Repos, Same unidbg.jar

Both `code-root/TikTokDeviceGenerator` and `xSaleh/TikTok-register-device_id` contain the **identical** `unidbg.jar` (58,293,284 bytes). The difference is the Python wrapper:

| Feature | code-root/TikTokDeviceGenerator | xSaleh/TikTok-register-device_id |
|---------|----------------------------------|-----------------------------------|
| Stars | 9 | — |
| Last updated | 4 months ago | 2 years ago |
| Batch mode | ✅ Built-in (threading, thread pool) | ❌ Single device only |
| Proxy support | ✅ SOCKS5/HTTP/HTTPS | ❌ |
| JSON export | ✅ Chunked device files | ❌ |
| GUI | ✅ Tkinter (optional) | ❌ |
| Headless scripts | ✅ `batch_generate.py` | ❌ |

**Recommendation**: Always use `code-root/TikTokDeviceGenerator`.

## Native Library Structure

```
TikTokDeviceGenerator/
├── Libs/
│   ├── unidbg.jar                    # Main unidbg (58MB, identical across repos)
│   ├── prebuilt/
│   │   ├── win64/
│   │   │   ├── capstone.dll          # Disassembly framework
│   │   │   ├── keystone.dll          # Assembly framework
│   │   │   └── unicorn_java.dll      # CPU emulator (ARM→x86)
│   │   ├── linux64/                  # Same libs for Linux
│   │   ├── osx64/                    # Same libs for macOS
│   │   └── jar/                      # Additional JARs (capstone, unicorn, utils)
│   └── example_binaries/
├── batch_generate.py                 # ★ Headless batch device_id generator
├── batch_generate_profiles.py        # ★ Full profiles: unidbg + EC keys + cookies
└── DeviceGenerator.py                # Original Tkinter GUI app
```

## How unidbg.jar Works

unidbg is a Java library that emulates ARM native code on x86/ARM JVM. TikTok's
device registration requires a native crypto operation (ttEncrypt) that cannot be
replicated in pure Python. unidbg runs the actual TikTok native library to produce
the encrypted payload.

### Command Pattern

```bash
java -Djna.library.path="<jni_path>" -Djava.library.path="<jni_path>" -jar unidbg.jar "<message>"
```

Where `<message>` = `"<gentime_ms> <ud_id> <openudid> <mac>"` (4 space-separated values).

### Output Parsing

unidbg prints:
```
hex=<64-char-hex-per-line blocks...>
size: <N>
```

Parse with: `re.search(r"(?is)hex\s*=\s*([\s\S]*?)\r?\n\s*size\b", stdout)`

## Headless Batch Script: batch_generate_profiles.py

Located at `C:\Users\Admin\TikTokDeviceGenerator\batch_generate_profiles.py`.

Combines three operations in one script:
1. **unidbg device registration** → real `device_id` + `install_id` from TikTok
2. **EC P-256 key generation** → private/public keys for guard headers
3. **Full profile assembly** → complete JSON matching `device_v44_3_1.json` schema

### Usage

```bash
cd C:\Users\Admin\TikTokDeviceGenerator

# Generate 10 US profiles
python batch_generate_profiles.py -n 10 --region US

# Generate 5 VN profiles with custom output directory
python batch_generate_profiles.py -n 5 --region VN -o C:/profiles

# Generate with delay between requests
python batch_generate_profiles.py -n 20 --delay 1.0

# Use specific Java installation
python batch_generate_profiles.py -n 10 --java "C:\Java\jdk-17\bin\java.exe"
```

### Output Format

Each profile is saved as `profiles/profile_NNNN_<device_id>.json` with the full schema:

```json
{
  "meta": { "version": "44.3.15", "region": "US", ... },
  "device": { "device_id": "7666245181868262919", "iid": "...", "openudid": "...", ... },
  "app": { "app_name": "musical_ly", "aid": "1233", ... },
  "network": { "ac": "wifi", "mcc_mnc": "310260", ... },
  "locale": { "timezone_name": "America/New_York", ... },
  "user_agent": "com.zhiliaoapp.musically/2024403150 ...",
  "session": { "cookie": "store-idc=useast5; ...; odin_tt=...", ... },
  "guard_keys": { "private_pem": "-----BEGIN PRIVATE KEY-----...", ... },
  "guard_headers": { "tt-ticket-guard-public-key": "...", ... }
}
```

### Verified Performance

- **25/25 profiles generated successfully** (100% success rate)
- ~2-3 seconds per profile (unidbg JVM startup + HTTP registration)
- Each device gets unique: device_id, install_id, openudid, EC P-256 key pair, odin_tt
- All profiles are compatible with `api_framework.py` and `build_headers()`

## Java PATH Notes

After `winget install EclipseAdoptium.Temurin.21.JDK`:
- Java may not be in current shell PATH immediately
- `batch_generate.py` auto-detects: JAVA_HOME, common JDK paths, `which java`
- On Windows, prefers 64-bit JVM (required for win64 native DLLs)
- Check: `java -version` should show `openjdk version "21.x"`

## Pitfalls

1. **unidbg.jar requires matching native DLLs.** The `Libs/prebuilt/win64/` directory must contain `capstone.dll`, `keystone.dll`, `unicorn_java.dll`. Without them, Java throws `UnsatisfiedLinkError`.

2. **32-bit JVM won't work with 64-bit DLLs.** On Windows, `getsystem()` returns `win64`, which needs 64-bit native libs. A 32-bit JVM cannot load them. The script checks for 64-bit via `java -version` output.

3. **unidbg output parsing is fragile.** The regex `hex\s*=\s*([\s\S]*?)\r?\n\s*size\b` handles both `\n` and `\r\n` line endings. If unidbg output format changes, this breaks silently.

4. **Rate limiting on device_register.** Sending too many requests too fast may get IP rate-limited. Use `--delay 0.5` or higher. 25 requests in ~60 seconds worked without issues.

5. **Same openudid across requests is fine.** Unlike device_id (which must be unique per request for dedup), openudid is a device fingerprint that can repeat. The server uses device_id+IP for dedup, not openudid.
