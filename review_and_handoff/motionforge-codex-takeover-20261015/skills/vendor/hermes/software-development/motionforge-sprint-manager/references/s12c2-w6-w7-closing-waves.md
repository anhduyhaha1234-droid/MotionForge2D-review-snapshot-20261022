# S12-C2 closing waves — W6 T06A + W7 T06B (2026-09-09)

Session continuation of the C2 correction sprint after W5's cross-lane addendum
and diverged-base fix. W6/W7 ran the SAME INT01 wave-transport template already
proven W1→W5 (merge verified SHAs → push non-force → ff next branch; see
`s12c2-w1-w4-wave-execution.md`) — 7 consecutive clean transports total, with
the T05 diverged-base case as the only documented exception (`s12c2-w5-diverged-base-merge.md`).

## W6 T06A — verify-only tip + lifecycle safety (F09)

- Worker committed `bb004b7` after ONE implementation turn (staged relocatable
  package: `scripts/s12/s12_t06a_stage.py` NEW, PID+creation+executable+token
  identity, failed-stop evidence, uninstall keeps data). 15 files, all T06A
  allowlist (packaging/scripts/docs/tests). 17 new tests passed.
- Manager verify before merge: `git rev-parse --short HEAD` + porcelain 0 +
  `git show --stat --oneline HEAD` scope check vs allowlist — do NOT re-run the
  full 40s suite for a lane whose fresh-green evidence came off the same commit
  (wrapper already re-verified after docs-only edits). Keep the verify cheap for
  waves that are otherwise clean.

## Regression-count shifts after an addendum merge (T03C 30 → 35)

- Cross-lane addendum (`s12c2-w5-cross-lane-result-endpoint-gap.md`) merged 5
  new backend tests into canonical → every downstream regression claim must use
  the NEW count (T05 finalize reported "T03C regression 35 passed" on base
  `fb59215`, not the old 30). Manager verify that compares against a stale
  pre-addendum count will false-alarm; check `pytest <dir> | tail` output, not
  memory.

## W7 T06B — verifier second round must prove old pinned-fail PASSES

- Base `5e6e0fa` now contains ALL production fixes (T01-C1 provenance closure
  among them). The verifier's C1-era test that documented the pre-fix bug
  (`test_f3` asserting dims-only `native_4k`) MUST pass now — W7 prompt orders
  the verifier to assert the new behavior on canonical instead of re-pinning
  the old expectation (pair with `s12c1-int01-merged-gate-and-route-quota.md`:
  the earlier INT01 merged the test-only fix `97a54b0`; the C2 round re-verifies
  from the product path).
- Close F11 positive acceptance through the NORMAL product flow (API → durable
  worker → published result → result/media endpoints) — the verifier may NOT
  accept an unrelated-ffmpeg-kill + separate-helper-resume split.

## Closing-wave checklist (after W7 passes)

1. INT01 final merge W7 → push → local==remote (ls-remote live, not cached).
2. Manager final gate on frozen canonical: per-dir S12 loop (short basetemp)
   + ruff F + diff-check + alembic sole head + tsc/build + E2E — all S12 tests
   collect together (duplicate-basename rule: per-dir only, or renamed files).
3. Packet: NEXT_REVIEW_PACKET.md + MATRIX 32 rows + FINDINGS_CLOSED F01–F11 /
   R01–R13 + EVIDENCE_INTEGRITY + ledger; state tested HEAD vs docs HEAD.
4. Kill own watch loops, verify zero watchers (`ps` for watch_24/heartbeat).
5. Terminal = `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW`;
   no watcher left, no APPROVED/CLOSED, no S13.