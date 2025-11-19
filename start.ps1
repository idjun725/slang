# Slang Bridge Server Startup Script
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

Write-Host "Starting Slang Bridge servers..." -ForegroundColor Green

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $scriptDir "backend"
$frontendPath = Join-Path $scriptDir "frontend"

Write-Host ""
Write-Host "[1/2] Starting backend server..." -ForegroundColor Yellow
Write-Host "Backend path: $backendPath" -ForegroundColor Gray

$backendCmd = @"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
`$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null
cd '$backendPath'
`$env:PYTHONUTF8=1
python main.py
"@
$backendEncoded = [System.Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($backendCmd))
Start-Process powershell -ArgumentList "-NoExit", "-EncodedCommand", $backendEncoded

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "[2/2] Starting frontend server..." -ForegroundColor Yellow
Write-Host "Frontend path: $frontendPath" -ForegroundColor Gray

$frontendCmd = @"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
`$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null
cd '$frontendPath'
python -m http.server 8001
"@
$frontendEncoded = [System.Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($frontendCmd))
Start-Process powershell -ArgumentList "-NoExit", "-EncodedCommand", $frontendEncoded

Write-Host ""
Write-Host "Servers started!" -ForegroundColor Green
Write-Host "Backend: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:8001" -ForegroundColor Cyan
Write-Host "Open http://localhost:8001/index.html in your browser" -ForegroundColor Magenta
Write-Host ""
Read-Host "Press Enter to continue"
