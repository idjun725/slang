#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
크롤링 직접 실행 스크립트
"""
import sys
import os
from dotenv import load_dotenv

# 환경변수 로드 (루트 디렉토리와 backend 디렉토리에서 .env 파일 찾기)
root_dir = os.path.dirname(os.path.abspath(__file__))
env_paths = [
    os.path.join(root_dir, '.env'),              # 루트 디렉토리
    os.path.join(root_dir, 'backend', '.env')     # backend 디렉토리
]

loaded = False
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"[ENV] 환경변수 로드: {env_path}")
        loaded = True
        break

if not loaded:
    load_dotenv()  # 기본 경로에서도 시도
    print(f"[ENV] 기본 경로에서 환경변수 로드 시도")

# backend 디렉토리를 Python 경로에 추가
backend_dir = os.path.join(root_dir, 'backend')
sys.path.insert(0, backend_dir)

from crawler import Crawler
from database import Database

def main():
    print("="*80)
    print("크롤링 시작...")
    print("="*80)
    
    try:
        # 크롤러 실행
        crawler = Crawler()
        result = crawler.crawl_and_analyze()
        
        print(f"\n크롤링 완료! {len(result)}개 신조어 발견")
        
        if len(result) == 0:
            print("\n[WARNING] 수집된 신조어가 없습니다.")
            return
        
        # 데이터베이스에 저장
        db = Database()
        added_count = 0
        
        # 필터링 결과만 사용
        enhanced_results = [s for s in result if s.get('method') == 'enhanced']
        
        print("\n데이터베이스에 저장 중...")
        
        # 필터링 신조어 저장 및 출력
        if enhanced_results:
            print("\n[필터링 신조어]")
            for slang_data in enhanced_results:
                word = slang_data['word']
                meaning = slang_data.get('meaning', '')
                examples = slang_data.get('examples', [])
                # count 필드 확인 및 디버깅
                count = slang_data.get('count')
                if count is None:
                    print(f"  [WARNING] '{word}'에 count 필드가 없습니다! 딕셔너리 키: {list(slang_data.keys())}")
                    count = 1
                method = slang_data.get('method', 'enhanced')
                gpt_prob = slang_data.get('gpt_probability')
                gpt_meaning_success = slang_data.get('gpt_meaning_success')
                
                print(f"  [DEBUG] '{word}' 저장 시도: count={count}, method={method}")
                if db.add_slang(word, meaning, examples, usage_count=count, method=method):
                    added_count += 1
                    prob_str = f" (GPT 확률: {gpt_prob:.2f})" if gpt_prob else ""
                    # GPT 의미 분석 성공 여부 표시
                    meaning_status = ""
                    if gpt_meaning_success is True:
                        meaning_status = " [GPT 의미 분석 성공]"
                    elif gpt_meaning_success is False:
                        # 의미가 분석되지 않은 경우만 표시
                        if meaning == f'{word}의 의미 (분석 중)':
                            meaning_status = " [의미 미확인]"
                        # 그 외의 경우는 의미가 추출된 것이므로 표시하지 않음
                    print(f"  [ENHANCED] {word} - {meaning} ({count} uses){prob_str}{meaning_status}")
                else:
                    print(f"  [ERROR] '{word}' 저장 실패!")
        
        print(f"\n총 {added_count}개 신조어가 데이터베이스에 저장되었습니다.")
        if enhanced_results:
            print(f"  - 필터링: {len(enhanced_results)}개")
        print("="*80)
        
    except Exception as e:
        print(f"\n[ERROR] 크롤링 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

