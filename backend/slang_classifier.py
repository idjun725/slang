import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SlangClassifier:
    """신조어 분류를 위한 NLP 모델 래퍼"""
    
    def __init__(self, model_path: Optional[str] = None, device: Optional[str] = None):
        """
        Args:
            model_path: 학습된 모델 경로 (None이면 기본 모델 사용)
            device: 'cuda' 또는 'cpu' (None이면 자동 선택)
        """
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = device
        
        # 모델 경로 결정
        if model_path is None:
            # 기본 모델 경로 (KR-ELECTRA 우선 - 더 높은 정확도)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            default_path = os.path.join(current_dir, 'training', 'output', 'KR-ELECTRA-discriminator')
            if os.path.exists(default_path):
                model_path = default_path
            else:
                # KcELECTRA 시도 (대체 모델)
                alt_path = os.path.join(current_dir, 'training', 'output', 'KcELECTRA-base-v2022')
                if os.path.exists(alt_path):
                    model_path = alt_path
                else:
                    raise FileNotFoundError(
                        f"학습된 모델을 찾을 수 없습니다. "
                        f"다음 경로 중 하나에 모델이 있어야 합니다: {default_path}, {alt_path}"
                    )
        
        self.model_path = model_path
        logger.info(f"[NLP 분류기] 모델 로딩 중: {model_path}")
        
        # 토크나이저와 모델 로드
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
            self.model.to(self.device)
            self.model.eval()
            logger.info(f"[NLP 분류기] 모델 로드 완료 (device: {self.device})")
        except Exception as e:
            logger.error(f"[NLP 분류기] 모델 로드 실패: {e}")
            raise
    
    def predict(self, word: str, contexts: List[str] = None, threshold: float = 0.5) -> Dict[str, float]:
        """
        단어가 신조어인지 예측
        
        Args:
            word: 예측할 단어
            contexts: 단어가 등장한 맥락 텍스트 리스트
            threshold: 신조어로 판단할 확률 임계값 (기본 0.5)
        
        Returns:
            {
                'is_slang': bool,  # 신조어 여부
                'probability': float,  # 신조어일 확률 (0~1)
                'confidence': float  # 신뢰도 (확률이 0.5에서 얼마나 떨어져 있는지)
            }
        """
        # 입력 텍스트 구성
        if contexts and len(contexts) > 0:
            context_text = ' '.join(contexts[:3])  # 최대 3개 맥락만 사용
            text = f"단어: {word} / 설명: {word} / 예시: {context_text}"
        else:
            text = f"단어: {word}"
        
        # 토크나이징
        inputs = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=96,
            return_tensors='pt'
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # 예측
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)
            slang_prob = probs[0][1].item()  # label=1 (신조어) 확률
        
        is_slang = slang_prob >= threshold
        confidence = abs(slang_prob - 0.5) * 2  # 0~1 범위로 정규화
        
        return {
            'is_slang': is_slang,
            'probability': slang_prob,
            'confidence': confidence
        }
    
    def predict_batch(self, words_with_contexts: List[Dict[str, any]], threshold: float = 0.5) -> List[Dict[str, any]]:
        """
        여러 단어를 배치로 예측
        
        Args:
            words_with_contexts: [{'word': str, 'contexts': List[str]}, ...]
            threshold: 신조어 판단 임계값
        
        Returns:
            각 단어에 대한 예측 결과 리스트
        """
        results = []
        for item in words_with_contexts:
            word = item.get('word', '')
            contexts = item.get('contexts', [])
            pred = self.predict(word, contexts, threshold)
            results.append({
                'word': word,
                **pred
            })
        return results

