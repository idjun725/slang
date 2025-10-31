# 로컬 개발 환경 설정 가이드 (Docker 없이)

## 필요한 프로그램

### 1. Python 3.11+
- 다운로드: https://www.python.org/downloads/
- 설치 시 "Add Python to PATH" 체크

### 2. Node.js 18+
- 다운로드: https://nodejs.org/

### 3. PostgreSQL 15+
- 다운로드: https://www.postgresql.org/download/windows/
- 설치 후 pgAdmin으로 관리

### 4. Redis
- Memurai (Windows용): https://www.memurai.com/get-memurai
- 또는 WSL2에서 Redis 실행

## 설정 단계

### 1. 데이터베이스 생성

PostgreSQL 설치 후 pgAdmin 또는 psql로 실행:

```sql
CREATE DATABASE slang_db;
CREATE USER slang_user WITH PASSWORD 'slang_password';
GRANT ALL PRIVILEGES ON DATABASE slang_db TO slang_user;
```

### 2. 환경 변수 설정

루트 디렉토리의 `.env` 파일 편집:

```env
DATABASE_URL=postgresql://slang_user:slang_password@localhost:5432/slang_db
REDIS_URL=redis://localhost:6379/0
SENDGRID_API_KEY=your-api-key
# ... 나머지 설정
```

### 3. Backend 설정 및 실행

```bash
# 1. Backend 디렉토리로 이동
cd backend

# 2. 가상환경 생성
python -m venv venv

# 3. 가상환경 활성화 (PowerShell)
.\venv\Scripts\Activate.ps1

# 4. 의존성 설치
pip install -r requirements.txt

# 5. 데이터베이스 마이그레이션
alembic upgrade head

# 6. 서버 실행
uvicorn app.main:app --reload
```

Backend API: http://localhost:8000

### 4. Frontend 설정 및 실행

새 터미널 창에서:

```bash
# 1. Frontend 디렉토리로 이동
cd frontend

# 2. 의존성 설치
npm install

# 3. 개발 서버 실행
npm run dev
```

Frontend: http://localhost:3000

### 5. Celery Worker 실행 (옵션 - 크롤링 기능)

새 터미널 창에서:

```bash
cd backend
.\venv\Scripts\Activate.ps1

# Worker 실행
celery -A app.tasks.celery_app worker --loglevel=info

# Beat 실행 (스케줄러 - 별도 터미널)
celery -A app.tasks.celery_app beat --loglevel=info
```

## 실행 순서 요약

1. PostgreSQL 서버 시작 (서비스로 자동 시작)
2. Redis 서버 시작 (Memurai 서비스)
3. Backend 서버 실행
4. Frontend 개발 서버 실행
5. (옵션) Celery Worker 및 Beat 실행

## 트러블슈팅

### PostgreSQL 연결 오류
```bash
# PostgreSQL 서비스 확인
services.msc
# "postgresql-x64-15" 서비스 시작
```

### Redis 연결 오류
```bash
# Memurai 서비스 확인 또는
# Redis CLI 테스트
redis-cli ping
```

### Python 패키지 설치 오류
```bash
# pip 업그레이드
python -m pip install --upgrade pip

# 개별 설치 시도
pip install fastapi uvicorn sqlalchemy
```

### Node 모듈 설치 오류
```bash
# 캐시 클리어
npm cache clean --force
npm install
```

## 개발 팁

### Backend만 테스트
- API 문서: http://localhost:8000/docs
- Swagger UI에서 직접 API 테스트 가능

### Frontend만 개발
- Backend 없이도 UI 개발 가능
- Mock 데이터 사용 권장

### 빠른 재시작
```bash
# Backend
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload

# Frontend
cd frontend
npm run dev
```


