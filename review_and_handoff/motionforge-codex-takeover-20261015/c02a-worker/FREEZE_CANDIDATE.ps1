param(
  [Parameter(Mandatory=$true)][string]$R6,
  [Parameter(Mandatory=$true)][string]$Worker,
  [Parameter(Mandatory=$true)][string]$Preflight
)
$candidate = Join-Path $Worker 'candidate-01'
if (Test-Path -LiteralPath $candidate) { throw "Candidate already exists: $candidate" }
$manifestBefore = Get-Content -LiteralPath $Preflight -Raw | ConvertFrom-Json
$lookup = @{}
foreach ($entry in $manifestBefore.files) { $lookup[$entry.relative] = $entry }
$files = @()
$relativePaths = @(
  'scripts/r6_cache.py', 'scripts/r6_gate.py',
  'tests/test_codex_c01_review_binding.py',
  'tests/test_codex_c02a_dependency_verification.py'
)
foreach ($relative in $relativePaths) {
  $source = Join-Path $R6 ($relative -replace '/', '\')
  $snapshot = Join-Path (Join-Path $candidate 'files') ($relative -replace '/', '\')
  New-Item -ItemType Directory -Path (Split-Path -Parent $snapshot) -Force | Out-Null
  Copy-Item -LiteralPath $source -Destination $snapshot
  $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
  $snapshotHash = (Get-FileHash -LiteralPath $snapshot -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($sourceHash -ne $snapshotHash) { throw "Candidate copy differs: $relative" }
  $old = $lookup[$relative]
  $files += [pscustomobject]@{
    relative = $relative; source = $source; snapshot = $snapshot
    sha256 = $snapshotHash; bytes = (Get-Item -LiteralPath $snapshot).Length
    lines = [IO.File]::ReadAllLines($snapshot).Length
    baseline_sha256 = if ($null -eq $old) { $null } else { $old.sha256 }
    status = if ($null -eq $old) { 'added' } else { 'modified' }
  }
}
$empty = Join-Path $candidate 'EMPTY'
[IO.File]::WriteAllBytes($empty, [byte[]]@())
$diffs = @()
for ($i = 0; $i -lt $relativePaths.Count; $i++) {
  $relative = $relativePaths[$i]
  $old = if ($i -eq 3) { $empty } else {
    Join-Path (Join-Path $Worker 'preimages') ($relative -replace '/', '\')
  }
  $new = $files[$i].snapshot
  $diff = Join-Path $candidate ('DIFF_' + ($i + 1).ToString('00') + '.patch')
  $stderr = Join-Path $candidate ('DIFF_' + ($i + 1).ToString('00') + '.stderr.txt')
  & git -c core.autocrlf=false diff --no-index -- $old $new 1> $diff 2> $stderr
  if ($LASTEXITCODE -ne 1) { throw "Unexpected diff exit for $relative`: $LASTEXITCODE" }
  $diffs += [pscustomobject]@{
    relative = $relative; path = $diff
    sha256 = (Get-FileHash -LiteralPath $diff -Algorithm SHA256).Hash.ToLowerInvariant()
    bytes = (Get-Item -LiteralPath $diff).Length
  }
}
$evidence = @(
  'AFFECTED_FINAL_01.txt', 'root-probe-self-02/RESULT.json',
  'STATIC_AUDIT.json', 'PROTECTED_SCOPE_CHECK.json'
)
$receipts = @()
foreach ($relative in $evidence) {
  $path = Join-Path $Worker ($relative -replace '/', '\')
  $receipts += [pscustomobject]@{
    relative = $relative; path = $path
    sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
  }
}
$manifest = [pscustomobject]@{
  task = 'CODEX-C02A-DEPENDENCY-VERIFICATION'
  status = 'TASK_SUBMITTED_PENDING_ROOT_REVIEW'
  owner = '/root/motionforge_c02a_coder'
  model = 'gpt-6-sol'; reasoning = 'max'; fallback = 'disabled'
  created_utc = [DateTime]::UtcNow.ToString('o')
  preflight = $Preflight
  preflight_sha256 = (Get-FileHash -LiteralPath $Preflight -Algorithm SHA256).Hash.ToLowerInvariant()
  files = $files; diffs = $diffs; receipts = $receipts
}
$manifestPath = Join-Path $candidate 'MANIFEST.json'
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8
Write-Output ([pscustomobject]@{
  candidate = $candidate
  manifest = $manifestPath
  manifest_sha256 = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
  files = $files.Count; diffs = $diffs.Count; receipts = $receipts.Count
})
