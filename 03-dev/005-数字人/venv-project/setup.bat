@echo off
echo.
echo ============================================
echo  数字员工项目 - 一键安装脚本
echo ============================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误：需要管理员权限运行
    echo    请右键点击此脚本，选择"以管理员身份运行"
    pause
    exit /b 1
)

:: 设置变量
set "INSTALL_DIR=%CD%"
set "PYTHON_VERSION=3.11.6"
set "NODE_VERSION=18.18.0"
set "REDIS_VERSION=7.2.3"
set "POSTGRES_VERSION=16.1"
set "MINIO_VERSION=RELEASE.2023-11-20T22-40-07Z"

echo 📍 安装目录：%INSTALL_DIR%
echo.

:: 创建目录结构
echo 📁 创建项目目录结构...
mkdir backend 2>nul
mkdir frontend 2>nul
mkdir scripts\services 2>nul
mkdir scripts\utils 2>nul
mkdir logs 2>nul
mkdir data\postgres 2>nul
mkdir data\redis 2>nul
mkdir data\minio 2>nul
mkdir models 2>nul
mkdir uploads 2>nul
mkdir temp 2>nul

:: 检查Python
echo 🔍 检查Python环境...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Python已安装
    python --version
) else (
    echo ❌ Python未安装，请先安装Python 3.8+
    pause
    exit /b 1
)

:: 创建Python虚拟环境
echo 📦 创建Python虚拟环境...
cd /d "%INSTALL_DIR%"
python -m venv venv
if %errorlevel% neq 0 (
    echo ❌ 虚拟环境创建失败
    pause
    exit /b 1
)
echo ✅ Python虚拟环境创建成功

:: 激活虚拟环境并安装依赖
echo 📚 安装Python依赖包...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Python依赖安装失败
    pause
    exit /b 1
)
echo ✅ Python依赖安装完成

:: 检查Node.js
echo 🔍 检查Node.js环境...
node --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Node.js已安装
    node --version
) else (
    echo ❌ Node.js未安装，请先安装Node.js 16+
    pause
    exit /b 1
)

:: 安装Redis
echo 📦 安装Redis...
if not exist "scripts\services\redis" (
    echo ⬇️  下载Redis...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/tporadowski/redis/releases/download/v%REDIS_VERSION%/Redis-x64-%REDIS_VERSION%.zip' -OutFile 'redis.zip'"
    powershell -Command "Expand-Archive -Path 'redis.zip' -DestinationPath 'scripts\services\redis' -Force"
    del redis.zip
)
echo ✅ Redis安装完成

:: 安装PostgreSQL
echo 📦 安装PostgreSQL...
if not exist "scripts\services\postgres" (
    echo ⬇️  下载PostgreSQL...
    powershell -Command "Invoke-WebRequest -Uri 'https://sbp.enterprisedb.com/api/v1/versions/%POSTGRES_VERSION%/windows/x86_64' -OutFile 'postgres.zip'"
    powershell -Command "Expand-Archive -Path 'postgres.zip' -DestinationPath 'scripts\services\postgres' -Force"
    del postgres.zip
)
echo ✅ PostgreSQL安装完成

:: 安装MinIO
echo 📦 安装MinIO...
if not exist "scripts\services\minio" (
    echo ⬇️  下载MinIO...
    powershell -Command "Invoke-WebRequest -Uri 'https://dl.min.io/server/minio/release/windows-amd64/minio.exe' -OutFile 'scripts\services\minio\minio.exe'"
    powershell -Command "Invoke-WebRequest -Uri 'https://dl.min.io/client/mc/release/windows-amd64/mc.exe' -OutFile 'scripts\services\minio\mc.exe'"
)
echo ✅ MinIO安装完成

:: 创建配置文件
echo ⚙️  创建服务配置文件...
(
echo port 6379
echo bind 127.0.0.1
echo dir ./data/redis
echo logfile ./logs/redis.log
echo daemonize no
echo save 900 1
echo save 300 10
echo save 60 10000
echo maxmemory 256mb
echo maxmemory-policy allkeys-lru
) > scripts\services\redis\redis.conf

:: 创建启动脚本
echo 📝 创建服务启动脚本...
(
echo @echo off
echo cd /d "%INSTALL_DIR%"
echo echo Starting PostgreSQL...
echo start "PostgreSQL" /B scripts\services\postgres\bin\pg_ctl -D data\postgres -l logs\postgres.log start
echo timeout /t 5 /nobreak ^>nul
echo echo Starting Redis...
echo start "Redis" /B scripts\services\redis\redis-server scripts\services\redis\redis.conf
echo timeout /t 3 /nobreak ^>nul
echo echo Starting MinIO...
echo start "MinIO" /B scripts\services\minio\minio.exe server data\minio --console-address ":9001" --address ":9000"
echo timeout /t 3 /nobreak ^>nul
echo echo ============================================
echo echo  所有服务已启动！
echo echo  访问地址：
echo echo  - MinIO控制台: http://localhost:9001
echo echo  - PostgreSQL: localhost:5432
echo echo  - Redis: localhost:6379
echo echo ============================================
echo pause
) > start-services.bat

:: 创建停止脚本
(
echo @echo off
echo cd /d "%INSTALL_DIR%"
echo echo Stopping services...
echo scripts\services\postgres\bin\pg_ctl -D data\postgres stop
echo taskkill /F /IM redis-server.exe ^>nul 2^>^&1
echo taskkill /F /IM minio.exe ^>nul 2^>^&1
echo echo 所有服务已停止！
echo pause
) > stop-services.bat

:: 创建状态检查脚本
(
echo @echo off
echo echo ============================================
echo echo  服务状态检查
echo ============================================
echo.
echo 🔍 PostgreSQL:
powershell -Command "try { $conn = New-Object System.Data.Odbc.OdbcConnection; $conn.ConnectionString = 'Driver={PostgreSQL Unicode};Server=localhost;Port=5432;Database=postgres;Uid=postgres;Pwd=password;'; $conn.Open(); Write-Host '✅ PostgreSQL运行正常' -ForegroundColor Green; $conn.Close() } catch { Write-Host '❌ PostgreSQL未运行' -ForegroundColor Red }"
echo.
echo 🔍 Redis:
powershell -Command "try { $redis = New-Object System.Net.Sockets.TcpClient; $redis.Connect('localhost', 6379); if ($redis.Connected) { Write-Host '✅ Redis运行正常' -ForegroundColor Green } else { Write-Host '❌ Redis未运行' -ForegroundColor Red }; $redis.Close() } catch { Write-Host '❌ Redis未运行' -ForegroundColor Red }"
echo.
echo 🔍 MinIO:
powershell -Command "try { $http = New-Object System.Net.WebClient; $result = $http.DownloadString('http://localhost:9000/minio/health/live'); if ($result -eq 'ok') { Write-Host '✅ MinIO运行正常' -ForegroundColor Green } else { Write-Host '❌ MinIO未运行' -ForegroundColor Red } } catch { Write-Host '❌ MinIO未运行' -ForegroundColor Red }"
echo.
echo ============================================
echo pause
) > check-status.bat

echo.
echo ============================================
echo ✅ 安装完成！
echo ============================================
echo 🚀 下一步操作：
echo    1. 双击 start-services.bat 启动所有服务
echo    2. 双击 check-status.bat 检查服务状态
echo    3. 访问 http://localhost:9001 查看MinIO控制台
echo.
echo 📚 文档说明：
echo    - 日志文件在 logs 目录
echo    - 数据文件在 data 目录
echo    - 服务程序在 scripts\services 目录
echo ============================================
pause