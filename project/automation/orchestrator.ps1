<#
.SYNOPSIS
    Safe local task/session orchestrator for MotionForge 2D and Hermes.

.DESCRIPTION
    Enforces one Task ID per new Hermes session. Corrections resume only the
    stored session ID. The orchestrator never approves tasks or releases the
    next roadmap item. Start/Resume/Close are dry-run unless -Execute is given.
#>

[CmdletBinding()]
param(
    [ValidateSet('Validate', 'Status', 'Start', 'Resume', 'Close', 'ResetFailed')]
    [string]$Action = 'Status',
    [string]$SessionPath,
    [string]$CorrectionPromptPath,
    [string]$TaskId,
    [switch]$Execute
)

$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$configPath = Join-Path $scriptDir 'config.json'

if (-not (Test-Path -LiteralPath $configPath)) {
    throw "Missing orchestrator config: $configPath"
}

$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
$runtimeRoot = Join-Path $repoRoot ([string]$config.runtime_root)
$statePath = Join-Path $runtimeRoot 'state.json'
$lockPath = Join-Path $runtimeRoot 'orchestrator.lock'
$inboxDir = Join-Path $runtimeRoot 'inbox'
$outboxDir = Join-Path $runtimeRoot 'outbox'
$logsDir = Join-Path $runtimeRoot 'logs'

@($runtimeRoot, $inboxDir, $outboxDir, $logsDir) | ForEach-Object {
    New-Item -ItemType Directory -Force -Path $_ | Out-Null
}

function Write-JsonFile {
    param([string]$Path, [object]$Value)
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    $json = $Value | ConvertTo-Json -Depth 8
    [System.IO.File]::WriteAllText($Path, $json, $utf8)
}

function Get-State {
    if (-not (Test-Path -LiteralPath $statePath)) { return $null }
    return Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
}

function ConvertTo-ArgumentString {
    param([string[]]$ArgumentList)
    $parts = foreach ($argument in $ArgumentList) {
        if ($argument -match '[\s"]') {
            '"' + ($argument -replace '"', '\"') + '"'
        } else {
            $argument
        }
    }
    return ($parts -join ' ')
}

function Acquire-Lock {
    try {
        $stream = [System.IO.File]::Open(
            $lockPath,
            [System.IO.FileMode]::CreateNew,
            [System.IO.FileAccess]::Write,
            [System.IO.FileShare]::None
        )
        $writer = New-Object System.IO.StreamWriter($stream)
        $writer.WriteLine("pid=$PID")
        $writer.WriteLine("started_at=$((Get-Date).ToString('o'))")
        $writer.Flush()
        return @{ Stream = $stream; Writer = $writer }
    } catch [System.IO.IOException] {
        throw "Orchestrator lock exists: $lockPath. Another run may be active."
    }
}

function Release-Lock {
    param($Lock)
    if ($null -ne $Lock) {
        $Lock.Writer.Dispose()
        $Lock.Stream.Dispose()
    }
    if (Test-Path -LiteralPath $lockPath) {
        Remove-Item -LiteralPath $lockPath -Force
    }
}

function Resolve-SessionPacket {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { throw 'SessionPath is required.' }
    $absolute = if ([System.IO.Path]::IsPathRooted($Path)) { $Path } else { Join-Path $repoRoot $Path }
    $absolute = [System.IO.Path]::GetFullPath($absolute)
    $sessionsRoot = [System.IO.Path]::GetFullPath((Join-Path $repoRoot 'docs\pm\sessions'))
    if (-not $absolute.StartsWith($sessionsRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Session path must stay under $sessionsRoot"
    }
    foreach ($name in @('START_PROMPT.md', 'TASK.md', 'REPORT.md', 'LOG.md', 'PM_REVIEW.md')) {
        if (-not (Test-Path -LiteralPath (Join-Path $absolute $name))) {
            throw "Incomplete session packet; missing $name"
        }
    }
    $taskText = Get-Content -LiteralPath (Join-Path $absolute 'TASK.md') -Raw
    $taskMatch = [regex]::Match($taskText, '(?m)^#\s+(S\d{2}-T\d{2}[A-Z0-9]*)\s+-')
    $statusMatch = [regex]::Match($taskText, '(?m)^\*\*Status:\*\*\s+([A-Z_]+)')
    if (-not $taskMatch.Success -or -not $statusMatch.Success) {
        throw 'TASK.md must expose Task ID and Status in the standard format.'
    }
    return [ordered]@{
        absolute_path = $absolute
        relative_path = $absolute.Substring($repoRoot.TrimEnd('\').Length).TrimStart('\').Replace('\', '/')
        task_id = $taskMatch.Groups[1].Value
        task_status = $statusMatch.Groups[1].Value
        prompt_path = Join-Path $absolute 'START_PROMPT.md'
        report_path = Join-Path $absolute 'REPORT.md'
        review_path = Join-Path $absolute 'PM_REVIEW.md'
    }
}

function Get-ReportStatus {
    param([string]$ReportPath)
    $text = Get-Content -LiteralPath $ReportPath -Raw
    $match = [regex]::Match($text, '(?m)^\*\*Status:\*\*\s+([A-Z_]+)')
    if ($match.Success) { return $match.Groups[1].Value }
    return 'UNKNOWN'
}

function Invoke-Hermes {
    param(
        [string]$Prompt,
        [string]$ExistingSessionId,
        [string]$RunLabel
    )
    $hermes = Get-Command ([string]$config.hermes_command) -ErrorAction Stop
    $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $stdoutPath = Join-Path $logsDir "$RunLabel-$timestamp.stdout.txt"
    $stderrPath = Join-Path $logsDir "$RunLabel-$timestamp.stderr.txt"

    $arguments = @('chat', '-q', $Prompt, '-Q', '--source', [string]$config.source_tag,
        '--max-turns', [string]$config.max_turns, '--provider', [string]$config.provider,
        '--model', [string]$config.model, '--pass-session-id')
    if ([bool]$config.require_checkpoints) { $arguments += '--checkpoints' }
    if (-not [string]::IsNullOrWhiteSpace($ExistingSessionId)) {
        $arguments += @('--resume', $ExistingSessionId, '--no-restore-cwd')
    }

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $hermes.Source
    $psi.WorkingDirectory = $repoRoot
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    # Windows PowerShell 5.1 does not expose ProcessStartInfo.ArgumentList.
    $psi.Arguments = ConvertTo-ArgumentString $arguments

    $process = [System.Diagnostics.Process]::Start($psi)
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $timeoutMs = [int]$config.timeout_minutes * 60 * 1000
    if (-not $process.WaitForExit($timeoutMs)) {
        try { $process.Kill() } catch { }
        throw "Hermes timed out after $($config.timeout_minutes) minutes."
    }
    $stdout = $stdoutTask.Result
    $stderr = $stderrTask.Result
    [System.IO.File]::WriteAllText($stdoutPath, $stdout)
    [System.IO.File]::WriteAllText($stderrPath, $stderr)

    $sessionMatch = [regex]::Match(
        ($stdout + "`n" + $stderr),
        '(?im)session(?:_id|\s+id)\s*[:=]\s*([A-Za-z0-9._-]+)'
    )
    $resolvedSession = if ($sessionMatch.Success) { $sessionMatch.Groups[1].Value } else { $ExistingSessionId }
    return [ordered]@{
        exit_code = $process.ExitCode
        session_id = $resolvedSession
        stdout_path = $stdoutPath
        stderr_path = $stderrPath
    }
}

if ($Action -eq 'Status') {
    $state = Get-State
    if ($null -eq $state) { Write-Host 'No active automation state.' } else { $state | ConvertTo-Json -Depth 8 }
    exit 0
}

if ($Action -eq 'ResetFailed') {
    $state = Get-State
    if ($null -eq $state) { Write-Host 'No failed state to reset.'; exit 0 }
    if (-not $Execute) { Write-Host "DRY RUN: would reset failed launch state for $($state.task_id)."; exit 0 }
    $packet = Resolve-SessionPacket $state.session_path
    $reportStatus = Get-ReportStatus $packet.report_path
    if (-not [string]::IsNullOrWhiteSpace($state.hermes_session_id)) {
        throw 'Reset denied: a Hermes session ID exists.'
    }
    if ($reportStatus -ne 'NOT_STARTED') {
        throw "Reset denied: report status is $reportStatus, not NOT_STARTED."
    }
    if ($state.hermes_exit_code -eq 0) { throw 'Reset denied: launch did not fail.' }
    Remove-Item -LiteralPath $statePath -Force
    Write-Host "Failed launch state reset for $($state.task_id); audit logs were preserved."
    exit 0
}

if ($Action -eq 'Validate') {
    $packet = Resolve-SessionPacket $SessionPath
    $hermes = Get-Command ([string]$config.hermes_command) -ErrorAction Stop
    Write-Host "Task             : $($packet.task_id)"
    Write-Host "Task status      : $($packet.task_status)"
    Write-Host "Session path     : $($packet.relative_path)"
    Write-Host "Hermes executable: $($hermes.Source)"
    Write-Host "Provider/model   : $($config.provider) / $($config.model)"
    Write-Host 'Validation only; Hermes was not launched.'
    exit 0
}

$lock = $null
try {
    $lock = Acquire-Lock
    $state = Get-State

    if ($Action -eq 'Start') {
        $packet = Resolve-SessionPacket $SessionPath
        if ($packet.task_status -ne 'READY') { throw "Task must be READY, found $($packet.task_status)." }
        $initialReportStatus = Get-ReportStatus $packet.report_path
        if ($initialReportStatus -ne 'NOT_STARTED') {
            throw "New session requires REPORT status NOT_STARTED, found $initialReportStatus. Use Resume for corrections."
        }
        if ($null -ne $state -and $state.status -notin @('CLOSED', 'EMPTY')) {
            throw "Active task $($state.task_id) must be closed before starting a new Task ID."
        }
        $prompt = Get-Content -LiteralPath $packet.prompt_path -Raw
        $envelope = [ordered]@{
            action = 'START_NEW_SESSION'; task_id = $packet.task_id
            session_path = $packet.relative_path; created_at = (Get-Date).ToString('o')
            execute = [bool]$Execute; prompt_sha256 = (Get-FileHash $packet.prompt_path -Algorithm SHA256).Hash
        }
        Write-JsonFile (Join-Path $outboxDir "$($packet.task_id)-start.json") $envelope
        if (-not $Execute) {
            $envelope | ConvertTo-Json -Depth 6
            Write-Host 'DRY RUN: add -Execute to launch a new Hermes session.'
            exit 0
        }
        $runningState = [ordered]@{
            schema_version = 1; task_id = $packet.task_id; session_path = $packet.relative_path
            hermes_session_id = ''; status = 'HERMES_RUNNING'; correction_attempts = 0
            report_status = $initialReportStatus; started_at = (Get-Date).ToString('o')
            updated_at = (Get-Date).ToString('o')
        }
        Write-JsonFile $statePath $runningState
        $result = Invoke-Hermes -Prompt $prompt -ExistingSessionId '' -RunLabel "$($packet.task_id)-start"
        $finalReportStatus = Get-ReportStatus $packet.report_path
        $handoffStatus = if ($result.exit_code -eq 0 -and $finalReportStatus -eq 'SUBMITTED') {
            'SUBMITTED_PENDING_PM'
        } else {
            'HERMES_FAILED'
        }
        $newState = [ordered]@{
            schema_version = 1; task_id = $packet.task_id; session_path = $packet.relative_path
            hermes_session_id = $result.session_id; status = $handoffStatus
            correction_attempts = 0; hermes_exit_code = $result.exit_code
            report_status = $finalReportStatus
            started_at = (Get-Date).ToString('o'); updated_at = (Get-Date).ToString('o')
            stdout_path = $result.stdout_path; stderr_path = $result.stderr_path
        }
        Write-JsonFile $statePath $newState
        $newState | ConvertTo-Json -Depth 8
        if ([string]::IsNullOrWhiteSpace($result.session_id)) {
            throw 'Hermes finished but session ID could not be captured; do not resume automatically.'
        }
        exit $result.exit_code
    }

    if ($Action -eq 'Resume') {
        if ($null -eq $state -or $state.status -eq 'CLOSED') { throw 'No active task session to resume.' }
        if ([string]::IsNullOrWhiteSpace($state.hermes_session_id)) { throw 'Stored Hermes session ID is missing.' }
        if ([int]$state.correction_attempts -ge [int]$config.max_correction_attempts) {
            throw 'Maximum correction attempts reached; human decision required.'
        }
        if ([string]::IsNullOrWhiteSpace($CorrectionPromptPath)) { throw 'CorrectionPromptPath is required.' }
        $correctionAbsolute = if ([System.IO.Path]::IsPathRooted($CorrectionPromptPath)) {
            $CorrectionPromptPath
        } else { Join-Path $repoRoot $CorrectionPromptPath }
        if (-not (Test-Path -LiteralPath $correctionAbsolute)) { throw 'Correction prompt file not found.' }
        if (-not $Execute) {
            Write-Host "DRY RUN: would resume task $($state.task_id), Hermes session $($state.hermes_session_id)."
            exit 0
        }
        $prompt = Get-Content -LiteralPath $correctionAbsolute -Raw
        $state.status = 'HERMES_RUNNING'
        $state.updated_at = (Get-Date).ToString('o')
        Write-JsonFile $statePath $state
        $result = Invoke-Hermes -Prompt $prompt -ExistingSessionId $state.hermes_session_id -RunLabel "$($state.task_id)-correction"
        $state.correction_attempts = [int]$state.correction_attempts + 1
        $state.hermes_exit_code = $result.exit_code
        $resumeReportPath = Join-Path (Join-Path $repoRoot $state.session_path) 'REPORT.md'
        $state.report_status = Get-ReportStatus $resumeReportPath
        $state.status = if ($result.exit_code -eq 0 -and $state.report_status -eq 'SUBMITTED') {
            'SUBMITTED_PENDING_PM'
        } else {
            'HERMES_FAILED'
        }
        $state.updated_at = (Get-Date).ToString('o')
        $state.stdout_path = $result.stdout_path
        $state.stderr_path = $result.stderr_path
        Write-JsonFile $statePath $state
        $state | ConvertTo-Json -Depth 8
        exit $result.exit_code
    }

    if ($Action -eq 'Close') {
        if ($null -eq $state) { throw 'No active state to close.' }
        if ($state.task_id -ne $TaskId) { throw "Close TaskId mismatch: active=$($state.task_id), requested=$TaskId" }
        if (-not $Execute) {
            Write-Host "DRY RUN: would close $TaskId. PM approval must already exist."
            exit 0
        }
        $packet = Resolve-SessionPacket $state.session_path
        $reportStatus = Get-ReportStatus $packet.report_path
        if ($state.status -ne 'SUBMITTED_PENDING_PM' -or $reportStatus -ne 'SUBMITTED') {
            throw "Close denied: state/report must be SUBMITTED_PENDING_PM/SUBMITTED, found $($state.status)/$reportStatus."
        }
        $review = Get-Content -LiteralPath $packet.review_path -Raw
        if ($review -notmatch '(?m)^\s*(?:-\s*)?\*\*Decision:\*\*\s+APPROVED\s*$') {
            throw 'PM_REVIEW.md is not APPROVED; close denied.'
        }
        if ($review -notmatch '(?m)^\s*(?:-\s*)?\*\*Reviewed commit/tree:\*\*\s+\S+') {
            throw 'PM_REVIEW.md must record the reviewed commit/tree; close denied.'
        }
        if ($review -notmatch '(?m)^\s*(?:-\s*)?\*\*Quality Run ID:\*\*\s+\S+') {
            throw 'PM_REVIEW.md must record a Quality Run ID; close denied.'
        }
        $state.status = 'CLOSED'
        $state | Add-Member -NotePropertyName closed_at -NotePropertyValue ((Get-Date).ToString('o')) -Force
        $state.updated_at = (Get-Date).ToString('o')
        Write-JsonFile $statePath $state
        $state | ConvertTo-Json -Depth 8
        exit 0
    }
} finally {
    Release-Lock $lock
}
