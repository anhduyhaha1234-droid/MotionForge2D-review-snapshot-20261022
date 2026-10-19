---
name: bom-intersection-niche-generator
description: Generate niche ideas from intersections of adjacent spaces.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: research
    tags: [research, niches, intersections, ideation]
---

# bom-intersection-niche-generator

## When to Use

**Positive triggers:**
- The user wants creative niche ideas beyond the obvious.
- A research session needs to explore cross-domain opportunities.
- The user asks for unique angles or blue ocean strategies.

**Negative triggers:**
- The user already has a specific niche in mind.
- The task is to evaluate a known niche, not discover new ones.
- The task is not research.

## Required Inputs

- Two or more domains or interest areas to intersect.
- Target audience or customer profile.
- Constraints: budget, skills, platform preferences.

## Procedure

1. Map the key themes, needs, and language of each input domain.
2. Generate intersection pairs: what needs from domain A are unmet by solutions in domain B.
3. For each intersection, assess: novelty, evidence of demand, competitive landscape, content feasibility.
4. Filter intersections by the user's constraints.
5. For promising intersections, find at least one signal of demand (not just logical possibility).
6. Rank intersections by: demand evidence, competition gap, feasibility.
7. Each intersection must propose a validation experiment.

## Decision Rules

- Logical possibility is not evidence of demand; every intersection needs at least one signal.
- Do not generate more than 10 intersections without user guidance.
- Each intersection must be specific enough to research further.
- Intersections that have been tried and failed must be noted.

## Pitfalls

- Generating too many vague intersections.
- Treating creative combinations as opportunities without demand evidence.
- Not checking if the intersection already exists.
- Ignoring feasibility constraints.

## Verification

- Each intersection has a demand signal.
- Existing solutions at each intersection are checked.
- Feasibility is assessed against user constraints.
- Validation experiments are proposed.

## Output Format

- Intersection matrix.
- Demand signal per intersection.
- Ranking with reasoning.
- Validation experiment proposals.
