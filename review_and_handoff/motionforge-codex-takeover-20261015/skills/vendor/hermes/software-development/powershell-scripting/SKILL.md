---
name: powershell-scripting
description: "Use when scripting PowerShell on Windows (PS 5.1 pitfalls)."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [powershell, windows, automation, scripting, process-capture]
---

# PowerShell Scripting on Windows

## Overview
Robust PowerShell scripts that run external tools, capture per-command stdout/stderr/exit code/duration, continue after failures, and emit machine-readable reports. Verified on Windows PowerShell 5.1 — the default on Windows 10 (`pwsh`/PS7 is often NOT installed).

## Step 0: Check the PS version first
`$PSVersionTable.PSVersion`. 5.1 vs 7+ differ significantly:
- **5.1** (Windows PowerShell, .NET Framework): NO `ProcessStartInfo.ArgumentList`; `Set-Content -Encoding utf8` writes a BOM; strict parse rules on line continuation; `$Args` is an automatic variable.
- **7+** (pwsh, .NET Core): has `ArgumentList`; utf8 default is BOM-less.

## PS 5.1 pitfalls (each cost real debugging time)
1. **`$psi.ArgumentList` does NOT exist on 5.1** — `.Add()` fails with "You cannot call a method on a null-valued expression". Use `$psi.Arguments = <quoted string>` built by a quoting helper.
2. **A parameter named `$Args` collides with the automatic `$args` variable** — the parameter is silently shadowed and arguments are DROPPED (e.g. `python --version` runs the REPL instead of printing the version). Rename to `$ArgList`.
3. **`-and`/`-or` at the END of a continued line** → `A parameter cannot be found that matches parameter name 'and'`. Put the operator at the START of the next line with backtick continuation:
   ```powershell
   $ok = (Test-Path $a) `
       -and (Test-Path $b)
   ```
4. **`Set-Content -Encoding utf8` writes a BOM** — Python `json.load` then fails with "Unexpected UTF-8 BOM". Write BOM-free:
   ```powershell
   $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
   [System.IO.File]::WriteAllText($path, $json, $utf8NoBom)
   ```
5. **Sequential `ReadToEnd()` on stdout then stderr can deadlock** when a pipe buffer fills. Read BOTH via `$p.StandardOutput.ReadToEndAsync()` / `$p.StandardError.ReadToEndAsync()` BEFORE `WaitForExit()`, then use `.Result` after exit.
6. **`.cmd` batch shims (npm.cmd, npx.cmd) fail under ProcessStartInfo with a bare name** — "The system cannot find the file specified", or npm's MODULE_NOT_FOUND resolving the wrong prefix (it resolves from cwd, which can be wrong). Resolve the absolute path and use THAT as FileName:
   ```powershell
   $npmCmd = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
   if (-not $npmCmd) { $npmCmd = 'npm.cmd' }
   ```
   Also always set `$psi.WorkingDirectory` explicitly.
7. **`$LASTEXITCODE` is lost through a pipeline** (e.g. `... | tail` shows the pipe's exit code). Capture without piping: run the script, then read `$LASTEXITCODE` (or `echo $?`) immediately.
8. **`Tee-Object` / `Out-File` write UTF-16LE on Windows PowerShell 5.1** — log files become NUL-padded garbage when read from bash. Decode with `tr -d '\0'` or `iconv -f UTF-16LE -t UTF-8`. If a downstream consumer (preview pane, grep, tail) needs the log, generate a UTF-8 tail file alongside it.
9. **Syntax-check a .ps1 WITHOUT executing it** (safe pre-flight before launching a runner):
   ```powershell
   [System.Management.Automation.Language.Parser]::ParseFile($path,[ref]$null,[ref]$errs)
   if ($errs.Count -eq 0) { "SYNTAX: OK" } else { $errs | % { "ERR: $($_.Message) @$($_.Extent.StartLineNumber)" } }
   ```
10. **`$pid` is a READ-ONLY automatic variable** — `foreach ($pid in @(1,2,3)) { … }` fails with
    `Cannot overwrite variable PID because it is read-only or constant` and **the loop body never runs**,
    so a kill/scan script reports success while doing nothing. Same family as `$Args`/`$args` (item 2).
    Use `$procId` (or `$targetPid`). Also avoid `$input`, `$error`, `$host`, `$home`, `$args`, `$matches`,
    `$PSItem` as loop/parameter names.
    ```powershell
    foreach ($procId in @(33592, 34280, 35952)) {
      try   { Stop-Process -Id $procId -Force -ErrorAction Stop; "stopped $procId" }
      catch { "already gone $procId" }
    }
    ```

## Argument quoting helper (5.1-safe)
```powershell
function ConvertTo-ArgumentString {
    param([string[]]$ArgList)
    $parts = foreach ($a in $ArgList) {
        if ($a -match '[\s"]') { '"' + ($a -replace '"', '\"') + '"' } else { $a }
    }
    return ($parts -join ' ')
}
```

## Reliable per-command capture pattern (multi-gate runners)
- `System.Diagnostics.ProcessStartInfo` with `UseShellExecute=$false`, `RedirectStandardOutput=$true`, `RedirectStandardError=$true`, `CreateNoWindow=$true`, explicit `WorkingDirectory`.
- Wrap `Start()` in try/catch; record start-failure as a FAIL record (exit -1) — never throw the whole script.
- Timeout: `$proc.WaitForExit($TimeoutSeconds * 1000)` then `Kill()` on timeout; record "timed out".
- Write per-command `.log` (stdout) and `.err.log` (stderr) with COMMAND / WORKDIR / EXIT CODE headers.
- Keep three distinct statuses: `PASS` (0), `FAIL` (non-zero), `SKIPPED/PREFLIGHT_BLOCKED` (dependency missing).

## Exit-code contract for multi-gate runners
- `0` = all required gates pass; `1` = any required gate FAILs; `2` = preflight blocked.
- ALWAYS write the full report even when exiting non-zero — failures are baseline data, not script bugs.
- In 5.1, `exit N` in a script sets `$LASTEXITCODE` for the caller.

## Repo-root resolution (cwd-independent)
```powershell
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot  = Split-Path -Parent $scriptDir   # scripts/ -> repo root
```
Prove it by running the script from a DIFFERENT cwd (e.g. `C:\Users\<user>`).

## Process command-line scanning (model/worker/process audits)
Audit which processes run a given model/flag (e.g. prove no old-model worker
still runs after a "switch everything to X" instruction) — write a .ps1 FILE
and run `powershell -ExecutionPolicy Bypass -File <path>`:

```powershell
$ErrorActionPreference = 'SilentlyContinue'
$procs = Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -match 'glm|deepseek-v4-flash-vision-exp|hermes --resume' }
foreach ($p in $procs) {
  $m = [regex]::Match($p.CommandLine, '(?i)(BAI/[^\s"]+|comboBAI|glm[^\s"]*)')
  "{0} | {1} | {2}" -f $p.ProcessId, $m.Value, $p.CommandLine.Substring(0, [Math]::Min(150, $p.CommandLine.Length))
}
"---DONE---"
```

Pitfalls (each cost a run):
- **Inline `powershell -Command "..."` from bash**: the Agent hardline parser
  blocks `wmic ... | grep`-style commands, and bash swallows `$_` / quotes in
  `-Command`. Always a `.ps1` + `-File`.
- Regex with a single-quote char class `[^\s"']` breaks INSIDE a single-quoted
  PS string (`Missing ')' in method call`). Drop the quote from the class or
  use double-quoted regex.
- `Where-Object` on `CommandLine` can match the audit command itself (its
  .ps1 path contains the pattern) — filter out the current process id or
  accept a noise line and subtract it.

### PID-scoped stop with a measured zero-collateral proof

When you must stop a process *chain* you launched (a stale launcher, a duplicate worker), never use
`taskkill /T`, never a name/port-wide kill. Stop the exact pids **leaf → root, one `Stop-Process -Id`
per call**, and prove no collateral damage by diffing the pid set of an interpreter you must not kill:

```powershell
$before = (Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' } |
           Select-Object -ExpandProperty ProcessId)
foreach ($procId in @(<leaf>, <middle>, <root>)) {   # $pid is reserved -> use $procId
  try   { Stop-Process -Id $procId -Force -ErrorAction Stop; "stopped $procId" }
  catch { "already gone $procId" }
}
Start-Sleep -Seconds 3
$after = (Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' } |
          Select-Object -ExpandProperty ProcessId)
"python.exe before=$($before.Count) after=$($after.Count)"
"pids_gone=" + (($before | Where-Object { $_ -notin $after }) -join ',')
```

`pids_gone` must equal exactly the target set — anything else is collateral damage and must be reported,
not hidden. Record the counts plus the surviving process list as the evidence (a claim of "no collateral"
that is not a pid-set diff is not a measurement). Verify the whole chain by PPID first
(`Get-CimInstance Win32_Process | Select ProcessId,ParentProcessId,CommandLine`) so you stop the right
pids when several workers share a launcher name.

## Template
`templates/multi-gate-runner.ps1` — copy-and-adapt skeleton for a multi-gate quality runner with per-gate capture, continue-on-fail, and the exit-code contract (proven in MotionForge2D S00-T02).

## Verification checklist
- [ ] `$PSVersionTable.PSVersion` known; 5.1-specific code used deliberately
- [ ] Script runs from repo root AND another cwd
- [ ] Exit code captured without a pipe
- [ ] JSON artifacts parse cleanly (no BOM) — validate with `python -c "import json; json.load(open(<path>))"`
- [ ] Generated artifacts git-ignored — `git check-ignore <path>` echoes the path
- [ ] No absolute machine paths in TRACKED docs (only in git-ignored run logs)
