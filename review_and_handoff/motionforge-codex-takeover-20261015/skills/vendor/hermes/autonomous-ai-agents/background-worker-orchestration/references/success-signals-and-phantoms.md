# Success signals that lie, and phantom guard failures

Companion to `monitoring-and-finish-runs.md` and `flap-resume-cycle.md`. Same provenance: measured during a
9-lane / 12-dispatch correction round (8 h dispatch wall time, 11 receipts, 2 upstream flaps).

## 1. Three different ways "success" is fake

| Signal | What it actually meant | Rule |
|---|---|---|
| `npm run build 2>&1 \| tail -30; echo "RC=$?"` → `RC=0` | `$?` was **`tail`'s** exit code, not the build's | Never pipe a gate whose result you will report. Redirect instead: `cmd > out.txt 2>&1; echo RC=$?`, or read `${PIPESTATUS[0]}`. This printed one wrong PASS in a UI gate (build was genuinely fine, but a *lint* failure was also masked in the same block); I only caught it by re-running unpiped. |
| launcher `exit 0` + 124–125 B log | pure transport flap (`HTTP 503 … 502 fetch connect timeout`) | log **bytes** is the discriminator: ~125 B ⇒ nothing ran; multi-KB prose tail ⇒ the worker did work and stopped for another reason. |
| launcher `exit 0` + long run, no commit | turn-budget exhaustion | read the worker's own log tail; it usually enumerates the unfinished steps, which is exactly what the finishing packet should replay. |

## 2. Confirmation run — when the artifacts already landed

If a run dies *after* writing its deliverables (report exists, commit exists, tree clean, but the log tail is a flap),
do **not** re-run the work and do **not** call it done on the worker's silence. Resume the same owner with a
**read-only confirmation packet**:

- re-state the footprint (`git rev-parse HEAD`/`HEAD^`, `git show --stat`, `git status --porcelain` must be empty);
- re-hash the sentinels the round promised not to touch, and quote bytes/rows/sha256;
- answer **one** explicit open question (e.g. "is the evaluated freeze still the only one on disk?");
- state that the run should normally write nothing, and cap the budget (~25 calls).

Measured value: the confirmation run produced the decisive "B4 stands" verdict, correctly attributing a mtime change to
a deterministic re-export with identical bytes, and reported that no newer freeze existed.

## 3. Phantom guard failures and how each was fixed

| Phantom | Cause | Fix |
|---|---|---|
| `outside_allowlist: ['pp/schemas/media_engine.py']` | `.strip()` applied to the whole `git status --porcelain` stdout ate the significant leading space of the first line (`' M app/…'`) and shifted the `XY` columns by one | strip per line **after** slicing; sanity-check that any reported violation path is a real file before accusing a writer |
| `protected_tree_drift:<LANE>:head=<new> porcelain=0` | the lane legitimately committed; the guard compared HEAD to the pre-dispatch baseline | accept a **verified advance**: old baseline is an ancestor of the new HEAD **and** every file in `base..HEAD` is inside that lane's own allowlist |
| drift flagged on a lane that is actively writing | the guard's "other trees" check ran while the worker still owned its tree | pass the currently-active lanes to the guard and skip them there |
| finish-run reported as drift on its own tree | `"<LANE>-finish"` did not match the `"<LANE>"` key used by the tree/allowlist maps | normalise `-finish` → base lane name before deciding which trees to skip |
| watchdog exits "all workers exited" mid-wave | its pid list belonged to the previous wave | re-arm (pids **and** session ids) on every new batch; treat a lane whose receipt file exists as DONE, not stalled |

## 4. Verification ladder (manager side)

1. Copy the reviewer's probe into **your own scratch**; repoint only its output/scratch paths (assert the substitution so
   a silently-unmatched replace cannot no-op). Running it in place overwrites review evidence.
2. The probe header usually embeds the module sha it imported — recompute that sha from disk and require equality before
   believing either side.
3. Require worker "before" evidence to reproduce the reviewer's published results **field-for-field**, and your own
   after-run to match the worker's after-run.
4. Re-run the load-bearing suite yourself and compare the numbers (a reproduced `68 passed / 185.25 s` is worth more than
   any prose).
5. If the reviewer's script **aborts** on the fixed code, that abort can *be* the fix (typed refusal replacing a silent
   pass). Capture per-item outcomes in `try/except` and say so, rather than reporting "the probe failed".

## 5. Reporting details that decide whether a claim survives review

- **Interface delta disclosure.** If the fix removes/renames a parameter the reviewer's probe calls (a caller-supplied
  boolean replaced by a backend-resolved proof object is the archetype), state the old call, the new call, and that the
  reviewer's one-liner will now raise — with the exact re-run form.
- **Staleness is judged by BYTES, not mtime.** A deterministic re-export rewrites identical bytes with a new mtime;
  the correct verdict is "freeze unchanged, evaluation stands", with the mtime movement disclosed.
- **Lineage before transport.** Measure `merge-base` between each source branch and the integration base *before*
  dispatching a transport owner: a branch can lack the integration base as an ancestor while sharing an older
  merge-base, which changes the method to cherry-pick-with-conflict-abort instead of fast-forward. Put that fact in
  the packet.
- **Coverage honesty.** State which artifacts/frames were actually inspected and which were not; a technical all-PASS is
  never a visual PASS.
