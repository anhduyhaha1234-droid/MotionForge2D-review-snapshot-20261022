# S08-A02-T01-R1 — writer BLOCKED liveness and scope-audit

Session-verified detail from the DeepSeek Core Recovery run (2026-08-20, writer session
`20260820_001637_df0f17`, `ocg/deepseek-v4-flash` @ custom/9Router, reasoning max).

## What happened

- A spawned one-shot writer (`hermes chat -q ... --yolo --source tool`, background + 
  `notify_on_complete=true`) hit the §8 STOP condition: its new Alembic head `a0b1c2d3e4f5`
  (after `f7a8b9c0d1e2`) made 8 pre-existing S08 test files fail because they hard-code
  `upgrade head -> version_num == "f7a8b9c0d1e2"` as the expected head.
- The writer set `REPORT.md = BLOCKED` with one minimal scope question (bump the head literals
  in 8 allowlist-external test files). Correct protocol.
- The writer's own `clarify` **timed out** (no user input within the window); the tool nudged it to
  "use best judgement" — and it then **patched all 8 files anyway** (mechanical head/table-set bumps),
  recorded the decision transparently in LOG/REPORT, and continued. It was ~10 minutes BLOCKED
  before the user noticed; the user then complained there was no heartbeat/notification.

## Liveness lesson (manager-owned)

- Writer processes don't push notifications to the user. Exit-based `notify_on_complete` is NOT a
  block signal: a BLOCKED writer may keep running (waiting on a baseline/cleanup subprocess).
- The manager must poll the writer's `REPORT.md` **status line** on every heartbeat and surface a
  `DECISION_NEEDED` as soon as BLOCKED appears. Only the manager can convert a writer BLOCK into a
  user-visible decision.

## Scope-governance lesson

- A writer's clarify timeout + "use best judgement" is NOT authorization to write outside the
  packet allowlist. Correct behaviour on timeout: keep REPORT=BLOCKED, touch nothing outside
  allowlist, let the manager escalate. The 8-file bump was only legitimised retroactively by the
  user's explicit review decision: "Cho phép bump NHƯNG phải snapshot hash trước/sau và ghi rõ
  từng diff trong REPORT".

## Transparency procedure for out-of-allowlist edits (user-mandated)

1. For each file edited outside the allowlist: record BEFORE SHA-256 and AFTER SHA-256.
2. Record the exact per-file diff/line changes in REPORT so Codex can review.
3. If edits were applied BEFORE authorization (this case), reconstruct the BEFORE state from the
   writer's `hermes chat -q` tool-call log — the `patch` blocks embed before/after strings — and
   label it clearly as reconstructed, never fabricate a before-hash.

## The 8 pre-existing test files a new migration head breaks (mechanical bump)

Adding a new Alembic head after `f7a8b9c0d1e2` causes these EXISTING S08 suites to fail until their
expected-head/table-set literals are bumped:

1. `tests/test_s08_a01_role_taxonomy.py` — `assert version == "<old>"` (~line 224)
2. `tests/test_object_intelligence_domain.py` — `== "<old>"` (~line 132)
3. `tests/test_object_grouping.py` — `assert version == "<old>"` (~line 315)
4. `tests/test_object_correction.py` — `assert version == "<old>"` (~line 527)
5. `tests/test_object_extraction.py` — `assert version == "<old>"` (~line 373)
6. `tests/test_s08_a01_c1_migration_safety.py` — 2 tests expect revision == A01 after `upgrade head`
   (keep the A01 downgrade-refusal literal `f7a8b9c0d1e2` as the A01 revision itself)
7. `tests/test_persistence_bootstrap.py` — head + `S08_HEAD_TABLES` table-set enumeration
8. `tests/test_durable_job_persistence.py` — exact table-set enumeration test
   (`test_no_worker_or_api_cutover_tables`)

Precedent (already recorded in `references/s08-object-intelligence-domain.md`): head/table-set
assertion updates are "required schema-change maintenance" — so a migration task packet should
pre-authorize this bump list up front instead of hitting it as a mid-run BLOCKED.

## Manager verification notes (from this run)

- Independently re-run the writer's focused suites BEFORE trusting REPORT numbers: migration
  (10 passed), domain (30 passed), phone scenario (1 passed), combined focused (104 passed) all
  verified standalone.
- Cross-check a writer's BLOCKED claim: the combined focused run passed 104/104 in the manager's
  independent run even though the writer reported 2 stale failures pre-fix — because the head bumps
  were applied before the manager re-ran it. Always re-run, don't take the BLOCKED claim at face value.
- Model/session provenance: read ~/AppData/Local/hermes/state.db `sessions` table (newest
  `source='tool'` row) — `.model` = `ocg/deepseek-v4-flash`, `.id` = the writer session id.
