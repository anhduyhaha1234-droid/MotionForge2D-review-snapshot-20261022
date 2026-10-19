# Bounded patch scripts on Windows: truncation, CRLF, and escape traps

Measured 2026-10-11/12 while patching harness files under strict write-set discipline
(preimage required, patch-only for existing files). These are the traps that destroyed or
corrupted files during a real session, and the patterns that fixed them.

## The truncation trap (file destroyed in one tool call)

`open(path, "w", newline=BAD)` raises `ValueError: illegal newline value` — but the O_TRUNC
open already ran: the target file is truncated to 0 bytes before you see the error.
Measured: a 13,635-byte tool file went to 0 bytes from a single failed call. Recovery worked
ONLY because a preimage snapshot had been taken first.

RULES:
1. In any patch script, never open the target directly for writing. Write
   `<name>.patched.tmp` then `os.replace(tmp, target)`.
2. Snapshot the preimage FIRST — bytes + sha256 + line count + mtime into an evidence dir;
   verify the snapshot hash against the source; recovery = copy back + hash check.
3. Construct the `newline=` value with `chr(13)+chr(10)` / `chr(10)` — never a literal
   escape sequence in the tool payload (see next section).

## Escape layering (write_file + heredoc + patch tool)

- Text passed through tool payloads and bash heredocs can arrive with backslashes DOUBLED
  (measured: `\\r\\n` reached the script as two literal backslash pairs → the exact
  ValueError above). When a script must EMIT literal backslash sequences (e.g. writing
  Python source containing `"\n"`), build them via `chr(92)` (backslash) and
  `chr(39)`/`chr(34)` (quotes): e.g. `Q + BS + 'n' + Q`.
- A "fixer" script that repairs doubled escapes post-hoc is a valid recovery: locate the
  damaged spots by constructing both the doubled and single patterns with chr() and
  `str.replace` with a count assert. Disclose the fix in the patch log.
- The `patch` tool is a THIRD layer: `\r\n` typed into new_string lands as REAL CR+LF
  characters (silently terminating Python string literals), not the literal two-char
  sequence. After ANY patch call, re-read the edited region; for large multi-line edits
  prefer runtime-located splices instead: find a unique start marker + end marker in the
  text you read, slice, insert a pre-built replacement block, write via the safe path.

## CRLF handling that survives round trips

- Read with `newline=None` (universal → `\n` patterns), write back with explicit
  translation: detect fully-CRLF as `data.count(b"\r\n") == data.count(b"\n")` (nonzero),
  then write with `newline=chr(13)+chr(10)`.
- Anchor exactness bites: a list tail `]` vs `],` (trailing-comma presence) fails the count
  assert silently if you guess. Read raw bytes around the region (`repr(b[i:i+200])`)
  before choosing the anchor; include enough context that the anchor is unique.

## Verification after every write

- Assert `count(old) == 1` (or N) per replacement with a label; abort the whole script on
  mismatch (assert BEFORE mutating, so a later anchor failure can't leave partial edits).
- Verify the postimage: `json.loads` for JSON; `py_compile.compile(..., cfile=<evidence tmp>)`
  for .py; log before/after sha256 + bytes + lines; then run the consumer's own test suite.
- Keep preimage copies of every edited existing file in the evidence dir — they double as
  reviewer artifacts and are the only recovery path when a write goes wrong.
- Reusable implementation: `scripts/safe_bounded_patch.py` (count-asserted replacements,
  auto preimage, CRLF-preserving tmp+os.replace write, hash/bytes/lines log).
