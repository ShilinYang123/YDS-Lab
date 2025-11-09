Param(
  [int]$ThresholdDays = 60
)

$ErrorActionPreference = 'Continue'
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$root = "S:\YDS-Lab"
$src = Join-Path $root 'backups\manual'
$dst = Join-Path $root 'backups\legacy'
$log = Join-Path $root ("tmp\legacy_migrate_" + $ts + ".log")

New-Item -ItemType Directory -Path $dst -Force | Out-Null
"[Start] legacy migrate from $src to $dst (threshold: $ThresholdDays days)" | Tee-Object -FilePath $log | Out-Null

if (-not (Test-Path $src)) {
  "[Skip] source not found: $src" | Tee-Object -Append -FilePath $log | Out-Null
  Write-Output "Log: $log"
  exit 0
}

$cutoff = (Get-Date).AddDays(-$ThresholdDays)
$items = Get-ChildItem -Path $src -Directory -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt $cutoff }

foreach ($it in $items) {
  try {
    $dateFolder = (Get-Date $it.LastWriteTime -Format 'yyyyMMdd')
    $targetFolder = Join-Path $dst ("d_" + $dateFolder)
    New-Item -ItemType Directory -Path $targetFolder -Force | Out-Null
    $destPath = Join-Path $targetFolder $it.Name
    "[Move] $($it.FullName) -> $destPath" | Tee-Object -Append -FilePath $log | Out-Null
    Move-Item -LiteralPath $it.FullName -Destination $destPath -Force
  } catch {
    "[Error] move $($it.FullName): $($_.Exception.Message)" | Tee-Object -Append -FilePath $log | Out-Null
  }
}

"[Done] legacy migrate completed" | Tee-Object -Append -FilePath $log | Out-Null
Write-Output "Log: $log"