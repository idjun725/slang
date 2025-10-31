import requests
from bs4 import BeautifulSoup
import re
from collections import Counter
from typing import List, Dict, Set
import time

class Crawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # RSS 피드 URL들
        self.rss_feeds = [
            "https://rss.cnn.com/rss/edition.rss",
            "https://feeds.bbci.co.uk/news/rss.xml",
            "https://rss.donga.com/total.xml",
            "https://rss.joins.com/joins_news_list.xml",
            "https://rss.hankookilbo.com/headline.xml"
        ]
        
        # 신조어 패턴들
        self.slang_patterns = [
            r'[가-힣]{2,4}(?:하다|되다|이다|네요|어요|아요)',
            r'[가-힣]{2,6}(?:킹|갓|신|왕|마스터)',
            r'[가-힣]{2,4}(?:충|족|러|러들)',
            r'[가-힣]{2,4}(?:빨|빨러|빨러들)',
            r'[가-힣]{2,4}(?:좌|우|파|파들)',
            r'[가-힣]{2,4}(?:남|녀|자|자들)',
            r'[가-힣]{2,4}(?:러|러들|러들들)',
            r'[가-힣]{2,4}(?:빠|빠들|빠들들)',
            r'[가-힣]{2,4}(?:충|충들|충들들)',
            r'[가-힣]{2,4}(?:족|족들|족들들)',
        ]
        
        # 일반적인 단어들 (필터링용)
        self.common_words = {
            '사람', '시간', '문제', '경우', '생각', '이야기', '이유', '방법', '결과',
            '상황', '기회', '가능', '중요', '필요', '이상', '이하', '이전', '이후',
            '위치', '상태', '조건', '내용', '형태', '성격', '특징', '목적', '의미'
        }
    
    def crawl_rss_feeds(self) -> List[Dict]:
        """RSS 피드에서 뉴스 제목 수집"""
        all_articles = []
        
        # 간단한 RSS 피드들로 변경
        simple_feeds = [
            "https://rss.cnn.com/rss/edition.rss",
            "https://feeds.bbci.co.uk/news/rss.xml"
        ]
        
        for feed_url in simple_feeds:
            try:
                print(f"RSS 피드 수집 중: {feed_url}")
                feed = feedparser.parse(feed_url)
                
                if not hasattr(feed, 'entries') or not feed.entries:
                    print(f"[WARNING] {feed_url}에서 기사를 찾을 수 없습니다")
                    continue
                
                for entry in feed.entries[:5]:  # 최대 5개씩
                    title = entry.get('title', '')
                    if title and len(title) > 10:  # 너무 짧은 제목 제외
                        all_articles.append({
                            'title': title,
                            'source': feed_url,
                            'published': entry.get('published', ''),
                            'link': entry.get('link', '')
                        })
                
                print(f"[OK] {len(feed.entries)}개 기사 수집")
                time.sleep(2)  # 요청 간격 증가
                
            except Exception as e:
                print(f"[ERROR] RSS 피드 수집 실패 ({feed_url}): {e}")
                # RSS 실패해도 계속 진행
                continue
        
        return all_articles
    
    def crawl_dcinside(self) -> List[Dict]:
        """디시인사이드 갤러리 크롤링"""
        base_url = "https://gall.dcinside.com"
        galleries = [
            "programming", "comic_new1", "baseball_new10",
            "hit", "stock",
            "entertain", "leagueoflegends", "overwatch"
        ]
        all_posts = []
        
        for gallery in galleries:
            try:
                url = f"{base_url}/board/lists/?id={gallery}"
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                titles = soup.find_all('td', class_='gall_tit')
                
                for title_elem in titles:
                    link = title_elem.find('a')
                    if link and link.text.strip():
                        all_posts.append({
                            'title': link.text.strip(),
                            'source': f"DCInside {gallery}",
                            'link': base_url + link.get('href', '')
                        })
                
                print(f"[OK] {gallery} 갤러리에서 {len(titles)}개 제목 수집")
                time.sleep(1)
                
            except Exception as e:
                print(f"[ERROR] {gallery} 갤러리 크롤링 실패: {e}")
        
        return all_posts
    
    def extract_keywords_with_patterns(self, texts: List[str]) -> Counter:
        """패턴 기반 키워드 추출"""
        all_keywords = []
        
        for text in texts:
            # 정규표현식으로 신조어 패턴 추출
            for pattern in self.slang_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if len(match) >= 2 and len(match) <= 8:
                        all_keywords.append(match)
        
        return Counter(all_keywords)
    
    def filter_slang_candidates(self, word_counts: Counter) -> Dict[str, int]:
        """신조어 후보 필터링"""
        slang_candidates = {}
        
        for word, count in word_counts.items():
            # 길이 체크
            if len(word) < 2 or len(word) > 8:
                continue
            
            # 일반적인 단어 필터링
            if word in self.common_words:
                continue
            
            # 패턴 매칭
            is_slang = False
            for pattern in self.slang_patterns:
                if re.search(pattern, word):
                    is_slang = True
                    break
            
            # 특수 문자나 숫자 포함 체크
            if re.search(r'[^가-힣]', word):
                continue
            
            # 빈도 체크 (최소 2회 이상)
            if count >= 2 and is_slang:
                slang_candidates[word] = count
        
        return slang_candidates
    
    def analyze_slang_meaning(self, word: str, contexts: List[str]) -> str:
        """신조어의 의미 분석"""
        
        # 패턴 기반 의미 추론
        if word.endswith('남'):
            return f'{word[:-1]}에 관련된 남성'
        elif word.endswith('녀'):
            return f'{word[:-1]}에 관련된 여성'
        elif word.endswith('충'):
            return f'{word[:-1]}에 열광하는 사람'
        elif word.endswith('족'):
            return f'{word[:-1]} 그룹의 구성원'
        elif word.endswith('러'):
            return f'{word[:-1]}를 좋아하는 사람'
        elif word.endswith('빨러'):
            return f'{word[:-2]}를 빠는 사람'
        elif word.endswith('파'):
            return f'{word[:-1]}를 지지하는 사람'
        elif word.endswith('킹') or word.endswith('갓'):
            return f'{word[:-1]}의 최고봉'
        elif word.endswith('하다'):
            return f'{word[:-2]}하는 행동'
        elif word.endswith('되다'):
            return f'{word[:-2]}되는 상태'
        elif word.endswith('이다'):
            return f'{word[:-2]}인 상태'
        
        # 맥락 기반 추론
        if contexts:
            context_text = ' '.join(contexts[:2])
            if '좋아' in context_text or '사랑' in context_text:
                return f'{word}를 좋아하는 표현'
            elif '싫어' in context_text or '혐오' in context_text:
                return f'{word}를 싫어하는 표현'
            elif '화나' in context_text or '짜증' in context_text:
                return f'{word}에 대한 화남 표현'
            elif '웃음' in context_text or '재미' in context_text:
                return f'{word}에 대한 재미있는 표현'
        
        # 기본값
        return f'{word}의 의미 (분석 중)'
    
    def calculate_slang_score(self, word: str, count: int, contexts: List[str]) -> float:
        score = 0.0
        
        # 기본 빈도 점수
        score += min(count * 0.1, 5.0)
        
        # 길이 점수 (3-5자가 최적)
        if 3 <= len(word) <= 5:
            score += 2.0
        elif len(word) == 2 or len(word) == 6:
            score += 1.0
        
        # 패턴 매칭 점수
        for pattern in self.slang_patterns:
            if re.search(pattern, word):
                score += 1.5
                break
        
        # 맥락 다양성 점수
        unique_contexts = len(set(contexts))
        score += min(unique_contexts * 0.3, 2.0)
        
        return score
    
    def crawl_and_analyze(self) -> List[Dict]:
        """고급 크롤링 및 분석 실행 (디시인사이드 전용)"""
        print("고급 크롤링 시작...")
        
        try:
            # 디시인사이드 크롤링만 실행
            print("디시인사이드 크롤링 중...")
            dc_posts = self.crawl_dcinside()
            print(f"디시인사이드에서 {len(dc_posts)}개 게시물 수집")
            
            if not dc_posts:
                print("[WARNING] 수집된 게시물이 없습니다. 기본 크롤링을 사용하세요.")
                return []
            
            # 모든 텍스트 수집
            all_texts = [post['title'] for post in dc_posts]
            
            # 패턴 기반 키워드 추출
            print("패턴 분석 중...")
            keyword_counts = self.extract_keywords_with_patterns(all_texts)
            
            # 신조어 후보 필터링
            slang_candidates = self.filter_slang_candidates(keyword_counts)
            
            # 점수 계산 및 정렬
            scored_slangs = []
            for word, count in slang_candidates.items():
                contexts = [text for text in all_texts if word in text]
                score = self.calculate_slang_score(word, count, contexts)
                meaning = self.analyze_slang_meaning(word, contexts)
                
                scored_slangs.append({
                    'word': word,
                    'count': count,
                    'score': score,
                    'contexts': contexts[:3],  # 최대 3개 맥락
                    'meaning': meaning,  # 실제 의미 분석
                    'examples': contexts[:2]  # 예시
                })
            
            # 점수순 정렬
            scored_slangs.sort(key=lambda x: x['score'], reverse=True)
            
            print(f"총 {len(scored_slangs)}개 신조어 후보 발견")
            return scored_slangs[:20]  # 상위 20개만 반환
            
        except Exception as e:
            print(f"[ERROR] 고급 크롤링 실패: {e}")
            return []
