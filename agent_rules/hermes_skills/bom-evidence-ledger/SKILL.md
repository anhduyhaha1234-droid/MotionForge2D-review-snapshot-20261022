---
name: bom-evidence-ledger
description: Maintain a structured ledger of all research evidence.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: research
    tags: [research, evidence, tracking]
---

# bom-evidence-ledger

## When to Use

**Positive triggers:**
- A research session has collected more than 5 evidence items.
- The user asks for sources, citations, or evidence trail.
- Multiple skills are contributing findings that need consolidation.

**Negative triggers:**
- A single simple lookup with one source.
- The task does not involve research.
- Evidence is already structured in a database.

## Required Inputs

- Evidence items to record (source, claim, date, tier).
- The research question each item supports.

## Procedure

1. Create a ledger entry for each evidence item: source URL, source type, publication date, retrieval date, claim supported, evidence tier, independence flag.
2. Classify each item as: signal (early indicator), evidence (directly supports), inference (derived conclusion), or assumption (no evidence).
3. Link each item to the sub-question or claim it supports.
4. Flag items that are single-source, date-expired, or from non-primary origins.
5. Maintain running counts: total items, by tier, by perspective.
6. At session end, produce a ledger summary.

## Decision Rules

- Every claim in the final report must trace to at least one ledger entry.
- Inference and assumption entries must be explicitly labeled in the output.
- Never merge two distinct sources into one entry.
- Retrieval date is mandatory; publication date is best-effort.

## Pitfalls

- Recording a source URL without opening it.
- Mixing up publication date and retrieval date.
- Losing track of which sub-question an evidence item supports.
- Treating the absence of evidence as evidence of absence.

## Verification

- Every ledger entry has a source URL and retrieval date.
- No entry is labeled "evidence" without a direct supporting relationship.
- The ledger count matches the evidence cited in the final report.
- Inference and assumption entries are clearly separated.

## Output Format

- Ledger table: source, type, date, claim, tier, independence.
- Summary statistics: by tier, by sub-question.
- Gaps: claims with insufficient evidence.
- Confidence assessment per claim.
