---
name: bom-market-whitespace-mapper
description: Map whitespace areas in a market with low competition.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: research
    tags: [research, market, whitespace, gaps]
---

# bom-market-whitespace-mapper

## When to Use

**Positive triggers:**
- The user wants to find underserved market segments.
- A niche assessment needs competitive landscape mapping.
- The user asks where competitors are not present.

**Negative triggers:**
- The user wants a full market sizing report.
- The market is too small to have meaningful whitespace.
- The task is not research.

## Required Inputs

- Market or niche to map.
- Dimensions to map by: geography, customer segment, price point, feature set, channel.
- Minimum evidence threshold for claiming whitespace.

## Procedure

1. Define the competitive landscape: list known players and their positioning.
2. Map each player across chosen dimensions (segment, price, feature, geography, channel).
3. Identify cells in the map with no or few players.
4. For each whitespace cell, investigate WHY it is empty: no demand, impossible to serve, regulatory barrier, not profitable, or genuine opportunity.
5. Do NOT conclude that whitespace equals opportunity without evidence of demand.
6. Check if whitespace exists because previous attempts failed.
7. Date-stamp: "Competitive landscape data retrieved YYYY-MM-DD."

## Decision Rules

- Whitespace without evidence of demand is "unvalidated," not "opportunity."
- A cell with 1-2 players is "emerging," not "whitespace."
- Low competition may indicate no market, not opportunity.
- Every whitespace claim must include a hypothesis for why it exists.

## Pitfalls

- Concluding "few competitors = opportunity" without demand evidence.
- Ignoring that whitespace may exist due to failed attempts.
- Not checking adjacent markets that serve the same need differently.
- Mapping too many dimensions, creating sparse cells with no signal.

## Verification

- Competitive landscape is based on actual players, not assumptions.
- Each whitespace cell has a hypothesis for its emptiness.
- Demand-side evidence is sought, not assumed.
- Failed attempts or adjacent solutions are documented.

## Output Format

- Competitive landscape map.
- Whitespace inventory with hypotheses.
- Demand evidence per whitespace cell.
- Validation recommendations per whitespace.
- Data freshness statement.
