from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SlangBase(BaseModel):
    """신조어 기본 스키마"""
    word: str = Field(..., min_length=1, max_length=100)
    meaning: Optional[str] = None
    category: Optional[str] = None


class SlangCreate(SlangBase):
    """신조어 생성 스키마"""
    usage_examples: List[str] = []
    source: Optional[str] = None


class SlangResponse(SlangBase):
    """신조어 응답 스키마"""
    id: int
    usage_examples: List[str] = []
    frequency: int
    rank: int
    rank_change: int
    source: Optional[str] = None
    first_seen: datetime
    last_updated: Optional[datetime] = None
    
    class Config:
        from_attributes = True


