# API 문서

## Base URL

- Development: `http://localhost:8000/api/v1`
- Production: `https://api.slangbridge.com/api/v1`

## 엔드포인트

### 신조어 (Slangs)

#### 신조어 목록 조회

```http
GET /slangs?skip=0&limit=100&category=게임
```

**응답**

```json
[
  {
    "id": 1,
    "word": "ㅇㅈ",
    "meaning": "인정",
    "usage_examples": ["ㅇㅈ합니다", "이건 ㅇㅈ해야함"],
    "frequency": 1234,
    "rank": 1,
    "rank_change": 2,
    "category": "일반",
    "source": "dcinside",
    "first_seen": "2025-01-01T00:00:00Z",
    "last_updated": "2025-01-20T12:00:00Z"
  }
]
```

#### 신조어 상세 조회

```http
GET /slangs/{slang_id}
```

#### 신조어 검색

```http
GET /slangs/search/{word}
```

### 랭킹 (Ranking)

#### 랭킹 조회

```http
GET /ranking?period=week&limit=10&category=게임
```

**파라미터**

- `period`: today | week | month
- `limit`: 1-100
- `category`: 카테고리 (옵션)

**응답**

```json
[
  {
    "id": 1,
    "word": "ㅇㅈ",
    "meaning": "인정",
    "frequency": 1234,
    "rank": 1,
    "rank_change": 2
  }
]
```

#### 급상승 신조어

```http
GET /ranking/trending?limit=10
```

### 뉴스레터 (Newsletter)

#### 뉴스레터 구독

```http
POST /newsletter/subscribe
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**응답**

```json
{
  "success": true,
  "message": "뉴스레터 구독이 완료되었습니다",
  "email": "user@example.com"
}
```

#### 구독 취소

```http
POST /newsletter/unsubscribe
Content-Type: application/json

{
  "email": "user@example.com"
}
```

#### 뉴스레터 발송 기록

```http
GET /newsletter/history?limit=10
```

### 사용자 (Users)

#### 사용자 생성

```http
POST /users
Content-Type: application/json

{
  "email": "user@example.com",
  "is_subscribed": true
}
```

#### 사용자 조회

```http
GET /users/{user_id}
```

## 에러 코드

| 코드 | 의미 |
|------|------|
| 200 | 성공 |
| 201 | 생성됨 |
| 400 | 잘못된 요청 |
| 404 | 찾을 수 없음 |
| 500 | 서버 오류 |

## 에러 응답 형식

```json
{
  "detail": "에러 메시지"
}
```

## Rate Limiting

- 기본: 100 requests/minute
- 인증된 사용자: 1000 requests/minute

## 인증 (향후 추가 예정)

```http
Authorization: Bearer {token}
```


