# S12-R7 final gates + probe re-run v2 (2026-09-16, Manager B)

Frozen tip `8a9d79365866f0e12d77d21b0d64845d07c9edf0` (integration = r1 `c3cf095` + CR2 merge `a30f71b` + docs r2).
Wave-base `35f6cb2`. Evidence root `outputs/s12-r7-two-managers/20260916T0351Z/B/`.

## 1. Finite v2 (lane suites, exact command)

```
pytest tests/s12/s12-lc3-retry/test_r6_identity_resolution.py \
       tests/s12/s12-lc3-retry/test_r7_identity_union_semantics.py \
       tests/s12/s12-lc3-val/test_r6_publication_ownership.py \
       tests/s12/s12-lc3-val/test_r7_lease_serialization.py \
       tests/s12/s12-t03c/test_publication.py \
       tests/test_s09_structural_lock_producer.py \
       tests/s12/s12-public-authority-bridge/ \
       tests/s12/s12-lc3-qa-r6/test_r6_finite_inventory.py \
       tests/s12/s12-lc3-qa-r6/test_r6_b01i_prep.py \
       tests/s12/s12-lc3-qa-r6/test_r7_prep_inventory.py \
  -q -p no:cacheprovider --basetemp <short temp>
```
Result: **197 passed / 0 failed** (342s) — `manager/final-finite-r7-v2.txt`.
Finite v1 (pre-CR2) was 195 passed / 1 failed → the red was `test_B01_F` (cross-lane supersession, fixed by CR2 27→28 nodes).

## 2. Broad gate (R6-comparable scope) + the env-test red

Chained in ONE bg command so broad never runs on a red finite:
`finite; if [ $? -eq 0 ]; then broad; fi` (else append `FINITE_RED_SKIP_BROAD`).

```
pytest tests/s12/ tests/test_s09_structural_lock_producer.py \
       tests/test_s09_reskin_config_api.py tests/test_s10_full_apply_api.py \
  -q -p no:cacheprovider --ignore=tests/s12/s12-lc3-qa-r6/test_r6_b01i_public_chain.py
```
Result: **656 passed / 1 skipped / 1 red** (813s) — `manager/final-broad-r7.txt`.
The single red: `tests/s12/s12-lc3-qa-r5/test_r5_matrix_packet.py::test_r5_probe_inventory_is_static_and_exactly_mapped`
— the R5 audit test needs `S12_R5_CANDIDATE_ROOT` + `S12_R5_EXPECTED_CANDIDATE_SHA`; the broad run had no env
(config miss — same test also failed at R6-era for a different reason; do not conflate).

### 2b. Env-correct re-run STILL fails → attribute, don't alarm (finding R7-B2)

Re-ran `tests/s12/s12-lc3-qa-r5/` WITH env (`root=integration worktree`, `SHA=8a9d793…`): still **1 failed / 2 passed**.
Raw assert:
```
AssertionError: ('tests/s12/s12-t03a/test_s12_export_migration.py', 'test_single_head_is_new_revision')
```
Root cause: the static `EXPECTED_PROBES` inventory referenced node names that the **authorized Q02 correction**
(`666dc5e`, bounded T03A exception) had deliberately renamed:
`test_single_head_is_new_revision` → `test_single_head_is_current_head` and
`test_upgrade_from_parent_retains_data` → `test_upgrade_from_parent_retains_data_to_current_head`.
Classification: same class as the contract-mandated supersession FINDINGs — the audit's *provenance assertions*
(env root/SHA/branch/clean checks) stay byte-intact; only the node-name inventory map is stale.
Action: `B/manager/FINDING_r7b2_r5_inventory_rename.md` + bounded QA sync turn (enumerate ALL renames
programmatically, patch only the names, full R5 dir re-run with env → expect 3 passed, commit
`S12-LC3-QA: R5 inventory sync to Q02-delivered T03A names (finding R7-B2)`). Never weaken the provenance
assertions; never count the inventory red as a code defect in the packet.

## 3. Immutable probe re-run v2 (frozen copy of the tip)

Runner: `outputs/s12-r7-two-managers/run_review_probes_r7_v2.py`. Frozen source:
`git archive 8a9d793… -o tip-r7.tar; tar -xf tip-r7.tar -C manager/frozen-tip-r7/`.

Hard requirements discovered v1→v2:
- **PYTHONPATH needs FOUR roots** (v1 died `ModuleNotFoundError` twice):
  `<frozen>` + `<frozen>/tests` (for `import test_s09_structural_lock_producer as base`) +
  `<frozen>/tests/s12/s12-lc3-retry` (`test_r4_retry_execution`) +
  `<frozen>/tests/s12/s12-t03c` (`test_publication`).
- **`S12_REVIEW_OUT` = fresh dir PER PROBE** (`open(..., 'x')` exclusive-create; reused dir = instant error).
  v1 symptom for inner_fence/planner: `KeyError: 'S12_REVIEW_OUT'` raised AFTER the full test logic had already
  executed (threads joined, snapshots taken) → classify as harness config, not a test failure.
- Per-probe `--basetemp` under the real Windows Temp; probe files copied hash-identical (sha256 recorded).

Results (probe copies sha256 in `review-probes-r7-out-v2/probe_results_v2.json`):
| Probe | sha256(12) | Result | Cross-check |
|---|---|---|---|
| identity | `0b8ff350c024` | 3 passed | == A-handoff RETRY gate1 probe sha `0b8ff350…` |
| inner_fence | `524d4a861eba` | 1 passed | == VAL handoff gate1 probe sha `524d4a86…` |
| producer | `0dc12b5edc28` | 6 passed | 3 timing-denial variants + points-only + 2 DB-rejection controls |
| planner | `40c9d3e88782` | 2 failed — BY DESIGN | see below |

Artifacts written by probes (all under `review-probes-r7-out-v2/<probe>/`): identity × 3 case JSONs
(`identity-{unknown_manifest_run,missing_manifest_other_type,escaped_manifest_duplicate}.json`), `inner-fence.json`,
planner × 2, producer × 4 (`timing-fps_num-None`, `timing-fps_den-None`, `timing-duration_ms-0`, `points-only`).

### Planner probes = interface-change mapping (NOT a regression)

Both cases replay the reviewer's captured **pre-timeline** authority; on the frozen candidate the submit path now
returns `FullApplyServiceError: LEGACY_AUTHORITY_REAPPROVAL_REQUIRED: v2 authority predates the frozen timeline
block; public reapproval is required (legacy rows are never backfilled or reinterpreted)` — the frozen Q7 semantics.
The probes' semantic intent (co-occurring plan compiles; same-role disjoint compiles) is re-verified in the new
world by the BRIDGE D2 nodes (`test_b03_cooccurring_graph_all_occurrences_active_layers`,
`test_b03_repeated_role_distinct_routes_regions_ranges`, + B05 legacy nodes), all green in the 31-node suite.
Written up in `B/manager/REVIEW_PROBES_RERUN_R7.md` with the explicit old→new mapping. Rule: probes failing after
an authorized interface change get a mapping + new-world coverage citation; never a regression verdict, never a
weakened probe.

## 4. Packet-doc build order that worked

`INTEGRATED_COMMITS.md` (merge table + deltas + static) → `BYTE_GUARDS.md` (guards + snapshots + stale-baseline
note) → `REVIEW_PROBES_RERUN_R7.md` → `REPORT.md` skeleton (QA-dependent sections left as explicit placeholders
filled from the QA chain turn) → MATRIX / VIDEO_STATUS / NEXT_REVIEW_PACKET after the chain lands. Interim docs
built while the QA public chain ran in parallel saved a full serial round at the end.
