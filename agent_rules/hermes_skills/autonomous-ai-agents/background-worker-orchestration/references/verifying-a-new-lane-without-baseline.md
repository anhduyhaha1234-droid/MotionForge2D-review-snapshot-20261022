# Verifying a NEW lane that has no before-baseline

Measured 2026-09-24 (Manager round: a brand-new `MF-DEMO-E2E` task whose write-set was an **empty**
directory at dispatch time). The standard post-writer guard needs a pre-dispatch manifest; a new lane
has none. This file is the substitute recipe, plus two harness bugs that made the first two attempts
report a green that proved nothing.

## 1. What breaks when the write-set is empty at capture

`capture_lane_writeset.py <LANE>` enumerates the lane's globs and drives `write_set_guard.py capture`.
For a NEW task the globs match **0 files**, so it prints `NO FILES IN WRITE-SET` and writes **no
manifest**. Later:

```
python tools/guard_after_worker.py DEMO
FileNotFoundError: ...\manager\writesets\writeset-DEMO.json
```

The guard does not degrade gracefully — it dies. Treat "guard crashed on a missing manifest" as
*expected for a new lane*, not as lane drift, and switch to the recipe below instead of weakening the
guard. Also: `capture_lane_writeset.py` may be a **copied** tool, and copies often carry the previous
run's hard-coded pin table — pins that do not match the current prompt show as `False` for every tree
and read like broad drift (see the sweep rule in `duplicate-session-and-dispatch-chains.md` §4).

Same family: the guard needs its baseline file to exist in the **current** run root
(`manager/audit/preflight_trees.json`). A fresh run root has none until the preflight generator is run
there, so run it (and refresh its pin table from the current prompt) **before the first guard call**.

## 2. The recipe that did verify a new lane

Three independent checks, all runnable from the Manager session:

1. **The lane's own manifest, verified against disk.** The worker pinned its artefacts in a file of
   its choosing (`DEMO_MANIFEST.json`). Read it, **print its schema first**, then re-hash every
   `sha256` leaf whose sibling is a path and compare. Measured: `ok=68 bad=0` across
   cast/ref/source/shot entries.
2. **Window mtime sweep.** Enumerate files under the trees that must NOT change and report those with
   an mtime inside `[dispatch, receipt-end]`. Measured: 13 hits, all inside the *live* other lane's own
   allowlist → expected, not a violation. Report the count and the attribution, never a bare number.
3. **Tree pins.** For every pinned tree, assert `HEAD == expected` **and** `porcelain == expected_dirty`
   (MAIN keeps its pre-existing dirty count; a lane that legitimately advanced is compared to the new
   value). Measured: 8/8 trees exact.

Only after those three may the round be called manager-verified — and the note must say the standard
before/after guard was **not** applicable, with the reason (empty write-set at capture).

## 3. Pitfall: a verifier that compares ZERO items will still print PASS

My first manifest verifier guessed the key names (`files` / `artifacts` / `sha256`) and reported:

```
[1] manifest-pinned files checked=0 matched=0
...
MANIFEST_VERIFY: PASS
```

The real schema was `artefacts` + per-entry `sha256`/`path`, so **nothing was compared** and the run
was green for the wrong reason — the same failure class as a blanket `0/0 corrupted` or `194/194
mismatch` result. Rules:

- Print the schema (`TOP-LEVEL KEYS: [...]`) and one full sample entry **before** interpreting counts.
- Make the verifier **fail loudly when `checked == 0`**: a check that examined nothing must never
  report PASS. Assert `checked > 0` as part of the same gate.
- Prefer structure-agnostic extraction: walk the JSON, treat any 64-hex string as a digest, and pair
  it with the nearest path-looking sibling — then report both `ok` and `bad` counts.

## 4. Enforcing the concurrent-stream cap without losing work

When a new lane is dispatched into a wave that is already at its evidence-based cap (3 upstream
streams), the count must be brought back down. Measured procedure, zero data loss:

1. **Identify every live chain by its cmdline**, not by start order:
   `Get-CimInstance Win32_Process | ? { $_.Name -eq 'hermes.exe' -and $_.CommandLine -like 'hermes -z*' }`
   then read the first ~190 chars of each `CommandLine` to map chain → packet → task.
2. **Stop the newest / least-invested chain** (seconds-old, no writes yet), leaf → root, exact pids,
   and prove zero collateral with the `python.exe` pid-set diff (see the sibling reference).
3. **Re-queue, do not discard:** the packet is already written and hashed, so re-dispatch needs no new
   authoring — only a slot. Record the row as `STOPPED_OVER_CAP` with the reason and the pid evidence,
   never as a task result, and say plainly which lane it will resume as.
4. Report the live-chain count before and after (`3`) so the cap is a measurement, not a claim.
