# Slang Bridge - 세대 간 소통 격차 해소 웹사이트

## 프로젝트 개요
최근 사용된 신조어를 조회하고 랭킹을 제공하는 웹사이트입니다. 디시인사이드 게시물 제목을 기반으로 신조어를 수집하고, 주간 뉴스레터를 제공합니다.

## 주요 기능
- 🔐 이메일/비밀번호 기반 로그인 시스템
- 📊 신조어 랭킹 조회
- 📧 뉴스레터 구독 ON/OFF
- 🤖 자동 크롤링 및 분석 (매일 09:00)
- 📬 주간 뉴스레터 자동 발송 (매주 월요일 10:00)

## 기술 스택
- **Backend**: FastAPI + SQLite
- **Frontend**: HTML + CSS + JavaScript (Tailwind 스타일)
- **크롤링**: BeautifulSoup4 + requests
- **분석**: 패턴 기반 신조어 추출
- **이메일**: Gmail SMTP
- **스케줄링**: schedule 라이브러리

## 설치 및 실행

### 1. 백엔드 실행
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 2. 프론트엔드 실행
```bash
cd frontend
python -m http.server 8001
```

### 3. 브라우저 접속
- 메인 페이지: http://localhost:8001
- API 문서: http://localhost:8000/docs

## API 엔드포인트
- `POST /register` - 회원가입
- `POST /login` - 로그인
- `POST /logout` - 로그아웃
- `GET /me` - 현재 사용자 정보
- `GET /ranking` - 신조어 랭킹 조회
- `POST /subscription/toggle` - 뉴스레터 구독 토글
- `GET /subscription/status` - 구독 상태 조회
- `POST /crawl` - 크롤링 실행
- `GET /stats` - 통계 정보 조회

## 데이터베이스
SQLite 데이터베이스 (`data/slangs.db`)에 다음 테이블이 있습니다:
- `users`: 사용자 정보 (username, email, password, newsletter_subscribed)
- `slangs`: 신조어 데이터
- `subscribers`: 구독자 정보 (레거시)

## 환경 설정
Gmail SMTP를 사용하려면 환경변수를 설정하세요:
- `GMAIL_USER`: Gmail 계정
- `GMAIL_PASS`: 앱 비밀번호

