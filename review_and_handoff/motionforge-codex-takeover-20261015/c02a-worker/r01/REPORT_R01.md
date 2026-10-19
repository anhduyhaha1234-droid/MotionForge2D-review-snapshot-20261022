# CODEX-C02A-DEPENDENCY-VERIFICATION — C02A-R01

Status: TASK_SUBMITTED_PENDING_ROOT_REVIEW. Owner: /root/motionforge_c02a_coder; gpt-6-sol / max; fallback disabled. CPU-only, same task and owner. Root alone may approve candidate-02.

Candidate-01 remains frozen. Candidate-02 changes only `r6_cache.py` and the new C02A test module. The cache validator now walks JSON values iteratively with a depth-256 bound; nested records accepted by the parser but beyond that bound return `(False, reason)`. Digest encoding errors also return a controlled failure. `r6_gate.py` and the 17-test C01 module are byte-identical to candidate-01. No producer, common, assembler, settings policy, or C02B code changed.

| Location | Depth | Loader | Verify | Real key gate | Skip |
| --- | ---: | --- | --- | --- | --- |
| settings | 10, 200 | parsed | valid | PASS | denied by existing current-settings comparison |
| settings | 400, 800 | parsed | controlled false | KEY_DEPS_INVALID | denied as changed dependency |
| settings | 1200 | controlled parser failure | controlled false | KEY_DEPS_MALFORMED | denied as malformed |
| extra top-level | 10, 200 | parsed | valid | PASS | denied by existing current-settings comparison |
| extra top-level | 400, 800 | parsed | controlled false | KEY_DEPS_INVALID | denied as changed dependency |
| extra top-level | 1200 | controlled parser failure | controlled false | KEY_DEPS_MALFORMED | denied as malformed |

The parsed depth-400 extra-field case also blocks `gate_assemble` and the real assembler entry before copy or encoder. Existing tests retain ordinary key/assembly and no-visible-actor source-passthrough positives. The R01 two-test focused run passed; the root nesting probe passed 8/8; the original dependency probe passed 55/55; full affected C01+C02A modules passed 30/30. Raw receipts and commands are in this correction directory.

Self-review compared exact candidate-01 bytes and diffs, found no duplicate definitions, and matched all 24 protected file hashes to preflight. C01 assertions remain intact because that complete test file is byte-identical to candidate-01. The original C02A A1–A6 controls remain green. Recorded-dependency validation is the only acceptance claim here; producer completeness, effective settings equality, staged-source freshness, asset reuse, and media quality remain outside C02A.

Candidate: `../candidate-02/MANIFEST.json`. Source/test writes stopped after candidate freeze. No live jobs.
