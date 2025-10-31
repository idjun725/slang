from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """사용자 모델"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    is_subscribed = Column(Boolean, default=True)
    subscription_preferences = Column(JSON, default=dict)  # 구독 설정
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<User {self.email}>"


class Newsletter(Base):
    """뉴스레터 발송 기록"""
    
    __tablename__ = "newsletters"
    
    id = Column(Integer, primary_key=True, index=True)
    sent_date = Column(DateTime(timezone=True), nullable=False)
    top_slangs = Column(JSON, default=list)  # 상위 5개 신조어 ID 목록
    recipient_count = Column(Integer, default=0)
    open_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Newsletter {self.sent_date}>"


