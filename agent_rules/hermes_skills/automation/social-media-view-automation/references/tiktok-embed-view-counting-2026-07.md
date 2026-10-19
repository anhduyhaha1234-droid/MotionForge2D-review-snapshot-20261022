# TikTok Embed View Counting (2026-07)

## Key Finding: Embed Views DO Count

**Confirmed source (admanage.ai, 2026):**
> "If a video is embedded outside TikTok or shared via link, do those views count? Generally, yes. TikTok videos shared and viewed through links or embeds should count toward the view total, as long as the video actually plays. TikTok's analytics might not specifically break out external views, but the count should still increase."

## TikTok Embed Player (Official Developer API)

**URL format:** `https://www.tiktok.com/player/v1/{video_id}`

**Source:** TikTok for Developers — https://developers.tiktok.com/doc/embed-player

### Parameters

| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `controls` | 0/1 | 1 | Show/hide progress bar, play button, volume, fullscreen |
| `progress_bar` | 0/1 | 1 | Show/hide progress bar (video only) |
| `play_button` | 0/1 | 1 | Show/hide play button |
| `volume_control` | 0/1 | 1 | Show/hide volume control |
| `fullscreen_button` | 0/1 | 1 | Show/hide fullscreen button |
| `timestamp` | 0/1 | 1 | Show/hide playback time |
| `loop` | 0/1 | 0 | Loop video (replays count as views!) |
| `autoplay` | 0/1 | 0 | Auto-play on page load |
| `music_info` | 0/1 | 0 | Show music info |
| `description` | 0/1 | 0 | Show video description |
| `rel` | 0/1 | 1 | 1=show recommended, 0=show author's videos |
| `native_context_menu` | 0/1 | 1 | Browser context menu |
| `closed_caption` | 0/1 | 1 | Closed caption icon |
| `muted` | 0/1 | 0 | Default volume 0, prevent volume change |

### Optimal Parameters for View Generation
```
https://www.tiktok.com/player/v1/{VIDEO_ID}?autoplay=1&loop=1&muted=1&controls=0&rel=0
```
- `autoplay=1` — video plays immediately on page load
- `loop=1` — replays count as additional views
- `muted=1` — prevents user volume interference, most browsers allow muted autoplay
- `controls=0` — hide UI to reduce user interaction
- `rel=0` — show author's videos (not recommended content that might distract)

### How Views Count
- Video must actually **auto-play** — iframe load alone does NOT count
- View starts at playback start (~3 seconds for 3+ min videos, immediate for shorter)
- **Muted plays count**
- **Paused plays count** (initial playback only)
- **Replays and loops DO count** as additional views
- Own views do NOT count (TikTok filters poster's account)
- Views from external embeds count but may not be broken out in analytics

## oEmbed Endpoint

**URL:** `https://www.tiktok.com/oembed?url=VIDEO_URL`

**Returns JSON:**
```json
{
  "version": "1.0",
  "type": "video",
  "title": "Video title",
  "author_url": "https://www.tiktok.com/@username",
  "author_name": "Display Name",
  "width": "100%",
  "height": "100%",
  "html": "<blockquote class=\"tiktok-embed\" ...><script async src=\"https://www.tiktok.com/embed.js\"></script></blockquote>",
  "thumbnail_url": "...",
  "provider_name": "TikTok"
}
```

**Use case:** Programmatically generate embed HTML for any TikTok video URL.

**Pitfall:** New/unindexed videos may return `{"message": "Something went wrong", "code": 400}`. oEmbed doesn't work for all videos.

## embed.js (Legacy Embed Method)

TikTok's legacy embed uses `<blockquote class="tiktok-embed" data-video-id="VIDEO_ID">` with `https://www.tiktok.com/embed.js` script. The Embed Player (`/player/v1/`) is the newer, more controllable method.

## Attack Surface Analysis

- **Embed on high-traffic sites:** Each page load with autoplay generates 1+ views. Loop parameter causes additional views per user.
- **NOT a free exploit:** Requires actual traffic to the embedding page.
- **Browser autoplay policies:** Most browsers require `muted=1` for autoplay. This is why the muted parameter is critical.
- **CSP/iframe restrictions:** Some sites block TikTok embeds via Content-Security-Policy. The embed must be on a page you control.
