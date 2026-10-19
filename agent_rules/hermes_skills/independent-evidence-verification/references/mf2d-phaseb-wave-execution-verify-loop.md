# MF2D Phase B — DAG wave execution + independent verify loop

Proven mechanics from the 28-task delivery RUN `mf-delivery-runs/20260927/20260927T163824Z`
(2 worker lanes + Manager; cap ≤3 upstream streams incl. Manager).

## 1. Task worktree + dependency transport
- `git worktree add -b codex/mf-end-<NN>-0928 <work>/mf-delivery-20260927/MF-END-<NN> <dep-commit>`.
- A task starts from ONE dependency's commit and receives the others by
  `git merge --no-ff <dep-commit>` **before dispatch** — not from the frozen wave SHA alone.
  Examples: MF-END-14 base `4500af7`(13) + `--no-ff 1ce1a4b`(08);
  MF-END-15 base `2d7a328`(05) + `--no-ff 88ef530`(14) + `--no-ff bc87fa3`(18);
  MF-END-19 base `9b10d1e`(15) + `--no-ff a2d7cc8`(16).
- After each merge assert `git status --porcelain == 0`, then record the transported shas in
  `manager/guards/<TASK>_before.json` and in the ledger row. Write-sets are disjoint across this DAG,
  so merges are conflict-free — still check per-path `exists` flags (patch-with-preimage vs NEW).

## 2. Manager guard BEFORE dispatch (measure, don't assume)
- head sha; porcelain count; per-path `{exists, bytes, sha256}`.
- **Migration head: `python -m alembic heads` ONLY.** A regex scan of `down_revision` produced a
  stale "sole head" (`f7a8b9c0d1e2` vs the real `d4e5f6a7b8c9`); the lane measured the truth and
  disclosed it. Pin the exact new migration filename + `down_revision` in the launch packet and
  forbid touching old migrations.
- Baseline: the task's test files + `tests/product_p1/public_chain` (30p/2s at this base).
- Launch packet carries measured facts the lane must not re-derive (proof numbers, node registrations,
  weights present/missing, D2 findings) plus the explicit rule set from the original task packet.

## 3. Verify on lane EXIT (first thing, same turn as the exit notice)
1. `git log --oneline -1` + `git show --stat` → commit scope == allowlist exactly; any extra path = inspect.
2. Re-run the task's own suite yourself: `python -m pytest tests/product_delivery/test_mf_end_<NN>.py -q -p no:cacheprovider`
   (the lane's gate rows are not a substitute).
3. porcelain clean; `git branch -r --contains HEAD | wc -l` == 0 (nothing pushed).
4. Append a ledger row (append-only, prefix sha asserted immutable), then dispatch the next
   dependency-ready task immediately.
- Protected tests may change ONLY with pre-registration: `writeset_guard_protected_test_change.json`
  written BEFORE the patch with the impacted assertions + writer attribution. MF-END-05 did this for a
  migration head re-point of `test_mf_end_02.py` and re-ran it green (13/13).

## 4. Wave / lane selection
- Readiness comes from the TASK_BOARD dependency column — do not guess layers.
  Actual chain observed: 01 → (02+08+11+18) → 03→04→05→06→07 (tool) and 12→13→14→15/16→17→19 (core).
- ≤2 workers + Manager. If no dependency-ready disjoint task exists, leave the slot idle AND say why —
  silence reads as breakage to this user.
- Conditional/challenger tasks: `SKIPPED_NOT_NEEDED` is a verdict, NOT a pass (`counts_as_test_pass=false`);
  never loosen a gate to make a challenger eligible; record `MEASURED_INELIGIBLE` /
  `BLOCKED_NO_WEIGHTS` with measurements (MF-END-17 pattern).

## 5. Monitor lifecycle (bg monitors)
- Monitor scripts bake their `LANES` dict at import. When lanes change, `sed` a copy with a new log name
  (`monitor_phaseb_d.py` → `_e` → `_f` → `_g`…) and launch the copy; the running instance keeps its
  stale lanes through its 6 ticks.
- Stale instances emit `STALL_AUDIT>8min` for lanes that already exited — false positive. Resolve real
  lane state from the hermes DB (message count + last-timestamp age), not from the monitor line.

## 6. Provider flaps at the very last step
- 502/503/422 often kill a lane right before it writes docs (GPU/disk outputs already complete):
  wait ≥5 min, `--resume` the SAME session with a docs-only packet, cap tool output (≤200 chars/command,
  write files via scripts).
- `exit 0` + ~125 B log = flap; a few KB = ran out of budget/conversation. Check disk/DB before
  believing anything.
