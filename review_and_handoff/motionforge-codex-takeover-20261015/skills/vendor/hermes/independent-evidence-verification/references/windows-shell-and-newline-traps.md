# Windows shell + newline traps that falsify a gate

Measured 2026-09-28 (MF-END-07, MotionForge2D delivery wave 13).

## 1. `git rev-parse HEAD^` through `subprocess.run(shell=True)` resolves HEAD itself

A final-gate script computed the commit parent with
`subprocess.run("git rev-parse HEAD^", shell=True, ...)`. On Windows `shell=True`
uses **cmd.exe**, where `^` is the escape character, so the caret was consumed and
the command degenerated to `git rev-parse HEAD` — the gate reported
`[FAIL] commit parent is the packet base` for a commit whose parent was correct all
along (`git log -1 --stat` showed `213832ae…`).

Rules:
- Never derive ancestry through a caret under `shell=True`. Use `git log -1 --format=%P <rev>`
  (caret-free, returns the parent list) or `subprocess.run(["git", "rev-parse", "HEAD~1"], shell=False)`.
- A **single-row** FAIL against a commit you just inspected is a measurement bug signal first:
  print the raw command output next to the verdict before "fixing" the repo (here the evidence
  file itself contained both the wrong `PARENT` and the right parent from `git log`).
- Disclose the near-miss in the report — the reviewer must know which measurements were
  re-derived, and the artifact was never wrong.

## 2. A bounded patch script can inject LF-only lines into a CRLF file

`app/schemas/project_cast.py` is CRLF throughout. A helper patch ran
`text.replace(old, new, 1)` where `new` was a Python literal with `\n` newlines, so 4 lines
landed LF-only in a CRLF file. Nothing failed: the module imported, ruff passed, the tests
passed — only `git` warned (`LF will be replaced by CRLF the next time Git touches it`) and
the guard field `crlf_after` came back `false`.

Rules:
- After every write to an existing file, assert the file's own convention:
  `data.count(b"\r\n") == data.count(b"\n")` (and record it in the patch receipt).
- Fix by an **assert-counted** normalisation, proving content is untouched first:
  `assert len(re.findall(rb"(?<!\r)\n", data)) == n_expected` then
  `after.replace(b"\r\n", b"\n") == before.replace(b"\r\n", b"\n")`.
- Prefer building the replacement with an explicit newline constant (or normalising the whole
  edited text) instead of trusting the copy-pasted literal.
