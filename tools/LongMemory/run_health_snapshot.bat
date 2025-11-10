@echo off
REM TraeLM 5-minute health snapshot runner (修订：公司级日志根 01-struc\logs\longmemory)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "S:\YDS-Lab\tools\LongMemory\health_check.ps1" -LogsRoot "S:\YDS-Lab\01-struc\logs\longmemory" -TraeLMPidFile "S:\YDS-Lab\03-dev\001-memory-system\TraeLM\trae-lm.pid"