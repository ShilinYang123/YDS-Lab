@echo off
REM TraeLM 30s metrics fast loop runner
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "S:\YDS-Lab\03-dev\001-memory-system\TraeLM\tools\LongMemory\metrics_fast.ps1" -IntervalSec 30 -TraeLMPidFile "S:\YDS-Lab\03-dev\001-memory-system\TraeLM\traelm.pid"