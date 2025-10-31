# 배포 가이드

## Docker Compose로 배포 (권장)

### 1. 환경 변수 설정

```bash
cp env.example .env
# .env 파일 편집
```

### 2. Docker Compose 실행

```bash
docker-compose up -d
```

### 3. 데이터베이스 마이그레이션

```bash
docker-compose exec backend alembic upgrade head
```

### 4. 서비스 확인

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 개별 서비스 배포

### Backend (AWS EC2 예시)

1. EC2 인스턴스 생성 (Ubuntu 22.04)
2. 필요한 패키지 설치

```bash
sudo apt update
sudo apt install python3.11 python3-pip postgresql redis-server
```

3. 애플리케이션 배포

```bash
git clone https://github.com/yourusername/slang-bridge.git
cd slang-bridge/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. 환경 변수 설정

```bash
cp ../env.example .env
# .env 편집
```

5. Gunicorn으로 실행

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

6. Systemd 서비스 등록

```bash
sudo nano /etc/systemd/system/slang-backend.service
```

```ini
[Unit]
Description=Slang Bridge Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/slang-bridge/backend
Environment="PATH=/home/ubuntu/slang-bridge/backend/venv/bin"
ExecStart=/home/ubuntu/slang-bridge/backend/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable slang-backend
sudo systemctl start slang-backend
```

### Frontend (Vercel 예시)

1. Vercel CLI 설치

```bash
npm install -g vercel
```

2. 프로젝트 배포

```bash
cd frontend
vercel --prod
```

3. 환경 변수 설정 (Vercel Dashboard)

- `NEXT_PUBLIC_API_URL`: Backend API URL

### Celery Worker 및 Beat

```bash
# Worker
celery -A app.tasks.celery_app worker --loglevel=info -D

# Beat (스케줄러)
celery -A app.tasks.celery_app beat --loglevel=info -D
```

## Nginx 설정 (리버스 프록시)

```nginx
server {
    listen 80;
    server_name api.slangbridge.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## SSL 인증서 (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.slangbridge.com
```

## 모니터링

### Sentry 설정

```python
import sentry_sdk

sentry_sdk.init(
    dsn="YOUR_SENTRY_DSN",
    environment="production",
)
```

### 로그 관리

- CloudWatch (AWS)
- Elasticsearch + Kibana
- Grafana + Loki

## 백업

### 데이터베이스 백업

```bash
# 백업
pg_dump -h localhost -U slang_user slang_db > backup.sql

# 복원
psql -h localhost -U slang_user slang_db < backup.sql
```

### 자동 백업 스크립트

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U slang_user slang_db | gzip > /backups/slang_db_$DATE.sql.gz
# S3 업로드
aws s3 cp /backups/slang_db_$DATE.sql.gz s3://slang-backups/
```

## 성능 최적화

1. **CDN 사용**: CloudFlare, CloudFront
2. **캐싱**: Redis 활용
3. **DB 인덱싱**: 자주 조회되는 컬럼
4. **Connection Pooling**: SQLAlchemy pool 설정
5. **이미지 최적화**: Next.js Image 컴포넌트

## 보안 체크리스트

- [ ] 환경 변수 암호화
- [ ] HTTPS 적용
- [ ] CORS 설정
- [ ] Rate Limiting
- [ ] SQL Injection 방어
- [ ] XSS 방어
- [ ] 정기적인 패키지 업데이트
- [ ] 방화벽 설정
- [ ] 백업 자동화

## 문제 해결

### 데이터베이스 연결 실패

```bash
# PostgreSQL 상태 확인
sudo systemctl status postgresql

# 연결 테스트
psql -h localhost -U slang_user -d slang_db
```

### Celery 작업 실행 안 됨

```bash
# Redis 확인
redis-cli ping

# Celery 로그 확인
celery -A app.tasks.celery_app inspect active
```

### 메모리 부족

```bash
# 메모리 사용량 확인
free -h

# 프로세스별 메모리 확인
ps aux --sort=-%mem | head
```


