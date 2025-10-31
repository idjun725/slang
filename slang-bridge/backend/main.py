from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional
import os
import hashlib
import secrets
from dotenv import load_dotenv

from database import Database
from email_service import EmailService
from crawler import Crawler
from scheduler import start_scheduler_thread

# 환경변수 로드
load_dotenv()

app = FastAPI(title="Slang Bridge API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 초기화
db = Database()

# 세션 저장소 (간단한 in-memory)
sessions = {}

# 요청 모델
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str

class SubscribeRequest(BaseModel):
    email: str

class UnsubscribeRequest(BaseModel):
    email: str

# 보안 헬퍼 함수
def hash_password(password: str) -> str:
    """비밀번호 해시"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_session(user_id: int) -> str:
    """세션 생성"""
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = user_id
    return session_id

def get_current_user(session_id: Optional[str] = None) -> Optional[Dict]:
    """현재 로그인한 사용자 조회"""
    if not session_id or session_id not in sessions:
        return None
    user_id = sessions[session_id]
    return db.get_user_by_id(user_id)

def get_user_from_session(session_id: str = None):
    """세션에서 사용자 정보 가져오기 (의존성)"""
    if not session_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    user = get_current_user(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다.")
    return user

@app.get("/")
async def root():
    return {"message": "Slang Bridge API", "version": "1.0.0"}

@app.post("/register")
async def register(request: RegisterRequest):
    """회원가입"""
    try:
        # 이메일 중복 확인
        if db.get_user_by_email(request.email):
            raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")
        
        # 이메일에서 자동으로 사용자 이름 생성 (이메일의 @ 앞부분)
        username = request.email.split('@')[0]
        
        # 사용자 이름이 이미 존재하면 숫자 추가
        original_username = username
        counter = 1
        while db.get_user(username):
            username = f"{original_username}{counter}"
            counter += 1
        
        # 비밀번호 해시
        hashed_password = hash_password(request.password)
        
        # 사용자 생성
        success = db.create_user(username, hashed_password, request.email)
        if success:
            return {"success": True, "message": "회원가입이 완료되었습니다."}
        else:
            raise HTTPException(status_code=400, detail="회원가입 처리 중 오류가 발생했습니다.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
async def login(request: LoginRequest):
    """로그인"""
    try:
        user = db.get_user_by_email(request.email)
        if not user:
            raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다.")
        
        hashed_password = hash_password(request.password)
        if user['password'] != hashed_password:
            raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다.")
        
        # 세션 생성
        session_id = create_session(user['id'])
        
        return {
            "success": True,
            "message": "로그인 성공",
            "session_id": session_id,
            "user": {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "newsletter_subscribed": user['newsletter_subscribed']
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/logout")
async def logout(session_id: Optional[str] = None):
    """로그아웃"""
    if session_id and session_id in sessions:
        del sessions[session_id]
    return {"success": True, "message": "로그아웃되었습니다."}

@app.get("/me")
async def get_current_user_info(session_id: Optional[str] = None):
    """현재 로그인한 사용자 정보 조회"""
    if not session_id:
        return {"success": False, "message": "로그인이 필요합니다."}
    
    user = get_current_user(session_id)
    if not user:
        return {"success": False, "message": "세션이 만료되었습니다."}
    
    return {
        "success": True,
        "user": {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "newsletter_subscribed": user['newsletter_subscribed']
        }
    }

@app.get("/ranking")
async def get_ranking(limit: int = 20):
    """신조어 랭킹 조회"""
    try:
        ranking = db.get_ranking(limit)
        return {"success": True, "data": ranking}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/subscription/toggle")
async def toggle_subscription(session_id: Optional[str] = None):
    """뉴스레터 구독 토글"""
    if not session_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    user = get_current_user(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다.")
    
    try:
        success = db.toggle_newsletter_subscription(user['id'])
        if success:
            new_status = db.get_newsletter_subscription_status(user['id'])
            return {
                "success": True,
                "message": "구독 상태가 변경되었습니다.",
                "subscribed": new_status
            }
        else:
            raise HTTPException(status_code=400, detail="구독 상태 변경 중 오류가 발생했습니다.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/subscription/status")
async def get_subscription_status(session_id: Optional[str] = None):
    """뉴스레터 구독 상태 조회"""
    if not session_id:
        return {"success": False, "subscribed": False}
    
    user = get_current_user(session_id)
    if not user:
        return {"success": False, "subscribed": False}
    
    status = db.get_newsletter_subscription_status(user['id'])
    return {"success": True, "subscribed": status}

@app.post("/crawl")
async def trigger_crawl():
    """크롤링 실행"""
    try:
        crawler = Crawler()
        result = crawler.crawl_and_analyze()
        
        # 데이터베이스에 저장
        added_count = 0
        for slang_data in result:
            if db.add_slang(
                slang_data['word'], 
                slang_data['meaning'], 
                slang_data['examples']
            ):
                added_count += 1
        
        return {"message": f"크롤링 완료! {added_count}개 신조어 발견", "count": added_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """통계 정보 조회"""
    try:
        stats = db.get_stats()
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # 스케줄러 시작
    start_scheduler_thread()
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
