# Slang Bridge 서버 시작 스크립트
Write-Host "Slang Bridge 서버 시작 중..." -ForegroundColor Green

Write-Host ""
Write-Host "[1/2] 백엔드 서버 시작..." -ForegroundColor Yellow
$backendPath = "D:\251615\SlangProject\slang-bridge\backend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; python main.py"

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "[2/2] 프론트엔드 서버 시작..." -ForegroundColor Yellow
$frontendPath = "D:\251615\SlangProject\slang-bridge\frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; python -m http.server 8001"

Write-Host ""
Write-Host "서버가 시작되었습니다!" -ForegroundColor Green
Write-Host "백엔드: http://localhost:8000" -ForegroundColor Cyan
Write-Host "프론트엔드: http://localhost:8001" -ForegroundColor Cyan
Write-Host "브라우저에서 http://localhost:8001/index.html 을 열어보세요." -ForegroundColor Magenta
Write-Host ""
Read-Host "Press Enter to continue"