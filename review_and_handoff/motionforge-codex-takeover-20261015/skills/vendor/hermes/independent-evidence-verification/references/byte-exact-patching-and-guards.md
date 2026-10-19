# Byte-exact patching, escape handling, and change-cut guards (measured 2026-10-11/12)

Context: patching live manager-tool files and CRLF JSON registries from Python scripts with
anchored replacements. Three ways this destroys a file, one way to make it safe, and the
verification order that catches the rest.

## 1. `open(path, "w", ...)` TRUNCATES BEFORE it validates — then raises

Measured: `open(F, "w", encoding="utf-8", newline="\r\n")` — where the value had arrived as
doubled backslashes (2 chars `\` `\` + r...) — raised `ValueError: illegal newline value`.
By then the O_TRUNC in `open()` had ALREADY zeroed the target file. A live tool file went to
0 bytes; recovery was only possible from the PREIMAGE snapshot taken minutes earlier.

RULE: never open a patch target with mode `"w"` directly. Write to `<target>.patched.tmp`,
then `os.replace(tmp, target)`. Keep the preimage copy + sha256 snapshot from BEFORE the
patch round; `cp preimages/<f> target && sha256sum` is a full recovery.

## 2. Escape mangling — know which layer eats backslashes

- `write_file` writes backslashes VERBATIM as typed in the tool payload: `newline="\\r\\n"`
  lands in the file as TWO backslashes per escape → Python parses the value as 4 literal
  chars → triggers bug #1 above (and any assert comparing against real CRLF fails).
- The `patch` tool's `new_string` containing `\r\n` decodes to REAL CRLF characters inside
  the file — which terminates string literals and produces `SyntaxError` blocks mid-file.
- SAFE SENTINELS — build every patch/generator script with `BS = chr(92)`, `Q = '"'`,
  `CRLF = chr(13) + chr(10)` and assemble escape-sensitive fragments from those. Never type
  raw backslash runs inside a tool payload (this is the same family as the heredoc-mangling
  rule — payloads pass through at least one unescape layer before reaching disk).
- If a file does get mangled, do NOT hand-repair: restore from preimage, fix the GENERATOR
  (via a small chr-based fixer script), re-run it, and re-verify.

## 3. CRLF JSON registries: universal-read, normalize-write, assert

- Read with `newline=None` (universal → `\n` only), do anchored replacements with plain
  `\n` patterns, write back with `newline='\r\n'`, then assert
  `data.count(b"\r\n") == data.count(b"\n")` and that the text still JSON-parses.
- Multi-line anchors must match the ACTUAL closing punctuation: a `    ],` anchor failed
  because that list was the file's LAST key (bytes showed `    ]` followed by `  },` — no
  comma). Dump `repr(bytes[i-80:i+200])` around the anchor before fixing the pattern.
- Assert `count(old) == 1` for EVERY replacement before any write; on failure nothing is
  written (fail-before-mutate). Record before/after sha256 + bytes + line counts + the
  replacement list into an evidence JSON.

## 4. Region-splice beats retyping large blocks

For "replace this whole function/region" edits where retyping risks subtle escape damage:
locate `start_marker` / `end_marker` at runtime with `.find()`, `assert` sanity tokens inside
the slice (`"lease_acquire" in region`), then `text[:s] + NEW + text[e:]`. No large old/new
string pair to get wrong; the new block is authored once, plainly.

## 5. Patching live consumers means patching their test fixtures too

When the consumer gets stricter (e.g. binding validation against the dispatch row), old
fixtures that were "conveniently sloppy" (ledger rows missing owner/run/packet fields) start
failing. Patch the FIXTURE to be binding-complete — read the values FROM the actual receipt
at fixture-build time so they can't drift. Deliverable = old suite still green PLUS the new
suite (measured: 70/70 regression + 51/51 new).

## 6. "Unexpected change" lists must use the right epoch domain

`time.mktime(time.strptime("2026-10-11 17:20:32", ...))` parses LOCAL time; the events being
compared (UTC log/ledger timestamps) live in UTC. Result: a "changed since takeover" report
built with a UTC wall-clock string flagged 62 files from BEFORE the round. Fix:
`datetime(..., tzinfo=timezone.utc).timestamp()`. Derive every cutoff from the SAME clock as
the evidence, print the cutoff next to the list, and ANNOTATE (don't silently rewrite) any
list produced with a wrong cut — the reviewer needs to know which measurements were redone.

## 7. Verification order that caught real bugs this round

1. `py_compile.compile(doraise=True)` the patched file BEFORE writing evidence/logs — a
   crash mid-script must leave previous bytes + no half-written record.
2. Import-smoke the patched module in a FRESH process (probe shapes with mocks) before the
   long suite; smoke each fix within seconds of applying it.
3. Run the new suite, then the OLD suite as regression; report both counts.
4. Final gate: re-hash every patched file vs its recorded post-hash, re-hash the frozen set,
   confirm process liveness (pid + create_time) and log growth in a 10 s window before
   reporting "running".

## 8. Related traps re-confirmed this round

- A patch tool edit that "looks local" can still corrupt when the payload's escaped chars
  decode to control characters — grep/print the edited region after EVERY edit (same family
  as the CRLF-deletion and table-row pitfalls).
- An abandoned scratch script that half-applied (write happened, compile failed) leaves the
  target in a broken-but-persisted state: restore-from-preimage is step one, fix the script
  is step two, NEVER "patch the broken file back" by hand.
- A read-only DB audit needs `file:...?mode=ro` + `PRAGMA query_only=1`; in the Hermes
  state.db the sessions table key is `id` (not `session_id`), and message timestamps are
  epoch floats — convert with `datetime.fromtimestamp(e, timezone.utc)` before comparing
  against UTC event times. (A same-day audit compared epoch floats against
  `datetime('now','-36 hours')` STRINGS: in SQLite a number always compares less than a
  string, so the "recent sessions" query silently returned nothing.)
