---
name: bom-cache-friendly-prompting
description: Structure prompts for stable cache reuse.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: quota
    tags: [cache, prompt, prefix]
---

# bom-cache-friendly-prompting

## When to Use

- A provider supports prompt or prefix caching.
- The same system instructions, tools, templates, or references recur across calls.
- A long-running workflow makes repeated calls with a mostly stable prefix.

## Required Inputs

- Provider cache behavior when known.
- Stable instructions and reusable examples.
- Dynamic metadata and current task content.

## Procedure

1. Place stable policy, tool schemas, templates, and reusable examples before dynamic content.
2. Move timestamps, request IDs, counters, and changing state to the end of the prompt or a separate message.
3. Keep whitespace, ordering, and serialization stable across repeated requests.
4. Avoid rewriting long system instructions during a session.
5. Reuse canonical templates and deterministic JSON key ordering where possible.
6. Measure cache-hit tokens or provider cost data before claiming savings.

## Decision Rules

- Do not weaken correctness merely to preserve a cache prefix.
- Do not insert secrets into a reusable shared cache block.
- A single changing character in the stable prefix may invalidate downstream caching.
- Use provider-specific cache controls only when documented.

## Pitfalls

- Putting current time in the system prompt.
- Reordering tool definitions every turn.
- Generating a new verbose plan prefix for each call.
- Assuming caching exists without checking provider behavior.

## Verification

- Stable and dynamic content are separated.
- Repeated calls preserve an identical prefix.
- Cache metrics or cost change are observed when available.
- No stale dynamic data is reused.

## Output Format

- Stable prefix design.
- Dynamic suffix fields.
- Cache measurement.
- Limitations.
