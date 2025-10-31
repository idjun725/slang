# 기여 가이드

슬랭 브릿지 프로젝트에 기여해주셔서 감사합니다! 🎉

## 시작하기

1. 저장소 Fork
2. 로컬에 클론
3. 새 브랜치 생성: `git checkout -b feature/amazing-feature`
4. 변경사항 커밋: `git commit -m '기능 추가: 멋진 기능'`
5. 브랜치에 푸시: `git push origin feature/amazing-feature`
6. Pull Request 생성

## 코드 스타일

### Python (Backend)
- Black 포맷터 사용
- isort로 import 정렬
- Type hints 사용 권장
- Docstring은 Google 스타일

```bash
black app/
isort app/
flake8 app/
```

### TypeScript (Frontend)
- ESLint 규칙 준수
- Prettier로 포맷팅
- 함수형 컴포넌트 사용

```bash
npm run lint
npm run format
```

## 커밋 메시지

다음 형식을 따라주세요:

```
<타입>: <제목>

<본문>

<푸터>
```

타입:
- `feat`: 새 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 포맷팅
- `refactor`: 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드/설정 변경

예시:
```
feat: 신조어 검색 자동완성 기능 추가

사용자가 신조어를 검색할 때 자동완성 제안을 표시합니다.

Closes #123
```

## 테스트

변경사항에 대한 테스트를 작성해주세요.

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## Pull Request

- 명확한 제목과 설명 작성
- 관련 이슈 번호 포함
- 스크린샷 첨부 (UI 변경 시)
- 모든 테스트 통과 확인

## 질문이나 제안

이슈를 생성하거나 이메일로 문의해주세요: contact@slangbridge.com

감사합니다!


