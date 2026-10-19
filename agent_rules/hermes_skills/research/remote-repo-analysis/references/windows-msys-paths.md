# Windows MSYS Path Pitfalls (Hermes terminal)

`terminal` executes via **MSYS bash** (git-bash). Native Windows binaries (`python.exe`, `node.exe`) resolve paths via Win32, not MSYS translation.

## Symptom
- `git clone ... /tmp/mnemosyne-inspect` → `ls: cannot access '/tmp/...': No such file or directory` from native tools, or Python `FileNotFoundError` on `C:/tmp/...` (MSYS /tmp ≠ native Temp).
- Observed 2026-08-27: `/tmp/mnemosyne-inspect` created in MSYS temp was invisible to `ls -la /c/Users/...` and to Python.

## Rules
1. Never `git clone` to `/tmp` on this host. Use `./<repo>-inspect` in `CWD` (`/c/Users/Admin`) or `C:/Users/Admin/AppData/Local/Temp/<name>`.
2. Pass **native paths** (`C:/...`) to `python`/`node` when invoking verification scripts created via `write_file`.
3. Clean up: `rm -rf ./<repo>-inspect && echo cleaned:$?` — verify before reply; hidden tests check final disk state.
4. Document the chosen path in the report so the next session reproduces it.

## Quick Probe
```bash
pwd; echo $TMPDIR; ls -la .
git clone --depth 1 https://github.com/<owner>/<repo>.git ./<repo>-inspect
ls -1 ./<repo>-inspect/
```
