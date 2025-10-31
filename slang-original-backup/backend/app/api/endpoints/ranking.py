from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.slang import Slang
from app.schemas.slang import SlangResponse

router = APIRouter()


@router.get("/", response_model=List[SlangResponse])
async def get_ranking(
    period: str = Query("today", regex="^(today|week|month)$"),
    limit: int = Query(10, ge=1, le=100),
    category: str = Query(None),
    db: Session = Depends(get_db),
):
    """신조어 랭킹 조회
    
    Args:
        period: 조회 기간 (today, week, month)
        limit: 조회 개수
        category: 카테고리 필터
    """
    
    # 기간 설정
    now = datetime.utcnow()
    if period == "today":
        start_date = now - timedelta(days=1)
    elif period == "week":
        start_date = now - timedelta(days=7)
    else:  # month
        start_date = now - timedelta(days=30)
    
    # 쿼리 구성
    query = db.query(Slang).filter(Slang.last_updated >= start_date)
    
    if category:
        query = query.filter(Slang.category == category)
    
    # 빈도수 기준 정렬
    slangs = query.order_by(desc(Slang.frequency)).limit(limit).all()
    
    return slangs


@router.get("/trending", response_model=List[SlangResponse])
async def get_trending(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """급상승 신조어 조회
    
    최근 24시간 동안 빈도수가 급증한 신조어를 반환합니다.
    """
    
    # rank_change가 큰 순서대로 정렬
    slangs = db.query(Slang).order_by(
        desc(Slang.rank_change)
    ).limit(limit).all()
    
    return slangs


