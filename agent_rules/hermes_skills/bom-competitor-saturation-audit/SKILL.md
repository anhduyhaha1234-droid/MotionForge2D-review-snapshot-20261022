---
name: bom-competitor-saturation-audit
description: Audit competitor density and saturation in a niche.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: research
    tags: [research, competitors, saturation, market]
---

# bom-competitor-saturation-audit

## When to Use

**Positive triggers:**
- The user wants to know how crowded a niche is.
- A niche assessment needs competition intensity data.
- The user asks if a market is saturated.

**Negative triggers:**
- The user wants to analyze a single competitor.
- The niche is brand new with no competitors.
- The task is not research.

## Required Inputs

- Niche or market to audit.
- Metrics for saturation: player count, content volume, ad density, price compression.
- Geography or platform scope.

## Procedure

1. Count active players in the niche (products, content creators, services).
2. Assess content saturation: how much quality content already exists for key topics.
3. Check price compression: are margins shrinking, is there a race to the bottom.
4. Look for saturation signals: declining new entrants, consolidation, commoditization.
5. Look for desaturation signals: new niches splitting off, underserved segments emerging.
6. Classify saturation level: unsaturated, emerging, moderately saturated, highly saturated, commoditized.
7. Date-stamp: "Saturation data retrieved YYYY-MM-DD."

## Decision Rules

- Saturation is not inherently bad; some saturated markets have underserved segments.
- Do not rely on a single saturation metric; use multiple signals.
- A market with many low-quality players is different from one with few high-quality players.
- Always check if saturation varies by segment, geography, or channel.

## Pitfalls

- Equating "many competitors" with "no opportunity."
- Not distinguishing between quality and quantity of competition.
- Ignoring that saturated markets validate demand.
- Not checking for emerging desaturation signals.

## Verification

- Multiple saturation metrics are used.
- Saturation level is classified with criteria.
- Both saturation and desaturation signals are documented.
- Segment-level variation is noted.

## Output Format

- Saturation metrics by dimension.
- Saturation level classification.
- Desaturation signals and emerging sub-niches.
- Entry difficulty assessment.
- Data freshness statement.
