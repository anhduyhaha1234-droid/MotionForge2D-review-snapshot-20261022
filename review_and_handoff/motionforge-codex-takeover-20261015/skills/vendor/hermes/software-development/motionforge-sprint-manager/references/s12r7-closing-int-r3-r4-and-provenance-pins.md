# S12-R7 closing rounds — QA chain outcome, INT r3/r4, provenance-pin re-freeze (2026-09-16, Manager B)

Companion to `s12r7-final-gates-and-probe-reruns.md`. Picks up after probe-v2 (`8a9d793`) and carries the wave
to the final frozen tip. Evidence root `outputs/s12-r7-two-managers/20260916T0351Z/B/`.

## 1. QA public-chain turn outcome (commit `393e1bf`, parent `c3cf095`)

Chain run `B/QA/chain/20260916T084317Z` — what a REAL green looks like on the former blocker:
- upload → analyze → DISCOVER_OBJECTS (1 scene, 2 occurrences, pixel-scale boxing) → per-role packs (own masks)
  → producer → CAS pins ×2 → **S09 reapproval with frozen `timeline` block live** (checkpoint `13c4772d…`,
  hash `df90782d…4046e`; frame_count 120, fps 30/1, shots `[0,119]`, occurrences with `raw_box` +
  `scale_mode=pixel` + clipped region) → **S10 submit 202 (the former 422 `shots overlap` is GONE)** →
  durable worker 6 chunks → stitch → **publication + audio attach completed**.
- **B06 sidecar proof** (`b01i-sidecar-sample.json`): `per_layer_evidence` = 6 rows (3 chunk runs × 2 layers),
  every row `verdict=contributed`, `threshold 0.01`, before≠after crops, co-active rows carry DISTINCT layer
  artifacts (no-dedup proof). Manager spot-verified raw + confirmed publication chunk MP4s exist in the runtime.
- All-row counts: before 0 → after_s10 {projects 1, videos 1, configs 2, manifests 1, checkpoints 1, s10_runs 1,
  s10_publications 1, artifacts 14, jobs 5} → at_failure {artifacts 15, jobs 7, s12_export_runs 0}.

### R7-F1 — S12 export leg blocked (pre-existing product gap; needs Codex ruling)
3-part evidence (verbatim in `R7_PREP.md` + chain dir): (1) S12 preflight requires readiness `ready`
(`routes/s12_export.py:324-331`); (2) readiness needs a completed `SCOPE_FULL RUN_QC_CHECKS` run; (3) the only
public QC submit refuses scope full — `422 QC_RUN_EVIDENCE_UNAVAILABLE: no server-side evidence composition path
for scope 'full' detector 'trajectory_drift'` (`compose_check_run_args`,
`app/workflow/qc_checks_handler.py:832` — Manager-verified: audio band only, everything else raises typed).
Corroboration: the repo's OWN S12 E2E (`frontend/e2e/s12-export-seed.py::_seed_completed_check_run`) writes the
full-run row directly — the leg was never publicly reachable. Options for the packet: implement non-audio
composition vs rule the readiness gate for this wave. **Never fabricate the full run** (GAP-8 semantics).

### R7-F3 — candidate frontend cannot `next build` as-is
Next 16.2.12 prerender errors (`useSearchParams() should be wrapped in a suspense boundary`) at `/characters`
then `/apply` — pre-existing, blocks any production build. `next dev --webpack` did not hydrate in this env
(zero API calls) → prod build was the only faithful UI path: disposable copy + `npm ci` (lockfile bytes
verified unchanged, sha before==after) + **2 disclosed copy-local route-config lines**
(`export const dynamic = "force-dynamic"` in `(app)/characters/page.tsx` + `(app)/layout.tsx`, shas recorded).
UI flow: context → preflight (REAL server verdict rendered: BLOCKED + Vietnamese reason + profile PASS) →
submit disabled fail-closed → reload → reopen (fresh profile) — identical server-derived state; 5 screenshots
+ `ui-flow.json`. Report a zero-edit UI run as blocked on F3 until ruled.

## 2. R5-sync verify + INT r3

- QA `3444a49` (R5 inventory sync): `git show --stat` == exactly 3 files (+35/-10: LOG +25, `R5_MATRIX.md`,
  `test_r5_matrix_packet.py`); re-run `tests/s12/s12-lc3-qa-r5/` with env → **3 passed** (was 1 failed).
  Exception shape kept: only node-name rows changed; env/provenance assertions byte-intact.
- INT r3 prompt shape (same discipline as r1/r2, 2 commits): verify tip+porcelain → per-commit
  `git diff --name-only <sha>^ <sha>` == announced set → serial `--no-ff` merges (`159b61d` then `05eed0f`) →
  static trio → docs `7c5e3cd` → ledger 98→139 → **total delta 43 paths exact, 0 removed**. Chain-test file
  was in the merge set; the `--ignore` in both finite/broad keeps the chain node out of gates (it re-raises
  the recorded blocker by design — QA's own dir shows 16 passed + 1 by-design red, never weakened).

## 3. Provenance-pin re-freeze class (finite v3 finding → INT r4)

**Symptom** (finite v3 on `7c5e3cd`): `test_r6_finite_inventory.py::test_r6_reviewer_assertion_provenance_hash_proven`
— `IN_REPO_IMMUTABLE` pin `R5_MATRIX.md` expected `D601E8FA…` vs actual `9E136CC4…`; 196 passed / 1 failed.

**Root cause**: the pin file hashes in-repo docs QA owns. The AUTHORIZED R5-sync (`3444a49`, granted R7-B2
exception) legitimately edited `R5_MATRIX.md`; the pin map wasn't re-frozen. The pin performed exactly its job —
the drift is authorized, not a violation.

**Fix recipe** (bounded QA turn, commit `5947088`, exactly 3 files +20/-2):
1. Reconcile ALL pins programmatically vs the authorized commits (`393e1bf` + `3444a49`); only files inside
   those commits may be re-frozen. Any drift outside them ⇒ STOP + report to Manager (real drift).
2. Update the pin(s); re-run the whole pin file → **7 passed** (was 1 failed).
3. LOG + ledger; commit; **INT r4** merges it (single-commit round: verify tip → merge `--no-ff` →
   static → docs → report new final tip).
4. Re-run finite v4 on the new tip before broad/probes.

**GM rule**: any authorized amendment that touches a file listed in a provenance/pin map must include the pin
re-freeze in the SAME bounded correction (or expect the next finite to cost one extra round). The closing loop
`finite ⇄ transport` is finite and cheap — run the full finite after EVERY INT round.

## 4. Final-tip record at capture time
- Wave: r1 `c3cf095` → r2 `8a9d793` → r3 `7c5e3cd` (43 paths, ledger 139) → r4 (pin re-freeze `5947088`) →
  final tip + gates v4 in flight. All rounds: compileall 0 / py_compile 0 / `ruff --select F` 0 / diff-check 0;
  `geometric-repack` warning = pre-existing noise (exit 0), never repaired or re-raised.
- Packet status line unchanged throughout: `SPRINT_SUBMITTED / MANAGER_VERIFIED_PENDING_CODEX_REVIEW /
  NOT_APPROVED / NOT_CLOSED`; open items for Codex = R7-F1 (S12 export), R7-F3 (frontend build), R7-B1
  (`test_s09_t06` supersessions), R7-B2 (R5 lineage, closing), planner-probe mapping note.
