param(
  [Parameter(Mandatory=$true)][string]$Preflight,
  [Parameter(Mandatory=$true)][string]$OwnPreimages,
  [Parameter(Mandatory=$true)][string]$NewTest,
  [Parameter(Mandatory=$true)][string]$Output
)
$j = Get-Content -LiteralPath $Preflight -Raw | ConvertFrom-Json
$errors = @()
$files = @()
foreach ($item in $j.files) {
  if (-not (Test-Path -LiteralPath $item.path -PathType Leaf)) {
    $errors += "missing $($item.relative)"
    continue
  }
  $own = Join-Path $OwnPreimages ($item.relative -replace '/', '\')
  if (-not (Test-Path -LiteralPath $own -PathType Leaf)) {
    $errors += "own preimage missing $($item.relative)"
    continue
  }
  $oldHash = (Get-FileHash -LiteralPath $own -Algorithm SHA256).Hash.ToLowerInvariant()
  $rootHash = (Get-FileHash -LiteralPath $item.snapshot -Algorithm SHA256).Hash.ToLowerInvariant()
  $hash = (Get-FileHash -LiteralPath $item.path -Algorithm SHA256).Hash.ToLowerInvariant()
  $bytes = (Get-Item -LiteralPath $item.path).Length
  $lines = [IO.File]::ReadAllLines($item.path).Length
  if ($oldHash -ne $item.sha256 -or $rootHash -ne $item.sha256) {
    $errors += "preimage authority mismatch $($item.relative)"
  }
  if ($item.role -eq 'protected' -and $hash -ne $item.sha256) {
    $errors += "protected drift $($item.relative)"
  }
  if ($item.role -eq 'writable' -and ($bytes -lt $item.bytes -or $lines -lt $item.lines)) {
    $errors += "writable shrink $($item.relative)"
  }
  $files += [pscustomobject]@{
    relative = $item.relative; role = $item.role; sha256 = $hash
    baseline_sha256 = $item.sha256; changed = ($hash -ne $item.sha256)
    bytes = $bytes; baseline_bytes = $item.bytes
    lines = $lines; baseline_lines = $item.lines
  }
}
if (-not (Test-Path -LiteralPath $NewTest -PathType Leaf)) { $errors += 'new C02A test missing' }
$new = if (Test-Path -LiteralPath $NewTest -PathType Leaf) {
  [pscustomobject]@{
    path = $NewTest
    sha256 = (Get-FileHash -LiteralPath $NewTest -Algorithm SHA256).Hash.ToLowerInvariant()
    bytes = (Get-Item -LiteralPath $NewTest).Length
    lines = [IO.File]::ReadAllLines($NewTest).Length
  }
} else { $null }
$changed = @($files | Where-Object { $_.changed } | ForEach-Object { $_.relative })
if (@($changed | Where-Object { $_ -notin @('scripts/r6_cache.py', 'scripts/r6_gate.py', 'tests/test_codex_c01_review_binding.py') }).Count -gt 0) {
  $errors += 'unexpected changed file'
}
$receipt = [pscustomobject]@{
  ok = ($errors.Count -eq 0); checked = $files.Count
  protected_unchanged = @($files | Where-Object { $_.role -eq 'protected' -and -not $_.changed }).Count
  changed = $changed; files = $files; new_test = $new; errors = $errors
}
$receipt | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $Output -Encoding utf8
$receipt | Select-Object ok,checked,protected_unchanged,changed,errors | Format-List
if ($errors.Count -gt 0) { exit 1 }
