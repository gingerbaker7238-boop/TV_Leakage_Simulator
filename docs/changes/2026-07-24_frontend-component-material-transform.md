# Frontend Component Tree·Material·Transform 이전

## 목적

임시 Component preview를 제거하고 실제 `mesh-scene.v1`의 component
metadata를 React 기능 화면과 작업 상태에 연결한다.

## Component Tree

- Model import를 CAD upload mutation과 scene query에 연결
- `ScenePayload.components` 기반 component 목록·검색·선택
- 숨김, Traceability, 삭제 상태를 Zustand action으로 통합
- 더블클릭 또는 `F2` 이름 변경과 화면 간 이름 동기화
- Tree와 Viewer state bridge가 같은 선택·상태를 사용
- Material·Transform·삭제 action을 공통 Context Menu와 직접 버튼에서 제공

## Material

- legacy의 base material 6개, surface property 10개, profile 3개 이전
- Part assignment와 Face override target 모델 구성
- base reflectance와 surface scale·ratio를 합친 optical preview 제공
- assignment 생성·수정·제거 및 Material 관리 패널 연결
- component 삭제 시 연결 assignment 자동 정리

## Transform

- Component move와 Local face move target 모델 구성
- Click·Box selection method와 Move X/Y/Z, Tilt Rx/Ry/Rz 입력
- rule 생성·수정·활성/비활성·제거 및 Transform 관리 패널 연결
- component 삭제 시 연결 rule 자동 정리

## 상태 경계

- CAD scene mesh와 component 원본은 TanStack Query cache가 소유
- 선택·숨김·해석 제외·이름·assignment·rule은 Zustand가 소유
- Face override와 Local face move는 face 선택 상태를 사용하며, 실제
  Viewer picking은 Step 08에서 연결
- Material과 Transform 상태의 실제 ray trace payload 연결은 실행 기능
  이전 단계에서 진행

## 검증

- `npm run typecheck`
- `npm run lint`
- `npm test` — 7 files, 25 tests
- `npm run build`
- `npm audit --audit-level=high`
- 실제 sample CAD `/api/scene`
  - `mesh-scene.v1`
  - 106,352 faces
  - 54,191 vertices
  - 4 components
  - synthetic `false`
- Chrome 1920px 화면에서 Components·Material·Transform 패널 전환
- horizontal overflow와 console warning/error 없음
