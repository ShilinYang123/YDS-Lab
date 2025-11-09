@echo off
REM TraeLM 5-minute health snapshot runner
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "S:\YDS-Lab\03-dev\001-memory-system\TraeLM\tools\LongMemory\health_check.ps1" -TraeLMPidFile "S:\YDS-Lab\03-dev\001-memory-system\TraeLM\traelm.pid"