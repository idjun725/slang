from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.slang import Slang
from app.schemas.slang import SlangResponse, SlangCreate

router = APIRouter()


@router.get("/", response_model=List[SlangResponse])
async def get_slangs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """신조어 목록 조회"""
    query = db.query(Slang)
    
    if category:
        query = query.filter(Slang.category == category)
    
    slangs = query.offset(skip).limit(limit).all()
    return slangs


@router.get("/{slang_id}", response_model=SlangResponse)
async def get_slang(
    slang_id: int,
    db: Session = Depends(get_db),
):
    """특정 신조어 조회"""
    slang = db.query(Slang).filter(Slang.id == slang_id).first()
    
    if not slang:
        raise HTTPException(status_code=404, detail="신조어를 찾을 수 없습니다")
    
    return slang


@router.get("/search/{word}", response_model=List[SlangResponse])
async def search_slang(
    word: str,
    db: Session = Depends(get_db),
):
    """신조어 검색"""
    slangs = db.query(Slang).filter(
        Slang.word.ilike(f"%{word}%")
    ).all()
    
    return slangs


