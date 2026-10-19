# S12-R6 final gates: baseline proof + frozen-copy probe re-runs (2026-09-15/16)

Worked example for SKILL.md §11–§12. Context: frozen candidate `35f6cb2` (28-path
transport of 4 Manager-verified lane commits + INT docs). Manager ran the final gates
on it AFTER finite acceptance and a broad gate.

## 1) Finite acceptance v2 — all green after the mapping fix

    pytest tests/s12/s12-lc3-retry/test_r6_identity_resolution.py \
           tests/s12/s12-lc3-val/test_r6_publication_ownership.py \
           tests/test_s09_structural_lock_producer.py \
           tests/s12/s12-lc3-qa-r6/test_r6_finite_inventory.py \
           tests/s12/s12-lc3-qa-r6/test_r6_b01i_prep.py -q
    → 102 passed (181.99s) EXIT=0     # was 101 passed / 1 failed before the QA correction

## 2) Broad gate — 5 failures, ALL pre-existing (baseline-proven)

    pytest tests/s12/ tests/test_s09_structural_lock_producer.py \
           tests/test_s09_reskin_config_api.py tests/test_s10_full_apply_api.py -q \
           --ignore=tests/s12/s12-lc3-qa-r6/test_r6_b01i_public_chain.py
    → 574 passed / 5 failed / 1 skipped (779.03s)

Failure classification:
- `s12-lc3-qa-r5/test_r5_matrix_packet.py::test_r5_probe_inventory_is_static_and_exactly_mapped`
  — ENV-gated: `S12_R5_CANDIDATE_ROOT` + `S12_R5_EXPECTED_CANDIDATE_SHA` required (set only
  inside the R5 audit context); without them the assertion fails by design.
- `s12-t03a/test_s12_export_migration.py` ×4 — test hard-codes `NEW_REV="c3d4e5f6a7b8"`;
  repo sole head is `d4e5f6a7b8c9` (`d4e5f6a7b8c9_s12_retry_lineage.py`, added in an earlier
  round). Historical staleness already recorded in the carried-forward matrix
  ("Four historical T03A failures retained").

Baseline proof:

    git archive 83af5167e9dddc931bc8590f547684c0c811784b | tar -x -C <runtime>/frozen-base
    cd <runtime>/frozen-base
    pytest tests/s12/s12-lc3-qa-r5/test_r5_matrix_packet.py::test_r5_probe_inventory_is_static_and_exactly_mapped \
           tests/s12/s12-t03a/test_s12_export_migration.py -q
    → 5 failed, 2 passed (7.17s)      # IDENTICAL failures on the pre-candidate base

Corroboration checked first: `git diff --name-only 83af5167 <tip>` contained no
`migrations/**`, no `tests/s12/s12-t03a/**`, no `tests/s12/s12-lc3-qa-r5/**` → failing
surfaces untouched by the candidate delta.

## 3) Frozen-copy re-run of the R5 reviewer's adversarial probes

    git archive <tip-sha> | tar -x -C <runtime>/frozen-src
    cp <review-dir>/test_review_r5_identity.py    <frozen-src>/tests/s12/s12-lc3-retry/
    cp <review-dir>/test_review_r5_publication.py <frozen-src>/tests/s12/s12-t03c/
    cd <frozen-src> && S12_REVIEW_OUT=<fresh-dir> PYTHONPATH=<frozen-src> \
      python -B -m pytest tests/s12/s12-lc3-retry/test_review_r5_identity.py \
                        tests/s12/s12-t03c/test_review_r5_publication.py -q
    → 7 passed / 0 failed (12.97s) EXIT=0

Placement rule: probes import their base modules (`import test_r4_retry_execution as base`,
`import test_publication as base`) → each probe must sit in the test dir of its base module.
Exclusive creation: probe writers use `open(name, 'x')` → `S12_REVIEW_OUT` must be a FRESH
dir per run (7 JSONs land there: identity-*.json, publication-*.json).

Old vs new deltas that prove the flip (quote in packet):
- `identity-retry-hidden`: OLD outcome = successor created, Jobs 2→3 (duplicate);
  NEW = typed `HTTP 409 S12_EXPORT_JOB_IDENTITY_CONTRADICTION`, counts 2/2→2/2 (zero mutation).
- `publication-foreign-False/True`: OLD retry adopted the foreign inode + receipt + completed;
  NEW = "completed output exists — refusing overwrite" (typed denial both variants).
- `publication-handoff-A` (the previously failing schedule): OLD stale A created the final;
  NEW A = "publication fence lost before rename" (no public mutation), current B completes
  with own bytes, recovery `reused=true`. B-first schedule still green.

## 4) By-design failing node handling

`test_r6_b01i_public_chain.py::test_b01i_public_product_chain_submit_worker_publisher_result_media_ui`
deliberately re-raises a recorded BLOCKED product state (real blocker: S10 422
`shots overlap or non-monotonic`, segment-vs-shot contract collision) instead of going green.
Handling: excluded from the broad gate via `--ignore` for that ONE file (exclusion visible in
the gate command raw); its state reported through the blocker finding + its own evidence dir
(`QA/B01-I/<run-id>/` with stages jsonl + summary + counts-at-failure proving zero mutation).
Never tune the harness green; "no false green" is the design.
