from typing import List
from sqlalchemy.orm import Session
from datetime import datetime

from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.slang import Slang
from app.services.crawler_service import DCInsideCrawler


@celery_app.task(name="app.tasks.crawler_tasks.crawl_and_update_slangs")
def crawl_and_update_slangs():
    """디시인사이드 크롤링 및 신조어 업데이트"""
    
    print(f"[{datetime.now()}] 크롤링 시작...")
    
    db = SessionLocal()
    
    try:
        # 크롤링 실행
        crawler = DCInsideCrawler()
        
        # 동기적으로 크롤링 (Celery worker에서)
        import asyncio
        titles = asyncio.run(crawler.crawl_all_galleries())
        
        print(f"총 {len(titles)}개 제목 수집")
        
        # 신조어 추출
        slang_freq = crawler.extract_slangs(titles)
        
        print(f"총 {len(slang_freq)}개 신조어 후보 추출")
        
        # 데이터베이스 업데이트
        for word, frequency in slang_freq.items():
            existing_slang = db.query(Slang).filter(Slang.word == word).first()
            
            if existing_slang:
                # 기존 신조어 업데이트
                old_freq = existing_slang.frequency
                existing_slang.frequency += frequency
                existing_slang.last_updated = datetime.utcnow()
                
                # 트렌드 데이터 추가
                trend_data = existing_slang.trend_data or []
                trend_data.append({
                    "date": datetime.utcnow().isoformat(),
                    "frequency": frequency
                })
                existing_slang.trend_data = trend_data
                
            else:
                # 새로운 신조어 추가
                new_slang = Slang(
                    word=word,
                    frequency=frequency,
                    source="dcinside",
                    first_seen=datetime.utcnow(),
                    last_updated=datetime.utcnow(),
                    trend_data=[{
                        "date": datetime.utcnow().isoformat(),
                        "frequency": frequency
                    }]
                )
                db.add(new_slang)
        
        db.commit()
        print(f"[{datetime.now()}] 크롤링 완료")
        
    except Exception as e:
        print(f"크롤링 오류: {str(e)}")
        db.rollback()
        raise
    
    finally:
        db.close()


@celery_app.task(name="app.tasks.crawler_tasks.update_rankings")
def update_rankings():
    """신조어 랭킹 업데이트"""
    
    print(f"[{datetime.now()}] 랭킹 업데이트 시작...")
    
    db = SessionLocal()
    
    try:
        # 빈도수 기준으로 정렬
        slangs = db.query(Slang).order_by(Slang.frequency.desc()).all()
        
        # 랭킹 업데이트
        for idx, slang in enumerate(slangs, 1):
            old_rank = slang.rank
            new_rank = idx
            
            slang.rank_change = old_rank - new_rank if old_rank > 0 else 0
            slang.rank = new_rank
        
        db.commit()
        print(f"[{datetime.now()}] 랭킹 업데이트 완료")
        
    except Exception as e:
        print(f"랭킹 업데이트 오류: {str(e)}")
        db.rollback()
        raise
    
    finally:
        db.close()


