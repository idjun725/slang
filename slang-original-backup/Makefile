.PHONY: help install dev build up down logs clean test lint format

help:
	@echo "슬랭 브릿지 프로젝트 명령어"
	@echo ""
	@echo "make install     - 의존성 설치"
	@echo "make dev         - 개발 서버 실행"
	@echo "make build       - Docker 이미지 빌드"
	@echo "make up          - Docker Compose 실행"
	@echo "make down        - Docker Compose 중지"
	@echo "make logs        - 로그 확인"
	@echo "make clean       - 정리"
	@echo "make test        - 테스트 실행"
	@echo "make lint        - 린트 검사"
	@echo "make format      - 코드 포맷팅"

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev:
	docker-compose up

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf backend/.pytest_cache
	rm -rf backend/htmlcov
	rm -rf frontend/.next
	rm -rf frontend/node_modules

test:
	cd backend && pytest
	cd frontend && npm test

lint:
	cd backend && flake8 app/
	cd frontend && npm run lint

format:
	cd backend && black app/ && isort app/
	cd frontend && npm run format

migrate:
	cd backend && alembic upgrade head

migrate-create:
	cd backend && alembic revision --autogenerate -m "$(message)"

db-reset:
	docker-compose down -v postgres
	docker-compose up -d postgres
	sleep 5
	$(MAKE) migrate


