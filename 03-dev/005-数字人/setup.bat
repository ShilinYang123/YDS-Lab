@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 数字员工项目 - 主初始化脚本
:: 适用于Windows环境的项目初始化

echo.
echo ============================================
echo  数字员工项目 - 虚拟环境初始化程序
echo ============================================
echo.
echo 欢迎使用数字员工项目虚拟环境方案！
echo 本程序将帮助您快速搭建开发环境。
echo.

:: 设置变量
set "PROJECT_ROOT=%~dp0"
set "SCRIPTS_DIR=%PROJECT_ROOT%\scripts"
set "INSTALL_DIR=%SCRIPTS_DIR%\install"
set "LOGS_DIR=%PROJECT_ROOT%\logs"
set "TIMESTAMP=%date:~0,4%-%date:~5,2%-%date:~8,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"

:: 创建日志目录
if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"

:: 记录开始时间
echo [%TIMESTAMP%] 开始项目初始化 >> "%LOGS_DIR%\setup.log"

:: 显示系统信息
echo [系统信息]
echo   操作系统：
ver | findstr "Windows" >nul && echo   ✓ Windows系统检测正常
echo   当前目录：%PROJECT_ROOT%
echo   时间：%date% %time%
echo.

:: 步骤1：环境检查
echo [步骤1/4] 环境检查...
echo 正在检查系统环境...
call "%INSTALL_DIR%\check-env.bat" > "%LOGS_DIR%\env-check.log" 2>&1
set "ENV_CHECK_RESULT=%errorlevel%"

if %ENV_CHECK_RESULT% equ 0 (
    echo ✅ 环境检查通过！
) else (
    echo ❌ 环境检查未通过！
    echo.
    echo 发现系统环境问题，建议先解决后再继续。
    echo 详细日志：%LOGS_DIR%\env-check.log
    echo.
    choice /C YN /M "是否继续安装（可能会失败）"
    if !errorlevel! equ 2 (
        echo 安装已取消。
        pause
        exit /b 1
    )
)
echo.

:: 步骤2：用户确认
echo [步骤2/4] 安装确认
echo.
echo 即将开始安装以下服务：
echo   • PostgreSQL 数据库（端口5432）
echo   • Redis 缓存服务（端口6379）
echo   • MinIO 对象存储（端口9000/9001）
echo   • Python 虚拟环境
echo.
echo 安装路径：
echo   项目根目录：%PROJECT_ROOT%
echo   服务目录：%PROJECT_ROOT%\services
echo   数据目录：%PROJECT_ROOT%\data
echo   日志目录：%PROJECT_ROOT%\logs
echo.
choice /C YN /M "确认开始安装"
if %errorlevel% equ 2 (
    echo 安装已取消。
    pause
    exit /b 1
)
echo.

:: 步骤3：执行安装
echo [步骤3/4] 开始安装...
echo.
echo 正在执行安装程序...
call "%INSTALL_DIR%\install-all.bat"
set "INSTALL_RESULT=%errorlevel%"

if %INSTALL_RESULT% neq 0 (
    echo.
    echo ❌ 安装过程中出现错误！
    echo 请查看日志文件：%LOGS_DIR%\install.log
    echo.
    choice /C YR /M "重试安装还是退出"
    if !errorlevel! equ 1 (
        echo 重新启动安装程序...
        call "%INSTALL_DIR%\install-all.bat"
    ) else (
        echo 安装已退出。
        pause
        exit /b 1
    )
)
echo.

:: 步骤4：完成配置
echo [步骤4/4] 完成配置...
echo.
echo 正在完成最后的配置...

:: 创建快速启动脚本
echo 创建快速启动脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo.
echo ============================================
echo  数字员工项目 - 快速启动
echo ============================================
echo.
echo 正在启动所有服务...
echo.
call "%~dp0scripts\manage\start-all.bat"
) > "%PROJECT_ROOT%\start.bat"

:: 创建快速停止脚本
echo 创建快速停止脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo.
echo ============================================
echo  数字员工项目 - 快速停止
echo ============================================
echo.
echo 正在停止所有服务...
echo.
call "%~dp0scripts\manage\stop-all.bat"
) > "%PROJECT_ROOT%\stop.bat"

:: 创建状态检查脚本
echo 创建状态检查脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo.
echo ============================================
echo  数字员工项目 - 服务状态
echo ============================================
echo.
call "%~dp0scripts\manage\status.bat"
) > "%PROJECT_ROOT%\status.bat"

:: 创建卸载脚本
echo 创建卸载脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo.
echo ============================================
echo  数字员工项目 - 卸载程序
echo ============================================
echo.
echo ⚠️  警告：此操作将删除所有服务和数据！
echo.
choice /C YN /M "确认卸载"
if !errorlevel! equ 2 (
    echo 卸载已取消。
    pause
    exit /b 1
)
echo.
echo 正在卸载...
echo 停止所有服务...
call "%~dp0scripts\manage\stop-all.bat" ^>nul 2^>^&1
echo 删除服务文件...
rd /s /q "%~dp0services" 2^>nul
echo 删除数据文件...
rd /s /q "%~dp0data" 2^>nul
echo 删除日志文件...
rd /s /q "%~dp0logs" 2^>nul
echo 删除Python虚拟环境...
rd /s /q "%~dp0python-env" 2^>nul
echo.
echo 卸载完成！
echo.
) > "%PROJECT_ROOT%\uninstall.bat"

:: 记录完成时间
set "COMPLETE_TIME=%date:~0,4%-%date:~5,2%-%date:~8,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%"
set "COMPLETE_TIME=%COMPLETE_TIME: =0%"
echo [%COMPLETE_TIME%] 项目初始化完成 >> "%LOGS_DIR%\setup.log"

:: 显示完成信息
echo.
echo ============================================
echo ✅ 项目初始化完成！
echo ============================================
echo.
echo 🎉 恭喜！数字员工项目已成功安装！
echo.
echo 快速使用命令：
echo   启动服务：   start.bat
echo   停止服务：   stop.bat
echo   查看状态：   status.bat
echo   卸载项目：   uninstall.bat
echo.
echo 管理脚本位置：
echo   安装脚本：   scripts\install\
echo   管理脚本：   scripts\manage\
echo   检查脚本：   scripts\check\
echo.
echo 服务访问地址：
echo   PostgreSQL管理： http://localhost:5050
echo   Redis管理：      http://localhost:8081
echo   MinIO控制台：    http://localhost:9001
echo   应用主页：       http://localhost:3000
echo.
echo 配置文件位置：
echo   环境配置：   config\environment\
echo   服务配置：   config\services\
echo.
echo 日志文件位置：
echo   安装日志：   %LOGS_DIR%\install.log
echo   环境检查：   %LOGS_DIR%\env-check.log
echo   服务日志：   %LOGS_DIR%\
echo.
echo 📖 下一步建议：
echo 1. 运行 start.bat 启动所有服务
echo 2. 访问 http://localhost:3000 查看应用
echo 3. 查看 docs 目录下的使用文档
echo.
echo 💡 提示：
echo • 所有服务都已配置为本地运行，无需Docker
echo • 数据文件存储在 data 目录，请定期备份
echo • 遇到问题请查看 logs 目录下的日志文件
echo.
echo 安装用时：从 %TIMESTAMP% 到 %COMPLETE_TIME%
echo.
echo 按任意键退出安装程序...
pause >nul

endlocal