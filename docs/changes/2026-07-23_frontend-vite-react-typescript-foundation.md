# Frontend Vite + React + TypeScript 기반 생성

## 목적

기존 `run_web.py` 인라인 UI를 단계적으로 이전할 수 있도록 독립적인
프론트엔드 빌드 작업 공간을 만든다.

## 적용 내용

- `frontend/` 디렉터리 생성
- Vite + React + TypeScript 기본 구성
- Oxlint 및 TypeScript 빌드 검사 구성
- npm 잠금 파일 생성
- 프로젝트용 최소 진입 화면과 실행 안내 추가
- `node_modules/`와 `dist/`를 Git 추적에서 제외

## 이번 단계에서 제외한 내용

- 기존 Python UI 및 API 연결
- Tailwind CSS와 shadcn/ui
- Zustand와 TanStack Query
- Three.js Viewer 이전
- WebView2 패키징 연결

## 검증

- `npm run typecheck`
- `npm run lint`
- `npm run build`
- `npm audit --audit-level=high`
