# Red gates from sibling lanes, and proving you did NOT push

Two verification situations from 2026-09-29 (MF2D CMC correction, 3 concurrent lanes)
where the honest answer is "this is real but it is not this lane's defect".

## 1. A lane's broad gate goes red because a SIBLING lane changed a hash input

Measured: a writer resuming on the integration baseline changed one file under `app/`.
Its broad gate returned `891 passed / 1 failed`:

```
tests/product_delivery/test_mf_end_28.py::test_28_2_builder_is_deterministic
  committed inventory.json is stale vs a fresh build
  app_tree_sha256 26ef7c09... (committed) != 1f7999ec... (fresh)
```

`packaging/demo/inventory.json` records `backend.app_tree_sha256` — a digest of the
**whole `app/` tree**. Any lane that edits anything under `app/` invalidates it, so the
red test has **nothing to do with the lane that observed it**.

**Triage, in order:**
1. Read the test to find the input it hashes (`grep -n inventory <test>`), then confirm
   the field is a tree-wide digest, not a per-file one.
2. Check the failing file against the **current lane's allowlist**. If it is outside →
   not this lane's defect. Do not widen the allowlist to silence it.
3. Route it to the owner whose allowlist *does* contain that path, and record the
   intended **order of operations** (see below).
4. Never waive the test and never let the lane regen it "to go green" — that is a
   cross-allowlist write.

Symptom to recognise: **the lane's own focused suite is fully green** and the only red
is a determinism/staleness test belonging to another task.

**Ordering matters.** If the correct owner is gated behind "only after a real product
result exists", the right sequence is: close the product blockers → freeze the
integration → let the owner regen the artifact → *then* run the single final broad gate.
Regenerating early just goes stale again on the next sibling commit.

**Disclose recurrence.** This was the 4th occurrence of the same seam. When you have
seen a seam before, say so and keep the same handling — the value of the record is that
the reviewer can see it is a known process seam, not a fresh product defect.

## 2. A commit that is on the remote without the lane pushing it

A worker reported — correctly, with numbers — that its commit sat on
`origin/review/<date>-<task>` while its own command ledger contained **zero push
commands** and its branch had no upstream. That is exactly the shape of an
**external actor**, and you must establish it with commands, not with trust:

```bash
git reflog show origin/review/<name>        # -> "...@{0}: update by push"
git ls-remote origin 'refs/heads/review/*'  # is the SHA really on the server?
git rev-parse --abbrev-ref @{u}             # -> fatal: no upstream configured
# plus: count push argv across the lane's own ledger rows
```

Then classify honestly:

- **In-scope content, out-of-scope authority.** The pushed range was entirely inside
  the lane's allowlist, so no product bytes are dirty — but the Git boundary granted to
  the round was crossed. Report it as a **process violation (P1-process)**, not as
  product contamination, and not as a lane defect.
- **Do not clean up.** No deleting the ref, no force-push, no touching remote state you
  do not own. Escalate to the user/reviewer with the evidence and let them identify the
  actor and set the ref policy.
- **Grade the worker fairly.** A lane that *reports* an anomaly it did not cause, with
  the reflog and the zero-push count, is behaving well. Mark the check
  **informational / non-blocking** in the final gate rather than painting it red against
  the worker — but do not paint it green either.

## 3. Why the two belong together

Both are the same discipline: when a gate goes red or a boundary is crossed, the
question is **"whose write caused this?"** — answered from allowlists and reflogs, never
from who happened to be running. A lane is responsible for its allowlist; everything
else is a routed finding plus a disclosure.

## 4. Establish WHICH SIDE is wrong before honouring the fix direction

A finding names a symptom, not the guilty file. Measured this round: a finding said a
source time map was wrong (boundaries stored as 120/240). The product's own detector,
called directly by the Manager, returned the real boundaries **121/241/343** — so the
**product was already correct** and the caller's hardcoded demo manifest was the wrong
side. Applying the fix to the product would have encoded the bug permanently.

Procedure:
1. Call the product's own producer/detector directly and **print what it returns** — do
   not reason about it from the finding text.
2. Compare that output with the caller's expectation; decide which the evidence supports.
3. If the **caller/fixture/harness** is the wrong side, direct the correction there and
   require the product bytes to stay untouched. Expect the owner to declare
   `no_change` for product files with a stated reason — that is a correct outcome, not an
   incomplete one; verify the files really are byte-unchanged.
4. Never "fix" the product to agree with a wrong expectation, and never rewrite the
   expected values to agree with a wrong product.

Cheapest available guard against a correction round that makes the product worse while
every test goes green.

## 5. A red test can be wrong about the app, not about the code

Corollary of §4, one level down. Measured: a lane's NEW tests were genuinely red
(`3 failed, 40 passed`; all 40 pre-existing tests green), and the failure looked like the
feature was missing:

```
assert missing == []        # missing = all 7 anchor route paths
E  AssertionError: assert ['/api/v2/pro.../reject', ...] == []
```

The routes **existed**. The test introspected them with the wrong API:

```python
paths = {getattr(route, "path", None) for route in api_app.routes}   # -> 0 hits
len(api_app.routes) == 37
```

`app.routes` did **not** flatten the included sub-router; the route objects simply are not
in that list. The product's own schema view proved the routes were registered:

```python
set(api_app.openapi()["paths"])   # -> exactly the 7 expected anchor paths
```

**Rule:** when a "missing feature" assertion fails, prove the feature's presence through a
second, independent view of the app before accepting the failure. `openapi()["paths"]`
(and a real request) are independent of `app.routes`; if the two disagree, the *test's
introspection method* is the defect. Fix the assertion, never the registration — and never
delete/re-add a router to satisfy a bad check. Two of the three failures in that lane had
unrelated causes (an input-validation layer firing before the readiness layer the test
expected, so the typed code was a different one), so triage each red test on its own;
assuming one shared cause misdirects the fix.
