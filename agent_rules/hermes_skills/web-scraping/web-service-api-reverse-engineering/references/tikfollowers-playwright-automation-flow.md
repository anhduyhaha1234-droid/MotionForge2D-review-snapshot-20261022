# tikfollowers.com Playwright Automation Flow
## Tested: 2026-07-23

## Complete Automation Sequence

### Prerequisites
- Playwright installed with Chromium
- No proxy needed (works from any IP)
- reCAPTCHA currently DISABLED (no CAPTCHA solving needed)

### Step-by-Step Flow

```python
from playwright.sync_api import sync_playwright
import time, re

VIDEO_URL = 'https://www.tiktok.com/@username/video/1234567890123456789'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        viewport={'width': 1920, 'height': 1080},
    )
    page = ctx.new_page()
    
    # 1. Navigate to views page
    page.goto('https://tikfollowers.com/free-tiktok-video-views', 
              timeout=30000, wait_until='networkidle')
    time.sleep(3)
    
    # 2. Wait for Search button to be ready (shows "Loading..." initially)
    page.wait_for_function('''() => {
        const btns = document.querySelectorAll('button');
        for (const b of btns) { 
            if (b.textContent.trim() === 'Search') return true; 
        }
        return false;
    }''', timeout=30000)
    
    # 3. Fill video URL
    page.fill('#inputFieldEl', VIDEO_URL)
    time.sleep(0.5)
    
    # 4. Click Search using expect_response for reliable capture
    with page.expect_response(
        lambda r: 'tikfollowers.com/api/search' in r.url, 
        timeout=20000
    ) as resp_info:
        page.click('button:has-text("Search")', force=True)
    
    search_response = resp_info.value.json()
    print(f"Search result: {search_response.get('status')}")
    # Returns: {status, token, username, aweme_id, user_id, sec_uid, stats}
    
    # 5. Wait for Start Earning button
    time.sleep(2)
    start = page.query_selector('#startProcessBtnEl')
    if not start or not start.is_visible():
        print("Start button not visible - search may have failed")
        # Check for error: video may not exist or be private
    
    # 6. Click Start Earning
    page.click('#startProcessBtnEl')
    time.sleep(2)
    
    # 7. Handle SweetAlert2 modal ("Process Starting - Click OK to continue")
    ok_btn = page.locator('.swal2-confirm')
    if ok_btn.count() > 0:
        modal_text = page.locator('.swal2-modal').inner_text()
        print(f"Modal: {modal_text[:100]}")
        ok_btn.click()
    
    # 8. Wait for progress bar (13-20 seconds, FAKE wait)
    #    The process API call fires AFTER the fake wait completes
    time.sleep(25)  # Wait longer than max fake wait (20s)
    
    # 9. Check for success/error modal
    ok_btn2 = page.locator('.swal2-confirm')
    if ok_btn2.count() > 0:
        result_text = page.locator('.swal2-modal').inner_text()
        print(f"Result: {result_text[:200]}")
        # Success: "Your request for 832 video_views for @user has been completed successfully"
        # Cooldown: "Please wait. You can use this service for 'user' again in approximately X minute(s)"
    
    browser.close()
```

### Key Timing Notes
| Phase | Duration | What Happens |
|-------|----------|-------------|
| Page load | 3-5s | JavaScript initializes, button shows "Loading..." |
| Button ready | 0-10s | Button text changes to "Search" |
| Search API | 1-3s | POST /api/search returns video details + token |
| Start button | 1-2s | Becomes visible after search success |
| Modal | 1s | SweetAlert2 "Process Starting" modal |
| Fake progress | 13-20s | Random setTimeout (config.processWaitTimeSeconds) |
| Process API | 1-3s | POST /api/process fires after fake wait |
| Result modal | 1s | Success or cooldown message |

### Error Handling

**"Failed to fetch video details"** → Video doesn't exist, is private, or TikTok is blocking the request

**"InvalidOrExpiredToken"** → Token not included in process body. Must pass entire search response + type field.

**Cooldown response (429):**
```json
{
    "status": "error",
    "message": "Please wait. You can use this service for 'username' again in approximately 12 minute(s) and 40 second(s).",
    "additional_offers": [...]
}
```

**"Route not found"** → Wrong endpoint path. The only working endpoints are `/api/search` and `/api/process`.

### Direct API Approach (No Browser)

After reverse-engineering, the flow can be done with pure `requests`:

```python
import requests

BASE = 'https://tikfollowers.com'
headers = {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 ...',
    'Origin': BASE,
    'Referer': f'{BASE}/free-tiktok-video-views',
}

# Step 1: Search
r1 = requests.post(f'{BASE}/api/search', 
    json={'input': '1234567890123456789', 'type': 'videoDetails'},
    headers=headers, timeout=15)
data = r1.json()
token = data.get('token', '')

# Step 2: Process (include token!)
payload = {
    'username': data['username'],
    'aweme_id': data['aweme_id'],
    'user_id': data['user_id'],
    'sec_uid': data['sec_uid'],
    'aweme_avatar': data['aweme_avatar'],
    'stats': data['stats'],
    'type': 'video_views',
    'token': token,  # REQUIRED!
}

r2 = requests.post(f'{BASE}/api/process', 
    json=payload, headers=headers, timeout=15)
print(r2.json())
```

**Advantages of direct API:**
- No browser overhead
- Faster execution
- Can run multiple requests in parallel
- No Playwright dependency

**Disadvantages:**
- No visual feedback
- Must handle errors from response JSON
- If reCAPTCHA gets re-enabled, need browser for CAPTCHA solving

### Automation Scaling

For 100K views at ~832 views/cycle with ~13 min cooldown:
- Cycles needed: ~120
- Time per cycle: ~15 min (including overhead)
- Total time: ~30 hours (single session)
- With multiple IPs/proxies: proportional reduction

**Rate limits:**
- ~832 views per cycle
- ~13 minute cooldown per IP per target
- reCAPTCHA currently disabled (may be re-enabled)
