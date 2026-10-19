# S10-C4A — PUBLICATION_CONTENT_HASH_MISMATCH gate regression (verified 2026-08-30)

## The defect

T04C-C3 (strict vertical harness, real e2e output) hit a production gate
regression that made `REVIEW_REQUIRED` **unreachable** on real output, both
pre- and post-correction:

- Gate: `app/api/routes/s10_full_apply.py:1038-1046` (structural_compare_gate)
  ```python
  if str(pub.content_hash) != str(art.sha256):
      return _blocked("PUBLICATION_CONTENT_HASH_MISMATCH", ...)
  ```
- `content_hash` in this domain is a **LINEAGE KEY**, not the raw file digest:
  - Full-apply producer: `app/workflow/s10_full_apply_jobs.py:903`
    `content_hash = sha256(f"pub:{run_id}:{stitch_sha}")`
  - Recompute producer: `app/services/s10_recompute.py:1245`
    `pub_hash = sha256(f"pub-recompute:{run_id}:{correction_id}:{sha}")`
  - Data model `app/persistence/models.py:2920`:
    `UniqueConstraint("run_id", "content_hash", name="uq_s10_pub_run_content_hash")`
    plus lineage dedupe in `s10_full_apply.py:736-744` — lineage key.

So the gate compared a lineage hash against a raw sha256 → NEVER equal on
real runs → `BLOCKED` before any measurement.

## Why synthetic tests missed it

T04A-C4's own `probe_direct.py` exercised the compare **SERVICE** with
synthetic inputs where `content_hash == sha` by construction — the route's
publication-binding check was never covered by T04A-C4's gate. The unit suite
(`test_s10_structural_compare.py` 54 tests) passed for the same reason.

## Manager verification before routing (do NOT trust the worker claim alone)

1. Read the producer contract lines (jobs:903, recompute:1245) + model
   UNIQUE constraint + lineage dedupe — confirmed content_hash is a formula.
2. Live DB probe on the real run (pristine state, t04c-c3 run1-c4a-green):
   - run `e8f109f5-...` status=completed, frame_count=100
   - pub content_hash=`4c573203...`, artifact sha256=`50812898...`
     (file SHA/size matched — NOT tampered)
   - derived `sha256("pub:e8f109f5...:50812898...")` == `4c573203...` == DB
     → producer contract holds 100%; the GATE is the bug, not the producer.
3. Only then route to the owner (structural measurement = T04A
   `20260828_014304_25d94a`, in-scope since the gate hunk was T04A-C4's).

## Fix (T04A-C4-R2, deployed)

- Service helper computes expected lineage hash from `natural_key`
  provenance (full-apply vs recompute formula).
- Gate uses it:
  ```python
  expected_pub_hash = expected_publication_lineage_hash(
      str(rec.id), str(art.sha256), getattr(pub, "natural_key", None))
  if expected_pub_hash is None or str(pub.content_hash) != expected_pub_hash:
      return _blocked("PUBLICATION_CONTENT_HASH_MISMATCH", ...)
  ```
- Raw-sha synthetic / tampered / foreign-provenance publications still BLOCK.
- Regression tests added: 6 R2 tests; one goes through the real producer
  path (create publication via repository with the lineage formula → GREEN).
- After fix: T04A 60×2 fresh roots, retained 117 passed, ruff 17-file zero,
  mypy 9-file literal `Success: no issues found in 9 source files` = J4'
  MANAGER_VERIFIED; T04C-C3 rerun resumed on the fixed tree.

## Class rule

Whenever a validator compares two hash fields, resolve WHAT each side
hashes. If any field is a lineage/formula key (name contains `content_hash`,
`lineage`, `natural_key`-derived, `pub:*` prefix) rather than a raw digest,
assert the **formula relationship**, not plain equality. And a probe that
seeds both sides equal-by-construction (synthetic `content_hash == sha`) is
blind to binding defects — the regression test must traverse the real
producer path.

## Related lesson

The worker (T04C) correctly did NOT patch production (`app/**` forbidden):
reported `BLOCKED_WITH_FINDINGS` with file:line + live repro + expected fix
direction, then Manager verified and routed to the exact owner. This is the
Acceptance-lane → owner-routing loop working as designed; the extra value
this round is the *lineage-hash semantic check* on both sides of a "hash
binding" assertion.