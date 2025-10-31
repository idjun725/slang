# 데이터베이스 스키마

## 개요

슬랭 브릿지 프로젝트의 데이터베이스 스키마 문서입니다.

## 테이블 구조

### slangs (신조어)

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | SERIAL | 기본키 |
| word | VARCHAR(100) | 신조어 (유니크) |
| meaning | TEXT | 의미 |
| usage_examples | JSONB | 사용 예시 배열 |
| frequency | INTEGER | 사용 빈도 |
| rank | INTEGER | 현재 순위 |
| rank_change | INTEGER | 순위 변화 |
| category | VARCHAR(50) | 카테고리 |
| source | VARCHAR(100) | 출처 |
| trend_data | JSONB | 트렌드 데이터 |
| first_seen | TIMESTAMP | 최초 발견 일시 |
| last_updated | TIMESTAMP | 마지막 업데이트 |
| created_at | TIMESTAMP | 생성 일시 |

### users (사용자)

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | SERIAL | 기본키 |
| email | VARCHAR(255) | 이메일 (유니크) |
| is_subscribed | BOOLEAN | 구독 여부 |
| subscription_preferences | JSONB | 구독 설정 |
| created_at | TIMESTAMP | 생성 일시 |
| updated_at | TIMESTAMP | 수정 일시 |

### newsletters (뉴스레터 발송 기록)

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | SERIAL | 기본키 |
| sent_date | TIMESTAMP | 발송 일시 |
| top_slangs | JSONB | 포함된 신조어 ID 배열 |
| recipient_count | INTEGER | 수신자 수 |
| open_count | INTEGER | 오픈 수 |
| click_count | INTEGER | 클릭 수 |
| created_at | TIMESTAMP | 생성 일시 |

## 마이그레이션

### 초기 마이그레이션 생성

```bash
cd backend
alembic revision --autogenerate -m "Initial migration"
```

### 마이그레이션 적용

```bash
alembic upgrade head
```

### 마이그레이션 롤백

```bash
alembic downgrade -1
```

## 초기 데이터

`init.sql` 파일에 초기 데이터를 추가할 수 있습니다.


