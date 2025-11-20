# NLP 모델 설정 가이드

Render에서 NLP 모델을 사용하려면 모델 파일을 외부 스토리지에 업로드하고 다운로드 URL을 설정해야 합니다.

## 1. 모델 파일 압축

로컬에서 모델 파일을 압축합니다:

```powershell
cd backend\training\output
Compress-Archive -Path "KR-ELECTRA-discriminator\*" -DestinationPath "..\..\..\model.zip" -Force
```

## 2. 모델 파일 업로드

다음 중 하나의 방법으로 모델 파일을 업로드하세요:

### 옵션 A: GitHub Releases (권장)

1. GitHub 저장소로 이동: https://github.com/idjun725/slang
2. "Releases" → "Create a new release" 클릭
3. Tag: `v1.0.0`, Title: `Model Release`
4. `model.zip` 파일을 드래그 앤 드롭
5. "Publish release" 클릭
6. 다운로드 URL: `https://github.com/idjun725/slang/releases/download/v1.0.0/model.zip`

### 옵션 B: Google Drive

1. Google Drive에 `model.zip` 업로드
2. 파일을 공개로 설정 (링크가 있는 모든 사용자)
3. 공유 링크에서 파일 ID 추출
4. 다운로드 URL: `https://drive.google.com/uc?export=download&id=FILE_ID`

### 옵션 C: 직접 호스팅

1. 웹 서버에 `model.zip` 업로드
2. 공개 URL 사용

## 3. Render 환경 변수 설정

Render 대시보드에서 다음 환경 변수를 추가하세요:

- **KEY**: `MODEL_DOWNLOAD_URL`
- **VALUE**: 모델 파일의 다운로드 URL (예: `https://github.com/idjun725/slang/releases/download/v1.0.0/model.zip`)

## 4. 재배포

환경 변수를 설정한 후 Render에서 서비스를 재배포하면 빌드 시 모델이 자동으로 다운로드됩니다.

## 확인

빌드 로그에서 다음 메시지를 확인하세요:

```
[모델 다운로드] 시작...
[모델 다운로드] 모델 다운로드 중...
[모델 다운로드] 압축 해제 중...
[모델 다운로드] 완료!
```

## 문제 해결

- 모델 다운로드 실패 시: `MODEL_DOWNLOAD_URL` 환경 변수가 올바르게 설정되었는지 확인
- 모델이 없어도 크롤러는 동작하지만 NLP 필터링은 비활성화됩니다

