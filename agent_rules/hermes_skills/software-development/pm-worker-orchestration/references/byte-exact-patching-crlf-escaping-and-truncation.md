# Byte-exact patching of live harness files — CRLF, escape mangling, truncation (measured 2026-10-12, R5 consumer patches)

Extends the "Patching existing consumers" section of
`references/structured-terminal-records-and-consumer-patching.md` with three traps that each
cost a real recovery during the R5 Manager round (4 consumer files patched; one file destroyed
mid-script and restored byte-identical from its preimage). Reusable runner:
`templates/byte-exact-patch-runner.py`.

## 1. `open(dest, "w")` TRUNCATES before it can fail — always tmp + os.replace

Measured: `open(F, "w", encoding="utf-8", newline="...")` raised `ValueError: illegal newline
value` — AND left the destination at **0 bytes**, because the file was already opened with
O_TRUNC before the newline value was validated. Second occurrence within the same round: a
later bad escape produced a SyntaxError AFTER the write, leaving broken bytes on disk (caught
only by the post-write `py_compile` check).

Rules:
- NEVER let a patcher write its output with `open(dest, "w")`. Write
  `dest.with_name(dest.name + ".patched.tmp")`, then `os.replace(tmp, dest)`. A crash then
  leaves the ORIGINAL bytes intact.
- Keep the preimage snapshot + its sha in evidence BEFORE the first patch — it is the
  recovery you will actually use. Prove a restore by re-checking the sha against the
  recorded preimage hash (measured: restore of a 13.6 KB module matched exactly).
- Validate everything BEFORE the write: anchor counts, JSON parse when the target is JSON,
  and (best) `py_compile` of the assembled Python text; then write; then re-verify
  bytes/lines/sha of the postimage.

## 2. Tool-payload escaping mangles literal escapes — build sentinels with chr()

Measured: a patch script authored through `write_file` landed with doubled backslashes where
the emitted file needed single-escape sequences (`newline="\\r\\n"` as a doubled literal
instead of the intended CR LF value); heredoc variants mangled a different way (the
terminal-tool layer unescapes once more before bash sees it).

Rules:
- In ANY script payload that must EMIT escape-bearing literals (CR LF, backslashes, quotes),
  construct them from `chr()`: `CRLF = chr(13) + chr(10)`; `BS = chr(92)`; `Q = '"'`. Zero
  backslash characters in the payload = zero mangling surface.
- After writing a patcher, grep its own source (`grep -n 'newline='`, `repr()` of the tricky
  line) and confirm the intended form is present BEFORE executing. A doubled backslash there
  means: fix the payload first, do not run it.
- `py_compile` the patcher itself before running it; a broken patcher that still opens the
  target for write is how files die.

## 3. CRLF files: read universal, write the ORIGINAL convention

The live registry/consumer files were CRLF (line-ending counts confirmed CRLF == LF count).
Pattern that worked across ~8 replacements in 4 files + 1 JSON registry:

- Read `open(p, "r", encoding="utf-8", newline=None)` → universal newlines give plain `\n`
  in the text → write all (old, new) anchor strings with plain `\n`; NO `\r` in patterns.
- Detect the convention from raw bytes first (`raw.count(bytes([13, 10])) > 0`), then write
  back with `newline=chr(13)+chr(10)` for CRLF (or `newline=""` to preserve LF), and
  post-check the file is uniformly CRLF (`raw.count(b"\r\n") == raw.count(b"\n")`).
- Single-line JSON field patches: anchor on `"key": "value",` including the trailing comma —
  but the LAST array element has NO trailing comma (`]` vs `],`); measured anchor miss from
  assuming the comma. Include the surrounding close bracket in the anchor when unsure.
- After the patch, JSON-parse the result and assert the specific values you intended
  (session id, status strings, appended history entries) before declaring success.

## 4. House pattern the runner enforces

`assert text.count(old) == 1` per anchor (the preimage proof) → replace → optional JSON parse
→ tmp + replace → optional `py_compile` → patch-log JSON {file, anchors, before/after
sha256/bytes/lines, crlf flag, at_utc} into evidence. Dry-run mode validates anchor counts
without writing. Measured good: 4 consumer files + registry across ~8 patches, every
post-check green; preimages needed exactly once (the truncation incident) and restored
byte-identical.
