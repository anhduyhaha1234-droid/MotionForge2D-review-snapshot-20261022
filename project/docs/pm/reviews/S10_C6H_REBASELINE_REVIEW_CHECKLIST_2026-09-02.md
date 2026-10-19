# S10-C6H rebaseline and closure — next Codex review checklist

This checklist is not approval. Manager completes it; Codex reproduces the
high-risk rows independently.

## Authority and incident preservation

- [ ] C6G remains labeled `BLOCKED_TEST_AUTHORITY`; no file/report claims exact
      restoration or rewrites the destructive incident.
- [ ] All three 2026-08-30 VSS copies are hashed; one exact 5B3127 ancestor is
      preserved in new C6H evidence without changing its bytes.
- [ ] DAD reconstruction, destroyed backup, state.db exports and every T3
      candidate are immutable and hash-indexed.
- [ ] C15 is a fresh session; both C14 session IDs are terminal and were not
      resumed.
- [ ] Pre/post write-set guards prove no overwrite/copy-over/redirection and no
      production-route drift during the authority phase.

## Rebaselined test authority

- [ ] Retained authority matrix covers 57/57 prior collected contracts and the
      exact 13 VSS-ancestor contracts; every row names its evidence source,
      setup, action, expected result and full durable-state invariant.
- [ ] Five C6G contracts are additive, for exactly 62 unique collected nodes.
- [ ] Every surplus/duplicate current definition has a documented disposition;
      there is no silent deletion or name-only preservation.
- [ ] Zero duplicate test names, unresolved symbols, collection errors, skips,
      xfails, tautological assertions, broad success sets or current-code-derived
      expectation weakening.
- [ ] Real route and fresh isolated SQLite are used; all relevant Job/Run rows
      and mutation counts are asserted.
- [ ] Race tests prove two live participants, rendezvous at the contested
      ownership operation, bounded joins and exact winner/loser outcomes.
- [ ] Manager reran structural audit and authority module independently before
      allowing route writes.

## C6G mechanism and matrix

- [ ] Resolver has typed true-zero, exact, wrong, ambiguous/multiple and
      read/query/parse-error outcomes over the complete durable identity union.
- [ ] Only true-zero repairs; wrong/ambiguous/error paths fail closed with zero
      mutation.
- [ ] Failed Retry ownership uses a real transition. Cancelled Retry ownership
      is the atomic successor insertion or another real version/state change,
      never a same-state rowcount.
- [ ] C6G locked matrix is exactly 14/14 with raw per-row evidence and truthful
      arithmetic in matrix, report, registry and exit packet.

## Exit gates

- [ ] Final hashes freeze before validation; every later result is tied to
      those hashes.
- [ ] Gate order is micro -> 14-row matrix -> focused/static -> broad.
- [ ] Focused/API/workflow and full `tests/test_s10*.py` each pass twice on
      distinct short isolated roots; broad runs are serialized.
- [ ] Ruff F, literal mypy, diff-check, Alembic one-head, OpenAPI operation-ID,
      J1 and protected-data checks pass with raw exits/durations.
- [ ] Unchanged frontend/build/vertical evidence is retained only by verified
      hash equality; changed bytes trigger the relevant rerun.
- [ ] Zero writer/readers at exit, heartbeat removed, ports free, DB guard unset,
      HEAD unchanged, no commit/push/merge.
- [ ] Terminal is exactly
      `S10-C6H = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`.

