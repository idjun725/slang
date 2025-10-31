from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func
from app.core.database import Base


class Slang(Base):
    """신조어 모델"""
    
    __tablename__ = "slangs"
    
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String(100), unique=True, index=True, nullable=False)
    meaning = Column(Text, nullable=True)
    usage_examples = Column(JSON, default=list)  # 사용 예시 목록
    frequency = Column(Integer, default=0)  # 사용 빈도
    rank = Column(Integer, default=0)  # 현재 순위
    rank_change = Column(Integer, default=0)  # 순위 변화
    category = Column(String(50), index=True)  # 카테고리
    source = Column(String(100))  # 출처
    trend_data = Column(JSON, default=list)  # 트렌드 데이터
    
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Slang {self.word}>"


