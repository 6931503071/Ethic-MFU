# START_BACKEND.ps1
# วิธีรัน: คลิกขวา → "Run with PowerShell"
# หรือพิมพ์ใน PowerShell: .\START_BACKEND.ps1

Set-Location -Path $PSScriptRoot

Write-Host ""
Write-Host " AI Document Generator Backend" -ForegroundColor Cyan
Write-Host " ==============================" -ForegroundColor Cyan
Write-Host " URL:    http://localhost:8050" -ForegroundColor Green
Write-Host " Health: http://localhost:8050/health" -ForegroundColor Green
Write-Host " API:    POST http://localhost:8050/api/analysis/fill" -ForegroundColor Green
Write-Host ""
Write-Host " Press CTRL+C to stop" -ForegroundColor Yellow
Write-Host ""

python standalone_server.py
