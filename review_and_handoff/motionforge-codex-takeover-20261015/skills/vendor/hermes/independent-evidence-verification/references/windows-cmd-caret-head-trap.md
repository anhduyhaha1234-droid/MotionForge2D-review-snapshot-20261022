# Windows: `subprocess` with `shell=True` runs cmd.exe — `HEAD^` loses its caret

Measured 2026-09-28 (MF-END-06 final gate).

A Python evidence/gate script called
`subprocess.run("git rev-parse HEAD^", shell=True, cwd=root, capture_output=True)`.
On Windows `shell=True` goes through `cmd.exe`, where `^` is the ESCAPE
character: the command degraded to `git rev-parse HEAD`, printed the SAME sha
as HEAD, and the gate reported two false FAILs:

* `parent == base` FAIL — `HEAD~1`-equivalent returned HEAD;
* `changed set == allowlist` FAIL — `git diff --name-only HEAD^` returned empty.

The repo was correct the whole time: the identical commands captured via the
bash (MSYS) terminal tool showed `HEAD^=2d7a328…` and the exact 3-path diff.

## Fix (durable)

Never route git through `shell=True` on Windows. Use argument lists:

```python
subprocess.run(["git", "rev-parse", "HEAD~1"], cwd=root, capture_output=True, text=True)
```

`HEAD~1` also sidesteps caret-shell issues entirely; the args-list is the real
fix because it removes every shell layer.

## Recognise it

A gate that fails ONLY on derived git fields (parent SHA, changed-file set)
while `status --porcelain` / blob checks pass is a shell bug signal — not a
repo defect. Cross-check with the same command typed in bash before accusing a
writer, and disclose the fixed false-FAIL in the gate notes so a reviewer does
not read the crash as a real finding.
