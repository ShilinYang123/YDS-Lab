Param(
  [string]$Project = "DeWatermark AI",
  [string]$Model = "qwen2:0.5b",
  [string]$ActionsModel = $null,
  [string]$Participants = $null,
  [string]$Agenda = $null,
  [string]$ProjectId = $null
)

$ErrorActionPreference = 'Stop'

# 计算路径
$repoRoot = Split-Path -Parent $PSScriptRoot
$timestamp = Get-Date -Format "yyyyMMdd-HHmm"
$logsDir = Join-Path $repoRoot "01-struc/0B-general-manager/logs"
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
$logFile = Join-Path $logsDir ("daily_meeting_" + $timestamp + ".log")

# 组装命令行
$python = "python"
$argsList = @("tools/agents/run_collab.py", "--meeting", "daily", "--project", $Project, "--model", $Model)
if ($ActionsModel) { $argsList += @("--actions-model", $ActionsModel) }
if ($Participants) { $argsList += @("--participants", $Participants) }
if ($Agenda) { $argsList += @("--agenda", $Agenda) }
if ($ProjectId) { $argsList += @("--project-id", $ProjectId) }

Push-Location $repoRoot
try {
  Write-Host "[schedule] Running: $python $($argsList -join ' ')"
  & $python $argsList 2>&1 | Tee-Object -FilePath $logFile
  Write-Host "[schedule] Output logged to $logFile"
}
catch {
  Write-Error "[schedule] Failed: $_"
}
finally {
  Pop-Location
}