@echo off
REM ============================================
REM AI Document Generator - Backend Startup
REM Double-click this file to start the backend
REM ============================================

cd /d "%~dp0"

echo.
echo  AI Document Generator Backend
echo  ==============================
echo  URL:    http://localhost:8050
echo  Health: http://localhost:8050/health
echo  API:    POST http://localhost:8050/api/analysis/fill
echo.
echo  Press CTRL+C to stop
echo.

python standalone_server.py

pause
