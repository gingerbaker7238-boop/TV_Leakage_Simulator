# ROI 선택 규칙 확장 계획 (V1: 박스 드래그 우선, 좌표 지정 보완)

## 상태
코드 구현 완료 (로컬 전용). Python 백엔드(`types.py`/`roi.py`) 단위 테스트 9/9 통과, `run_web.py` UI 배선 완료. 아직 브라우저 클릭 테스트(실제 드래그 동작 확인)는 안 함 - 팀 확인 + 사용성 검증 끝난 뒤 커밋/푸시 예정.

## 배경

- 현재(`docs/changes/2026-07-08_web-ui-v0.3.4-3d-roi-picking.md` ~ `v0.4.5`): Canvas 뷰어에서 Face 클릭 토글 + 좌측 패널 체크박스. `ROI 선택 방식`은 `Combined`/`3D click only`/`Left panel only` 3가지.
- `docs/web-ui.md`에 "3차원 공간 선택(확장 예정)"이 이미 미구현 확장 지점으로 명시되어 있음 - 이 계획이 그 자리를 채운다.
- 일정이 촉박해 **V1 범위를 좁혔다**: 기존 Face 클릭/좌측 패널 방식은 그대로 두고 건드리지 않는다. 이번엔 **박스 드래그 하나만** 새로 추가한다. 좌표 지정은 "마우스 드래그가 예전에 제대로 구현된 적이 없었다"는 경험 때문에 넣는 **보완/대체 입력 경로**로, 박스 드래그와 나란히 준비하되 우선순위는 낮다.
- **기존 좌측 패널의 컴포넌트 체크박스(show/hide 가시성 토글)는 그대로 유지한다.** 이번 박스 드래그 작업과는 무관한 기능이라 건드리지 않음 - 새로 구현하는 코드가 이 체크박스 동작을 깨뜨리지 않도록 주의.
- 판정 규칙 자체는 `NX_RoiSelection`(C++, NX Open 기반) 챕터 설계에서 가져오되, 아래처럼 이번 V1에 맞게 단순화했다.

## V1으로 확정된 동작 (지난 대화에서 확인됨)

**실제 사용 흐름**: (1) 분석에 필요한 item(컴포넌트)을 먼저 파악 → (2) 기존 좌측 패널 체크박스로 필요 없는 컴포넌트는 Hide, 필요한 것만 Show로 정리 → (3) 그 상태에서 박스 드래그로 ROI 지정. 즉 **박스 드래그는 항상 "지금 Show 상태인 컴포넌트"만을 대상으로 한다.**

1. **뷰 고정**: 3D Viewer가 정면(XY) 또는 후면(-XY) **정투영 상태**일 때만 박스 드래그가 유효하다. 자유 회전 상태에서는 지원하지 않는다.
   - 이 덕분에 화면 좌표가 곧 모델의 X/Y 좌표다 (스케일/팬만 반영) - 카메라 투영 계산이 필요 없다. 이전 Box-Select Verifier가 하던 `camera.project()` 변환 자체가 불필요해짐 - Region-Clip Verifier 쪽 방식과 동일.
2. **Z축 무제한 (단, Hide된 컴포넌트는 애초에 후보에서 제외)**: 드래그 박스는 X/Y 평면의 사각형이고, Z 방향으로는 전혀 제한을 두지 않는다 - **Show 상태인 컴포넌트들의** XY 범위를 관통하는 무한 프리즘으로 취급한다. Hide된 컴포넌트는 그 XY 위치가 박스와 겹쳐도 결과에 안 들어간다 - "관련 없어서 숨겨둔 것"이 Z가 무제한이라는 이유로 도로 섞여 들어오면 안 되기 때문.
3. **판정 = Intersection만**: Window/Crossing 방향 구분 없이, **박스와 조금이라도 겹치면 선택**한다 (C++ 쪽 Window/Crossing 구분은 이번 V1엔 안 씀 - 필요해지면 나중에 추가).
4. **메타데이터는 Face 단위로 clip**: 컴포넌트 전체가 아니라, **박스와 실제로 겹치는 Face만** 골라서 그 Face들만으로 area/bbox/mesh를 만든다 (컴포넌트 통째로 포함시키지 않음). 여러 컴포넌트에 걸쳐 있으면 컴포넌트별로 결과가 나뉜다.
5. **좌표 지정은 보완 경로**: 박스 드래그와 별개로, 좌표 3개를 입력하면 그 좌표를 포함/최근접하는 Face(들)를 바로 찾아주는 기능을 나란히 준비한다. 드래그가 잘 안 될 때의 대체 수단. 이것도 Hide된 컴포넌트는 후보에서 제외하는 게 일관적일 것으로 보임(아래 "확인 필요" 참고).

## 반드시 지킬 것: 기존 데이터 계약

`docs/viewer-data-contract.md`(`mesh-scene.v1`)를 따른다:
- **ROI는 항상 `face_id[]`로 표현한다**
- `face_id` = `mesh.faces` 배열 index, `component_id` = `components[].component_id`
- 이미 있는 `mesh.face_areas_mm2`/`mesh.face_centroids`/`mesh.vertices`를 그대로 재사용 (NX처럼 별도 계산 API 필요 없음)

## 판정 알고리즘 (Face 단위 XY 교차 테스트)

카메라 투영이 필요 없으므로 이전 시뮬레이터들보다 더 단순하다:

1. **먼저 Hide 필터링**: 현재 Show 상태인 `component_id` 집합을 받아서, `mesh.face_component_ids`가 그 집합에 속하는 face만 후보로 남긴다 (Hide된 컴포넌트의 face는 이 시점에서 완전히 제외 - 이후 단계에서 아예 안 봄)
2. 드래그 시작/끝 지점을 뷰어의 스케일/팬 정보로 **모델 X/Y 좌표**로 변환 → `drag_rect = (x_min, x_max, y_min, y_max)`
3. 남은 후보 face 각각에 대해, 그 face를 이루는 3개 vertex의 X/Y만 보고 **face의 XY 바운딩박스**를 구한다 (Z는 무시)
4. `drag_rect`와 face의 XY 바운딩박스가 **조금이라도 겹치면**(표준 AABB-AABB overlap 테스트) 그 face를 결과에 포함
5. Z는 어디서도 비교하지 않음 - 이게 "무제한으로 선택"의 실제 구현 (단, 1번에서 Hide된 건 이미 빠진 상태)
6. 포함된 face 전체가 곧 "clip된 결과"다 - 별도의 폴리곤 재분할(sub-triangle clipping)은 하지 않는다. 경계에 걸친 삼각형은 통째로 포함되거나 제외되거나 둘 중 하나 (근사치이지만, mesh가 충분히 세밀하면 실용적으로 문제 없음 - 정말 필요해지면 나중에 실제 폴리곤 클리핑으로 정교화)

## 메타데이터/Mesh 계산 (포함된 face 목록 기준)

- **Area**: 포함된 face들의 `mesh.face_areas_mm2` 합
- **BoundingBox**: 포함된 face들이 참조하는 vertex 좌표의 min/max
- **Component 그룹화**: 포함된 face들을 `mesh.face_component_ids`로 묶어서, 컴포넌트별로 별도 결과 항목 생성 (하나의 드래그가 여러 컴포넌트에 걸치면 컴포넌트 수만큼 결과가 나옴)
- **Mesh 추출**: 포함된 face 자체가 이미 실제 mesh 데이터이므로 별도 삼각화 불필요 - 그 face들의 vertex/normal을 그대로 서브셋으로 반환

## ROI 스코프 (`scope_id`)

C++ 쪽 설계 그대로 유지: 국부 영역("하단 코너 확인 → 후면 중앙부 확인")을 독립적으로 관리. NX Hide 대신 데이터 레벨에서만 스코프 태깅.

## 데이터 모델 초안 (`types.py`에 추가 제안)

```python
@dataclass
class ROIRegionResult:
    scope_id: str
    drag_rect_xy: Tuple[float, float, float, float]  # (x_min, x_max, y_min, y_max), 모델 좌표
    view: str  # "front_xy" | "back_neg_xy"
    components: List["ROIComponentClip"]

@dataclass
class ROIComponentClip:
    component_id: int
    component_name: str
    face_indices: List[int]     # 이 컴포넌트에서 박스와 겹쳐 포함된 face만
    area_mm2: float
    bbox_min: Vec3
    bbox_max: Vec3

@dataclass
class ROIPointSelection:  # 보완 경로 (좌표 지정)
    coordinate: Vec3
    face_index: int
    component_id: Optional[int]
    note: str = ""
```

## 구현 단계

1. `types.py`: 위 `ROIRegionResult`/`ROIComponentClip`/`ROIPointSelection` 추가
2. `roi.py`: 순수 계산 함수 추가
   - `resolve_faces_in_xy_box(mesh, x_min, x_max, y_min, y_max, visible_component_ids) -> List[int]` - **먼저 `visible_component_ids`로 후보를 거른 뒤** Z 무시 AABB 교차 판정 (Hide된 컴포넌트는 애초에 후보에서 제외)
   - `group_faces_by_component(mesh, face_indices) -> List[ROIComponentClip]` - area/bbox 계산 포함
   - `resolve_nearest_face_to_point(mesh, coordinate, visible_component_ids) -> int` - 보완 경로용, 마찬가지로 Hide된 컴포넌트 제외
   - 전부 Three.js/뷰어 상태에 안 묶인 순수 함수로 작성 - 단위 테스트 가능
3. `run_web.py`: 정면/후면 정투영 상태 감지(또는 강제) + 드래그 이벤트 → 화면 좌표를 모델 XY로 역변환 + **현재 Show 상태인 component_id 목록(기존 좌측 패널 체크박스 상태)을 같이 넘김** → 위 함수 호출 + 좌표 입력 필드(보완 경로) UI
   - **실제 구현은 이보다 단순해졌다**: 화면 좌표 → 모델 XY 역변환을 새로 만들지 않고, 기존 Gap 드래그 선택이 쓰던 `scene.triList`의 화면 투영 좌표(`tri.p0.screenX/screenY` 등)를 그대로 재사용해 "화면 사각형 안에 삼각형 중심이 들어오는지"만 검사한다 (`selectRoiFacesInRect`). 정면/후면 정투영 뷰에서는 화면 X/Y = 모델 X/Y이므로 결과가 동일하고, 카메라 투영 역산 코드가 아예 필요 없다.
   - 정투영 상태 강제는 `snapCameraToNearestFrontBack()`이 ROI 모드를 "박스 드래그"로 바꾸는 순간 현재 yaw에서 더 가까운 쪽(XY 또는 -XY 프리셋)으로 자동 스냅해서 처리 - 사용자가 프리셋 버튼을 직접 누를 필요 없음.
   - Hide 필터는 `state.hiddenObjectIds`(신규 Show/Hide 토글)를 `selectRoiFacesInRect`/`resolveRoiPoint`에서 직접 참조해서 적용.
   - 좌표 입력 보완 경로는 `resolveRoiPoint()`가 `state.mesh.face_centroids`로 최근접 face를 client-side에서 찾아 스코프에 추가.
4. `engine.py`: `roi_face_indices` 연결 지점 재사용 (여러 컴포넌트에 걸치면 합쳐서 전달하거나 스코프별로 분리 - 아래 "확인 필요")
5. `docs/changes/2026-07-20_roi-native-selection.md`로 변경 기록

## 확인 필요 (구현 전/구현 중 결정할 것)

- ~~정면/후면 정투영 상태를 어떻게 강제/감지하나~~ → 해결됨: `snapCameraToNearestFrontBack()`이 박스 드래그 모드 진입 시 자동으로 더 가까운 정투영 프리셋(XY/-XY)으로 스냅하고, 실제 판정은 기존 Gap 방식과 동일하게 화면 투영 좌표(`scene.triList`)로 하므로 카메라 상태를 별도로 다시 읽어 판별할 필요가 없어짐.
- **경계에 걸친 face 처리**: 지금은 통째로 포함/제외 (근사) - 실제로 써보고 부정확하면 다음 단계에서 폴리곤 클리핑 고려
- **스코프가 여러 개면 실행을 어떻게 나누나**: 스코프별로 `engine.execute_run()`을 따로 돌릴지, 한 번에 다 돌리고 결과만 분리할지
- **팀(ROI 담당자) 확인**: "3차원 공간 선택" 문서상 자리와 이 구현이 같은 것으로 봐도 되는지
- **JS/Python 로직 이중 유지 부담**: `run_web.py`의 `groupFacesByComponentJs`는 `roi.py`의 `group_faces_by_component`를 손으로 미러링한 것 - 브라우저 미리보기(스코프 리스트)는 JS 계산 결과를 보여주지만, 실제 시뮬레이션 실행은 Python 쪽 `face_indices`만 넘겨서 Python이 다시 계산하므로 최종 결과의 정확성 자체는 영향 없음. 다만 둘이 어긋나면 미리보기 area/bbox 숫자가 실제 실행 결과와 다르게 보일 수 있어 - 스키마(`roi.py`) 바뀌면 이 JS 함수도 같이 수정해야 함.
- **브라우저 실사용 테스트 미완**: 이 세션에서는 Python 문법 검사 + 서버 부팅(HTTP 200)만 확인했고, 실제 브라우저에서 드래그/Hide 버튼/좌표 입력을 클릭해본 적은 없음 (에이전트 환경에 브라우저 자동화가 없음) - 커밋 전 사용자가 직접 클릭 테스트 필요.
