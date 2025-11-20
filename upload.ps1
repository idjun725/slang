# GitHub Upload Script
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

Write-Host "GitHub 업로드 스크립트" -ForegroundColor Green
Write-Host ""

# 현재 상태 확인
Write-Host "[1/4] Git 상태 확인 중..." -ForegroundColor Yellow
git status --short

Write-Host ""
$hasChanges = git diff --quiet --exit-code 2>$null; $hasStaged = git diff --cached --quiet --exit-code 2>$null

if (-not $hasChanges -and -not $hasStaged) {
    $untracked = git ls-files --others --exclude-standard
    if (-not $untracked) {
        Write-Host "업로드할 변경사항이 없습니다." -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit
    }
}

# 제외할 폴더 확인
Write-Host ""
Write-Host "[2/4] 파일 스테이징 중..." -ForegroundColor Yellow
Write-Host "제외 폴더: backend/training, data, backend/__pycache__, backend/.env" -ForegroundColor Gray

# 제외 폴더를 제외하고 스테이징
git add . ':!backend/training' ':!data' ':!backend/__pycache__' ':!backend/.env'

# .env 파일이 실수로 포함되었는지 확인
$stagedFiles = git diff --cached --name-only
if ($stagedFiles -contains 'backend/.env') {
    Write-Host "경고: .env 파일이 스테이징되었습니다. 제거합니다..." -ForegroundColor Yellow
    git reset HEAD backend/.env
}

Write-Host "스테이징 완료" -ForegroundColor Green

# 커밋 메시지 입력
Write-Host ""
Write-Host "[3/4] 커밋 메시지 입력" -ForegroundColor Yellow
$defaultMessage = "Update code"
$commitMessage = Read-Host "커밋 메시지 (기본값: '$defaultMessage')"

if ([string]::IsNullOrWhiteSpace($commitMessage)) {
    $commitMessage = $defaultMessage
}

# 커밋
Write-Host ""
Write-Host "[4/4] 커밋 및 푸시 중..." -ForegroundColor Yellow
git commit -m $commitMessage

if ($LASTEXITCODE -eq 0) {
    Write-Host "커밋 성공!" -ForegroundColor Green
    Write-Host ""
    Write-Host "GitHub에 푸시 중..." -ForegroundColor Yellow
    git push origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "업로드 완료!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "푸시 실패. 네트워크 문제나 권한 문제일 수 있습니다." -ForegroundColor Red
    }
} else {
    Write-Host ""
    Write-Host "커밋 실패. 변경사항이 없거나 오류가 발생했습니다." -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to exit"

