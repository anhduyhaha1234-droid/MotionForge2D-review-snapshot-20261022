---
name: bom-community-pain-miner
description: Mine community discussions for pain points and unmet needs.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: research
    tags: [research, community, pain-points, ux]
---

# bom-community-pain-miner

## When to Use

**Positive triggers:**
- The user wants to find problems people are complaining about.
- A niche assessment needs qualitative pain data.
- The user asks about unmet needs, frustrations, or gaps.

**Negative triggers:**
- The user wants quantitative market data.
- The community is too small for meaningful patterns.
- The task is not research.

## Required Inputs

- Topic or niche to mine.
- Communities to scan: Reddit, forums, Stack Overflow, Twitter/X, Discord, Quora.
- Minimum frequency threshold for a pain point.

## Procedure

1. Identify the most active communities for the niche.
2. Search for complaint-pattern language: "I wish", "frustrated", "can't find", "why isn't there", "hate", "broken", "need alternative", "looking for".
3. Cluster complaints into pain themes.
4. Count occurrences per theme (quantified when possible).
5. For each theme, assess: frequency, intensity, duration (how long people have complained), existing solutions quality.
6. Distinguish between: solved-but-unknown problems, genuinely unsolved problems, and preference complaints.
7. Date-stamp: "Community data retrieved YYYY-MM-DD."

## Decision Rules

- A pain point mentioned 3+ times independently is a signal; 1 mention is anecdotal.
- Do not treat a single Reddit post as a market gap.
- Complaints about pricing are different from complaints about missing features.
- Always check if existing solutions already address the pain.

## Pitfalls

- Selection bias: communities attract complainers, not satisfied users.
- Confusing vocal minority with widespread pain.
- Not checking if the pain is already solved by a lesser-known product.
- Treating all complaints as equally actionable.

## Verification

- Each pain theme has multiple independent mentions with dates.
- Existing solutions for each pain are checked.
- Frequency counts are documented.
- The distinction between solved and unsolved pains is clear.

## Output Format

- Pain theme inventory with frequency and intensity.
- Existing solution assessment per theme.
- Unsolved pain ranking.
- Data sources and retrieval dates.
