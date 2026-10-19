---
name: bom-research-question-decomposer
description: Break a research question into answerable sub-questions.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: research
    tags: [research, decomposition, planning]
---

# bom-research-question-decomposer

## When to Use

**Positive triggers:**
- The user asks a broad, multi-faceted research question.
- The question mixes factual, comparative, and speculative parts.
- A research task will consume significant quota and needs scoping.

**Negative triggers:**
- The question is narrow and answerable with a single search.
- The user wants a quick factual lookup.
- The task is coding, not research.

## Required Inputs

- The original research question or brief.
- Decision the research must support.
- Time and quota constraints.

## Procedure

1. Restate the question in plain language.
2. Separate factual sub-questions (what, when, how many) from evaluative ones (why, which is better, what opportunity exists).
3. Identify which sub-questions need primary evidence and which can be inferred.
4. Order sub-questions by dependency: foundational facts first, synthesis last.
5. Estimate tool calls and token cost per sub-question.
6. Flag sub-questions that risk scope creep and propose a boundary.
7. Produce a decomposition map with dependency arrows.

## Decision Rules

- Every sub-question must be independently answerable or clearly dependent on another.
- Do not decompose into more than 7 top-level branches without user approval.
- Mark each sub-question as: factual, comparative, inferential, or speculative.
- If a sub-question requires access to a paywalled or unavailable source, flag it early.

## Pitfalls

- Over-decomposing into trivial fragments that waste calls.
- Under-decomposing so the research agent still faces an ambiguous question.
- Mixing the research question with the decision question.
- Treating speculative sub-questions as factual.

## Verification

- Every sub-question maps to at least one source type.
- Dependencies are acyclic.
- The sum of sub-questions covers the original question.
- Each sub-question has a clear completion criterion.

## Output Format

- Decomposition map: tree of sub-questions with type labels.
- Dependency order.
- Estimated quota cost per branch.
- Recommended execution plan.
