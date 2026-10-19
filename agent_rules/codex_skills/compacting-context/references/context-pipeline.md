# Context Management Pipeline

A five-stage pipeline for managing conversation context within token limits. Stages are ordered from cheapest to most expensive — cheap stages run every turn and often prevent expensive ones from triggering.

## Stage Overview

```
Every turn:
  Stage 1: Tool Result Budget    → Truncate oversized tool outputs
  Stage 2: Snip Compaction       → Remove stale summaries if context outgrew them
  Stage 3: Micro-Compaction      → Deduplicate paths, code, redundant content

When context pressure is high:
  Stage 4: Context Collapse      → Merge sequences of similar tool results
  Stage 5: Auto-Compaction       → Full LLM-driven summarization
```

## Stage 1: Tool Result Budget

Each tool output has a maximum size (default: 50,000 characters). Results exceeding the limit are handled:
- Truncate to the limit with a `[truncated — full result saved to disk]` marker
- Store full result to a temp file on disk
- The agent can read the full result via a file read tool if needed

**Constants:**
- Max result size per tool: 50,000 chars (configurable per tool)
- Max tool result tokens per message: 100,000
- Max tool result bytes per message: 400,000
- Max total tool results per message: 200,000 chars

## Stage 2: Snip Compaction

When context grows past a previous compaction summary, the old summary may be less useful than the actual messages it replaced. This stage removes stale summaries that are no longer covering the most recent context.

## Stage 3: Micro-Compaction

Lightweight in-place compression of redundant content within messages:
- Deduplicate repeated file paths
- Collapse repeated code snippets
- Shorten repeated structural patterns (e.g., long JSON responses with identical shapes)

This is cheap (string operations only, no LLM calls) and runs on every turn.

## Stage 4: Context Collapse

When multiple sequential tool results are similar (e.g., reading 20 files in a row), collapse them into a summary:
- "Read 20 files in `src/components/` — key findings: [summary]"
- Preserves the most recent and most important results
- Summarizes the rest

Triggers only when context utilization exceeds ~80% of the effective window.

## Stage 5: Auto-Compaction

Full LLM-driven summarization of the entire conversation, using the 9-section structured template from the compacting-context skill.

**Trigger:** When total tokens exceed `effectiveContextWindow - 13,000` (buffer).

**Circuit breaker:** After 3 consecutive compaction failures, auto-compaction disables itself. This prevents pathological loops where inherently incompressible context wastes budget on doomed summarization attempts.

## Post-Compaction Re-injection

After compaction replaces the conversation history with a summary, the agent loses awareness of its operational context. Re-inject:

| What | Budget | Why |
|------|--------|-----|
| Recently read files (top 5) | 50K tokens total, 5K each | Agent needs to know what files it was working with |
| Active plan or task list | Unbounded | Agent needs to know what it's supposed to do next |
| Loaded skills | 25K tokens | Agent needs to know its enhanced capabilities |
| Tool descriptions (delta) | As needed | Tools discovered mid-session must survive compaction |
| Sub-agent listing (delta) | As needed | Active sub-agents must be visible |
| MCP server instructions (delta) | As needed | External tool configs |
| Environment facts | ~200 tokens | CWD, OS, git branch, model ID — the agent forgets these |

**Key principle:** Treat post-compaction as a fresh session start. Everything the model needs to function — not just history, but operational context — must survive compaction.

## Prompt Cache Optimization

Split the system prompt into static (cacheable) and dynamic (per-turn) sections:

```
Static prefix (cached across turns):
  - Identity and behavioral rules
  - Security directives
  - Tool preference hierarchy
  - Tone and output style
  ─── CACHE BOUNDARY ───
Dynamic suffix (changes per turn):
  - Environment info (CWD, OS, git state)
  - Memory content
  - Available tools and skills
  - Context window parameters
```

Everything above the boundary stays constant between turns, enabling the LLM provider to cache the KV states. Every token in the dynamic section costs a cache miss — minimize it.
