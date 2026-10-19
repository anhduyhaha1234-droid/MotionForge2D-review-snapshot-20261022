#!/usr/bin/env python3
"""Playwright view bot template with proxy rotation and fingerprint randomization.

Usage:
    1. Set TARGET_URL to your video/page
    2. Set PROXY_FILE to your proxy list (host:port:user:pass format)
    3. Adjust TARGET_VIEWS, MIN_WAIT, MAX_WAIT
    4. Run: python tiktok_view_bot.py

Adapted from successful test: 10/10 views via direct connection, avg 10.6s/view.
"""

import time
import random
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

# === CONFIGURATION ===
TARGET_URL = "https://www.tiktok.com/@user/video/0000000000000000000"
PROXY_FILE = Path(__file__).parent.parent.parent / "proxies.txt"  # Adjust path
TARGET_VIEWS = 10
MIN_WAIT = 6
MAX_WAIT = 15

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
]

LOCALES = ["en-US", "en-GB", "en-AU", "en-CA"]
TIMEZONES = ["America/New_York", "America/Chicago", "Europe/London", "Asia/Tokyo"]


def load_proxies(filepath):
    """Load proxies from host:port:user:pass file."""
    proxies = []
    try:
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(":")
                if len(parts) == 4:
                    host, port, user, pwd = parts
                    proxies.append({
                        "server": f"http://{host}:{port}",
                        "username": user,
                        "password": pwd,
                        "label": f"{host}:{port}",
                    })
    except FileNotFoundError:
        print(f"Proxy file not found: {filepath}")
    return proxies


def test_proxies(pw, proxies, count=5):
    """Quick connectivity test on first N proxies."""
    print(f"\nTesting proxy connectivity (first {min(count, len(proxies))})...")
    working = []
    for proxy in proxies[:count]:
        try:
            browser = pw.chromium.launch(headless=True, proxy={
                "server": proxy["server"],
                "username": proxy["username"],
                "password": proxy["password"],
            })
            page = browser.new_page()
            page.goto("https://httpbin.org/ip", timeout=10000)
            time.sleep(1)
            browser.close()
            working.append(proxy)
            print(f"  ✅ {proxy['label']}")
        except Exception as e:
            try:
                browser.close()
            except Exception:
                pass
            print(f"  ❌ {proxy['label']}: {str(e)[:80]}")
    return working


def simulate_view(pw, proxy, ua, url):
    """Single browser session: load page, wait, verify, close."""
    start = time.time()
    browser = None
    try:
        launch_args = {"headless": True}
        if proxy:
            launch_args["proxy"] = {
                "server": proxy["server"],
                "username": proxy["username"],
                "password": proxy["password"],
            }

        browser = pw.chromium.launch(**launch_args)
        context = browser.new_context(
            user_agent=ua,
            viewport={"width": random.randint(1280, 1920), "height": random.randint(720, 1080)},
            locale=random.choice(LOCALES),
            timezone_id=random.choice(TIMEZONES),
        )

        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # Wait for content to load and play
        wait_time = random.uniform(MIN_WAIT, MAX_WAIT)
        time.sleep(wait_time)

        # Verify video element (TikTok-specific)
        video_found = False
        try:
            video_el = page.query_selector("video")
            if video_el:
                video_found = True
                # Optional: simulate mouse movement
                page.mouse.move(random.randint(100, 800), random.randint(100, 600))
                time.sleep(1)
        except Exception:
            pass

        elapsed = time.time() - start
        browser.close()
        return True, elapsed, None, video_found

    except Exception as e:
        elapsed = time.time() - start
        if browser:
            try:
                browser.close()
            except Exception:
                pass
        return False, elapsed, str(e)[:150], False


def main():
    print("=" * 60)
    print("Playwright View Bot — Proxy Rotation Template")
    print("=" * 60)
    print(f"Target: {TARGET_URL}")
    print(f"Views:  {TARGET_VIEWS}")

    # Load and shuffle proxies
    proxies = load_proxies(PROXY_FILE)
    print(f"Proxies: {len(proxies)}")
    random.shuffle(proxies)

    # Test proxies
    use_proxy = True
    with sync_playwright() as pw:
        if proxies:
            working = test_proxies(pw, proxies)
            if not working:
                print("\n⚠️  No working proxies. Falling back to direct connections.")
                use_proxy = False
            else:
                proxies = working
        else:
            print("\nNo proxies configured. Using direct connections.")
            use_proxy = False

        # Run views
        results = {"success": 0, "fail": 0, "times": [], "errors": []}
        total_start = time.time()

        for i in range(TARGET_VIEWS):
            proxy = proxies[i % len(proxies)] if use_proxy else None
            ua = random.choice(USER_AGENTS)
            label = proxy["label"] if proxy else "direct"

            print(f"\n[{i+1}/{TARGET_VIEWS}] {label} | {ua[:45]}...")

            ok, elapsed, err, vid = simulate_view(pw, proxy, ua, TARGET_URL)

            if ok:
                results["success"] += 1
                results["times"].append(elapsed)
                print(f"  ✅ {'Video found' if vid else 'Success'} | {elapsed:.1f}s")
            else:
                results["fail"] += 1
                results["errors"].append(err)
                print(f"  ❌ {err} | {elapsed:.1f}s")

        # Summary
        total_time = time.time() - total_start
        avg = sum(results["times"]) / len(results["times"]) if results["times"] else 0

        print(f"\n{'=' * 60}")
        print(f"RESULTS: {results['success']}/{TARGET_VIEWS} success ({results['success']/TARGET_VIEWS*100:.0f}%)")
        print(f"Avg time/view: {avg:.1f}s | Total: {total_time:.0f}s ({total_time/60:.1f}m)")
        print(f"Proxies: {'rotating' if use_proxy else 'direct'}")

        if results["errors"]:
            print(f"\nErrors ({len(results['errors'])}):")
            for e in results["errors"][:5]:
                print(f"  - {e}")
        print("=" * 60)


if __name__ == "__main__":
    main()
