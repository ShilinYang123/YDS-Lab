Param(
  [int]$Tail = 1
)

$ErrorActionPreference = 'Continue'
$base = 'S:\YDS-Lab\01-struc\logs\longmemory\health'

if (-not (Test-Path $base)) {
  Write-Output "Health dir not found: $base"
  exit 1
}

try {
  $f = Get-ChildItem -Path $base -Filter 'health_*.jsonl' -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
} catch {
  Write-Output "[Error] list health files: $($_.Exception.Message)"
  exit 1
}

if (-not $f) {
  Write-Output 'No health jsonl files found.'
  exit 0
}

Write-Output ("Latest health file: " + $f.FullName)
try {
  Get-Content -Path $f.FullName -Tail $Tail
} catch {
  Write-Output "[Error] read latest: $($_.Exception.Message)"
}