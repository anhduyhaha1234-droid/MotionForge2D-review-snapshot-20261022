---
name: bom-knowledge-gap-loop
description: Identify and iteratively fill knowledge gaps in research.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: research
    tags: [research, gaps, iteration]
---

# bom-knowledge-gap-loop

## When to Use

**Positive triggers:**
- Initial research has gaps that block a conclusion.
- The user asks to go deeper or find missing information.
- A research report has uncertainty markers that need resolution.

**Negative triggers:**
- The research is already complete and cited.
- The user explicitly says to stop researching.
- The gap is in opinion, not fact.

## Required Inputs

- Current research state or draft.
- Identified gaps or uncertainty markers.
- Maximum iteration budget.

## Procedure

1. Parse the current research for claims marked uncertain, inferred, or missing.
2. Rank gaps by impact on the final conclusion.
3. For each high-impact gap, formulate a specific search query.
4. Execute targeted searches with source diversity.
5. Integrate new findings and re-evaluate remaining gaps.
6. Stop when gaps are resolved, budget exhausted, or diminishing returns detected.
7. Document what remains unknown and why.

## Decision Rules

- Maximum 3 iteration loops unless user approves more.
- Each loop must use different search terms or sources than the previous.
- A gap that survives 3 loops gets marked as "unresolvable with available sources."
- Never fill a gap with inference without labeling it.

## Pitfalls

- Infinite loops searching for perfect evidence.
- Lowering evidence standards to close gaps.
- Ignoring that some gaps are genuinely unresolvable.
- Repeating the same search with minor variations.

## Verification

- Every closed gap has new evidence with date and source.
- Remaining gaps are explicitly listed with impact assessment.
- The loop count and quota used are reported.
- No gap was closed with unlabeled inference.

## Output Format

- Gap inventory: open, closed, unresolvable.
- Evidence added per gap.
- Iteration summary with quota cost.
- Final confidence assessment.
