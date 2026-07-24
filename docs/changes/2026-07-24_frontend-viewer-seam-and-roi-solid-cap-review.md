# Frontend Viewer 접합선 수정·ROI solid cap 사전 검토

## Viewer 접합선 증상

경사진 면과 인접 면이 하나의 모서리에서 만나지 않고 surface가 feature
edge보다 안쪽이나 아래쪽에 형성된 것처럼 보였다.

## 원인과 수정

- CAD vertex와 component bbox의 접합 높이는 정상이다.
- z-fighting 방지를 위한 `polygonOffsetFactor`가 polygon slope에 비례해
  서로 다른 depth를 더하면서 hard edge에 시각적 틈을 만들었다.
- slope factor는 `0`으로 제거하고 component별 고정 `polygonOffsetUnits`만
  사용한다.
- 고정 units는 실제 geometry 위치를 바꾸지 않으며, 겹친 component의
  depth 우선순위만 결정한다.
- 샘플 CAD의 `z=30~33 mm`에는 LCD가 있는 영역과 실제 내부 공간이
  공존한다. 이 실제 component 측면·공간은 렌더러에서 임의로 메우지 않는다.

## ROI section cap 이식 요구사항

React ROI Viewer에서 Three.js clipping plane만 적용하면 triangle 외피만
잘리고 절단면이 비어 보인다. Step 09에서는 기존 `run_web.py`의
`buildRoiClippedGeometries` 흐름을 분리·이식한다.

1. ROI box의 각 평면으로 triangle을 실제 clipping한다.
2. 절단 평면 위의 boundary segment를 component별로 수집하고 tolerance
   기반으로 endpoint와 T-junction을 정리한다.
3. segment를 폐곡선으로 연결하고 hole을 보존해 triangulation한다.
4. clipped surface와 동일한 좌표로 section cap과 cap 외곽선을 생성한다.
5. 원본 CAD feature edge와 cap 외곽선만 표시하고 cap 내부 삼각분할선은
   표시하지 않는다.
6. `openChainCount`가 0이 아니면 빈 단면을 그대로 표시하지 않고 오류
   상태로 처리한다.
7. component transform이 있으면 동일한 좌표계에서 surface와 cap을
   생성한다.
8. cap은 렌더링 geometry이며 원본 CAD와 ray tracing 충돌 mesh는
   변경하지 않는다.

## Step 09 완료 조건

- 좌·우 하단 50,944-face 샘플과 전체 조립체 샘플에서 section cap 생성
- 모든 검증 ROI에서 `openChainCount = 0`
- Surface·Surface + Edge·Wireframe에서 빈 껍데기나 내부 mesh 격자 없음
- 다중 ROI와 component transform 상태에서도 cap 경계와 surface가 일치
- component·face picking 및 ROI 계산 데이터 회귀 없음

기존 UI의 기준 검증에서는 전체 TV ROI가 cap loop 11개, 좌측 하단
50,944-face 샘플이 cap loop 13개였고 두 경우 모두 open chain이 0개였다.
React 이식에서도 이 결과를 최소 회귀 기준으로 사용한다.

## Viewer 검증

- `npm run typecheck`
- `npm run lint`
- `npm test` — 8 files, 28 tests
- `npm run build`
- `npm audit --audit-level=high` — 취약점 0건
- Chrome에서 우측 하단 문제 STEP(50,944 faces, 4 components) 재검증
  - 확대·경사 Surface에서 면과 실루엣 접합선 일치
  - Surface 중첩면 패턴 재발 없음
  - Wireframe 정지 8프레임의 최대 채널 변화 3/255
  - console error·warning 없음
