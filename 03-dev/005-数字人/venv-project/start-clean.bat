@echo off
chcp 65001 >nul
echo.
echo ============================================
echo  Digital Employee Project - Start Services
echo ============================================
echo.

:: Check if in project root
if not exist "backend\main.py" (
    echo ERROR: Please run this script from project root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

:: Set project directory
set "PROJECT_DIR=%CD%"
set "PYTHON=%PROJECT_DIR%\venv\Scripts\python.exe"
set "NODE=%PROJECT_DIR%\frontend\node_modules\.bin\vite"

echo Project directory: %PROJECT_DIR%
echo.

:: Check virtual environment
if not exist "%PYTHON%" (
    echo ERROR: Python virtual environment not found
    echo Please run setup.bat first to install environment
    pause
    exit /b 1
)

:: Check frontend dependencies
if not exist "%NODE%" (
    echo Installing frontend dependencies...
    cd /d "%PROJECT_DIR%\frontend"
    call npm install
    if %errorlevel% neq 0 (
        echo ERROR: Frontend dependencies installation failed
        pause
        exit /b 1
    )
    cd /d "%PROJECT_DIR%"
)

:: Start backend API
echo Starting backend API service...
cd /d "%PROJECT_DIR%\backend"
start "Backend API" /B %PYTHON% main.py
cd /d "%PROJECT_DIR%"
timeout /t 5 /nobreak >nul
echo Backend API started successfully

:: Start frontend development server
echo Starting frontend development server...
cd /d "%PROJECT_DIR%\frontend"
start "Frontend Dev" /B npm run dev
cd /d "%PROJECT_DIR%"
timeout /t 5 /nobreak >nul
echo Frontend development server started successfully

:: Display access information
echo.
echo ============================================
echo All services started successfully!
echo ============================================
echo.
echo Application access:
echo    Frontend:   http://localhost:3000
echo    API Docs:   http://localhost:8000/docs
echo    Health:     http://localhost:8000/health
echo.
echo Management:
echo    Stop:       stop.bat
echo    Status:     check-status.bat
echo    Logs:       logs directory
echo.
echo Tips:
echo    - First startup may take longer, please be patient
echo    - Check logs directory if services fail to start
echo    - Ctrl+C stops this script but not running services
echo ============================================
echo.
echo Press any key to close this window (running services will continue)...
pause >nul