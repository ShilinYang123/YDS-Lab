param(
  [int]$Tail = 40
)

$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path "$PSScriptRoot/../..").Path
$LogDir = Join-Path $RepoRoot 'docs/系统维护'
$hb = Join-Path $RepoRoot 'LongMemory/heartbeat.txt'

if (-not (Test-Path $LogDir)) {
  Write-Output "LogDir not found: $LogDir"
  exit 0
}

$latest = Get-ChildItem -Path $LogDir -Filter 'LongMemory_健康检查日志_*.txt' -File |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

if ($latest) {
  Write-Output ("LogFile: " + $latest.FullName)
  Get-Content -Path $latest.FullName -Tail $Tail
} else {
  Write-Output 'No log found.'
}

if (Test-Path $hb) {
  Write-Output ("Heartbeat: " + $hb)
  Get-Content -Path $hb -Tail 5
} else {
  Write-Output 'Heartbeat not found.'
}