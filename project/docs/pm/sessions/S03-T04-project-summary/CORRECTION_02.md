# S03-T04 - PM correction round 2

Resume the same Hermes MAX lineage. Close exactly these final P1 blockers:

1. The globally activity-ordered Project query still calls `.all()` before
   slicing in Python. Apply SQL `OFFSET offset LIMIT limit+1` after the global
   `last_activity_at DESC, Project.id` ordering so DB rows and memory are truly
   page-bounded. Test with many off-page Projects and assert SQL/page behavior,
   honest `has_more`, and unchanged global ordering.
2. Batched active jobs use one global `LIMIT 10` for the whole page. Return the
   newest at most 10 active jobs **per Project**, deterministically ordered by
   `created_at DESC, Job.id`, while keeping a constant query count. Use a
   window rank partitioned by resolved Project ownership or an equivalent
   batch-safe strategy. Test two Projects where one has more than ten newer
   jobs; the other must still receive its own jobs and correct total count.

Run all three focused summary suites, Ruff, mypy, diff-check, and the combined
durable regression. Preserve `channels.json`; do not commit or run the full
baseline until PM re-review.
