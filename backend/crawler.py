import requests
from bs4 import BeautifulSoup
import re
from collections import Counter
from typing import List, Dict, Set, Optional
import time
import os
import sys
import math
import json
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# 백그라운드 작업에서도 로그가 즉시 출력되도록 print를 래핑
_original_print = print
def print(*args, **kwargs):
    """즉시 flush되는 print 함수"""
    kwargs.setdefault('flush', True)
    _original_print(*args, **kwargs)
    sys.stdout.flush()

# 환경변수 로드 (backend 디렉토리의 .env 파일 명시적으로 로드)
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
load_dotenv(env_path)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("[WARNING] OpenAI library not installed. GPT filtering will be disabled.")

class Crawler:
    @staticmethod
    def _get_env_int(name: str, default: int) -> int:
        value = os.getenv(name)
        if value is None or value.strip() == '':
            return default
        try:
            return int(value)
        except ValueError:
            print(f"[WARNING] 환경변수 {name} 값을 정수로 변환할 수 없습니다: '{value}'. 기본값 {default} 사용")
            return default

    @staticmethod
    def _get_env_float(name: str, default: float) -> float:
        value = os.getenv(name)
        if value is None or value.strip() == '':
            return default
        try:
            return float(value)
        except ValueError:
            print(f"[WARNING] 환경변수 {name} 값을 실수로 변환할 수 없습니다: '{value}'. 기본값 {default} 사용")
            return default

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # 한국어 조사 목록 (제거 대상) - 긴 조사부터 정렬
        self.korean_particles = sorted([
            '을', '를', '의','이', '가',  # 격조사
            '에', '에게', '께', '한테', '에서', '로', '으로',  # 처소격 조사
            '와', '과',  # 접속 조사
            '은', '는', '도', '만', '조차', '마저', '까지', '부터',  # 보조사
        ], key=len, reverse=True)  # 긴 조사부터 정렬
        
        # 일반적인 단어들 (필터링용) - 확장
        self.common_words = {
            '사람', '시간', '문제', '경우', '생각', '이야기', '이유', '방법', '결과',
            '상황', '기회', '가능', '중요', '필요', '이상', '이하', '이전', '이후',
            '위치', '상태', '조건', '내용', '형태', '성격', '특징', '목적', '의미',
            '생활', '일반', '주변', '관련', '대한', '때문', '이후', '이전', '이상',
            '이하', '이번', '다음', '이전', '이후', '이상', '이하', '이번', '다음',
            '관계', '의견', '확인', '이해', '학습', '교육', '경험', '생각', '관점',
            '기본', '원칙', '규칙', '원인', '결과', '영향', '효과', '이유', '목적',
            '일반', '특별', '특정', '일부', '전체', '부분', '조건', '상황', '환경',
            '사용', '이용', '활용', '적용', '처리', '작업', '실행', '진행', '수행',
            '시작', '종료', '완료', '중단', '계속', '지속', '유지', '보존', '보호',
            '아니', '아닌', '없는', '없이', '없을', '없는', '없이', '없을', '또한',
            '실베추', '공유', '추천', '스크랩', '신고', '투표'
            '일본', '대한민국', '한국', '중국', '미국', '캄보디아'
        }
        
        # 신조어가 아닌 확실한 일반 단어 패턴 (정규표현식)
        self.non_slang_patterns = [
            r'하다$',
            r'되다$',
            r'이다$',
            r'같다$',
            r'있다$',
            r'없다$',
            r'하는$',
            r'되는$',
            r'있는$',
            r'없는$',
            r'하고$',
            r'되고$',
            r'이고$',
            r'같고$',
            r'있고$',
            r'없고$',
            r'하면$',
            r'되면$',
            r'하면서$',
            r'되면서$',
            r'이면서$',
            r'만큼', r'처럼', r'뿐만',  # 조사 성격의 단어
            r'이[가-힣]{1,2}$',  # 이~ 패턴 (이것, 이런 등)
            r'그[가-힣]{1,2}$',  # 그~ 패턴
            r'저[가-힣]{1,2}$',  # 저~ 패턴
            r'어떤$', r'어떠한$', r'어떻게$',  # 의문사
            r'모든$', r'전체$', r'일부$', r'많은$', r'적은$',  # 수량 표현
        ]
        
        # API 설정
        self.naver_client_id = os.getenv('NAVER_CLIENT_ID', '')
        self.naver_client_secret = os.getenv('NAVER_CLIENT_SECRET', '')
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        
        # OpenAI 클라이언트 초기화
        use_gpt_str = os.getenv('GPT_USE_ENABLED', '').strip().lower()
        use_gpt = use_gpt_str == 'true' or use_gpt_str == '1'
        
        print(f"[DEBUG] GPT 설정 확인: GPT_USE_ENABLED='{use_gpt_str}' (변환: {use_gpt})")
        print(f"[DEBUG] OPENAI_API_KEY 존재: {bool(self.openai_api_key)}")
        print(f"[DEBUG] OPENAI_AVAILABLE: {OPENAI_AVAILABLE}")
        
        if OPENAI_AVAILABLE and self.openai_api_key and use_gpt:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            print("[GPT] API 활성화됨")
        else:
            self.openai_client = None
            if not use_gpt:
                print("[GPT] API 비활성화됨 (GPT_USE_ENABLED=true로 설정하면 활성화)")
            elif not self.openai_api_key:
                print("[GPT] API 비활성화됨 (OPENAI_API_KEY가 설정되지 않았습니다)")
            elif not OPENAI_AVAILABLE:
                print("[GPT] API 비활성화됨 (OpenAI 라이브러리가 설치되지 않았습니다)")
        
        # 수동 의미 사전 로드
        self.manual_meanings = {}
        try:
            data_dir = os.path.join(current_dir, 'data')
            os.makedirs(data_dir, exist_ok=True)
            manual_path = os.path.join(data_dir, 'manual_meanings.json')
            if os.path.exists(manual_path):
                # UTF-8 BOM 문제 해결: utf-8-sig 사용
                with open(manual_path, 'r', encoding='utf-8-sig') as f:
                    import json
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        if isinstance(data, dict):
                            # 새 형식: {"단어": {"meaning": "...", "examples": [...]}}
                            # 구 형식 호환: {"단어": "의미"}
                            self.manual_meanings = {}
                            for k, v in data.items():
                                if isinstance(v, dict):
                                    # 새 형식
                                    self.manual_meanings[str(k)] = v
                                elif isinstance(v, str):
                                    # 구 형식 호환: 문자열을 객체로 변환
                                    self.manual_meanings[str(k)] = {"meaning": v, "examples": []}
                            print(f"[의미사전] 수동 의미 {len(self.manual_meanings)}개 로드 (예문 포함)")
            else:
                # 파일이 없으면 빈 파일 생성 (BOM 없이)
                with open(manual_path, 'w', encoding='utf-8') as f:
                    f.write("{}")
        except Exception as e:
            print(f"[의미사전] 수동 의미 로드 실패: {e}")
            # 실패해도 빈 딕셔너리로 계속 진행
            self.manual_meanings = {}

        # 단어 노출 규칙(허용/차단) 로드
        self.word_rules = {"allow": [], "block": []}
        try:
            rules_path = os.path.join(current_dir, 'data', 'word_rules.json')
            if os.path.exists(rules_path):
                import json
                with open(rules_path, 'r', encoding='utf-8-sig') as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        if isinstance(data, dict):
                            allow = data.get('allow') or []
                            block = data.get('block') or []
                            self.word_rules = {
                                'allow': [str(w) for w in allow if w],
                                'block': [str(w) for w in block if w],
                            }
            else:
                # 기본 파일 생성
                os.makedirs(os.path.dirname(rules_path), exist_ok=True)
                with open(rules_path, 'w', encoding='utf-8') as f:
                    f.write('{"allow": [], "block": []}')
            print(f"[단어규칙] allow={len(self.word_rules['allow'])}, block={len(self.word_rules['block'])}")
        except Exception as e:
            print(f"[단어규칙] 로드 실패: {e}")
            self.word_rules = {"allow": [], "block": []}

        # 필터 강도 관련 파라미터 (환경변수로 조정 가능)
        self.filter_min_count = self._get_env_int('SLANG_FILTER_MIN_COUNT', 3)
        self.filter_nlp_threshold = self._get_env_float('SLANG_FILTER_NLP_THRESHOLD', 0.46)
        self.filter_target_count = self._get_env_int('SLANG_FILTER_TARGET_COUNT', 30)

        # 의미 캐시 파일 경로 및 초기화
        self.meaning_cache_file = os.path.join(current_dir, 'meaning_cache.json')
        self.meaning_cache = self._load_meaning_cache()
        
        # 네이버 사전 확인 결과 캐시 (메모리 캐시)
        self.naver_dict_cache = {}
        self.naver_dict_cache_file = os.path.join(current_dir, 'standard_word_cache.json')
        self._naver_cache_dirty = False
        self._load_naver_dict_cache()
        
        # 욕설 판별 캐시
        self.profane_cache_file = os.path.join(current_dir, 'profane_word_cache.json')
        self.profane_cache = self._load_profane_cache()
        self._profane_cache_dirty = False
        
        # NLP 분류기 초기화 (옵션)
        self.nlp_classifier = None
        use_nlp_str = os.getenv('USE_NLP_FILTER', '').strip().lower()
        use_nlp = use_nlp_str == 'true' or use_nlp_str == '1'
        if use_nlp:
            try:
                from slang_classifier import SlangClassifier
                nlp_model_path = os.getenv('NLP_MODEL_PATH', None)
                self.nlp_classifier = SlangClassifier(model_path=nlp_model_path)
                print("[NLP 분류기] 활성화됨")
            except Exception as e:
                print(f"[NLP 분류기] 로드 실패: {e}")
                print("[NLP 분류기] NLP 필터링이 비활성화됩니다. USE_NLP_FILTER=true로 설정하고 모델 경로를 확인하세요.")
                self.nlp_classifier = None
        else:
            print("[NLP 분류기] 비활성화됨 (USE_NLP_FILTER=true로 설정하면 활성화)")

    def _is_word_allowed(self, word: str) -> bool:
        """허용/차단 규칙 적용"""
        if not word:
            return False
        if word in self.word_rules.get('block', []):
            return False
        return True
    
    def _load_meaning_cache(self) -> Dict[str, tuple[str, bool]]:
        """저장된 의미 캐시 로드"""
        if not os.path.exists(self.meaning_cache_file):
            return {}
        
        try:
            with open(self.meaning_cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            # JSON 형태를 tuple로 변환
            result = {}
            for word, (meaning, success) in cache_data.items():
                result[word] = (meaning, success)
            return result
        except Exception as e:
            print(f"[캐시] 로드 실패: {e}")
            return {}
    
    def _save_meaning_cache(self, new_meanings: Dict[str, tuple[str, bool]]):
        """새로운 의미를 캐시에 저장"""
        # 기존 캐시와 병합
        self.meaning_cache.update(new_meanings)
        
        try:
            # tuple을 JSON 직렬화 가능한 형태로 변환
            cache_data = {word: [meaning, success] for word, (meaning, success) in self.meaning_cache.items()}
            with open(self.meaning_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            print(f"[캐시] {len(new_meanings)}개 의미 저장됨 (총 {len(self.meaning_cache)}개)")
        except Exception as e:
            print(f"[캐시] 저장 실패: {e}")
    
    def _load_profane_cache(self) -> Dict[str, bool]:
        """욕설 판별 결과 캐시 로드"""
        if not os.path.exists(self.profane_cache_file):
            return {}
        try:
            with open(self.profane_cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return {str(k): bool(v) for k, v in data.items()}
        except Exception as e:
            print(f"[욕설필터] 캐시 로드 실패: {e}")
        return {}
    
    def _save_profane_cache(self):
        """욕설 판별 캐시 저장"""
        try:
            with open(self.profane_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.profane_cache, f, ensure_ascii=False, indent=2)
            print(f"[욕설필터] 캐시 저장: {len(self.profane_cache)}개 단어")
        except Exception as e:
            print(f"[욕설필터] 캐시 저장 실패: {e}")
    
    def remove_particles(self, word: str) -> str:
        """한국어 조사 제거"""
        cleaned = word
        for particle in self.korean_particles:
            if cleaned.endswith(particle):
                cleaned = cleaned[:-len(particle)]
                break
        return cleaned
    
    def fetch_post_content(self, post_url: str) -> str:
        """게시글 URL에서 내용 추출"""
        # 잘못된 링크 필터링
        if not post_url or post_url.startswith('javascript:') or 'javascript:;' in post_url:
            return ""
        
        # 외부 링크는 건너뛰기
        if not post_url.startswith('https://gall.dcinside.com'):
            return ""
        
        try:
            response = requests.get(post_url, headers=self.headers, timeout=8)
            response.raise_for_status()
            
            # 응답이 HTML인지 확인
            if 'text/html' not in response.headers.get('Content-Type', ''):
                return ""
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 디시인사이드 게시글 내용 셀렉터 (우선순위 순)
            content_selectors = [
                'div.writing_view_box',  # 가장 일반적인 게시글 내용
                'div.view_content_wrap',
                'div.view_content',
                'div.section_view',
                'div.view_content_wrap div',
                'div[class*="writing"]',
                'div[class*="view"]',
            ]
            
            content_text = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 스크립트, 스타일, 주석 제거
                    for tag in content_elem(["script", "style", "noscript", "iframe"]):
                        tag.decompose()
                    
                    # 공지사항, 댓글 영역 제거
                    for unwanted in content_elem.find_all(['div', 'section'], class_=lambda x: x and any(
                        keyword in str(x).lower() for keyword in ['comment', 'reply', 'notice', 'ad', 'advertisement']
                    )):
                        unwanted.decompose()
                    
                    content_text = content_elem.get_text(separator=' ', strip=True)
                    # 의미있는 내용인지 확인 (너무 짧거나 공지사항 같은 경우 제외)
                    if content_text and len(content_text) > 20 and not content_text.startswith('안녕하세요? 디시인사이드입니다'):
                        break
            
            # 내용이 없으면 본문 영역 전체에서 텍스트 추출 시도
            if not content_text or len(content_text) < 20:
                # 게시글 본문을 포함하는 메인 영역 찾기
                main_areas = soup.find_all('div', class_=lambda x: x and isinstance(x, (str, list)) and (
                    'view' in str(x).lower() or 'content' in str(x).lower() or 'writing' in str(x).lower()
                ))
                
                for area in main_areas:
                    # 불필요한 요소 제거
                    for tag in area(["script", "style", "nav", "header", "footer", "aside", "noscript"]):
                        tag.decompose()
                    
                    # 댓글, 공지사항 제거
                    for unwanted in area.find_all(['div', 'section'], class_=lambda x: x and any(
                        keyword in str(x).lower() for keyword in ['comment', 'reply', 'notice', 'ad']
                    )):
                        unwanted.decompose()
                    
                    temp_text = area.get_text(separator=' ', strip=True)
                    if temp_text and len(temp_text) > len(content_text) and not temp_text.startswith('안녕하세요? 디시인사이드입니다'):
                        content_text = temp_text
                        if len(content_text) > 50:  # 충분한 길이면 중단
                            break
            
            # 내용 정제 (공백 정리, 길이 제한)
            if content_text:
                # 연속된 공백 제거
                import re
                content_text = re.sub(r'\s+', ' ', content_text).strip()
                # 내용 길이 제한 (너무 긴 경우 앞부분만)
                content_text = content_text[:2000]  # 최대 2000자
            
            return content_text
            
        except requests.exceptions.Timeout:
            return ""  # 타임아웃은 조용히 처리
        except requests.exceptions.RequestException as e:
            # 503, 404 등은 조용히 처리 (너무 많은 로그 방지)
            if '503' not in str(e) and '404' not in str(e):
                pass  # 다른 에러는 로그 남기지 않음
            return ""
        except Exception as e:
            # 예상치 못한 에러만 로그
            return ""
    
    def crawl_dcinside(self, include_content: bool = True, max_posts_per_gallery: int = 20) -> List[Dict]:
        """디시인사이드 크롤링"""
        galleries = ['dcbest', 'baseball_new11', 'ani1_new2', 'entertain',
        'leagueoflegends6', 'valorant', 'battlegrounds']
        base_url = 'https://gall.dcinside.com'
        all_posts = []
        
        for gallery in galleries:
            try:
                # 일반 목록만 크롤링
                list_url = f"{base_url}/board/lists/?id={gallery}"
                
                gallery_posts = []
                gallery_titles_count = 0
                seen_links = set()
                
                print(f"[크롤링] {gallery} 갤러리 크롤링 시작: {list_url}")
                
                response = requests.get(list_url, headers=self.headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 제목 추출 - 다양한 셀렉터 시도
                title_elements = soup.find_all('td', class_='gall_tit')
                if not title_elements:
                    # 대체 셀렉터 시도
                    title_elements = soup.find_all('a', class_='icon_txt')
                if not title_elements:
                    # 추가 대체 셀렉터
                    title_elements = soup.select('td.gall_tit a, a.icon_txt, .gall_tit a')
                
                # 디버깅: 셀렉터 결과가 없으면 HTML 구조 확인
                if not title_elements:
                    print(f"[DEBUG] {gallery} 갤러리 HTML 구조 확인 중...")
                    # 모든 링크 찾기 시도
                    all_links = soup.find_all('a', href=True)
                    print(f"[DEBUG] 전체 링크 개수: {len(all_links)}")
                    if all_links:
                        # 게시물 링크 패턴 확인
                        board_links = [a for a in all_links if '/board/view/' in a.get('href', '')]
                        print(f"[DEBUG] 게시물 링크 개수: {len(board_links)}")
                        if board_links:
                            # 링크에서 제목 추출 시도
                            title_elements = board_links
                            print(f"[DEBUG] 대체 셀렉터로 {len(title_elements)}개 게시물 링크 발견")
                    
                    # 여전히 없으면 HTML 일부 출력
                    if not title_elements:
                        print(f"[WARNING] {gallery} 갤러리에서 게시물을 찾을 수 없습니다.")
                        # HTML 구조 확인을 위한 샘플 출력
                        sample_html = soup.prettify()[:500] if soup else "HTML 없음"
                        print(f"[DEBUG] HTML 샘플 (처음 500자): {sample_html}")
                
                url_posts_before = len(gallery_posts)
                url_found_count = 0  # 발견된 게시물 수 (중복 포함)
                
                for title_elem in title_elements:
                    if len(gallery_posts) >= max_posts_per_gallery:
                        break
                    
                    if title_elem.name == 'a':
                        link = title_elem
                    else:
                        link = title_elem.find('a')
                    
                    if not link:
                        continue
                    
                    title_text = link.text.strip() if hasattr(link, 'text') else link.get_text(strip=True)
                    if not title_text:
                        continue
                    
                    # href 추출
                    href = link.get('href', '')
                    if href and not href.startswith('http'):
                        if href.startswith('/'):
                            full_link = base_url + href
                        else:
                            full_link = base_url + '/' + href
                    else:
                        full_link = href if href else ''
                    
                    # 잘못된 링크 필터링
                    if not full_link or full_link.startswith('javascript:') or 'javascript:;' in full_link:
                        continue
                    
                    # 디시인사이드 게시글 링크인지 확인
                    if '/board/view/' not in full_link:
                        continue
                    
                    url_found_count += 1
                    
                    # 동일 게시글 중복 수집 방지
                    if full_link in seen_links:
                        continue
                    seen_links.add(full_link)
                    
                    post_data = {
                        'title': title_text,
                        'source': f"DCInside {gallery}",
                        'link': full_link,
                        'content': ''  # 기본값
                    }
                    
                    # 게시글 내용 가져오기
                    if include_content and full_link:
                        content = self.fetch_post_content(full_link)
                        post_data['content'] = content
                        time.sleep(0.5)  # 서버 부하 방지를 위한 대기
                    
                    gallery_posts.append(post_data)
                    gallery_titles_count += 1
                
                # 게시물 수집 결과 로그
                url_posts_after = len(gallery_posts)
                url_posts_added = url_posts_after - url_posts_before
                duplicate_count = url_found_count - url_posts_added
                if url_posts_added > 0:
                    print(f"[크롤링] {gallery} 갤러리: {url_posts_added}개 게시물 수집 (발견: {url_found_count}개, 중복 제외: {duplicate_count}개)")
                else:
                    print(f"[크롤링] {gallery} 갤러리: 게시물 없음 (발견: {url_found_count}개)")
                
                all_posts.extend(gallery_posts)
                print(f"[OK] {gallery} 갤러리에서 총 {gallery_titles_count}개 제목 수집" + 
                      (f" (내용 포함: {sum(1 for p in gallery_posts if p.get('content'))}개)" if include_content else ""))
                time.sleep(1)
                
            except Exception as e:
                print(f"[ERROR] {gallery} 갤러리 크롤링 실패: {e}")
        
        return all_posts
    
    def extract_all_keywords(self, texts: List[str]) -> Counter:
        """모든 한글 키워드 추출 (조사 제거 포함)"""
        keyword_counts = Counter()
        
        for text in texts:
            # 한글 단어 추출 (길이 제한 제거)
            words = re.findall(r'[가-힣]{2,15}', text)
            for word in words:
                # 조사 제거
                cleaned = self.remove_particles(word)
                if len(cleaned) >= 2:
                    keyword_counts[cleaned] += 1
        
        return keyword_counts
    
    def filter_slang_candidates(self, keyword_counts: Counter) -> Dict[str, int]:
        """기본 필터링 (일반 단어 제외)"""
        filtered = {}
        for word, count in keyword_counts.items():
            # 일반 단어 제외
            if word in self.common_words:
                continue
            # 일반 단어 패턴 체크
            is_common = False
            for pattern in self.non_slang_patterns:
                if re.match(pattern, word):
                    is_common = True
                    break
            if is_common:
                continue
            # 네이버 사전 캐시 확인 (이미 확인된 표준어는 제외)
            if word in self.naver_dict_cache and self.naver_dict_cache[word]:
                continue
            filtered[word] = count
        return filtered
    
    def pre_naver_filter(self, word_counts: Dict[str, int], min_count: int = 3) -> Dict[str, int]:
        """
        네이버 사전 API 호출 전 사전 필터링
        - 빈도수 기반 필터링 (너무 적게 나온 단어 제외)
        - 더 강력한 패턴/조사 필터링
        """
        filtered = {}
        
        # 추가 일반 단어 패턴 (신조어가 아닌 확실한 패턴)
        additional_patterns = [
            r'[0-9]',  # 숫자 포함
            r'[a-zA-Z]',  # 영문 포함
            r'하다$', r'되다$', r'이다$', r'같다$', r'있다$', r'없다$',  # 일반 동사/형용사
            r'^이[가-힣]{0,2}$', r'^그[가-힣]{0,2}$', r'^저[가-힣]{0,2}$',  # 지시사
            r'^어떤$', r'^어떻게$', r'^왜$', r'^언제$', r'^어디$',  # 의문사
            r'^모든$', r'^전체$', r'^일부$', r'^많은$', r'^적은$', r'^모두$',  # 수량 표현
            r'^그리고$', r'^그런데$', r'^그래서$', r'^그러나$',  # 접속사
            r'^하지만$', r'^그러면$', r'^그래도$',  # 접속사
            r'^이렇게$', r'^그렇게$', r'^저렇게$',  # 부사
            r'^여기$', r'^거기$', r'^저기$',  # 장소 지시
            r'^지금$', r'^오늘$', r'^어제$', r'^내일$',  # 시간 표현
            r'^여러$', r'^다른$', r'^같은$', r'^다른$',  # 형용사
        ]
        
        for word, count in word_counts.items():
            # 1. 빈도수 체크 (너무 적게 나온 단어 제외)
            if count < min_count:
                continue
            
            # 2. 추가 패턴 체크
            is_common = False
            for pattern in additional_patterns:
                if re.match(pattern, word):
                    is_common = True
                    break
            if is_common:
                continue
            
            # 4. 일반적인 한국어 어미 패턴 제외
            common_endings = ['에서', '에게', '으로', '로', '의', '을', '를', '이', '가', '은', '는', '도', '만']
            if any(word.endswith(ending) for ending in common_endings):
                continue
            
            filtered[word] = count
        
        return filtered
    
    def filter_contained_words(self, word_counts: Dict[str, int]) -> Dict[str, int]:
        """
        포함 관계 필터링: 짧은 단어를 포함한 더 긴 단어구 제거
        예: "갓생"을 포함한 "갓생살기"가 있으면 "갓생살기" 제거, "갓생"만 남김
        """
        words_list = list(word_counts.keys())
        words_to_remove = set()
        
        # 길이순으로 정렬 (짧은 단어부터)
        words_list_sorted = sorted(words_list, key=len)
        
        for i, word1 in enumerate(words_list_sorted):
            if word1 in words_to_remove:
                continue
            
            # 현재 단어보다 긴 단어들 중에서 현재 단어를 포함하는 것 찾기
            for word2 in words_list_sorted[i+1:]:
                if word2 in words_to_remove:
                    continue
                
                # word1이 word2에 포함되어 있으면 word2 제거 (긴 단어 제거)
                if word1 in word2:
                    words_to_remove.add(word2)
        
        # 포함된 단어 제거
        final_filtered = {word: count for word, count in word_counts.items() if word not in words_to_remove}
        
        if words_to_remove:
            print(f"[필터링] 포함 관계 필터링: {len(words_to_remove)}개 단어 제거 (짧은 단어를 포함한 긴 단어구)")
        
        return final_filtered
    
    def _load_naver_dict_cache(self):
        """네이버 사전 확인 결과 캐시 로드"""
        if not os.path.exists(self.naver_dict_cache_file):
            return
        
        try:
            with open(self.naver_dict_cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # True(표준어) 항목만 유지
            filtered = {word: value for word, value in data.items() if value}
            removed = len(data) - len(filtered)
            self.naver_dict_cache = filtered
            if removed:
                print(f"[네이버 사전 캐시] {removed}개 False 항목 제거 후 {len(filtered)}개 유지")
                self._save_naver_dict_cache()
            else:
                print(f"[네이버 사전 캐시] {len(self.naver_dict_cache)}개 결과 로드됨")
        except Exception as e:
            print(f"[네이버 사전 캐시] 로드 실패: {e}")
            self.naver_dict_cache = {}
    
    def _save_naver_dict_cache(self):
        """네이버 사전 확인 결과 캐시 저장"""
        try:
            with open(self.naver_dict_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.naver_dict_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[네이버 사전 캐시] 저장 실패: {e}")
    
    def check_naver_dictionary(self, word: str) -> bool:
        """네이버 사전에서 표준어인지 확인 (True면 표준어) - 캐싱 지원"""
        # 캐시 확인
        if word in self.naver_dict_cache:
            return self.naver_dict_cache[word]
        
        # 캐시에 없으면 API 호출
        result = self._check_naver_dictionary_api(word)
        
        # True(표준어)만 캐시에 저장
        if result:
            self.naver_dict_cache[word] = True
            self._naver_cache_dirty = True
        else:
            # False 결과는 캐시에서 제거하여 불필요한 저장 방지
            if word in self.naver_dict_cache:
                del self.naver_dict_cache[word]
                self._naver_cache_dirty = True
        return result
    
    def _check_naver_dictionary_api(self, word: str) -> bool:
        """네이버 사전 API 호출 (내부 메서드)"""
        if not self.naver_client_id or not self.naver_client_secret:
            # API 키가 없으면 웹 스크래핑 방식 사용
            try:
                url = f"https://ko.dict.naver.com/api3/koko/search?query={word}"
                response = requests.get(url, headers=self.headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('items') and len(data.get('items', [])) > 0:
                        return True
                return False
            except:
                return False
        
        # 네이버 사전 API 사용 (API 키가 있는 경우)
        try:
            url = "https://openapi.naver.com/v1/search/encyc"
            headers = {
                'X-Naver-Client-Id': self.naver_client_id,
                'X-Naver-Client-Secret': self.naver_client_secret
            }
            params = {'query': word}
            response = requests.get(url, headers=headers, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                # 검색 결과가 있으면 표준어
                if data.get('items') and len(data.get('items', [])) > 0:
                    return True
            return False
        except Exception as e:
            # 에러 발생 시 False 반환 (캐시에 저장하지 않음)
            return False
    
    def check_naver_dictionary_batch(self, words: List[str], max_workers: int = 10) -> Dict[str, bool]:
        """네이버 사전 확인을 배치로 처리 (병렬 처리)"""
        results = {}
        
        # 캐시에 있는 단어는 먼저 처리
        words_to_check = []
        for word in words:
            if word in self.naver_dict_cache:
                results[word] = self.naver_dict_cache[word]
            else:
                words_to_check.append(word)
        
        if not words_to_check:
            return results
        
        print(f"[네이버 사전] {len(words_to_check)}개 단어 병렬 확인 중... (캐시: {len(results)}개)")
        
        # 병렬 처리
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_word = {
                executor.submit(self._check_naver_dictionary_api, word): word 
                for word in words_to_check
            }
            
            for future in as_completed(future_to_word):
                word = future_to_word[future]
                try:
                    result = future.result()
                    results[word] = result
                    if result:
                        self.naver_dict_cache[word] = True
                        self._naver_cache_dirty = True
                    elif word in self.naver_dict_cache:
                        del self.naver_dict_cache[word]
                except Exception as e:
                    print(f"[WARNING] 네이버 사전 확인 실패 ({word}): {e}")
                    results[word] = False
        
        # 캐시 저장
        self._save_naver_dict_cache()
        
        return results
    
    def _is_profane_word(self, word: str) -> bool:
        """GPT를 사용해 단어가 욕설인지 판별 (단일 단어용)"""
        if not word:
            return False
        cached = self.profane_cache.get(word)
        if cached is not None:
            return cached
    
        if not self.openai_client:
            return False
        
        prompt = (
            "다음 한국어 단어가 욕설·비속어·차별적 표현에 해당하는지 웹에서 검색한 결과를 바탕으로 판단해해주세요.\n"
            f"단어: {word}\n\n"
            "욕설/비속어라면 YES, 아니면 NO만 대문자로 답변하세요."
        )
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a Korean content moderator. Answer with YES or NO only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=5
            )
            answer = response.choices[0].message.content.strip().upper()
            is_profane = answer.startswith("YES")
            self.profane_cache[word] = is_profane
            self._profane_cache_dirty = True
            if is_profane:
                print(f"[욕설필터] '{word}' → GPT 판별: 욕설/비속어 (제외)")
            else:
                print(f"[욕설필터] '{word}' → GPT 판별: 안전")
            return is_profane
        except Exception as e:
            print(f"[욕설필터] GPT 판별 실패 ({word}): {e}")
            return False
    
    def _is_profane_words_batch(self, words: List[str]) -> Dict[str, bool]:
        """GPT를 사용해 여러 단어가 욕설인지 배치로 판별"""
        if not words:
            return {}
        if not self.openai_client:
            return {word: False for word in words}
        
        # 캐시 확인
        results = {}
        words_to_check = []
        for word in words:
            cached = self.profane_cache.get(word)
            if cached is not None:
                results[word] = cached
            else:
                words_to_check.append(word)
        
        if not words_to_check:
            return results
        
        # 배치 요청 (최대 20개)
        words_batch = words_to_check[:20]
        words_list = "\n".join([f"- {word}" for word in words_batch])
        
        prompt = (
            "다음 한국어 단어들이 욕설·비속어·차별적 표현에 해당하는지 판단해 주세요.\n\n"
            f"단어 목록:\n{words_list}\n\n"
            "각 단어에 대해 욕설/비속어라면 YES, 아니면 NO를 대문자로 답변하세요.\n"
            "답변 형식: 각 줄에 '단어: YES' 또는 '단어: NO' 형식으로 답변하세요."
        )
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a Korean content moderator. Answer with YES or NO for each word."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=200
            )
            answer = response.choices[0].message.content.strip()
            
            # 결과 파싱
            for word in words_batch:
                is_profane = False
                # 단어: YES 또는 단어: NO 형식 찾기
                word_line = None
                for line in answer.split('\n'):
                    if word in line and (': YES' in line.upper() or ': NO' in line.upper()):
                        word_line = line.upper()
                        break
                
                if word_line and ': YES' in word_line:
                    is_profane = True
                
                results[word] = is_profane
                self.profane_cache[word] = is_profane
                self._profane_cache_dirty = True
                
                if is_profane:
                    print(f"[욕설필터] '{word}' → GPT 판별: 욕설/비속어 (제외)")
            else:
                    print(f"[욕설필터] '{word}' → GPT 판별: 안전")
            
            return results
        except Exception as e:
            print(f"[욕설필터] GPT 배치 판별 실패: {e}")
            # 실패 시 모두 안전으로 처리
            for word in words_batch:
                results[word] = False
            return results
    
    def _filter_profane_candidates(self, sorted_candidates: List[Dict], target_count: int) -> List[Dict]:
        """NLP 상위 후보에 GPT 욕설 필터 적용 (비속어면 제외하고 다음 단어로 대체)"""
        if target_count <= 0:
            return []
        if not sorted_candidates:
            return []
        if not self.openai_client:
            # GPT 사용 불가 시 기존 로직 유지
            print("[욕설필터] GPT 비활성화 상태이므로 욕설 필터를 건너뜁니다.")
            return sorted_candidates[:target_count]
        
        print(f"[욕설필터] NLP 상위 {target_count}개 후보에 욕설 필터링 적용...")
        
        # 1단계: NLP 확률 기준으로 정렬된 리스트에서 상위 target_count개 선택
        top_candidates = sorted_candidates[:target_count]
        top_words = [c['word'] for c in top_candidates]
        
        print(f"[욕설필터] 상위 {len(top_words)}개 단어 배치 판별 시작...")
        
        # 2단계: 상위 20개에 비속어 필터 적용 (배치로)
        batch_results = self._is_profane_words_batch(top_words)
        
        # 배치 처리 후 대기 (RPM 제한 준수)
        wait_time = 10
        print(f"[욕설필터] RPM 제한 준수를 위해 {wait_time}초 대기...")
        time.sleep(wait_time)
        
        # 3단계: 비속어로 판별된 단어 제외하고 안전한 후보만 수집
        safe_candidates = []
        profane_count = 0
        
        for candidate in top_candidates:
            word = candidate['word']
            is_profane = batch_results.get(word, False)
            
            if is_profane:
                profane_count += 1
                print(f"[욕설필터] '{word}' → 욕설/비속어 판별 (제외)")
                continue
            
            safe_candidates.append(candidate)
        
        # 4단계: 비속어로 제외된 단어만큼 다음 순위 단어로 대체
        if profane_count > 0 and len(safe_candidates) < target_count:
            print(f"[욕설필터] {profane_count}개 비속어 제외됨. 다음 순위 단어로 대체 중...")
            replace_count = target_count - len(safe_candidates)
            next_idx = target_count
            
            while len(safe_candidates) < target_count and next_idx < len(sorted_candidates):
                candidate = sorted_candidates[next_idx]
                word = candidate['word']
                
                # 개별 비속어 판별
                if self._is_profane_word(word):
                    print(f"[욕설필터] '{word}' → 욕설/비속어 판별 (제외)")
                    next_idx += 1
                    # 개별 요청 후 대기 (RPM 제한 준수)
                    if next_idx < len(sorted_candidates):
                        wait_time = 2
                        time.sleep(wait_time)
                    continue
                
                safe_candidates.append(candidate)
                next_idx += 1
                
                # 개별 요청 후 대기 (RPM 제한 준수)
                if len(safe_candidates) < target_count and next_idx < len(sorted_candidates):
                    wait_time = 2
                    time.sleep(wait_time)
        
        if len(safe_candidates) < target_count:
            print(f"[욕설필터] 충분한 안전 후보가 없어 {len(safe_candidates)}개만 선택되었습니다.")
        else:
            print(f"[욕설필터] {len(safe_candidates)}개 안전한 후보 선택 완료 (비속어 {profane_count}개 제외)")
        
        if self._profane_cache_dirty:
            self._save_profane_cache()
            self._profane_cache_dirty = False
        
        return safe_candidates
    
    def calculate_slang_score(self, word: str, count: int, contexts: List[str]) -> float:
        """신조어 점수 계산 (기본 점수)"""
        score = 0.0
        
        # 길이 점수 (3-5자가 최적)
        word_len = len(word)
        if 3 <= word_len <= 5:
            score += 2.0
        elif word_len == 2 or word_len == 6:
            score += 1.0
        
        # 빈도 점수 (log1p 사용)
        if count > 0:
            score += min(math.log1p(count) * 0.5, 2.0)
        
        # 맥락 다양성 점수
        unique_contexts = len(set(contexts))
        score += min(unique_contexts * 0.3, 2.0)
        
        return score
    
    def enhanced_filter_slang_candidates(
        self, 
        word_counts: Counter, 
        all_texts: List[str],
        use_naver: bool = True,
        use_gpt: bool = False,  # 기본값을 False로 변경 (필터링에서 GPT 비활성화)
        min_count: int = 2,
        target_count: int = 30,  # 상위 30개 반환
        nlp_analysis_count: int = 2000,  # NLP로 분석할 단어 개수
        nlp_threshold: float = 0.41  # NLP 확률 임계값
    ) -> List[Dict]:
        """
        필터링: 네이버 사전 + NLP 확률 기반 필터링
        
        프로세스:
        1. 기본 필터링 (common_words, 패턴 제외)
        1.5. 네이버 사전 전 사전 필터링 (빈도수, 패턴, 길이 등) - API 호출 수 감소
        1.6. 포함 관계 필터링 (짧은 단어를 포함한 더 긴 단어구 제거) - API 호출 수 감소
        2. 네이버 사전 확인 (표준어 제외)
        3. NLP로 분석 (배치 처리, 최대 nlp_analysis_count개)
        4. 확률 0.41 미만 제외
        5. 확률 기준으로 상위 30개 선택
        """
        total_words = len(word_counts)
        print(f"[필터링] 총 {total_words}개 단어 후보 분석 시작...")
        
        # 1단계: 기본 필터링
        filtered = self.filter_slang_candidates(word_counts)
        print(f"[필터링] 1단계 - 기본 필터링 후: {len(filtered)}개")
        
        # 맥락 수집
        word_contexts = {}
        for text in all_texts:
            words_in_text = re.findall(r'[가-힣]{2,8}', text)
            for word in words_in_text:
                cleaned = self.remove_particles(word)
                if cleaned in filtered:
                    if cleaned not in word_contexts:
                        word_contexts[cleaned] = []
                    word_contexts[cleaned].append(text[:200])
        
        # 1.5단계: 네이버 사전 API 호출 전 사전 필터링 (빈도수, 패턴, 길이 등)
        pre_naver_filtered = self.pre_naver_filter(filtered, min_count=min_count)
        print(f"[필터링] 1.5단계 - 네이버 사전 전 사전 필터링 후: {len(pre_naver_filtered)}개")
        
        # 1.6단계: 포함 관계 필터링 (더 긴 단어구에 포함된 짧은 단어 제거)
        pre_naver_filtered = self.filter_contained_words(pre_naver_filtered)
        print(f"[필터링] 1.6단계 - 포함 관계 필터링 후: {len(pre_naver_filtered)}개")
        
        # 2단계: 네이버 사전 확인 및 차단 리스트 체크
        # 차단 리스트 먼저 적용
        filtered_by_block = {}
        for word, count in pre_naver_filtered.items():
            if word in self.word_rules.get('block', []):
                continue
            filtered_by_block[word] = count
        
        # 네이버 사전 확인 (배치 처리)
        naver_results = {}
        if use_naver and filtered_by_block:
            words_to_check = list(filtered_by_block.keys())
            naver_results = self.check_naver_dictionary_batch(words_to_check, max_workers=10)
        
        # 최종 후보 선정
        pre_nlp_candidates = []
        for word, count in filtered_by_block.items():
            # 네이버 사전 확인 결과 (표준어면 제외)
            if use_naver and naver_results.get(word, False):
                continue
            
            contexts = word_contexts.get(word, [])
            pre_nlp_candidates.append({
                'word': word,
                'count': count,
                'contexts': contexts
            })
        
        print(f"[필터링] 2단계 - 네이버 사전 필터링 후: {len(pre_nlp_candidates)}개")
        
        # NLP 분석 개수 제한 (빈도순으로 정렬하여 상위 nlp_analysis_count개만 분석)
        if len(pre_nlp_candidates) > nlp_analysis_count:
            pre_nlp_candidates.sort(key=lambda x: x['count'], reverse=True)
            pre_nlp_candidates = pre_nlp_candidates[:nlp_analysis_count]
            print(f"[필터링] NLP 분석 대상: 상위 {nlp_analysis_count}개로 제한 (빈도순)")
        
        # 3단계: NLP 분류기로 단어 분석 (배치 처리)
        nlp_results = {}
        if self.nlp_classifier and pre_nlp_candidates:
            print(f"[필터링] 3단계 - NLP 분석 시작 ({len(pre_nlp_candidates)}개 단어)...")
            
            # 배치 입력 구성
            batch_items = []
            for candidate in pre_nlp_candidates:
                batch_items.append({
                    'word': candidate['word'],
                    'contexts': candidate['contexts']
                })
            
            # 배치 예측 (slang_classifier의 predict_batch 사용)
            try:
                nlp_predictions = self.nlp_classifier.predict_batch(batch_items, threshold=nlp_threshold)
                
                # 결과를 딕셔너리로 변환
                for pred in nlp_predictions:
                    word = pred['word']
                    nlp_results[word] = {
                        'probability': pred.get('probability', 0.0),
                        'is_slang': pred.get('is_slang', False),
                        'confidence': pred.get('confidence', 0.0)
                    }
                
                print(f"[필터링] NLP 분석 완료: {len(nlp_results)}개 결과")
            except Exception as e:
                print(f"[필터링] NLP 배치 분석 실패: {e}")
                # NLP 실패 시 빈 결과 반환
                return []
        else:
            if not self.nlp_classifier:
                print("[필터링] NLP 분류기가 비활성화되어 있습니다.")
            return []
        
        # 4단계: 확률 0.41 미만 제외
        filtered_by_nlp = []
        for candidate in pre_nlp_candidates:
            word = candidate['word']
            nlp_result = nlp_results.get(word)
            
            if nlp_result is None:
                continue
            
            nlp_probability = nlp_result['probability']
            
            # 확률이 임계값 미만이면 제외
            if nlp_probability < nlp_threshold:
                    continue
            
            filtered_by_nlp.append({
                'word': word,
                'count': candidate['count'],
                'contexts': candidate['contexts'],
                'nlp_probability': nlp_probability,
                'nlp_confidence': nlp_result['confidence']
            })
        
        print(f"[필터링] 4단계 - NLP 확률 필터링 후: {len(filtered_by_nlp)}개 (임계값: {nlp_threshold})")
        
        # 5단계: 확률 기준으로 정렬
        filtered_by_nlp.sort(key=lambda x: x['nlp_probability'], reverse=True)
        
        # 5.5단계: GPT 욕설 필터 적용 (가능한 경우)
        final_candidates = self._filter_profane_candidates(filtered_by_nlp, target_count)
        
        # 최종 결과 구성
        candidates = []
        for item in final_candidates:
            word = item['word']
            count = item['count']
            contexts = item['contexts']
            nlp_probability = item['nlp_probability']
            
            # 점수 계산 (확률 기반)
            base_score = self.calculate_slang_score(word, count, contexts)
            final_score = base_score + (nlp_probability * 10)  # 확률을 더 크게 반영
            
            candidates.append({
                'word': word,
                'count': count,
                'score': final_score,
                'contexts': contexts[:5],
                'gpt_probability': None,  # 레거시 필드 (호환성 유지)
                'nlp_probability': nlp_probability,  # NLP 확률
                'gpt_comparison': None  # GPT 비교 결과 (현재 비활성화)
            })
            
        print(f"[필터링] 최종 결과: {len(candidates)}개 신조어 후보 (확률 기준 상위 {target_count}개)")
        if candidates:
            print("[필터링] 최종 후보 목록 (NLP 확률 포함):")
            for idx, item in enumerate(candidates, 1):
                prob = item.get('nlp_probability', 0.0)
                print(f"  {idx:2d}. {item['word']} - NLP 확률 {prob:.3f}")
        
        if self._naver_cache_dirty:
            self._save_naver_dict_cache()
            self._naver_cache_dirty = False
        
        return candidates
    
    def crawl_and_analyze(self, use_enhanced_filter: bool = True) -> List[Dict]:
        """ 크롤링 및 분석 실행 (디시인사이드 전용)"""
        print(" 크롤링 시작...")
        
        try:
            # 디시인사이드 크롤링만 실행 (게시글 내용 포함)
            print("디시인사이드 크롤링 중... (제목 + 내용)")
            dc_posts = self.crawl_dcinside(include_content=True, max_posts_per_gallery=15)
            print(f"디시인사이드에서 {len(dc_posts)}개 게시물 수집")
            
            if not dc_posts:
                print("[WARNING] 수집된 게시물이 없습니다. 기본 크롤링을 사용하세요.")
                return []
            
            # 모든 텍스트 수집 (제목 + 내용)
            all_texts = []
            for post in dc_posts:
                text_parts = [post.get('title', '')]
                content = post.get('content', '')
                if content:
                    text_parts.append(content)
                # 제목과 내용을 합쳐서 하나의 텍스트로
                combined_text = ' '.join(text_parts)
                if combined_text.strip():
                    all_texts.append(combined_text)
            scored_slangs = []
            
            #  필터링만 사용
            if use_enhanced_filter:
                print("\n 필터링 (네이버 사전) 시작... (GPT는 의미 생성에만 사용)")
                all_keyword_counts = self.extract_all_keywords(all_texts)
                
                filtered_counts = Counter(all_keyword_counts)
                
                #  필터링 실행 (NLP 확률 기반 필터링)
                enhanced_candidates = self.enhanced_filter_slang_candidates(
                    filtered_counts,
                    all_texts,
                    use_naver=True,
                    use_gpt=False,  # 필터링에서는 GPT 사용 안 함 (Rate Limit 방지)
                    min_count=self.filter_min_count,
                    target_count=self.filter_target_count,  # 상위 N개 반환
                    nlp_analysis_count=2000,  # NLP로 분석할 단어 개수
                    nlp_threshold=self.filter_nlp_threshold  # NLP 확률 임계값
                )
                
                # 의미 생성 배치 처리 준비
                from meaning_extractor import MeaningExtractor
                extractor = MeaningExtractor(openai_client=self.openai_client)
                
                # 배치 입력 구성 (컨텍스트 최소화)
                batch_items = []
                for candidate in enhanced_candidates:
                    word = candidate['word']
                    contexts = candidate.get('contexts', [])
                    # 캐시에 없을 때만 배치에 포함
                    # 수동 의미 사전에 있으면 배치 제외
                    if self.manual_meanings.get(word):
                        continue
                    if not self.meaning_cache.get(word):
                        # 컨텍스트 최소화: 첫 번째 컨텍스트만 사용 (토큰 절약)
                        batch_items.append({
                            'word': word,
                            'contexts': [contexts[0]] if contexts else []
                        })
                
                batch_results = {}
                if self.openai_client and batch_items:
                    # 배치 호출 (RPM=3 준수를 위해 5개 단위로 분할, 각 배치 사이 30초 대기)
                    batch_results = {}
                    chunk_size = 5  # RPM 제한 준수를 위해 5개로 줄임
                    import math
                    for i in range(0, len(batch_items), chunk_size):
                        chunk = batch_items[i:i+chunk_size]
                        print(f"[의미추출] 배치 처리 중 ({i//chunk_size + 1}/{(len(batch_items)-1)//chunk_size + 1}): {len(chunk)}개 단어")
                        res = extractor.extract_meanings_batch(chunk)
                        if res:
                            batch_results.update(res)
                            print(f"[의미추출] 배치 성공: {len(res)}개 의미 추출")
                        else:
                            print(f"[의미추출] 배치 실패 또는 Rate Limit - 다음 배치까지 대기")
                            # Rate Limit 발생 시 즉시 중단 (재시도 없음)
                            if i + chunk_size < len(batch_items):
                                break
                        
                        # RPM=3 준수: 각 배치 사이 최소 30초 대기
                        if i + chunk_size < len(batch_items):
                            wait_time = 10
                            print(f"[의미추출] RPM 제한 준수를 위해 {wait_time}초 대기...")
                            time.sleep(wait_time)
                    # 결과를 파일로 저장
                    try:
                        import json, datetime
                        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
                        data_dir = os.path.abspath(data_dir)
                        os.makedirs(data_dir, exist_ok=True)
                        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                        out_path = os.path.join(data_dir, f'meanings_{ts}.json')
                        with open(out_path, 'w', encoding='utf-8') as f:
                            json.dump(batch_results, f, ensure_ascii=False, indent=2)
                        print(f"[의미추출] 배치 결과 저장: {out_path}")
                    except Exception as e:
                        print(f"[의미추출] 배치 결과 파일 저장 실패: {e}")
                
                #  필터링 결과 추가 (수동 사전/배치 결과 적용)
                for candidate in enhanced_candidates:
                    word = candidate['word']
                    contexts = candidate.get('contexts', [])
                    meaning = f'{word}의 의미 (분석 중)'
                    gpt_meaning_success = None
                    
                    cached = self.meaning_cache.get(word)
                    if cached:
                        if isinstance(cached, tuple):
                            meaning, gpt_meaning_success = cached
                        else:
                            meaning = cached
                    else:
                        # 수동 의미 우선 적용
                        manual_data = self.manual_meanings.get(word)
                        if manual_data:
                            if isinstance(manual_data, dict):
                                meaning = manual_data.get('meaning', f'{word}의 의미 (분석 중)')
                            else:
                                # 구 형식 호환
                                meaning = str(manual_data)
                            gpt_meaning_success = None  # 수동 입력
                            self.meaning_cache[word] = (meaning, gpt_meaning_success)
                        elif word in batch_results:
                            meaning = batch_results[word]
                            gpt_meaning_success = True if meaning and meaning != f'{word}의 의미 (분석 중)' else False
                            self.meaning_cache[word] = (meaning, gpt_meaning_success)
                        else:
                            # GPT 비활성화 또는 배치 실패 시 기본값 유지
                            pass
                    
                    # 예문 설정 (수동 예문 우선)
                    final_examples = contexts[:3]
                    manual_data = self.manual_meanings.get(word)
                    if manual_data and isinstance(manual_data, dict):
                        manual_examples = manual_data.get('examples', [])
                        if manual_examples and isinstance(manual_examples, list) and len(manual_examples) > 0:
                            final_examples = manual_examples
                    
                    scored_slangs.append({
                        'word': word,
                        'count': candidate['count'],
                        'score': candidate['score'],
                        'contexts': contexts,
                        'meaning': meaning,
                        'examples': final_examples,
                        'method': 'enhanced',
                        'is_standard_word': False,
                        'gpt_probability': candidate.get('gpt_probability'),
                        'gpt_meaning_success': gpt_meaning_success,
                        'nlp_probability': candidate.get('nlp_probability')
                    })
            
            # 중복 제거 및 정렬
            unique_slangs = {}
            for slang in scored_slangs:
                word = slang['word']
                if word not in unique_slangs or slang['score'] > unique_slangs[word]['score']:
                    unique_slangs[word] = slang
            
            result = list(unique_slangs.values())
            # NLP 확률 우선 정렬 (동률 시 사용 횟수, 점수 순)
            result.sort(
                key=lambda x: (
                    x.get('nlp_probability', 0.0),
                    x.get('count', 0),
                    x.get('score', 0)
                ),
                reverse=True
            )
            
            enhanced_count = sum(1 for s in result if s.get('method') == 'enhanced')
            
            print(f"\n[결과] 총 {len(result)}개 신조어 후보 발견 (중복 제거 후)")
            if enhanced_count > 0:
                print(f"  -  필터링: {enhanced_count}개")
            
            return result[:30]  # 상위 30개 반환
            
        except Exception as e:
            print(f"[ERROR]  크롤링 실패: {e}")
            import traceback
            traceback.print_exc()
            return []
