from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """사용자 기본 스키마"""
    email: EmailStr


class UserCreate(UserBase):
    """사용자 생성 스키마"""
    is_subscribed: Optional[bool] = True


class UserResponse(UserBase):
    """사용자 응답 스키마"""
    id: int
    is_subscribed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


