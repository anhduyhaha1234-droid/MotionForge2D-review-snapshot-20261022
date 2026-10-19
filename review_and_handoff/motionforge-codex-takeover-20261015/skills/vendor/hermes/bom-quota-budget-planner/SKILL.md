---
name: bom-quota-budget-planner
description: Set a task budget for tokens, calls, and retries.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: quota
    tags: [quota, budget, tokens]
---

# bom-quota-budget-planner

## When to Use

- A task is likely to require many tool calls, long files, web research, or several agents.
- The user has limited provider credits, token quota, time, or rate limits.
- A long-running workflow needs a stop rule.

## Required Inputs

- Task outcome and acceptance criteria.
- Known model/provider quota or a relative mode: economy, balanced, maximum-quality.
- Available tools and expected input size.

## Procedure

1. Classify task complexity as simple, bounded, exploratory, or high-risk.
2. Set explicit budgets for model calls, tool calls, retries, context utilization, and output length.
3. Reserve 10 percent of the context window for the final answer and recovery.
4. Allocate most budget to the highest-uncertainty phase, not evenly across all steps.
5. Define checkpoint conditions and what evidence is sufficient to stop research or iteration.
6. Track actual use against the plan and downgrade optional work before mandatory verification.
7. At completion, report budget consumed, savings actions, and unresolved work.

## Decision Rules

- Quality-critical verification is protected before optional breadth.
- Do not start parallel agents unless expected savings exceed coordination cost.
- Do not spend remaining budget polishing an already accepted result.
- When exact quota is unknown, use conservative relative limits and state the assumption.

## Pitfalls

- Using the full quota as a target.
- Setting token limits without reserving final-response capacity.
- Allowing open-ended research.
- Cutting validation before cutting optional exploration.

## Verification

- A budget exists before expensive execution.
- Stop conditions are measurable.
- Actual use is compared with plan.
- The task ends with enough budget for a coherent result.

## Output Format

- Budget mode.
- Limits by phase.
- Stop and escalation conditions.
- Usage summary.
