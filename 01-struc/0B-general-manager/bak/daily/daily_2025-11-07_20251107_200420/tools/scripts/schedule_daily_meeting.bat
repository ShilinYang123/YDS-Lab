@echo off
setlocal
set SCRIPT_DIR=%~dp0
set REPO_DIR=%SCRIPT_DIR%..

REM 调用 PowerShell 脚本执行每日晨会
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%schedule_daily_meeting.ps1" %*

endlocal
exit /b %ERRORLEVEL%