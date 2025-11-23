@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: PostgreSQL安装脚本
:: 适用于Windows环境的PostgreSQL安装

echo.
echo [PostgreSQL] 开始安装PostgreSQL...
echo.

:: 设置变量
set "POSTGRES_VERSION=15.4-1"
set "POSTGRES_MAJOR=15"
set "DOWNLOAD_URL=https://get.enterprisedb.com/postgresql/postgresql-15.4-1-windows-x64.exe"
set "INSTALL_DIR=%~dp0..\..\services\postgresql"
set "DATA_DIR=%~dp0..\..\data\postgres"
set "LOGS_DIR=%~dp0..\..\logs\postgres"
set "CONFIG_DIR=%~dp0..\..\config\services"

:: 创建目录
echo [PostgreSQL] 创建安装目录...
mkdir "%INSTALL_DIR%" 2>nul
mkdir "%DATA_DIR%" 2>nul
mkdir "%LOGS_DIR%" 2>nul
mkdir "%CONFIG_DIR%" 2>nul

:: 检查是否已安装 PostgreSQL
echo [PostgreSQL] 检查现有安装...
if exist "%INSTALL_DIR%\pgsql-%POSTGRES_MAJOR%\bin\postgres.exe" (
    echo PostgreSQL %POSTGRES_MAJOR% 已安装，跳过安装步骤
    goto :configure_postgres
)

:: 下载PostgreSQL安装程序
echo [PostgreSQL] 下载安装程序...
set "INSTALLER_PATH=%TEMP%\postgresql-%POSTGRES_VERSION%-windows-x64.exe"

if not exist "%INSTALLER_PATH%" (
    echo 正在下载PostgreSQL %POSTGRES_VERSION%...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%INSTALLER_PATH%' -UseBasicParsing}"
    if %errorlevel% neq 0 (
        echo 错误：下载PostgreSQL失败！
        exit /b 1
    )
)

:: 解压安装程序（使用zip版本）
echo [PostgreSQL] 解压安装文件...
powershell -Command "& {Expand-Archive -Path '%INSTALLER_PATH%' -DestinationPath '%INSTALL_DIR%' -Force}"
if %errorlevel% neq 0 (
    echo 错误：解压PostgreSQL失败！
    exit /b 1
)

:: 配置PostgreSQL
:configure_postgres
echo [PostgreSQL] 配置PostgreSQL...

:: 创建PostgreSQL配置文件
echo [PostgreSQL] 创建配置文件...
(
echo # PostgreSQL 配置文件
echo listen_addresses = '*'
echo port = 5432
echo max_connections = 100
echo shared_buffers = 128MB
echo effective_cache_size = 512MB
echo maintenance_work_mem = 32MB
echo checkpoint_completion_target = 0.9
echo wal_buffers = 16MB
echo default_statistics_target = 100
echo random_page_cost = 1.1
echo effective_io_concurrency = 200
echo work_mem = 4MB
echo min_wal_size = 1GB
echo max_wal_size = 4GB
echo log_destination = 'stderr'
echo logging_collector = on
echo log_directory = '%LOGS_DIR%'
echo log_filename = 'postgresql-%%Y-%%m-%%d_%%H%%M%%S.log'
echo log_rotation_age = 1d
echo log_rotation_size = 100MB
echo log_min_duration_statement = 1000
echo log_line_prefix = '%%t [%%p]: [%%l-1] user=%%u,db=%%d,app=%%a,client=%%h '
echo log_checkpoints = on
echo log_connections = on
echo log_disconnections = on
echo log_lock_waits = on
echo log_temp_files = 0
echo lc_messages = 'en_US.UTF-8'
echo lc_monetary = 'en_US.UTF-8'
echo lc_numeric = 'en_US.UTF-8'
echo lc_time = 'en_US.UTF-8'
echo default_text_search_config = 'pg_catalog.english'
) > "%CONFIG_DIR%\postgresql.conf"

:: 创建pg_hba.conf文件
echo [PostgreSQL] 创建认证配置...
(
echo # PostgreSQL Client Authentication Configuration
echo local   all             all                                     trust
echo host    all             all             127.0.0.1/32            trust
echo host    all             all             ::1/128                 trust
echo host    all             all             0.0.0.0/0               md5
echo local   replication     all                                     trust
echo host    replication     all             127.0.0.1/32            trust
echo host    replication     all             ::1/128                 trust
) > "%CONFIG_DIR%\pg_hba.conf"

:: 初始化数据库
echo [PostgreSQL] 初始化数据库...
if not exist "%DATA_DIR%\PG_VERSION" (
    echo 正在初始化数据库集群...
    "%INSTALL_DIR%\pgsql-%POSTGRES_MAJOR%\bin\initdb.exe" -D "%DATA_DIR%" -U postgres --encoding=UTF8 --locale=en_US.UTF-8
    if %errorlevel% neq 0 (
        echo 错误：数据库初始化失败！
        exit /b 1
    )
)

:: 创建启动脚本
echo [PostgreSQL] 创建启动脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo.
echo [PostgreSQL] 启动PostgreSQL服务...
echo.
echo 数据目录：%DATA_DIR%
echo 日志目录：%LOGS_DIR%
echo.
echo 正在启动PostgreSQL...
echo.
echo "%~dp0..\..\services\postgresql\pgsql-%POSTGRES_MAJOR%\bin\postgres.exe" -D "%DATA_DIR%" -c config_file="%~dp0..\..\config\services\postgresql.conf"
echo.
echo PostgreSQL服务已启动！
echo 日志文件位置：%LOGS_DIR%
echo.
echo 按 Ctrl+C 停止服务
echo.
) > "%~dp0..\..\services\postgresql\start-postgres.bat"

:: 创建停止脚本
echo [PostgreSQL] 创建停止脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo.
echo [PostgreSQL] 停止PostgreSQL服务...
echo.
echo 正在查找PostgreSQL进程...
tasklist /FI "IMAGENAME eq postgres.exe" 2^>nul ^| find /I /N "postgres.exe"^>nul
echo.
echo PostgreSQL服务已停止！
echo.
) > "%~dp0..\..\services\postgresql\stop-postgres.bat"

:: 创建状态检查脚本
echo [PostgreSQL] 创建状态检查脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo.
echo [PostgreSQL] 检查PostgreSQL状态...
echo.
echo 端口检查：
netstat -ano ^| findstr ":5432"
echo.
echo 进程检查：
tasklist /FI "IMAGENAME eq postgres.exe"
echo.
echo 服务检查：
if exist "%DATA_DIR%\postmaster.pid" (
    echo PostgreSQL 正在运行
echo 数据目录：%DATA_DIR%
) else (
    echo PostgreSQL 未运行
)
echo.
) > "%~dp0..\..\services\postgresql\status-postgres.bat"

:: 设置环境变量
echo [PostgreSQL] 配置环境变量...
setx POSTGRES_HOME "%INSTALL_DIR%\pgsql-%POSTGRES_MAJOR%" /M >nul 2>&1
setx PATH "%PATH%;%INSTALL_DIR%\pgsql-%POSTGRES_MAJOR%\bin" /M >nul 2>&1

echo.
echo [PostgreSQL] PostgreSQL %POSTGRES_VERSION% 安装完成！
echo.
echo 安装位置：%INSTALL_DIR%\pgsql-%POSTGRES_MAJOR%
echo 数据目录：%DATA_DIR%
echo 日志目录：%LOGS_DIR%
echo 配置文件：%CONFIG_DIR%\postgresql.conf
echo.
echo 使用方法：
echo   启动：   %INSTALL_DIR%\start-postgres.bat
echo   停止：   %INSTALL_DIR%\stop-postgres.bat
echo   状态：   %INSTALL_DIR%\status-postgres.bat
echo.
echo 连接信息：
echo   主机： localhost
echo   端口： 5432
echo   用户： postgres
echo   密码： postgres123
echo.

endlocal
exit /b 0