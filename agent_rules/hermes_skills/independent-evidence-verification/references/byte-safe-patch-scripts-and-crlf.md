# Byte-safe patch scripts: escape traps, truncation, CRLF targets

Measured 2026-10-11/12 while patching 4 live Python tools + a CRLF JSON registry + a CRLF
test suite (MF-DEMO-LONG-01 R5). Every item below is an incident that actually happened,
with the working recipe. Applies whenever you edit EXISTING files via a generated Python
script (`skill_manage write_file` → run) instead of the `patch` tool.

## 1. `write_file` writes your content VERBATIM — never rely on tool-layer escaping

Typing `newline="\r\n"` into a generated script's text does NOT reliably land as a Python
escape sequence; the file received the doubled/different form and the run died with
`ValueError: illegal newline value: \r\n`. Same family as the terminal-heredoc backslash
mangling — the tool layer is not an escaping layer.

**Rule: build every escape-bearing string from sentinels inside the script.**
- `BS = chr(92)` (backslash), `CRLF = chr(13) + chr(10)`, `Q = chr(34)` / `chr(39)` quotes.
- `open(path, "w", encoding="utf-8", newline=CRLF)` — never a literal `"\r\n"` you typed.
- A fixer script that edits ANOTHER script uses the same sentinels for BOTH sides of the
  replacement (`'newline=' + Q + BS + BS + 'r' + BS + BS + 'n' + Q` → `'newline=' + Q + BS + 'r' + BS + 'n' + Q`).
- Direction matters per string class and a blanket "fix escapes" pass WILL break one of them:
  a generator that must EMIT the two-character text `\n` needs DOUBLE backslash in its own
  source; a generator that must emit a real newline needs the single escape or `chr(10)`.
  Measured: an over-eager fixer inverted a `"\n" in t` check into a real newline → the
  TARGET file got an unterminated string literal.

## 2. `open(target, "w")` TRUNCATES before the illegal-newline ValueError surfaces

The same failed run left `tools/invocation_runtime.py` at **0 bytes** — CPython opens the
raw file with O_TRUNC before validating the `newline` argument, so a validation error
still destroyed the target. Recovery worked byte-identically because a preimage snapshot
existed (copy + sha256 manifest taken before patching).

**Rules:**
- Write to `<target>.patched.tmp` (same directory), then `os.replace(tmp, target)` — the
  live target is never opened for writing until everything passed.
- Always snapshot preimages first: copy each target to an evidence dir + record
  sha256/bytes/lines/mtime in a manifest; after restore, verify the sha matches the
  manifest entry before re-running anything.
- Treat a zero-byte/truncated target discovered mid-run as a stop: restore from preimage,
  fix the generator, re-run; disclose the incident in the patch log (no silent re-do).

## 3. CRLF targets: universal-read → assert-count anchors → CRLF-write → post-verify

Working recipe for CRLF files (JSON registry, Python tools, test suites):
1. `open(target, "r", encoding="utf-8", newline=None)` → `\n`-only text; anchors use plain `\n`.
2. One `repl(old, new, label)` helper asserting `text.count(old) == expect` (default 1)
   BEFORE any replacement; collect ALL replacement results into a log. A count of 0 is a
   STOP — read the exact bytes around the region with `repr()` before adjusting the anchor.
   Measured: a pattern ending `"],"` vs the real `"]` (last array element) found 0 occurrences
   only after the assert — the assert is what turns a silent no-op into a diagnosis.
3. For big blocks, SPLICE at runtime-located markers instead of retyping the block:
   `s = text.find(start_marker); e = text.find(end_marker, s); text = text[:s] + NEW_BLOCK + text[e:]`,
   with sanity asserts (`"lease_acquire" in region`) so a wrong marker cannot silently eat code.
4. Write with `open(tmp, "w", encoding="utf-8", newline=CRLF)` + `os.replace`.
5. Post-verify: `after.count(b"\r\n") == after.count(b"\n")` (fully CRLF); `py_compile.compile(..., doraise=True)`
   for `.py`; `json.loads` for `.json`; log before/after sha256 + bytes + lines into evidence.
6. After a JSON rewrite, re-parse AND re-assert the values you changed (`parsed["worker"]["status"]...`)
   — the write is not proof until the semantic check passes.

## 4. The `patch` tool CAN mangle `\r\n` in `new_string` into real newlines

Measured twice: a JSON-array insertion and an `if ... in t` string literal both landed with
REAL line breaks inside string literals → `SyntaxError: unterminated string literal` in the
target. The tool reported success and the diff "looked local".

**Rules:**
- After EVERY `patch` call on an existing file, re-read the edited region (grep/read_file)
  before running anything that depends on it.
- For CRLF-heavy files, or when the replacement text itself needs escape sequences, prefer
  the byte-exact script (sections 1–3) over the patch tool.
- If a patch already mangled a file: fix with a sentinel-based fixer script (section 1),
  never by retrying the same patch call with the same new_string.

## 5. Verify-before-trust ritual for a patch batch

Per batch: (a) preimage snapshot + manifest; (b) dry count-assert pass (all anchors found);
(c) write tmp+replace; (d) compile/parse checks; (e) hash the result and grep for the NEW
markers you introduced (`text.count("reconcile_gpu_leases") == 1`); (f) log
before/after sha + bytes + lines to the evidence dir. Reusable skeleton:
`templates/byte_safe_patch_script.py`.
