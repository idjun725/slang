"""
의미 추출 모듈 (GPT API + 여러 방법 조합)
여러 방법을 조합하여 신조어의 의미를 추론합니다.
"""
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from collections import Counter
import os

class MeaningExtractor:
    """신조어 의미 추출기 (GPT API + 여러 방법 조합)"""
    
    def __init__(self, openai_client=None):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'ko-KR,ko;q=0.9'
        }
        self.openai_client = openai_client
        
        # 패턴 기반 의미 매핑 (순서 중요: 긴 패턴 먼저)
        self.pattern_meanings = [
            (r'.*빨러$', lambda w: f"{w[:-2]}를 좋아하는 사람"),
            (r'.*러$', lambda w: f"{w[:-1]}를 좋아하는 사람"),
            (r'.*충$', lambda w: f"{w[:-1]}에 빠진 사람"),
            (r'.*족$', lambda w: f"{w[:-1]} 같은 성향을 가진 사람들"),
            (r'.*킹$', lambda w: f"{w[:-1]}의 최고봉"),
            (r'.*갓$', lambda w: f"{w[:-1]}의 신"),
            (r'.*빨$', lambda w: f"{w[:-1]}를 좋아하는 사람"),
            (r'.*하다$', lambda w: f"{w}는 의미"),
            (r'.*되다$', lambda w: f"{w}는 의미"),
        ]
    
    def extract_meaning_from_pattern(self, word: str) -> Optional[str]:
        """패턴 기반 의미 추출"""
        for pattern, meaning_func in self.pattern_meanings:
            if re.match(pattern, word):
                try:
                    meaning = meaning_func(word)
                    return meaning
                except Exception as e:
                    print(f"[의미추출] 패턴 매칭 오류 ({word}, {pattern}): {e}")
                    pass
        return None
    
    def extract_meaning_from_contexts(self, word: str, contexts: List[str]) -> Optional[str]:
        """컨텍스트에서 의미 추출 (키워드 분석)"""
        if not contexts:
            return None
        
        # 컨텍스트에서 공통 키워드 찾기
        all_words = []
        for context in contexts[:10]:  # 상위 10개만 분석
            words = re.findall(r'[가-힣]{2,6}', context)
            all_words.extend(words)
        
        # 빈도 높은 단어들 (의미와 관련된 단어 추출)
        word_counter = Counter(all_words)
        common_words = [w for w, count in word_counter.most_common(10) if w != word and len(w) >= 2]
        
        # 간단한 의미 추론
        if common_words:
            # 컨텍스트에서 "word는/은", "word가/이" 같은 패턴 찾기
            definition_patterns = [
                rf'{word}는\s+([^다\.]+)',
                rf'{word}은\s+([^다\.]+)',
                rf'{word}가\s+([^다\.]+)',
                rf'{word}이\s+([^다\.]+)',
                rf'{word}의\s+의미는\s+([^다\.]+)',
            ]
            
            for pattern in definition_patterns:
                for context in contexts:
                    match = re.search(pattern, context)
                    if match:
                        meaning_text = match.group(1).strip()
                        if len(meaning_text) > 5 and len(meaning_text) < 50:
                            return meaning_text
        
        return None
    
    def extract_meaning_from_naver_search(self, word: str) -> Optional[str]:
        """네이버 검색 결과에서 의미 추출"""
        try:
            url = f"https://search.naver.com/search.naver?where=nexearch&query={word}+의미"
            response = requests.get(url, headers=self.headers, timeout=5)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 검색 결과 요약문에서 의미 추출
            # 네이버 검색 결과의 구조에 따라 셀렉터 조정 필요
            summary_elements = soup.select('.api_subject_bx, .dsc_txt, .sh_web_top')
            
            for element in summary_elements[:3]:  # 상위 3개만 확인
                text = element.get_text(strip=True)
                if word in text and len(text) > 10:
                    # 의미 관련 문장 추출
                    sentences = re.split(r'[\.\!\?]', text)
                    for sentence in sentences:
                        if word in sentence and ('의미' in sentence or '설명' in sentence or '설명은' in sentence):
                            # 의미 부분만 추출
                            meaning_match = re.search(r'(?:의미|설명|설명은)[는은]?\s*:?\s*([^\.]+)', sentence)
                            if meaning_match:
                                meaning = meaning_match.group(1).strip()
                                if 5 < len(meaning) < 80:
                                    return meaning
            
            return None
        except Exception as e:
            print(f"[의미추출] 네이버 검색 실패 ({word}): {e}")
            return None
    
    def extract_meaning_from_examples(self, word: str, examples: List[str]) -> Optional[str]:
        """예문에서 공통 패턴 분석하여 의미 추론"""
        if not examples or len(examples) < 2:
            return None
        
        # 예문에서 공통된 구조나 맥락 찾기
        common_verbs = []
        common_objects = []
        
        for example in examples[:5]:
            # 동사 패턴 찾기
            verb_patterns = [
                rf'{word}\s+([가-힣]+다)',
                rf'([가-힣]+다)\s+{word}',
            ]
            
            for pattern in verb_patterns:
                match = re.search(pattern, example)
                if match:
                    verb = match.group(1)
                    if len(verb) > 1:
                        common_verbs.append(verb)
        
        if common_verbs:
            # 가장 많이 사용된 동사와 조합하여 의미 추론
            verb_counter = Counter(common_verbs)
            top_verb = verb_counter.most_common(1)[0][0]
            
            # 동사에서 의미 유추
            verb_to_meaning = {
                '하다': '행동',
                '되다': '상태',
                '이다': '사물',
                '있다': '존재',
            }
            
            if top_verb in verb_to_meaning:
                return f"{word}는 {verb_to_meaning[top_verb]}를 나타냄"
        
        return None
    
    def extract_meaning_with_gpt(self, word: str, contexts: List[str] = None, examples: List[str] = None) -> Optional[str]:
        """GPT를 사용한 의미 추출"""
        if not self.openai_client:
            return None
        
        try:
            # 컨텍스트와 예문 결합
            context_text = ''
            if contexts:
                context_text += ' '.join(contexts[:5])
            if examples:
                context_text += ' ' + ' '.join(examples[:3])
            
            prompt = f"""다음 한국어 신조어의 의미를 간단하고 명확하게 설명해주세요.

단어: {word}
사용 맥락: {context_text[:300] if context_text else '없음'}

답변 형식: "의미: [간단한 의미 설명]"만 출력하세요. 30자 이내로 간결하게 설명해주세요."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a Korean language expert. Answer concisely."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            result = response.choices[0].message.content.strip()
            if '의미:' in result:
                meaning = result.split('의미:')[1].strip()
            else:
                meaning = result
            
            if len(meaning) > 2:
                print(f"[의미추출] GPT: {word} -> {meaning}")
                return meaning
        except Exception as e:
            error_str = str(e)
            # Rate Limit 에러는 특별 처리하지 않고 그냥 실패로 처리
            # (호출하는 쪽에서 재시도 로직이 있을 수 있음)
            if '429' in error_str or 'rate_limit' in error_str.lower() or 'insufficient_quota' in error_str.lower():
                print(f"[의미추출] GPT Rate Limit ({word}): API 할당량 초과")
            else:
                print(f"[의미추출] GPT 실패 ({word}): {e}")
        
        return None
    
    def extract_meanings_batch(self, items: List[Dict]) -> Dict[str, str]:
        """여러 단어의 의미를 한번에 GPT로 요청하여 반환.
        items: [{"word": str, "contexts": [str], "examples": [str]}]
        returns: { word: meaning }
        """
        if not self.openai_client:
            return {}
        try:
            # 입력 축약 (토큰 절약) - 최소화
            compact = []
            for it in items:
                w = it.get("word", "").strip()
                if not w:
                    continue
                # 컨텍스트 최소화: 첫 번째 컨텍스트만, 최대 50자만 사용
                ctx_list = it.get("contexts") or []
                ctx_short = ctx_list[0][:50] if ctx_list else ""
                compact.append({"word": w, "ctx": ctx_short})
            if not compact:
                return {}
            import json
            user_prompt = (
                "다음 신조어들의 의미를 웹에서 검색한 결과를 바탕으로 한국어로 매우 간결하게 생성하세요. 각 항목은 30자 이내.\n"
                "입력은 JSON 배열이며, 각 객체는 {word, ctx}를 가집니다.\n"
                "반드시 다음 형식의 JSON으로만 답변하세요: {\\\"results\\\":[{\\\"word\\\":\\\"...\\\",\\\"meaning\\\":\\\"...\\\"}, ...]}"
            )
            messages = [
                {"role": "system", "content": "You are a Korean slang expert. Respond ONLY with valid JSON."},
                {"role": "user", "content": user_prompt},
                {"role": "user", "content": json.dumps(compact, ensure_ascii=False)}
            ]
            resp = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.2,
                max_tokens=200  # 토큰 절약
            )
            content = resp.choices[0].message.content.strip()
            # JSON 파싱 시도
            try:
                data = json.loads(content)
                results = data.get("results", [])
                out = {}
                for r in results:
                    w = r.get("word")
                    m = r.get("meaning")
                    if w and m:
                        out[w] = m
                return out
            except Exception:
                print("[의미추출] 배치 응답 JSON 파싱 실패")
                return {}
        except Exception as e:
            error_str = str(e)
            # Rate Limit 에러는 재시도 없이 즉시 실패 처리
            if '429' in error_str or 'rate_limit' in error_str.lower() or 'insufficient_quota' in error_str.lower():
                print(f"[의미추출] 배치 GPT Rate Limit: 재시도 없이 건너뜀")
            else:
                print(f"[의미추출] 배치 GPT 실패: {e}")
            return {}  # 재시도 없이 빈 결과 반환

    def extract_meaning(self, word: str, contexts: List[str] = None, examples: List[str] = None, use_gpt: bool = True) -> str:
        """의미 추출 메인 함수 (GPT만 사용)"""
        # GPT 기반 의미 추출만 사용
        if use_gpt and self.openai_client:
            gpt_meaning = self.extract_meaning_with_gpt(word, contexts, examples)
            if gpt_meaning:
                return gpt_meaning
        
        # GPT 실패 또는 비활성화 시 기본값 반환
        return f'{word}의 의미 (분석 중)'
