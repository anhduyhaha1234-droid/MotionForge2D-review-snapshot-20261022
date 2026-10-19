# Incident evidence preservation + guard extension (frozen-file drift)

Context: a reviewer found that N frozen evidence files from a PRIOR round had changed bytes
since that round's baseline (here: 16/21 drifted paths — 1 report + 15 receipts — rewritten
by a regression rerun of an OLD test harness whose code hardcodes the old output paths).
A stale nested-manifest entry was found at the same time (record refreshed after manifest).

## Preservation procedure (do exactly this, once)

1. Take the reviewer's measured drift list as authoritative history: for each path record
   `before` and `after` (sha256/bytes/mtime) — copy their probe JSON verbatim into the new
   round's evidence tree (`incident_reconcile/INCIDENT_<X>.json`), plus a summary split of
   "frozen evidence" vs "paths the current scope legitimately allows".
2. Re-hash each drifted path NOW and record `current == after?` (proves nothing changed
   again between review and your preflight).
3. COPY the current bytes of every affected file into the new tree
   (`preserved_bytes/`); also copy the frozen manifest that is stale. Copies are evidence.
4. Append-only reconciliation note (`RECONCILIATION_APPEND.md`): what changed, the measured
   mechanism (no motive attribution), what stays frozen, and the standing policy:
   **no restore / no backdate / no refresh of history to hide a mismatch.**
5. NEVER rewrite the drifted files back, and never "fix" the frozen manifest — the next
   round's manifest must compute hashes AFTER its own final record write.

## Guard extension (the lesson that prevents recurrence)

- Old-round trees that new scripts are TEMPTED to write into must be added to the guard
  baseline explicitly. Examples that bit here: a runner wrote masks/tracks into the PREVIOUS
  revision's directory; therefore the guard now hashes `R4/tracks/**` (3171 files) and
  `R4/masks/**` (3184 files) as protected.
- Guard baseline = sha256/bytes per file into JSONL + summary counts; re-verify after each
  worker invocation (all-files re-hash is fine at these sizes: ~6k files, seconds).
- Frozen-file check: re-hash a small explicit set (master videos, terminal records, source,
  style, cast board) before AND after each round.

## Isolation-proof scan (prove only-expected writes)

- Enumerate EXPECTED write-set prefixes (new evidence tree, new packets/receipts/logs,
  registry/ledger, patched tools/tests) and walk the task+manager trees for every file with
  mtime > a cutoff; split into expected vs unexpected; also assert the PREVIOUS round's
  evidence dir gained zero new files.
- TIMEZONE TRAP (measured): building the cutoff with `time.mktime(strptime('...17:20:32'))`
  parses the string as LOCAL time; mixing a UTC hour into it flags hours of pre-existing
  files. Use `datetime(..., tzinfo=timezone.utc).timestamp()` and print the cutoff epoch.
- `py_compile`/import checks create `__pycache__/*.pyc` under tools/tests — they will show
  as "unexpected" unless (a) listed as expected cache paths and (b) verified fresh by
  reading the pyc header (source mtime+size ints at bytes 8..16) against the current source.
  A fresh pyc of the patched source is legitimate; note it, don't fight it.

## CRLF-safe bounded patch recipe (used for registry/guard/contract edits)

- Detect newline style first: `b"\r\n" in raw`. Then ONE of:
  - read with `newline=None` (universal -> `\n` in text) and WRITE with
    `newline=chr(13)+chr(10)` so the file stays CRLF; or
  - read raw (`newline=""`) and convert ANCHORS: `anchor.replace("\n", "\r\n")` before
    counting. (Reading raw but using `\n` anchors gives count=0 assert — symptom.)
- Always: assert `text.count(old) == 1` (preimage), write tmp + `os.replace`, print
  before/after sha256 + byte delta + CRLF counts, and re-parse the JSON after the write.
- If a scratch script gets mangled by chained patches (e.g. leftover fragment ->
  IndentationError), stop patching it — rewrite the scratch file cleanly with write_file;
  it's your own scratch, whole-file rewrite is allowed.
