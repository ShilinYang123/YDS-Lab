@echo off
chcp 65001 >nul
echo.
echo ============================================
echo  数字员工项目 - 一键启动脚本
echo ============================================
echo.

:: 检查是否在项目根目录
if not exist "backend\main.py" (
    echo 错误：请在项目根目录运行此脚本
    echo    当前目录：%CD%
    pause
    exit /b 1
)

:: 设置项目目录
set "PROJECT_DIR=%CD%"
set "PYTHON=%PROJECT_DIR%\venv\Scripts\python.exe"
set "PIP=%PROJECT_DIR%\venv\Scripts\pip.exe"
set "NODE=%PROJECT_DIR%\frontend\node_modules\.bin\vite"

echo 项目目录：%PROJECT_DIR%
echo.

:: 检查虚拟环境
if not exist "%PYTHON%" (
    echo 错误：Python虚拟环境不存在
    echo    请先运行 setup.bat 安装环境
    pause
    exit /b 1
)

:: 检查前端依赖
if not exist "%NODE%" (
    echo 安装前端依赖...
    cd /d "%PROJECT_DIR%\frontend"
    call npm install
    if %errorlevel% neq 0 (
        echo 前端依赖安装失败
        pause
        exit /b 1
    )
    cd /d "%PROJECT_DIR%"
)

:: 启动PostgreSQL
echo 启动PostgreSQL...
if exist "scripts\services\postgres\bin\pg_ctl.exe" (
    start "PostgreSQL" /B scripts\services\postgres\bin\pg_ctl -D data\postgres -l logs\postgres.log start
    timeout /t 5 /nobreak >nul
    echo PostgreSQL启动完成
) else (
    echo PostgreSQL未安装，跳过
)

:: 启动Redis
echo 启动Redis...
if exist "scripts\services\redis\redis-server.exe" (
    start "Redis" /B scripts\services\redis\redis-server scripts\services\redis\redis.conf
    timeout /t 3 /nobreak >nul
    echo Redis启动完成
) else (
    echo Redis未安装，跳过
)

:: 启动MinIO
echo 启动MinIO...
if exist "scripts\services\minio\minio.exe" (
    start "MinIO" /B scripts\services\minio\minio.exe server data\minio --console-address ":9001" --address ":9000"
    timeout /t 3 /nobreak >nul
    echo MinIO启动完成
) else (
    echo MinIO未安装，跳过
)

:: 启动后端API
echo 启动后端API服务...
cd /d "%PROJECT_DIR%\backend"
start "Backend API" /B %PYTHON% main.py
cd /d "%PROJECT_DIR%"
timeout /t 5 /nobreak >nul
echo 后端API启动完成

:: 启动前端开发服务器
echo 启动前端开发服务器...
cd /d "%PROJECT_DIR%\frontend"
start "Frontend Dev" /B npm run dev
cd /d "%PROJECT_DIR%"
timeout /t 5 /nobreak >nul
echo 前端开发服务器启动完成

:: 显示访问信息
echo.
echo ============================================
echo 所有服务启动成功！
echo ============================================
echo.
echo 应用访问地址：
echo    前端界面：  http://localhost:3000
echo    API文档：  http://localhost:8000/docs
echo    健康检查： http://localhost:8000/health
echo.
echo 服务管理地址：
echo    MinIO控制台： http://localhost:9001
echo    PostgreSQL： localhost:5432
echo    Redis：      localhost:6379
echo.
echo 管理命令：
echo    停止服务：   stop.bat
echo    检查状态：   check-status.bat
echo    查看日志：   logs\目录下查看各服务日志
echo.
echo 提示：
echo    - 首次启动可能需要较长时间，请耐心等待
echo    - 如服务启动失败，请检查logs目录下的日志文件
echo    - 按 Ctrl+C 可停止当前脚本，不会影响已启动的服务
echo ============================================
echo.
echo 按任意键关闭此窗口（不会影响已启动的服务）...
pause >nul