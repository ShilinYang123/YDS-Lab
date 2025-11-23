@echo off
chcp 65001 >nul
echo.
echo ============================================
echo  Digital Employee Project - Service Status
echo ============================================
echo.

echo Checking service status...
echo.

:: Check backend API
echo Backend API Service (http://localhost:8000):
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/health' -TimeoutSec 5; if ($response.StatusCode -eq 200) { Write-Host 'RUNNING' -ForegroundColor Green } else { Write-Host 'ERROR' -ForegroundColor Red } } catch { Write-Host 'STOPPED' -ForegroundColor Red }"
echo.

:: Check frontend dev server
echo Frontend Dev Server (http://localhost:3000):
powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('localhost', 3000); if ($tcp.Connected) { Write-Host 'PORT OPEN' -ForegroundColor Green } else { Write-Host 'PORT CLOSED' -ForegroundColor Red }; $tcp.Close() } catch { Write-Host 'STOPPED' -ForegroundColor Red }"
echo.

:: Check PostgreSQL
echo PostgreSQL Database (localhost:5432):
powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('localhost', 5432); if ($tcp.Connected) { Write-Host 'PORT OPEN' -ForegroundColor Green } else { Write-Host 'PORT CLOSED' -ForegroundColor Red }; $tcp.Close() } catch { Write-Host 'STOPPED' -ForegroundColor Red }"
echo.

:: Check Redis
echo Redis Cache (localhost:6379):
powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('localhost', 6379); if ($tcp.Connected) { Write-Host 'PORT OPEN' -ForegroundColor Green } else { Write-Host 'PORT CLOSED' -ForegroundColor Red }; $tcp.Close() } catch { Write-Host 'STOPPED' -ForegroundColor Red }"
echo.

:: Check MinIO
echo MinIO Storage (http://localhost:9000):
powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('localhost', 9000); if ($tcp.Connected) { Write-Host 'PORT OPEN' -ForegroundColor Green } else { Write-Host 'PORT CLOSED' -ForegroundColor Red }; $tcp.Close() } catch { Write-Host 'STOPPED' -ForegroundColor Red }"
echo.

:: Check MinIO Console
echo MinIO Console (http://localhost:9001):
powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient; $tcp.Connect('localhost', 9001); if ($tcp.Connected) { Write-Host 'PORT OPEN' -ForegroundColor Green } else { Write-Host 'PORT CLOSED' -ForegroundColor Red }; $tcp.Close() } catch { Write-Host 'STOPPED' -ForegroundColor Red }"
echo.

:: Show process info
echo Process Information:
echo    Backend API Process:
tasklist /FI "WINDOWTITLE eq Backend API" 2>nul | findstr /I "python" >nul && echo    Python Backend: RUNNING || echo    Python Backend: STOPPED
echo.
echo    Frontend Dev Process:
tasklist /FI "WINDOWTITLE eq Frontend Dev" 2>nul | findstr /I "node" >nul && echo    Node.js Frontend: RUNNING || echo    Node.js Frontend: STOPPED
echo.
echo    Redis Process:
tasklist | findstr /I "redis-server" >nul && echo    Redis Server: RUNNING || echo    Redis Server: STOPPED
echo.
echo    MinIO Process:
tasklist | findstr /I "minio" >nul && echo    MinIO Server: RUNNING || echo    MinIO Server: STOPPED
echo.

:: Check log files
echo Log Files:
if exist "logs\postgres.log" (
    echo    PostgreSQL log: EXISTS
) else (
    echo    PostgreSQL log: NOT FOUND
)

if exist "logs\redis.log" (
    echo    Redis log: EXISTS
) else (
    echo    Redis log: NOT FOUND
)
echo.

echo ============================================
echo Troubleshooting:
echo.
echo If services are not running:
echo 1. Try running start.bat to restart services
echo 2. Check logs directory for detailed logs
echo 3. Ensure ports are not used by other programs
echo 4. Check firewall settings
echo.
echo If services have errors:
echo 1. Check specific service log files
echo 2. Verify configuration files
echo 3. Ensure all dependencies are installed
echo 4. Try restarting individual services
echo ============================================
echo.
pause