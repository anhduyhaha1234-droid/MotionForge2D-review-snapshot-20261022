---
name: compacting-context
description: Provides a structured 9-section summarization template for compressing long conversations while preserving critical details. Use when a session approaches context limits and history must be compressed without losing user intent, file changes, errors, or next steps.
---

# Compacting Context

When conversation history must be compressed, use this structured approach to preserve everything needed to continue work without loss.

## Critical rules

- **TEXT ONLY.** Do NOT call any tools during summarization. You already have all the context you need in the conversation above. Tool calls will be rejected and waste your turn.
- Use a **two-phase approach**: first draft your analysis in an `<analysis>` block (scratchpad — will be stripped), then write the final summary in a `<summary>` block.
- Be thorough — this summary **replaces the entire conversation history**. Anything not captured here is lost.

## Template

Your summary MUST include ALL nine sections. If a section has nothing to report, write "None" — do not skip it.

### 1. Primary request and intent
Capture ALL of the user's explicit requests and intents in full detail. Include original wording where precision matters. If the user's intent changed during the conversation, document the evolution.

### 2. Key technical concepts
List all important technical concepts, technologies, frameworks, and domain knowledge discussed. Include version numbers, specific APIs, architectural patterns, and library names.

### 3. Files and code sections
Enumerate every file examined, modified, or created. For each:
- Full file path and what was done (read/edited/created/deleted)
- Why this file matters to the task
- **Full code snippets** for recent or critical changes — these cannot be recovered after compaction
- Summary of changes for files modified earlier in the conversation

### 4. Errors and fixes
Every error encountered and how it was resolved. Pay special attention to:
- **User corrections** ("do it this way instead") — these reflect intent changes
- **Approaches that failed** — include enough detail to avoid retrying them
- **Specific error messages** — exact text, not paraphrased

### 5. Problem solving
Problems solved and solutions applied. Document reasoning chains for non-obvious decisions. Note ongoing troubleshooting that hasn't been resolved.

### 6. All user messages
List ALL non-tool-result user messages **verbatim or near-verbatim**. Do not paraphrase. These capture the user's evolving intent, tone, and feedback. Losing these means losing the ability to understand why decisions were made.

### 7. Pending tasks
Tasks explicitly asked to work on that are not yet complete. Include the user's original wording for each.

### 8. Current work
Describe in detail precisely what was being worked on immediately before compaction. Include:
- File names and paths being edited
- Code snippets of work in progress
- Exact state of progress (what's done, what remains)

### 9. Next step
The single next action, directly aligned with the user's most recent request. Include **verbatim quotes** from the most recent conversation showing exactly what task was being worked on and where it left off. This prevents drift in task interpretation.

## After compaction

Reinject these to restore operational context:
- **Recently read files** (top 5 by recency, up to 50K tokens total)
- **Active plan or task list** (if one exists)
- **Available tool descriptions** (especially any that changed or were discovered during the session)
- **Project instruction files** (ensure the agent still knows about project-level rules)
- **Environment facts** (CWD, git branch, OS — the model forgets these after compaction)

## Scripts

- **[estimate-tokens.sh](scripts/estimate-tokens.sh)** — Estimate token count for files, directories, or stdin. Helps decide when compaction is needed.
  - `./estimate-tokens.sh file1.md file2.ts` — estimate per file
  - `./estimate-tokens.sh src/` — estimate entire directory
  - `./estimate-tokens.sh --context-check 128000` — check against a context window size (warns at 85%+)

## References

For the full context management pipeline (5 stages, trigger thresholds, budget constants, prompt cache optimization):

- **[Context pipeline](references/context-pipeline.md)** — Five-stage preparation pipeline from cheap (every turn) to expensive (on demand), post-compaction re-injection table, and static/dynamic prompt split for cache efficiency.
