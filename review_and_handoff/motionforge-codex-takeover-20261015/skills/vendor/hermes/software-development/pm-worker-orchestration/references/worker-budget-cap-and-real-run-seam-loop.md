# Worker budget cap + real-run seam loop — orchestration quick rules (bridge)

Full field notes (all measured, incl. occurrence logs R1–R4 and seam-class catalogue A–G):
**`independent-evidence-verification/references/iteration-budget-exhaustion-and-finish-packets.md`**.
This file is the short version for dispatch/verify turns; when in doubt, read that doc first.

## The 6 rules that matter most (each cost a real incident)

1. **Cap 160/160 ≠ loss.** The cap frequently lands AFTER commit+evidence (banner only in the
   final summary turn). On every `exit=0`, check the log tail for the banner, then MEASURE:
   porcelain → run the task's own tests yourself → evidence dir. Post-commit ⇒ verify normally.
   Pre-commit ⇒ resume the SAME session with a ≤40-call finish packet (4 steps: rerun 2 test
   commands → close REPORT/final gate/commands.jsonl → commit exact allowlist → terminal).
   Measured recovery: 3m28s–5m46s.
2. **Pin the advisory in every large packet:** "budget ~110 calls; ~130 → commit allowlist +
   REPORT FIRST, then continue." Cheap; not always sufficient — hence rule 1.
3. **SHA provenance:** only `git rev-parse`-measured SHAs in packets/ledgers/freeze docs.
   A plausible hand-extended tail was caught by the worker's `rev-parse --verify` and had to
   be disclosed + corrected. Packet step: "resolve HEAD by rev-parse; flag any packet SHA that
   fails `rev-parse --verify`."
4. **Fixture route-parity:** a green unit test proves nothing if its fixture fabricated the
   contract (measured: layer-keyed fixture vs role-keyed real route → 6/6 green, real run dead
   at chunk 0). Fixtures for seam-fixes must come from the FAILING REAL RUN's artifacts
   (captured manifests/MP4s/DB rows) and the test rebuild ships in the SAME commit as the fix.
5. **Wave arithmetic:** expect `passed == previous_candidate_total + new_tests`; add FAILED rows
   to the collected total before calling a shortfall a collection defect. Generated-artifact
   regen (packaging inventory) goes into the SAME advancing commit — or is DEFERRED with a
   ledger row when a read-only lane is running on the tree (never regen mid-run), folded after
   the LAST `app/**` change of the batch.
6. **New migration → older head-pinned tests go red by design:** pre-register the protected-test
   change BEFORE patching, re-pin to the measured chain (`python -m alembic heads`), keep the
   fail-closed behaviour untouched, then re-run that file + the full wave.

## Measured Windows transport constants (recurring in payload-bearing pipelines)

- Child-process argv ESCAPED ceiling: ~**32,500 B spawns OK / 32,700 B → WinError 206**;
  payloads above it need file-based transport (already struck task-23 and the QC composer).
- Deep managed roots push FILENAMEs past MAX_PATH (276 chars measured) → run engines under a
  SHORT managed root (`%TEMP%/<short>`), copy receipts back to the evidence root.
- ComfyUI 0.37 publishes SaveVideo under history bucket `images` (+`animated`), not `videos` —
  pin media-kind expectations to captured server history, never to names.

## Monitoring hygiene for long single-rollover chains (this RUN's tooling)

- Resolve each new lane's session id from the state DB by matching the packet's FIRST line
  (~40–60 s after launch); never guess an id. Put the resolved id into the monitor's LANES.
- Monitor rollover: `sed` the log-name token to mint the next monitor script (`_s`→`_t`→…).
  A RUNNING monitor instance keeps the LANES it loaded at launch — after you edit the file for
  a new lane pair, either accept stale ticks on finished lanes until rollover, or launch a
  fresh instance immediately (`_u`, `_v`, …) pointed at the current pair.
- Ticks reporting `end=None STALL_AUDIT` on a lane whose task is already verified/terminal are
  noise from a stale LANES set — not a new stall. Fix the LANES, don't chase the audit.
