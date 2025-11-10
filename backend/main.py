from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional
import os
import hashlib
import secrets
import json
import re
from dotenv import load_dotenv

from database import Database
from email_service import EmailService
from crawler import Crawler
from scheduler import start_scheduler_thread
from youtube_service import YouTubeService

# 환경변수 로드 (backend 디렉토리의 .env 파일 명시적으로 로드)
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    # 루트 디렉토리에서도 시도
    root_env = os.path.join(os.path.dirname(current_dir), '.env')
    if os.path.exists(root_env):
        load_dotenv(root_env)
    else:
        load_dotenv()  # 기본 경로에서도 시도

app = FastAPI(title="Slang Bridge API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://newwords-sinabro.netlify.app",  # Netlify 배포 도메인
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "*"  # 개발용 (프로덕션에서는 제거 권장)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 초기화
db = Database()
# 전역 크롤러 (수동 의미 사전 접근용)
global_crawler_for_meanings = Crawler()

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

# 수동 의미 업서트용 모델
class BulkMeaningsRequest(BaseModel):
    meanings: Dict[str, str]

class WordRulesRequest(BaseModel):
    allow: Optional[List[str]] = None
    block: Optional[List[str]] = None

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
async def get_ranking(limit: int = 100, period: Optional[str] = None):
    """신조어 랭킹 조회
    
    Args:
        limit: 반환할 최대 개수 (기본값: 100)
        period: 시간 필터 ('today', 'week', 'month', None=전체)
    """
    try:
        if period and period not in ['today', 'week', 'month']:
            raise HTTPException(status_code=400, detail="period는 'today', 'week', 'month' 중 하나여야 합니다.")
        ranking = db.get_ranking(limit, period)
        # 단어 규칙 적용 (차단/허용) - 파일에서 최신 규칙 로드
        try:
            import json
            data_dir = os.path.join(current_dir, 'data')
            rules_path = os.path.join(data_dir, 'word_rules.json')
            rules = {"allow": [], "block": []}
            if os.path.exists(rules_path):
                with open(rules_path, 'r', encoding='utf-8-sig') as f:
                    content = f.read().strip()
                    if content:
                        rules = json.loads(content)
                        if not isinstance(rules, dict):
                            rules = {"allow": [], "block": []}
            # 메모리 캐시도 갱신
            global_crawler_for_meanings.word_rules = rules
        except Exception as e:
            print(f"[랭킹] 단어 규칙 로드 실패: {e}")
            rules = global_crawler_for_meanings.word_rules
        
        if rules and (rules.get('allow') or rules.get('block')):
            allow = set(rules.get('allow') or [])
            block = set(rules.get('block') or [])
            original_count = len(ranking)
            
            # allow 리스트가 있지만 비어있지 않은 경우
            allow_not_empty = len(allow) > 0
            
            def _allowed(item):
                w = item.get('word')
                if not w:
                    return False
                # block 리스트에 있으면 무조건 제외
                if w in block:
                    return False
                # allow 리스트가 비어있지 않으면 allow 리스트에 있는 것만 허용
                if allow_not_empty and w not in allow:
                    return False
                return True
            
            ranking = list(filter(_allowed, ranking))
            filtered_count = len(ranking)
            
            # 디버그 정보 출력
            if filtered_count == 0 and original_count > 0:
                print(f"[랭킹 필터링] 원본 {original_count}개 → 필터링 후 {filtered_count}개")
                print(f"[랭킹 필터링] allow={len(allow)}개, block={len(block)}개")
                if allow_not_empty:
                    print(f"[랭킹 필터링] allow 리스트 예시: {list(allow)[:5]}")
                    print(f"[랭킹 필터링] 원본 단어 예시: {[r.get('word') for r in db.get_ranking(5) if r.get('word')]}")
                    print(f"[랭킹 필터링] ⚠️ allow 리스트 단어들이 DB에 없습니다. 크롤러를 실행하세요.")
        return {"success": True, "data": ranking, "period": period or "all"}
    except HTTPException:
        raise
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
                slang_data.get('examples', []),
                usage_count=slang_data.get('count', 1),
                method=slang_data.get('method', 'enhanced')
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

@app.post("/meanings/bulk")
async def upsert_bulk_meanings(payload: BulkMeaningsRequest):
    """수동 의미와 예문을 대량 업서트. 기존 값에 병합 저장.
    본문 형식: 
    - 구 형식: { "meanings": { "단어": "뜻", ... } }
    - 새 형식: { "meanings": { "단어": {"meaning": "뜻", "examples": [...]}, ... } }
    """
    try:
        data_dir = os.path.join(current_dir, 'data')
        os.makedirs(data_dir, exist_ok=True)
        manual_path = os.path.join(data_dir, 'manual_meanings.json')
        existing = {}
        if os.path.exists(manual_path):
            with open(manual_path, 'r', encoding='utf-8-sig') as f:
                try:
                    content = f.read().strip()
                    if content:
                        existing = json.loads(content) or {}
                except Exception:
                    existing = {}
        # 병합 (구 형식과 새 형식 모두 지원)
        for k, v in (payload.meanings or {}).items():
            if v:
                if isinstance(v, dict):
                    # 새 형식: {"meaning": "...", "examples": [...]}
                    existing[str(k)] = v
                elif isinstance(v, str):
                    # 구 형식: 문자열만 있으면 새 형식으로 변환
                    if str(k) in existing and isinstance(existing[str(k)], dict):
                        # 기존에 새 형식이 있으면 의미만 업데이트
                        existing[str(k)]['meaning'] = v
                    else:
                        # 새로 추가하면 기본 구조로 변환
                        existing[str(k)] = {"meaning": v, "examples": []}
        # 저장
        with open(manual_path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        # 전역 크롤러 캐시 갱신
        global_crawler_for_meanings.manual_meanings = existing
        return {"updated": len(payload.meanings or {}), "total": len(existing)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/words/rules")
async def get_word_rules():
    return global_crawler_for_meanings.word_rules

@app.post("/words/rules")
async def upsert_word_rules(payload: WordRulesRequest):
    try:
        data_dir = os.path.join(current_dir, 'data')
        os.makedirs(data_dir, exist_ok=True)
        rules_path = os.path.join(data_dir, 'word_rules.json')
        # 기존 로드
        rules = {"allow": [], "block": []}
        if os.path.exists(rules_path):
            with open(rules_path, 'r', encoding='utf-8-sig') as f:
                content = f.read().strip()
                if content:
                    rules = json.loads(content)
                    if not isinstance(rules, dict):
                        rules = {"allow": [], "block": []}
        # 병합/치환
        if payload.allow is not None:
            rules['allow'] = [str(w) for w in payload.allow if w]
        if payload.block is not None:
            rules['block'] = [str(w) for w in payload.block if w]
        # 저장 (BOM 없이)
        with open(rules_path, 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)
        # 메모리 갱신
        global_crawler_for_meanings.word_rules = rules
        return rules
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ranking/videos")
async def get_word_videos(word: str, limit: int = 5):
    """특정 신조어가 사용된 숏폼 영상 조회
    Query parameter로 word를 받습니다 (한글 인코딩 문제 해결)
    """
    try:
        # 1. 캐시된 영상 확인
        cached_videos = db.get_videos_for_word(word, limit=limit)
        
        if cached_videos and len(cached_videos) >= limit:
            return {
                "success": True,
                "word": word,
                "videos": cached_videos,
                "cached": True
            }
        
        # 2. YouTube API로 검색 및 분석
        youtube_service = YouTubeService()
        
        if not youtube_service.youtube:
            # YouTube API가 설정되지 않은 경우
            if cached_videos:
                return {
                    "success": True,
                    "word": word,
                    "videos": cached_videos,
                    "cached": True,
                    "message": "YouTube API 키가 설정되지 않았습니다. 캐시된 영상만 표시합니다."
                }
            return {
                "success": False,
                "word": word,
                "videos": [],
                "message": "YouTube API 키를 설정해야 영상을 검색할 수 있습니다. .env 파일에 YOUTUBE_API_KEY를 추가해주세요."
            }
        
        print(f"[영상 조회] '{word}' 검색 시작 (캐시: {len(cached_videos)}개)")
        videos = youtube_service.find_videos_with_slang(word, max_results=limit)
        print(f"[영상 조회] '{word}' 검색 완료: {len(videos)}개 영상 발견")
        
        if not videos:
            # 캐시된 영상이 있으면 반환 (부족하더라도)
            if cached_videos:
                print(f"[영상 조회] '{word}' - 캐시된 영상 반환 ({len(cached_videos)}개)")
                return {
                    "success": True,
                    "word": word,
                    "videos": cached_videos,
                    "cached": True,
                    "message": "새로운 영상을 찾지 못했습니다. 캐시된 영상만 표시합니다."
                }
            
            # YouTube API가 설정되어 있는데 결과가 없으면
            print(f"[영상 조회] '{word}' - 검색 결과 없음 (API 설정: {youtube_service.youtube is not None})")
            return {
                "success": False,
                "word": word,
                "videos": [],
                "message": f"'{word}' 키워드로 YouTube를 검색했지만 결과가 없습니다. 다른 키워드로 시도해보세요."
            }
        
        # 3. 영상 정보를 DB에 저장
        for video in videos:
            db.add_slang_video(
                slang_word=word,
                video_id=video['video_id'],
                video_title=video.get('title'),
                video_thumbnail=video.get('thumbnail'),
                video_duration=video.get('duration', 0),
                view_count=video.get('view_count', 0),
                like_count=video.get('like_count', 0),
                caption_match_times=video.get('match_times', [])
            )
        
        # 4. 응답 형식 맞추기
        formatted_videos = []
        for video in videos:
            formatted_videos.append({
                'video_id': video['video_id'],
                'title': video.get('title', ''),
                'thumbnail': video.get('thumbnail', ''),
                'duration': video.get('duration', 0),
                'view_count': video.get('view_count', 0),
                'like_count': video.get('like_count', 0),
                'match_times': video.get('match_times', [])
            })
        
        return {
            "success": True,
            "word": word,
            "videos": formatted_videos,
            "cached": False
        }
    
    except Exception as e:
        print(f"[ERROR] 영상 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ranking/enhanced")
async def get_ranking_with_videos(limit: int = 20, include_videos: bool = True):
    """랭킹 + 각 신조어별 영상 정보 포함"""
    try:
        # 기본 랭킹 조회
        ranking = db.get_ranking(limit)
        
        if not include_videos:
            return {"success": True, "data": ranking}
        
        # 상위 5개만 영상 정보 포함 (성능 고려)
        top_words = ranking[:5]
        
        enhanced_ranking = []
        youtube_service = YouTubeService()
        
        for item in ranking:
            enhanced_item = item.copy()
            
            # 상위 5개만 영상 정보 추가
            if item in top_words:
                # 캐시된 영상 확인
                videos = db.get_videos_for_word(item['word'], limit=3)
                
                # 캐시가 없거나 부족하면 API 호출 (비동기로 처리하거나 간단히 스킵)
                if not videos:
                    # 비동기로 처리하지 않고, 간단히 빈 리스트로 설정
                    videos = []
                
                enhanced_item['videos'] = videos
            else:
                enhanced_item['videos'] = []
            
            enhanced_ranking.append(enhanced_item)
        
        return {
            "success": True,
            "data": enhanced_ranking,
            "has_videos": include_videos
        }
    
    except Exception as e:
        print(f"[ERROR] 향상된 랭킹 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/slangs/search")
async def search_slang(word: str):
    """신조어 검색 (의미 + 예문 + 영상)"""
    try:
        from crawler import Crawler
        from youtube_service import YouTubeService
        
        word = word.strip()
        if not word:
            raise HTTPException(status_code=400, detail="검색할 단어를 입력해주세요.")
        
        print(f"[검색] '{word}' 검색 시작")
        
        # 1. 데이터베이스에서 기존 정보 확인
        db_result = db.get_slang_by_word(word)
        
        # 2. 의미 생성 (수동 의미 우선, GPT는 필요시)
        from meaning_extractor import MeaningExtractor
        from crawler import Crawler
        
        meaning = db_result.get('meaning', '') if db_result else ''
        
        if not meaning or meaning == '' or '분석 중' in meaning:
            print(f"[검색] '{word}' 의미 추출 중...")
            
            # 수동 의미 우선 적용
            manual_data = global_crawler_for_meanings.manual_meanings.get(word)
            if manual_data:
                if isinstance(manual_data, dict):
                    meaning = manual_data.get('meaning', '')
                else:
                    # 구 형식 호환
                    meaning = str(manual_data)
            
            # GPT 클라이언트 가져오기 (수동 의미 없을 때만)
            crawler = Crawler() if not manual_data else global_crawler_for_meanings
            openai_client = crawler.openai_client if crawler else None
            
            # 의미 추출기 초기화 (GPT 클라이언트 포함)
            extractor = MeaningExtractor(openai_client=openai_client)
            
            # 컨텍스트와 예문 준비
            contexts = []
            examples = []
            
            if db_result:
                # 기존 예문을 컨텍스트로 사용
                existing_examples = db_result.get('examples', [])
                if existing_examples:
                    if isinstance(existing_examples, str):
                        examples = json.loads(existing_examples)
                    else:
                        examples = existing_examples
                    contexts = examples.copy()
            
            # 영상 자막에서 예문 수집 (아직 수집되지 않은 경우)
            if len(examples) < 3:
                from youtube_service import YouTubeService
                youtube_service = YouTubeService()
                if youtube_service.youtube:
                    try:
                        videos = youtube_service.find_videos_with_slang(word, max_results=3)
                        for video in videos[:2]:
                            try:
                                caption_text = youtube_service.get_video_captions(video['video_id'])
                                if caption_text:
                                    captions = youtube_service.parse_srt(caption_text)
                                    for caption in captions[:10]:  # 상위 10개만
                                        text = caption['text'].strip()
                                        if word in text and len(text) > 10:
                                            contexts.append(text[:200])
                                            if len(contexts) >= 5:
                                                break
                            except:
                                continue
                    except Exception as e:
                        print(f"[검색] 예문 수집 실패: {e}")
            
            # 여러 방법으로 의미 추출 시도
            meaning = extractor.extract_meaning(word, contexts=contexts, examples=examples)
            
            print(f"[검색] '{word}' 의미 추출 완료: {meaning}")
        
        # 3. 예문 수집 (수동 예문 우선 → DB → 영상 자막)
        examples = []
        
        # 수동 예문 우선 적용
        manual_data = global_crawler_for_meanings.manual_meanings.get(word)
        if manual_data and isinstance(manual_data, dict):
            manual_examples = manual_data.get('examples', [])
            if manual_examples and isinstance(manual_examples, list):
                examples.extend(manual_examples)
                print(f"[검색] '{word}' 수동 예문 {len(manual_examples)}개 사용")
        
        # 기존 예문이 있으면 추가 (수동 예문이 부족할 때만)
        if len(examples) < 3 and db_result and db_result.get('examples'):
            existing_examples = json.loads(db_result['examples']) if isinstance(db_result['examples'], str) else db_result['examples']
            examples.extend(existing_examples)
        
        # 예문이 부족하면 영상 자막에서 추출
        if len(examples) < 5:
            print(f"[검색] '{word}' 예문 수집 중... (현재 {len(examples)}개)")
            youtube_service = YouTubeService()
            
            if youtube_service.youtube:
                # 영상 검색
                videos = youtube_service.find_videos_with_slang(word, max_results=10)
                
                # 영상 자막에서 예문 추출
                for video in videos:
                    if len(examples) >= 10:  # 충분히 수집했으면 중단
                        break
                    
                    try:
                        caption_text = youtube_service.get_video_captions(video['video_id'])
                        if caption_text:
                            captions = youtube_service.parse_srt(caption_text)
                            
                            # 단어가 포함된 자막 문장 추출
                            for caption in captions:
                                if len(examples) >= 10:
                                    break
                                
                                text = caption['text'].strip()
                                if word in text:
                                    # 문장 정리 (중복 제거, 길이 필터링)
                                    sentence = text.strip()
                                    # 특수 문자나 URL 제거
                                    sentence = re.sub(r'http[s]?://\S+', '', sentence)
                                    sentence = re.sub(r'\[.*?\]', '', sentence)
                                    sentence = sentence.strip()
                                    
                                    # 유효한 문장인지 확인
                                    if (len(sentence) > 10 and len(sentence) < 200 and 
                                        sentence not in examples and 
                                        not sentence.startswith('http')):
                                        examples.append(sentence)
                            
                            if len(examples) >= 10:
                                break
                    except Exception as e:
                        print(f"[검색] 예문 추출 실패 ({video.get('video_id', 'unknown')}): {e}")
                        continue
        
        # 예문이 없으면 기본 메시지
        if not examples:
            examples = [f"{word}를 사용한 예문을 찾는 중입니다..."]
        
        # 4. 영상 정보 가져오기
        videos = []
        youtube_service = YouTubeService()
        if youtube_service.youtube:
            # 캐시된 영상 먼저 확인
            cached_videos = db.get_videos_for_word(word, limit=5)
            if cached_videos and len(cached_videos) >= 3:
                videos = cached_videos[:5]
            else:
                # 새로 검색
                videos_data = youtube_service.find_videos_with_slang(word, max_results=5)
                
                # 영상 정보 저장
                for video in videos_data:
                    db.add_slang_video(
                        slang_word=word,
                        video_id=video['video_id'],
                        video_title=video.get('title'),
                        video_thumbnail=video.get('thumbnail'),
                        video_duration=video.get('duration', 0),
                        view_count=video.get('view_count', 0),
                        like_count=video.get('like_count', 0),
                        caption_match_times=video.get('match_times', [])
                    )
                
                videos = [{
                    'video_id': v['video_id'],
                    'title': v.get('title', ''),
                    'thumbnail': v.get('thumbnail', ''),
                    'duration': v.get('duration', 0),
                    'view_count': v.get('view_count', 0),
                    'like_count': v.get('like_count', 0)
                } for v in videos_data]
        
        # 5. 데이터베이스에 업데이트 (의미나 예문이 새로 생성된 경우)
        if not db_result or (meaning and meaning != db_result.get('meaning')):
            db.add_slang(
                word=word,
                meaning=meaning,
                examples=examples[:5],
                usage_count=db_result.get('usage_count', 1) if db_result else 1,
                method=db_result.get('method', 'search') if db_result else 'search'
            )
        
        print(f"[검색] '{word}' 검색 완료 - 의미: {meaning}, 예문: {len(examples)}개, 영상: {len(videos)}개")
        
        return {
            "success": True,
            "data": {
                "word": word,
                "meaning": meaning,
                "examples": examples[:5],
                "videos": videos[:5]
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] 신조어 검색 실패: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # 스케줄러 시작
    start_scheduler_thread()
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
