# Combined-candidate interactions & expectation-superseded triage (S12-R7 harvest, 2026-09-16)

Context: one wave, two managers, 5 lane commits transported serially onto one integration tip (zero conflicts). Every lane was independently green. The **combined finite gate then caught what no per-lane gate could see** — a cross-lane interaction. This file is the triage playbook; extend, don't re-derive.

## 1. Cross-lane interaction reds (why the combined gate exists)
- Signature: node **green on the owner lane at owner tip**, **RED on the combined tip**, and the failing assertion contradicts a *sibling lane's newly-frozen semantics*. Example: B01's `test_B01_F` asserted `full_apply_executable is True` for a geometry-less fixture; BRIDGE froze "no boxed geometry → typed ineligible" (its F04/B04 mandate) → on the combined tip the assertion fails with the NEW typed reason quoted in the failure (`OCCURRENCE_GEOMETRY_BOX_MISSING …`). **Not a production bug.**
- Diagnose from RAW output before assigning blame: quote the typed reason from the failure line; check which lane owns each side of the interaction; check the delta shows no production file needs a change.
- Reproduction sequence: ff the owner worktree onto the combined tip (pre-verified pure fast-forward), then have the owner re-run the module there.

## 2. Expectation-superseded-by-frozen-contract (distinct class)
Test conditions (all three): assertion pins pre-contract behavior; failure message carries the NEW typed contract reason; owner lane is green at owner tip.
- **IN the owner's write-set** → bounded owner correction in ONE turn: update the fixture so the positive control satisfies the new prerequisites (keep it a *positive* control — add an assertion for the new artifact, e.g. the timeline block), plus ADD a negative node asserting the new typed denial. Then a fresh INT transport round. Verify delta vs parent = exactly the intended paths.
- **OUT of every write-set** → file a finding with the exact minimal proposal (file path, specific asserts, proposed owner, precedent) and request a bounded exception; never edit, never ignore. (R7 examples: `test_s09_t06` 2 points-only asserts + alembic pin → finding + exception proposal; R5 inventory referencing Q02-renamed nodes → finding + manager-granted bounded exception, QA patched names only, provenance asserts byte-intact.)
- Never green this class by loosening/skipping; label it as a class everywhere (matrix, report, packet): "expectation superseded by frozen contract" ≠ "regression".

## 3. Stale guard manifests after transport (false-alarm class)
- Pre-wave guard manifests (captured at the old base) will show `protected_file_changed` "failures" that are actually **other lanes' transported commits**. Proof package: `git diff --name-only <parent>..<tip>` = exactly the expected path list; every changed file's post sha256 **matches the sibling lane's own reported post-patch sha** (hash-attribution).
- Then **re-capture guard manifests at the new tip** (re-baseline) so the next round compares against current state. Keep pre + post + the attribution proof in lane evidence.

## 4. SHA literal typos in prompts/handoffs
- A 41-hex (or otherwise wrong-length) SHA is impossible for the hash function. Resolve against ground truth before merge: `git rev-parse <branch>` tip, parent check (`git log -1 --format=%P`), diffstat match; record BOTH forms in the transport report. (R7: duplicated `c` in RETRY's sha in both the dispatch prompt and the handoff — resolved to branch tip, documented, not a deviation.)

## 5. Env-gated audit tests at broad-gate time
- Some acceptance nodes are env-gated (require audit env vars, e.g. `<PROJ>_R5_CANDIDATE_ROOT` + `_EXPECTED_CANDIDATE_SHA`). A broad gate WITHOUT the env shows a false red on that node — that is the gate command's gap, not a product red.
- Ship BOTH raws: the broad gate (node red, noted as env-gated) AND a dedicated run of the audit module exported with the exact env (root = candidate worktree, SHA = frozen tip). **Refresh the SHA value whenever the tip moves** — the audit asserts it.

## 6. Report discipline for this class set
- Every red ships with: raw failure quote, triage class (interaction bug / superseded expectation / stale baseline / env-gated / real regression), owner, action taken, evidence path.
- Never inflate: a fixed-superseded red is reported as "expected red → owner fix landed" not as "all green".
