# Manager round-restart hygiene — repeated dispatch rounds over one long-lived worker (measured 2026-10-12, MF R6)

Ops that repeat EVERY round of a resumed-worker loop. Each item bit at least once; all fixes
below were executed and verified on disk.

## 1. CRLF-preserving bounded patch (Windows files you must not normalize)

A universal-read patcher + raw write silently CONVERTS a CRLF file to LF; a raw-read patcher
with `\n` anchors silently finds NOTHING (anchor count=0). Detect and adapt:

```python
raw = path.read_bytes()
crlf = b"\r\n" in raw
text = path.read_text(encoding="utf-8", newline="")   # raw: keeps \r\n in the string
# for CRLF files: convert every anchor before counting:
#   old = old.replace("\n", "\r\n"); new = new.replace("\n", "\r\n")
# write back with newline="" and os.replace()
```

Proof after writing: print BEFORE/AFTER sha16 + bytes + `raw.count(b"\r\n")` — a CRLF count
that grew by exactly the number of inserted lines proves nothing was normalized away.

Two observed failure shapes (2026-10, registry file): (a) universal-read anchors PASSED but the
follow-up raw-read attempt got count=0; (b) one botched partial replacement left a fragment and
a SyntaxError — when a patcher script gets mangled mid-edit, REWRITE it clean from the plan
(whole-file, it is your own scratch) instead of patching the patcher. Also: two identical
target strings (e.g. the same output-path literal twice) break a `count==1` assertion — replace
one contiguous 2-line block instead.

## 2. `py_compile` writes .pyc even with `-B` — expect it in isolation scans

`python -B -m py_compile a.py` still emits `__pycache__/a.cpython-3XX.pyc` (py_compile writes by
design; `-B`/`dont_write_bytecode` only affects import). An isolation scan ("files newer than
cutoff → flag unexpected") will flag these two. Keep them, and PROVE freshness from the pyc
header — bytes 8..12 = source mtime (LE u32), 12..16 = source size — equals the current source;
then list `__pycache__` in the expected-prefix set with a comment.

## 3. Packet probe-sim before dispatch (argv-scanned runner probes)

If a monitor/lease probe classifies processes by scanning the LLM child's argv tokens (classic
arm: "interpreter in argv0 AND token basename ends `.py`/.exe/… AND stem matches runner
patterns"), a packet containing script REFERENCES can false-positive — the probe would classify
your own worker as a render runner and block lease release at terminal. Simulate worst case
BEFORE dispatch: split the packet on whitespace, apply the probe's exact predicate to every
token (skip tokens >400 chars or containing newlines), testing both raw tokens and tokens
stripped of backticks/parens/`:NN` suffixes.

Measured: refs like `` `r5_vace.py:89` `` or `` `video_blend` `` are safe (the extension is not
at the token end / the stem lacks `.py`), while a bare `vace_run.py` token WOULD flag. Phrase
all refs as `name.py:LINE` or `name (line N)` and re-run the sim until zero hits.

## 4. Isolation proof = expected-prefix scan, not a raw mtime diff

After each round's Manager-side work, enumerate every file modified since the round cutoff
under BOTH the task tree and the manager tree (epoch cutoff via
`datetime(..., tzinfo=utc).timestamp()` — naive string/mtime comparisons mis-hit timezones),
filter through an EXPLICIT expected-prefix list (this round's evidence tree, packets, receipts,
logs, patched tools/tests, registry, `__pycache__`), and report `unexpected == 0` + per-dir
counts + `new_files_in_previous_evidence_dir == 0`. Keep the JSON in the round's evidence so
the next reviewer re-derives it.

## 5. Control-file succession across rounds

Round-scoped control flags (STOP files, lock sentinels, "closed" markers) written by round N
will silently alter round N+1's tooling — the newest observed: a prior round's heartbeat-STOP
made the next round's monitor exit on its first tick. Before starting any daemon for a new
round, sweep for the prior round's control files; RENAME (never delete) them to
`<NAME>.<round>-closed` and verify the daemon's first fresh output binds to the NEW round
(cross-ref: `independent-evidence-verification/references/monitor-succession-and-lane-terminality.md` §4).
