# Gates that measure themselves, and checks that match their own process

Measured 2026-10-01 (MotionForge M1-01 correction rounds). **Six separate false-red
classes** in one round's own verification machinery. Every one of them was a *gate bug*,
not a product defect — and each one cost real time because the default reading of a red
row is "the artifact is broken".

> **The governing rule:** when a gate row goes red **on something you yourself just
> wrote**, the first hypothesis is a bug in the gate. Print the raw command output in the
> row detail *before* believing it. A red row naming a file/count/process you created
> seconds ago is a bug signal, not a finding.

## 1. A manifest that hashes itself (or files carrying its own digest)

Symptom: re-verify reports `CHANGED` for one or two entries while every byte is intact.
The offenders were the files that **carry the manifest's own digest**:

- the seal/summary file that *records* `manifest_sha256`, and
- any step-output file written *after* the manifest was built.

Fixes:

1. **Exclude self-referential files BY NAME** in the builder (`EXCLUDE = {...}`), and
   record the exclusion list inside the manifest (`excluded_self_referential`) so a
   reviewer sees why the count is smaller than the tree.
2. **Prove determinism** by running the builder **twice** and comparing the `entries`
   digest — identical output on both runs is the proof the exclusions are sufficient.
3. Then run a **third, read-only** `verify` pass whose only job is to report
   `mismatch` / `unlisted_on_disk`.
4. **Never quote the manifest digest inside a prose document in the same tree.** That
   document is itself manifested, so any digest printed in it is stale by construction.
   Point the reader at the verify output file instead of transcribing numbers.

## 2. A gate that asserts artifacts written *after* it runs

Symptom: `FAIL deliverable manager/EVIDENCE_MANIFEST.json` and
`FAIL deliverable manager/FINAL_GATE.txt` — the gate was checking for the two files it
was about to produce.

Fix — fix the **ordering**, not the expectation:

```
STEP 1  gate            -> writes FINAL_GATE.{json,txt}
STEP 2  build manifest  -> the last write into the RUN
STEP 3  verify          -> READ-ONLY; nothing may write into the RUN afterwards
```

Keep the gate's `PRESENT` set to artifacts that exist *before* it runs. Anything the gate
or the manifest produces is asserted by the orchestrator step, never by the gate.

## 3. "Collateral damage" checks must be scoped to the owned set

Symptom: `FAIL no python.exe collateral` on a **clean** cleanup, because the run's own
backend legitimately appears in `lost_pids` (you killed it, on purpose).

```python
owned = {r["pid"] for r in cleanup_report["stopped"]}
collateral = sorted(set(report["python_exe_lost_pids"]) - owned)   # must be []
```

Asserting `lost_pids == []` is asserting an impossible condition. Phrase the row as
*"deaths outside the owned set"* and compare against the owned set.

## 4. Liveness / concurrent-writer checks that match their own process

Two distinct shapes, both producing a **false "a writer is active" alarm**:

**(a) The session id passed inline in the checker's own argv.** A one-liner like
`python -c "... WHERE cmdline LIKE '%<session_id>%' ..."` puts the id into its *own*
command line, so the scan finds itself. Fix: **read the id from a file**
(`manager/tools/owner_session.txt`) so it never appears in any argv, and exclude
`os.getpid()` plus the **ancestor chain**.

**(b) Ancestor shells carrying your command text.** Terminal-tool wrappers show up as
`bash.exe -c source /…/hermes-snap-…`, and a wrapper can contain the very text you are
grepping for. Always exclude self → parent → … (walk ~6 levels) before counting hits.

Corroborate with a second, independent signal before reporting a live writer: per-session
`MAX(messages.timestamp)` from the read-only session DB, which cannot match a process at
all. Measured: process scan `0` matches and worker idle `928.3` minutes agreed —
`ZERO_CONCURRENT_WRITER`.

## 5. `PowerShell .Count` on a single object yields *nothing*, not `0`

`(Get-CimInstance … | Where-Object {...}).Count` returns an **empty string** when the
filter matches exactly one object (no array, no `.Count`). A gate comparing that to `0`
prints an empty `actual=` and reads as FAIL. Use `@(...).Count`, or better, do the count
in a language whose semantics you control (Python/`psutil`).

## 6. Expectations pinned to a literal on an append-only artifact

Symptom: `FAIL usage ledger rows (exp=10 got=12)` — the ledger was *supposed* to grow.

Encode the **invariant**, not the snapshot: `n >= 10 → AT_LEAST_10`, or a row that
asserts append-only-ness (row count never decreases, previously-seen rows still present).
A frozen count on an append-only file fails by construction the moment the round does more
work.

## 7. Preserve every failing raw run; fix gates by editing gates, not numbers

When you repair a gate bug, **keep the pre-fix output in the same evidence tree**
(`T015`, `T019`, `T020`, `T021`, …) and disclose the sequence in the final report — for
each red row: what it said, why the gate was wrong, what the corrected predicate is.
Never regenerate a red artifact in place so the tree reads clean; a reviewer needs to see
which measurements were double-checked and which were bug-fixes rather than findings.

## Measured sequence (one round, for calibration)

| # | Red row | Root cause | Class |
|---|---|---|---|
| 1 | `no worker hermes chat process` (empty actual) | PowerShell `.Count` on a single object | §5 |
| 2 | same row, `actual=1` | checker matched **its own argv** | §4a |
| 3 | `usage ledger rows` exp=10 got=12 | literal vs append-only invariant | §6 |
| 4 | `evidence manifest integrity` got=1 (then 2) | seal file + gate file carry the manifest's digest | §1 |
| 5 | `deliverable EVIDENCE_MANIFEST.json` / `FINAL_GATE.txt` | gate asserted its own outputs | §2 |
| 6 | `no python.exe collateral` | run's own backend counted as collateral | §3 |

Six reds, **zero** product defects. Report them as gate bugs with the fix — do not let
them stand as findings against the artifact.
