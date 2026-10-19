# S03-T04 - PM correction round 1

Resume the same Hermes MAX lineage. Do not commit or run the full baseline
until all findings below are closed.

## P1 blockers

1. Collection is N+1: it calls `_summarize` with many SELECTs per Project and
   the current test permits query count proportional to page size. Refactor to
   select a page and batch-load/aggregate its Projects with a constant number
   of queries independent of page size. Item and collection must share the
   same batch composition algorithm. Add a test comparing query counts for
   page size 1 versus many and require the same bounded count.
2. Global order/pagination is wrong: page selection uses Project.updated_at
   before deriving activity. Compute authoritative `last_activity_at` from
   Project, Video, and all Job activity before `ORDER BY ... LIMIT/OFFSET`, then
   order globally by activity DESC and Project ID. Test an old Project with a
   newer Video/terminal Job outranks a recently updated Project across page
   boundaries.
3. Required `completion_percent = completed / active * 100` (zero for no
   active videos) is missing. Add it to record/DTO/docs and replace the test
   that incorrectly asserts absence.
4. One SQLAlchemy Session does not prove one SQLite snapshot for many SELECTs.
   Begin an explicit read transaction at the request dependency boundary and
   close it with rollback; add a deterministic concurrent-write interleaving
   test proving the summary is not mixed-time.
5. `last_activity_at` ignores Job updates and terminal Jobs. Include all
   Project- and real-Video-owned Job activity, using authoritative Job
   `updated_at` (and timestamps as needed), not only active-job creation.

## P2 findings

6. Count every deduplicated artifact with NULL `size_bytes` as unknown,
   regardless of state, matching the API document.
7. Fix `has_more` for an exactly-full final page using `limit + 1` or an exact
   filtered total; return honest collection `total` semantics and test both.
8. Channel display lookup must include the expected workspace predicate so a
   malformed/imported cross-workspace reference cannot disclose metadata.
9. Active jobs require deterministic `created_at DESC, id ASC` ordering,
   including stable membership at the 10-row boundary.

Run focused summary tests, combined durable regressions, Ruff, mypy and
diff-check. Update LOG/REPORT to `SUBMITTED`; preserve `channels.json` exactly.
