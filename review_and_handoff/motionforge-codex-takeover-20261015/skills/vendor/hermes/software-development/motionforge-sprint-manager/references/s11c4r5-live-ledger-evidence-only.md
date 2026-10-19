# S11-C4-R5 Live-Ledger Evidence-Only Closure (2026-09-06/07)

Class: **truthful live execution ledger** — remedy for a reconstructed
`commands.jsonl`. R4 packet recorded rows 5–21 with the IDENTICAL start+end
timestamp `2026-09-06T14:33:30+00:00` for sequential gates reporting
172.63s / 14.63s / 385.62s / 172.85s runtimes; raw gate mtimes spanned
14:33:47–15:10:15 UTC while the ledger was last written 15:10:33 UTC; most
raw files held output+exit only (no command/CWD/timestamps/HEAD/roots); and
`guard_preresume.json` (failed missing-script invocation) was absent from the
old ledger while `g11-guard-postpatch.log` held only `GUARD_EXIT:0`. Codex
verdict: P1 evidence-provenance, product+test findings CLOSED, R5 runs fresh
gates through a self-recording ledger with zero repo writes.

## Live runner contract (external-root-only, stdlib python)

The runner — not a later manual summary — executes every gate. Per gate it
must: (1) append+flush a START event BEFORE process launch; (2) record
monotonic seq, exact argv/command (no secrets), absolute CWD, ISO-UTC start,
reviewed HEAD/tree, all DB/basetemp/cache/port/output roots; (3) capture raw
stdout+stderr losslessly to one raw artifact; (4) record the numeric exit from
the actual process; (5) in `finally`, append+flush END event + one final
`commands.jsonl` row with real ISO-UTC end + measured non-negative duration
(`time.perf_counter`); (6) include raw path + SHA-256 + bytes in the final
row; (7) preserve failed attempts exactly like passes, never overwrite a
prior raw file or row. One row per shell action — no batching multiple
actions into one indistinguishable row, no summary label (`matrix 152`)
in place of the exact command, never backfill a START or invent a timestamp.

Row schema (keys actually used): `seq, label, cwd, head, command,
start_utc, end_utc, duration_s, exit, raw_path, sha256, bytes`.
Note: the hash key is `sha256`, not `raw_sha256` — read one real row before
writing any validator, or the validator false-fails on a key-name guess.

## Recorder self-test (gate before the gates)

One harmless command with real duration ≥ 2s (e.g. `sleep 2; echo
SELFTEST_OK`). Require: end > start, duration agrees within clock
tolerance, raw output hash verifies, marker string present. Self-test fail ⇒
stop before closure gates, fix only the external runner. R5 also hit one
pre-ledger runner failure (MSYS `/c/...` CWD → WinError 267, exit 99) during
runner development BEFORE the ledger reset: disclosed in the packet, left no
ledger row, fixed runner re-hashed + self-tested. Pre-ledger failures are
disclosed, not hidden; in-ledger failures keep their rows.

## Mechanical validation (run over the two jsonl files, not by eye)

seq unique/contiguous/monotonic from 0; every final row has exactly one
earlier START + one END; every end ≥ start; every non-trivial gate has
positive duration; rows follow raw artifact mtimes/order within filesystem
tolerance; every raw path exists with matching hash+bytes; every failed
attempt present. R5: 21 rows seq 0–20, 42 events, ALL-OK (T03G 170.72s,
T05A 15.27s, T06 379.00s…).

## Negative controls on the actual committed test (§6 shape)

Helper lives ONLY in the evidence root, hashed before execution. It imports
the committed C4R1 test module and mutates its payload IN MEMORY — never
copies over or writes a repository file. Must prove both: (a) delay caller B
before its thread-id/lock-attempt path + shorten the in-memory marker wait ⇒
committed test raises `AssertionError` on `b_lock_attempted_wait == false`;
(b) corrupt entry_point/version/description in the in-memory final snapshot
keeping names/order ⇒ `AssertionError` on exact snapshot comparison. Helper
exits 0 only if both mutants are rejected. Preserve helper source + exact
command + raw output through the live runner.

## Zero-write guard without a write phase (§7 shape)

R5 has no repository write, so do NOT claim a missing `write_set_guard.py`
invocation passed (that overclaim was part of the R4 P1). Instead capture
path/hash/bytes/lines for the guarded files (C4R1 test, T03G LOG/REPORT, four
protected production files) BEFORE and AFTER all gates and compare exactly:
R5 postimage 7/7 MATCH. Plus `git status --porcelain=v1` empty + HEAD ==
remote ref + tree hash at preflight, mid-ladder, and final audit. Any drift
is terminal; never repair it.

## Version-attribution note (mypy)

R4 recorded 2 `no-any-return` errors in `job_service.py` (lines 542, 727)
under mypy 1.16.1. R5 ran mypy 2.3.0: binding files Success AND
`job_service.py` Success, with the file byte-identical (baseline==postimage
MATCH). Difference is checker version, not source drift. Record checker
version + bytes; never silently upgrade a "known finding" away.

## Same-suffix scaffold disclosure

A second same-suffix directory (`...-171600-R5-live-ledger-final`) existed
beside the final root — an empty scaffold (0 ledger rows, created after the
gates). Left untouched (no delete/rename → no history rewrite) and disclosed
in the packet, which names the single final root. Rule: one final root per
round; strays are disclosed in-packet, never silently removed.
