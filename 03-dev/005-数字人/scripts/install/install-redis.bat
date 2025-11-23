@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: Redis安装脚本
:: 适用于Windows环境的Redis安装

echo.
echo [Redis] 开始安装Redis...
echo.

:: 设置变量
set "REDIS_VERSION=7.2.3"
set "DOWNLOAD_URL=https://github.com/tporadowski/redis/releases/download/v7.2.3/Redis-x64-7.2.3.zip"
set "INSTALL_DIR=%~dp0..\..\services\redis"
set "DATA_DIR=%~dp0..\..\data\redis"
set "LOGS_DIR=%~dp0..\..\logs\redis"
set "CONFIG_DIR=%~dp0..\..\config\services"

:: 创建目录
echo [Redis] 创建安装目录...
mkdir "%INSTALL_DIR%" 2>nul
mkdir "%DATA_DIR%" 2>nul
mkdir "%LOGS_DIR%" 2>nul
mkdir "%CONFIG_DIR%" 2>nul

:: 检查是否已安装 Redis
echo [Redis] 检查现有安装...
if exist "%INSTALL_DIR%\redis-server.exe" (
    echo Redis 已安装，跳过安装步骤
    goto :configure_redis
)

:: 下载Redis安装包
echo [Redis] 下载安装包...
set "INSTALLER_PATH=%TEMP%\redis-x64-%REDIS_VERSION%.zip"

if not exist "%INSTALLER_PATH%" (
    echo 正在下载Redis %REDIS_VERSION%...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%INSTALLER_PATH%' -UseBasicParsing}"
    if %errorlevel% neq 0 (
        echo 错误：下载Redis失败！
        exit /b 1
    )
)

:: 解压Redis
echo [Redis] 解压安装文件...
powershell -Command "& {Expand-Archive -Path '%INSTALLER_PATH%' -DestinationPath '%INSTALL_DIR%' -Force}"
if %errorlevel% neq 0 (
    echo 错误：解压Redis失败！
    exit /b 1
)

:: 配置Redis
:configure_redis
echo [Redis] 配置Redis...

:: 创建Redis配置文件
echo [Redis] 创建配置文件...
(
echo # Redis 配置文件
echo port 6379
echo bind 127.0.0.1
echo protected-mode yes
echo timeout 0
echo tcp-keepalive 300
echo daemonize no
echo supervised no
echo pidfile "%DATA_DIR%/redis.pid"
echo loglevel notice
echo logfile "%LOGS_DIR%/redis.log"
echo databases 16
echo save 900 1
echo save 300 10
echo save 60 10000
echo stop-writes-on-bgsave-error yes
echo rdbcompression yes
echo rdbchecksum yes
echo dbfilename dump.rdb
echo dir "%DATA_DIR%"
echo replica-serve-stale-data yes
echo replica-read-only yes
echo repl-diskless-sync no
echo repl-diskless-sync-delay 5
echo repl-disable-tcp-nodelay no
echo replica-priority 100
echo maxmemory 256mb
echo maxmemory-policy allkeys-lru
echo appendonly yes
echo appendfilename "appendonly.aof"
echo appendfsync everysec
echo no-appendfsync-on-rewrite no
echo auto-aof-rewrite-percentage 100
echo auto-aof-rewrite-min-size 64mb
echo aof-load-truncated yes
echo aof-use-rdb-preamble yes
echo lua-time-limit 5000
echo slowlog-log-slower-than 10000
echo slowlog-max-len 128
echo latency-monitor-threshold 0
echo notify-keyspace-events ""
echo hash-max-ziplist-entries 512
echo hash-max-ziplist-value 64
echo list-max-ziplist-size -2
echo list-compress-depth 0
echo set-max-intset-entries 512
echo zset-max-ziplist-entries 128
echo zset-max-ziplist-value 64
echo hll-sparse-max-bytes 3000
echo stream-node-max-bytes 4096
echo stream-node-max-entries 100
echo activerehashing yes
echo client-output-buffer-limit normal 0 0 0
echo client-output-buffer-limit replica 256mb 64mb 60
echo client-output-buffer-limit pubsub 32mb 8mb 60
echo hz 10
echo dynamic-hz yes
echo aof-rewrite-incremental-fsync yes
echo rdb-save-incremental-fsync yes
echo jemalloc-bg-thread yes
) > "%CONFIG_DIR%\redis.conf"

:: 创建启动脚本
echo [Redis] 创建启动脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo.
echo [Redis] 启动Redis服务...
echo.
echo 数据目录：%DATA_DIR%
echo 日志目录：%LOGS_DIR%
echo.
echo 正在启动Redis...
echo.
echo "%~dp0..\..\services\redis\redis-server.exe" "%CONFIG_DIR%\redis.conf"
echo.
echo Redis服务已启动！
echo 日志文件位置：%LOGS_DIR%
echo.
echo 按 Ctrl+C 停止服务
echo.
) > "%~dp0..\..\services\redis\start-redis.bat"

:: 创建停止脚本
echo [Redis] 创建停止脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo.
echo [Redis] 停止Redis服务...
echo.
echo 正在查找Redis进程...
tasklist /FI "IMAGENAME eq redis-server.exe" 2^>nul ^| find /I /N "redis-server.exe"^>nul
if !errorlevel! == 0 (
    echo 正在停止Redis服务...
    taskkill /F /IM redis-server.exe ^>nul 2^>nul
    echo Redis服务已停止！
) else (
    echo Redis服务未运行
echo.
echo Redis服务已停止！
echo.
) > "%~dp0..\..\services\redis\stop-redis.bat"

:: 创建状态检查脚本
echo [Redis] 创建状态检查脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo.
echo [Redis] 检查Redis状态...
echo.
echo 端口检查：
netstat -ano ^| findstr ":6379"
echo.
echo 进程检查：
tasklist /FI "IMAGENAME eq redis-server.exe"
echo.
echo 服务检查：
if exist "%DATA_DIR%\redis.pid" (
    echo Redis 正在运行
echo 数据目录：%DATA_DIR%
) else (
    echo Redis 未运行
)
echo.
echo 连接测试：
echo "%~dp0..\..\services\redis\redis-cli.exe" ping
echo.
) > "%~dp0..\..\services\redis\status-redis.bat"

:: 设置环境变量
echo [Redis] 配置环境变量...
setx REDIS_HOME "%INSTALL_DIR%" /M >nul 2>&1
setx PATH "%PATH%;%INSTALL_DIR%" /M >nul 2>&1

echo.
echo [Redis] Redis %REDIS_VERSION% 安装完成！
echo.
echo 安装位置：%INSTALL_DIR%
echo 数据目录：%DATA_DIR%
echo 日志目录：%LOGS_DIR%
echo 配置文件：%CONFIG_DIR%\redis.conf
echo.
echo 使用方法：
echo   启动：   %INSTALL_DIR%\start-redis.bat
echo   停止：   %INSTALL_DIR%\stop-redis.bat
echo   状态：   %INSTALL_DIR%\status-redis.bat
echo.
echo 连接信息：
echo   主机： localhost
echo   端口： 6379
echo   密码： 无
echo.

endlocal
exit /b 0