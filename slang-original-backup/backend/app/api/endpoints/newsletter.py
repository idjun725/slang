from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.newsletter import NewsletterSubscribe, NewsletterResponse
from app.services.email_service import subscribe_newsletter, unsubscribe_newsletter

router = APIRouter()


@router.post("/subscribe", response_model=NewsletterResponse)
async def subscribe(
    data: NewsletterSubscribe,
    db: Session = Depends(get_db),
):
    """뉴스레터 구독
    
    Args:
        data: 구독 정보 (이메일)
    """
    
    # 이미 구독 중인지 확인
    existing_user = db.query(User).filter(User.email == data.email).first()
    
    if existing_user and existing_user.is_subscribed:
        raise HTTPException(
            status_code=400,
            detail="이미 구독 중인 이메일입니다"
        )
    
    # 구독 처리
    result = await subscribe_newsletter(data.email, db)
    
    return {
        "success": True,
        "message": "뉴스레터 구독이 완료되었습니다",
        "email": data.email
    }


@router.post("/unsubscribe")
async def unsubscribe(
    email: str,
    db: Session = Depends(get_db),
):
    """뉴스레터 구독 취소"""
    
    result = await unsubscribe_newsletter(email, db)
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail="구독 정보를 찾을 수 없습니다"
        )
    
    return {
        "success": True,
        "message": "구독이 취소되었습니다"
    }


@router.get("/history")
async def get_newsletter_history(
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """뉴스레터 발송 히스토리 조회"""
    
    # TODO: Newsletter 모델에서 조회
    return {
        "newsletters": [],
        "total": 0
    }


