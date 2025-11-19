"""크롤러를 한 번 실행해서 결과를 확인하는 스크립트"""
import os
import json

# 환경변수 기본값 설정
os.environ.setdefault("USE_NLP_FILTER", "true")
os.environ.setdefault("GPT_USE_ENABLED", "false")  # GPT 비활성화

from crawler import Crawler


def main():
    print("[RUN] 크롤러 실행 시작 (NLP 필터 활성화)")
    crawler = Crawler()
    results = crawler.crawl_and_analyze(use_enhanced_filter=True)
    print(f"[DONE] 총 {len(results)}개 결과")

    # 상위 10개만 출력
    for item in results[:10]:
        print("-" * 60)
        print(f"단어: {item.get('word')}")
        print(f"카운트: {item.get('count')}, 점수: {item.get('score')}")
        print(f"NLP 확률: {item.get('nlp_probability')}")
        print(f"예문: {item.get('examples')}")

    # 결과를 파일로 저장
    output_path = os.path.join("backend", "data", "latest_crawl_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[SAVE] 결과가 {output_path}에 저장되었습니다.")


if __name__ == "__main__":
    main()

