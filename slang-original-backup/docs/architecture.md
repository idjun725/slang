# 아키텍처 문서

## 시스템 개요

슬랭 브릿지는 마이크로서비스 지향 아키텍처를 사용하여 확장 가능하고 유지보수가 용이한 구조로 설계되었습니다.

## 시스템 구성도

```
┌─────────────┐
│   사용자    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│        Next.js Frontend         │
│   (SSR/SSG + React Query)       │
└───────────┬─────────────────────┘
            │
            ▼
    ┌───────────────┐
    │   Nginx/CDN   │
    └───────┬───────┘
            │
            ▼
┌─────────────────────────────────┐
│      FastAPI Backend API        │
│  (RESTful + WebSocket)          │
└───────┬─────────────────────────┘
        │
        ├────────────────────┐
        │                    │
        ▼                    ▼
┌─────────────┐    ┌──────────────┐
│ PostgreSQL  │    │    Redis     │
│  (메인 DB)  │    │  (캐시/큐)   │
└─────────────┘    └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │    Celery    │
                   │ Worker/Beat  │
                   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │   Crawler    │
                   │  (디시인사이드)│
                   └──────────────┘
```

## 컴포넌트 상세

### 1. Frontend (Next.js)

**역할**: 사용자 인터페이스 제공

**기술 스택**:
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- React Query (데이터 페칭)
- Zustand (상태 관리)

**주요 페이지**:
- `/` - 홈페이지
- `/ranking` - 신조어 랭킹
- `/dictionary` - 신조어 사전
- `/newsletter` - 뉴스레터 구독

### 2. Backend (FastAPI)

**역할**: REST API 제공, 비즈니스 로직 처리

**기술 스택**:
- FastAPI
- SQLAlchemy (ORM)
- Pydantic (데이터 검증)
- Celery (비동기 작업)

**주요 모듈**:
- `api/`: REST API 엔드포인트
- `models/`: 데이터베이스 모델
- `schemas/`: Pydantic 스키마
- `services/`: 비즈니스 로직
- `tasks/`: Celery 작업

### 3. Database (PostgreSQL)

**역할**: 메인 데이터 저장소

**주요 테이블**:
- `slangs`: 신조어 정보
- `users`: 사용자 정보
- `newsletters`: 뉴스레터 발송 기록

### 4. Cache & Queue (Redis)

**역할**: 
- 캐싱: API 응답, 랭킹 데이터
- 메시지 큐: Celery 브로커

### 5. Task Queue (Celery)

**역할**: 비동기 작업 처리

**주요 작업**:
- 크롤링 (매시간)
- 랭킹 업데이트 (매일)
- 뉴스레터 발송 (매주 월요일)

### 6. Crawler

**역할**: 디시인사이드 데이터 수집

**프로세스**:
1. 주요 갤러리 게시물 제목 크롤링
2. 형태소 분석으로 신조어 추출
3. 빈도 계산 및 DB 저장
4. AI 기반 의미 분석 (옵션)

## 데이터 플로우

### 1. 신조어 수집 플로우

```
Celery Beat (매시간)
  → Crawler Task 실행
    → 디시인사이드 크롤링
      → 게시물 제목 수집
        → 신조어 추출
          → DB 저장
            → 랭킹 업데이트
```

### 2. 뉴스레터 발송 플로우

```
Celery Beat (매주 월요일 09:00)
  → Newsletter Task 실행
    → DB에서 상위 5개 신조어 조회
      → 구독자 목록 조회
        → SendGrid API 호출
          → 이메일 발송
            → 발송 기록 저장
```

### 3. API 요청 플로우

```
사용자 요청
  → Next.js Frontend
    → API 호출
      → FastAPI Backend
        → Redis 캐시 확인
          → (캐시 없음) PostgreSQL 조회
            → 결과 캐싱
              → 응답 반환
```

## 보안

### 인증 및 권한

- JWT 기반 인증 (향후 추가)
- API Key 인증 (관리자 기능)

### 데이터 보호

- HTTPS 강제
- SQL Injection 방어 (SQLAlchemy ORM)
- XSS 방어 (입력 검증)
- CORS 정책

### Rate Limiting

- Redis 기반 요청 제한
- IP별, 사용자별 제한

## 확장성

### 수평 확장

- Stateless API 설계
- Load Balancer 추가
- Redis Cluster
- PostgreSQL Replication

### 수직 확장

- Worker 프로세스 증가
- DB Connection Pool 확대
- 캐시 메모리 증가

## 모니터링

### 메트릭

- API 응답 시간
- 에러율
- 크롤링 성공률
- 이메일 발송 성공률

### 로그

- 애플리케이션 로그
- 액세스 로그
- 에러 로그
- Celery 작업 로그

### 알림

- Sentry (에러 추적)
- Slack/Discord (알림)
- CloudWatch (AWS)

## 성능 최적화

### 캐싱 전략

1. **Redis 캐싱**
   - 랭킹 데이터: 1시간 TTL
   - 신조어 상세: 30분 TTL
   - 검색 결과: 10분 TTL

2. **CDN 캐싱**
   - 정적 파일
   - 이미지
   - API 응답 (일부)

### 데이터베이스 최적화

1. **인덱싱**
   - word (UNIQUE INDEX)
   - frequency (DESC INDEX)
   - category (INDEX)
   - last_updated (INDEX)

2. **쿼리 최적화**
   - N+1 문제 방지 (eager loading)
   - 페이지네이션
   - 불필요한 컬럼 제외

### 비동기 처리

- 무거운 작업 Celery로 처리
- 이메일 발송 비동기화
- 크롤링 병렬 처리

## 재해 복구

### 백업

- PostgreSQL 자동 백업 (매일)
- S3 저장 (30일 보관)
- Redis AOF/RDB 백업

### 복구 전략

- DB 복구: 백업 파일에서 복원
- 서비스 복구: Docker 재시작
- 데이터 손실 최소화: Replication

## 향후 개선 사항

1. **GraphQL API 추가**
2. **실시간 알림 (WebSocket)**
3. **머신러닝 기반 신조어 예측**
4. **다국어 지원**
5. **모바일 앱 개발**
6. **사용자 커뮤니티 기능**


