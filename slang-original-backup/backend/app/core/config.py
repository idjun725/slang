from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 프로젝트 정보
    PROJECT_NAME: str = "슬랭 브릿지"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # 서버 설정
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    # 데이터베이스
    DATABASE_URL: str
    REDIS_URL: str

    # JWT 인증
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # 이메일 (SendGrid)
    SENDGRID_API_KEY: str
    EMAIL_FROM: str
    EMAIL_FROM_NAME: str

    # 크롤러 설정
    CRAWLER_INTERVAL_HOURS: int = 1
    CRAWLER_USER_AGENT: str = "SlangBridge-Bot/1.0"
    CRAWLER_MAX_PAGES: int = 100

    # OpenAI (선택사항)
    OPENAI_API_KEY: Optional[str] = None

    # 환경
    PYTHON_ENV: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


