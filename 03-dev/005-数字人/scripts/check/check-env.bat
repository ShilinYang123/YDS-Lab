@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 环境检查脚本
:: 检查数字员工项目所需的环境和依赖

echo.
echo ============================================
echo  数字员工项目 - 环境检查
echo ============================================
echo.

:: 设置变量
set "PROJECT_ROOT=%~dp0..\.."
set "ERRORS=0"
set "WARNINGS=0"

:: 检查操作系统
echo [1/9] 检查操作系统...
echo   系统版本：
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
if "%VERSION%" GEQ "10.0" (
    echo   ✓ Windows 10/11 或更高版本
) else (
    echo   ✗ Windows版本过低，推荐Windows 10或更高版本
    set /a ERRORS+=1
)
echo.

:: 检查系统架构
echo [2/9] 检查系统架构...
if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    echo   ✓ 64位系统
) else (
    echo   ✗ 需要64位系统
    set /a ERRORS+=1
)
echo.

:: 检查内存
echo [3/9] 检查系统内存...
for /f "skip=1 tokens=4" %%a in ('wmic os get TotalVisibleMemorySize /value') do set /a TOTAL_MEM=%%a/1024
if !TOTAL_MEM! GEQ 8192 (
    echo   ✓ 内存充足 ^(!TOTAL_MEM! MB，推荐8GB以上^)
) else if !TOTAL_MEM! GEQ 4096 (
    echo   ⚠ 内存较少 ^(!TOTAL_MEM! MB，推荐8GB以上^)
    set /a WARNINGS+=1
) else (
    echo   ✗ 内存不足 ^(!TOTAL_MEM! MB，需要至少4GB^)
    set /a ERRORS+=1
)
echo.

:: 检查磁盘空间
echo [4/9] 检查磁盘空间...
for /f "tokens=3" %%a in ('dir "%PROJECT_ROOT%" /-c ^| findstr /c:"个字节"') do set FREE_SPACE=%%a
set /a FREE_GB=!FREE_SPACE:~0,-9!/1024/1024/1024
if !FREE_GB! GEQ 10 (
    echo   ✓ 磁盘空间充足 ^(!FREE_GB! GB，推荐10GB以上^)
) else if !FREE_GB! GEQ 5 (
    echo   ⚠ 磁盘空间较少 ^(!FREE_GB! GB，推荐10GB以上^)
    set /a WARNINGS+=1
) else (
    echo   ✗ 磁盘空间不足 ^(!FREE_GB! GB，需要至少5GB^)
    set /a ERRORS+=1
)
echo.

:: 检查Python
echo [5/9] 检查Python环境...
python --version >nul 2>&1
if %errorlevel% == 0 (
    for /f "tokens=2" %%a in ('python --version') do set PYTHON_VERSION=%%a
    echo   ✓ Python已安装 ^(版本：!PYTHON_VERSION!^)
    
    :: 检查Python版本
    for /f "tokens=1,2 delims=." %%a in ("!PYTHON_VERSION!") do (
        set MAJOR=%%a
        set MINOR=%%b
    )
    if !MAJOR! GEQ 3 (
        if !MINOR! GEQ 8 (
            echo   ✓ Python版本符合要求 ^(3.8+^)
        ) else (
            echo   ⚠ Python版本较低 ^(推荐3.8+^)
            set /a WARNINGS+=1
        )
    ) else (
        echo   ✗ Python版本过低 ^(需要3.8+^)
        set /a ERRORS+=1
    )
) else (
    echo   ✗ Python未安装
    set /a ERRORS+=1
)
echo.

:: 检查Node.js
echo [6/9] 检查Node.js环境...
node --version >nul 2>&1
if %errorlevel% == 0 (
    for /f "tokens=1" %%a in ('node --version') do set NODE_VERSION=%%a
    echo   ✓ Node.js已安装 ^(版本：!NODE_VERSION!^)
    
    :: 检查Node.js版本
    set NODE_VERSION=!NODE_VERSION:v=!
    for /f "tokens=1,2 delims=." %%a in ("!NODE_VERSION!") do (
        set NODE_MAJOR=%%a
        set NODE_MINOR=%%b
    )
    if !NODE_MAJOR! GEQ 18 (
        echo   ✓ Node.js版本符合要求 ^(18+^)
    ) else if !NODE_MAJOR! GEQ 16 (
        echo   ⚠ Node.js版本较低 ^(推荐18+^)
        set /a WARNINGS+=1
    ) else (
        echo   ✗ Node.js版本过低 ^(需要16+^)
        set /a ERRORS+=1
    )
) else (
    echo   ✗ Node.js未安装
    set /a ERRORS+=1
)
echo.

:: 检查Git
echo [7/9] 检查Git环境...
git --version >nul 2>&1
if %errorlevel% == 0 (
    for /f "tokens=3" %%a in ('git --version') do set GIT_VERSION=%%a
    echo   ✓ Git已安装 ^(版本：!GIT_VERSION!^)
) else (
    echo   ⚠ Git未安装 ^(推荐安装Git^)
    set /a WARNINGS+=1
)
echo.

:: 检查Visual C++运行库
echo [8/9] 检查Visual C++运行库...
reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Version >nul 2>&1
if %errorlevel% == 0 (
    echo   ✓ Visual C++ 2015-2022运行库已安装
) else (
    echo   ⚠ Visual C++运行库未安装 ^(推荐安装^)
    set /a WARNINGS+=1
)
echo.

:: 检查Windows功能
echo [9/9] 检查Windows功能...
echo   检查.NET Framework...
reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full" /v Release >nul 2>&1
if %errorlevel% == 0 (
    echo   ✓ .NET Framework已安装
) else (
    echo   ⚠ .NET Framework未安装
    set /a WARNINGS+=1
)
echo.

:: 检查端口占用
echo [附加] 检查端口占用...
echo   检查常用端口...
set "PORTS=5432 6379 9000 9001 3000 3001 5050 8081"
for %%p in (%PORTS%) do (
    netstat -ano | findstr ":%%p" >nul
    if !errorlevel! == 0 (
        echo   ⚠ 端口%%p已被占用
        set /a WARNINGS+=1
    ) else (
        echo   ✓ 端口%%p可用
    )
)
echo.

:: 显示检查结果
echo ============================================
echo  环境检查结果
echo ============================================
echo.
echo 错误数量：!ERRORS!
echo 警告数量：!WARNINGS!
echo.

if !ERRORS! == 0 (
    if !WARNINGS! == 0 (
        echo ✅ 环境检查通过！系统环境符合要求。
        echo.
        echo 可以继续安装数字员工项目。
    ) else (
        echo ⚠️  环境检查通过，但有!WARNINGS!个警告。
        echo.
        echo 建议处理警告项以获得更好的体验，但可以继续安装。
    )
) else (
    echo ❌ 环境检查未通过！有!ERRORS!个错误需要修复。
    echo.
    echo 请先修复错误项，然后重新运行环境检查。
)
echo.

:: 提供修复建议
if !ERRORS! GTR 0 (
    echo 修复建议：
    echo.
    if !ERRORLEVEL! GEQ 1 (
        echo 1. 安装Python 3.8+：
echo    访问 https://www.python.org/downloads/
    )
    if !ERRORLEVEL! GEQ 2 (
        echo 2. 安装Node.js 18+：
echo    访问 https://nodejs.org/
    )
    if !ERRORLEVEL! GEQ 3 (
        echo 3. 升级Windows到10或更高版本
    )
    if !ERRORLEVEL! GEQ 4 (
        echo 4. 增加系统内存到8GB以上
    )
    if !ERRORLEVEL! GEQ 5 (
        echo 5. 释放磁盘空间到10GB以上
    )
    echo.
    echo 安装完成后请重新运行此脚本。
)

if !WARNINGS! GTR 0 (
    echo.
    echo 警告项建议：
    echo 1. 安装Git以获得更好的开发体验
echo 2. 安装Visual C++运行库
echo 3. 关闭占用相关端口的程序
echo 4. 升级硬件配置以获得更好性能
)

echo.
echo 详细日志已保存到：%PROJECT_ROOT%\logs\env-check.log
echo.
echo 按任意键退出检查程序...
pause >nul

endlocal
exit /b %ERRORS%