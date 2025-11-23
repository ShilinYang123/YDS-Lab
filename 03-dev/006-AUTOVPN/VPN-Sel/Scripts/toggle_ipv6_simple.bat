@echo off
chcp 65001 >nul
echo AUTOVPN IPv6 Toggle Tool
echo ========================
echo.

:menu
echo Current IPv6 Status:
if exist "S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env" (
    findstr /C:"IPv6_ENABLE=" "S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env" >nul
    if %errorlevel% equ 0 (
        findstr /C:"IPv6_ENABLE=" "S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env"
    ) else (
        echo [ERROR] IPv6_ENABLE not found in config
    )
) else (
    echo [ERROR] Config file not found
)
echo.
echo Select operation:
echo 1. Enable IPv6 support
echo 2. Disable IPv6 support (IPv4 only)
echo 3. View current config
echo 4. Validate IPv6 config
echo 5. Exit
echo.

set /p choice=Enter option (1-5): 

if "%choice%"=="1" goto enable_ipv6
if "%choice%"=="2" goto disable_ipv6
if "%choice%"=="3" goto view_config
if "%choice%"=="4" goto validate_config
if "%choice%"=="5" goto end

echo [ERROR] Invalid input, please enter number 1-5
echo.
echo Press any key to return to menu...
pause > nul
cls
goto menu

:enable_ipv6
echo Enabling IPv6 support...
if exist "S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env" (
    powershell -Command "(Get-Content 'S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env') -replace 'IPv6_ENABLE=false', 'IPv6_ENABLE=true' | Set-Content 'S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env'"
    echo [SUCCESS] IPv6 enabled, please restart AUTOVPN service
    echo [WARNING] Please ensure server supports IPv6
) else (
    echo [ERROR] Config file not found
)
goto end

:disable_ipv6
echo Disabling IPv6 support...
if exist "S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env" (
    powershell -Command "(Get-Content 'S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env') -replace 'IPv6_ENABLE=true', 'IPv6_ENABLE=false' | Set-Content 'S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env'"
    echo [SUCCESS] IPv6 disabled, IPv4 mode only
    echo [SUCCESS] No service restart required, config active
) else (
    echo [ERROR] Config file not found
)
goto end

:view_config
echo Current IPv6 configuration:
if exist "S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env" (
    findstr /C:"IPv6_ENABLE=" "S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env"
) else (
    echo [ERROR] Config file not found
)
goto end

:validate_config
echo Validating IPv6 configuration...
if exist "S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\check_ipv6_config.py" (
    python "S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\check_ipv6_config.py"
) else (
    echo [WARNING] Validation script not found, checking config file
    if exist "S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env" (
    findstr /C:"IPv6_ENABLE=" "S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env"
    )
)
goto end

:end
echo.
echo Press any key to return to menu...
pause > nul
cls
goto menu