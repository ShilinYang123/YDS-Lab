Param(
  [string]$ConfigPath = "S:\YDS-Lab\config\backup_config.json"
)

$ErrorActionPreference = 'Continue'
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'  # 符合要求：YYYYMMDD-HHmmss
$root = "S:\YDS-Lab"
$dailyRoot = Join-Path $root 'backups\daily'
$zipPath = Join-Path $dailyRoot ($ts + '.zip')
$log = Join-Path $root ("tmp\daily_backup_" + $ts + ".log")
$staging = Join-Path $root ("tmp\backup_staging_" + $ts)

# 默认配置
$retentionDays = 14
$sources = @('01-struc','02-task','03-dev','04-prod','config','docs')
# 可配置的排除（默认值）
$defaultExcludeDirs = @('backups','backup','bak','tmp','coverage','lcov','lcov-report','node_modules','.git','.trae')
$defaultExcludeFiles = @('*.zip')
$globalExcludeDirs = @()
$globalExcludeFiles = @()

try {
  if (Test-Path $ConfigPath) {
    $cfg = Get-Content $ConfigPath -Raw | ConvertFrom-Json
    if ($cfg.retentionDays) { $retentionDays = [int]$cfg.retentionDays }
    if ($cfg.sources) { $sources = $cfg.sources }
    if ($cfg.globalExcludeDirs) { $globalExcludeDirs = @($cfg.globalExcludeDirs) }
    if ($cfg.globalExcludeFiles) { $globalExcludeFiles = @($cfg.globalExcludeFiles) }
  }
} catch {
  "[Warn] 读取配置失败，采用默认值：retentionDays=$retentionDays" | Tee-Object -FilePath $log | Out-Null
}

New-Item -ItemType Directory -Path $dailyRoot -Force | Out-Null
New-Item -ItemType Directory -Path $staging -Force | Out-Null
"[Start] daily backup to $zipPath (staging: $staging)" | Tee-Object -FilePath $log | Out-Null

foreach ($s in $sources) {
  # 允许 sources 为绝对或相对路径，支持对象形式：{ path, excludeDirs, excludeFiles }
  $srcPath = $null
  $perExcludeDirs = @()
  $perExcludeFiles = @()
  if ($s -is [string]) {
    if ([System.IO.Path]::IsPathRooted($s)) { $srcPath = $s } else { $srcPath = Join-Path $root $s }
  } else {
    # PSCustomObject
    $p = $s.path
    if ([System.IO.Path]::IsPathRooted($p)) { $srcPath = $p } else { $srcPath = Join-Path $root $p }
    if ($s.PSObject.Properties.Name -contains 'excludeDirs' -and $s.excludeDirs) { $perExcludeDirs = @($s.excludeDirs) }
    if ($s.PSObject.Properties.Name -contains 'excludeFiles' -and $s.excludeFiles) { $perExcludeFiles = @($s.excludeFiles) }
  }

  $leaf = Split-Path -Path $srcPath -Leaf
  $dstPath = Join-Path $staging $leaf
  New-Item -ItemType Directory -Path $dstPath -Force | Out-Null
  if (Test-Path $srcPath) {
    "[Copy] $srcPath -> $dstPath" | Tee-Object -Append -FilePath $log | Out-Null
    # 组装排除参数（全局 + 默认 + 逐源覆盖）
    $xd = ($defaultExcludeDirs + $globalExcludeDirs + $perExcludeDirs) | Where-Object { $_ -and $_.ToString().Trim() -ne '' } | Select-Object -Unique
    $xf = ($defaultExcludeFiles + $globalExcludeFiles + $perExcludeFiles) | Where-Object { $_ -and $_.ToString().Trim() -ne '' } | Select-Object -Unique
    $args = @($srcPath, $dstPath, '/E','/R:2','/W:2','/MT:16','/NFL','/NDL','/NP')
    if ($xd.Count -gt 0) { $args += '/XD'; $args += $xd }
    if ($xf.Count -gt 0) { $args += '/XF'; $args += $xf }
    & robocopy @args |
      Tee-Object -Append -FilePath $log | Out-Null
  } else {
    "[Skip] not found: $srcPath" | Tee-Object -Append -FilePath $log | Out-Null
  }
}

# Zip to single file and remove staging
try {
  "[Zip] -> $zipPath" | Tee-Object -Append -FilePath $log | Out-Null
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  [System.IO.Compression.ZipFile]::CreateFromDirectory($staging, $zipPath)
  try {
    Remove-Item -LiteralPath $staging -Recurse -Force -ErrorAction Stop
  } catch {
    "[Warn] remove staging failed, fallback to CMD RD: $($_.Exception.Message)" | Tee-Object -Append -FilePath $log | Out-Null
    Start-Process -FilePath cmd.exe -ArgumentList '/c','rd','/s','/q', $staging -NoNewWindow -Wait
  }
  "[ZipDone] $zipPath" | Tee-Object -Append -FilePath $log | Out-Null
} catch {
  "[Error] zip: $($_.Exception.Message)" | Tee-Object -Append -FilePath $log | Out-Null
}

# 保留策略：清理超期的 daily ZIP
"[Retention] keep last $retentionDays days" | Tee-Object -Append -FilePath $log | Out-Null
$cutoff = (Get-Date).AddDays(-$retentionDays)
if (Test-Path $dailyRoot) {
  $oldZips = Get-ChildItem -Path $dailyRoot -File -Filter '*.zip' -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt $cutoff }
  foreach ($oz in $oldZips) {
    try {
      Remove-Item -LiteralPath $oz.FullName -Force
      "[Prune] removed $($oz.FullName)" | Tee-Object -Append -FilePath $log | Out-Null
    } catch {
      "[Error] prune $($oz.FullName): $($_.Exception.Message)" | Tee-Object -Append -FilePath $log | Out-Null
    }
  }
}

"[Done] daily backup completed" | Tee-Object -Append -FilePath $log | Out-Null
Write-Output "Log: $log"