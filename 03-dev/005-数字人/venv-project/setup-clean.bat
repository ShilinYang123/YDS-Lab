@echo off
chcp 65001 >nul
echo.
echo ============================================
echo  Digital Employee Project - Setup Script
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
set "PIP=%PROJECT_DIR%\venv\Scripts\pip.exe"

echo Project directory: %PROJECT_DIR%
echo.

:: Create Python virtual environment
echo Creating Python virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created successfully
echo.

:: Install Python dependencies
echo Installing Python dependencies...
%PIP% install --upgrade pip
%PIP% install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)
echo Python dependencies installed successfully
echo.

:: Install frontend dependencies
echo Installing frontend dependencies...
cd /d "%PROJECT_DIR%\frontend"
call npm install
if %errorlevel% neq 0 (
    echo ERROR: Failed to install frontend dependencies
    pause
    exit /b 1
)
cd /d "%PROJECT_DIR%"
echo Frontend dependencies installed successfully
echo.

:: Create necessary directories
echo Creating project directories...
mkdir logs 2>nul
mkdir data\postgres 2>nul
mkdir data\redis 2>nul
mkdir data\minio 2>nul
mkdir temp 2>nul
mkdir uploads 2>nul
echo Directories created successfully
echo.

:: Create logs directory
echo Creating logs directory...
if not exist "logs" mkdir logs
echo Logs directory created
echo.

:: Display completion message
echo.
echo ============================================
echo Setup completed successfully!
echo ============================================
echo.
echo Next steps:
echo 1. Run start.bat to start all services
echo 2. Access application at http://localhost:3000
echo 3. API documentation at http://localhost:8000/docs
echo.
echo To check service status, run: check-status.bat
echo To stop services, run: stop.bat
echo ============================================
echo.
pause