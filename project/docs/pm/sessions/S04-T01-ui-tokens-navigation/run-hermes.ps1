$ErrorActionPreference = "Stop"
$sessionRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $sessionRoot "..\..\..\..")
$prompt = Get-Content (Join-Path $sessionRoot "START_PROMPT.md") -Raw -Encoding utf8

Set-Location $repoRoot
& hermes -m "ocg/deepseek-v4-flash" --skills motionforge-autopilot --oneshot $prompt --pass-session-id *>> (Join-Path $sessionRoot "hermes.log")
exit $LASTEXITCODE
