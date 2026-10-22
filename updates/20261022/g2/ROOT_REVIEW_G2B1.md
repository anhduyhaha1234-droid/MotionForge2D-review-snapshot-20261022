# MotionForge2D — root review G2-B1-PREFLIGHT-01

Verdict: **DIAGNOSTIC_APPROVED / G2_MEDIA_BLOCKED**. This verdict applies only to the read-only CPU readiness checker and its exact `READINESS.json`; it does not authorize inference, rendering, a 300-second pilot, or G2 acceptance.

Frozen authority: G1 candidate 16 manifest SHA-256 `4df7de9ccc81dff7a82a9b9d70d90a48eae2bb17cd9ff455748b041f20a0ba82`, previously approved by root for exact bytes. Transport root review: `ROOT_REVIEW_G2P01.md`. B1 worker output: `C:/Users/Admin/Documents/Codex/g2b1-readiness/`.

Independent checks performed by root on 2026-10-22:

- Re-ran `python -B -m unittest -v test_readiness` with bytecode disabled: process exit 0; all 9 tests pass. Negative cases include absent/tampered/tiny CAST, source mismatch, manifest extra file, plan gap, missing runtime, path duplication/escape. A synthetic valid input also passes.
- Re-ran `verify_postimage.ps1`: process exit 0; C16 75 files including manifest, pilot 76 including source, no candidate `.pyc`, exact hashes.
- Independently SHA-256 hashed pilot video: 36,971,916 bytes, `5a175454c2c2965bac5013a53926e210a9f70a185d802d0f2e0083a6fb399fa2`. Checked historical R6 ledger: 36,876 bytes, `1012a20a03b10e91a22e1e7a588e4f6b7f8259599f90f0d4fd855bec9f9c3715`; it remains outside pilot.
- Parsed actual `READINESS.json`: 51 checks, 19 PASS / 25 FAIL / 7 UNKNOWN, overall `BLOCKED`, media/model execution `NOT_RUN`. Plan evidence says S0021–S0074 uses 9,000 contiguous frames [2820,11820) at 30 fps; S0074 contributes 141 of its 301 frames. All 14 CAST checks are FAIL. No full 54-shot storyboard was found; historical S0021-only copies are test fixtures.
- Reviewed checker source for read-only project access, pinned authority/inventory/CAST validation, AST-only inspection of R6 modules, refusal to infer weight loadability from file presence, and `UNKNOWN` for endpoint and lease ownership. It writes only its explicit receipt in its isolated output directory. The runtime Python path is absent and 8188/8210 endpoints are not established; no service or GPU job was started.

The checker is a trustworthy *diagnostic*, not a repaired media pipeline. Recoverable exact bytes include the historical R6 actor ledger and a 16,804-byte graph template candidate; each must be checked for lineage before a new, separately reviewed pilot copy. The CAST atlas itself is present, but 0/14 pinned PNG bytes were found in the accessible C-drive sweep. New CAST generation would require an explicit repin/versioned lineage, not a fixture substitution. Other missing storyboard/input/model/runtime requirements remain real blockers.

Next permitted work: one isolated implementation writer may stage only verifiably recovered inputs or prepare a versioned CAST repin plan, then self-review; root must review the postimage before the next task. Do not mutate frozen C16, original source, old RUN, MAIN or owner work. G2 media remains blocked until fresh preflight, process/queue/lease audit, and separately gated render.
