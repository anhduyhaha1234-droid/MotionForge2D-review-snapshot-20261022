#!/usr/bin/env python3
"""Reusable TikTok view count reader.

Reads playCount from TikTok web pages using multiple methods.
Use this to verify if views were counted after sending.

Usage:
    python count_views.py 7654840470471789845
    python count_views.py 7654840470471789845 7547761978786319624
"""
import re
import ssl
import subprocess
import sys
import urllib.request


def get_views_urllib(video_id):
    """Read playCount via Python urllib (most reliable)."""
    url = f"https://www.tiktok.com/@unknown/video/{video_id}"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        })
        resp = urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=20)
        html = resp.read().decode("utf-8", errors="ignore")
        m = re.search(r'"playCount"\s*:\s*(\d+)', html)
        if m:
            return int(m.group(1)), "urllib"
    except Exception as e:
        pass
    return None, "urllib"


def get_views_curl(video_id):
    """Read playCount via curl (fallback, may hit Cloudflare)."""
    url = f"https://www.tiktok.com/@unknown/video/{video_id}"
    try:
        result = subprocess.run(
            ["curl", "-s", "-L", "--max-time", "20",
             "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
             url],
            capture_output=True, text=True, timeout=25
        )
        m = re.search(r'"playCount"\s*:\s*(\d+)', result.stdout)
        if m:
            return int(m.group(1)), "curl"
    except Exception:
        pass
    return None, "curl"


def get_views(video_id):
    """Get view count using all available methods. Returns (views, method)."""
    views, method = get_views_urllib(video_id)
    if views is not None:
        return views, method
    views, method = get_views_curl(video_id)
    if views is not None:
        return views, method
    return None, None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} VIDEO_ID [VIDEO_ID ...]")
        sys.exit(1)

    for vid in sys.argv[1:]:
        views, method = get_views(vid)
        if views is not None:
            print(f"  {vid}: {views:,} views (via {method})")
        else:
            print(f"  {vid}: UNAVAILABLE")
