@echo off
cd /d "%~dp0"

echo.
echo  Ethic-MFU Backend
echo  =================
echo  URL: http://127.0.0.1:8050
echo  Docs: http://127.0.0.1:8050/docs
echo.
echo  Press CTRL+C to stop
echo.

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8050
) else (
    python -m uvicorn app.main:app --reload --port 8050
)

pause
