$action = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument '-NoProfile -ExecutionPolicy Bypass -File "S:\YDS-Lab\tools\LongMemory\health_check.ps1" -LogsRoot "S:\YDS-Lab\01-struc\logs\longmemory" -TraeLMPidFile "S:\YDS-Lab\03-dev\001-memory-system\TraeLM\trae-lm.pid" -Port 8765 -TestHost localhost'
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 3650)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "TraeLM-HealthCheck" -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -Force | Out-Null
Write-Output "Task TraeLM-HealthCheck created/updated with extended metrics."