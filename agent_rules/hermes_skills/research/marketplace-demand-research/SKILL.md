---
name: marketplace-demand-research
description: >
  Research product demand and niche trends using marketplace data (Gumroad, Etsy,
  Udemy, Amazon, Fiverr, etc.). Uses product counts, title analysis, and quality
  signals as demand proxies. Primary fallback when Google Trends, Reddit, and
  search engines are blocked by CAPTCHAs. Use when the user asks "what's trending
  in X", "what products are selling", "find the best niche for Y", or any
  demand/trend research for digital or physical products.
tags: [research, marketplace, demand, trends, gumroad, niche, product-research, osint]
---

# Marketplace Demand Research

Systematically research product demand and niche trends using marketplace data as a demand proxy. This is the primary research path when Google Trends, Reddit, and search engines are blocked by CAPTCHAs.

## When to Use

**Positive triggers:**
- User asks "what's trending in X" or "what products are selling"
- User wants niche validation or demand signals for a product idea
- User asks to find the best niche for a digital product, prompt pack, template, course, etc.
- Google Trends, Reddit, and search engines are returning CAPTCHAs
- User wants competitive landscape analysis on a marketplace

**Negative triggers:**
- User wants SEO keyword data (use keyword tools instead)
- User wants to analyze a single product's sales (use direct product page)
- The topic has no marketplace presence (e.g., academic research, policy)

## Procedure

### Step 1: Choose the Right Marketplace

| Product Type | Best Marketplace | URL Pattern |
|---|---|---|
| Digital products / prompt packs | **Gumroad** | `gumroad.com/discover?query=<q>` |
| Templates / design assets | **Creative Market** | `creativemarket.com/search?q=<q>` |
| Courses / info products | **Udemy** | `udemy.com/courses/search/?q=<q>` |
| Handmade / digital downloads | **Etsy** | `etsy.com/search?q=<q>` |
| Freelance services | **Fiverr** | `fiverr.com/search/gigs?query=<q>` |
| Physical products | **Amazon** | `amazon.com/s?k=<q>` |
| Software / apps | **Product Hunt** | `producthunt.com/search?q=<q>` |
| SaaS reviews | **G2** | `g2.com/search?query=<q>` |

### Step 2: Run Multiple Query Variations (5-10)

Search the marketplace with variations covering the niche from different angles. Record the **product count** for each query. This is your primary demand signal.

**Query pattern formula:**
```
1. "<exact niche> prompts"        — core term
2. "<exact niche> 2025"           — recency angle
3. "<tool name> prompts"          — tool-specific
4. "<format> <niche>"             — format-specific (e.g., "video prompts")
5. "<use case> <niche>"           — use-case specific (e.g., "viral ASMR")
6. "<adjacent niche>"             — adjacent market
7. "<broad category> pack"        — broader category
8. "<character/entity> prompts"   — specific viral format
9. "<platform> <niche>"           — platform-specific
10. "<monetization angle>"        — money-making angle
```

### Step 3: Record Product Counts and Analyze

For each query, record:
- **Product count**: Raw number from marketplace results header
- **Top 3-5 product titles**: Reveal sub-niche patterns, bundling strategies, price positioning
- **Creator names**: Repeat creators = niche leaders; many small creators = healthy market
- **Quality signals**: Ratings, review counts, "X left" badges, "Updated" dates

### Step 4: Analyze Product Titles for Sub-Niche Signals

Product titles are a goldmine. They reveal:
- **Hot sub-niches**: What topics appear in 3+ titles = trending sub-niche
- **Bundling patterns**: What gets combined = buyer expectations
- **Price anchoring**: "Ultimate" = premium, "Starter" = entry-level, "Mega Pack" = volume play
- **Platform targeting**: TikTok vs YouTube vs Instagram = different buyer segments
- **Update recency**: "Updated August 2025" = active market with changing needs

### Step 5: Cross-Reference with Accessible Sources

Even when major sources are blocked, these often work:
- **old.reddit.com**: HTML scraping works even when Reddit API/JSON returns 403. See `references/reddit-and-x-scraping.md` for extraction patterns.
- **Bing News search**: Less aggressive CAPTCHA than web search
- **YouTube search**: Video titles and view counts = trend signal
- **Direct platform pages**: Official product announcements, changelog pages
- **Hacker News / Lobsters**: Developer-focused trend discussions
- **Brave Search + site:x.com**: Finds indexed tweets even when X is inaccessible directly. See `references/reddit-and-x-scraping.md` for patterns.

### Step 6: Produce Structured Analysis

See output format below.

## Decision Rules

- **Product count as demand proxy**: More products = more sellers = more buyers. This is the core assumption. Validate with quality signals (reviews, ratings).
- **Multiple queries required**: A single query can be misleading. 5-10 queries triangulated give reliable signals.
- **Title analysis > count alone**: Two niches with equal product counts can have very different dynamics. Title analysis reveals whether it's growing or saturated.
- **Date-stamp everything**: "Data retrieved YYYY-MM-DD" on all findings.
- **Don't confuse supply with demand**: A market with many low-quality products might be oversaturated, not high-demand. Look for quality signals.

## Pitfalls

- **Using a single query**: Always run 5+ variations. Different phrasings surface different products.
- **Ignoring quality signals**: Product count alone doesn't tell you if buyers are satisfied. Check ratings and reviews.
- **Platform bias**: Gumroad skews creator/side-hustle. Etsy skews handmade+digital. Udemy skews education. Pick the right platform.
- **Survivorship bias**: Dead products get delisted. What you see is surviving supply, not total historical demand.
- **Giving up when search engines block**: Marketplace direct search is MORE reliable than Google Trends for niche research. Treat CAPTCHAs as a signal to go direct, not as a blocker.
- **Not reading product descriptions**: Titles tell you the niche. Descriptions tell you the value proposition and buyer objections.
- **Confusing bundles with single products**: A "150K AI Prompts" bundle competes differently than a focused "50 Veo 3 ASMR Prompts" pack. Note the difference.

## Output Format

### Marketplace Demand Analysis: [Niche Name]

**Data retrieved: YYYY-MM-DD**
**Marketplace(s) searched: [list]**

#### Product Count by Query

| Search Query | Products Found | Signal Strength |
|---|---|---|
| "query 1" | N | 🔥🔥🔥 / 🔥🔥 / 🔥 / 🟡 |

#### Top 3 Trending Sub-Niches

For each:
1. **Topic name**
2. **Why it's hot** (evidence from product counts + titles)
3. **Target audience**
4. **Sample prompt/product categories** (5-8 specific categories)
5. **Differentiation angle** (how to enter this niche with a unique position)

#### Quality Signals

- Products with ratings/reviews: count and range
- Recently updated products: count
- Repeat creators (niche leaders): names and product counts
- Price range observed: min-max

#### Recommended Action

- Best niche to enter and why
- Suggested product structure (categories, count, bonus items)
- Price sweet spot based on competitor analysis
- Cross-sell / upsell opportunities

#### Data Limitations

- Which sources were blocked and why
- What data is missing that would improve the analysis
- Confidence level per finding (high/medium/low)

## Linked Files
- `references/gumroad-research-patterns.md` — Gumroad-specific search patterns, URL structures, and parsing tips
- `references/reddit-and-x-scraping.md` — Reddit HTML scraping via old.reddit.com and X/Twitter search via Brave/DuckDuckGo when APIs are blocked
