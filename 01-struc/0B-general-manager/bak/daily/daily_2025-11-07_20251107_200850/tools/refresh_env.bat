@echo off
chcp 65001 >nul
echo === Refresh Environment Variables ===
echo.

REM Refresh environment variables
echo Refreshing environment variables...
for /f "tokens=2*" %%i in ('reg query "HKEY_CURRENT_USER\Environment" /v PATH 2^>nul') do set "USER_PATH=%%j"
for /f "tokens=2*" %%i in ('reg query "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SYSTEM_PATH=%%j"

REM Merge PATH
set "PATH=%SYSTEM_PATH%;%USER_PATH%"

echo [OK] Environment variables refreshed
echo.

REM Test Git command
echo Testing Git command...
git --version 2>nul
if %errorlevel% equ 0 (
    echo [OK] Git command is now available!
) else (
    echo [ERROR] Git command still not available, may need to restart terminal
)

echo.
echo [INFO] If Git is still not available, please:
echo    1. Close current terminal and reopen
echo    2. Or re-login to Windows
echo.
pause