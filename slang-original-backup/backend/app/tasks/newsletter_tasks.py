from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.slang import Slang
from app.models.user import User, Newsletter
from app.services.email_service import send_weekly_newsletter


@celery_app.task(name="app.tasks.newsletter_tasks.send_weekly_newsletter_task")
def send_weekly_newsletter_task():
    """주간 뉴스레터 발송 작업"""
    
    print(f"[{datetime.now()}] 주간 뉴스레터 발송 시작...")
    
    db = SessionLocal()
    
    try:
        # 지난 주 상위 5개 신조어 조회
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        top_slangs = db.query(Slang).filter(
            Slang.last_updated >= week_ago
        ).order_by(Slang.frequency.desc()).limit(5).all()
        
        if not top_slangs:
            print("발송할 신조어가 없습니다.")
            return
        
        # 신조어 데이터 직렬화
        slang_data = []
        for slang in top_slangs:
            slang_data.append({
                "word": slang.word,
                "meaning": slang.meaning or "의미 분석 중...",
                "usage_examples": slang.usage_examples or [],
                "frequency": slang.frequency,
                "rank_change": slang.rank_change,
            })
        
        # 구독자 조회
        subscribers = db.query(User).filter(
            User.is_subscribed == True
        ).all()
        
        if not subscribers:
            print("구독자가 없습니다.")
            return
        
        recipient_emails = [user.email for user in subscribers]
        
        print(f"총 {len(recipient_emails)}명의 구독자에게 발송합니다.")
        
        # 이메일 발송
        import asyncio
        asyncio.run(send_weekly_newsletter(slang_data, recipient_emails))
        
        # 발송 기록 저장
        newsletter = Newsletter(
            sent_date=datetime.utcnow(),
            top_slangs=[slang.id for slang in top_slangs],
            recipient_count=len(recipient_emails),
        )
        db.add(newsletter)
        db.commit()
        
        print(f"[{datetime.now()}] 뉴스레터 발송 완료")
        
    except Exception as e:
        print(f"뉴스레터 발송 오류: {str(e)}")
        db.rollback()
        raise
    
    finally:
        db.close()


@celery_app.task(name="app.tasks.newsletter_tasks.send_test_newsletter")
def send_test_newsletter(email: str):
    """테스트 뉴스레터 발송
    
    Args:
        email: 테스트 수신자 이메일
    """
    
    db = SessionLocal()
    
    try:
        # 현재 상위 5개 신조어
        top_slangs = db.query(Slang).order_by(
            Slang.frequency.desc()
        ).limit(5).all()
        
        slang_data = []
        for slang in top_slangs:
            slang_data.append({
                "word": slang.word,
                "meaning": slang.meaning or "의미 분석 중...",
                "usage_examples": slang.usage_examples or [],
                "frequency": slang.frequency,
                "rank_change": slang.rank_change,
            })
        
        import asyncio
        asyncio.run(send_weekly_newsletter(slang_data, [email]))
        
        print(f"테스트 뉴스레터를 {email}로 발송했습니다.")
        
    finally:
        db.close()


