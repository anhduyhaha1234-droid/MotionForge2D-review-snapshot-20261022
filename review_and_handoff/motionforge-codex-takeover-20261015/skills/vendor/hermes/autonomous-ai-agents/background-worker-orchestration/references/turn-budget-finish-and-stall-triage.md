# Turn-budget finish packets, stall triage, and reviewer-probe hygiene (2026-09-24 round)

Session-specific detail behind the SKILL.md updates of the same date. Wave: 3 correction lanes
(`MF-V1-COMFY` ∥ `MF-P1-QC-EVIDENCE` ∥ `MF-TOOL-CONTRACT`) resumed in their own worktrees on a pinned
route, cap of 3 upstream streams, 45 s stagger, one packet per lane per round.

## 1. Same launch, three different endings — all `exit 0`

| lane | duration | rows | true state at exit |
|---|---|---|---|
| COMFY | 2,916.7 s (48.6 min) | ~216 | **complete**: 5 files committed (`aacb99e…`, +1,411/−17), REPORT+HANDOFF+19 raw files, tree clean |
| CONTRACT | 3,341.4 s (55.7 min) | 194 | **budget-exhausted mid-flight**: implementation done, 5 files dirty, but `final_gates.py` never executed, no suite/ruff re-run, **no commit**, **no REPORT.md** |
| P1QC | 3,777.3 s (63.0 min) | 198 | **budget-exhausted mid-flight**: evidence root never created, no REPORT/PROVENANCE, ruff full not run, final test count measured before the last hunk, **no commit** |

All three receipts were byte-comparable (`exit_code: 0`). The discriminator was the **log tail**: the two
incomplete lanes each ended with a numbered "what is left" block naming their own remaining commands —
the classic iteration-cap signature — while the complete lane ended with a delivered-artifacts report.
Neither incomplete lane had a tiny log, so this was NOT a connection death and NOT a resumable-unchanged case.

## 2. Finish-packet skeleton actually used

```
# <TASK> — finish the round (<n> steps + report). Same owner, same task, no new scope.
Owner session (resume this exact id): <parent>
Tree / branch / baseline HEAD ; note "<k> uncommitted paths, all inside your allowlist"
Your evidence root (literal, no nested NEW folder): <abs path>   ← P1QC had never created it
1. Why you are being resumed → quote its own log's remaining-step list; state plainly the run
   ended on BUDGET, not on an error; add the Manager-measured guard result (VERIFIED, k paths in scope)
2. Do exactly these steps (copy the lane's OWN commands, verbatim) + report shape
3. Non-negotiables unchanged (allowlist, patch-only preimages, forbidden paths, local commit only)
4. Terminal + "iteration budget ~45-60 turns — closing run, not a redesign"
```

Both finish packets were dispatched as background + `notify_on_complete`, each minting a new session id
(`20260924_190346_117cc4`, `20260924_190556_490177`) resolved from the first-user-message match.

## 3. Stall triage actually performed

`STALL DETECTED ... CONTRACT rows=194 age=8.8m` fired 9 minutes after CONTRACT's run had already ended.
Order of triage that resolved it in one pass:

1. `manager/receipts/<lane>.json` exists → `exit_code 0`, `ended_at_utc` 11:54:15Z → the lane is DONE.
2. Log tail read → coherent closing report, not a hang.
3. `git log -1` in the tree → no commit for CONTRACT (expected — it ran out of budget), tree dirty in
   allowlist only.
4. Heartbeat then showed the OTHER two lanes still moving (rows +0.2 min) → no real stall in the wave.

Fix applied afterwards: the watchdog module gained a per-lane `FINISHED_RECEIPTS` map (receipt ⇒
`DONE(exit, not stalled)`) and the lane list was re-pointed at the **minted** session ids + freshly
derived pid pairs. See `scripts/receipt_aware_lane_watchdog.py`.

## 4. Post-worker guard false positives (both were tool bugs, not lane violations)

- **Porcelain `.strip()`** on the whole `git status --porcelain` stdout ate the leading space of the
  first line and produced a phantom `outside_allowlist: ['pp/schemas/media_engine.py']` — the real path
  was `app/...`, entirely inside the allowlist. Never strip the aggregate; strip per line after slicing.
- **Verified HEAD advance misread as protected drift.** A lane that legitimately committed moves its own
  tree's HEAD. The guard now accepts an advance only when the old HEAD is still an ancestor
  (`git merge-base --is-ancestor`) AND every file in `<old>..<new>` is inside that lane's allowlist AND
  the worktree is clean; it records `verified_advance: true` so a reviewer sees why the check passed.
- Active writers must be passed as `known_active` entries, else their in-flight dirty state reads as
  cross-tree drift.

## 5. Reviewer-probe hygiene (independent repro of a worker's fix)

To re-run the reviewer's own probe against the lane's fixed bytes without touching review evidence:

1. Copy `REVIEW/.../probe_adapter.py` into the Manager's own scratch and rewrite **only** the output path
   and the scratch root (`re.sub` on the two literals; keep `SRC` pointing at the lane tree).
2. Run it; assert the probe's self-reported source hash equals the hash you recompute from disk at the
   new HEAD — that is what proves the probe ran against the FIXED bytes (observed: `925f9117…` = disk).
3. Compare three ways: worker `probe_before` ≡ reviewer's published results (9/9 fields) → the baseline
   was the same bytes; worker `probe_after` ≡ Manager's own run (9/9) → the fix is independently
   reproduced; Manager-run full module suite (`131 passed, 10 skipped`) → the claim holds at HEAD.
4. **Scratch depth matters on Windows:** `<deep evidence root>/manager/scratch/repro/<probe>/<case>/reservations/<32-hex>__att.reservation.json.tmpNNNNN`
   exceeded MAX_PATH (260) and the third case died with `FileNotFoundError` while the first two passed.
   Put probe scratch under `C:/Users/<u>/AppData/Local/Temp/<tag>` and keep only the RESULT JSON in the
   deep evidence root.

## 6. Numbers worth reusing as calibration

- Resumed lanes mint new session ids in the same second-window as dispatch; resolve by content, never by
  order (three lanes, three ids, stagger 45 s but ids 10 s apart).
- Per-lane evidence-file counts at exit are a good first triage signal: 21 (complete COMFY) vs 15
  (implementation-but-no-report CONTRACT) vs 0 (P1QC, root never created).
- A 3-lane wave at 48–63 min per lane with ~200 messages/lane stayed inside a 3-stream cap with 45 s
  staggering and produced zero upstream flaps this round.
