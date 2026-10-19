---
name: bom-niche-opportunity-scorer
description: Score and rank niche opportunities with evidence.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: research
    tags: [research, scoring, opportunities, ranking]
---

# bom-niche-opportunity-scorer

## When to Use

**Positive triggers:**
- Multiple niche candidates need to be compared and ranked.
- The user asks which opportunity is best or most promising.
- A research session needs a final scoring synthesis.

**Negative triggers:**
- Only one niche is being evaluated.
- The user does not want quantitative comparison.
- The task is not research.

## Required Inputs

- List of niche opportunities to score.
- Scoring criteria and weights (or defaults).
- Evidence collected for each opportunity.

## Procedure

1. Define scoring dimensions: demand evidence strength, competition intensity, entry barriers, monetization clarity, scalability, timing (why now), personal fit.
2. Assign weights based on user priorities (default: demand 25%, competition 20%, barriers 15%, monetization 15%, scalability 10%, timing 10%, fit 5%).
3. Score each opportunity on each dimension using evidence from the evidence ledger.
4. Distinguish between scores backed by evidence vs. scores based on inference or assumption.
5. Calculate weighted total and rank opportunities.
6. Sensitivity analysis: how does ranking change if top criterion weight doubles.
7. Each opportunity must have a proposed next validation experiment.

## Decision Rules

- No opportunity scores above 7/10 on any dimension without strong evidence.
- Assumption-backed scores are capped at 4/10.
- The ranking must include a sensitivity check.
- Every opportunity, even the top-ranked, must have a stated risk and validation step.

## Pitfalls

- False precision: scoring 8.3 vs 8.1 when both are based on weak evidence.
- Not disclosing which scores are evidence-backed vs. assumed.
- Ignoring timing and "why now" in favor of static metrics.
- Ranking without proposing next steps.

## Verification

- Each score has evidence backing or is labeled as assumption.
- Weights are explicit and user-approved.
- Sensitivity analysis is performed.
- Validation experiments are proposed for top 3.

## Output Format

- Score matrix: opportunities × dimensions.
- Weighted ranking.
- Evidence quality per score.
- Sensitivity analysis.
- Top 3 with validation experiments.
- Data freshness statement.
