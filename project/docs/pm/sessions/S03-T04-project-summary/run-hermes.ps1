$ErrorActionPreference = "Stop"
$sessionRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $sessionRoot "..\..\..\..")
Set-Location $repoRoot
$prompt = Get-Content (Join-Path $sessionRoot "START_PROMPT.md") -Raw -Encoding utf8
& hermes --oneshot $prompt --pass-session-id *>> (Join-Path $sessionRoot "hermes.log")
exit $LASTEXITCODE
