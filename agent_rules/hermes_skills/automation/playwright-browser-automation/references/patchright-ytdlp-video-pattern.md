# Patchright + yt-dlp Video Download Pattern

## Patchright (Anti-detect Playwright Fork)

Vanilla Playwright gets detected by Facebook/Instagram. Use `patchright` instead — drop-in replacement that patches navigator.webdriver, Canvas fingerprint, etc.

```bash
pip install patchright
patchright install chromium
```

```python
try:
    from patchright.async_api import async_playwright
except ImportError:
    from playwright.async_api import async_playwright

pw = await async_playwright().start()
browser = await pw.chromium.launch(headless=True)
context = await browser.new_context(
    viewport={"width": 1280, "height": 800},
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
)
# Add cookies for authenticated access
await context.add_cookies(cookies_list)
```

## Facebook Reels DOM Scraping

Facebook uses dynamic class names. Target by role/attribute instead:
- Reel links: `a[href*="/reel/"]`, `a[href*="/reels/"]`
- View counts: regex `r'([\d,.]+[KMBkmb]?)\s*(?:views|lượt xem|xem)'` on inner_text
- Parse "1.2M" → 1200000, "500K" → 500000

Without cookies, Facebook redirects to login. Always check `page.url` after navigation.

## yt-dlp Async Subprocess with Progress

```python
cmd = ["yt-dlp", "--no-playlist", "-o", output_template, "--newline", url]
proc = await asyncio.create_subprocess_exec(
    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
)
async for raw_line in proc.stdout:
    line = raw_line.decode(errors="replace").strip()
    # Parse: [download]  42.3% of ~12.5MiB
    match = re.search(r"\[download\]\s+([\d.]+)%\s+of\s+~?([\d.]+\w+)", line)
    if match:
        progress_cb({"percent": float(match.group(1)), "size": match.group(2)})
    # Parse: [download] Destination: /path/to/file.mp4
    dest_match = re.search(r"\[download\]\s+Destination:\s+(.+)", line)
    if dest_match:
        file_path = dest_match.group(1).strip()
```

Key flags: `--newline` forces progress on stdout, `--no-playlist` limits to single video.

## Task Queue Pattern for Downloads

Wrap yt-dlp downloads in asyncio.Task with progress callback that feeds into SSE logger:

```python
async def _download_task(progress_cb, url=url):
    async def _yt_progress(info):
        pct = info.get("percent", 0)
        if pct: progress_cb(int(pct))
    result = await yt_downloader.download(url, on_progress=_yt_progress)
    progress_cb(100)
    return result

task_id = await task_manager.create_task(f"Download: {url}", _download_task)
```

## Windows Pitfalls

- MSYS bash: `&` backgrounding rejected by terminal tool. Use `terminal(background=true)` for servers.
- `patchright install chromium` downloads ~180MB. Takes 20-30s on good connection.
- yt-dlp output paths: use forward slashes or `pathlib.Path` — backslashes can break in subprocess.
