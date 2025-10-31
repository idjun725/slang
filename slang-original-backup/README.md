# 슬랭 브릿지 (Slang Bridge)

세대 간 소통을 위한 신조어 학습 플랫폼

## 프로젝트 개요

디시인사이드 등 온라인 커뮤니티에서 실시간으로 사용되는 신조어를 수집·분석하여, 모든 세대가 최신 언어 트렌드를 쉽게 파악할 수 있도록 돕는 웹 플랫폼입니다.

## 주요 기능

- 📊 실시간 신조어 랭킹 시스템
- 📧 주간 신조어 이메일 뉴스레터
- 🔍 신조어 검색 및 사전
- 👥 커뮤니티 피드백 시스템

## 기술 스택

### Frontend
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- React Query
- Zustand

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy
- Celery (작업 큐)
- Redis (캐싱 및 큐)

### Database
- PostgreSQL 15+
- Redis 7+

### Infrastructure
- Docker & Docker Compose
- SendGrid (이메일 발송)

## 프로젝트 구조

```
slang/
├── frontend/          # Next.js 프론트엔드
├── backend/           # FastAPI 백엔드
├── crawler/           # 크롤링 시스템
├── database/          # DB 스키마 및 마이그레이션
├── docker/            # Docker 설정 파일
└── docs/              # 문서
```

## 시작하기

### 필요 사항

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### 설치

1. 저장소 클론
```bash
git clone https://github.com/yourusername/slang-bridge.git
cd slang-bridge
```

2. 환경 변수 설정
```bash
# 루트 디렉토리에서
cp .env.example .env
# .env 파일을 편집하여 필요한 값 설정
```

3. Docker로 실행 (권장)
```bash
docker-compose up -d
```

4. 또는 로컬에서 개별 실행

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### 데이터베이스 마이그레이션

```bash
cd backend
alembic upgrade head
```

### 크롤러 실행

```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info
celery -A app.tasks.celery_app beat --loglevel=info
```

## 개발 가이드

### 코드 스타일

- Python: Black, isort, flake8
- TypeScript: ESLint, Prettier

### 테스트

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## API 문서

개발 서버 실행 후 다음 URL에서 확인:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 배포

배포 가이드는 `docs/deployment.md`를 참조하세요.

## 라이센스

MIT License

## 기여

기여 가이드는 `CONTRIBUTING.md`를 참조하세요.

## 문의

- 이슈: [GitHub Issues](https://github.com/yourusername/slang-bridge/issues)
- 이메일: contact@slangbridge.com


