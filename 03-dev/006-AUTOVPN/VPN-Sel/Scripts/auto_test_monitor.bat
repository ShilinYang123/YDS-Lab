@echo off
echo AUTOVPN 自动测试监控系统启动中...
echo =====================================
echo 系统将自动进行所有测试并处理屏幕等待
echo 测试过程无需人工干预
echo.

set LOG_FILE=auto_test_monitor_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
set REPORT_FILE=auto_test_report_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt

echo 开始时间: %date% %time% >> %LOG_FILE%
echo 日志文件: %LOG_FILE% >> %LOG_FILE%
echo 报告文件: %REPORT_FILE% >> %LOG_FILE%
echo. >> %LOG_FILE%

echo [INFO] 启动综合自动化测试...
python comprehensive_auto_test.py >> %LOG_FILE% 2>&1

if %errorlevel% equ 0 (
    echo [SUCCESS] 测试完成！
    echo [INFO] 详细报告已生成
    echo [INFO] 日志文件: %LOG_FILE%
    echo [INFO] 报告文件: comprehensive_test_report.txt
) else (
    echo [ERROR] 测试执行失败！
    echo [ERROR] 请检查日志文件: %LOG_FILE%
)

echo.
echo 按任意键退出...
pause > nul