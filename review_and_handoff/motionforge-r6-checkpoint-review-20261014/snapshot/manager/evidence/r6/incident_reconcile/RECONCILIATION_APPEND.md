# R6 reconciliation append (append-only; does not rewrite history)

UTC: 2026-10-12T07:50:22Z · Manager 20261012_002032_daa36c

## A. 16 frozen R4 evidence files drifted since R4 review (measured by reviewer probes)

- Files: manager/evidence/r4/R4_HARNESS_TEST_RESULTS.json (report) + 15 receipts in
  manager/evidence/r4/consumer_test_receipts/ (api_error, dupkeys, empty_cont, exit_nonzero,
  future_pass, matrix_mismatch, missing_artifact, ok_continue, ok_submitted, prose_only,
  quoted, truncated, wrong_invocation, wrong_owner, wrong_packet).
- before/after hash pairs: see INCIDENT_A_FROZEN_R4_DRIFT.json (verbatim from
  O/FRESH_PROBES_R5.json). Current bytes preserved under preserved_bytes/ (16 copies).
- Mechanism (consistent with the reviewer's note, motive NOT attributed): the R5-round
  regression re-run of the OLD R4 harness (test_r4_terminal_consumers.py, which hardcodes
  r4 output paths and rewrites the report at line ~351) refreshed exactly these paths.
- R6 policy: no restore, no backdate, no refresh. These 16 paths + R4 tracks/masks join the
  R6 guard as PROTECTED. All R6 test outputs go under manager/evidence/r6/** only
  (isolation proof required before dispatch).

## B. R5_MANIFEST.json nested entry for the R5d terminal record is stale by one revision

- Manifest entry sha 40df34d2… (7081 B) vs current record sha ff93e3c2… (see
  INCIDENT_B_R5D_MANIFEST_STALE.json). Cause: RECORD-LAST (record refresh is the final
  write of the invocation; the manifest predates it). The record itself is the validated
  terminal (PENDING_SAME_OWNER_CONTINUATION). R5_MANIFEST stays frozen; R6 manifest must
  hash AFTER its own final record write.

## Standing policy

- Old evidence/receipts/terminal/packets frozen; generic manager/** grants no overwrite.
- Any missing/shrink/out-of-scope write is an incident: freeze evidence, stop, report.
