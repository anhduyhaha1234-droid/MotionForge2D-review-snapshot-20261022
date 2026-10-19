# S12-T01 single-wrapper double-dispatch + FROZEN_ACK freeze (2026-09-07)

One background `hermes chat -q "$(cat prompt.md)" -Q` wrapper
(`proc_d6332342cec6`, exit 0) produced TWO worker sessions ~4 min apart on the
SAME task worktree/branch (`s12-s12-t01-0907a` / `codex/s12/s12-t01-0907a`):

| Session | First user msg (VN) | Verdict |
|---|---|---|
| `20260907_083443_186832` | 08:34:46 | KEEP — earlier, owning lane |
| `20260907_083851_481996` | 08:38:54 | FROZEN — duplicate, never resume for work |

## Detection (before any freeze)

1. `dispatch.log` held TWO `session_id:` lines + TWO `DISPATCH_EXIT:0` lines
   (173 B total) — one wrapper invocation, two sessions. Any
   `dispatch.log` with >1 session_id line IS a double-dispatch incident;
   treat the wrapper exit 0 as suspect, not as done.
2. Confirm via state-DB (read-only): both sessions share the exact prompt
   bytes as first user message; earlier first-msg = owner.
3. Confirm no write collision: task-worktree porcelain empty,
   `docs/pm/sessions/S12-T01/` empty dir, allowlist files absent.

## Freeze procedure (rules §4, no third writer)

- Resume the DUPLICATE only, with a freeze order demanding a one-line
  `FROZEN_ACK` and immediate exit (no writes/commits/dispatch/push, no
  resuming other sessions). Verified: `FROZEN_ACK` received, exit 0,
  duplicate msg/tool counts frozen afterwards (26/16).
- Single writer (owner, 78+ msgs) continues untouched. Record both SIDs +
  first-msg times + decision in REGISTRY. Never create a recovery session.

## Nudge-timeout companion lesson

A `-Q` status nudge (`"tiếp tục làm việc đi"`) hit the 600 s Manager-side
timeout while the worker kept progressing (LOG.md baseline landed, allowlist
bytes grew). Before stacking another nudge: check state-DB msg/tool counts +
worktree porcelain — fresh bytes = alive, do NOT re-nudge; only nudge on
8-min zero-advance (tip + porcelain + log growth, not log alone).
