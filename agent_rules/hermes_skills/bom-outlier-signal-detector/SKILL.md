---
name: bom-outlier-signal-detector
description: Detect outlier signals that deviate from niche norms.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: research
    tags: [research, outliers, signals, anomalies]
---

# bom-outlier-signal-detector

## When to Use

**Positive triggers:**
- The user asks what is unusual or surprising in a niche.
- A niche assessment needs to identify what stands out from the norm.
- The research involves finding emerging players or unconventional approaches.

**Negative triggers:**
- The user wants average or typical patterns.
- The niche is well-understood with no surprises expected.
- The task is not research.

## Required Inputs

- Niche or market to analyze.
- Baseline metrics for comparison (or let the skill establish one).
- What constitutes an outlier for the user's purpose.

## Procedure

1. Establish baseline metrics for the niche: average pricing, typical features, standard business models, common customer segments.
2. Search for players, products, or approaches that deviate significantly from the baseline.
3. For each outlier, document: what deviates, by how much, with what evidence.
4. Classify outliers as: positive (outperforming), negative (underperforming or failing), novel (different approach).
5. For positive and novel outliers, investigate why they deviate.
6. Check if the outlier is replicable or dependent on unique circumstances.
7. Date-stamp: "Baseline and outlier data retrieved YYYY-MM-DD."

## Decision Rules

- An outlier must be quantifiably different, not just "feels different."
- Do not assume outliers are opportunities; investigate why they exist.
- A single data point is not an outlier; need context from the baseline.
- Distinguish between genuine innovation and unsustainable approaches.

## Pitfalls

- Survivorship bias: only looking at successful outliers.
- Confusing luck or timing with a replicable strategy.
- Not investigating why failed outliers failed.
- Treating every outlier as an opportunity.

## Verification

- Baseline is established with multiple data points.
- Each outlier has quantified deviation from baseline.
- Both positive and negative outliers are documented.
- Root cause analysis is attempted for key outliers.

## Output Format

- Baseline metrics.
- Outlier inventory with deviation magnitude.
- Root cause analysis for key outliers.
- Replicability assessment.
- Data freshness statement.
