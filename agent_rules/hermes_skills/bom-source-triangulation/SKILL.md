---
name: bom-source-triangulation
description: Cross-verify claims using independent source types.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: research
    tags: [research, verification, sources]
---

# bom-source-triangulation

## When to Use

**Positive triggers:**
- A load-bearing claim is supported by only one source.
- The research conclusion depends on data that could be biased or outdated.
- The user asks to verify or double-check findings.

**Negative triggers:**
- The claim is trivially verifiable (e.g., official documentation).
- Multiple independent sources already agree.
- The task is not research.

## Required Inputs

- The claim to triangulate.
- The existing source(s) for that claim.
- Required confidence level.

## Procedure

1. Classify the existing source: primary, secondary, tertiary; dated or undated.
2. Identify 2-3 independent source types that could confirm or contradict.
3. Search each source type independently (do not follow citations from the first source).
4. Compare findings: confirm, contradict, add nuance, or remain silent.
5. Assign a confidence tier: confirmed (3+ independent), likely (2 independent), unverified (1 source), disputed (conflicting sources).

## Decision Rules

- Two sources from the same origin (e.g., both citing the same paper) count as one.
- A source that merely repeats another without independent verification does not count.
- Contradictory evidence must be presented, not suppressed.
- Date mismatch between sources must be flagged.

## Pitfalls

- Counting citation chains as independent sources.
- Treating SEO aggregation articles as independent verification.
- Ignoring sources in other languages when the topic is regional.
- Presenting "no contradicting source found" as confirmation.

## Verification

- Each triangulation attempt lists source type and independence.
- Confidence tier is assigned with explicit criteria.
- Contradictions are documented with both sides.
- The claim's status changed or stayed the same based on evidence.

## Output Format

- Claim with original source.
- Triangulation sources with type and date.
- Confidence tier and reasoning.
- Remaining risks.
