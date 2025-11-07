@echo off
echo 启动YDS-Lab Trae平台生产环境...
echo ========================================

cd /d "%~dp0.."

echo 启动MCP集群...
start "MCP-GitHub" python tools\mcp\servers\GitHub\github_mcp_server.py
start "MCP-Excel" python tools\mcp\servers\Excel\excel_mcp_server.py
start "MCP-Builder" python tools\mcp\servers\Builder\builder_mcp_server.py
start "MCP-FileSystem" python tools\mcp\servers\FileSystem\filesystem_mcp_server.py
start "MCP-Database" python tools\mcp\servers\Database\database_mcp_server.py

echo 等待MCP服务启动...
timeout /t 5 /nobreak > nul

echo 启动智能体协作系统...
python tools\scripts\start_collaboration.py

echo Trae平台生产环境启动完成！
echo 访问监控面板: http://localhost:8080
pause
