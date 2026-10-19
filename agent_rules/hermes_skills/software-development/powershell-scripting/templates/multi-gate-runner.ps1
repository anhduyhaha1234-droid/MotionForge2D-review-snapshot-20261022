# Multi-gate runner skeleton (PS 5.1-safe) — proven in MotionForge2D S00-T02

Copy and adapt. Key contract: per-gate capture (command/stdout/stderr/exit/duration/status/log path),
continue-on-fail, exit 0 only if ALL required gates pass, full report even on non-zero exit.

```powershell
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

# Repo root resolution (cwd-independent)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot  = Split-Path -Parent $scriptDir

# Output dir
$outDir = Join-Path $repoRoot 'output\quality-baseline'
$runId  = Get-Date -Format 'yyyyMMdd-HHmmss'
$runDir = Join-Path $outDir $runId
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
$summaryPath = Join-Path $runDir 'summary.json'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)   # PS5.1: Set-Content utf8 writes BOM

$summary = [ordered]@{
    run_id = $runId; started_at = (Get-Date).ToString('o'); repo_root = $repoRoot
    tool_versions = [ordered]@{}; gates = @(); overall = [ordered]@{ status='RUNNING'; exit_code=1 }
}

function Write-Summary {
    [System.IO.File]::WriteAllText($summaryPath, ($summary | ConvertTo-Json -Depth 6), $utf8NoBom)
}

# 5.1-safe quoting: NEVER name the param $Args (automatic variable collision)
function ConvertTo-ArgumentString {
    param([string[]]$ArgList)
    $parts = foreach ($a in $ArgList) {
        if ($a -match '[\s"]') { '"' + ($a -replace '"', '\"') + '"' } else { $a }
    }
    return ($parts -join ' ')
}

# Per-gate runner: never throws; records start-failure and timeout as FAIL
function Invoke-Gate {
    param([string]$Name, [string]$Command, [string]$WorkingDir, [string[]]$Arguments, [int]$TimeoutSeconds = 1800)
    $start = Get-Date
    $safe = $Name -replace '[^A-Za-z0-9_-]', '_'
    $logFile = Join-Path $runDir ($safe + '.log')
    $errFile = Join-Path $runDir ($safe + '.err.log')
    $argString = ConvertTo-ArgumentString $Arguments

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Command
    $psi.Arguments = $argString
    $psi.WorkingDirectory = if ($WorkingDir) { $WorkingDir } else { $repoRoot }
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true

    try { $proc = [System.Diagnostics.Process]::Start($psi) }
    catch {
        $summary.gates += [ordered]@{ name=$Name; command="$Command $argString"; status='FAIL';
            exit_code=-1; duration_seconds=(Get-Date - $start).TotalSeconds; log_path=$logFile;
            error="start failed: $($_.Exception.Message)" }
        Write-Summary; return
    }

    # Read BOTH streams async BEFORE WaitForExit (avoids pipe-buffer deadlock)
    $outTask = $proc.StandardOutput.ReadToEndAsync()
    $errTask = $proc.StandardError.ReadToEndAsync()

    if (-not $proc.WaitForExit($TimeoutSeconds * 1000)) {
        try { $proc.Kill() } catch { }; $proc.WaitForExit()
        $summary.gates += [ordered]@{ name=$Name; command="$Command $argString"; status='FAIL';
            exit_code=-1; duration_seconds=(Get-Date - $start).TotalSeconds; log_path=$logFile;
            error="timed out after ${TimeoutSeconds}s" }
        Write-Summary; return
    }

    $stdout = $outTask.Result; $stderr = $errTask.Result; $code = $proc.ExitCode
    Set-Content -Path $logFile -Value "COMMAND: $Command $argString`r`nWORKDIR: $WorkingDir`r`nEXIT CODE: $code`r`n--- STDOUT ---" -Encoding utf8
    Add-Content -Path $logFile -Value $stdout -Encoding utf8
    Add-Content -Path $errFile -Value "--- STDERR ---" -Encoding utf8
    Add-Content -Path $errFile -Value $stderr -Encoding utf8

    $status = if ($code -eq 0) { 'PASS' } else { 'FAIL' }
    $summary.gates += [ordered]@{ name=$Name; command="$Command $argString"; status=$status;
        exit_code=$code; duration_seconds=[math]::Round((Get-Date - $start).TotalSeconds,2); log_path=$logFile }
    Write-Summary
}

# ── Example: absolute-path resolution for .cmd shims (bare name FAILS on PS5.1) ──
$npmCmd = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $npmCmd) { $npmCmd = 'npm.cmd' }
$npxCmd = (Get-Command npx.cmd -ErrorAction SilentlyContinue).Source
if (-not $npxCmd) { $npxCmd = 'npx.cmd' }

# ── Gates (adapt list) ──
# Gate 1 preflight: check tool versions + deps exist; if FAIL → mark later gates SKIPPED/PREFLIGHT_BLOCKED, exit 2.
# Required gates list drives the final exit code:
$required = @('Gate 2 - X', 'Gate 3 - Y')
$failed = @($summary.gates | Where-Object { $_.name -in $required -and $_.status -eq 'FAIL' })
$blocked = @($summary.gates | Where-Object { $_.name -in $required -and $_.status -eq 'SKIPPED/PREFLIGHT_BLOCKED' })
if ($blocked.Count -gt 0) { $summary.overall.status='PREFLIGHT_BLOCKED'; $summary.overall.exit_code=2 }
elseif ($failed.Count -gt 0) { $summary.overall.status='FAIL'; $summary.overall.exit_code=1 }
else { $summary.overall.status='PASS'; $summary.overall.exit_code=0 }
$summary.finished_at = (Get-Date).ToString('o')
[System.IO.File]::WriteAllText($summaryPath, ($summary | ConvertTo-Json -Depth 6), $utf8NoBom)
exit $summary.overall.exit_code
```

## Verification after adapting
1. `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/<runner>.ps1; echo $?` (NO pipe — exit code lost through pipes).
2. Run from a different cwd to prove repo-root resolution.
3. `python -c "import json; json.load(open('<summary>'), encoding='utf-8-sig')"` — JSON must parse.
4. `git check-ignore <artifact>` — generated artifacts must be ignored.
