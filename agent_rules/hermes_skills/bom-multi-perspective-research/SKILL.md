---
name: bom-multi-perspective-research
description: Research a topic from multiple expert perspectives.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: research
    tags: [research, perspectives, synthesis]
---

# bom-multi-perspective-research

## When to Use

**Positive triggers:**
- The topic has technical, business, legal, and user dimensions.
- A single-perspective answer would miss critical risks or trade-offs.
- The user asks for a comprehensive or balanced analysis.

**Negative triggers:**
- The user wants a single quick answer.
- The topic is purely factual with no interpretive dimension.
- The task is to write content, not research.

## Required Inputs

- Research question or topic.
- List of perspectives to include (or let the skill auto-detect).
- Evidence depth required per perspective.

## Procedure

1. Identify 3-5 relevant perspectives: technical, business, user, regulatory, competitive, academic.
2. For each perspective, define what evidence would be convincing.
3. Search for primary sources from each perspective's domain.
4. Record findings per perspective with source, date, and evidence tier.
5. Identify where perspectives agree, disagree, or reveal blind spots.
6. Synthesize a multi-dimensional answer that surfaces tensions.

## Decision Rules

- Never present only one perspective when multiple exist.
- Label each finding with its perspective origin.
- When perspectives conflict, present both with evidence quality.
- Do not merge perspectives into a false consensus.

## Pitfalls

- Simulating perspectives without real sources.
- Giving equal weight to unequal evidence.
- Ignoring regulatory or legal perspectives on commercial topics.
- Treating blog opinions as equivalent to primary data.

## Verification

- Each perspective has at least one primary or strong secondary source.
- Disagreements between perspectives are explicitly stated.
- The synthesis acknowledges which perspective dominates the conclusion.
- Date of evidence is recorded per perspective.

## Output Format

- Per-perspective findings with citations.
- Agreement/disagreement matrix.
- Synthesis with confidence levels.
- Gaps that require additional perspectives.
