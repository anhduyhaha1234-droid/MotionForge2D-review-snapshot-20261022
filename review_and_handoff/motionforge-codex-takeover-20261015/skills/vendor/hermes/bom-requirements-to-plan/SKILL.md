---
name: bom-requirements-to-plan
description: Turn requirements into a verifiable execution plan.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: coding
    tags: [requirements, planning, acceptance]
---

# bom-requirements-to-plan

## When to Use

- A request requires several implementation steps.
- Requirements are scattered across messages, screenshots, files, or existing behavior.
- The user needs an execution-ready plan rather than generic advice.

## Required Inputs

- User goal.
- Explicit must-have and must-not-have constraints.
- Current project state and technical limits.
- Expected deliverable and deadline when provided.

## Procedure

1. Extract requirements into functional, visual, data, operational, and non-functional groups.
2. Separate confirmed facts from assumptions; resolve only assumptions that can be inspected from available context.
3. Define measurable acceptance criteria for each requirement.
4. Identify dependencies, affected files or systems, and irreversible actions.
5. Order work by prerequisite and risk, keeping each step independently verifiable.
6. Attach a verification method and stop condition to every implementation phase.

## Decision Rules

- Do not silently invent product content, design choices, credentials, or business rules.
- Use exact names, paths, values, and constraints supplied by the user.
- Prefer a smaller complete plan over a broad speculative roadmap.
- Planning output must be executable by another agent without reinterpreting the goal.

## Pitfalls

- Restating the prompt without decomposing it.
- Using vague steps such as “implement the feature.”
- Leaving visual or data acceptance criteria subjective.
- Mixing optional improvements into required scope.

## Verification

- Every user constraint maps to at least one plan step or acceptance criterion.
- Every step has a concrete output and validation method.
- Assumptions are labeled.
- No required item is hidden under “later” or “optional.”

## Output Format

- Goal and scope.
- Requirements matrix.
- Ordered execution plan.
- Acceptance criteria.
- Risks and assumptions.
