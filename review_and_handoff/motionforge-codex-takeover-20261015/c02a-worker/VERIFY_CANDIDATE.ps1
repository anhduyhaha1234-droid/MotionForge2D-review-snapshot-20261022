param(
  [Parameter(Mandatory=$true)][string]$Manifest,
  [Parameter(Mandatory=$true)][string]$Output
)
$m = Get-Content -LiteralPath $Manifest -Raw | ConvertFrom-Json
$errors = @()
foreach ($item in $m.files) {
  foreach ($path in @($item.source, $item.snapshot)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
      $errors += "missing $path"
      continue
    }
    $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne $item.sha256) { $errors += "file hash mismatch $path" }
    if ((Get-Item -LiteralPath $path).Length -ne $item.bytes) { $errors += "file size mismatch $path" }
    if ([IO.File]::ReadAllLines($path).Length -ne $item.lines) { $errors += "line count mismatch $path" }
  }
}
foreach ($item in @($m.diffs) + @($m.receipts)) {
  if (-not (Test-Path -LiteralPath $item.path -PathType Leaf)) {
    $errors += "missing evidence $($item.path)"
  } elseif ((Get-FileHash -LiteralPath $item.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256) {
    $errors += "evidence hash mismatch $($item.path)"
  }
}
if ((Get-FileHash -LiteralPath $m.preflight -Algorithm SHA256).Hash.ToLowerInvariant() -ne $m.preflight_sha256) {
  $errors += 'preflight hash mismatch'
}
$result = [pscustomobject]@{
  ok = ($errors.Count -eq 0)
  manifest = $Manifest
  manifest_sha256 = (Get-FileHash -LiteralPath $Manifest -Algorithm SHA256).Hash.ToLowerInvariant()
  files = $m.files.Count; diffs = $m.diffs.Count; receipts = $m.receipts.Count
  errors = $errors
}
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $Output -Encoding utf8
$result | Format-List
if ($errors.Count -gt 0) { exit 1 }
exit 0
