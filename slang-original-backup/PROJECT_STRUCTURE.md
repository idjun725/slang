# 프로젝트 구조

```
slang/
│
├── frontend/                      # Next.js 프론트엔드
│   ├── src/
│   │   ├── app/                  # Next.js App Router
│   │   │   ├── layout.tsx        # 루트 레이아웃
│   │   │   └── page.tsx          # 홈페이지
│   │   ├── components/           # React 컴포넌트
│   │   │   └── Providers.tsx     # React Query Provider
│   │   ├── lib/                  # 유틸리티
│   │   │   └── api.ts            # API 클라이언트
│   │   ├── styles/               # 스타일
│   │   │   └── globals.css       # 글로벌 CSS
│   │   └── types/                # TypeScript 타입
│   │       └── index.ts          # 공통 타입
│   ├── public/                   # 정적 파일
│   ├── package.json              # Node.js 의존성
│   ├── tsconfig.json             # TypeScript 설정
│   ├── next.config.js            # Next.js 설정
│   ├── tailwind.config.js        # Tailwind CSS 설정
│   └── Dockerfile                # Docker 이미지
│
├── backend/                       # FastAPI 백엔드
│   ├── app/
│   │   ├── api/                  # API 엔드포인트
│   │   │   ├── __init__.py
│   │   │   └── endpoints/
│   │   │       ├── slangs.py     # 신조어 API
│   │   │       ├── ranking.py    # 랭킹 API
│   │   │       ├── newsletter.py # 뉴스레터 API
│   │   │       └── users.py      # 사용자 API
│   │   ├── core/                 # 핵심 설정
│   │   │   ├── config.py         # 환경 설정
│   │   │   ├── database.py       # DB 연결
│   │   │   └── redis_client.py   # Redis 연결
│   │   ├── models/               # SQLAlchemy 모델
│   │   │   ├── slang.py          # 신조어 모델
│   │   │   └── user.py           # 사용자 모델
│   │   ├── schemas/              # Pydantic 스키마
│   │   │   ├── slang.py          # 신조어 스키마
│   │   │   ├── user.py           # 사용자 스키마
│   │   │   └── newsletter.py     # 뉴스레터 스키마
│   │   ├── services/             # 비즈니스 로직
│   │   │   ├── crawler_service.py   # 크롤링 서비스
│   │   │   └── email_service.py     # 이메일 서비스
│   │   ├── tasks/                # Celery 작업
│   │   │   ├── celery_app.py     # Celery 앱
│   │   │   ├── crawler_tasks.py  # 크롤링 작업
│   │   │   └── newsletter_tasks.py # 뉴스레터 작업
│   │   └── main.py               # FastAPI 앱
│   ├── alembic/                  # DB 마이그레이션
│   │   ├── versions/             # 마이그레이션 파일
│   │   ├── env.py                # Alembic 환경
│   │   └── script.py.mako        # 마이그레이션 템플릿
│   ├── tests/                    # 테스트
│   │   └── test_main.py          # 메인 테스트
│   ├── requirements.txt          # Python 의존성
│   ├── Dockerfile                # Docker 이미지
│   ├── alembic.ini               # Alembic 설정
│   ├── pytest.ini                # Pytest 설정
│   ├── pyproject.toml            # Python 프로젝트 설정
│   └── .flake8                   # Flake8 설정
│
├── database/                      # 데이터베이스 관련
│   ├── migrations/               # 수동 마이그레이션 (필요시)
│   ├── init.sql                  # 초기화 스크립트
│   ├── schema.sql                # 스키마 참고용
│   └── README.md                 # DB 문서
│
├── docs/                          # 문서
│   ├── architecture.md           # 아키텍처 문서
│   ├── api.md                    # API 문서
│   └── deployment.md             # 배포 가이드
│
├── .gitignore                    # Git 제외 파일
├── .dockerignore                 # Docker 제외 파일
├── docker-compose.yml            # Docker Compose 설정
├── env.example                   # 환경 변수 예시
├── Makefile                      # Make 명령어
├── README.md                     # 프로젝트 README
├── PRD.md                        # 제품 요구사항 문서
├── CONTRIBUTING.md               # 기여 가이드
├── LICENSE                       # 라이센스
└── PROJECT_STRUCTURE.md          # 이 파일
```

## 주요 디렉토리 설명

### Frontend (`frontend/`)
- Next.js 14 기반 React 애플리케이션
- TypeScript + Tailwind CSS
- React Query를 통한 데이터 페칭
- SSR/SSG 지원

### Backend (`backend/`)
- FastAPI 기반 REST API
- SQLAlchemy ORM
- Celery 비동기 작업
- Alembic DB 마이그레이션

### Database (`database/`)
- PostgreSQL 스키마 정의
- 초기화 및 마이그레이션 스크립트
- DB 관련 문서

### Docs (`docs/`)
- 프로젝트 문서 모음
- 아키텍처, API, 배포 가이드

## 주요 파일 설명

### 설정 파일
- `docker-compose.yml`: 모든 서비스 오케스트레이션
- `env.example`: 환경 변수 템플릿
- `Makefile`: 개발 편의 명령어

### 문서 파일
- `README.md`: 프로젝트 개요 및 시작 가이드
- `PRD.md`: 제품 요구사항 문서
- `CONTRIBUTING.md`: 기여 가이드
- `LICENSE`: MIT 라이센스

## 개발 워크플로우

1. **환경 설정**: `cp env.example .env` 후 편집
2. **의존성 설치**: `make install`
3. **개발 서버 실행**: `make dev`
4. **테스트**: `make test`
5. **코드 포맷팅**: `make format`
6. **린트**: `make lint`

## 배포 워크플로우

1. **이미지 빌드**: `make build`
2. **서비스 시작**: `make up`
3. **마이그레이션**: `make migrate`
4. **로그 확인**: `make logs`

## 기술 스택 요약

**Frontend**
- Next.js 14, React 18, TypeScript
- Tailwind CSS, React Query, Zustand

**Backend**
- Python 3.11, FastAPI, SQLAlchemy
- Celery, Redis, PostgreSQL

**Infrastructure**
- Docker, Docker Compose
- Nginx (리버스 프록시)
- SendGrid (이메일)

**DevOps**
- GitHub Actions (CI/CD)
- Sentry (모니터링)
- AWS/Vercel (호스팅)

## 다음 단계

1. 환경 변수 설정
2. Docker Compose로 서비스 실행
3. 데이터베이스 마이그레이션
4. 크롤러 테스트
5. 이메일 발송 테스트
6. 프론트엔드 개발
7. API 테스트
8. 배포

자세한 내용은 각 문서를 참조하세요.


