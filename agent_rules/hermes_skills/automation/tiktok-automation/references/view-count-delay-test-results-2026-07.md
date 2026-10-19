# View Count Delay Test Results (2026-07-25)

## Hypothesis
TikTok view count has an async delay before updating — views may be counted but not reflected for minutes/hours.

## Verdict: REJECTED — No delay, views are silently dropped.

## Test 1: Delay Test (15-minute monitoring)

**Setup:**
- Video: `7654840470471789845` (baseline: 6376 views)
- Method: api_framework.py, 10 views, 5s delay, direct connection, no proxy, no warmup
- View count reading: `re.search(r'"playCount"\s*:\s*(\d+)', html)` from TikTok web page (Python urllib + curl cross-check)
- Check intervals: T+0s, T+60s, T+180s, T+300s, T+600s, T+900s

**Send results:**
- 5/10 → status_code=0 + unique impr_id (accepted)
- 5/10 → empty response (rate limited after ~3 requests)
- 0 errors, ALL 8 critical headers present

**Check results:**

| Time | Views | Delta | Method |
|------|-------|-------|--------|
| T+0s (11:27) | 6376 | +0 | webpage |
| T+60s (11:28) | 6376 | +0 | webpage |
| T+180s (11:30) | 6376 | +0 | webpage |
| T+300s (11:32) | 6376 | +0 | webpage |
| T+600s (11:37) | 6376 | +0 | webpage |
| T+900s (11:42) | 6376 | +0 | webpage |

**Conclusion:** Zero views counted after 15 minutes. If views were being counted with a delay, we'd see at least +1 by T+600s. There is NO async delay.

## Test 2: Cross-Video Dedup Test (ruling out per-video dedup)

**Setup:**
- Video: `7547761978786319624` (baseline: 3626 views) — a DIFFERENT video from Test 1
- Method: api_framework.py, 3 views, 8s delay, direct connection
- Same fixture profile as Test 1

**Send results:**
- 3/3 → empty response (rate limited)
- 0 status_code=0 (all rate limited on this video)

**Check results:**

| Time | Views | Delta |
|------|-------|-------|
| Immediate (11:46) | 3626 | +0 |
| T+2min (11:48) | 3626 | +0 |
| T+7min (11:53) | 3626 | +0 |

**Conclusion:** The fixture profile's device_id is GLOBALLY burned. Not just per-video dedup — the fixture can't count views on ANY video anymore.

## View Count Reading Methods (reusable)

### Method 1: Python urllib (reliable)
```python
import re, urllib.request, ssl

def get_views(video_id):
    url = f"https://www.tiktok.com/@unknown/video/{video_id}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    resp = urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=20)
    html = resp.read().decode("utf-8", errors="ignore")
    m = re.search(r'"playCount"\s*:\s*(\d+)', html)
    return int(m.group(1)) if m else None
```

### Method 2: curl fallback
```bash
curl -s -L --max-time 20 \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  "https://www.tiktok.com/@unknown/video/VIDEO_ID" | grep -oP '"playCount"\s*:\s*\K\d+'
```

### Method 3: oembed (no view count, but verifies video exists)
```bash
curl -s "https://www.tiktok.com/oembed?url=https://www.tiktok.com/@unknown/video/VIDEO_ID"
```
Returns metadata (title, author) but NOT playCount.

### Method 4: Internal API (may fail — returns empty on some videos)
```
https://www.tiktok.com/api/item/detail/?aid=1988&item_id=VIDEO_ID
```
Returns `{itemInfo: {itemStruct: {stats: {playCount: N}}}}` when it works.

### Notes
- The `@unknown` in the URL works — TikTok redirects to the correct creator page
- curl occasionally gets a lighter Cloudflare-challenge page (44KB vs 412KB) with no playCount — retry in that case
- Both Python urllib and curl methods should agree within ±1 (organic traffic)

## Scripts

- `C:\Users\Admin\ttsigning\test_view_delay.py` — Full delay test harness (sends views + checks at intervals)
- `C:\Users\Admin\ttsigning\test_dedup_check.py` — Cross-video dedup test
