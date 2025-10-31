from pydantic import BaseModel, EmailStr


class NewsletterSubscribe(BaseModel):
    """뉴스레터 구독 스키마"""
    email: EmailStr


class NewsletterResponse(BaseModel):
    """뉴스레터 응답 스키마"""
    success: bool
    message: str
    email: str


