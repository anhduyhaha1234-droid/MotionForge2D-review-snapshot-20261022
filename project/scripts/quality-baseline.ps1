<#
.SYNOPSIS
    MotionForge 2D quality baseline runner.

.DESCRIPTION
    Runs the seven required quality gates sequentially, capturing each gate's
    command, stdout/stderr, exit code, duration and status independently.
    A failing gate does NOT stop later gates. Produces per-gate logs and a
    summary JSON under <repo-root>/output/quality-baseline/.
    Exits 0 ONLY if every required gate PASSes; otherwise exits non-zero
    (a failing baseline is data, not a bug in this script).

    Gates:
      1. Environment/preflight  - python/node/npm versions + frontend deps exist (no install)
      2. Python tests           - python -m pytest -q -m "not gpu and not sam2 and not integration"
      3. Python lint            - python -m ruff check app tests
      4. Python typing          - python -m mypy app
      5. Frontend typecheck     - npx tsc --noEmit        (in frontend/)
      6. Frontend lint          - npm run lint            (in frontend/)
      7. Frontend build         - npm run build           (in frontend/)

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/quality-baseline.ps1
#>

[CmdletBinding()]
param(
    [switch]$SkipFrontendDepsCheck
)

$ErrorActionPreference = 'Stop'

# ── Repo root resolution (independent of current working directory) ─────────
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir          # scripts/ -> repo root

# ── Output dir for generated artifacts ───────────────────────────────────────
$outDir = Join-Path $repoRoot 'output\quality-baseline'
$runId   = Get-Date -Format 'yyyyMMdd-HHmmss'
$runDir  = Join-Path $outDir $runId
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$summaryPath = Join-Path $runDir 'summary.json'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

$summary = [ordered]@{
    run_id        = $runId
    started_at    = (Get-Date).ToString('o')
    repo_root     = $repoRoot
    tool_versions = [ordered]@{}
    gates         = @()
    overall       = [ordered]@{ status = 'RUNNING'; exit_code = 1 }
}

function Write-Summary {
    $json = $summary | ConvertTo-Json -Depth 6
    [System.IO.File]::WriteAllText($summaryPath, $json, $utf8NoBom)
}

# ── Helper: build a command-line string with correct quoting (PS 5.1 safe) ──
function ConvertTo-ArgumentString {
    param([string[]]$ArgList)
    $parts = foreach ($a in $ArgList) {
        if ($a -match '[\s"]') {
            '"' + ($a -replace '"', '\"') + '"'
        } else {
            $a
        }
    }
    return ($parts -join ' ')
}

# ── Helper: run one command, capture everything, never throw ─────────────────
function Invoke-Gate {
    param(
        [string]$Name,
        [string]$Command,
        [string]$WorkingDir,
        [string[]]$Arguments,
        [int]$TimeoutSeconds = 1800
    )

    $start = Get-Date
    $safeName = $Name -replace '[^A-Za-z0-9_-]', '_'
    $logFile = Join-Path $runDir ($safeName + '.log')
    $errFile = Join-Path $runDir ($safeName + '.err.log')
    $argString = ConvertTo-ArgumentString $Arguments

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Command
    $psi.Arguments = $argString
    $psi.WorkingDirectory = if ($WorkingDir) { $WorkingDir } else { $repoRoot }
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true

    try {
        $proc = [System.Diagnostics.Process]::Start($psi)
    } catch {
        $finish = Get-Date
        $summary.gates += [ordered]@{
            name = $Name; command = "$Command $argString"; status = 'FAIL'
            exit_code = -1; duration_seconds = ($finish - $start).TotalSeconds
            log_path = $logFile; error = "start failed: $($_.Exception.Message)"
        }
        Set-Content -Path $logFile -Value "COMMAND: $Command $argString" -Encoding utf8
        Add-Content -Path $logFile -Value "START FAILED: $($_.Exception.Message)" -Encoding utf8
        Write-Summary
        return
    }

    $stdoutTask = $proc.StandardOutput.ReadToEndAsync()
    $stderrTask = $proc.StandardError.ReadToEndAsync()

    if (-not $proc.WaitForExit($TimeoutSeconds * 1000)) {
        try { $proc.Kill() } catch { }
        $proc.WaitForExit()
        $finish = Get-Date
        $stdout = $stdoutTask.Result
        $stderr = $stderrTask.Result
        $summary.gates += [ordered]@{
            name = $Name; command = "$Command $argString"; status = 'FAIL'
            exit_code = -1; duration_seconds = ($finish - $start).TotalSeconds
            log_path = $logFile; error = "timed out after ${TimeoutSeconds}s"
        }
        Set-Content -Path $logFile -Value "COMMAND: $Command $argString" -Encoding utf8
        Add-Content -Path $logFile -Value $stdout -Encoding utf8
        Add-Content -Path $errFile -Value $stderr -Encoding utf8
        Write-Summary
        return
    }

    $finish = Get-Date
    $stdout = $stdoutTask.Result
    $stderr = $stderrTask.Result
    $code = $proc.ExitCode

    Set-Content -Path $logFile -Value "COMMAND: $Command $argString" -Encoding utf8
    Add-Content -Path $logFile -Value "WORKDIR: $WorkingDir" -Encoding utf8
    Add-Content -Path $logFile -Value "EXIT CODE: $code" -Encoding utf8
    Add-Content -Path $logFile -Value "--- STDOUT ---" -Encoding utf8
    Add-Content -Path $logFile -Value $stdout -Encoding utf8
    Add-Content -Path $errFile -Value "--- STDERR ---" -Encoding utf8
    Add-Content -Path $errFile -Value $stderr -Encoding utf8

    $status = if ($code -eq 0) { 'PASS' } else { 'FAIL' }
    $summary.gates += [ordered]@{
        name = $Name; command = "$Command $argString"; status = $status
        exit_code = $code; duration_seconds = [math]::Round(($finish - $start).TotalSeconds, 2)
        log_path = $logFile
    }
    Write-Summary
}

# ── Tool version capture (never dumps full environment or secrets) ───────────
function Get-ToolVersion {
    param([string]$Name, [string]$Command, [string[]]$Arguments)
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $Command
        $psi.Arguments = ConvertTo-ArgumentString $Arguments
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.CreateNoWindow = $true
        $p = [System.Diagnostics.Process]::Start($psi)
        $outTask = $p.StandardOutput.ReadToEndAsync()
        $errTask = $p.StandardError.ReadToEndAsync()
        if (-not $p.WaitForExit(30000)) {
            try { $p.Kill() } catch { }
            return "unavailable: timed out"
        }
        $out = $outTask.Result
        $err = $errTask.Result
        return (($out + $err).Trim())
    } catch {
        return "unavailable: $($_.Exception.Message)"
    }
}

# ═════════════════════════════════════════════════════════════════════════════
# GATE 1 — Environment / preflight
# ═════════════════════════════════════════════════════════════════════════════
$gate1 = [ordered]@{
    name = 'Gate 1 - Environment/Preflight'; command = 'version checks + frontend deps'
    status = 'PASS'; exit_code = 0; duration_seconds = 0; log_path = ''
}

$preflightLog = Join-Path $runDir 'gate1_preflight.log'
$preflightLines = @('GATE 1 - ENVIRONMENT/PREFLIGHT')

$pyVer = Get-ToolVersion 'python' 'python' @('--version')
$nodeVer = Get-ToolVersion 'node' 'node' @('--version')
$npmCmd = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $npmCmd) { $npmCmd = 'npm.cmd' }
$npmVer = Get-ToolVersion 'npm' $npmCmd @('--version')

$summary.tool_versions.python = $pyVer
$summary.tool_versions.node = $nodeVer
$summary.tool_versions.npm = $npmVer

$preflightLines += "python: $pyVer"
$preflightLines += "node: $nodeVer"
$preflightLines += "npm: $npmVer"

$preflightOk = $true
if ($pyVer -match 'unavailable|^$') { $preflightOk = $false }
if ($nodeVer -match 'unavailable|^$') { $preflightOk = $false }
if ($npmVer -match 'unavailable|^$') { $preflightOk = $false }

# Frontend dependencies must EXIST — never auto-install.
$feNodeModules = Join-Path $repoRoot 'frontend\node_modules'
$feDepsOk = (Test-Path (Join-Path $feNodeModules '.bin\tsc')) `
    -and (Test-Path (Join-Path $feNodeModules '.bin\eslint')) `
    -and (Test-Path (Join-Path $feNodeModules '.bin\next'))
$preflightLines += "frontend/node_modules present: $(Test-Path $feNodeModules)"
$preflightLines += "frontend .bin/tsc: $(Test-Path (Join-Path $feNodeModules '.bin\tsc'))"
$preflightLines += "frontend .bin/eslint: $(Test-Path (Join-Path $feNodeModules '.bin\eslint'))"
$preflightLines += "frontend .bin/next: $(Test-Path (Join-Path $feNodeModules '.bin\next'))"
if (-not $feDepsOk) { $preflightOk = $false }

if (-not $preflightOk) {
    $gate1.status = 'FAIL'
    $gate1.exit_code = 1
    $gate1.error = 'preflight failure: missing tool or frontend dependencies (install is out of scope)'
}
$gate1.log_path = $preflightLog
$gate1.duration_seconds = 0
Set-Content -Path $preflightLog -Value ($preflightLines -join "`r`n") -Encoding utf8
$summary.gates += $gate1
Write-Summary

# If preflight failed, mark the tool-dependent gates as SKIPPED/PREFLIGHT_BLOCKED
# (they cannot run meaningfully) but STILL record them; required gates are never omitted.
if (-not $preflightOk) {
    $skippedGates = @(
        'Gate 2 - Python tests',
        'Gate 3 - Python lint',
        'Gate 4 - Python typing',
        'Gate 5 - Frontend typecheck',
        'Gate 6 - Frontend lint',
        'Gate 7 - Frontend build'
    )
    foreach ($g in $skippedGates) {
        $summary.gates += [ordered]@{
            name = $g; command = ''; status = 'SKIPPED/PREFLIGHT_BLOCKED'
            exit_code = -1; duration_seconds = 0; log_path = $preflightLog
            error = 'preflight blocked (see gate 1)'
        }
    }
} else {
    # ═════════════════════════════════════════════════════════════════════════
    # GATE 2 — Python tests
    # ═════════════════════════════════════════════════════════════════════════
    $pytestMarker = 'not gpu and not sam2 and not integration'
    Invoke-Gate -Name 'Gate 2 - Python tests' -Command 'python' -WorkingDir $repoRoot `
        -Arguments @('-m', 'pytest', '-q', '-m', $pytestMarker)

    # ═════════════════════════════════════════════════════════════════════════
    # GATE 3 — Python lint
    # ═════════════════════════════════════════════════════════════════════════
    Invoke-Gate -Name 'Gate 3 - Python lint' -Command 'python' -WorkingDir $repoRoot `
        -Arguments @('-m', 'ruff', 'check', 'app', 'tests')

    # ═════════════════════════════════════════════════════════════════════════
    # GATE 4 — Python typing
    # ═════════════════════════════════════════════════════════════════════════
    Invoke-Gate -Name 'Gate 4 - Python typing' -Command 'python' -WorkingDir $repoRoot `
        -Arguments @('-m', 'mypy', 'app')

    # ═════════════════════════════════════════════════════════════════════════
    # GATE 5 — Frontend typecheck
    # ═════════════════════════════════════════════════════════════════════════
    $feDir = Join-Path $repoRoot 'frontend'
    $npxCmd = (Get-Command npx.cmd -ErrorAction SilentlyContinue).Source
    if (-not $npxCmd) { $npxCmd = 'npx.cmd' }
    Invoke-Gate -Name 'Gate 5 - Frontend typecheck' -Command $npxCmd -WorkingDir $feDir `
        -Arguments @('tsc', '--noEmit')

    # ═════════════════════════════════════════════════════════════════════════
    # GATE 6 — Frontend lint
    # ═════════════════════════════════════════════════════════════════════════
    Invoke-Gate -Name 'Gate 6 - Frontend lint' -Command $npmCmd -WorkingDir $feDir `
        -Arguments @('run', 'lint')

    # ═════════════════════════════════════════════════════════════════════════
    # GATE 7 — Frontend production build
    # ═════════════════════════════════════════════════════════════════════════
    Invoke-Gate -Name 'Gate 7 - Frontend build' -Command $npmCmd -WorkingDir $feDir `
        -Arguments @('run', 'build')
}

# ── Overall result ───────────────────────────────────────────────────────────
$required = @(
    'Gate 2 - Python tests',
    'Gate 3 - Python lint',
    'Gate 4 - Python typing',
    'Gate 5 - Frontend typecheck',
    'Gate 6 - Frontend lint',
    'Gate 7 - Frontend build'
)

$failed = @($summary.gates | Where-Object { $_.name -in $required -and $_.status -eq 'FAIL' })
$blocked = @($summary.gates | Where-Object { $_.name -in $required -and $_.status -eq 'SKIPPED/PREFLIGHT_BLOCKED' })

if ($blocked.Count -gt 0) {
    $summary.overall.status = 'PREFLIGHT_BLOCKED'
    $summary.overall.exit_code = 2
} elseif ($failed.Count -gt 0) {
    $summary.overall.status = 'FAIL'
    $summary.overall.exit_code = 1
} else {
    $summary.overall.status = 'PASS'
    $summary.overall.exit_code = 0
}

$summary.finished_at = (Get-Date).ToString('o')
$json = $summary | ConvertTo-Json -Depth 6
[System.IO.File]::WriteAllText($summaryPath, $json, $utf8NoBom)

# Human-readable summary to stdout (report file is the machine-readable record).
Write-Host ''
Write-Host '========================= QUALITY BASELINE ========================='
Write-Host "run id      : $runId"
Write-Host "repo root   : $repoRoot"
Write-Host "summary     : $summaryPath"
Write-Host '--------------------------------------------------------------------'
foreach ($g in $summary.gates) {
    $dur = if ($null -eq $g.duration_seconds) { '-' } else { "$($g.duration_seconds)s" }
    Write-Host ("{0,-38} {1,-24} exit={2,-4} {3}" -f $g.name, $g.status, $g.exit_code, $dur)
}
Write-Host '--------------------------------------------------------------------'
Write-Host ("OVERALL: {0} (exit code {1})" -f $summary.overall.status, $summary.overall.exit_code)
Write-Host '===================================================================='

exit $summary.overall.exit_code
