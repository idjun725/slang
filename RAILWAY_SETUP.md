# Railway 배포 설정 가이드

Railway로 백엔드를 배포하는 방법입니다.

## 1. Railway 프로젝트 설정

1. Railway 대시보드에서 프로젝트 선택 또는 새로 생성
2. GitHub 저장소 연결
3. 서비스 생성

## 2. 환경 변수 설정

Railway 대시보드 → Variables 탭에서 다음 환경 변수들을 설정하세요:

### 필수 환경 변수:

- **OPENAI_API_KEY**: OpenAI API 키
- **USE_NLP_FILTER**: `true` (NLP 필터링 활성화)
- **NLP_MODEL_PATH**: (선택사항) 모델 경로, 없으면 기본 경로 사용

### 모델 다운로드 (선택사항):

NLP 모델을 사용하려면:

- **MODEL_DOWNLOAD_URL**: 모델 파일 다운로드 URL
  - Google Drive: `https://drive.google.com/uc?export=download&id=FILE_ID`
  - GitHub Releases: `https://github.com/idjun725/slang/releases/download/v1.0.0/model.zip`
- **MODEL_PARTS**: (여러 부분으로 나뉜 경우) 부분 개수

### 기타 환경 변수:

- **NAVER_CLIENT_ID**: 네이버 API 클라이언트 ID
- **NAVER_CLIENT_SECRET**: 네이버 API 클라이언트 시크릿
- **GMAIL_USER**: Gmail 계정 (뉴스레터 발송용)
- **GMAIL_PASS**: Gmail 앱 비밀번호
- **YOUTUBE_API_KEY**: YouTube API 키

## 3. 빌드 설정

Railway는 `nixpacks.toml` 파일을 자동으로 인식하여 빌드합니다.

- Python 3.11 사용
- `backend/requirements.txt`에서 의존성 설치
- `torch` CPU 버전 자동 설치
- 모델 다운로드 스크립트 실행 (MODEL_DOWNLOAD_URL이 설정된 경우)

## 4. 배포 확인

1. Railway 대시보드 → Deployments 탭에서 배포 상태 확인
2. Logs 탭에서 빌드 및 실행 로그 확인
3. 서비스 URL 확인 (예: `https://slang-production.up.railway.app`)

## 5. 프론트엔드 설정

Netlify에서 프론트엔드를 배포할 때:

1. Netlify 대시보드 → Site settings → Environment variables
2. **API_BASE_URL** 환경 변수 추가:
   - 값: Railway 서비스 URL (예: `https://slang-production.up.railway.app`)

## 6. 크롤러 실행

### 방법 1: Railway 대시보드에서 실행

1. Railway 대시보드 → 서비스 선택
2. "Run Command" 또는 "Shell" 탭
3. 다음 명령 실행:
   ```bash
   cd backend
   python run_crawler.py
   ```

### 방법 2: 프론트엔드에서 실행

1. 프론트엔드에서 "크롤러 실행" 버튼 클릭
2. `/crawl` API 엔드포인트가 백그라운드에서 크롤링 실행

## 7. 문제 해결

### 모델 다운로드 실패

- `MODEL_DOWNLOAD_URL` 환경 변수가 올바르게 설정되었는지 확인
- 모델이 없어도 크롤러는 동작하지만 NLP 필터링은 비활성화됩니다

### torch 설치 실패

- Railway 빌드 로그에서 오류 확인
- `nixpacks.toml`의 torch 설치 명령 확인

### 서비스가 시작되지 않음

- Railway Logs 탭에서 오류 메시지 확인
- 환경 변수가 모두 설정되었는지 확인
- 포트가 `$PORT` 환경 변수를 사용하는지 확인

