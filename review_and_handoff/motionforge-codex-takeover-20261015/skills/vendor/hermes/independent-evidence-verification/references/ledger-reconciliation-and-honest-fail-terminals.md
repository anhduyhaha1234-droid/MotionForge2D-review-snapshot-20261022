# Reconciling an append-only dispatch ledger, and grading an honest FAIL

> **See also (added 2026-10-01):**
> - `self-referential-gates-and-own-process-false-positives.md` — six false-red classes in a
>   round's OWN machinery: manifests that hash themselves, gates asserting their own outputs,
>   "collateral" checks scoped to the wrong set, liveness checks matching their own argv,
>   `PowerShell .Count` on a single object, frozen counts on append-only files.
> - `declared-vs-enforced-budget-and-superseded-preconditions.md` — ENFORCED vs OBSERVED
>   budget claims, why a false "well under budget" is worse than an honest overrun, and how
>   to record a reviewer-withdrawn precondition (SUPERSEDED, never PASS).

Two round-closing disciplines measured 2026-09-29 (MF2D CMC correction, 6 dispatches
across 3 lanes). Both guard against the same failure: a closing artifact that *reads*
clean while describing something that did not happen.

## 1. Reconcile the ledger against receipts before you trust either one

An append-only dispatch ledger (`ledgers/dispatch-ledger.jsonl`, one `dispatch` row at
launch + one `exit` row at child exit) accumulates three silent defect classes:

| Defect | How it hides |
|---|---|
| Duplicate rows for one round | Backfilling earlier rounds re-appends them; row count still looks plausible |
| A dispatch with no receipt file | A launcher that died **before** writing its receipt leaves a row pointing at nothing |
| Two rounds sharing one receipt name | A re-dispatch of the same task reuses the receipt path, so the first round's identity is overwritten |

Run `scripts/reconcile_dispatch_ledger.py <run_root> [--emit]`. It pairs rows by receipt
path, counts receipt files actually on disk, and prints
`duplicate_dispatch_rows` / `dispatches_missing_receipt` / `not_yet_exited`.

Measured clean result: `rows_total 10, dispatches 6, exits 4, receipt_files_on_disk 6,
duplicate_dispatch_rows {}, dispatches_missing_receipt []`. The two non-exited entries
were the lanes still running — reported, not hidden.

### Do not assert a row exists before reading the ledger back

When writing the reconciliation note, I described a "failed first attempt that was
re-dispatched under the same receipt name" **from memory of the incident**. The ledger
showed no such row: that attempt died at `read_text()` *before* the launcher's ledger
append, so it was never recorded at all. The note claimed a row the evidence did not
contain.

Rule: **derive every sentence of a reconciliation note from the reconciled rows**, then
re-read the emitted file. A near-miss that was never logged belongs in the *incident*
narrative with an explicit "not present in the ledger because the failure preceded the
append" — never in the ledger table.

## 2. An honest FAIL with named red items is the correct deliverable

A lane finished its full chain and its own final gate returned **`FAIL 12/15`**, with the
three red checks named exactly (`export_run_completed`, `export_media_has_audio`,
`demo_audio_stream_present`) — precisely the steps it had not completed. It said so
verbatim: *"trung thực, KHÔNG sửa gate để xanh"*.

That is a **pass at the process level** even though the gate is red:

- The gate's job is to describe state, not to be green. Editing the gate, dropping the
  failing checks, or widening a tolerance so the suite goes green destroys the only
  instrument that was telling the truth.
- A FAIL that names its red items is *more* reviewable than a green that hides a gap —
  the reviewer can route each red item to an owner without re-deriving anything.
- Report the honest FAIL as the headline; put the completed work in a table beside it.
  "FAIL 12/15 (3 export items), everything else measured" beats a vague "partially done".

Corollary — **grade an anomaly informational, not red-against-the-wrong-party.** A lane's
final gate surfaced a remote ref holding its commit that its own ledger proved it did not
push (0 push argv, no upstream configured). The correct grading is an **informational,
non-blocking** check carrying the reflog evidence — the lane *reported* an anomaly it did
not cause, which is good behaviour. Do not paint it red against that lane, and do not
paint it green either. Two-sided honesty: neither accuse the reporter nor launder the
finding.

## 3. Never let `exit 0` stand in for "done" — at either level

Both halves of this round's closing evidence had `exit=0` and were **not** complete:

- the demo lane's launcher returned `exit=0` while its gate was `12/15`;
- two code lanes returned `exit=0` after their **output-token** ceiling cut a `patch` and
  the runtime refused the incomplete tool call
  (see `output-truncation-and-allowlist-grants.md`).

Read the payload, measure the disk, then decide. `exit 0` is a statement about the
process, never about the work.
