#!/bin/bash
# Render 빌드 시 NLP 모델 다운로드 스크립트

set -e

MODEL_DIR="backend/training/output"
MODEL_NAME="KR-ELECTRA-discriminator"

# 환경 변수에서 다운로드 URL 가져오기 (없으면 기본값 사용)
MODEL_URL="${MODEL_DOWNLOAD_URL}"

# 모델 URL이 설정되지 않았으면 스킵
if [ -z "${MODEL_URL}" ]; then
    echo "[모델 다운로드] MODEL_DOWNLOAD_URL 환경 변수가 설정되지 않았습니다."
    echo "[모델 다운로드] 모델 다운로드를 스킵합니다. NLP 필터링이 비활성화됩니다."
    exit 0
fi

echo "[모델 다운로드] 시작..."
echo "[모델 다운로드] URL: ${MODEL_URL}"

# 모델 디렉토리 생성
mkdir -p "${MODEL_DIR}"

# 모델이 이미 있는지 확인
if [ -d "${MODEL_DIR}/${MODEL_NAME}" ] && [ -f "${MODEL_DIR}/${MODEL_NAME}/model.safetensors" ]; then
    echo "[모델 다운로드] 모델이 이미 존재합니다. 스킵합니다."
    exit 0
fi

# 모델 다운로드
echo "[모델 다운로드] 모델 다운로드 중..."
cd "${MODEL_DIR}"

# wget 또는 curl 사용
if command -v wget &> /dev/null; then
    wget -q --show-progress "${MODEL_URL}" -O model.zip || {
        echo "[오류] 모델 다운로드 실패"
        exit 1
    }
elif command -v curl &> /dev/null; then
    curl -L --progress-bar "${MODEL_URL}" -o model.zip || {
        echo "[오류] 모델 다운로드 실패"
        exit 1
    }
else
    echo "[오류] wget 또는 curl이 필요합니다."
    exit 1
fi

# 압축 해제
echo "[모델 다운로드] 압축 해제 중..."
if command -v unzip &> /dev/null; then
    unzip -q model.zip -d . || {
        echo "[오류] 압축 해제 실패"
        exit 1
    }
elif command -v tar &> /dev/null; then
    tar -xzf model.zip || {
        echo "[오류] 압축 해제 실패"
        exit 1
    }
else
    echo "[오류] unzip 또는 tar가 필요합니다."
    exit 1
fi

# 임시 파일 삭제
rm -f model.zip

echo "[모델 다운로드] 완료!"

