$ErrorActionPreference = 'Stop'
$candidate = 'C:/Users/Admin/Documents/Codex/2026-10-12/a-l-m-video-ra-m-2/outputs/motionforge-g1-review-04-20261020/submissions/g1-candidate-16'
$pilot = 'C:/Users/Admin/Documents/Codex/g2p01-transport/pilot-g2p01-001'
$originSource = 'C:/Users/Admin/.gemini/antigravity/scratch/goha_mmo_clone/backend/downloads/Tại sao thật tệ khi ĐỨNG TÊN HỘ công ty？.mp4'
$manifestHash = '4df7de9ccc81dff7a82a9b9d70d90a48eae2bb17cd9ff455748b041f20a0ba82'
$sourceHash = '5a175454c2c2965bac5013a53926e210a9f70a185d802d0f2e0083a6fb399fa2'
$sourceBytes = 36971916

$manifestPath = Join-Path $candidate 'MANIFEST.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.total_files -ne 74 -or @($manifest.files).Count -ne 74) { throw 'C16 manifest count changed' }
if ((Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $manifestHash) { throw 'C16 manifest SHA changed' }
if ((Get-FileHash -LiteralPath (Join-Path $pilot 'MANIFEST.json') -Algorithm SHA256).Hash.ToLowerInvariant() -cne $manifestHash) { throw 'pilot manifest SHA mismatch' }

$candidateExpected = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
$pilotExpected = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
[void]$candidateExpected.Add('MANIFEST.json')
[void]$pilotExpected.Add('MANIFEST.json')
foreach ($row in $manifest.files) {
    [void]$candidateExpected.Add($row.relative)
    [void]$pilotExpected.Add($row.relative)
    foreach ($root in @($candidate, $pilot)) {
        $path = Join-Path $root $row.relative
        $item = Get-Item -LiteralPath $path -ErrorAction Stop
        $digest = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($item.Length -ne $row.bytes -or $digest -cne $row.sha256) { throw "bytes mismatch: $path" }
    }
}
[void]$pilotExpected.Add('task/source/source_full.mp4')

$candidateActual = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
foreach ($item in Get-ChildItem -LiteralPath $candidate -Recurse -File -Force) {
    [void]$candidateActual.Add($item.FullName.Substring($candidate.Length + 1).Replace('\', '/'))
}
$pilotActual = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
foreach ($item in Get-ChildItem -LiteralPath $pilot -Recurse -File -Force) {
    [void]$pilotActual.Add($item.FullName.Substring($pilot.Length + 1).Replace('\', '/'))
}
if (-not $candidateActual.SetEquals($candidateExpected)) { throw 'C16 inventory changed' }
if (-not $pilotActual.SetEquals($pilotExpected)) { throw 'pilot inventory mismatch' }

$copySource = Join-Path $pilot 'task/source/source_full.mp4'
foreach ($path in @($originSource, $copySource)) {
    $item = Get-Item -LiteralPath $path -ErrorAction Stop
    $digest = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($item.Length -ne $sourceBytes -or $digest -cne $sourceHash) { throw "source pin mismatch: $path" }
}

[pscustomobject]@{
    CandidateFiles = $candidateActual.Count
    PilotFiles = $pilotActual.Count
    ManifestSHA256 = $manifestHash
    SourceSHA256 = $sourceHash
    CandidatePyc = @(Get-ChildItem -LiteralPath $candidate -Recurse -File -Force -Filter '*.pyc').Count
    Result = 'POSTIMAGE_VERIFIED'
} | ConvertTo-Json -Compress
