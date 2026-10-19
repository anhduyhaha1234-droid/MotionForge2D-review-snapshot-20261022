---
name: bom-usage-audit
description: Audit quota use and find the biggest waste.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: quota
    tags: [usage, audit, cost]
---

# bom-usage-audit

## When to Use

- Provider credits disappear faster than expected.
- A workflow needs evidence-based quota optimization.
- Token, tool-call, model, or retry logs are available.

## Required Inputs

- Usage logs by model, session, task, or provider.
- Expected task volume and quality targets.
- Current pricing or quota rules when available.

## Procedure

1. Collect input tokens, output tokens, cached tokens, calls, retries, tool-output size, latency, and failures by task phase.
2. Normalize metrics per successful task rather than per request only.
3. Rank waste sources: oversized context, repeated reads, broad tool output, failed retries, wrong model tier, duplicate agents, or excessive final output.
4. Estimate savings for the top three interventions using transparent assumptions.
5. Change one major control at a time and compare against a baseline.
6. Reject optimizations that reduce measurable quality beyond the accepted threshold.
7. Produce a recurring audit checklist and alert thresholds.

## Decision Rules

- Use current provider prices or label cost estimates as approximate.
- Do not optimize only average cost; inspect expensive outliers.
- Separate cached and uncached input where providers report both.
- A cheaper failed task is not an optimization.

## Pitfalls

- Relying on total monthly tokens without task attribution.
- Changing several controls and losing causal evidence.
- Ignoring tool calls because they are not billed as tokens.
- Reporting percentage savings without a baseline.

## Verification

- Metrics are tied to successful tasks.
- Top waste sources are quantified.
- Recommended changes have measurable gates.
- Quality and completion rate remain visible.

## Output Format

- Baseline metrics.
- Waste ranking.
- Prioritized interventions.
- Post-change comparison plan.
