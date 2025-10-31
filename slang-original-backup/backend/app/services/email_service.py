from typing import List
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User


async def subscribe_newsletter(email: str, db: Session) -> bool:
    """뉴스레터 구독 처리
    
    Args:
        email: 구독할 이메일 주소
        db: 데이터베이스 세션
        
    Returns:
        구독 성공 여부
    """
    
    # 사용자 찾기 또는 생성
    user = db.query(User).filter(User.email == email).first()
    
    if user:
        user.is_subscribed = True
    else:
        user = User(email=email, is_subscribed=True)
        db.add(user)
    
    db.commit()
    
    # 환영 이메일 발송
    await send_welcome_email(email)
    
    return True


async def unsubscribe_newsletter(email: str, db: Session) -> bool:
    """뉴스레터 구독 취소
    
    Args:
        email: 구독 취소할 이메일 주소
        db: 데이터베이스 세션
        
    Returns:
        구독 취소 성공 여부
    """
    
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        return False
    
    user.is_subscribed = False
    db.commit()
    
    return True


async def send_welcome_email(email: str):
    """환영 이메일 발송
    
    Args:
        email: 수신자 이메일
    """
    
    message = Mail(
        from_email=Email(settings.EMAIL_FROM, settings.EMAIL_FROM_NAME),
        to_emails=To(email),
        subject="슬랭 브릿지 뉴스레터 구독을 환영합니다!",
        html_content=f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #0ea5e9;">슬랭 브릿지에 오신 것을 환영합니다! 🎉</h1>
                    <p>안녕하세요!</p>
                    <p>슬랭 브릿지 뉴스레터 구독을 환영합니다.</p>
                    <p>매주 월요일 아침, 가장 인기 있는 신조어 TOP 5를 이메일로 받아보실 수 있습니다.</p>
                    
                    <h2 style="color: #0ea5e9;">뉴스레터에서 무엇을 받아볼 수 있나요?</h2>
                    <ul>
                        <li>지난 주 가장 많이 사용된 신조어 TOP 5</li>
                        <li>각 신조어의 의미와 사용 예시</li>
                        <li>신조어 트렌드 분석</li>
                    </ul>
                    
                    <p>감사합니다!</p>
                    <p><strong>슬랭 브릿지 팀</strong></p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    <p style="font-size: 12px; color: #666;">
                        더 이상 이메일을 받고 싶지 않으시다면 
                        <a href="{settings.NEXT_PUBLIC_SITE_URL}/unsubscribe?email={email}">여기</a>를 클릭하세요.
                    </p>
                </div>
            </body>
        </html>
        """
    )
    
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code == 202
    except Exception as e:
        print(f"이메일 발송 실패: {str(e)}")
        return False


async def send_weekly_newsletter(top_slangs: List[dict], recipients: List[str]):
    """주간 뉴스레터 발송
    
    Args:
        top_slangs: 상위 5개 신조어 정보
        recipients: 수신자 이메일 목록
    """
    
    # HTML 콘텐츠 생성
    slang_items = ""
    for i, slang in enumerate(top_slangs, 1):
        slang_items += f"""
        <div style="background: #f0f9ff; padding: 20px; margin: 15px 0; border-radius: 8px;">
            <h3 style="color: #0ea5e9; margin: 0 0 10px 0;">
                {i}. {slang['word']}
                {_get_rank_badge(slang.get('rank_change', 0))}
            </h3>
            <p style="margin: 10px 0;"><strong>의미:</strong> {slang['meaning']}</p>
            <p style="margin: 10px 0;"><strong>사용 예시:</strong> {slang['usage_examples'][0] if slang.get('usage_examples') else '-'}</p>
            <p style="margin: 10px 0; color: #666;"><strong>사용 횟수:</strong> {slang['frequency']}회</p>
        </div>
        """
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #0ea5e9; text-align: center;">📊 이번 주 신조어 TOP 5</h1>
                <p style="text-align: center; color: #666;">지난 주 가장 많이 사용된 신조어를 소개합니다</p>
                
                {slang_items}
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{settings.NEXT_PUBLIC_SITE_URL}/ranking" 
                       style="background: #0ea5e9; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block;">
                        전체 랭킹 보러가기
                    </a>
                </div>
                
                <p style="text-align: center;">감사합니다!<br><strong>슬랭 브릿지 팀</strong></p>
            </div>
        </body>
    </html>
    """
    
    # 이메일 발송
    for recipient in recipients:
        message = Mail(
            from_email=Email(settings.EMAIL_FROM, settings.EMAIL_FROM_NAME),
            to_emails=To(recipient),
            subject=f"[슬랭 브릿지] 이번 주 신조어 TOP 5 📊",
            html_content=html_content
        )
        
        try:
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            sg.send(message)
        except Exception as e:
            print(f"이메일 발송 실패 ({recipient}): {str(e)}")


def _get_rank_badge(rank_change: int) -> str:
    """순위 변화 뱃지 반환"""
    if rank_change > 0:
        return f'<span style="color: #ef4444;">▲ {rank_change}</span>'
    elif rank_change < 0:
        return f'<span style="color: #3b82f6;">▼ {abs(rank_change)}</span>'
    else:
        return '<span style="color: #10b981;">NEW</span>'


