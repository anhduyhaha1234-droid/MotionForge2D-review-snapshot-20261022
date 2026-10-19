---
name: bom-session-checkpoint-handoff
description: Create compact checkpoints for a new session.
version: 1.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    category: quota
    tags: [handoff, checkpoint, session]
---

# bom-session-checkpoint-handoff

## When to Use

- A session is nearing context or quota limits.
- Work must continue in another model, agent, terminal, or later session.
- A task has reached a clean phase boundary.

## Required Inputs

- Current goal and acceptance criteria.
- Completed actions and changed artifacts.
- Exact unresolved errors, decisions, and next commands.

## Procedure

1. Capture the goal, scope, constraints, and current phase in a compact task ledger.
2. List completed actions with evidence rather than replaying conversation.
3. Record exact file paths, branches, commands, identifiers, and unresolved error text.
4. Separate verified facts from hypotheses and discarded approaches.
5. Specify the next single action and the verification command that follows it.
6. Save the checkpoint to a workspace file when possible and start the new session from that file.

## Decision Rules

- Do not include irrelevant conversational history.
- Preserve exact values that cannot be reconstructed.
- Do not mark hypotheses as decisions.
- A handoff must be actionable without re-reading the old transcript.

## Pitfalls

- Writing a narrative summary without paths or commands.
- Omitting failed approaches so they are repeated.
- Including huge logs instead of the decisive excerpt.
- Starting a new session before saving uncommitted state.

## Verification

- A new agent can state the goal, current state, and next action from the checkpoint alone.
- Changed artifacts and verification status are explicit.
- No critical exact value depends on the old transcript.
- The checkpoint is stored at a known path.

## Output Format

- Checkpoint path.
- Current state.
- Next action.
- Known blockers and proof.
