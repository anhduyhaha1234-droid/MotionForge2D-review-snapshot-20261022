# CODEX-C02A-DEPENDENCY-VERIFICATION — TASK_SUBMITTED_PENDING_ROOT_REVIEW

Owner `/root/motionforge_c02a_coder`; `gpt-6-sol` / `max`; fallback disabled. One CPU-only writer. Candidate `candidate-01/MANIFEST.json` SHA-256 `d3478b534182dd6cc34e219f7da12fe71bb9fde3abdbe2a6978e17c3d8fe2a18` identifies the exact four submitted files. `CANDIDATE_VERIFY.json` confirms the candidate copies, live files, diffs and pinned receipts match that manifest. Source/test writes stop with this submission; independent root review determines the verdict.

## Behavior and scope

`r6_cache.verify_deps(dep, sid=None, fid=None)` now rejects absent/incomplete/non-v3 records, invalid types and hashes, wrong requested shot/fid or plan frame/span, wrong canonical source/model paths, a bad self-digest, and missing or changed recorded files. The one-argument API remains usable. `load_deps` rejects malformed JSON, duplicate fields, non-JSON constants, invalid UTF-8 and excessive nesting with a controlled reason. Explicit `keep_source_no_visible_actor` v3 records may have empty cast/mask lists and `graph=None`; generated records require a graph. `skip_allowed` uses the strict loader and requested identity while retaining its current-settings comparison.

`r6_gate.key_inputs_now` now validates the actual dependency record before calculating review inputs. `gate_key` therefore blocks invalid dependencies before review lookup; the existing `gate_shot_before_propagate` and `gate_assemble` paths already call it before assembly copying/encoding. C01's approved review binding code and assertions remain intact. The two C01 assembly tests received only isolated fixture data: tiny source/model files, a current plan, a real isolated cache module, and a v3 passthrough record built with `build_deps`. No assertion, skip, or expected outcome changed.

| Acceptance | Evidence |
|---|---|
| A1 | Actual `build_deps` generated and no-visible-actor records verify in the new test module; positive real `gate_key` and `gate_assemble` pass. |
| A2 | Table matrix: 43 shape/type negatives and 8 strict JSON negatives; missing files and unreadable directory paths are controlled failures. |
| A3 | 7 one-field and 1 combined wrong-identity cases, each resealed, block; source/model alternate paths hold identical bytes. |
| A4 | Self-digest tamper and independent same-path, same-size source/model/cast/mask/graph mutations block; five restored controls verify. |
| A5 | Omitted source and omitted source hash block real `gate_key`, `gate_assemble`, and `r6_assemble.main` before copy/encoder tripwires. |
| A6 | Full C01 17-test module and C02A 11-test module pass together; AST audit confirms 17 C01 test names and all assertion calls preserved, syntax valid, no duplicate definitions. Final hashes and protected scope are pinned below. |

## Verification

- `AFFECTED_FINAL_01.txt`: `python -B -m unittest discover -s tests -p 'test_codex_c0*.py' -v`, exit 0, 28/28 tests. Both fixture roots were set to `OUT/c02a-worker`; fake source/model files were small.
- `root-probe-self-02/RESULT.json`: independent copied-module probe on the final source bytes, exit 0, 55/55 cases. Its fixtures and copied scripts are wholly under `OUT/c02a-worker`.
- `STATIC_AUDIT.json`: exit 0, no duplicate definitions or syntax errors; C01 test names/assertion calls preserved.
- `PROTECTED_SCOPE_CHECK.json`: exit 0; 27 pinned paths checked, 24 protected paths unchanged, only the three authorized existing files changed. The new C02A test is separately hashed.
- `CANDIDATE_VERIFY.json`: exit 0; four live files and snapshots, four diffs, four test/scope receipts match the frozen manifest.
- Red receipts: `BASELINE_EMPTY.txt`, `RED_02.txt`, `RED_03.txt`, `RED_04.txt` show the original bypass and two self-review edge cases before their respective repairs. Patch hashes/size/line counts are in `PATCH_01.json` through `PATCH_11.json`; 27 byte-matching initial snapshots are in `PREIMAGES.json` and `preimages/`.

| File | Final SHA-256 | Bytes/lines |
|---|---|---|
| `R6/scripts/r6_cache.py` | `946935906625d79b95153a92d4cf86310551cfbc4533a3661f2011854aeae7a7` | 10018 / 209 |
| `R6/scripts/r6_gate.py` | `8c2e3f9eedd4d8e11832809c2b72293db17df1fb5a4012bd39fa396f93143f94` | 17804 / 367 |
| `R6/tests/test_codex_c01_review_binding.py` | `351c39e764e53d67466688d9ec032cf9e352167e105ee0be580129f1db38fdf7` | 14693 / 330 |
| `R6/tests/test_codex_c02a_dependency_verification.py` | `403e45568fddeda038b3f10a62cf3b311764d1e91e7a5f9ef9ca3fbf78877899` | 18036 / 374 |

The candidate freeze command emitted a shell exit code of 1 because its last `git diff --no-index` correctly found differences; it still created all four snapshots, diffs and the manifest. The separate `VERIFY_CANDIDATE.ps1` command returned exit 0 and pinned their hashes. No Git commit, push, reset, stash or clean occurred.

## Open boundary

This validates recorded v3 dependencies; it does not establish that the historical producer recorded every consumed graph/reference. Effective settings equality, asset reuse wiring, staged-source freshness and unchanged end-to-end reuse remain C02B. No render, semantic media acceptance, parent task approval, UI/full-source gate or project completion is claimed. Root should review these exact bytes independently before opening another task.
