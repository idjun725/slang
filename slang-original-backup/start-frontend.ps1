# Frontend 시작 스크립트 (PowerShell)

Write-Host "슬랭 브릿지 Frontend 시작 중..." -ForegroundColor Green

# Frontend 디렉토리로 이동
Set-Location frontend

# node_modules 확인
if (-Not (Test-Path "node_modules")) {
    Write-Host "의존성 설치 중..." -ForegroundColor Yellow
    npm install
}

# 개발 서버 실행
Write-Host "Frontend 서버 실행 중..." -ForegroundColor Green
Write-Host "URL: http://localhost:3000" -ForegroundColor Cyan
npm run dev


