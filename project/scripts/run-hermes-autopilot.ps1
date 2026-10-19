param(
    [Parameter(Mandatory = $true)]
    [string]$SessionId,
    [ValidateSet("A", "B", "C", "D", "FINAL", "ALL")]
    [string]$ThroughPhase = "ALL",
    [int]$MaxTurns = 200,
    [int]$WaitForProcessId = 0,
    [string]$HermesModel = "ocg/deepseek-v4-flash"
)

throw "Legacy roadmap autopilot is disabled because it mixes PM approval and Hermes implementation in one long-lived session. Use automation/orchestrator.ps1 so each Task ID has one Hermes session and an explicit PM gate."

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$statePath = Join-Path $repoRoot "docs\pm\AUTOPILOT_STATE.json"
$logPath = Join-Path $repoRoot "output\hermes-autopilot.log"
$notificationPath = Join-Path $repoRoot "output\HERMES_AUTOPILOT_NOTIFICATION.md"
$popupScript = Join-Path $repoRoot "scripts\show-hermes-autopilot-popup.ps1"
Set-Location $repoRoot

if ($WaitForProcessId -gt 0) {
    Wait-Process -Id $WaitForProcessId -ErrorAction SilentlyContinue
    Add-Content $logPath "$(Get-Date -Format o) wait_complete_pid=$WaitForProcessId"
}

for ($turn = 1; $turn -le $MaxTurns; $turn++) {
    $state = Get-Content $statePath -Raw -Encoding utf8 | ConvertFrom-Json
    if ($state.status -eq "SUCCESS") {
        if ($ThroughPhase -eq "ALL" -or $state.phase -eq $ThroughPhase) {
            Add-Content $logPath "$(Get-Date -Format o) SUCCESS phase=$($state.phase)"
            $notification = @(
                "🏁 PROJECT_READY_FOR_CODEX_REVIEW",
                "",
                "Hermes completed the selected roadmap scope and final quality evidence.",
                "Open Codex and send: Review tổng thể MotionForge2D và bàn giao bản sử dụng được."
            ) -join [Environment]::NewLine
            Set-Content -Path $notificationPath -Encoding utf8 -Value $notification
            Start-Process powershell -ArgumentList @(
                "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $popupScript,
                "-Type", "READY"
            ) -WindowStyle Hidden | Out-Null
            exit 0
        }
    }
    if ($state.status -eq "BLOCKED") {
        Add-Content $logPath "$(Get-Date -Format o) BLOCKED $($state.blocker)"
        $notification = @(
            "🛑 AUTOPILOT_BLOCKED $($state.active_task)",
            "",
            "$($state.blocker)",
            "",
            "Ask Codex: Kiểm tra blocker Autopilot và tiếp tục."
        ) -join [Environment]::NewLine
        Set-Content -Path $notificationPath -Encoding utf8 -Value $notification
        Start-Process powershell -ArgumentList @(
            "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $popupScript,
            "-Type", "BLOCKED", "-Task", "$($state.active_task)",
            "-Message", "$($state.blocker)"
        ) -WindowStyle Hidden | Out-Null
        exit 2
    }

    $prompt = @(
        "Continue MotionForge2D autonomously using the motionforge-autopilot skill.",
        "Read docs/pm/AUTOPILOT_STATE.json and current repository evidence first.",
        "Runner target is phase $ThroughPhase. Complete the next durable checkpoint,",
        "update state atomically, and continue through ordinary failures. Do not merely",
        "report progress. End only with the skill's CHECKPOINT/SUCCESS/BLOCKED contract."
    ) -join [Environment]::NewLine
    Add-Content $logPath "$(Get-Date -Format o) turn=$turn session=$SessionId phase=$($state.phase) task=$($state.active_task)"
    & hermes -m $HermesModel --resume $SessionId --skills motionforge-autopilot --oneshot $prompt --pass-session-id *>> $logPath
    if ($LASTEXITCODE -ne 0) {
        Add-Content $logPath "$(Get-Date -Format o) hermes_exit=$LASTEXITCODE; retrying same durable state"
    }
}

Add-Content $logPath "$(Get-Date -Format o) BLOCKED max_turns=$MaxTurns"
exit 3
