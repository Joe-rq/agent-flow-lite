@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

set PROJECT_ROOT=%~dp0
set BACKEND_DIR=%PROJECT_ROOT%backend
set FRONTEND_DIR=%PROJECT_ROOT%frontend

echo ========================================
echo Agent Flow Lite Startup
echo ========================================
echo.

REM Check backend venv
if not exist "%BACKEND_DIR%\.venv" (
    echo [ERROR] Backend venv not found. Please run install.bat first.
    pause
    exit /b 1
)

echo [START] Starting backend service (port 8000)...
cd /d "%BACKEND_DIR%"
start "Agent Flow Backend" cmd /k "uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend
ping -n 4 127.0.0.1 > nul

echo [START] Starting frontend service (port 5173)...
cd /d "%FRONTEND_DIR%"
start "Agent Flow Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo [DONE] Services started successfully!
echo.
echo   Backend: http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:8000/docs
echo.
echo Note: Services are running in separate windows.
echo Close the windows to stop the services.
echo.
pause
