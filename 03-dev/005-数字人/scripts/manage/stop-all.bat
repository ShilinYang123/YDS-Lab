@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 停止所有服务脚本
:: 按依赖顺序停止前端、后端API、MinIO、Redis、PostgreSQL

echo.
echo ============================================
echo  数字员工项目 - 停止所有服务
echo ============================================
echo.

:: 设置变量
set "PROJECT_ROOT=%~dp0..\.."
set "LOGS_DIR=%PROJECT_ROOT%\logs"
set "TIMESTAMP=%date:~0,4%-%date:~5,2%-%date:~8,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"

:: 创建日志目录
if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"

:: 记录停止日志
echo [%TIMESTAMP%] 开始停止所有服务 >> "%LOGS_DIR%\service-stop.log"

:: 停止前端应用
echo [1/6] 停止前端应用...
tasklist /FI "WINDOWTITLE eq Frontend" 2>nul | find /I /N "cmd.exe" >nul
if %errorlevel% == 0 (
    echo 正在停止前端应用...
    taskkill /FI "WINDOWTITLE eq Frontend" /F >nul 2>&1
    echo 前端应用已停止！
) else (
    echo 前端应用未运行
)
echo.

:: 停止后端API
echo [2/6] 停止后端API服务...
tasklist /FI "WINDOWTITLE eq Backend API" 2>nul | find /I /N "cmd.exe" >nul
if %errorlevel% == 0 (
    echo 正在停止后端API...
    taskkill /FI "WINDOWTITLE eq Backend API" /F >nul 2>&1
    echo 后端API已停止！
) else (
    echo 后端API未运行
)
echo.

:: 停止其他可能的API进程
echo 检查其他API进程...
tasklist /FI "IMAGENAME eq python.exe" 2>nul | find /I /N "python" >nul
if %errorlevel% == 0 (
    echo 发现Python进程，确认是否停止？(Y/N)
    choice /C YN /N >nul
    if !errorlevel! == 1 (
        echo 正在停止Python进程...
        taskkill /IM python.exe /F >nul 2>&1
        echo Python进程已停止！
    ) else (
        echo 保留Python进程
    )
)
echo.

:: 停止MinIO
echo [3/6] 停止MinIO对象存储...
tasklist /FI "IMAGENAME eq minio.exe" 2>nul | find /I /N "minio" >nul
if %errorlevel% == 0 (
    echo 正在停止MinIO...
    taskkill /IM minio.exe /F >nul 2>&1
    timeout /t 2 /nobreak >nul
    echo MinIO已停止！
) else (
    echo MinIO未运行
)
echo.

:: 停止Redis
echo [4/6] 停止Redis缓存服务...
tasklist /FI "IMAGENAME eq redis-server.exe" 2>nul | find /I /N "redis-server" >nul
if %errorlevel% == 0 (
    echo 正在停止Redis...
    taskkill /IM redis-server.exe /F >nul 2>&1
    echo Redis已停止！
) else (
    echo Redis未运行
)
echo.

:: 停止PostgreSQL
echo [5/6] 停止PostgreSQL数据库...
tasklist /FI "IMAGENAME eq postgres.exe" 2>nul | find /I /N "postgres" >nul
if %errorlevel% == 0 (
    echo 正在停止PostgreSQL...
    
    :: 尝试优雅停止
    if exist "%PROJECT_ROOT%\services\postgresql\stop-postgres.bat" (
        cd /d "%PROJECT_ROOT%\services\postgresql"
        call stop-postgres.bat
    )
    
    timeout /t 3 /nobreak >nul
    
    :: 强制停止剩余进程
    taskkill /IM postgres.exe /F >nul 2>&1
    taskkill /IM pg_ctl.exe /F >nul 2>&1
    
    echo PostgreSQL已停止！
) else (
    echo PostgreSQL未运行
)
echo.

:: 清理临时文件
echo [6/6] 清理临时文件...
echo 清理PID文件...
if exist "%PROJECT_ROOT%\data\postgres\postmaster.pid" (
    del /F /Q "%PROJECT_ROOT%\data\postgres\postmaster.pid" >nul 2>&1
    echo PostgreSQL PID文件已清理
)

if exist "%PROJECT_ROOT%\data\redis\redis.pid" (
    del /F /Q "%PROJECT_ROOT%\data\redis\redis.pid" >nul 2>&1
    echo Redis PID文件已清理
)

echo 清理日志文件（可选）...
echo 是否清理旧的日志文件？(Y/N)
choice /C YN /N >nul
if %errorlevel% == 1 (
    echo 正在清理旧日志文件...
    forfiles /P "%LOGS_DIR%" /M *.log /D -7 /C "cmd /c del @path" >nul 2>&1
    echo 旧日志文件已清理
) else (
    echo 保留日志文件
)
echo.

:: 显示停止结果
echo ============================================
echo  服务停止状态
echo ============================================
echo.
echo [PostgreSQL] 端口5432: 
netstat -ano | findstr ":5432" >nul && echo   ✗ 仍在运行 || echo   ✓ 已停止
echo.
echo [Redis] 端口6379: 
netstat -ano | findstr ":6379" >nul && echo   ✗ 仍在运行 || echo   ✓ 已停止
echo.
echo [MinIO API] 端口9000: 
netstat -ano | findstr ":9000" >nul && echo   ✗ 仍在运行 || echo   ✓ 已停止
echo.
echo [MinIO Console] 端口9001: 
netstat -ano | findstr ":9001" >nul && echo   ✗ 仍在运行 || echo   ✓ 已停止
echo.
echo [Backend API] 端口3001: 
netstat -ano | findstr ":3001" >nul && echo   ✗ 仍在运行 || echo   ✓ 已停止
echo.
echo [Frontend] 端口3000: 
netstat -ano | findstr ":3000" >nul && echo   ✗ 仍在运行 || echo   ✓ 已停止
echo.

:: 记录完成时间
echo [%TIMESTAMP%] 所有服务停止完成 >> "%LOGS_DIR%\service-stop.log"

echo.
echo 服务停止完成！
echo.
echo 日志文件位置：%LOGS_DIR%
echo.
echo 按任意键退出停止脚本...
pause >nul

endlocal