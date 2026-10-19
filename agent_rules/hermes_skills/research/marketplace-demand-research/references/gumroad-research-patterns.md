# Gumroad Marketplace Research Patterns

## URL Structure

### Search / Discover
```
https://gumroad.com/discover?query=<URL-encoded query>&sort=highest_rated
```

Sort options: `highest_rated`, `most_relevant` (default), `newest`
Pagination: `?page=2` appended to existing query

### Category Browsing
```
https://gumroad.com/discover?category=<category-slug>
```

Known category slugs from menu:
- `drawing-painting`, `self-improvement`, `3d`, `design`
- `music-sound-design`, `films`, `software-development`, `gaming`

## What You Can Extract from Search Results

### From the results page snapshot:
- **Product count**: Shown in heading "Showing 1-36 of N products"
- **Product titles**: Full titles visible in article headers
- **Creator names**: Shown as links below each title
- **Ratings**: Shown as "Rating" generic elements (when present)
- **Scarcity badges**: "48 left", "3 left" — demand signal
- **Category tags**: Menu items show available category filters

### What you CANNOT extract from the listing page:
- Price (need to click into product)
- Sales count (not displayed publicly)
- Review count (only star rating visible)
- Product description (need to click in)

## Query Patterns That Work Well

### For AI prompt niche research:
```
"veo 3 prompts"                    — tool-specific, high volume
"seedance prompts"                 — tool-specific, growing
"AI ASMR video prompts"            — format + use case
"AI prompt pack 2025"              — broad + recency
"bigfoot yeti AI video prompts"    — character/format specific
"midjourney sref prompts 2025"     — tool + feature specific
"AI influencer virtual character"  — use case specific
"faceless AI video prompts 2025"   — monetization angle
"chatgpt SEO prompts"              — tool + use case
"AI content creator bundle"        — bundle format
```

### General formula:
```
"<tool> <feature> prompts"         — e.g., "midjourney sref codes"
"<format> <niche> pack"            — e.g., "video ASMR prompts"
"<use case> AI prompts 2025"       — e.g., "monetization AI prompts"
"<viral character> <tool>"         — e.g., "bigfoot veo 3"
"<platform> content prompts"       — e.g., "tiktok viral prompts"
```

## Data Analysis Tips

### Interpreting product counts:
- **200+**: Hot market, high demand, many sellers (e.g., "veo 3 prompts" = 204)
- **50-200**: Growing market, good opportunity
- **20-50**: Established niche, moderate competition
- **10-20**: Emerging or niche market
- **<10**: Early stage or very specific niche

### Title analysis patterns:
- "Ultimate" / "Complete" / "Mega" = premium positioning
- "Viral" = targeting TikTok/Reels/Shorts creators
- "Blueprint" / "System" / "Playbook" = comprehensive guide
- "Faceless" = monetization angle (no face on camera)
- "Updated [Month] 2025" = actively maintained = active market
- "[N]+ Prompts" = volume play (100+, 200+, 500+, 700+)
- Emoji in titles = targeting casual/aspiring creators
- Multiple languages = global market (French, Arabic, Korean products seen alongside English)

### Creator saturation analysis:
- **Many unique creators** = healthy, competitive market (good sign)
- **Few dominant creators** = concentrated market (harder to enter)
- **Same creator with multiple products** = niche leader, study their positioning
- **Creators with ratings** = validated demand
- **Creators without ratings** = new entrants, unvalidated

## Known Limitations (as of July 2025)

- Gumroad does not expose sales data publicly
- Product counts may include inactive/delisted products in some cases
- Search relevance algorithm weights are unknown
- "Load more" button pagination — may need to click through for complete counts
- Category filtering is available but not all products are categorized
- Some products appear under multiple search queries (cross-niche overlap)
