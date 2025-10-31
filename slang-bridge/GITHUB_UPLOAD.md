# GitHub 업로드 가이드

## 저장소 생성 후 다음 명령어 실행:

```bash
# 원격 저장소 추가 (YOUR_USERNAME과 YOUR_REPO_NAME을 실제 값으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# 기본 브랜치를 main으로 변경 (선택사항)
git branch -M main

# 코드 푸시
git push -u origin main
```

## 또는 SSH 사용 시:
```bash
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

## 이후 업데이트 방법:
```bash
git add .
git commit -m "커밋 메시지"
git push
```

