---
name: bom-keyword-adjacency-miner
description: Find adjacent keyword spaces and related search intents.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: research
    tags: [research, keywords, seo, adjacency]
---

# bom-keyword-adjacency-miner

## When to Use

**Positive triggers:**
- The user wants to find related niches or keyword opportunities.
- A niche assessment needs to map the adjacent search landscape.
- The user asks about long-tail or related search intents.

**Negative triggers:**
- The user wants a full SEO campaign.
- Search volume data is not accessible.
- The task is not research.

## Required Inputs

- Seed keywords or niche terms.
- Target market or geography.
- Purpose: content planning, niche expansion, competitor analysis.

## Procedure

1. Start with seed keywords and find semantically related terms.
2. Map adjacency by: synonyms, related problems, adjacent use cases, upstream/downstream intents, "also searched" patterns.
3. For each adjacent keyword cluster, assess: relevance, estimated demand signal (not just search volume), competition level, content gap indicators.
4. Identify keyword spaces where existing content is thin, outdated, or low-quality.
5. Distinguish between informational, navigational, commercial, and transactional intent.
6. Do NOT use SEO aggregation articles as primary evidence for keyword data.
7. Date-stamp: "Keyword landscape data retrieved YYYY-MM-DD."

## Decision Rules

- Search volume alone is not evidence of opportunity; combine with competition, intent, and content quality.
- Do not treat keyword tools' difficulty scores as ground truth.
- Adjacent niches must be genuinely related, not tangentially connected.
- Always verify that keyword demand signals come from primary data (Google Trends, actual search results), not SEO blog posts.

## Pitfalls

- Treating search volume as the only metric.
- Using SEO aggregation articles as primary sources.
- Confusing keyword adjacency with market adjacency.
- Not checking the actual search results for content quality.

## Verification

- Adjacent keywords are semantically connected to the seed.
- Demand signals come from primary or tool data, not blog claims.
- Content gap analysis is based on actual search results.
- Intent classification is consistent.

## Output Format

- Keyword adjacency map.
- Content gap indicators per cluster.
- Intent classification.
- Recommended exploration directions.
- Data freshness statement.
