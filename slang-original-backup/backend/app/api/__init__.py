from fastapi import APIRouter

from app.api.endpoints import slangs, ranking, newsletter, users

api_router = APIRouter()

# 엔드포인트 등록
api_router.include_router(slangs.router, prefix="/slangs", tags=["slangs"])
api_router.include_router(ranking.router, prefix="/ranking", tags=["ranking"])
api_router.include_router(newsletter.router, prefix="/newsletter", tags=["newsletter"])
api_router.include_router(users.router, prefix="/users", tags=["users"])


