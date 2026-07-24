# Frontend Viewer 면·Wireframe 깊이 안정화

## 증상

- CAD를 불러온 뒤 Surface에서 일부 평면에 불규칙한 밝고 어두운 패턴이 나타났다.
- Wireframe은 면이 완전히 사라졌고 일부 모서리가 전환 후 깜빡였다.

## 원인

- STEP 조립체의 여러 component가 같은 평면을 서로 다른 삼각분할로
  중복 소유해 depth buffer에서 `z-fighting`이 발생했다.
- feature edge가 surface와 같은 깊이에 있으면서 depth buffer에도 기록되어
  모서리 표시 순서가 프레임별로 불안정해질 수 있었다.

## 수정

- component 순서에 따른 고정 polygon offset을 surface에 적용했다.
- Wireframe 보조 면의 불투명도를 65%로 조정하고 depth 기록을 유지한다.
- feature edge는 depth test를 유지하되 depth buffer에는 기록하지 않고,
  surface 뒤에 그려지지 않도록 render order를 고정했다.
- Wireframe에서는 바닥 격자를 숨기고, 다른 렌더 모드에서도 격자를 모델
  최저면에서 분리해 아래쪽 시점이나 바닥 면에 모눈이 겹치지 않게 했다.
- Wireframe feature edge는 불투명하게 그려 alpha blending에 의한
  미세한 밝기 변화를 줄였다.

## 영향 범위

렌더링 표현만 변경한다. CAD 좌표, component·face ID, picking, ROI 및
해석 데이터에는 영향을 주지 않는다.

## 검증

- `npm run typecheck`
- `npm run lint`
- `npm test` — 8 files, 28 tests
- `npm run build`
- `npm audit --audit-level=high` — 취약점 0건
- Chrome에서 문제 STEP(50,944 faces, 4 components) 재검증
  - Surface 중첩면 패턴 제거
  - Wireframe 65% 불투명 면과 안정된 feature edge 표시
  - 모델 내부 및 바닥 면의 격자 비침 제거
  - 정지 후 연속 8프레임 변화가 최대 4/255, 화면의 0.07% 이하
  - 가시적 점멸 및 console error·warning 없음
