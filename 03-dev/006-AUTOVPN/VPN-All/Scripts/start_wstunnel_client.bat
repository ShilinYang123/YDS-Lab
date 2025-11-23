@echo off
echo Starting wstunnel client...

REM 从config.env读取配置参数
for /f "tokens=1,2 delims==" %%a in (config.env) do (
    if "%%a"=="WSTUNNEL_PORT" set WSTUNNEL_PORT=%%b
    if "%%a"=="SERVER_RESTRICT_PORT" set SERVER_RESTRICT_PORT=%%b
    if "%%a"=="SERVER_IP" set SERVER_IP=%%b
    if "%%a"=="SERVER_PORT" set SERVER_PORT=%%b
)

REM 设置默认值
if "%WSTUNNEL_PORT%"=="" set WSTUNNEL_PORT=1081
if "%SERVER_RESTRICT_PORT%"=="" set SERVER_RESTRICT_PORT=8443
if "%SERVER_IP%"=="" set SERVER_IP=192.210.206.52
if "%SERVER_PORT%"=="" set SERVER_PORT=443

REM 使用配置参数启动wstunnel
S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-All\Scripts\wstunnel.exe --log-lvl DEBUG client -L udp://127.0.0.1:%WSTUNNEL_PORT%:127.0.0.1:%SERVER_RESTRICT_PORT% ws://%SERVER_IP%:%SERVER_PORT%

echo.
echo wstunnel client exited. Press any key to close window.
pause >nul