# Lane identity + append-only ledger invariants (what "verify against disk truth" means here)

Two verification surfaces that bite managers of long-running worker lanes. Both measured 2026-09-27.

## 1. Which session is the LIVE lane? (identity)

`--resume <parent_id>` **mints a new session id** and stamps the parent's row `end_reason=agent_close`
immediately — before any work happens. Consequences, all observed:

- A monitor/probe keyed on the parent prints e.g. `VIDEO14B: 208msg api=90 end=agent_close age=1326s`
  while the resumed writer is alive and mid-run. Reading `end_reason` as "task finished" is wrong.
- `sessions.message_count` is a **stale snapshot**: one row said 603 while the `messages` table held 1,223
  rows for the same id. Count `messages` rows for progress; use `api_call_count` for budget burn.
- A manager lineage at `api_call_count` ≈ its turn-budget ceiling (measured 451) cannot be resumed to
  operate — record it as evidence-only, note it in the registry, and do NOT create a duplicate manager
  lineage to compensate.

Resolve the live session like this (read-only, `mode=ro`):

```sql
SELECT id, started_at, model, end_reason FROM sessions WHERE started_at > :dispatch_ts ORDER BY started_at;
-- then for each: first user message must equal the head of that lane's packet file
SELECT content FROM messages WHERE session_id=:sid AND role='user' ORDER BY id LIMIT 1;
```

One packet file per lane per round makes that match unique. Materialize rows before inner queries.
Then **re-point every monitor/probe at the new id**; treat tick lines for an already-resumed id as STALE.

## 2. Append-only ledger: the invariant is the PREFIX, not the file

When you append correction events to a frozen history (dispatch ledger, transport ledger, audit log):

- **Never edit or delete an old row.** Corrections are new rows that name the row they supersede
  (`corrects_ledger_line`, `recorded_actual_session_invalid` vs `actual_session`, `grade`, proof string).
- Snapshot the pre-append bytes to the evidence root and record `sha256(first N rows)` where N = the frozen
  row count. Re-assert that prefix digest after EVERY append. A guard that hashes the whole file will
  REFUSE the second append onward (observed: first correction append passed, next five refused until the
  check was scoped to the 36-row prefix). Measured invariant: 6 appends, 36 → 59 rows, prefix
  `e129c5c6…` byte-identical every time.
- Keep N and its digest as constants inside the tooling so a reviewer can re-derive the invariant without
  you. Never "fix" a refusal by widening the check.
- A PENDING dispatch row later reconciled by a follow-up row is legal history — do not rewrite it; do not
  delete it. Percent-style counts (rows before/after, bytes before/after) belong in the evidence file.
- Also correct **format** lies: a session id carrying a status suffix (e.g. `…70b95b-STOPPED`) is an
  annotation, not an id — record the real id and keep the status in its own field.

## 3. Report shape

`manager/ledger_<round>_result.json` with `prefix_sha256_before`, `prefix_sha256_after`,
`prefix_immutable`, `rows_before/after`, `bytes_before/after`, `appended_sha256`, `pre_append_snapshot` —
plus the corrected registry as a NEW file in the new run root (leave the old registry untouched). DB probes
go in the evidence root too (`db_reconcile_<round>.json`), never only in %TEMP%.
