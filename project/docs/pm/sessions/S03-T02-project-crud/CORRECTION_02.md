# S03-T02 - PM correction round 2

Resume this exact S03-T02 session. Do not commit. Preserve `channels.json`
byte-for-byte and keep all legacy `/api/projects` routes and tests untouched.

## Blocking findings

1. Ordinary project PATCH currently accepts `status="archived"` and can also
   move an archived project back to a live status while retaining
   `archived_at`. Make the archive endpoint the only transition into archived,
   and make archived projects immutable until a separately designed restore
   workflow exists. Add API and repository tests for both bypass directions.

2. Channel validation and project INSERT/UPDATE are not atomic. A concurrent
   Channel archive can commit after validation but before the Project write,
   creating a new reference to an archived channel. Implement a transaction or
   conditional-write strategy that proves a newly assigned source/production
   channel is active, in the same workspace, and has the correct role at the
   atomic write boundary. Cover both CREATE-vs-archive and PATCH-vs-archive
   using deterministic interleavings. SQLite behavior must be explicitly
   handled; do not rely on a SELECT read lock that legacy transaction mode does
   not provide.

3. The current two-archive race test does not force both calls to read active
   before either CAS. Add an intentional repository test seam/hook or another
   deterministic mechanism that pauses after the initial state load, then
   orders the competing CAS operations. Avoid timing/sleep-based assertions.

## Required verification

- Focused S03-T02 tests, combined Channel/Project/bootstrap tests, legacy API
  regression suite, Ruff, mypy, and the complete 7/7 quality baseline.
- Re-read final rows with fresh state (or `populate_existing`) in race paths.
- Update TASK/LOG/REPORT with exact evidence and disclose the implementation
  strategy and any limitations.
- Leave the session SUBMITTED for PM review; do not mark APPROVED and do not
  commit.
