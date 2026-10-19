# S12-R7 execution round + INT transport (Manager B, 2026-09-16) — annotated detail

Companion to `s12r7-two-manager-split-and-b-activation.md` (covers split, freeze, rulings,
flapping-502). This file covers the round AFTER the freeze: lane execution → QA review →
coverage follow-up → INT transport R1 → post-transport sync + parallel chain/gates → combined-candidate
finite red (CR2 fix + guard re-baseline, §7).

## 1. Lane execution results (all Manager-verified, no push)

| Lane | Tip | Manager verify |
|---|---|---|
| B01 (F03 timing) | `a027c59` ← `2871f8f` (+741/-46; NEW `structural_lock_source_timing.py` 295L, codes MISSING/UNPROVEN/VFR/MISMATCH, Fraction arithmetic, probe_source) | re-run 27 passed; ruff clean; guard allow 8/8 + protected 18/18; committed==worktree bytes proven (6× green runs) |
| BRIDGE (F04) | `c49a578` = `b6108d4` (4 svc +1251/-148) + `34e680c` (+2444) + hashrec | gate-set parity: micro 27 / api 71 / reg 66; G4 out-of-gate confirmed flagged 3-fail set; `derive_region` clip reviewed; guards 4/4+18/18 |
| QA (F05) | `666dc5e` → `d22d069` (freeze sign-off) → `958d021` (BRIDGE review) | micro re-runs; t03a module 4-fail→9-pass |

## 2. QA review of BRIDGE (one bounded verify turn) — what a good review delivers

QA commit `958d021` (+39/-5): D2 VERBATIM_27 (programmatic diff empty; QA re-ran the suite
independently 27p), Q9 CONFORMANT 19/19 fields + real sidecar sample archived, legacy alias
BOUNDED-no-hole (202-control), **Q4 v0.2.1 code ACCEPTED but coverage gap: 3 missing nodes +
unused `cross_key_conflict` fixture**, FINDING-r7b1 opinion AGREE-supersede.

## 3. Coverage-gap follow-up (bounded, test-only, owner-side)

Prompt to BRIDGE owner: add 4 nodes ONLY in `tests/s12/s12-public-authority-bridge/` + docs —
(1) Mode-B padded clip POSITIVE (`{400,100,250,250}` on 640×360 → region `[0.625,0.2778,0.375,0.6944]`,
proceeds 202); (2) SCALE_UNRESOLVED NEGATIVE (dims hidden → typed deny, zero mutation);
(3) fully-outside DENY; (4) cross-key precedence via the unused fixture. Result: commits
`db1c66c` + `dae7632`, suite 27→31, ruff/diff-check clean, protected 18/18. Docs record
"Q4-coverage additions beyond D2" (original list stays DELIVERED VERBATIM). Manager re-verified:
31 passed + protected guard + scope.

## 4. INT transport round 1 (sole integrator, 5 lanes)

Prompt = 5-row table (lane | branch | exact commit | verified-by | files) + per-merge pre-checks +
merge command pattern + static gates + evidence paths. Order VAL → RETRY → B01 → BRIDGE → QA.

- Pre-merge per lane: branch tip == exact commit; owner porcelain per handoff
  (VAL `?? work/`, others empty); `git diff --name-only <sha>^ <sha>` ⊆ handoff file list.
- Merges (serial `--no-ff`, zero conflict): `0ea57b5`(VAL 8f) → `2942efb`(RETRY 3f) →
  `4cd2966`(B01 8f) → `761414a`(BRIDGE 13f) → `8704ec0`(QA 6f); docs `c3cf095` (+70).
  Deltas 8/3/8/13/6 = 38 paths exact (+7573/-249); total 40 vs base.
- **41-char SHA typo incident**: prompt + handoff carried `4ce3b13...c1aceace...` (extra 'c');
  INT resolved to `4ce3b136c8c9d7bd7c1aceace590dfb6a8c2d15ab` via branch tip + parent==wave-base +
  diffstat match (+ A's NO_ACTIVE_WRITER.json used the 40-hex form); both forms recorded in
  R7_REPORT — classification: documented correction, not a deviation.
- Static: compileall 0; py_compile 24 files 0; ruff `--select F` All checks passed; full-ruleset
  informational only (136 style-class, no F). `geometric-repack` stderr = pre-existing noise.
- Final tip `c3cf0955ffea02cb2070c0f6a3ce694c10ed3c5e`; ledger 70 entries; RAW 106,946 B.

Manager verify of transport: `git log --format='%h %p %s'` shows each merge's second parent ==
source SHA; tip == docs commit; porcelain 0.

## 5. Post-transport: lane sync + parallel chain/gates

- ff-only sync the QA worktree to `c3cf095` BEFORE re-dispatching QA (its branch is an ancestor →
  `git merge --ff-only <tip>`; exit 0 with the repack warning; ends at new tip, porcelain 0).
- Dispatch in one batch: QA public-chain turn (`--max-turns 600`; Q04+P01–P03; R5 env refreshed to
  candidate root + NEW tip SHA; chain explicitly must now pass the former S10 422 seam; UI install
  lockfile-respecting in disposable copy; replay/cancel/expiry) + Manager finite suite (10 files:
  retry×2, val×2, t03c publication, b01, bridge (31), qa-r6 finite+prep+inventory(r7)) in a bg run.
- Broad gate + R5 probes stay serial after finite green; packet build last.

## 6. Reusable checklists

- Dispatch-prompt SHA rows: resolve each from `git rev-parse <branch>` (assert 40 hex), never from
  memory notes; transporter resolves malformed SHA from tip + parent + diffstat and records both.
- Verify a follow-up turn: `git show --stat` each commit, suite re-run count match, protected guard
  verify, docs "additions beyond" note present, original frozen list untouched.
- After any transport round: ff-sync the next writer's lane first; refresh env SHAs (R5) to the new
  tip; then dispatch chains/gates in parallel, broad serial-only.

## 7. Combined-candidate finite → cross-lane interaction fix (CR2) + guard re-baseline

Context: finite suite (10 files) ran on `c3cf095` in parallel with the QA public-chain turn.

- Result: **195 passed / 1 failed (348.26s)** — lone red
  `tests/test_s09_structural_lock_producer.py::test_B01_F_pin_and_reapproval_full_apply_executable`.
  Raw failure (extracted from the gate log, not guessed): `assert eligibility["full_apply_executable"]
  is True` → actual False, reason `OCCURRENCE_GEOMETRY_BOX_MISSING: missing/ambiguous affected geometry
  (no boxed segmentation/prompt evidence)`.
- Root cause: B01_F's `seed()` fixture created occurrence segments WITHOUT boxed geometry; BRIDGE's
  frozen F04/B04 semantics (no boxed geometry ⇒ typed ineligible) deny that on the combined code,
  while B01's own lane (pre-BRIDGE) still treated it as executable → green. NOT a production bug —
  superseded POSITIVE control. In-write-set (B01 owns its test file) ⇒ direct bounded correction;
  the OUT-of-write-set sibling (`tests/test_s09_t06_backend_authority.py`, 2 reds) correctly routes as
  FINDING r7b1 + Codex write-set decision instead.
- CR2 execution: (1) `git merge --ff-only c3cf095` in the B01 worktree (clean, exit 0, known
  geometric-repack noise); (2) bounded prompt: `_seed_graph` persists sanctioned boxed geometry
  (normalized `segmentation.boxes`, same persisted interface BRIDGE's conftest uses; boxed=True/False
  variants) + assert the timeline block inside B01_F + new no-boxes negative node; production untouched.
  (3) commit `396a3c81589ea19b6c5b119e446b1bd4c7f4b754` (+148/-7; 4 files: test +101, CONTRACT/LOG/REPORT).
  Gates: **28 passed (27→28)**, 4 consecutive green runs on frozen bytes (75.00/76.12/74.14/74.85s),
  committed==worktree sha proven, porcelain 0.
- **Stale-guard false alarm → delta-vs-parent proof → re-baseline.** Re-running the PRE-WAVE guard
  manifests on the ff-synced worktree reported protected `FAILED 9/18` + allow `FAILED 3/8`. Every
  flagged protected after-hash ≡ another lane's transported commit (e.g. `s09_approval.py`
  `61916B717684…` == BRIDGE's own REPORT value). Proof-of-scope for CR2 = `git diff --name-only
  c3cf095..396a3c8` == exactly the 4 announced paths. Then captured FRESH manifests at the cr2 base:
  allow 9 entries (adds `structural_lock_source_timing.py` from B01's round 1), protected 15 entries
  (now includes `publication_lease_guard.py` — VAL's NEW file). Old + new manifests both kept in
  `B/B01/` evidence; registry records the re-baseline.
- INT transport round 2 (short prompt): verify B01 tip == `396a3c8` + porcelain empty → allowlist
  delta vs parent == 4 paths → `git merge --no-ff 396a3c8…` → static trio (compileall / py_compile /
  ruff F / diff-check) → LOG §10 + ledger append → report merge SHA + new final tip. Then: finite
  re-run on the new tip (expect 196→197 total) → broad gate → R5 probes → packet.
- General rule: when lane-green and combined-red disagree, classify from the typed reason BEFORE
  routing — superseded expectation (fix the test via its owner, ff-synced worktree first), cross-lane
  interaction defect (route to the exact owner with lane-vs-combined proof), or environment. Never
  weaken assertions; never call it a regression without the comparison.
