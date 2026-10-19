---
name: bom-model-routing
description: Choose the cheapest model that can finish safely.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: quota
    tags: [model, routing, cost]
---

# bom-model-routing

## When to Use

- Several models or providers are available.
- Task complexity varies across planning, extraction, coding, review, and synthesis.
- Quota should be preserved without sacrificing critical quality.

## Required Inputs

- Available models, context limits, tool support, and current quota.
- Task complexity, risk, input size, and required output quality.

## Procedure

1. Classify each phase by reasoning depth, context size, tool-use reliability, and consequence of error.
2. Route deterministic extraction, formatting, classification, and summarization to a cheaper capable model.
3. Reserve stronger reasoning models for architecture, ambiguous debugging, security-sensitive review, and final synthesis when needed.
4. Use the same stable model within a tightly coupled reasoning phase to avoid repeated context transfer.
5. Escalate only after a cheaper model fails a defined quality gate, not by instinct.
6. Record the reason for escalation and whether the expensive model materially improved the result.

## Decision Rules

- Never route solely by input length; risk and reasoning difficulty matter.
- The selected model must support required tools and sufficient context.
- Do not move confidential content to an unapproved provider.
- Avoid multi-model fan-out for a task a single cheap model can complete.

## Pitfalls

- Using the flagship model for every phase.
- Using a small model for ambiguous architecture or high-stakes review.
- Escalating repeatedly without a quality test.
- Ignoring context-transfer cost between models.

## Verification

- Each phase has a justified model tier.
- Escalation follows a measurable failure.
- Provider and context constraints are satisfied.
- Quality-critical steps retain adequate capability.

## Output Format

- Routing plan.
- Model tier by phase.
- Escalation gates.
- Observed savings or trade-offs.
