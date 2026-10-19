---
name: bom-batch-deduplicate
description: Batch similar work and remove duplicate calls.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: quota
    tags: [batching, deduplication, calls]
---

# bom-batch-deduplicate

## When to Use

- Many similar files, records, URLs, prompts, or API requests must be processed.
- Overlapping agents or repeated searches may duplicate work.

## Required Inputs

- Item list and operation.
- Batch limits, ordering constraints, and failure behavior.
- Existing results or cache keys.

## Procedure

1. Normalize inputs and generate stable deduplication keys.
2. Remove exact duplicates and identify near-duplicates requiring one canonical representative.
3. Group items by compatible operation, model requirement, and context size.
4. Choose batch size below provider and context limits with recovery room.
5. Process batches with item-level result tracking so failed items can be retried alone.
6. Merge results in original logical order and report skipped duplicates.

## Decision Rules

- Do not batch non-idempotent writes unless partial failure is safe.
- Do not combine items whose instructions or privacy boundaries differ.
- Prefer one structured request over repeated nearly identical prompts.
- Retry only failed items, not the successful batch.

## Pitfalls

- Creating batches so large that one failure loses all progress.
- Deduplicating records that share text but differ in identity.
- Running multiple agents on the same item.
- Losing source-to-result mapping.

## Verification

- Each unique item has exactly one result or explicit failure.
- Duplicates are traceable to a canonical item.
- Successful items are not reprocessed.
- Batch sizes stay within limits.

## Output Format

- Unique and duplicate counts.
- Batch plan.
- Per-item status.
- Savings summary.
