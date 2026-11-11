# Ethic-MFU Backend Startup Script
# วิธีรัน: คลิกขวา → "Run with PowerShell"
# หรือพิมพ์ใน PowerShell: .\START_BACKEND.ps1

Set-Location -Path $PSScriptRoot

Write-Host ""
Write-Host " Ethic-MFU Backend" -ForegroundColor Cyan
Write-Host " ==================" -ForegroundColor Cyan
Write-Host " URL:  http://127.0.0.1:8050" -ForegroundColor Green
Write-Host " Docs: http://127.0.0.1:8050/docs" -ForegroundColor Green
Write-Host ""
Write-Host " Press CTRL+C to stop" -ForegroundColor Yellow
Write-Host ""

$python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
& $python -m uvicorn app.main:app --reload --port 8050
