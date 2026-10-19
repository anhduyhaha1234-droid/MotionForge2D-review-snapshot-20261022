---
name: bom-weak-signal-detector
description: Detect weak signals before they become clear trends.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: research
    tags: [research, weak-signals, early-warning, foresight]
---

# bom-weak-signal-detector

## When to Use

**Positive triggers:**
- The user asks about early indicators or emerging opportunities.
- The research needs to detect things before they become obvious trends.
- The user wants foresight, not just current state analysis.

**Negative triggers:**
- The user wants confirmed, well-documented trends.
- The niche moves too slowly for weak signals to matter.
- The task is not research.

## Required Inputs

- Domain or niche to monitor.
- Time horizon for signal relevance.
- Current state baseline.

## Procedure

1. Search for early indicators: academic papers in preprint, patent filings, job postings for new roles, startup seed rounds, regulatory proposals, niche forum discussions, GitHub repos with low stars but active development.
2. For each weak signal, document: source, date, what it suggests, current magnitude.
3. Classify signals by stage: embryonic (single data point), emerging (2-3 confirming signals), early trend (multiple signals with acceleration).
4. Look for convergence: multiple weak signals pointing to the same direction.
5. Check if any weak signals contradict the dominant narrative.
6. Date-stamp: "Weak signal scan date: YYYY-MM-DD."

## Decision Rules

- A weak signal is not evidence; it is an early indicator worth monitoring.
- Never present a weak signal as a confirmed trend.
- Convergence of 3+ weak signals from different source types upgrades classification.
- Always state what would confirm or disprove the signal.

## Pitfalls

- Pattern matching from noise (seeing trends in random data).
- Confirmation bias: selecting weak signals that support a desired conclusion.
- Not stating the failure mode (what would disprove the signal).
- Treating preprint papers as confirmed findings.

## Verification

- Each signal has a source and date.
- Signal stage classification is consistent with evidence count.
- Convergence analysis is documented.
- Disconfirmation criteria are stated for each signal.

## Output Format

- Weak signal inventory by stage.
- Convergence analysis.
- Confirmation/disconfirmation criteria.
- Monitoring recommendations.
- Data freshness statement.
