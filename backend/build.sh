#!/bin/bash
# Railway 빌드 스크립트 - torch 설치

set -e

echo "[빌드] 기본 패키지 설치 중..."
pip install -r requirements.txt

echo "[빌드] torch CPU 버전 설치 중..."
pip install torch --index-url https://download.pytorch.org/whl/cpu || pip install torch

echo "[빌드] transformers 설치 중..."
pip install transformers>=4.30.0

echo "[빌드] 완료!"

