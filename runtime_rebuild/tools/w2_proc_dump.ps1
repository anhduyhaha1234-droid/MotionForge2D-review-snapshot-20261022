# Dump a process set to a text table: pid, ppid, name, workingset MB, cmdline.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File w2_proc_dump.ps1 -Pids 1,2,3 -Out C:\path\out.txt
#        powershell ... -File w2_proc_dump.ps1 -Filter python.exe -Out ...
param(
  [int[]]$Pids = @(),
  [string]$Filter = "",
  [string]$Out = ""
)
$ErrorActionPreference = "Stop"
if ($Filter -ne "") {
  $procs = Get-CimInstance Win32_Process -Filter "Name='$Filter'"
} else {
  $all = Get-CimInstance Win32_Process
  $procs = $all | Where-Object { $Pids -contains [int]$_.ProcessId }
}
$lines = @()
$lines += "pid`tppid`tname`tws_mb`tcmdline"
foreach ($p in ($procs | Sort-Object ProcessId)) {
  $ws = [math]::Round(([double]$p.WorkingSetSize) / 1MB, 1)
  $lines += ("{0}`t{1}`t{2}`t{3}`t{4}" -f $p.ProcessId, $p.ParentProcessId, $p.Name, $ws, $p.CommandLine)
}
$text = ($lines -join "`r`n") + "`r`n"
if ($Out -ne "") { Set-Content -LiteralPath $Out -Value $text -Encoding UTF8 }
Write-Output $text
