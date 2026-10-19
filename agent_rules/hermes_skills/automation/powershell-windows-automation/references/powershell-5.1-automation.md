# PS 5.1 automation — debugging transcript (quality-baseline runner build)

Session: MotionForge2D S00-T02 (quality baseline runner). The runner had to
execute 7 gates sequentially, capture per-gate stdout/stderr/exit/duration,
continue after failures, and write JSON + logs under an output dir.

## Trap-by-trap record (each with exact symptom → fix)

### 1. `ProcessStartInfo.ArgumentList` does not exist on PS 5.1

- Symptom: `You cannot call a method on a null-valued expression` at
  `$psi.ArgumentList.Add(...)`.
- Root cause: `ArgumentList` is .NET Core / PS 7+; Windows PowerShell 5.1 gives
  `$null`. Verified with `$psi.ArgumentList -eq $null` → True.
- Fix: build a command-line string with a quoting helper and assign
  `$psi.Arguments = $argString`.

### 2. Function parameter named `$Args` silently shadows the automatic variable

- Symptom: `python --version` appeared to launch the interactive REPL
  (banner + `>>>`), `node --version` printed nothing, npm failed to find its
  module — ALL child invocations lost their arguments.
- Root cause: in PS 5.1 a `param([string[]]$Args)` collides with the automatic
  `$args` array; the parameter is shadowed and receives nothing.
- Fix: rename to `$ArgList`. (Isolated test: `Test-Fn -Arguments @('-m', $m)`
  worked fine in isolation, which made the collision hard to spot — the helper
  was only broken when called from the real script.)

### 3. `-and` at end of line + backtick continuation

- Symptom: `A parameter cannot be found that matches parameter name 'and'`
  at the multi-line boolean expression.
- Root cause: PS 5.1 does not continue an expression after a line-ending
  binary operator; it parses `and` as a new statement's parameter.
- Fix: put the operator at the START of the next line with backticks:
  `$ok = (Test-Path A) \` + newline + `    -and (Test-Path B)`.

### 4. npm/npx as relative `.cmd` names fail under ProcessStartInfo

- Symptom: gates invoking `npx.cmd`/`npm.cmd` exited 1 in ~0.09s with
  `Error: Cannot find module '<repo>\node_modules\npm\bin\npm-prefix.js'`
  (npm resolved its prefix against the WRONG cwd).
- Root cause: with `UseShellExecute=$false`, a bare `.cmd` name is not
  resolved from PATH the way a shell would; the child cmd.exe loses the
  intended working-directory context.
- Fix: resolve the absolute path once and reuse:
  `$npmCmd = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source`.
  Verified: `FileName='C:\Program Files\nodejs\npx.cmd'` +
  `WorkingDirectory=frontend` → exit 0.

### 5. `Set-Content -Encoding utf8` writes a BOM (PS 5.1)

- Symptom: `json.load(...)` raised `Unexpected UTF-8 BOM`.
- Fix: `[System.IO.File]::WriteAllText($path, $json, (New-Object System.Text.UTF8Encoding($false)))`.

### 6. stdout/stderr sequential reads can deadlock

- Fix: start `ReadToEndAsync()` for BOTH streams before `WaitForExit()`,
  then read `.Result` after exit.

### 7. Exit code capture through a pipe is wrong

- `powershell ... | tail; echo $?` reports tail's exit. Run without pipe
  (`> /dev/null 2>&1; echo $?`) or use `$LASTEXITCODE` from a non-piped
  invocation.

## Reusable runner skeleton (7-gate, continue-on-fail)

- Repo root from script location:
  `$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)`
- Output: `$outDir = Join-Path $repoRoot 'output\quality-baseline'`; per-run
  dir `Get-Date -Format 'yyyyMMdd-HHmmss'`.
- Per-gate record dict: name, command, status (PASS/FAIL/SKIPPED-PREFLIGHT_BLOCKED),
  exit_code, duration_seconds, log_path. `Invoke-Gate` NEVER throws; on start
  failure or timeout it records FAIL with error string and continues.
- Overall exit: 0 only if all required gates PASS; 1 if any FAIL; 2 if
  preflight blocked. Summary JSON written incrementally AND at the end.
- Preflight (gate 1): tool versions via `Get-ToolVersion` (stdout+stderr
  concatenated — `python --version` writes to stderr on Windows), frontend
  deps existence checks (`Test-Path node_modules/.bin/tsc` etc.), never
  auto-install.
- Status semantics: if preflight fails, later gates are recorded as
  `SKIPPED/PREFLIGHT_BLOCKED` — they are STILL recorded (7 records always),
  which is what the PM contract required.

## Validation pattern that caught the regression

- `certutil -hashfile channels.json SHA256` before/after two targeted test
  runs — hash change after ONE run proved tests polluted production data.
- Per-file `sha256sum presets/characters/*.png | sort -k2` snapshot before,
  `diff` after — content-level proof of no-mutation (file-list equality alone
  is insufficient; a write-capable call can be a no-op only because files
  already exist).
