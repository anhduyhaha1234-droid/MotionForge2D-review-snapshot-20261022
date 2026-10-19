---
name: damru-setup
description: "Set up and operate Damru — Android-native stealth browser automation framework (Redroid + Playwright + CDP) on Windows via WSL2 or native Linux. Covers WSL2 custom kernel, Docker/binderfs, Redroid container lifecycle, Chrome APK installation, device profile spoofing, proxy configuration, and multi-worker pools. Use when the user wants anti-detect browser automation, Android fingerprint spoofing, stealth web scraping, or Damru CLI/API work."
version: 1.4.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [automation, android, antidetect, browser, wsl2, docker, redroid, stealth]
    related: [terminal-engineering-discipline, playwright-browser-automation]
---

# Damru Setup & Operation

## Overview

Damru is the first open-source, Android-native stealth browser automation framework. It runs real Android 14 inside Docker (Redroid), drives Chrome via CDP + Playwright, and spoofs fingerprints at 8 OS/binary/protocol layers with ZERO JavaScript injection. Scores 85%+ on CreepJS, bypasses Cloudflare Turnstile, DataDome, Akamai, PerimeterX, Kasada.

**Repo:** https://github.com/akwin1234/damru  
**License:** PolyForm Noncommercial 1.0.0 (non-commercial use only)

## When to Use

- User wants anti-detect browser for web scraping, automation testing, or fingerprinting research
- User needs Android-native browser automation (not desktop Chrome pretending to be mobile)
- User asks about Damru, Redroid, or stealth browser setup
- User wants to bypass Cloudflare, DataDome, or other WAFs
- Setting up multi-session browser pools with unique fingerprints

## When to Use vs Desktop Playwright

Damru is the heavy option. For simpler needs, use `playwright-browser-automation` (desktop Playwright):
- Quick testing / proof of concept → Desktop Playwright
- Single-session automation → Desktop Playwright
- Scale with unique device fingerprints + anti-bot bypass → Damru
- See `playwright-browser-automation` skill for desktop setup and proxy rotation patterns

## Architecture (8 Layers of Zero-JS Stealth)

1. **Layer 1 — Android System Props** (`resetprop`): `ro.product.model`, `ro.build.fingerprint`, SDK version
2. **Layer 2 — GPU Binary Patching**: Physical `.so` file patching (Vulkan/GLES drivers) — no SwiftShader leak
3. **Layer 3 — Syscall Interception** (`libfakemem.so` via `LD_PRELOAD`): Fakes `sysinfo`/`sysconf` for RAM/CPU
4. **Layer 4 — CDP Protocol Overrides**: `Emulation.setHardwareConcurrencyOverride`, touch emulation
5. **Layer 5 — Thread/Worker Interception**: `Target.setAutoAttach` closes Web Worker leak vectors
6. **Layer 6 — Chrome Preferences & Flags**: Locale, TLS cipher randomization (~184 JA3 variants), DoH disable
7. **Layer 7 — OS-Level Evasions**: iptables blocks WebRTC IP leaks, disables IPv6, debugger pause bypass
8. **Layer 8 — Display/Density Spoofing**: `wm size/density` for physical screen accuracy

## Platform Requirements

| Platform | Status | Notes |
|---|---|---|
| **Ubuntu 24.04 native** | Production-ready | Best option for VPS |
| **Ubuntu 24.04 WSL2** | Production-ready | Requires custom WSL kernel |
| **Ubuntu 26.04 WSL2** | Works (tested) | Not officially supported but functional |
| **Windows native Docker** | NOT SUPPORTED | Redroid is Linux-only |
| **Physical Android devices** | NOT SUPPORTED | Will refuse auto-select |

**Hardware minimums (per worker):**
- CPU: 2 vCPU minimum, 4 recommended
- RAM: 4 GB minimum, 8 GB recommended (worker uses ~1-2 GB in 2 GB container limit)
- Disk: 15 GB minimum, 25-30 GB recommended

## Setup Steps (Windows WSL2)

### Step 1: Install WSL2 + Ubuntu

```bash
wsl --install -d Ubuntu
```

If freshly installed, a reboot is required before the distro is usable.

### Step 2: Install Custom WSL Kernel (for binderfs)

The default WSL2 kernel lacks `CONFIG_ANDROID_BINDER_IPC`. Damru ships a bundled kernel at `damru/damru/wsl_kernel/wsl2-kernel-redroid-natfix-*`.

```bash
# Copy kernel to Windows user home
cp <damru-repo>/damru/wsl_kernel/wsl2-kernel-redroid-natfix-* ~/vmlinux-redroid
```

Create `C:\Users\<user>\.wslconfig`:

```ini
[wsl2]
kernel=C:\\Users\\<user>\\vmlinux-redroid
dnsTunneling=true
networkingMode=NAT
memory=8GB
processors=4
```

**PITFALL:** Kernel path in `.wslconfig` needs double backslashes (`C:\\Users\\...`).

Restart WSL: `wsl --shutdown`, then reopen and verify:

```bash
zcat /proc/config.gz | grep -i binder
# Must show: CONFIG_ANDROID_BINDER_IPC=y, CONFIG_ANDROID_BINDERFS=y
```

### Step 3: Install Docker + Dependencies in WSL

```bash
# Inside WSL as root
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv adb wget curl git jq
curl -fsSL https://get.docker.com -o /tmp/get-docker.sh && sh /tmp/get-docker.sh
```

**PITFALL — iptables error on WSL:** Docker may fail with `addrtype revision 0 not supported`. Fix:

```bash
update-alternatives --set iptables /usr/sbin/iptables-legacy
update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy
# Then restart dockerd
```

### Step 4: Mount Binderfs + Start Docker

```bash
mkdir -p /dev/binderfs && mount -t binder binder /dev/binderfs
dockerd &>/tmp/dockerd.log &
```

Verify: `ls /dev/binderfs/` should show binder, hwbinder, vndbinder, binder-control.

### Step 5: Install Damru

```bash
cd /home/damru
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -e /path/to/damru   # or: pip install git+https://github.com/akwin1234/damru.git
```

### Step 6: Load Redroid Image

```bash
python -m damru install-image --download
# Or manually:
wget -O damru-baked.tar.gz 'https://dl.damru.dev/assets/damru-baked.tar.gz'
gunzip -c damru-baked.tar.gz | docker load
```

Image is ~1.3 GB compressed, ~4.4 GB in Docker.

### Step 7: Download Chrome APK Bundle

```bash
python -m damru install-apks --download
```

Downloads ~3.3 GB ZIP, extracts to `/home/damru/chrome-apks/` with Chrome 143-148 split APKs.

### Step 8: Apply Playwright Patch

```bash
# Find target
TARGET=$(find .venv -name 'crPage.js' -path '*/chromium/*' | head -1)
# Copy Damru's patch
cp <damru-repo>/damru/playwright_patch/crPage.js "$TARGET"
```

### Step 9: Configure `damru/config.py`

**CRITICAL PITFALL:** The config.py MUST contain ALL variables imported by `docker.py`. Both template files (`config.py.windows` and `config.py.linux`) are INCOMPLETE. `docker.py` imports these from config:

```
CONTAINER_BOOT_TIMEOUT, DOCKER_CMD_TIMEOUT, APK_INSTALL_TIMEOUT,
REDROID_BASE_IMAGE, REDROID_BASE_PORT, REDROID_CONTAINER_PREFIX,
REDROID_CPUS, REDROID_GPU_MODE, REDROID_IMAGE, REDROID_MEMORY,
REDROID_SETUPWIZARD_DISABLED, WSL_DISTRO, WSL_USERNAME
```

**The Linux template is missing `REDROID_BASE_IMAGE`. The Windows template is missing many more.** Always verify with:

```bash
python -c "from damru.docker import *; print('OK')"
```

See `references/damru-config-complete.py` for a known-good config.

### Step 10: Start Redroid + Install Chrome

```bash
# Start container — these exact boot args match Damru's source code (docker.py start_container)
docker run -d --name damru-worker-0 \
    --privileged \
    --restart=on-failure:3 \
    -v /dev/binderfs:/dev/binderfs \
    -p 5600:5555 \
    --cpus=2 --memory=2g \
    damru-redroid:latest \
    androidboot.use_memfd=true \
    androidboot.use_redroid_stream=1 \
    androidboot.redroid_gpu_mode=guest \
    androidboot.redroid_net_ndns=2 \
    androidboot.redroid_net_dns1=1.1.1.1 \
    androidboot.redroid_net_dns2=8.8.8.8 \
    ro.setupwizard.mode=DISABLED
```

**PITFALL — Missing boot args:** `androidboot.use_memfd=true` and `androidboot.use_redroid_stream=1` are critical for Redroid's internal startup. Omitting them causes degraded boot behavior. The DNS boot args (`redroid_net_dns1/dns2`) ensure Android's resolver works even if `net.dns1` stays empty. `ro.setupwizard.mode=DISABLED` prevents the setup wizard from blocking activity launches.

**Wait sequence (from Damru's source):** `sys.boot_completed=1` does NOT mean services are ready. Damru uses a multi-layer readiness check:

```bash
SERIAL=127.0.0.1:5600

# Phase 1: Wait for sys.boot_completed (up to 90s, poll every 2s)
for i in $(seq 1 45); do
    [ "$(adb -s $SERIAL shell getprop sys.boot_completed 2>/dev/null)" = "1" ] && break
    sleep 2
done

# Phase 2: Wait for package service (up to 90s, poll every 3s)
# This is the FIX for "Too early to start activity" and "Can't find service: window"
for i in $(seq 1 30); do
    result=$(adb -s $SERIAL shell "service check package" 2>&1)
    echo "$result" | grep -q "Service package:" && break
    sleep 3
done

# Phase 3: Verify ALL critical services are stable (3 consecutive passes with 3s gaps)
for check in 1 2 3; do
    adb -s $SERIAL shell "pidof system_server >/dev/null && \
        service check activity | grep -q found && \
        service check activity_task | grep -q found && \
        service check package | grep -q found && \
        service check webviewupdate | grep -q found"
    [ $check -lt 3 ] && sleep 3
done

# Phase 4: Verify Chrome package is resolvable
adb -s $SERIAL shell "pm path com.android.chrome | head -1"
# Must return: package:/data/app/...base.apk (NOT empty)
```

**CRITICAL PITFALL — Chrome APK install order:** The trichrome library MUST be installed BEFORE Chrome, or `pm install-commit` fails with `INSTALL_FAILED_MISSING_SHARED_LIBRARY`. Use Damru's push-then-pm-session approach — `adb install` streaming (abb_exec) is unreliable over ADB TCP with Redroid containers and causes "device offline" errors.

```bash
SERIAL=127.0.0.1:5600
CHROME=/home/damru/chrome-apks/148.0.7778.217
REMOTE_DIR=/data/local/tmp/chrome-install

adb -s $SERIAL shell mkdir -p $REMOTE_DIR

# 1. Push ALL APKs to device first (avoids abb_exec streaming failures)
for f in $CHROME/*.apk; do
    adb -s $SERIAL push "$f" "$REMOTE_DIR/$(basename $f)"
done

# 2. Install trichrome library FIRST via pm install
adb -s $SERIAL shell pm install -r -d $REMOTE_DIR/google_trichrome_library.apk

# 3. Calculate total size for remaining Chrome APKs
TOTAL=$(du -b $CHROME/base.apk $CHROME/split_*.apk 2>/dev/null | awk '{s+=$1} END {print s}')

# 4. Install Chrome split APKs via pm session API
SESSION=$(adb -s $SERIAL shell pm install-create -r -d -S $TOTAL | grep -oP '\[\K[0-9]+')
IDX=0
for f in $CHROME/base.apk $CHROME/split_*.apk; do
    SIZE=$(stat -c%s "$f")
    adb -s $SERIAL shell pm install-write -S $SIZE $SESSION split_$IDX $REMOTE_DIR/$(basename "$f)")
    IDX=$((IDX+1))
done
adb -s $SERIAL shell pm install-commit $SESSION

# 5. Cleanup
adb -s $SERIAL shell rm -rf $REMOTE_DIR
```

**PITFALL — ADB `install-multiple` flag:** ADB 1.0.41 (Ubuntu default) doesn't support `install-multiple -r`. Use `pm install-create` + `pm install-write` + `pm install-commit` instead. Always push APKs to the device first — never stream directly from host over ADB TCP.

**PITFALL — Trichrome "Broken pipe" (UNRESOLVED):** `pm install` for `google_trichrome_library.apk` (220MB+) returns "Broken pipe (32)". This affects ALL install methods: `pm install`, `adb install`, `adb install-multiple`, `pm install-create` + `pm install-write` session API (crashes package service entirely with StorageManager NullPointerException), AND `python -m damru bake-image` itself. ALL trichrome versions across Chrome 143-148 exceed the 200MB Redroid PackageManager threshold (213-255MB). **The pre-baked image from `install-image --download` also does NOT include trichrome** — verified on 2026-07-25 with a fresh download. Pushing .so files to the filesystem doesn't work because `extractNativeLibs=false`. **This is an unresolved Redroid limitation with no known workaround as of 2026-07-25.** Chrome cannot launch on Redroid without trichrome — activities return "Activity class does not exist". `org.chromium.webview_shell` is installed but cannot handle full page rendering for automation. Fallback: use desktop Playwright with Chromium (loses Android fingerprint but functions for web automation).

### Step 11: Apply Device Profile

```bash
python -m damru force-profile --serial 127.0.0.1:5600 --device "Samsung Galaxy S24"
```

**PITFALL:** `--device random` is NOT valid for `force-profile`. Must specify a named device. Use the full list from the error message.

### Step 12: Verify

```bash
python -m damru check preflight
python -m damru quick-check --serial 127.0.0.1:5600
```

All checks should be PASS. WARN on ADB port range is expected when a container is running.

## Using Damru with Proxies

```python
import asyncio
from damru import AsyncDamru

async def main():
    async with AsyncDamru(
        device="Samsung Galaxy S24",
        proxy="socks5://user:pass@proxy:1080",  # GeoIP auto-resolved
        # timezone and locale auto-derived from proxy exit IP
    ) as browser:
        page = await browser.new_page()
        await page.goto("https://www.tiktok.com/@user/video/xxxxx")
        await page.wait_for_timeout(30000)
        await page.screenshot(path="proof.png")

asyncio.run(main())
```

**Proxy features:**
- SOCKS5 and HTTP CONNECT supported
- Authenticated proxies: Damru starts a local no-auth bridge for Android Chrome
- GeoIP auto-resolution: timezone, locale, Accept-Language derived from proxy exit
- Sticky sessions for rotating proxies (DataImpulse support built-in)
- Per-worker proxy lists for pool mode

## Multi-Worker Pool

```python
from damru import DamruPool

proxies = ["socks5://p1:1080", "socks5://p2:1080", "socks5://p3:1080"]

async with DamruPool(max_devices=3, proxies=proxies) as pool:
    async with pool.session() as ctx:
        page = await ctx.new_page()
        await page.goto("https://target.com")
```

Budget: ~2 vCPU + 2-3 GB RAM per worker.

## CLI Reference

| Command | Purpose |
|---|---|
| `python -m damru check preflight` | Read-only readiness check |
| `python -m damru quick-check --serial X` | Android/Chrome stealth sanity |
| `python -m damru force-profile --serial X --device Y` | Apply named profile |
| `python -m damru open-url --serial X URL` | Open URL in Android Chrome |
| `python -m damru stealth-open-url --serial X URL` | Full stealth session open |
| `python -m damru screenshot --serial X --output Y` | Capture screen |
| `python -m damru benchmark` | Run anti-bot benchmark suite |
| `python -m damru ui` | Localhost dashboard |

## Redroid Container Lifecycle

Container can exit/get removed (exit code 255, docker daemon restart, host reboot). Recreate with the exact flags from Step 10 above.

- `docker start <id>` only works if container still exists. If `docker ps -a` shows it gone, must `docker run` again.
- Without `-v`, container uses image's own `/data` (baked Chrome pre-installed). With `-v /host:/data`, an empty host dir replaces all baked app data.
- `--restart=on-failure:3` auto-restarts on crash up to 3 times.
- `--privileged` and `-v /dev/binderfs:/dev/binderfs` are **mandatory** — container crashes (exit 255) without binderfs.
- Port 5600→5555 is the default. Change host port (`-p 5700:5555`) for multi-worker setups.
- **Multi-worker timeout scaling:** Damru increases boot timeout for higher-index workers: `max(90s, min(600s, 90 + (index * 30)))` because they share CPU with already-running Android instances.
- **Boot timeout default:** 90 seconds (`CONTAINER_BOOT_TIMEOUT`). Can be overridden in `config.py`.
- `sys.boot_completed=1` does NOT mean services are ready. Always run the full service readiness check from Step 10 before launching Chrome.
- **Chrome activity probing order:** Damru tries 4 activities in order: `com.google.android.apps.chrome.Main`, `ChromeTabbedActivity`, `ChromeTabbedActivity2`, with 4 retries × 3s delays per round.

## ADB-Based Automation (Direct ADB, no CDP/Playwright)

When Damru's CDP layer isn't needed (e.g., simple view counting via ADB taps), use direct ADB commands:

```bash
adb -s 127.0.0.1:5600 shell am start -a android.intent.action.VIEW -d "URL" com.android.chrome
adb -s 127.0.0.1:5600 shell input tap 540 1200
adb -s 127.0.0.1:5600 shell input keyevent KEYCODE_BACK
adb -s 127.0.0.1:5600 shell screencap -p /data/local/tmp/ss.png
adb -s 127.0.0.1:5600 pull /data/local/tmp/ss.png /tmp/ss.png
```

### CRITICAL — Chrome First Run Experience (FRE) Blocks Everything

**The #1 failure mode for ADB-based Chrome automation.** After `pm clear com.android.chrome` or first launch, Chrome shows a FirstRunActivity (terms/privacy acceptance screen). ALL subsequent `am start` intents are queued behind FRE — the target URL NEVER loads.

**Symptoms:**
- `dumpsys window | grep mCurrentFocus` shows `FirstRunActivity` instead of target page
- Script checks "is Chrome in foreground?" → TRUE → reports SUCCESS → but video never loaded
- `pm clear` on every profile rotation RE-TRIGGERS FRE each time

**Fix strategies (in order of reliability):**

1. **Bake FRE into the Docker image** (best — Damru's approach via `bake_image()`):
   The baked image already has FRE dismissed. `python -m damru bake-image` launches Chrome, taps through FRE using `uiautomator dump`, creates Preferences, then commits the image. Every new container starts with `has_preferences()=True` → warm path.

2. **Tap through FRE via uiautomator** (Damru's runtime approach):
   Damru uses `uiautomator dump` to find FRE buttons and taps their center coordinates. Button IDs in priority order: `signin_fre_dismiss_button`, `negative_button`, `no_button`, `signin_fre_continue_button`, `positive_button`. Also handles "Use without an account" text buttons and "Accept & continue" text.
   ```bash
   # Dump UI, find button bounds, tap center
   adb -s $SERIAL shell uiautomator dump /data/local/tmp/ui.xml
   adb -s $SERIAL shell cat /data/local/tmp/ui.xml
   # Parse bounds="x1,y1][x2,y2]" from button ID, tap center: input tap $cx $cy
   # Wait 2s between taps, retry up to 8 times
   ```

3. **Don't `pm clear` on rotation** — use `am force-stop` + proxy change only. Accept that Chrome state accumulates but FRE stays dismissed.

4. **Verify FRE is dismissed** before automation:
   ```bash
   FOCUS=$(adb -s $SERIAL shell "dumpsys window | grep mCurrentFocus")
   if echo "$FOCUS" | grep -q "FirstRunActivity"; then
       echo "FRE STILL ACTIVE — fix before proceeding"
   fi
   ```

### CRITICAL — Page Verification Must Check ACTUAL Content

Checking "Chrome is in foreground" is NOT enough. Chrome foreground can be FRE, settings, download manager, etc.

**Proper verification:**
```bash
# Check the actual URL loaded (not just foreground)
adb -s $SERIAL shell "dumpsys activity top | grep -i 'tiktok\|url\|mCurrentFocus'"
# Or capture a screenshot and inspect visually
adb -s $SERIAL shell screencap -p /data/local/tmp/check.png
adb -s $SERIAL pull /data/local/tmp/check.png /tmp/check.png
```

**PITFALL — ADB quoting in `wsl bash -c`:** Complex ADB commands with pipes, redirects, or nested quotes fail silently inside `wsl -d Ubuntu -- bash -c '...'`. Errors like `adb: unknown command am` indicate quoting broke. Fix: use `execute_code` with individual `terminal('wsl -d Ubuntu -- adb -s ... shell ...')` calls, or write a Python/shell script file in WSL and execute it as one piece.

### Proxy Rotation via ADB

```bash
# Set HTTP proxy (HTTP port = SOCKS port - 1 for SOCKS proxies)
adb -s $SERIAL shell settings put global http_proxy <host>:<http_port>
# Clear proxy
adb -s $SERIAL shell settings put global http_proxy :0
```

**PITFALL:** Android `http_proxy` only works for HTTP/HTTPS traffic via Chrome. Does NOT route through SOCKS5 directly. For SOCKS5 proxies, use Damru's built-in local bridge or configure at the OS level.

## Pitfalls Summary

1. **WSL kernel must be custom** — stock WSL2 kernel has no binderfs
2. **`.wslconfig` kernel path needs double backslashes** (`C:\\Users\\...`)
3. **iptables-legacy required** on most WSL setups (nft backend fails)
4. **config.py is incomplete in both templates** — must add missing vars manually
5. **Chrome trichrome library must install BEFORE Chrome APK**
6. **`adb install-multiple -r` not supported** on ADB 1.0.41 — use pm session API
7. **`--device random` invalid for force-profile** — must name device explicitly
8. **Docker restart loses images** — container data persists but images need reload
9. **Baked image HAS Chrome baked in** — but Chrome native libs may be EMPTY in `lib/x86_64/`. `pm path com.android.chrome` returns paths but `ls <path>/lib/x86_64/` is empty. Chrome activities crash with "Activity class does not exist". **Do NOT push .so files to the filesystem** — Chrome's package has `extractNativeLibs=false`, meaning Android reads native libs directly from the APK, not the filesystem directory. Pushed files are invisible to the linker. This is caused by missing trichrome library — see pitfall #15 for the full diagnosis (UNRESOLVED as of 2026-07-25).
10. **WSL distro reboot needed** after first `wsl --install` before distro is usable
11. **Chrome FRE blocks ALL page loads** — must dismiss before automation; `pm clear` re-triggers it
12. **"Chrome foreground" ≠ "page loaded"** — always verify actual URL/page content, not just activity focus
13. **ADB commands break inside `wsl bash -c` with nested quotes** — use individual calls or script files
14. **Container exit code 255 = container removed** — must `docker run` again, not `docker start`
15. **Trichrome library (220MB+) crashes Redroid PackageManager** — ALL install methods fail: `pm install` → "Broken pipe (32)", `adb install` (streamed) → same Broken pipe, `pm install-create` + `pm install-write` session API → crashes the package service entirely (requires 10s recovery). Increasing container RAM (2g→4g) does NOT fix it. This is a Redroid PackageManager bug with APKs >200MB. ALL trichrome versions across Chrome 143-148 exceed this threshold (213-226MB). **Pushing .so files to the filesystem does NOT work** because Chrome's package has `extractNativeLibs=false` (Android reads libs from APK, not filesystem). **The ONLY reliable fix is `python -m damru bake-image`** which installs trichrome during image build. If trichrome fails to install, the baked image is incomplete — Chrome will be listed in `pm list packages` but all activity launches return "Activity class does not exist".
16. **Container `-v` data volume wipes baked app data** — Without `-v`, container uses image's own `/data` (Chrome pre-installed). With `-v /home/damru/data:/data`, an empty host dir replaces all app data — Chrome must be reinstalled. Always check `pm list packages | grep chrome` after boot.
17. **Chrome activity "does not exist" despite package installed** — usually means the trichrome library package is missing (`pm list packages | grep trichrome` returns nothing). Without trichrome, Chrome's `libmonochrome_64.so` is unavailable and activities can't be instantiated. **Do NOT push .so files to the lib/ directory** — `extractNativeLibs=false` means Android ignores the filesystem. Diagnose: `dumpsys package com.android.chrome | grep extractNativeLibs` shows the flag. Fix: UNRESOLVED as of 2026-07-25 — see pitfall #15. `bake-image` fails, `install-image` downloads image without trichrome, all APK install methods hit Broken pipe. If services are unstable (intermittent "Can't find service: package"), wait for the full readiness check from Step 10 before diagnosing.
18. **ADB quoting breaks with `$SERIAL` in bash** — variables containing `:` (like `127.0.0.1:5600`) get mangled. Use Python `execute_code` with `terminal()` for reliable ADB calls, or hardcode the serial string.
19. **`sys.boot_completed=1` ≠ services ready** — ActivityManager, activity_task, package, and webviewupdate services register AFTER boot_completed. Run the full service check sequence from Step 10 before any `am start`. "Too early to start activity" and "Can't find service: window" are fixed by waiting for `service check package` to return "Service package:", not by waiting longer.
20. **Missing boot args cause silent degradation** — `androidboot.use_memfd=true` and `androidboot.use_redroid_stream=1` are mandatory. Without them, Redroid boots but input/touch and memory allocation are broken.
21. **`docker commit` must stop container first** — Damru stops the container before `docker commit` to ensure a clean OverlayFS snapshot. Committing a running container produces an image with stale file handles.
22. **TikTok views REQUIRE accounts** — Unauthenticated browser sessions, direct API calls, and event replays all fail to increment view count. TikTok requires: (a) real browser, (b) logged-in account, (c) unique IP per view, (d) minimum watch time. Third-party services like tikfollowers.com work because they maintain their own pool of TikTok accounts. To self-host views, you need either: tikapis.com SDK (free tier 1000/day) with Vietnamese SOCKS5 proxies, or Damru + real TikTok accounts on Redroid devices.
23. **Proxy testing must target the ACTUAL site** — Testing SOCKS5 proxies against httpbin.org returns 503 even when proxies work fine. Always test against the actual target (e.g., TikTok). Expect 200 with 300KB+ response size for working proxies.
24. **pproxy SOCKS5 auth format uses `#` not `@`** — Wrong: `socks5://user:pass@host:port`. Right: `socks5://host:port#user:pass`. The `@` format causes pproxy to fail silently.
25. **`extractNativeLibs=false` makes filesystem-pushed .so files invisible** — Chrome's package declares `extractNativeLibs=false`, meaning Android's linker loads native libs directly from the APK zip via mmap, completely ignoring the filesystem `lib/` directory. Verify with `dumpsys package com.android.chrome | grep extractNativeLibs`. This means the old workaround of pushing .so files to Chrome's lib path DOES NOT WORK. Trichrome must be properly installed as a package.
26. **ADB connection drops when PackageManager crashes** — Large APK installs crash Redroid's PackageManager, which cascades to drop the ADB connection. After any failed `pm install` of trichrome, always `adb connect 127.0.0.1:5600` before retrying. Services may be intermittent for 10-15s after a PM crash — run `service check package` before proceeding.
27. **Container zombie state** — Docker containers can become zombies (PID status visible in `docker ps -a` as "Exited (255)"). `docker restart` fails with "container PID is zombie and cannot be killed". Fix: `docker stop --timeout 5 <name>` then `docker rm -f <name>`, then recreate with `docker run`. Always verify with `docker ps` after recreation.
28. **Port conflict on container recreation** — When removing and recreating containers, BOTH the container and port mapping must be fully freed. Old stopped containers still hold port reservations. Check with `docker ps -a --filter name=damru` and remove ALL old containers before recreating. Also check `ss -tlnp | grep 5600` for stray listeners. Bake-image creates temporary containers (named `damru-redroid` by default) that also hold the port — remove these too.
29. **`pm list packages` (with space, not dash)** — The correct Android shell command is `pm list packages` (space-separated). `pm list-packages` (with dash) gives "Unknown command: list-packages". Common typo when scripting ADB commands.
30. **`install-image --download` baked image does NOT have trichrome** — Verified 2026-07-25: a fresh `python -m damru install-image --download` + `docker load` produces an image where Chrome is installed (`pm list packages` shows `com.android.chrome`) but trichrome is absent. Chrome activities fail with "does not exist". This means the upstream build pipeline also hits the trichrome install bug.
31. **Trichrome library sizes for all Chrome versions** — Chrome 143: 213MB, Chrome 144-148: 213-237MB. All exceed Redroid's 200MB PackageManager limit. `vanadium_trichrome_library.apk` (Chrome 143): 243MB. None are installable.
32. **`org.chromium.webview_shell` is NOT a Chrome replacement** — This package is installed in the baked image but it's a minimal test harness for WebView, not a full browser. It cannot handle external URL intents, full page rendering, or JavaScript-heavy sites. Do not attempt to use it for automation tasks that require a real browser.

## References

- `references/damru-config-complete.py` — Known-good config.py with all required variables
- `references/tiktok-automation-notes.md` — TikTok detection mechanisms, ADB workflow, proxy testing methodology
- `references/redroid-troubleshooting.md` — Redroid container boot issues, Chrome native lib fix, trichrome workaround
- `references/tiktok-view-services-reverse-engineering.md` — Reverse-engineered tikfollowers.com/tikapis.com API endpoints, SDK usage, Vietnamese view strategy
- `references/trichrome-investigation-2026-07-25.md` — Exhaustive trichrome install investigation: all methods tried, root cause, fallback options, account-based TikTok view approach
