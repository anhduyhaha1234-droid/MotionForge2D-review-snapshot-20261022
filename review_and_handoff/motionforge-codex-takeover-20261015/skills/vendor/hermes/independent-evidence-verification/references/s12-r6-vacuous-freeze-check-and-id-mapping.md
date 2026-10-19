# S12-R6: vacuous freeze-consistency check + frozen-ID mapping divergence (2026-09-15)

Worked example for SKILL.md §10. Context: Hermes Manager ran the finite acceptance
(M01–M19 + V01–V15 + B01 + QA inventory, ~102 tests) directly on the FROZEN integrated
candidate `0c18d2d` (after a 4-lane transport of verified lane commits).

## The failure (fires only post-merge)

    pytest tests/s12/s12-lc3-retry/test_r6_identity_resolution.py \
           tests/s12/s12-lc3-val/test_r6_publication_ownership.py \
           tests/test_s09_structural_lock_producer.py \
           tests/s12/s12-lc3-qa-r6/  →  1 failed, 101 passed (158.6s)

    tests/s12/s12-lc3-qa-r6/test_r6_finite_inventory.py::test_r6_owner_modules_are_frozen_waiting_or_present
    AssertionError: ('M01', 'tests/s12/s12-lc3-retry/test_r6_identity_resolution.py',
                     'test_r6_m01_unchanged_initial_replay')

Check body:

    target = REPO_ROOT / module
    if target.is_file():
        assert node in _module_nodes(target)

Pre-merge, the owner modules did not exist on the QA worktree → the branch was skipped →
the harness reported 11/11 "passed" (vacuous). On the merged candidate the modules exist
under OWNER names → assertion fires. Same test, same code: only the integration state
changed its meaning.

## Root cause: two parallel pre-review freezes

- QA inventory (commit `69a1280`, 21:33Z) froze PRE-DRAFTED node IDs:
  `test_r6_m01_unchanged_initial_replay`, `test_r6_v01_...`, `test_b01_a_...`.
- Owners froze their own IDs inside their commits:
  - RETRY `1d9ed94`: `test_m01_initial_replay_unchanged_no_duplicate` (no `r6_` infix,
    different clause order)
  - VAL `535d7c1`: `test_v01_owned_publication_and_completed_replay` (no `r6_` infix)
  - B01 `9caa223`: `test_B01_A_success_current_source_evidence_graph` (capital `B01_A`),
    and some cases map 1→2 nodes (V14 supported + unsupported; B01-H transaction + read).

## Quantification (42 cases: M01–M19, V01–V15, B01-A–H)

- 0 exact / 25 fuzzy-equivalent / 17 manual-mapping.
- Every one of the 17 "unmapped" cases WAS present under an owner name — spot-checked
  each (M03, M06, M14, M15, M17, M18; V04–V06, V10–V12, V14; B01-D/F/G/H before
  concluding "naming-only, no missing tests".
- Tool pattern: parse the freeze doc rows + `ast.parse` the modules for `test_*`
  functions, normalize (`test_` prefix, `r6_` infix, case-folding) and score token
  overlap; emit a JSON mapping table for the packet.

## Resolution (routing decision)

- Authority wording (all-62 matrix): "test IDs must be frozen **by owners** before
  implementation" → owner-frozen executable IDs are canonical.
- REJECTED: renaming 91 verified test functions across 3 Manager-VERIFIED commits
  (would force 3 owner re-verifications + re-transport for zero functional gain, on
  bytes that already pass).
- CHOSEN: bounded correction to QA (owner of the inventory + harness): update the node
  mapping column to owner-frozen IDs with a provenance note, update harness
  expectations, re-run micro, commit. The check keeps its strength — "module present ⇒
  mapped node must exist" — it just stops being vacuous.
- The correction was QUEUED until QA's in-flight B01-I turn exited (no mid-turn
  interrupt, no second writer on a worktree), then resumed on the SAME session.
- Finding md + machine-readable mapping table were shipped in the review packet so the
  reviewer can re-route to owner renames if they disagree with the resolution.

## Reusable bullets

1. Re-run freeze/mapping/consistency checks on the MERGED candidate — that is where
   vacuous checks fire.
2. Grep test suites for `if <artifact>.is_file():` guards; they convert real checks into
   no-ops pre-integration.
3. Parallel freezes diverging → fix the mapping doc/harness, keep verified bytes;
   quantify + prove no case lost its executing test.
4. Route corrections to owners AFTER their current turn; record the finding with both
   mappings in the packet (transparency over tidy-looking green).
