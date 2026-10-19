---
name: bom-review-gap-miner
description: Mine product reviews for gaps and improvement signals.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: research
    tags: [research, reviews, products, gaps]
---

# bom-review-gap-miner

## When to Use

**Positive triggers:**
- The user wants to know what customers dislike about existing products.
- A product or niche assessment needs review-based evidence.
- The user asks about feature gaps in competing products.

**Negative triggers:**
- The user wants to write reviews, not analyze them.
- No review data is accessible.
- The task is not research.

## Required Inputs

- Products or categories to analyze.
- Review sources: Amazon, G2, Capterra, App Store, Google Play, Trustpilot.
- Minimum review count threshold.

## Procedure

1. Identify the top 3-5 products in the niche with the most reviews.
2. For each product, scan 1-3 star reviews for recurring complaints.
3. Cluster complaints into themes: missing features, quality issues, pricing, UX problems, support gaps.
4. Quantify theme frequency when review counts are available.
5. Look for cross-product patterns (same complaint across competitors = industry gap).
6. Check if any complaint is addressed by a newer or lesser-known product.
7. Date-stamp: "Review data retrieved YYYY-MM-DD."

## Decision Rules

- A complaint in 5+ reviews across 2+ products is an industry gap.
- Verified purchase reviews carry more weight than unverified.
- Do not extrapolate from review counts below 20.
- Distinguish between product-specific bugs and category-wide needs.

## Pitfalls

- Cherry-picking negative reviews while ignoring positive ones.
- Treating review manipulation (fake reviews) as genuine signal.
- Ignoring that review platforms have selection bias.
- Not checking the date of reviews (old complaints may be resolved).

## Verification

- Each gap theme has multiple independent review sources.
- Review dates are within the relevance window.
- Cross-product patterns are documented.
- Alternative products addressing gaps are identified.

## Output Format

- Gap theme inventory with frequency per product.
- Cross-product gap patterns.
- Opportunity ranking by frequency and intensity.
- Data sources and retrieval dates.
