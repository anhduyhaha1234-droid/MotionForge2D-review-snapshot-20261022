---
name: bom-tool-output-minimizer
description: Reduce file, shell, web, and MCP output volume.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: quota
    tags: [tools, output, tokens]
---

# bom-tool-output-minimizer

## When to Use

- Commands, file reads, searches, or MCP tools may return large output.
- A previous tool result flooded context or repeated unchanged data.

## Required Inputs

- Information needed from the tool.
- Likely output size and available filtering options.
- Whether exact full output must be retained externally.

## Procedure

1. State the exact fields, symbols, lines, files, or records needed before calling a tool.
2. Use search, filters, line ranges, pagination, selectors, SQL projection, grep, head, tail, or structured output.
3. Request metadata first, then retrieve only relevant content.
4. For commands, suppress progress noise and limit logs while preserving errors and summary counts.
5. Store large raw outputs in a file when they must exist, and return only the path plus a focused summary.
6. Avoid returning unchanged content already available in context.

## Decision Rules

- Never truncate the only copy of evidence needed to diagnose a failure.
- Prefer semantic selection over arbitrary first-N truncation.
- Use one well-scoped call instead of many overlapping calls.
- For visual PDFs or screenshots, retrieve only the required pages or frames.

## Pitfalls

- Running recursive listings without depth or exclusions.
- Printing entire lockfiles, minified assets, logs, or API payloads.
- Using broad web queries then opening every result.
- Repeating a tool because its earlier output was not read carefully.

## Verification

- Tool output contains the requested evidence.
- Noise and duplicate data are absent.
- Full raw data is preserved externally when required.
- No follow-up call is needed merely because the first call was too broad.

## Output Format

- Focused result.
- Source path or query.
- Any truncation or filtering applied.
