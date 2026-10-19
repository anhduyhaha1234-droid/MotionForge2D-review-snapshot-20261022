# S10-C6G next-review readiness checklist

This is a Codex review-routing checklist, not approval and not a substitute for
the canonical rules or the binding C14 recovery prompt. Manager must include a
completed copy in the C6G exit packet; Codex independently rechecks every row.

## A. Incident and source authority

- [ ] Actual writer session is reconciled against read-only Hermes state.db,
      not inferred only from registry prose.
- [ ] Zero writer/process/listener proof is newer than the final worker output.
- [ ] Pre-C14 API-test candidate SHA equals
      `963ED50E350ABB5441829737149867D488462AC6DF6C5FA38F01C3DFD758CBC3`.
- [ ] Deterministic state.db extraction/replay script, ordered message ledger and
      raw payload hashes are retained under C6G evidence, not only `%TEMP%`.
- [ ] Main API test was restored only after exact candidate match; no
      `write_file`, full overwrite, copy-over, redirection or memory rebuild.
- [ ] Exact 57 retained pytest node IDs are archived before the C6G delta.
- [ ] Final API module has exactly 62 unique collected nodes: 57 retained + five
      C6G nodes; no missing retained node, duplicate test definition or
      unresolved helper/class/name.
- [ ] `write_set_guard.py` capture/verify reports and byte snapshots exist; the
      route stayed at the Phase-A protected hash until recovery R-GATE.

## B. Contract and mechanism

- [ ] One durable-job resolver searches the union of canonical key,
      deterministic generation, stored manifest run/project/plan identity and
      workspace/owner identity; it does not rely on only one field.
- [ ] Resolver outcomes are typed: true zero, exact one, wrong one,
      multiple/ambiguous and query/read/parse error.
- [ ] Only true zero may repair. Every wrong/ambiguous/error case fails closed
      with exact all-row and zero-mutation evidence.
- [ ] Failed Retry ownership uses a real state transition.
- [ ] Cancelled Retry ownership is the actual atomic successor insertion or a
      real version/state transition, never same-state rowcount.
- [ ] Winner count is instrumented at the ownership operation; a downstream
      unique constraint is not used as sole proof.

## C. Test structure and independent micro evidence

- [ ] G1-I1..I7 and G2-R1..R5 each map to an exact test, source location,
      expected HTTP result, all Job/Run rows and mutation count.
- [ ] Every race has two live participants, a barrier at the contested
      operation, bounded joins, rendezvous proof, raw outcomes and all-row
      lifecycle assertions.
- [ ] Manager independently reran ambiguity, resolver error, true orphan,
      valid replay, direct cancelled claim, failed/cancelled Retry races and
      replay-vs-Retry on fresh isolated DBs.
- [ ] Codex-facing evidence distinguishes sequential controls from races.

## D. Gate order and arithmetic

- [ ] Final source/test hashes were frozen before closure gates.
- [ ] Gate order was `micro -> matrix 14/14 -> focused/static -> final broad`.
- [ ] No broad run was used to waive an open micro/matrix row.
- [ ] Focused/API/workflow ran twice on distinct short roots.
- [ ] Full `tests/test_s10*.py` ran twice, serialized, after final bytes.
- [ ] Ruff, mypy, diff-check, Alembic one-head, OpenAPI operation-ID, J1 and
      protected-hash checks are raw and successful.
- [ ] Matrix, REPORT, registry and EXIT all say exactly 14/14; no stale 15/6 or
      contradictory pass/fail count remains.

## E. Review packet and terminal

- [ ] `NEXT_REVIEW_PACKET.md` indexes every raw artifact, command, exit code,
      duration, source/test hash, node count, session/model/turn and remaining
      risk without requiring Codex to search logs by guesswork.
- [ ] Every report claim is traceable to a raw file that still exists and has a
      recorded SHA/mtime.
- [ ] Worker and readers are terminal; heartbeat is removed; task ports free;
      database guard unset; HEAD unchanged; no commit/push/merge.
- [ ] Terminal is exactly
      `S10-C6G = SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`.
- [ ] S11/S12/S13 production was not opened.
