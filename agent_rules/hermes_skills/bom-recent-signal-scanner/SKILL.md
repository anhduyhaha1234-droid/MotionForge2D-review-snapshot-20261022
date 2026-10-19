---
name: bom-recent-signal-scanner
description: Scan for recent signals and trends in a niche.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: research
    tags: [research, trends, signals, recent]
---

# bom-recent-signal-scanner

## When to Use

**Positive triggers:**
- The user asks about recent trends, new developments, or what changed in the last 30-90 days.
- A niche assessment needs current signal data, not historical.
- The research involves fast-moving technology or markets.

**Negative triggers:**
- The user wants historical analysis.
- The topic is stable and slow-changing.
- The task is not research.

## Required Inputs

- Niche or topic to scan.
- Time window (default: 30 days).
- Signal types to look for: launches, funding, policy changes, community growth, content velocity.

## Procedure

1. Define signal types relevant to the niche: product launches, funding rounds, policy/regulatory changes, community activity spikes, content publication velocity, hiring patterns.
2. For each signal type, search for the most recent occurrences within the time window.
3. Record each signal with: date, source, signal type, magnitude (quantified when possible).
4. Classify each signal as: strong (multiple confirming sources), medium (single reliable source), weak (single unverified source).
5. Look for signals that contradict the expected trajectory.
6. Date-stamp all findings: "Data retrieved YYYY-MM-DD."

## Decision Rules

- Signals without dates are worthless; always record when the signal occurred and when you retrieved it.
- A single social media post is a weak signal, not evidence.
- Do not extrapolate trends from fewer than 3 data points.
- Distinguish between "growing" and "hyped" signals.

## Pitfalls

- Confusing press releases with organic signals.
- Treating social media buzz as market evidence.
- Ignoring signals in non-English sources for global topics.
- Not distinguishing between signal date and retrieval date.

## Verification

- Every signal has a date and source.
- Signal strength classification is consistent.
- At least 3 signal types were scanned.
- Contradicting signals are included.

## Output Format

- Signal inventory by type with dates.
- Strength classification per signal.
- Trend direction with confidence level.
- Data freshness statement: "All data retrieved YYYY-MM-DD."
