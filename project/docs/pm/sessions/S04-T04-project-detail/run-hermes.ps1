$ErrorActionPreference = "Continue"
$sessionRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $sessionRoot "..\..\..\..")
$prompt = Get-Content (Join-Path $sessionRoot "START_PROMPT.md") -Raw -Encoding utf8

Set-Location $repoRoot
& hermes -m "ocg/deepseek-v4-flash" --skills motionforge-autopilot --oneshot $prompt 2>&1 | Out-File -Append -FilePath (Join-Path $sessionRoot "hermes.log") -Encoding utf8
exit $LASTEXITCODE
