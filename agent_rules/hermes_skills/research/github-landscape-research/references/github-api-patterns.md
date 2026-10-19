# GitHub API Patterns for Research

## Search Repos (unauthenticated, 60 req/hr limit)
```bash
curl -s "https://api.github.com/search/repositories?q=tiktok+view+bot&sort=stars&per_page=15" \
  -H "Accept: application/vnd.github.v3+json"
```

## Single Repo Metadata
```bash
curl -s "https://api.github.com/repos/<owner>/<repo>"
```
Key fields: `stargazers_count`, `forks_count`, `pushed_at`, `language`, `archived`, `description`

## List Files in Repo Root
```bash
curl -s "https://api.github.com/repos/<owner>/<repo>/contents/"
```

## Fetch Raw File
```bash
curl -s "https://raw.githubusercontent.com/<owner>/<repo>/main/<path>"
```

## DuckDuckGo HTML Search (bypasses Google's curl blocking)
```bash
curl -s "https://html.duckduckgo.com/html/?q=<URL_ENCODED_QUERY>" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  | grep -oP 'class="result__a"[^>]*href="[^"]*"[^>]*>[^<]*' \
  | sed 's/class="result__a"[^>]*href="//;s/"[^>]*>/\t/'
```

## Paginated DDG Search
```bash
curl -s "https://html.duckduckgo.com/html/" \
  -H "User-Agent: Mozilla/5.0" \
  -d "q=<query>&s=10&nextParams=&v=l&o=json&dc=11&api=d.js"
```

## Notes
- Google returns empty/blocked responses to curl — always use DuckDuckGo
- GitHub API returns `403` with rate limit message when exhausted; check `X-RateLimit-Remaining` header
- Some repos use `master` instead of `main` as default branch — check via contents API or try both
- README badges claiming "WORKING" are often stale; `pushed_at` and issues activity are more reliable signals
