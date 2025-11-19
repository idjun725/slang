#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NLP 분류기 임계값 테스트 스크립트
여러 임계값을 테스트하여 최적의 값을 찾습니다.
"""
import os
import sys
import json
import argparse
from typing import List, Dict

# 환경변수 로드
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
from dotenv import load_dotenv
load_dotenv(env_path)

from slang_classifier import SlangClassifier

def load_test_words() -> tuple[List[str], List[str]]:
    """테스트용 신조어와 일반어 로드"""
    word_rules_path = os.path.join(current_dir, 'data', 'word_rules.json')
    
    with open(word_rules_path, 'r', encoding='utf-8') as f:
        word_rules = json.load(f)
    
    slang_words = word_rules.get('allow', [])
    general_words = word_rules.get('block', [])
    
    # 너무 긴 단어 제거 (실제 신조어는 보통 짧음)
    slang_words = [w for w in slang_words if 2 <= len(w) <= 8]
    general_words = [w for w in general_words if 2 <= len(w) <= 8]
    
    return slang_words[:30], general_words[:30]  # 각각 30개씩만 테스트

def evaluate_threshold(classifier: SlangClassifier, 
                      slang_words: List[str], 
                      general_words: List[str], 
                      threshold: float) -> Dict:
    """특정 임계값에 대한 성능 평가"""
    true_positives = 0  # 신조어를 신조어로 올바르게 분류
    false_positives = 0  # 일반어를 신조어로 잘못 분류
    false_negatives = 0  # 신조어를 일반어로 잘못 분류
    true_negatives = 0  # 일반어를 일반어로 올바르게 분류
    
    # 신조어 테스트
    for word in slang_words:
        result = classifier.predict(word, contexts=[], threshold=threshold)
        if result['is_slang']:
            true_positives += 1
        else:
            false_negatives += 1
    
    # 일반어 테스트
    for word in general_words:
        result = classifier.predict(word, contexts=[], threshold=threshold)
        if result['is_slang']:
            false_positives += 1
        else:
            true_negatives += 1
    
    # 메트릭 계산
    total = len(slang_words) + len(general_words)
    accuracy = (true_positives + true_negatives) / total if total > 0 else 0
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'threshold': threshold,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'true_positives': true_positives,
        'false_positives': false_positives,
        'false_negatives': false_negatives,
        'true_negatives': true_negatives,
        'slang_total': len(slang_words),
        'general_total': len(general_words)
    }

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="신조어 분류 임계값 테스트")
    parser.add_argument(
        "--threshold_start",
        type=float,
        default=0.40,
        help="테스트할 임계값 시작값",
    )
    parser.add_argument(
        "--threshold_end",
        type=float,
        default=0.45,
        help="테스트할 임계값 종료값",
    )
    parser.add_argument(
        "--threshold_step",
        type=float,
        default=0.01,
        help="임계값 증가 간격",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    print("=" * 80)
    print("NLP 분류기 임계값 테스트")
    print("=" * 80)
    
    # 모델 로드
    print("\n[1/3] 모델 로딩 중...")
    try:
        classifier = SlangClassifier()
        print("[OK] 모델 로드 완료")
    except Exception as e:
        print(f"[ERROR] 모델 로드 실패: {e}")
        return
    
    # 테스트 단어 로드
    print("\n[2/3] 테스트 단어 로드 중...")
    slang_words, general_words = load_test_words()
    print(f"[OK] 신조어 {len(slang_words)}개, 일반어 {len(general_words)}개 로드")
    print(f"  신조어 예시: {', '.join(slang_words[:5])}...")
    print(f"  일반어 예시: {', '.join(general_words[:5])}...")
    
    # 여러 임계값 테스트
    print("\n[3/3] 임계값 테스트 중...")
    thresholds = []
    current = args.threshold_start
    # 부동소수 오차 방지를 위해 약간 여유를 둠
    while current <= args.threshold_end + 1e-9:
        thresholds.append(round(current, 4))
        current += args.threshold_step
    results = []
    
    for threshold in thresholds:
        print(f"\n  임계값 {threshold:.2f} 테스트 중...", end='', flush=True)
        result = evaluate_threshold(classifier, slang_words, general_words, threshold)
        results.append(result)
        print(f" 완료 (정확도: {result['accuracy']:.2%})")
    
    # 결과 출력
    print("\n" + "=" * 80)
    print("테스트 결과 요약")
    print("=" * 80)
    print(f"{'임계값':<8} {'정확도':<10} {'정밀도':<10} {'재현율':<10} {'F1점수':<10} {'TP':<6} {'FP':<6} {'FN':<6} {'TN':<6}")
    print("-" * 80)
    
    for result in results:
        print(f"{result['threshold']:<8.2f} "
              f"{result['accuracy']:<10.2%} "
              f"{result['precision']:<10.2%} "
              f"{result['recall']:<10.2%} "
              f"{result['f1_score']:<10.2%} "
              f"{result['true_positives']:<6} "
              f"{result['false_positives']:<6} "
              f"{result['false_negatives']:<6} "
              f"{result['true_negatives']:<6}")
    
    # 최적 임계값 찾기 (F1 점수가 가장 높은 값)
    best_result = max(results, key=lambda x: x['f1_score'])
    print("\n" + "=" * 80)
    print(f"최적 임계값: {best_result['threshold']:.2f}")
    print(f"  정확도: {best_result['accuracy']:.2%}")
    print(f"  정밀도: {best_result['precision']:.2%}")
    print(f"  재현율: {best_result['recall']:.2%}")
    print(f"  F1 점수: {best_result['f1_score']:.2%}")
    print("=" * 80)
    
    # 추천 임계값 (일반어 필터링을 강화하기 위해 정밀도가 높은 값)
    # 정밀도가 높으면 일반어를 잘못 신조어로 분류하는 경우가 적음
    high_precision_results = [r for r in results if r['precision'] >= 0.7]
    if high_precision_results:
        recommended = max(high_precision_results, key=lambda x: x['f1_score'])
        print(f"\n추천 임계값 (정밀도 우선): {recommended['threshold']:.2f}")
        print(f"  정확도: {recommended['accuracy']:.2%}")
        print(f"  정밀도: {recommended['precision']:.2%}")
        print(f"  재현율: {recommended['recall']:.2%}")
        print(f"  F1 점수: {recommended['f1_score']:.2%}")
        print("=" * 80)

if __name__ == '__main__':
    main()

