# S02-T03 - PM Review

**Decision:** APPROVED
**Reviewer:** PM/Codex

**Reviewed:** 2026-08-03 21:15 +07:00

## Blocking finding

The worker only renews its lease when a handler calls a progress/checkpoint
callback. A healthy long-running handler that emits no callback can exceed TTL,
be reclaimed, and continue computing under a stale token. AC3 and the approved
contract require periodic heartbeat independent of handler behavior.

Implement a per-claim heartbeat loop using its own short-lived sessions and the
current fence token. It must stop/join on success, exception, cancellation,
shutdown and fencing. Heartbeat conflict/fencing must signal the execution path
to abort before any later mutation/publication. Add deterministic tests for a
silent long handler and heartbeat failure; retain bounded SQLite transactions.

## Final decision

Correction round 2 adds an independent per-claim heartbeat loop with isolated
sessions, thread-safe failure propagation, bounded stop/join and protection of
newer leases. PM independently verified 32 targeted tests, 79 combined tests
and quality baseline `20260803-212653`: all PASS. S02-T04 is released.
