@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 数字员工项目 - 一键安装所有服务脚本
:: 适用于Windows环境的本地开发部署

echo.
echo ============================================
echo  数字员工项目 - 虚拟环境安装程序
echo ============================================
echo.

:: 设置变量
set "PROJECT_ROOT=%~dp0..\.."
set "SERVICES_DIR=%PROJECT_ROOT%\services"
set "CONFIG_DIR=%PROJECT_ROOT%\config"
set "LOGS_DIR=%PROJECT_ROOT%\logs"
set "DATA_DIR=%PROJECT_ROOT%\data"

:: 创建必要的目录
echo [1/8] 创建项目目录结构...
mkdir "%SERVICES_DIR%" 2>nul
mkdir "%LOGS_DIR%" 2>nul
mkdir "%DATA_DIR%" 2>nul
mkdir "%DATA_DIR%\postgres" 2>nul
mkdir "%DATA_DIR%\redis" 2>nul
mkdir "%DATA_DIR%\minio" 2>nul
mkdir "%DATA_DIR%\uploads" 2>nul
echo 目录结构创建完成！
echo.

:: 检查管理员权限
echo [2/8] 检查系统权限...
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：需要管理员权限运行此脚本！
    echo 请右键点击脚本，选择"以管理员身份运行"
    pause
    exit /b 1
)
echo 管理员权限验证通过！
echo.

:: 检查系统环境
echo [3/8] 检查系统环境...
call "%~dp0check-system.bat" >nul 2>&1
if %errorlevel% neq 0 (
    echo 系统环境检查失败，请查看日志文件
    pause
    exit /b 1
)
echo 系统环境检查通过！
echo.

:: 安装Python环境
echo [4/8] 安装Python环境...
call "%~dp0install-python.bat"
if %errorlevel% neq 0 (
    echo Python环境安装失败
    pause
    exit /b 1
)
echo Python环境安装完成！
echo.

:: 安装PostgreSQL
echo [5/8] 安装PostgreSQL数据库...
call "%~dp0install-postgres.bat"
if %errorlevel% neq 0 (
    echo PostgreSQL安装失败
    pause
    exit /b 1
)
echo PostgreSQL安装完成！
echo.

:: 安装Redis
echo [6/8] 安装Redis缓存服务...
call "%~dp0install-redis.bat"
if %errorlevel% neq 0 (
    echo Redis安装失败
    pause
    exit /b 1
)
echo Redis安装完成！
echo.

:: 安装MinIO
echo [7/8] 安装MinIO对象存储...
call "%~dp0install-minio.bat"
if %errorlevel% neq 0 (
    echo MinIO安装失败
    pause
    exit /b 1
)
echo MinIO安装完成！
echo.

:: 初始化环境配置
echo [8/8] 初始化环境配置...
call "%~dp0init-environment.bat"
if %errorlevel% neq 0 (
    echo 环境初始化失败
    pause
    exit /b 1
)
echo 环境初始化完成！
echo.

:: 创建桌面快捷方式
echo 创建桌面快捷方式...
call "%~dp0..\utils\create-shortcuts.bat"
echo.

:: 显示安装结果
echo ============================================
echo  安装完成！
echo ============================================
echo.
echo 服务安装位置：%SERVICES_DIR%
echo 配置文件位置：%CONFIG_DIR%
echo 日志文件位置：%LOGS_DIR%
echo 数据文件位置：%DATA_DIR%
echo.
echo 请使用以下命令管理服务：
echo   启动所有服务： scripts\manage\start-all.bat
echo   停止所有服务： scripts\manage\stop-all.bat
echo   查看服务状态： scripts\manage\status.bat
echo.
echo 管理界面访问地址：
echo   PostgreSQL管理： http://localhost:5050
echo   Redis管理：      http://localhost:8081
echo   MinIO控制台：    http://localhost:9001
echo   应用主页：       http://localhost:3000
echo.
echo 安装日志保存在：%LOGS_DIR%\install.log
echo.
echo 按任意键退出安装程序...
pause >nul