# Restart hygiene & freshness proofs — stop files, epoch cutoffs, pyc, isolation (2026-10-12, R6 preflight)

Four measured failure classes when a NEW round restarts machinery from a CLOSED round.
All are about proving what is fresh vs stale without rewriting history.

## 1. Stop-file daemons: the previous round's STOP kills the restarted monitor

A monitor loop that exits when `<dir>/HEARTBEAT_STOP` exists will exit **immediately** on
the new round if the old stop file is still on disk (measured: the restarted heartbeat died
before writing a single tick, message `STOP file present -> exit`, twice). The new round's
dispatch was already live — the monitor was silently absent until someone noticed the
heartbeat file's last row still showed the PREVIOUS invocation.

Recipe:
1. Before restarting any stop-file-controlled daemon, rename the old file to
   `<name>.<round>-closed` — preserves the bytes as evidence (it documents WHY the old
   round stopped) while unblocking the new loop.
2. After restart, verify the FIRST tick within ~2 intervals, and check the tick's
   `invocation` resolves to the NEW dispatch row (not the previous one).

## 2. Same-second read race (benign — check timestamps before "debugging")

A monitor tick that reads a shared ledger microseconds BEFORE the new dispatch row lands
reports the PREVIOUS invocation's closed state (open=False) for exactly one tick. Measured
gap: dispatch row `at_utc` 21:30:40.372Z, tick read at 21:30:40.473Z — still saw the old
row. Not a defect; next tick resolves. Triage rule: when a monitor shows a stale/wrong
invocation, compare the row's `at_utc` with the tick time FIRST; only investigate if the
tick is later than the row and still wrong.

## 3. Epoch cutoffs MUST be tz-aware — a UTC string through mktime silently shifts the window

`time.mktime(time.strptime("2026-10-11 17:20:32", ...))` parses as LOCAL time. A cutoff
intended as 17:20 UTC became 10:20 UTC (+07 host) — the "modified since" scan then flagged
a dozen R4-era files as fresh writes and produced a phantom concurrent-writer alarm.
Always: `datetime(y, m, d, H, M, S, tzinfo=timezone.utc).timestamp()`; print the cutoff
epoch in the proof JSON so a reviewer can audit it. (Same family as the `find -newermt`
MSYS shift — this is the Python-side variant, and it bit twice in consecutive rounds.)

## 4. Isolation proof for a new round (what "no stray writes" looks like on disk)

Pattern measured green (20 expected / 0 unexpected):
- Walk every writable tree; collect files with `mtime > round_start_epoch`.
- Classify against an EXPECTED-PREFIX list (new evidence root, new packets/receipts/logs,
  the bounded-patched files, and **by-design tool caches** — `__pycache__`).
- Pass = `unexpected == 0` AND `new files in the frozen previous-round evidence dir == 0`.
- Prove cache legitimacy instead of flagging it: `py_compile` (and imports without `-B`)
  write `.pyc` caches; read the pyc header — `magic(4) + flags(4) + src_mtime(4) +
  src_size(4)` — and compare with `os.stat(source).st_mtime / st_size`. Equal mtime+size =
  the cache was compiled from the CURRENT patched source (measured: both match after a
  CRLF-preserving patch).
- Keep the proof JSON in the NEW round's evidence root; it is the "output isolation"
  artifact a guarded-continuation grant is conditioned on.

## 5. Newline-safe bounded patchers (CRLF files) — two working shapes

Both measured this round (files: one pure-CRLF, one pure-LF, in the same batch):
- Shape A: read raw (`newline=""`), convert the anchor strings to the file's newline
  convention (`old.replace("\n", "\r\n")`), replace, write raw (`newline=""`).
- Shape B: read universal (`newline=None`, text has `\n`), write with
  `newline="\r\n"` so every line is re-emitted CRLF.
- ALWAYS print before/after sha256 + byte count + CRLF count and assert both moved ONLY
  in the intended direction; then `py_compile` both files.
- If a fuzzy text-patch wrecks your own scratch script mid-edit (stray fragment, wrong
  indent), do NOT stack more patches — rewrite the scratch file wholesale with
  `write_file` and re-run. Scratch scripts are disposable; evidence files are not.
