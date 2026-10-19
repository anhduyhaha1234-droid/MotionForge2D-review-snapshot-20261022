# T01 dispatch pitfalls — model-alias trap, window-index trap, silent dispatch log, same-turn dispatch

Generalizes MF-DEMO-V3-R2 T00→T01 continuation (2026-09-08, F05 PM decision
`ACCEPT_RISK_BOUNDED / AUTHORIZED_TO_DISPATCH_AFTER_LOCAL_GUARDS`).

## 1. Transposed-token model IDs are NOT aliases

`ocgfree/muse-spark-1.3-contributor-free` vs `ocgfree/muse-spark-contributor-1.3-free`
 differ only by token order — and a `ping` succeeds (pong, exit 0) on BOTH.
Ping-success does NOT establish alias equivalence.

Ground truth is the actual session row plus the launch string, queried read-only:

```sql
SELECT id, model, cwd, ended_at, end_reason, message_count
FROM sessions WHERE id = '<worker-or-manager-id>';
-- PRAGMA query_only=ON, mode=ro. Never write state.db.
```

On mismatch: append a `MODEL_ERRATA.md` that preserves the original registry text
and pins the forward model explicitly. Never rewrite history to claim "same exact
model", never treat it as blocking independently-verified facts (Codex verified
T00 DB forensics despite the label error). Always reconcile the exact model id
before dispatch when a decision/correction flags routing — including against the
user's typed string, which may itself carry the transposition.

## 2. Source-window indices vs clip-local indices

Occurrence window was source frames 450..569 of a 30 s clip; output-local
0/60/119 ↔ source 450/510/569. But `ffmpeg -vf "select='eq(n,0)+eq(n,60)+eq(n,119)'"`
on the clip yields CLIP frames 0/60/119, not window frames — the manager made
exactly this error, then deleted the wrong probes and recorded the correction in
`PM_DECISION_ACK.md` rather than hiding it.

Rule: every frame-extraction command must state which index space `n` lives in;
record the local↔source mapping in evidence; any diagnostic named 0/60/119 must
declare whether it is local or source-absolute. Never label clip-absolute samples
as occurrence fixtures.

## 3. Zero-byte dispatch log ≠ dead worker

`hermes -z "$(cat prompt)" ... >> dispatch.log` can sit at 0 bytes for the entire
run — output is buffered and flushes at exit (final report + `EXIT-*` line).
Both T00 and T01 dispatches showed this shape while workers made real progress.

Verify lane liveness via, in order: evidence-dir mtimes, state.db row
(`message_count` growing, `ended_at` NULL), process liveness. Never kill or
re-dispatch on log silence alone. Prefer a bounded watchdog on the
`REPORT.md` `STATUS:` marker (poll 60 s, cap 90–180 min, notify on exit) over
manual polling loops — it also preserves the shared in-flight budget.

## 4. Authorized guards → dispatch in the SAME turn

When a decision reads `AUTHORIZED_TO_DISPATCH_AFTER_LOCAL_GUARDS`, the turn must
end with a live dispatch (or a concrete guard failure) — never a "prompt is 90%
ready" message. Fixed sequence that worked: local guards
(owner/HEAD/dirty/DB-hash/roots/ports/resources) → errata + ack files →
pre-write manifest + inventory → prompt file → `commands.jsonl` START →
background dispatch → lane-alive check via state.db (not log size) →
registry update → watchdog arm. Log every START/END with exit code; keep
failures in the ledger.
