@echo off
echo.
echo ============================================
echo  数字员工项目 - 一键停止脚本
echo ============================================
echo.

echo 🛑 正在停止所有服务...
echo.

:: 停止后端API
echo 🔴 停止后端API服务...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Backend API" 2>nul
taskkill /F /IM uvicorn.exe 2>nul
echo ✅ 后端API服务已停止

:: 停止前端开发服务器
echo 🔴 停止前端开发服务器...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq Frontend Dev" 2>nul
echo ✅ 前端开发服务器已停止

:: 停止PostgreSQL
echo 🔴 停止PostgreSQL...
if exist "scripts\services\postgres\bin\pg_ctl.exe" (
    scripts\services\postgres\bin\pg_ctl -D data\postgres stop >nul 2>&1
    echo ✅ PostgreSQL已停止
) else (
    echo ⚠️ PostgreSQL未安装，跳过
)

:: 停止Redis
echo 🔴 停止Redis...
taskkill /F /IM redis-server.exe 2>nul
echo ✅ Redis已停止

:: 停止MinIO
echo 🔴 停止MinIO...
taskkill /F /IM minio.exe 2>nul
echo ✅ MinIO已停止

echo.
echo ============================================
echo ✅ 所有服务已停止！
echo ============================================
echo.
echo 📝 提示：
echo    - 服务停止可能需要几秒钟时间
echo    - 如有个别服务未能停止，可手动在任务管理器中结束进程
echo    - 日志文件保存在 logs 目录中，可用于故障排查
echo ============================================
echo.
pause