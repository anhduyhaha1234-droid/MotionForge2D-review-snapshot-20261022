# C01 self-review — TASK_SUBMITTED, pending independent root review

Candidate: `CANDIDATE_MANIFEST_FINAL.json` (SHA-256
`F6161FFCAE80BD700D84749F635307018A7EB7A475367EFAEFF726CE186A8DEE`).
Source preimages and exact candidate diffs are in `PREIMAGE_MANIFEST.json`,
`DIFF_R6_GATE.patch`, and `DIFF_NEW_TEST_FINAL.patch`.

## Contract and scope pass

- `require_review` now checks nonempty, typed current and recorded dependency
  mappings with identical key sets and canonical JSON values. An omitted
  `deps_sha` or other current key cannot authorize a reviewed artifact.
- The review ID, reviewed artifact path and SHA, expected shot/frame identity,
  reviewer, timestamp, evidence, verdict and reviewed frames are validated.
  Invalid JSON, duplicate fields, non-JSON constants and malformed records
  raise `GateBlock` diagnostics. No boolean-to-string or boolean-to-integer
  equality is used to accept a review.
- Only `R6/scripts/r6_gate.py` and the new
  `R6/tests/test_codex_c01_review_binding.py` changed. Preimaged
  `r6_assemble.py` and `r6_common.py` still match their original SHA-256 hashes.
  Assembly already calls the real `gate_assemble` before frame copying or
  encoding, so no assembler edit was needed.
- No historical review/evidence/media, model, DB, registry, PM file, or
  production render was written. No commit was made.

## Correctness and compatibility pass

- Baseline focused run: 13 tests, 15 assertion failures and 1 uncontrolled
  JSON exception, recorded in `RED_TEST_OUTPUT.txt`. It reproduced omitted
  dependency, wrong same-byte artifact path, wrong review ID, malformed types,
  and assembler fallthrough to the later blend-manifest gate.
- Final isolated focused run: 16 tests, exit 0 (`FINAL_FOCUSED_TEST_OUTPUT.txt`).
  This includes a real `r6_assemble.main()` call against isolated `K` paths,
  the actual `gate_assemble`, a pre-copy assertion and an encoder tripwire.
- Two unchanged F02 function bodies from the historical R6g gate suite pass
  under isolated paths (`EXISTING_GATE_SAFE_OUTPUT.txt`). The full historical
  test module executes probes on import that overwrite/delete R6 artifacts;
  it was not run against protected production data.
- A read-only survey accepted the record shape and artifact hash of all 1013
  nonfixture key reviews and all 54 blend reviews. Three old fixture records
  remained blocked, as detailed in `EXISTING_REVIEW_SCHEMA_SURVEY.json`.
  This survey supplies recorded inputs for shape comparison and does not prove
  that live producer dependencies are fresh.
- The first self-review found numeric `_sha` could raise `TypeError`, and
  expected frame identity was not yet bound. New failing probes reproduced
  both; the final focused run passed after bounded corrections.

C01 checks binding to dependency mappings supplied by the existing consumers.
It does not establish source/model dependency recomputation or semantic media
quality. The git no-index diff emitted a Windows LF/CRLF advisory; the Python
tests and read-only record survey passed on the exact manifest hashes.
