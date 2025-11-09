param(
  [string]$RunMode = "Manual"
)

# LongMemory 健康检查脚本
# 目标：定期巡检长记忆系统（目录存在性、心跳、磁盘空间、计划任务状态），并生成日志。

$ErrorActionPreference = 'Stop'

# 全局日志文件路径（在 try 中初始化）
$script:LogFile = $null

function Write-Log([string]$msg) {
  $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $msg"
  Write-Output $line
  if ($script:LogFile) {
    try { Add-Content -Path $script:LogFile -Value $line } catch {}
  }
}

try {
  # 仓库根目录（脚本位于 tools/scripts）
  $RepoRoot = (Resolve-Path "$PSScriptRoot/../..").Path
  $Timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  $LogDir = Join-Path $RepoRoot 'docs/系统维护'
  if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
  $script:LogFile = Join-Path $LogDir "LongMemory_健康检查日志_$Timestamp.txt"

  Write-Log "开始 LongMemory 健康检查 (RunMode=$RunMode)"

  # 载入或创建配置
  $ConfigPath = Join-Path $RepoRoot 'config/long_memory_config.json'
  if (-not (Test-Path $ConfigPath)) {
    $defaultCfg = @{ 
      storeDirs = @('LongMemory', '.trae/memory');
      heartbeatFile = 'LongMemory/heartbeat.txt';
      diskSpaceThresholdGB = 2;
      maxLogDays = 60;
      autoFix = $true
    } | ConvertTo-Json -Depth 5
    $cfgDir = Split-Path $ConfigPath -Parent
    if (-not (Test-Path $cfgDir)) { New-Item -ItemType Directory -Path $cfgDir -Force | Out-Null }
    Set-Content -Path $ConfigPath -Value $defaultCfg -Encoding UTF8
    Write-Log "配置文件缺失，已生成默认配置：$ConfigPath"
  }

  $cfg = Get-Content -Raw -Path $ConfigPath | ConvertFrom-Json

  # 解析路径为绝对路径
  $storeDirs = @()
  foreach ($d in $cfg.storeDirs) {
    if ([System.IO.Path]::IsPathRooted($d)) {
      $storeDirs += $d
    } else {
      $storeDirs += (Join-Path $RepoRoot $d)
    }
  }

  if ([System.IO.Path]::IsPathRooted($cfg.heartbeatFile)) {
    $HeartbeatFile = $cfg.heartbeatFile
  } else {
    $HeartbeatFile = Join-Path $RepoRoot $cfg.heartbeatFile
  }

  # 检查磁盘空间
  $drive = Split-Path -Qualifier $RepoRoot # e.g. 'S:'
  $driveLetter = $drive.TrimEnd(':')
  try {
    $disk = Get-CimInstance -ClassName Win32_LogicalDisk -Filter "DeviceID='$drive'"
    $freeGB = [math]::Round(($disk.FreeSpace / 1GB), 2)
    $totalGB = [math]::Round(($disk.Size / 1GB), 2)
    Write-Log "磁盘空间：$drive 总计=${totalGB}GB，剩余=${freeGB}GB，阈值=${cfg.diskSpaceThresholdGB}GB"
    if ($freeGB -lt [double]$cfg.diskSpaceThresholdGB) {
      Write-Log "警告：剩余磁盘空间低于阈值！"
    }
  } catch {
    Write-Log "磁盘空间检查失败：$($_.Exception.Message)"
  }

  # 检查/创建存储目录
  foreach ($dir in $storeDirs) {
    if (-not (Test-Path $dir)) {
      if ($cfg.autoFix) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Log "存储目录不存在，已创建：$dir"
      } else {
        Write-Log "存储目录缺失：$dir"
      }
    } else {
      Write-Log "存储目录存在：$dir"
    }
  }

  # 写入心跳
  $hbDir = Split-Path $HeartbeatFile -Parent
  if (-not (Test-Path $hbDir)) { New-Item -ItemType Directory -Path $hbDir -Force | Out-Null }
  $hbLine = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] HealthCheck PASS | RunMode=$RunMode"
  Add-Content -Path $HeartbeatFile -Value $hbLine
  Write-Log "心跳写入：$HeartbeatFile"

  # 计划任务状态（如果权限允许）
  try {
    $task = Get-ScheduledTask -TaskName 'YDS-LongMemory-HealthCheck' -ErrorAction Stop
    $next = $task.NextRunTime
    $state = $task.State
    Write-Log "计划任务存在：YDS-LongMemory-HealthCheck | 状态=$state | 下次运行=$next"
  } catch {
    Write-Log "计划任务查询失败或不存在：$($_.Exception.Message)"
  }

  # 清理历史日志（根据 maxLogDays）
  $maxDays = [int]$cfg.maxLogDays
  try {
    Get-ChildItem -Path $LogDir -Filter 'LongMemory_健康检查日志_*.txt' -File | Where-Object {
      $_.LastWriteTime -lt (Get-Date).AddDays(-$maxDays)
    } | ForEach-Object { Remove-Item -Path $_.FullName -Force }
    Write-Log "历史日志清理完成（超过 $maxDays 天的记录）"
  } catch {
    Write-Log "历史日志清理失败：$($_.Exception.Message)"
  }

  Write-Log "LongMemory 健康检查完成"
  exit 0
} catch {
  $err = $_.Exception.Message
  try {
    if ($script:LogFile) { Add-Content -Path $script:LogFile -Value "[ERROR] $err" }
  } catch {}
  Write-Output "[ERROR] $err"
  exit 1
}