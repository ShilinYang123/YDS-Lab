@echo off
echo.
echo ============================================
echo  数字员工项目 - 服务状态检查
echo ============================================
echo.

echo 🔍 正在检查服务状态...
echo.

:: 检查后端API
echo 📡 后端API服务 (http://localhost:8000):
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/health' -TimeoutSec 5; if ($response.StatusCode -eq 200) { Write-Host '运行正常' -ForegroundColor Green } else { Write-Host '状态异常' -ForegroundColor Red } } catch { Write-Host '未运行' -ForegroundColor Red }"
echo.

:: 检查前端开发服务器
echo 🌐 前端开发服务器 (http://localhost:3000):
powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('localhost', 3000); if ($tcp.Connected) { Write-Host '端口监听正常' -ForegroundColor Green } else { Write-Host '端口未监听' -ForegroundColor Red }; $tcp.Close() } catch { Write-Host '未运行' -ForegroundColor Red }"
echo.

:: 检查PostgreSQL
echo 🗄️  PostgreSQL数据库 (localhost:5432):
powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('localhost', 5432); if ($tcp.Connected) { Write-Host '端口监听正常' -ForegroundColor Green } else { Write-Host '端口未监听' -ForegroundColor Red }; $tcp.Close() } catch { Write-Host '未运行' -ForegroundColor Red }"
echo.

:: 检查Redis
echo 💾 Redis缓存服务 (localhost:6379):
powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('localhost', 6379); if ($tcp.Connected) { Write-Host '端口监听正常' -ForegroundColor Green } else { Write-Host '端口未监听' -ForegroundColor Red }; $tcp.Close() } catch { Write-Host '未运行' -ForegroundColor Red }"
echo.

:: 检查MinIO
echo 📦 MinIO对象存储 (http://localhost:9000):
powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('localhost', 9000); if ($tcp.Connected) { Write-Host '端口监听正常' -ForegroundColor Green } else { Write-Host '端口未监听' -ForegroundColor Red }; $tcp.Close() } catch { Write-Host '未运行' -ForegroundColor Red }"
echo.

:: 检查MinIO控制台
echo 🎛️  MinIO控制台 (http://localhost:9001):
powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('localhost', 9001); if ($tcp.Connected) { Write-Host '端口监听正常' -ForegroundColor Green } else { Write-Host '端口未监听' -ForegroundColor Red }; $tcp.Close() } catch { Write-Host '未运行' -ForegroundColor Red }"
echo.

:: 显示进程信息
echo 📊 相关进程信息:
echo    后端API进程:
tasklist /FI "WINDOWTITLE eq Backend API" 2>nul | findstr /I "python" >nul && echo    Python后端进程运行中 || echo    Python后端进程未运行
echo.
echo    前端开发进程:
tasklist /FI "WINDOWTITLE eq Frontend Dev" 2>nul | findstr /I "node" >nul && echo    Node.js前端进程运行中 || echo    Node.js前端进程未运行
echo.
echo    Redis进程:
tasklist | findstr /I "redis-server" >nul && echo    Redis进程运行中 || echo    Redis进程未运行
echo.
echo    MinIO进程:
tasklist | findstr /I "minio" >nul && echo    MinIO进程运行中 || echo    MinIO进程未运行
echo.

:: 检查日志文件
echo 📝 日志文件检查:
if exist "logs\postgres.log" (
    echo    PostgreSQL日志文件存在
) else (
    echo    PostgreSQL日志文件不存在
)

if exist "logs\redis.log" (
    echo    Redis日志文件存在
) else (
    echo    Redis日志文件不存在
)
echo.

echo ============================================
echo 🔧 故障排查建议：
echo.
echo 如果服务未运行：
echo    1. 尝试运行 start.bat 重新启动服务
echo    2. 检查 logs 目录下的详细日志
echo    3. 确保端口未被其他程序占用
echo    4. 检查防火墙设置
echo.
echo 如果服务运行异常：
echo    1. 查看具体服务的日志文件
echo    2. 检查配置文件是否正确
echo    3. 确保所有依赖已正确安装
echo    4. 尝试重启单个服务
echo ============================================
echo.
pause