# S02-T05 Start Prompt

Read TASK and all Required reading before coding. First audit every current
`create_job` call and write a bounded plan mapping closures to reconstructable
durable job types/manifests/registered handlers. If faithful restart-safe
reconstruction requires a scope or product decision not authorized, mark
BLOCKED rather than preserving RAM authority or dual-writing.

Implement explicit app lifecycle wiring, durable submit/poll/cancel compatibility
and recovery acceptance tests. Keep HTTP requests submission-only. Use temp DB/
managed roots in tests and preserve channels.json. Do not add migrations/deps or
break frontend response fields. Run all validation, submit LOG/REPORT, and stop
without commit or roadmap edits.
