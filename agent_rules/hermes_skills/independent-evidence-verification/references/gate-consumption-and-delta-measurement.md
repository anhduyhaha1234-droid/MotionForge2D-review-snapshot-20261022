# Gate consumption: refuse only on an EXPLICIT verdict

Measured 2026-09-28 (MF-END-26, MF2D delivery): wiring a new export gate
(`mf-end-23/export-gate@1`) into the S12 export legs (submit/retry/publish)
with a FAIL-CLOSED rule ("if the gate cannot be resolved, refuse") broke 5
protected legacy rows: `compute_export_gate` raised `UnsafeRuntimeRootError`
because the test harness monkeypatches the ROUTE's managed root but not
`app.api.deps.get_managed_root`, so the gate's runtime-root guard fired.

Rule that survived review:
- refuse ONLY on an explicit `blocked` verdict;
- `not_run` belongs to the standing authority that every leg already consumes
  (readiness) — do not duplicate it;
- an unresolvable gate stays visible as a FAILING CHECK on the display path
  (preflight authority check → ineligible), but must NOT be turned into a
  fabricated refusal on the mutate path (submit/publish).

## Ruff delta measurement pitfalls (same round)

`ruff check --output-format=concise` echoes the path AS GIVEN:
- linting a temp copy prints the temp path → normalize it back;
- on Windows the worktree path renders with BACKSLASHES while the logical
  filename uses forward slashes → normalize `\` → `/` before comparing;
- line numbers SHIFT when you insert code, so comparing raw lines reports
  pre-existing findings as "NEW". Normalize each finding to
  `<file>: <CODE> <message>` (drop line/col) before diffing base vs work.

## Identity-key conflation in the S12 validator (defect class)

`_expectation_for` reads `manifest["expected_sha256"] or ["authority_sha256"]`
as the OUTPUT identity, and `_build_source_reference` reads the SAME chain for
the approved-artifact identity. A submit path that writes the SOURCE sha into
that key makes every re-encoded export fail the source-locked `provenance`
probe (typed FAIL). For re-encode paths the manifest must leave the identity
keys empty so psnr mode uses the server-MEASURED candidate sha; keep the
approved sha under a distinct audit key.
