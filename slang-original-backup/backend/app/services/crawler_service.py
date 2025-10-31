import re
from typing import List, Dict
from bs4 import BeautifulSoup
import httpx
from datetime import datetime

from app.core.config import settings


class DCInsideCrawler:
    """디시인사이드 크롤러"""
    
    def __init__(self):
        self.base_url = "https://www.dcinside.com"
        self.headers = {
            "User-Agent": settings.CRAWLER_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        self.galleries = [
            "baseball_new11",  # 야구
            "football_new6",   # 축구
            "hit",             # 힙합
            "game",            # 게임
            "programming",     # 프로그래밍
        ]
    
    async def crawl_gallery(self, gallery_id: str, page: int = 1) -> List[str]:
        """갤러리 게시물 제목 크롤링
        
        Args:
            gallery_id: 갤러리 ID
            page: 페이지 번호
            
        Returns:
            게시물 제목 목록
        """
        url = f"{self.base_url}/board/lists/?id={gallery_id}&page={page}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=10.0)
                response.raise_for_status()
        except Exception as e:
            print(f"크롤링 실패 ({gallery_id}): {str(e)}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        titles = []
        
        # 제목 추출 (실제 HTML 구조에 맞게 수정 필요)
        post_titles = soup.find_all('a', class_='title')
        
        for post in post_titles:
            title = post.get_text(strip=True)
            if title:
                titles.append(title)
        
        return titles
    
    async def crawl_all_galleries(self) -> List[str]:
        """모든 갤러리 크롤링
        
        Returns:
            모든 게시물 제목 목록
        """
        all_titles = []
        
        for gallery_id in self.galleries:
            titles = await self.crawl_gallery(gallery_id)
            all_titles.extend(titles)
            
            print(f"[{gallery_id}] {len(titles)}개 제목 수집")
        
        return all_titles
    
    def extract_slangs(self, titles: List[str]) -> Dict[str, int]:
        """제목에서 신조어 추출
        
        Args:
            titles: 게시물 제목 목록
            
        Returns:
            {신조어: 빈도수} 딕셔너리
        """
        slang_counter = {}
        
        # 한글 2-10자 단어 추출 (간단한 휴리스틱)
        pattern = re.compile(r'[가-힣]{2,10}')
        
        for title in titles:
            words = pattern.findall(title)
            
            for word in words:
                # 일반적인 단어 필터링 (실제로는 더 정교한 필터링 필요)
                if self._is_potential_slang(word):
                    slang_counter[word] = slang_counter.get(word, 0) + 1
        
        return slang_counter
    
    def _is_potential_slang(self, word: str) -> bool:
        """신조어 후보 판별 (간단한 휴리스틱)
        
        Args:
            word: 검사할 단어
            
        Returns:
            신조어 후보 여부
        """
        # 제외할 일반적인 단어들
        common_words = {
            '게시판', '게시물', '댓글', '추천', '비추천', '신고',
            '질문', '답변', '공지', '이벤트', '안녕하세요', '감사합니다'
        }
        
        if word in common_words:
            return False
        
        # 2-5자 단어만 (너무 짧거나 긴 것 제외)
        if len(word) < 2 or len(word) > 8:
            return False
        
        # 영어+한글 조합, 특수문자 포함 등 체크
        # (실제로는 KoNLPy 등을 사용하여 더 정교하게 분석)
        
        return True


async def analyze_slang_meaning(word: str, context_examples: List[str]) -> str:
    """신조어 의미 분석 (AI 기반)
    
    Args:
        word: 신조어
        context_examples: 사용 예시 문맥
        
    Returns:
        신조어 의미
    """
    # TODO: OpenAI API를 사용한 의미 추론
    # 현재는 간단한 플레이스홀더
    
    if not settings.OPENAI_API_KEY:
        return "의미 분석 중..."
    
    # OpenAI API 호출 로직
    # ...
    
    return "의미 분석 결과"


