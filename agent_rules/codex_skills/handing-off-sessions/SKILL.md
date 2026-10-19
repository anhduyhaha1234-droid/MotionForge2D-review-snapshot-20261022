---
name: handing-off-sessions
description: Captures structured session state for resuming work in a new session or handing off to another agent. Use at the end of a session, before context limits, or when the user asks to save progress. Not needed for trivial sessions (quick questions, one-line answers).
---

# Handing Off Sessions

Create a handoff document that lets any agent resume work cold — without access to prior conversation history.

## When to create
- End of a work session with meaningful progress
- Context window approaching limits
- Switching between agents or tools
- User explicitly asks to save progress

## When NOT to create
- Trivial sessions (quick questions, one-line fixes, informational queries)
- Session where no files were modified and no ongoing work exists

## Storage

Save handoff documents to `.agent/handoffs/` at the project root. Name files with a timestamp and brief slug: `2025-04-07-auth-middleware.md`.

If the project already has an agent state directory (`.claude/`, `.cursor/`, etc.), use that instead. Create `.agent/` on first use and add to `.gitignore` unless the team wants shared agent state.

## Template

Every section must be filled. Use "N/A" only if genuinely not applicable.

```markdown
# Session: [5-10 word descriptive title — info-dense, no filler]

## Current state
What is actively being worked on right now.
Pending tasks not yet completed.
Immediate next steps when resuming.

## Task specification
What the user asked to build or fix.
Key design decisions made and why.
Constraints or preferences the user specified.

## Important files
| File | Role | Status |
|------|------|--------|
| /absolute/path/to/file.ts | Main implementation | Modified — added auth middleware |
| /absolute/path/to/test.ts | Test suite | Passing after fix |
| /absolute/path/to/config.ts | Configuration | Read only — contains DB settings |

## System architecture
How the relevant components fit together.
Data flow between services if applicable.
Key interfaces or contracts between modules.

## Workflow
Commands to run and in what order. Include expected output.
```bash
npm test -- --filter auth    # expect: 12 passing, 0 failing
npm run build                # expect: no type errors
npm run lint                 # expect: clean
```

## Errors and corrections
Errors encountered and how they were fixed.
What the user corrected — include their exact words if possible.
Approaches that failed and MUST NOT be retried:
- [approach] — [why it failed]

## Learnings
What worked well. What did not. Patterns to follow or avoid.
Project-specific conventions discovered during the session.

## Key results
If the user asked for specific output (answers, tables, analysis,
documents), include the exact result here — it cannot be regenerated.

## Worklog
One line per step. Terse. Chronological.
- Explored auth module structure
- Found race condition in session.ts:45
- Fixed with SELECT FOR UPDATE + transaction
- Tests passing (12/12)
- User requested: also add rate limiting (not started)
```

## Guidelines
- Write for someone with **zero context**. No shorthand, abbreviations, or codenames without explanation.
- Use **absolute file paths**, never relative.
- Include **exact command outputs** for critical results that would be expensive to regenerate.
- The document alone must be **sufficient to continue** — no "see previous conversation" references.
- Keep the worklog **dense but complete** — one line per meaningful action, not one line per tool call.

## Scripts

- **[gather-session-context.sh](scripts/gather-session-context.sh)** — Collects CWD, OS, git state (branch, recent commits, modified/staged/untracked files), project type, recent files, and directory structure in one shot. Run this to auto-populate the Environment, Important files, and System architecture sections.
  - `./gather-session-context.sh` — current directory
  - `./gather-session-context.sh /path/to/project` — specified directory
