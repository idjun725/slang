# Backend 시작 스크립트 (PowerShell)

Write-Host "슬랭 브릿지 Backend 시작 중..." -ForegroundColor Green

# Backend 디렉토리로 이동
Set-Location backend

# 가상환경 확인
if (-Not (Test-Path "venv")) {
    Write-Host "가상환경 생성 중..." -ForegroundColor Yellow
    python -m venv venv
}

# 가상환경 활성화
Write-Host "가상환경 활성화 중..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# 의존성 설치 확인
Write-Host "의존성 확인 중..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

# 데이터베이스 마이그레이션
Write-Host "데이터베이스 마이그레이션 중..." -ForegroundColor Yellow
alembic upgrade head

# 서버 실행
Write-Host "Backend 서버 실행 중..." -ForegroundColor Green
Write-Host "API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Docs: http://localhost:8000/docs" -ForegroundColor Cyan
uvicorn app.main:app --reload


