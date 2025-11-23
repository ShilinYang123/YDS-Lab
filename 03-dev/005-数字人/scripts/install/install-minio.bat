@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: MinIO安装脚本
:: 适用于Windows环境的MinIO安装

echo.
echo [MinIO] 开始安装MinIO...
echo.

:: 设置变量
set "MINIO_VERSION=RELEASE.2023-11-20T22-40-07Z"
set "DOWNLOAD_URL=https://dl.min.io/server/minio/release/windows-amd64/minio.exe"
set "MC_DOWNLOAD_URL=https://dl.min.io/client/mc/release/windows-amd64/mc.exe"
set "INSTALL_DIR=%~dp0..\..\services\minio"
set "DATA_DIR=%~dp0..\..\data\minio"
set "LOGS_DIR=%~dp0..\..\logs\minio"
set "CONFIG_DIR=%~dp0..\..\config\services"

:: 创建目录
echo [MinIO] 创建安装目录...
mkdir "%INSTALL_DIR%" 2>nul
mkdir "%DATA_DIR%" 2>nul
mkdir "%LOGS_DIR%" 2>nul
mkdir "%CONFIG_DIR%" 2>nul

:: 检查是否已安装 MinIO
echo [MinIO] 检查现有安装...
if exist "%INSTALL_DIR%\minio.exe" (
    echo MinIO 已安装，跳过安装步骤
    goto :configure_minio
)

:: 下载MinIO
echo [MinIO] 下载MinIO程序...
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%INSTALL_DIR%\minio.exe' -UseBasicParsing}"
if %errorlevel% neq 0 (
    echo 错误：下载MinIO失败！
    exit /b 1
)

:: 下载MinIO客户端
echo [MinIO] 下载MinIO客户端...
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%MC_DOWNLOAD_URL%' -OutFile '%INSTALL_DIR%\mc.exe' -UseBasicParsing}"
if %errorlevel% neq 0 (
    echo 警告：下载MinIO客户端失败，继续安装...
)

:: 配置MinIO
:configure_minio
echo [MinIO] 配置MinIO...

:: 创建启动脚本
echo [MinIO] 创建启动脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo.
echo [MinIO] 启动MinIO服务...
echo.
echo 数据目录：%DATA_DIR%
echo 日志目录：%LOGS_DIR%
echo.
echo 设置环境变量...
echo set MINIO_ROOT_USER=minioadmin
echo set MINIO_ROOT_PASSWORD=minioadmin123
echo set MINIO_BROWSER=on
echo set MINIO_CONSOLE_ADDRESS=:9001
echo set MINIO_API_ADDRESS=:9000
echo set MINIO_LOG_FILE=%LOGS_DIR%/minio.log
echo.
echo 正在启动MinIO...
echo.
echo "%~dp0..\..\services\minio\minio.exe" server "%DATA_DIR%" --console-address ":9001" --address ":9000"
echo.
echo MinIO服务已启动！
echo.
echo 访问地址：
echo   API地址：      http://localhost:9000
echo   控制台地址：   http://localhost:9001
echo.
echo 默认账号：
echo   用户名： minioadmin
echo   密码：   minioadmin123
echo.
echo 按 Ctrl+C 停止服务
echo.
) > "%~dp0..\..\services\minio\start-minio.bat"

:: 创建停止脚本
echo [MinIO] 创建停止脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo.
echo [MinIO] 停止MinIO服务...
echo.
echo 正在查找MinIO进程...
tasklist /FI "IMAGENAME eq minio.exe" 2^>nul ^| find /I /N "minio.exe"^>nul
if !errorlevel! == 0 (
    echo 正在停止MinIO服务...
    taskkill /F /IM minio.exe ^>nul 2^>nul
    echo MinIO服务已停止！
) else (
    echo MinIO服务未运行
)
echo.
echo MinIO服务已停止！
echo.
) > "%~dp0..\..\services\minio\stop-minio.bat"

:: 创建状态检查脚本
echo [MinIO] 创建状态检查脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo.
echo [MinIO] 检查MinIO状态...
echo.
echo 端口检查：
echo API端口 9000：
netstat -ano ^| findstr ":9000"
echo 控制台端口 9001：
netstat -ano ^| findstr ":9001"
echo.
echo 进程检查：
tasklist /FI "IMAGENAME eq minio.exe"
echo.
echo 服务检查：
if exist "%DATA_DIR%\.minio.sys" (
    echo MinIO 正在运行
echo 数据目录：%DATA_DIR%
) else (
    echo MinIO 未运行
)
echo.
echo 连接测试：
echo 测试API连接...
powershell -Command "& {try {$response = Invoke-WebRequest -Uri 'http://localhost:9000/minio/health/live' -UseBasicParsing; if ($response.StatusCode -eq 200) { Write-Host 'API连接正常' } else { Write-Host 'API连接异常' }} catch { Write-Host 'API连接失败' }}"
echo.
echo 测试控制台连接...
powershell -Command "& {try {$response = Invoke-WebRequest -Uri 'http://localhost:9001' -UseBasicParsing; if ($response.StatusCode -eq 200) { Write-Host '控制台连接正常' } else { Write-Host '控制台连接异常' }} catch { Write-Host '控制台连接失败' }}"
echo.
) > "%~dp0..\..\services\minio\status-minio.bat"

:: 创建初始化脚本
echo [MinIO] 创建初始化脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo.
echo [MinIO] 初始化MinIO配置...
echo.
echo 设置环境变量...
echo set MINIO_ROOT_USER=minioadmin
echo set MINIO_ROOT_PASSWORD=minioadmin123
echo.
echo 等待MinIO启动...
timeout /t 5 /nobreak ^>nul
echo.
echo 创建默认存储桶...
echo "%~dp0..\..\services\minio\mc.exe" alias set local http://localhost:9000 minioadmin minioadmin123
echo "%~dp0..\..\services\minio\mc.exe" mb local/digital-employee-dev --ignore-existing
echo "%~dp0..\..\services\minio\mc.exe" mb local/digital-employee-prod --ignore-existing
echo "%~dp0..\..\services\minio\mc.exe" mb local/user-uploads --ignore-existing
echo "%~dp0..\..\services\minio\mc.exe" mb local/system-backups --ignore-existing
echo.
echo 设置存储桶策略...
echo "%~dp0..\..\services\minio\mc.exe" anonymous set download local/digital-employee-dev
echo "%~dp0..\..\services\minio\mc.exe" anonymous set download local/user-uploads
echo.
echo MinIO初始化完成！
echo.
) > "%~dp0..\..\services\minio\init-minio.bat"

:: 设置环境变量
echo [MinIO] 配置环境变量...
setx MINIO_HOME "%INSTALL_DIR%" /M >nul 2>&1
setx PATH "%PATH%;%INSTALL_DIR%" /M >nul 2>&1
setx MINIO_ROOT_USER "minioadmin" /M >nul 2>&1
setx MINIO_ROOT_PASSWORD "minioadmin123" /M >nul 2>&1

echo.
echo [MinIO] MinIO %MINIO_VERSION% 安装完成！
echo.
echo 安装位置：%INSTALL_DIR%
echo 数据目录：%DATA_DIR%
echo 日志目录：%LOGS_DIR%
echo.
echo 使用方法：
echo   启动：   %INSTALL_DIR%\start-minio.bat
echo   停止：   %INSTALL_DIR%\stop-minio.bat
echo   状态：   %INSTALL_DIR%\status-minio.bat
echo   初始化： %INSTALL_DIR%\init-minio.bat
echo.
echo 访问地址：
echo   API地址：      http://localhost:9000
echo   控制台地址：   http://localhost:9001
echo.
echo 默认账号：
echo   用户名： minioadmin
echo   密码：   minioadmin123
echo.

endlocal
exit /b 0