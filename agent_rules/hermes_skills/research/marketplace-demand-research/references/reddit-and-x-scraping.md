# Scraping Reddit & X/Twitter When APIs Are Blocked (2025+)

## Reddit Scraping via old.reddit.com

Reddit's API (`.json` endpoints) and new reddit return **403 Blocked** for automated requests, even with realistic User-Agents. The reliable workaround is **old.reddit.com HTML scraping**.

### Working Endpoint Pattern
```
https://old.reddit.com/r/{SUBREDDIT}/top/?sort=top&t={TIMEFRAME}
```
- Valid timeframes: `hour`, `day`, `week`, `month`, `year`, `all`
- Works with `curl` and basic User-Agent headers
- No authentication required

### Extracting Post Data from HTML

Use `grep -oP` with these patterns (all return values in matching order, so they can be correlated by position):

```bash
# Post titles + links
grep -oP '<a[^>]*class="[^"]*title[^"]*"[^>]*>[^<]+</a>'

# Upvote scores (one per post, in order)
grep -oP 'data-score="[^"]*"'

# Comment counts
grep -oP 'data-comments-count="[^"]*"'

# Permalink paths (build full URL with https://old.reddit.com{PERMALINK})
grep -oP 'data-permalink="[^"]*"'

# Domain (self vs link posts)
grep -oP 'data-domain="[^"]*"'
```

### Correlating Fields
All grep patterns extract values **in document order**, so index N of each pattern corresponds to the same post. Extract all patterns from the same page HTML to build a structured dataset.

### Key Subreddits by Niche
| Subreddit | Focus | Typical Top Score (week) |
|-----------|-------|--------------------------|
| r/ChatGPT | General ChatGPT memes/discussion | 3,000–12,000 |
| r/PromptEngineering | Practical prompt techniques | 50–400 |
| r/midjourney | MJ image generation | 200–700 |
| r/aivideo | AI video generation (Sora, Kling, Veo) | 500–6,000 |
| r/soraAI | OpenAI Sora specific | 100–500 |
| r/StableDiffusion | SD/ComfyUI ecosystem | 200–1,000 |
| r/LocalLLaMA | Local models, open source AI | 500–3,000 |

### Pitfalls
- HTML returns ~25 posts per page; paginate with `?after=t3_XXXXX` for more
- old.reddit.com does NOT expose vote ratio or awards in HTML
- Rate limiting kicks in after ~30 rapid requests; add 1-2s delays
- Permalink extraction is more reliable than title extraction for matching to scores
- Subreddit names are case-sensitive in URLs

---

## X/Twitter Search via Search Engines

X/Twitter blocks all automated access (API requires paid tier, website requires login). Workaround: use search engines that index tweets.

### Brave Search Pattern
```
https://search.brave.com/search?q="{KEYWORD}"+site:x.com+2025&tf=pw
```
- Extract tweet URLs: `grep -oiP 'https://x\.com/[a-zA-Z0-9_]+/status/[0-9]+'`
- Use `sort -u` to deduplicate
- Brave may show CAPTCHA slider; retry or fall back to DuckDuckGo

### DuckDuckGo HTML Endpoint (fallback)
```
https://html.duckduckgo.com/html/?q={QUERY}
```
- Lightweight text-only results, less likely to CAPTCHA
- Form-based; may need to submit a hidden form with checkboxes

### What You CAN'T Get Without Login
- Tweet engagement metrics (likes, retweets, replies, views)
- Real-time trending topics
- Full tweet text (search engines show truncated snippets)
- User follower counts

### Workaround for Engagement Data
If you need tweet engagement metrics, use the browser tool to load x.com directly (sometimes works for public profiles) or note the limitation in your output.
