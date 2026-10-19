---
name: bom-context-budget-manager
description: Keep context focused and below safe limits.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: quota
    tags: [context, compression, tokens]
---

# bom-context-budget-manager

## When to Use

- Conversation history, documents, logs, or tool results are growing large.
- The model begins repeating, missing constraints, or approaching its context limit.
- A long task spans several independent phases.

## Required Inputs

- Model context limit when known.
- Current task phase.
- Critical constraints, decisions, unresolved errors, and evidence.

## Procedure

1. Estimate which context category dominates: system, skill catalog, history, retrieved documents, or tool output.
2. Keep a compact task ledger containing goal, constraints, decisions, changed files, unresolved issues, and next action.
3. Remove or summarize resolved observations while preserving exact errors still under investigation.
4. Use targeted retrieval instead of replaying source material.
5. Trigger checkpoint or compression before context pressure damages reasoning; prefer the configured Hermes compressor rather than manual destructive rewriting.
6. Start a clean phase or handoff when the task changes domain and old detail no longer supports the next step.

## Decision Rules

- Preserve user constraints, decisions, identifiers, and current failure evidence.
- Do not summarize data that must remain exact, such as code patches, amounts, or contract fields.
- Do not repeatedly re-read unchanged file regions.
- Context reduction must be measured by relevance, not by deleting the oldest content blindly.

## Pitfalls

- Compressing during active debugging and losing the original error.
- Keeping completed tool output because it might be useful.
- Loading full documents when a section or search result is enough.
- Waiting until the context is almost full.

## Verification

- The active ledger can reconstruct the current task state.
- Critical exact values survive context reduction.
- Resolved bulk output is no longer carried.
- There is reserved capacity for verification and final response.

## Output Format

- Context pressure diagnosis.
- Items preserved.
- Items summarized or dropped.
- Next checkpoint.
