@echo off
echo AUTOVPN IPv6功能切换工具
echo ========================
echo.

:menu
echo 当前IPv6状态:
if exist "S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env" (
    type "S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env" | findstr "IPv6_ENABLE" 2>nul
) else (
    echo [错误] 配置文件不存在
)
echo.
echo 请选择操作:
echo 1. 启用IPv6支持
echo 2. 禁用IPv6支持（仅IPv4）
echo 3. 查看当前配置
echo 4. 验证IPv6配置
echo 5. 退出
echo.

set /p choice=请输入选项(1-5): 

if "%choice%"=="1" (
    echo 正在启用IPv6支持...
    powershell -Command "
        $config = Get-Content 'S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env'
        $config = $config -replace 'IPv6_ENABLE=false', 'IPv6_ENABLE=true'
        if ($config -notmatch 'IPv6_ENABLE=') {
            $config += '`nIPv6_ENABLE=true'
        }
        $config | Set-Content 'S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env'
    "
    echo [成功] IPv6已启用，请重启AUTOVPN服务
    echo [警告] 请确保服务器支持IPv6
    goto end
)

if "%choice%"=="2" (
    echo 正在禁用IPv6支持...
    powershell -Command "
        $config = Get-Content 'S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env'
        $config = $config -replace 'IPv6_ENABLE=true', 'IPv6_ENABLE=false'
        if ($config -notmatch 'IPv6_ENABLE=') {
            $config += '`nIPv6_ENABLE=false'
        }
        $config | Set-Content 'S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env'
    "
    echo [成功] IPv6已禁用，仅使用IPv4模式
    echo [成功] 无需重启服务，配置已生效
    goto end
)

if "%choice%"=="3" (
    echo 当前IPv6配置:
    if exist "S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env" (
        type "S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env" | findstr "IPv6"
    ) else (
        echo [错误] 配置文件不存在
    )
    goto end
)

if "%choice%"=="4" (
    echo 正在验证IPv6配置...
    if exist "S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\check_ipv6_config.py" (
        python "S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\check_ipv6_config.py"
    ) else (
        echo [警告] 验证脚本不存在，请查看配置文件
        if exist "S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env" (
        type "S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env" | findstr "IPv6"
        )
    )
    goto end
)

if "%choice%"=="5" (
    exit
)

echo [错误] 输入无效，请输入1-5之间的数字
echo.
echo 按任意键返回菜单...
pause > nul
cls
goto menu

:end
echo.
echo 按任意键返回菜单...
pause > nul
cls
goto menu