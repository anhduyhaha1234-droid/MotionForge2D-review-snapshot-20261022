# Redroid Container Troubleshooting

## Container Boot — "Too early" / "Can't find service"

Redroid Android 14 containers report `sys.boot_completed=1` BEFORE system services are fully initialized.

### Damru's Multi-Layer Service Readiness Check

Damru (`docker.py`) does NOT trust `sys.boot_completed` alone. Its boot sequence:

1. **`_wait_for_container_boot_internal()`** — polls `getprop sys.boot_completed` OR checks services stability after 30s
2. **ADB connect**
3. **`_wait_for_boot()`** — polls `sys.boot_completed` via ADB; also checks `_android_services_stable_adb()` after 30s as fallback
4. **`_wait_for_package_service(timeout=90)`** — polls `service check package` until "Service package:" appears
5. **`_wait_for_touchscreen_input(timeout=30)`** — waits for input device
6. **`_wait_for_android_dns_usable(timeout=60)`** — verifies DNS resolution works

**The services-stable check** requires ALL of these simultaneously, 3 consecutive passes with 3s gaps:
```bash
pidof system_server >/dev/null
service check activity | grep -q found
service check activity_task | grep -q found
service check package | grep -q found
service check webviewupdate | grep -q found
```

**Implementation for manual testing:**
```bash
SERIAL=127.0.0.1:5600

# Phase 1: Wait for boot_completed (up to 90s)
for i in $(seq 1 45); do
    [ "$(adb -s $SERIAL shell getprop sys.boot_completed 2>/dev/null)" = "1" ] && break
    sleep 2
done

# Phase 2: Wait for package service (the REAL "Too early" fix)
for i in $(seq 1 30); do
    result=$(adb -s $SERIAL shell "service check package" 2>&1)
    echo "$result" | grep -q "Service package:" && break
    sleep 3
done

# Phase 3: Verify all services stable (3 consecutive passes)
PASS=0
for i in $(seq 1 10); do
    if adb -s $SERIAL shell "pidof system_server >/dev/null && \
        service check activity | grep -q found && \
        service check activity_task | grep -q found && \
        service check package | grep -q found && \
        service check webviewupdate | grep -q found" 2>/dev/null; then
        PASS=$((PASS+1))
        [ $PASS -ge 3 ] && echo "SERVICES READY" && break
    else
        PASS=0
    fi
    sleep 3
done
```

### Error Meanings
- `"Too early to start activity"` → ActivityManager not ready; the package service check hasn't completed
- `"Can't find service: activity"` → AM crashed or not registered; retry after 5s
- `"Can't find service: package"` → PM crashed; retry after 10s  
- `"Can't find service: window"` → WindowManager not ready; same root cause as "Too early"
- Services are INTERMITTENT during boot — retry 2-3 times before concluding failure
- **Multi-worker containers** get increased boot timeout: `max(90s, min(600s, 90 + (index * 30)))`

### Boot Args That Matter

Damru's `docker.py` passes these critical boot args:
```
androidboot.use_memfd=true           # Required for Redroid internal startup
androidboot.use_redroid_stream=1     # Starts uinput service for InputReader
androidboot.redroid_gpu_mode=guest   # Software renderer (use 'host' for GPU passthrough)
androidboot.redroid_net_ndns=2       # DNS resolver config
androidboot.redroid_net_dns1=1.1.1.1
androidboot.redroid_net_dns2=8.8.8.8
ro.setupwizard.mode=DISABLED         # Prevents setup wizard from blocking launches
```

Missing `use_memfd` or `use_redroid_stream` causes degraded boot behavior.

## Image Baking Process

Damru's `bake_image()` (14 steps):
1. Start temp container from base image (`redroid/redroid:14.0.0_64only-latest`)
2. Wait for boot via `_wait_for_boot()`
3. Install input node boot repair script (fixes touchscreen InputReader race)
4. Install native AIDL sensor HAL (optional, skipped gracefully if AIDL missing)
5. Install Chrome + TrichromeLibrary via push-then-pm-session
6. Replace system WebView APK with matching version
7. Install TTS engines (eSpeak, Google TTS, RHVoice)
8. Bake host ADB public keys into `/data/misc/adb/adb_keys`
9. Push resetprop binary
10. Install native preload assets + extra fonts
11. Configure eSpeak as default TTS, backup vulkan.pastel.so, apply 48kHz audio fix
12. **Launch Chrome → dismiss FRE via uiautomator → create Preferences** (warm path enabler)
13. Patch universal Chrome Preferences (DoH off, WebRTC policy, DNS prefetch off)
14. Clean up + `docker commit` (container must be stopped before commit for clean OverlayFS snapshot)

**Key insight:** The baked image's `/data` contains Chrome with FRE dismissed and Preferences written. This means `has_preferences()=True` on first boot → warm fast path (~10-15s per session instead of cold start with pm clear + FRE).

## Chrome Won't Launch — "Activity does not exist"

Even though `pm list packages | grep chrome` shows Chrome installed, `am start` returns "Activity class does not exist".

**Root cause:** Chrome's trichrome library (`com.google.android.trichromelibrary`) is NOT installed. Without it, `libmonochrome_64.so` (the main Chrome rendering engine) is unavailable and activities can't be instantiated.

**Diagnosis:**
```bash
# Check if trichrome is installed
adb -s 127.0.0.1:5600 shell "pm list packages" | grep trichrome
# If empty → this is the problem

# Confirm extractNativeLibs=false (Android reads from APK, not filesystem)
adb -s 127.0.0.1:5600 shell "dumpsys package com.android.chrome" | grep extractNativeLibs
# → extractNativeLibs=false means pushing .so files to lib/ directory WON'T WORK

# Check native libs are empty (expected, NOT the problem to fix here)
adb -s 127.0.0.1:5600 shell pm path com.android.chrome
# e.g. /data/app/~~HASH==/com.android.chrome-HASH==
adb -s 127.0.0.1:5600 shell "ls -la /data/app/~~HASH==/com.android.chrome-HASH==/lib/x86_64/"
# If empty → expected; the libs should come from the trichrome PACKAGE, not the filesystem
```

**Why pushing .so files doesn't work:**
Chrome's package manifest declares `extractNativeLibs=false`, which tells Android's linker to load `.so` files directly from the APK using `dlopen` on the zip entry — NOT from the filesystem's `lib/` directory. Pushing files to `lib/x86_64/` places them on disk where Android never looks. This applies to all Chrome versions (143-148) and both `pm install` and filesystem approaches.

**Fix — rebake the image:**
```bash
python -m damru bake-image --chrome-apk /home/damru/chrome-apks/<version>
```
The `bake-image` process installs trichrome + Chrome during image build where the PackageManager can handle it (the 200MB+ APK crash only happens at runtime, not during build). After rebaking:
1. Recreate the container with the new image
2. Verify: `pm list packages | grep trichrome` should show `com.google.android.trichromelibrary`
3. Launch Chrome: `am start -a android.intent.action.VIEW -d "https://example.com" com.android.chrome`

**Why trichrome fails to install at runtime:**
ALL trichrome library APKs across Chrome 143-148 exceed 200MB (213-226MB). Redroid's PackageManager consistently crashes with "Broken pipe (32)" on APKs this large. This affects:
- `pm install -r -d <apk>` → Broken pipe
- `adb install -r -d <apk>` (streamed) → Broken pipe
- `pm install-create` + `pm install-write` session API → crashes the package service entirely (requires ~10s recovery)
- Increasing container RAM (2g→4g) does NOT fix the issue

## Trichrome Library Install Crashes PackageManager

**ALL install methods for `google_trichrome_library.apk` (220MB+) fail on Redroid:**

| Method | Result |
|--------|--------|
| `pm install -r -d <apk>` | "Broken pipe (32)" |
| `adb install -r -d <apk>` (streamed) | "Broken pipe (32)" |
| `pm install-create` + `pm install-write` session API | Crashes package service (10s recovery) |
| Increasing container RAM to 4g | Same failure |
| Pushing .so files to lib/ directory | Files land on disk but `extractNativeLibs=false` means Android ignores them |

This is a Redroid PackageManager bug with APKs >200MB. ALL trichrome versions across Chrome 143-148 exceed this threshold (213-226MB). There is no version workaround.

### The Only Reliable Fix: `bake-image`

The `bake-image` process installs trichrome during Docker image build where the PackageManager can handle large APKs. This is the ONLY method that works.

```bash
python -m damru bake-image --chrome-apk /home/damru/chrome-apks/147.0.7727.101
```

After baking:
1. Remove old container: `docker stop damru-worker-0 && docker rm damru-worker-0`
2. Recreate with new image using the flags from Step 10
3. Wait for boot (90-120s)
4. Verify trichrome: `pm list packages | grep trichrome`
5. Verify Chrome launch: `am start -a android.intent.action.VIEW -d "https://example.com" com.android.chrome`

### Push-then-pm-session (Does NOT Work)

Previously documented as a workaround, this also fails. The `pm install-create` session API crashes the package service when writing >200MB of APK data:
```
pm install-create -r -d -S 231958590    → "Success: created install session [ID]"
pm install-write -S 231958590 <ID> ...  → "cmd: Can't find service: package"
```
The package service recovers after ~10s but the install is incomplete.

### extractNativeLibs=false — Why Filesystem Libs Don't Work

Chrome's package manifest declares `extractNativeLibs=false`. This means:
- Android's linker uses `dlopen` to load `.so` files **directly from the APK zip** using page-aligned mmap
- The filesystem `lib/x86_64/` directory is **completely ignored** by the runtime
- Even if you push `libmonochrome_64.so` (222MB) to the lib dir, Chrome crashes with "Activity does not exist" because the linker can't find it in the APK

Check the flag: `dumpsys package com.android.chrome | grep extractNativeLibs`

### If Trichrome Is NOT in the Baked Image

If `bake-image` ran but `pm list packages | grep trichrome` returns nothing after container start, the bake failed silently. Check:
1. Did `bake-image` output show trichrome install success?
2. Is the container using the NEW image tag? (`docker inspect` → image)
3. Was `-v /host:/data` used? (volume mount replaces baked `/data` with empty host dir)

## Data Volume Behavior

| Container mode | `/data` contents | Chrome state |
|---|---|---|
| `docker run` (no `-v`) | Image's own data | Chrome 147 + trichrome pre-installed |
| `docker run -v /host:/data` | Host directory (may be empty) | Chrome missing, must reinstall |

**Key insight:** The baked image has Chrome baked into `/data/app/`. Without a volume mount, this persists. With a volume mount to an empty host dir, all baked app data is replaced.

If Chrome was working but broke after container recreation, check if you changed the `-v` flag.

## Container Recreation Checklist

When `docker stop` + `docker rm` + `docker run` is needed:

1. Note current container flags (`docker inspect damru-worker-0`)
2. Stop + remove
3. Recreate with SAME flags
4. Wait 90-120s for boot
5. Verify: `pm list packages | grep chrome` 
6. If Chrome missing: install APKs (trichrome FIRST)
7. If Chrome present but won't launch: check if trichrome is installed (`pm list packages | grep trichrome`). If not, the baked image is incomplete — rebake with `python -m damru bake-image`.
8. Enable Chrome: `pm enable com.android.chrome`
9. Test with activity probing (Damru tries these in order):
```bash
SERIAL=127.0.0.1:5600
# Damru tries 4 activities with 4 retries × 3s delays each
for activity in \
    "com.android.chrome/com.google.android.apps.chrome.Main" \
    "com.android.chrome/org.chromium.chrome.browser.ChromeTabbedActivity" \
    "com.android.chrome/org.chromium.chrome.browser.ChromeTabbedActivity2"; do
    adb -s $SERIAL shell "am start -W --activity-clear-top -n $activity -a android.intent.action.VIEW -d https://example.com" && break
    sleep 3
done
```

## ADB Quoting Pitfalls in WSL

**Broken:** `wsl -d Ubuntu -- bash -c 'adb -s $SERIAL shell "am start ..."'`
Variables with `:` get mangled, pipes inside double-quoted `shell "..."` break.

**Working:** Use Python `execute_code` with individual `terminal()` calls:
```python
from hermes_tools import terminal
terminal('wsl -d Ubuntu -- adb -s 127.0.0.1:5600 shell am force-stop com.android.chrome')
terminal('wsl -d Ubuntu -- adb -s 127.0.0.1:5600 shell "am start -a android.intent.action.VIEW -d https://example.com com.android.chrome"')
```

**Working (bash):** Hardcode serial, avoid nested quotes:
```bash
wsl -d Ubuntu -- adb -s 127.0.0.1:5600 shell am force-stop com.android.chrome
```
