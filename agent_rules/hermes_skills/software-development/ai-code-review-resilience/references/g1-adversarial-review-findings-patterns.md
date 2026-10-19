# G1 Adversarial Review: 7 P1 + 2 P2 Findings and Prevention Patterns

Documented from the MotionForge2D G1 independent review (2026-10-18), where 76/76 unit tests were green but an adversarial Codex review identified 7 P1 and 2 P2 findings.

## 1. Provenance & Dependency Verification (G1-R01)
- **Defect**: Dependency verifier accepted a record where a consumed reference (`grey_ref`) was removed and the self-digest recomputed. Furthermore, changing graph sampler from `euler` to `heun` in the generated workflow was ignored because the verifier only checked steps, CFG, and model name.
- **Root Cause**: `if "grey_ref" in consumed:` instead of requiring `consumed["grey_ref"]`. Lack of sampler verification in graph inspector.
- **Prevention Pattern**:
  - Enforce mandatory consumed references per generation mode (fail-closed if missing, null, or role mismatch).
  - Inspect generated graph JSON for effective sampler, scheduler, and reference image nodes against the authoritative recipe.

## 2. CLI Tooling & Argparse Availability (G1-R02)
- **Defect**: `r6_cotracker.py` crashed with `NameError: name 'argparse' is not defined` when invoked via CLI `python -B r6_cotracker.py --help`.
- **Root Cause**: Module import cleanup accidentally dropped `import argparse` while `main()` called `argparse.ArgumentParser()`.
- **Prevention Pattern**:
  - Unit tests that test a CLI tool must include a subprocess invocation test: `subprocess.run([sys.executable, "-B", script_path, "--help"])` asserting `returncode == 0` and expected usage string.

## 3. Strict Tensor & Metric Contracts (G1-R03)
- **Defect**: CoTracker validator accepted empty tensors ($T=0, N=0$), visibility containing `NaN`, or visibility values outside $[0, 1]$ (such as 9.0). In window drift calculation, when a window contained no visible pairs, `np.nanmean` produced `NaN` which serialized into invalid JSON.
- **Root Cause**: Shape-only assertions without value range checks; clip-wide visibility checks (`both.any()`) used to gate windowed calculations.
- **Prevention Pattern**:
  - Always validate tensor dimensions ($T > 0, N > 0$), finiteness (`np.isfinite`), and domain range (visibility $\in [0, 1]$).
  - In windowed metrics, check visibility within the specific window slice (`both[window].any()`). When empty, assign `None` and ensure serialized JSON contains no `NaN`.

## 4. Subprocess Fail-Closed Propagation (G1-R04)
- **Defect**: Child blend process exited with return code 7, but parent runner caught `SystemExit`, printed a log message, and exited with code 0. Subsequent pipeline steps saw exit 0 and attempted to reuse stale manifests.
- **Root Cause**: Catching errors in `main()` without re-raising or calling `sys.exit(1)`.
- **Prevention Pattern**:
  - In orchestrator CLI scripts, any non-zero child exit must cause the parent CLI to exit non-zero.
  - On failure, unlink prior intermediate manifests (`blend_manifest.json`) immediately so stale success artifacts can never be adopted by subsequent stages.

## 5. Transition Boundary Event Mapping (G1-R05)
- **Defect**: Event key discovery only sampled start boundaries (`from`) of visible windows, missing occlusion transitions, entity exit boundaries, and contact release points.
- **Root Cause**: Filtering `w["class"] in ("VISIBLE", "PARTIALLY_VISIBLE")` ignored the frame where an actor became occluded or exited.
- **Prevention Pattern**:
  - Transition boundaries occur whenever state changes: entry ($w_{from}$), occlusion start, reappearance, and exit ($w_{to} + 1$).
  - Contact events must track both acquisition (`from`) and release (`to`).
  - Propagation plan runs must split at hard cut and transition boundaries to prevent interpolation across scene changes.

## 6. Evidentiary Rigor in Quality Matrices (G1-R06)
- **Defect**: Quality matrix awarded `PASS` if an evidence file simply existed (even if 0 bytes), or if a string was found in source code. Gate conformance accepted invalid mode `"finla"` as valid and lacked real callers.
- **Root Cause**: Checking `p.exists()` instead of parsing the file; loose enum checks in gate functions.
- **Prevention Pattern**:
  - Evidence files must exist AND have `st_size > 0`. JSON evidence must be parsed, schema-validated, and checked for `verdict == "PASS"`.
  - Batch gate functions must strictly whitelist modes (`mode in ("engineering", "final")`) and raise typed `GateBlock` on unknown modes.
  - Wire all gate functions into the actual submission pipeline rather than leaving them as orphan helpers.

## 7. Windows Ancestor Path Filtering (G1-R07)
- **Defect**: `build_manifest()` skipped any path containing substring `"/work/"` or `"\\work\\"`. Because the repository sat under `C:\Users\Admin\Documents\Codex\work\...`, ALL files were excluded, producing an empty manifest.
- **Root Cause**: Applying substring exclusion to absolute paths rather than relative paths from the task root.
- **Prevention Pattern**:
  - Always compute `rel = p.relative_to(root)` and check exclusions against `rel.as_posix()` (e.g. `rel.startswith("work/")`).
  - Assert `manifest["count"] > 0` before returning.
