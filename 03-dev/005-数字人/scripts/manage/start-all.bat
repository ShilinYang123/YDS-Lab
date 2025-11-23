@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 启动所有服务脚本
:: 按依赖顺序启动PostgreSQL、Redis、MinIO、后端API、前端

echo.
echo ============================================
echo  数字员工项目 - 启动所有服务
echo ============================================
echo.

:: 设置变量
set "PROJECT_ROOT=%~dp0..\.."
set "LOGS_DIR=%PROJECT_ROOT%\logs"
set "TIMESTAMP=%date:~0,4%-%date:~5,2%-%date:~8,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"

:: 创建日志目录
if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"

:: 记录启动日志
echo [%TIMESTAMP%] 开始启动所有服务 >> "%LOGS_DIR%\service-start.log"

:: 检查端口占用
echo [1/6] 检查端口状态...
call "%~dp0check-ports.bat" >nul 2>&1
if %errorlevel% neq 0 (
    echo 端口检查失败，请查看端口占用情况
    pause
    exit /b 1
)
echo 端口检查完成！
echo.

:: 启动PostgreSQL
echo [2/6] 启动PostgreSQL数据库...
echo 正在启动PostgreSQL...
start "PostgreSQL" cmd /c "cd /d "%PROJECT_ROOT%\services\postgresql" && call start-postgres.bat >> "%LOGS_DIR%\postgres-start.log" 2>&1"
timeout /t 5 /nobreak >nul

:: 检查PostgreSQL是否启动成功
echo 检查PostgreSQL状态...
netstat -ano | findstr ":5432" >nul
if %errorlevel% neq 0 (
    echo 错误：PostgreSQL启动失败！
    echo 请查看日志文件：%LOGS_DIR%\postgres-start.log
    pause
    exit /b 1
)
echo PostgreSQL启动成功！
echo.

:: 启动Redis
echo [3/6] 启动Redis缓存服务...
echo 正在启动Redis...
start "Redis" cmd /c "cd /d "%PROJECT_ROOT%\services\redis" && call start-redis.bat >> "%LOGS_DIR%\redis-start.log" 2>&1"
timeout /t 3 /nobreak >nul

:: 检查Redis是否启动成功
echo 检查Redis状态...
netstat -ano | findstr ":6379" >nul
if %errorlevel% neq 0 (
    echo 错误：Redis启动失败！
    echo 请查看日志文件：%LOGS_DIR%\redis-start.log
    pause
    exit /b 1
)
echo Redis启动成功！
echo.

:: 启动MinIO
echo [4/6] 启动MinIO对象存储...
echo 正在启动MinIO...
start "MinIO" cmd /c "cd /d "%PROJECT_ROOT%\services\minio" && call start-minio.bat >> "%LOGS_DIR%\minio-start.log" 2>&1"
timeout /t 8 /nobreak >nul

:: 检查MinIO是否启动成功
echo 检查MinIO状态...
netstat -ano | findstr ":9000" >nul
if %errorlevel% neq 0 (
    echo 错误：MinIO启动失败！
    echo 请查看日志文件：%LOGS_DIR%\minio-start.log
    pause
    exit /b 1
)
echo MinIO启动成功！
echo.

:: 初始化MinIO
echo [4.5/6] 初始化MinIO配置...
cd /d "%PROJECT_ROOT%\services\minio"
call init-minio.bat >> "%LOGS_DIR%\minio-init.log" 2>&1
timeout /t 3 /nobreak >nul
echo MinIO初始化完成！
echo.

:: 检查Python虚拟环境
echo [5/6] 检查Python虚拟环境...
if not exist "%PROJECT_ROOT%\python-env\venv\Scripts\activate.bat" (
    echo Python虚拟环境未创建，开始创建...
    cd /d "%PROJECT_ROOT%"
    python -m venv python-env\venv
    if %errorlevel% neq 0 (
        echo 错误：Python虚拟环境创建失败！
        pause
        exit /b 1
    )
)

:: 激活虚拟环境并安装依赖
echo 激活Python虚拟环境...
call "%PROJECT_ROOT%\python-env\venv\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo 错误：Python虚拟环境激活失败！
    pause
    exit /b 1
)

:: 安装Python依赖
echo 安装Python依赖包...
cd /d "%PROJECT_ROOT%"
if exist "requirements.txt" (
    pip install -r requirements.txt >> "%LOGS_DIR%\pip-install.log" 2>&1
    if %errorlevel% neq 0 (
        echo 警告：部分Python依赖安装失败，请查看日志
    )
)
echo Python环境准备完成！
echo.

:: 启动后端API（可选）
echo [6/6] 启动后端API服务（可选）...
choice /C YN /M "是否启动后端API服务"
if %errorlevel% == 1 (
    echo 正在启动后端API...
    if exist "%PROJECT_ROOT%\backend\api\start.bat" (
        start "Backend API" cmd /c "cd /d "%PROJECT_ROOT%\backend\api" && call start.bat >> "%LOGS_DIR%\api-start.log" 2>&1"
        timeout /t 5 /nobreak >nul
        
        :: 检查API是否启动成功
        echo 检查API状态...
        netstat -ano | findstr ":3001" >nul
        if %errorlevel% neq 0 (
            echo 警告：后端API启动失败！
            echo 请查看日志文件：%LOGS_DIR%\api-start.log
        ) else (
            echo 后端API启动成功！
        )
    ) else (
        echo 后端API启动脚本不存在，跳过启动
    )
) else (
    echo 跳过后端API启动
)
echo.

:: 显示服务状态
echo ============================================
echo  服务启动状态
echo ============================================
echo.
echo [PostgreSQL] 端口5432: 
netstat -ano | findstr ":5432" >nul && echo   ✓ 运行中 || echo   ✗ 未运行
echo.
echo [Redis] 端口6379: 
netstat -ano | findstr ":6379" >nul && echo   ✓ 运行中 || echo   ✗ 未运行
echo.
echo [MinIO API] 端口9000: 
netstat -ano | findstr ":9000" >nul && echo   ✓ 运行中 || echo   ✗ 未运行
echo.
echo [MinIO Console] 端口9001: 
netstat -ano | findstr ":9001" >nul && echo   ✓ 运行中 || echo   ✗ 未运行
echo.
echo [Backend API] 端口3001: 
netstat -ano | findstr ":3001" >nul && echo   ✓ 运行中 || echo   ✗ 未运行
echo.

:: 记录完成时间
echo [%TIMESTAMP%] 所有服务启动完成 >> "%LOGS_DIR%\service-start.log"

echo.
echo 服务启动完成！
echo.
echo 访问地址：
echo   PostgreSQL管理： http://localhost:5050
echo   Redis管理：      http://localhost:8081
echo   MinIO控制台：    http://localhost:9001
echo   后端API文档：    http://localhost:3001/docs
echo.
echo 日志文件位置：%LOGS_DIR%
echo.
echo 按任意键退出启动脚本...
pause >nul

endlocal