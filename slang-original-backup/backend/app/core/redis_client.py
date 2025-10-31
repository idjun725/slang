import redis
from app.core.config import settings

# Redis 클라이언트
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    encoding="utf-8",
)


def get_redis():
    """Redis 클라이언트 반환"""
    return redis_client


