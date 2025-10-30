@echo off
echo [1/4] 正在检查 8000 端口占用...
netstat -ano | findstr :8000 >nul
if %errorlevel% == 0 (
    echo 端口 8000 已被占用，正在终止进程...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /PID %%a /F
)

echo [2/4] 正在添加防火墙规则（允许 8000 端口）...
netsh advfirewall firewall add rule name="DeWatermark API (8000)" dir=in action=allow protocol=TCP localport=8000 profile=private

echo [3/4] 正在启动 Flask 服务...
cd /d "%~dp0"
start /B python api_server.py

echo [4/4] 验证服务状态...
timeout /t 3 >nul
netstat -ano | findstr :8000 >nul
if %errorlevel% == 0 (
    echo.
    echo ✅ 成功！服务已在 http://192.168.101.98:8000 运行
    echo 请在笔记本执行：telnet 192.168.101.98 8000 验证
) else (
    echo ❌ 启动失败，请检查 Python 环境和 api_server.py 文件
)

pause