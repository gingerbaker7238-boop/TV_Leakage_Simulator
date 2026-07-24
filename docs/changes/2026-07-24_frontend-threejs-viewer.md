# Frontend Three.js Viewer·선택 연동

## 목적

React Viewer의 component 카드 자리표시자를 실제 `mesh-scene.v1` 기반
Three.js 장면으로 교체하고 Step 07의 작업 상태를 3D 객체와 연결한다.

## Viewer

- component별 `BufferGeometry`와 CAD feature edge 생성
- Z-up 좌표계, OrbitControls, 자동 resize와 fit-to-view 구성
- `Fit`, `Iso`, `XY`, `-XY` 카메라 preset 연결
- `Wireframe`, `Surface`, `Surface + Edge` 렌더 모드 연결
- WebGL renderer의 pixel ratio 상한과 cleanup lifecycle 구성
- CAD를 불러올 때만 Three.js chunk를 받도록 lazy loading 적용

## 선택·상태 연동

- Viewer click의 triangle index를 원본 `face_id`로 복원
- face picking 결과를 component·face Zustand 선택 상태에 동기화
- Component Tree 선택을 Viewer surface·edge highlight에 반영
- Shift/Ctrl/Meta click으로 다중 선택 지원
- component 숨김·삭제 상태를 장면 가시성에 반영
- Part/Face material assignment를 Viewer 재질에 반영
- Component move·tilt와 Local face transform overlay를 Viewer에 반영

## 검증

- `npm run typecheck`
- `npm run lint`
- `npm test` — 8 files, 28 tests
- `npm run build`
- 실제 sample CAD Chrome E2E
  - 106,352 faces
  - 54,191 vertices
  - 4 components
  - component·face 양방향 선택 연동
  - 카메라·렌더 모드 전환
  - component 가시성
  - Material·Transform Viewer 반영
  - 새 탭 기준 console error 0건
