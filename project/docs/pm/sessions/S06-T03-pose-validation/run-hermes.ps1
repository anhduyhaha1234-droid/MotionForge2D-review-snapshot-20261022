$ErrorActionPreference = "Stop"
$sessionRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = "C:\Users\Admin\MotionForge2D-worktrees\s06-t01"
$prompt = Get-Content (Join-Path $sessionRoot "START_PROMPT.md") -Raw -Encoding utf8

Set-Location $repoRoot
& hermes -m "ocg/deepseek-v4-flash" --skills motionforge-autopilot --oneshot $prompt *>> (Join-Path $sessionRoot "hermes.log")
exit $LASTEXITCODE
