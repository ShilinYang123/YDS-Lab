Param(
  [int]$Tail = 120
)

$ErrorActionPreference = 'Continue'
$root = 'S:\YDS-Lab'
$tmp = Join-Path $root 'tmp'
$dailyRoot = Join-Path $root 'backups\\daily'

try {
  $logs = Get-ChildItem -Path $tmp -Force -Filter 'daily_backup_*.log' -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending
} catch {
  Write-Output "[Error] list logs: $($_.Exception.Message)"
  exit 1
}

if (-not $logs -or $logs.Count -eq 0) {
  Write-Output "No daily backup logs found in $tmp"
} else {
  $latest = $logs[0].FullName
  Write-Output "Latest backup log: $latest"
  if (Test-Path $latest) {
    try {
      Get-Content -Path $latest -Tail $Tail
    } catch {
      Write-Output "[Error] read log: $($_.Exception.Message)"
    }
  }
}

Write-Output "---"
Write-Output "Daily backup dir: $dailyRoot"
try {
  $zips = Get-ChildItem -Path $dailyRoot -Force -Filter '*.zip' -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending
  if ($zips -and $zips.Count -gt 0) {
    Write-Output "Latest zip files:"
    $zips | Select-Object -First 5 | ForEach-Object { $_.FullName }
  } else {
    Write-Output "No zip files found."
  }
} catch {
  Write-Output "[Error] list zips: $($_.Exception.Message)"
}

Write-Output "---"
try {
  $stagingDirs = Get-ChildItem -Path $tmp -Force -Directory -Filter 'backup_staging_*' -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending
  if ($stagingDirs -and $stagingDirs.Count -gt 0) {
    Write-Output "Latest staging dirs:"
    $stagingDirs | Select-Object -First 3 | ForEach-Object { $_.FullName }
  } else {
    Write-Output "No staging dirs found."
  }
} catch {
  Write-Output "[Error] list staging: $($_.Exception.Message)"
}