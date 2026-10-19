# SQLite fixed-bind-parameter scalability — json_each() idiom (S08-A02-C5→C6)

Reprod and the two-stage fix for historical queries that must scale to thousands
of videos without unbounded SQL (SQLite `999 max parameters` / `500-term
compound SELECT` limits).

## Failure modes seen

1. Per-stale-video `UNION ALL` built with `literal_column(f"'{v}'")` →
   `OperationalError: too many terms in compound SELECT` at 501 videos.
2. Chunked `IN(...)` per 900 (`or_(IN(c1), IN(c2), ... IN(cN))`) → the final
   COUNT/page SELECT carries a total bind count = the whole stale set. Still
   NOT bounded. (Chunking bounded *per statement*, the or_() chain did not.)

## Final idiom (C6)

```python
# bind the WHOLE id-set as ONE JSON text param
stale_json = json.dumps(stale_vids)
hist_filters = list(base_filters) + [
    or_(
        OccurrenceSegment.superseded_by_id.is_not(None),
        text(
            "occurrence_segment.video_item_id IN "
            "(SELECT value FROM json_each(:stale_json))"
        ).bindparams(bindparam("stale_json", value=stale_json, type_=String)),
    ),
]
total = session.scalar(select(func.count(...)).where(*hist_filters))
rows  = session.scalars(select(...).where(*hist_filters).order_by(...).offset(o).limit(l)).all()
```
Bind budget becomes FIXED regardless of set size: base predicates + 1 `:stale_json`
+ LIMIT/OFFSET. `json_each` is built into SQLite JSON1 (present by default).

## Capability probe (fail clear, never raw interpolation)

```python
try:
    session.execute(text("SELECT value FROM json_each(:_probe)"), {"_probe": '["__probe__"]'}).fetchall()
except Exception as exc:
    raise RuntimeError("SQLite JSON1 unavailable — cannot use json_each(); no raw interpolation fallback") from exc
```

## Verification harness (manager-owned, real SQL execution — not source grep)

Attach a `before_cursor_execute` event listener that captures `statement` +
`parameters` for EVERY statement, filter keeping those on the target table, and
assert:
- per-statement param count ≤ declared budget
- at 1001 AND 5001 stale videos, the final COUNT + page SELECT remain bounded
- no `UNION`, no OR-chain growth, no UUID string literally interpolated.

Key implementation details:
- `event.listen(engine, "before_cursor_execute", fn)` from SQLAlchemy; keep a
  counter dict; remove listener after the call.
- Count ONLY `SELECT` statements (`stmt.lstrip().upper().startswith("SELECT")`)
  for the no-N+1 check — never count BEGIN/ROLLBACK (SQLAlchemy's autobegin
  emits them and breaks `<= N` assertions under flaky state).
- `--count=N` requires pytest-repeat (often absent); use a shell loop:
  `for i in $(seq 1 30); do pytest test::x -q ...; done` and tally.

## Pitfall this ran into

Flaky counter test: setup helper wrapped in `contextlib.suppress(Exception)`,
silently failed, left session pending-rollback, and the next query emitted
extra ROLLBACK/BEGIN statements that inflated the counter on a *correct* batch
query. Fix: remove the suppress (setup error must fail the test), deterministic
setup, count SELECTs only.
