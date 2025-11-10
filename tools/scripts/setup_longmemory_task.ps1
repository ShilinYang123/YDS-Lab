param(
  [string]$TaskName = "YDS-LongMemory-HealthCheck",
  [string]$LogsRoot = "S:\YDS-Lab\01-struc\logs\longmemory",
  [string]$TraeLMPidFile = "S:\YDS-Lab\03-dev\001-memory-system\TraeLM\trae-lm.pid",
  [int]$Port = 8765,
  [string]$TestHost = "localhost"
)

$ErrorActionPreference = 'Stop'

$action = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument ('-NoProfile -ExecutionPolicy Bypass -File "S:\YDS-Lab\tools\LongMemory\health_check.ps1" -LogsRoot "' + $LogsRoot + '" -TraeLMPidFile "' + $TraeLMPidFile + '" -Port ' + $Port + ' -TestHost ' + $TestHost)
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 3650)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

try {
  if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
  }
} catch {}

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -Force | Out-Null
Write-Output "Task $TaskName created/updated to run health_check.ps1 every 30 minutes."