# Three.js Picking / STEP Solid Transform 보정

## 배경
- 사용자가 STEP 도면 로드 후 `부품 전체 이동`을 선택해도 일부 면만 움직이는 것처럼 보이는 문제를 재현했다.
- 3D viewer에서 도면을 클릭했을 때 클릭한 면이 속한 부품 전체가 직관적으로 하이라이트되어야 한다.
- 마우스 조작 시 일반 CAD처럼 회전/팬/롤 조작이 더 명확해야 한다.

## 원인
- STEP import 결과를 component로 나눌 때 STEP solid/body 경계를 우선 사용하지 않아, 실제 부품 단위가 아니라 면 연결성 기준으로 그룹이 만들어질 수 있었다.
- Three.js viewer의 클릭 picking 결과가 기존 canvas selection 경로와 완전히 연결되지 않아, 3D viewer에서 클릭한 face가 component highlight까지 안정적으로 이어지지 않았다.
- viewer 안내 문구가 모드 변경 때마다 예전 조작 설명으로 덮어써져 실제 조작법과 맞지 않았다.

## 변경 사항
- `src/leakage_simulator/importers.py`
  - OCP STEP import 시 `TopAbs_SOLID`를 우선 순회하고, 각 tessellated face에 `step_component_id`, `step_component_name` metadata를 부여했다.
  - 전역 vertex dedupe를 추가해 solid별 face가 같은 좌표계를 공유하도록 정리했다.
- `src/leakage_simulator/components.py`
  - `step_component_id` metadata가 있으면 이를 최우선 component grouping 기준으로 사용한다.
  - 기본 `max_faces_per_object`를 `None`으로 변경해 component transform용 `face_indices`가 잘리지 않도록 했다.
- `run_web.py`
  - Web UI 버전을 `v0.7.13`으로 갱신했다.
  - Three.js raycaster picking을 추가해 3D viewer에서 클릭한 face의 source face id를 추적한다.
  - picking 결과를 기존 ROI/local face/component selection 경로와 통합했다.
  - `component_move_gap` 상태에서는 클릭한 face가 속한 component 전체를 선택/하이라이트한다.
  - `Shift/Alt + drag` roll, `Middle drag` rotate, `Right drag` pan 안내를 모드별 문구에 반영했다.

## 검증
- `MODULE_3_Z27_HELICAL_GEAR_SAG.stp`
  - synthetic: `False`
  - faces: `9486`
  - vertices: `4731`
  - objects/components: `1`
- `samples/tv_leakage_full_assembled_no_gap.stp`
  - synthetic: `False`
  - faces: `116`
  - vertices: `64`
  - objects/components: `4`
- `samples/tv_leakage_roi_left_bottom_no_gap.stp`
  - synthetic: `False`
  - faces: `88`
  - vertices: `51`
  - objects/components: `4`

## 사용자 확인 포인트
- 서버 재시작 후 브라우저를 새로고침한다.
- 3D viewer에서 기어 STEP을 클릭하면 component 1개 전체가 하이라이트되어야 한다.
- Transform popup에서 move/tilt 값을 입력하면 전체 기어가 preview되고, Apply 후 원본 일부 face만 남지 않아야 한다.
- 일반 회전은 drag/middle drag, 화면 roll은 `Shift` 또는 `Alt`를 누른 채 drag로 확인한다.
