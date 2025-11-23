@echo off
echo ========================================
echo AUTOVPN 自动测试和监控启动器
echo ========================================
echo.

REM 设置工作目录
cd /d "%~dp0"

echo 步骤1: 运行功能测试...
echo.
python menu_function_tester.py

if %errorlevel% neq 0 (
    echo ❌ 功能测试失败，请检查错误
    pause
    exit /b 1
)

echo.
echo 步骤2: 启动服务监控器...
echo.
echo 正在启动后台监控服务...
start "" "start_monitor.bat"

echo.
echo ========================================
echo 自动测试和监控部署完成！
echo ========================================
echo.
echo ✅ 功能测试已完成 - 查看 menu_function_test_report.txt
echo ✅ 监控服务已启动 - 查看 autovpn_monitor.log
echo ✅ 服务状态文件 - service_status.json
echo.
echo 监控器将在后台持续运行，您现在可以安全离开电脑。
echo 要停止监控器，请关闭相应的命令窗口。
echo.
pause