# C01-R01 coder self-review

Status: `SELF_REVIEW_PASS_PENDING_ROOT_REVIEW`. Exact candidate bytes and receipts are pinned in `CANDIDATE_MANIFEST_R01.json` (SHA256 `261a7d9b20c046c3eee3ede50fac250992a084aec856583c5e0992397e2a6850`).

## Contract and scope

The reproduced defect was a self-consistent but truncated or overlong blend review authorizing an actual three-frame `gate_assemble`. The new check derives frame identity from the current bound manifest's ordered `0001.jpg`-style entries. It requires the review's `expected.frames` and ordered `frames` to match those current entries. `gate_blend_fresh` checks that manifest's frame files and hashes before the review check. Malformed frame entries and non-list frame collections now produce `GateBlock` diagnostics before indexing. The complete dependency-map comparison and existing review schema remain unchanged.

Only `r6_gate.py` and `test_codex_c01_review_binding.py` changed. Candidate01 preimages were copied byte-for-byte before the patch; `r6_assemble.py` and `r6_common.py` hashes remain unchanged. No historical review/media, production render, encoder, model/runtime, PM, or Git operation was performed.

## Evidence and correctness

- Red: the original root blend probe accepted both truncated and overlong reviews (exit 1); new gate tests failed on truncated, overlong, reordered, and malformed current names. A second red test exposed an uncontrolled `TypeError` for numeric manifest `frames`.
- Green: full C01 module `17 tests OK`; original independent review probe `30/30`; independent blend probe accepted full and blocked truncated/overlong; two unchanged historical F02 bodies passed. The read-only schema survey accepted 54 blend and 1013 key record shapes, with three malformed fixture records blocked. All final-hash commands exited 0.
- The real `gate_assemble` tests cover full, truncated, overlong, reordered, boolean-entry, and numeric-collection cases. They use isolated paths and do not invoke the encoder. The existing main-path test still verifies rejection before frame copy or encoder access.

## Limits

This is an engineering review-binding correction. It does not establish semantic media quality or recompute model/source dependency identity; those remain outside C01-R01. Root independent review is required before acceptance or opening C02.
