# ROI 네이티브 선택 V1: 박스 드래그 + 좌표 지정 + Show/Hide

## 변경 목적
- STEP 기반 V1 파이프라인에서, 기존 Face 클릭/좌측 패널 선택 방식은 그대로 두고 **박스 드래그 ROI 선택**을 새로 추가한다.
- 정면(XY)/후면(-XY) 정투영 뷰에서만 동작하며, Z축은 무제한(무한 프리즘)으로 판정한다.
- 마우스 드래그가 여의치 않을 경우를 대비한 **좌표 지정(보완 경로)**을 나란히 제공한다.
- 분석 대상 컴포넌트를 먼저 Show/Hide로 정리한 뒤 ROI를 지정하는 실제 작업 흐름을 지원하기 위해, 진짜 **Show/Hide 뷰어 가시성 토글**을 신규로 추가한다 (기존 좌측 패널 체크박스는 "ROI에 포함" 용도이지 가시성 토글이 아니었음 - 그대로 유지, 건드리지 않음).

상세 설계 근거는 `docs/roi-native-selection-plan.md` 참고.

## Backend 구현
- `src/leakage_simulator/types.py`: `ROIRegionResult`, `ROIComponentClip`, `ROIPointSelection` dataclass 추가.
- `src/leakage_simulator/roi.py`: 순수 판정 함수 추가 (Three.js/뷰어 상태에 의존하지 않음, 단위 테스트 가능).
  - `resolve_faces_in_xy_box(mesh, x_min, x_max, y_min, y_max, face_component_ids, visible_component_ids=None)` - Z 무시 AABB 교차, `visible_component_ids`로 Hide 필터링.
  - `group_faces_by_component(mesh, face_indices, face_component_ids, component_names=None)` - 컴포넌트별 area/bbox 그룹화.
  - `resolve_faces_in_xy_box_grouped(...)` - 위 두 함수를 합쳐 `ROIRegionResult`로 반환.
  - `resolve_nearest_face_to_point(mesh, coordinate, face_component_ids=None, visible_component_ids=None)` / `build_point_selection(...)` - 좌표 지정 보완 경로.
- `mesh.faces`/`face_areas_mm2`/`face_centroids` 등 기존 `mesh-scene.v1` 계약을 그대로 재사용 - 별도 계산 API 불필요.
- `engine.py`는 수정하지 않음 - `execute_run(roi_face_indices=...)`가 `ROIRegionResult.face_indices`(flatten된 `List[int]`)를 그대로 받아들이는 것을 실제 STEP 파일 기반 end-to-end 테스트로 확인.

## Web UI (`run_web.py`)
- ROI 선택 방식 드롭다운에 `Box 드래그 (XY 평면, Z 무제한)` 옵션 추가.
- 신규 UI 블록: `roiBoxDragBlock`(스코프 라벨 입력 + 결과 리스트), `roiPointBlock`(X/Y/Z 좌표 입력 + `좌표로 Face 찾기` 버튼).
- `snapCameraToNearestFrontBack()`: 박스 드래그 모드 진입 시 현재 카메라 yaw에서 더 가까운 쪽(XY/-XY)으로 자동 정투영 스냅 - 사용자가 프리셋 버튼을 별도로 누를 필요 없음.
- `selectRoiFacesInRect(canvas, mode, rect)`: 기존 Gap 박스 드래그(`selectGapComponentsInRect`)가 쓰던 화면 투영 좌표(`scene.triList`) 방식을 그대로 재사용 - 정투영 뷰에서는 화면 X/Y = 모델 X/Y이므로 카메라 역투영 계산이 필요 없음. `state.hiddenObjectIds`에 속한 컴포넌트의 face는 후보에서 먼저 제외.
- `groupFacesByComponentJs`/`computeFaceBBox`/`addRoiScope`/`renderRoiScopeResults`: 선택된 face를 컴포넌트별로 묶어 area/bbox를 계산하고 `state.roiScopes`에 스코프로 누적, 결과 패널에 렌더링 (Python `group_faces_by_component`를 JS로 미러링 - 미리보기 전용, 실제 실행은 Python이 재계산).
- `resolveRoiPoint()`: 좌표 입력값과 `state.mesh.face_centroids`로 최근접 face를 client-side에서 찾아 스코프에 추가 (Hide 필터 동일 적용).
- `shouldUseDragSelection()`/mouseup 디스패치에 `state.roiSelectionMode === 'box_drag'` 분기 추가 - 기존 Gap 드래그 분기와 공존.

### 신규 Show/Hide 가시성 토글
- 컴포넌트 트리 각 행에 `Hide`/`Show` 버튼 추가 (`toggleObjectVisibility`).
- `state.hiddenObjectIds`(Set)로 상태 관리, `getHiddenComponentFaces()`/`getThreeHiddenFaces()`가 기존 Gap/Transform 전용이었던 `hiddenFaces`(Three.js `excludeFaces`) 메커니즘을 컴포넌트 단위로 확장 재사용 - 실제로 지오메트리에서 제외되어 렌더링됨 (기존 좌측 패널 "ROI 포함" 체크박스와는 완전히 별개 기능).
- `loadScene()` 시 `hiddenObjectIds`/`roiScopes` 초기화.

### 버그 수정: Three.js 렌더러에서 박스 드래그 자체가 안 되던 문제
1차 브라우저 테스트에서 드러남 - 정면 뷰 자동 전환까지는 되는데, 실제 드래그는 항상 카메라 회전으로만 동작했음.
- **원인**: Three.js가 기본 렌더러가 된 뒤 `.viewer-card.three-active .viewer-canvas { display:none; }`로 기존 2D 캔버스가 완전히 숨겨지면서, 그 캔버스에 붙어있던 `mousedown` 기반 박스-드래그 로직(`initViewerInteraction`)이 더 이상 입력을 받지 못함. 대신 위에 있는 Three.js 캔버스(`LeakageThreeViewer.handlePointerDown`)가 모든 포인터 입력을 가로채서 무조건 자유 회전(`freeRotateDrag`)으로 처리 - ROI/Gap 박스-드래그 모드를 전혀 몰랐음. 같은 이유로 기존 Gap 박스 드래그도 이 시점부터 잠재적으로 깨져 있었을 것으로 추정.
- **수정**: `LeakageThreeViewer.handlePointerDown`에 `isThreeBoxDragActive(ev)` 체크 추가 - ROI box_drag(armed 상태) 또는 Gap 드래그 모드일 때는 `this.controls.enabled = false`로 두고 `beginSelectionBoxForMode(ev, this.mode)`로 기존 `state.selectionBox` 흐름에 합류시킴. 이때 `preventDefault()`/`setPointerCapture()`는 의도적으로 호출하지 않음 - 호출하면 브라우저가 호환 `mousemove`/`mouseup` 이벤트 자체를 억제해서, `initViewerInteraction`의 `window` 레벨 mousemove/mouseup 리스너(박스 렌더링 + 최종 판정 dispatch)가 아예 못 받게 되기 때문.
- `handlePointerUp`/`handlePointerCancel`에 `boxDragActive` 플래그를 추가해 드래그 종료 시 OrbitControls를 다시 켜고, 진짜 클릭(pick)과 박스-드래그를 구분.

### 드래그 시인성(가시성) 개선
기존 드래그 사각형은 (구) 2D 캔버스에 그려졌는데, Three.js 활성 시 그 캔버스가 `display:none`이라 아예 안 보였음.
- `dragSelectOverlay`: `position:fixed`인 별도 div를 만들어 드래그 중 실시간으로 위치/크기를 갱신 (파란 점선 박스) - 렌더러 종류와 무관하게 항상 보임. 기존 Gap 박스 드래그에도 동일하게 적용됨 (`syncDragOverlay()`를 기존 `beginSelectionBox`/mousemove/mouseup 지점에도 추가).

### 버그 수정: 드래그는 되는데 항상 "선택 결과: 없음"이던 문제
위 픽업 버그를 고친 뒤 2차 브라우저 테스트에서 드러남 - 드래그 박스는 보이는데 뭘 드래그해도 항상 빈 결과.
- **원인**: `selectRoiFacesInRect`가 참조하는 `state.renderScenes.full/roi`(`scene.triList`, 화면 투영된 삼각형 좌표)는 `drawViewerOn()`이 채우는데, `drawViewer()`는 `state.viewerEngine === 'three'`일 때 `syncThreeViewer()`만 호출하고 `drawViewerOn()` 자체를 아예 건너뜀. 즉 Three.js가 기본 렌더러인 한(사실상 항상) `triList`가 채워질 일이 없어서 - Hide 여부와 무관하게 - 매번 빈 배열이었음. Gap의 기존 박스 드래그도 같은 이유로 잠재적으로 항상 빈 결과였을 것으로 추정.
- **수정**: `scene.triList` 의존을 완전히 버리고, Three.js 카메라로 드래그 박스의 화면 좌표 4개 모서리를 직접 모델 공간으로 역투영하는 `computeThreeXyBoxFromScreenRect()`를 추가. Box 드래그는 `snapCameraToNearestFrontBack()` 이후에만 armed 가능하므로 pitch=0, yaw=0|π가 보장되고, 이때 카메라 시선 방향은 정확히 world Z축과 일치 - 그래서 `controls.target`을 지나는 시선-수직 평면(Z=const)에 각 모서리의 ray를 교차시키면 원근 왜곡(keystone) 없이 정확한 모델 X/Y 사각형을 얻는다. 이 사각형을 `resolveFaceIndicesInXyBoxJs()`(= `roi.py`의 `resolve_faces_in_xy_box`를 JS로 그대로 미러링, Hide 필터 포함)에 넘겨 face를 고른다 - 화면 투영(centroid) 기반이 아니라 모델 공간 AABB 겹침 기반이라 Python 백엔드와 판정 기준이 완전히 동일해짐 (기존 계획의 "JS/Python 이중 유지" 한계가 오히려 줄어듦).
- `state.selectionBox`에 `engine: 'three'` 태그를 추가해, 좌표 저장 방식을 분리했다: Three 경로는 (구)캔버스가 `display:none`일 때 `getBoundingClientRect()`가 전부 0을 반환하는 문제를 피하기 위해 뷰포트 raw `clientX/clientY`를 그대로 저장하고, 해석 시점에 Three 캔버스의 실제(보이는) rect를 그때 가져와 사용한다. 기존 2D 캔버스 레거시 경로(`engine` 미설정)는 그대로 유지.

### 버그 수정: Box 드래그 모드에서도 회전이 되고, 드래그 도중 박스가 끊기던 문제
3차 브라우저 테스트 피드백: (1) ROI 드래그 선택을 ON 하기 전에도 화면이 회전돼서 정면/후면 뷰가 고정되지 않음. (2) ON 상태에서 드래그해도 박스 시작점만 찍히고 끝점(마우스를 뗀 위치)까지 못 따라가고 끊김.
- **(1) 회전 잠금**: 지금까지는 `roiBoxDragArmed`(ON 버튼)일 때만 회전을 막았는데, `Box 드래그` 모드를 고르기만 하고 아직 ON을 안 누른 상태에서는 여전히 자유 회전이 가능했음. `LeakageThreeViewer.handlePointerDown`에서 `state.roiSelectionMode === 'box_drag'`이면 (armed 여부와 무관하게) 좌클릭 드래그를 완전히 무시하도록 변경 - 이제 Box 드래그 모드를 고르는 순간부터 화면 방향이 고정되고, 줌(휠)/팬은 OrbitControls가 별도로 처리하므로 그대로 동작한다.
- **(2) 드래그 중 박스 끊김**: 드래그 중 `mousemove`마다 `drawViewer()` → `syncThreeViewer()` → Three.js 씬 전체를 다시 빌드(`setScene`)하고 있었음 - 이게 무거워서 마우스를 빠르게 움직이면 이벤트가 밀리고, 결과적으로 드래그 오버레이가 마지막 위치까지 못 따라가는 것처럼 보였음(회전 정지 문제와 겹쳐서 더 눈에 띄었을 것). Three 엔진 경로에서는 `mousemove`마다 `drawViewer()` 호출을 빼고 `syncDragOverlay()`(가벼운 DOM 위치 갱신)만 하도록 변경 - 3D 씬 자체는 드래그 중에 변할 이유가 없으므로 매 프레임 재빌드가 애초에 불필요했음.

### 버그 수정: 드래그를 놓아도(mouseup) 박스가 마지막 위치에 고정되지 않던 문제
4차 피드백: 화면 고정은 됐지만, 드래그를 마쳐도 박스가 마지막 지점에 멈추지 않고 계속 움직이며 영역이 안 잡힘 - ON 버튼도 클릭하면 바로 OFF로 되돌아가는 것처럼 보임.
- **원인**: `OrbitControls`는 생성자에서 `renderer.domElement`에 자신의 `pointerdown` 리스너를 등록하는데, 이게 `LeakageThreeViewer`가 나중에 등록하는 커스텀 `handlePointerDown`보다 항상 먼저 실행된다(리스너는 등록 순서대로 실행됨). 그래서 같은 pointerdown 이벤트 안에서 우리 코드가 `this.controls.enabled = false`로 끄기 *전에*, OrbitControls가 이미 `enabled === true` 상태로 자기 로직을 먼저 실행해 `setPointerCapture()`를 걸고 자체 pointermove/pointerup 리스너까지 등록해버림 - 이 경쟁 상태가 이후 드래그의 mouseup 처리(당시엔 `window` 레벨 `mousemove`/`mouseup` 호환 이벤트에 의존)를 불안정하게 만들었던 것으로 보인다. 또한 박스-드래그 자체가 `window`의 `mousemove`/`mouseup`(포인터다운을 취소하지 않아 브라우저가 만들어주는 호환 이벤트)에 의존하고 있어서, 다른 로직과 타이밍이 얽히기 쉬운 구조였다.
- **수정**: 두 가지를 함께 적용했다.
  1. `Box 드래그` 모드가 선택된 순간(armed 여부 무관) `threeFullRenderer.controls.enabled`/`threeRoiRenderer.controls.enabled`를 바로 꺼서(`setThreeOrbitControlsEnabled`), OrbitControls의 pointerdown 핸들러가 아예 `enabled === false`로 즉시 리턴하게 만들었다 - `setPointerCapture` 경쟁 자체가 발생하지 않는다.
  2. 박스-드래그를 `window` 레벨 호환 이벤트에 기대는 대신 `LeakageThreeViewer` 안에서 완결시키도록 재작성했다: `handlePointerDown`에서 직접 `setPointerCapture()`를 걸고 `preventDefault()`도 호출해서 호환 mousemove/mouseup 자체가 발생하지 않게 하고, `handlePointerMove`/`handlePointerUp`이 진짜 `pointermove`/`pointerup`(캡처되어 있어 커서가 다른 뷰어 카드 위로 벗어나도 계속 이 엘리먼트로 전달됨)으로 직접 좌표 갱신 + 최종 판정(`selectRoiFacesInThreeRect` 호출)까지 처리한다. 레거시 2D 캔버스 경로(`initViewerInteraction`의 `window` mousemove/mouseup)는 그대로 유지 - 서로 다른 이벤트 종류(호환 이벤트가 아예 안 생김)라 겹칠 일이 없다.

### ROI 드래그 선택 ON/OFF + 선택 결과 팝업
"드래그는 됐는데 뭔가 선택됐는지 모르겠다", "선택 후에도 계속 드래그=선택 모드로 남아 회전이 안 된다"는 피드백 반영.
- `state.roiBoxDragArmed`(기본 false) + `roiBoxDragArmToggle` 버튼 추가: Box 드래그 모드에서도 이 버튼을 눌러 명시적으로 ON 해야만 드래그가 박스-선택으로 동작 - OFF일 때는 그냥 화면 회전.
- `selectRoiFacesInRect()`가 실행되자마자(성공/실패 무관) `disarmRoiBoxDrag()`를 호출해 자동으로 OFF로 복귀 - 매번 다시 켜야 하므로 "계속 선택 모드로 남는" 문제가 사라짐.
- `showRoiScopePopup()`: 박스 드래그(빈 결과 포함) 또는 좌표 지정으로 스코프가 추가/시도될 때마다 화면 중앙 모달 팝업으로 결과(컴포넌트별 face 수/면적, 또는 "결과 없음")를 바로 보여줌 - 결과 패널 문구를 놓쳐서 "선택됐는지 모르겠다"는 상황을 방지.

### 버그 수정: `ReferenceError: THREE is not defined` (박스 드래그가 조용히 실패하던 진짜 원인)
try/finally로 감싼 뒤 콘솔에 실제로 찍힌 에러: `computeThreeXyBoxFromScreenRect`에서 `THREE is not defined`.
- **원인**: 이 페이지는 `<script type=\"module\">`(THREE를 `import`, ~line 2374)와 별개의 classic `<script>`(~line 3204, ROI 관련 함수들이 사는 곳)로 나뉘어 있음. ES 모듈의 `import` 바인딩은 그 모듈 스코프 밖으로 새어나가지 않으므로, classic 스크립트 쪽에서 `new THREE.Vector3(...)` 등을 쓰자마자 매번 예외가 났던 것.
- **수정**: module 스크립트에서 `window.THREE = THREE;`로 전역에 노출 - classic 스크립트에서도 `THREE`가 정상적으로 resolve됨.
- 안전장치로, 박스-드래그 판정 코드 전체(`selectRoiFacesInThreeRect`/레거시 `selectGapComponentsInRect` 경로 둘 다)를 `try/finally`로 감싸서, 앞으로 비슷한 예외가 나더라도 `state.selectionBox.active`/오버레이 정리는 항상 실행되도록 함 - 최소한 "박스가 커서에 붙어서 안 없어지는" 증상만은 재발하지 않게.

### 버그 수정: 회전 잠금이 "Box 드래그 모드 선택 여부"에 묶여 있어 선택 끝나고도 회전이 안 풀림
"선택 끝나면 회전도 마우스 조작 기능도 같이 풀리는 게 좋을 거 같다", "그 뒤에 리시버/이미터 설정하려면 도면은 돌아야 한다"는 피드백 반영.
- 이전 수정에서는 회전 잠금을 "Box 드래그 모드가 선택되어 있는 동안 전체"에 걸어놨었음 (드래그 여러 번 하는 중간에 실수로 뷰가 틀어지는 걸 막으려던 의도) - 그런데 이러면 드래그 하나 끝나서 ON/OFF 버튼이 자동으로 OFF로 돌아가도, 모드 자체는 여전히 "Box 드래그"라서 회전은 계속 잠긴 채로 남아있었음.
- **수정**: 회전 잠금을 `roiBoxDragArmed`(ON/OFF 버튼) 하나에만 연동하도록 단순화 (`updateRoiBoxDragArmUI()`가 `setThreeOrbitControlsEnabled(!armed)`를 직접 소유). ON 누르면 잠기고, 드래그가 끝나 자동으로 OFF 되면 즉시 회전도 풀림 - 이제 ROI를 다 만들고 나서 바로 화면을 돌려 Receiver/Emitter를 배치할 수 있음.

## V2: ROI 선택 방식을 Box 드래그(+좌표 보완)만 남기고 단순화, ROI List에 체크박스 추가
"드롭다운/Component 선택/Face 직접 입력을 없애고 마우스 드래그로 직관적으로만 쓰게 하자. 여러 영역을 만들어두고 체크박스로 켰다 껐다 하면서 분석하고 싶다"는 요청 반영. Scope List를 ROI List로 개명.

### 제거
- ROI 선택 방식 `<select>`(드롭다운: 선택 방식/Component 선택/3D view에서 선택/Box 드래그) 및 관련 UI(`componentSelectBlock`/`objectList` 체크박스 목록, `faceIndexBlock`/`roiFacesInput` 직접 입력) 전부 삭제.
- 연쇄적으로 제거된 JS: `state.clickedFaces`/`state.panelFaces`/`state.selectedObjectIds`, `refreshSelectionFromObject()`, `toggleClickedFace()`, `handleViewerPickFace()`의 `roiSelectionMode === 'click'` 분기, `objectList` 관련 렌더링/리스너(`roiInput` input 리스너, `roiSelectionMode` change 리스너, `refreshComponentNameDom()`의 `roiRow` 갱신 부분).
- `state.roiSelectionMode`는 내부적으로 `'box_drag'` 고정값만 남김(항상 참이 되므로 기존 `isThreeBoxDragActive`/`shouldUseDragSelection`/mouseup 디스패치의 조건문은 안전하게 그대로 둠 - 별도 리팩터 불필요).
- `updateSelectionModeUI()`는 모드 분기 없이 Gap 관련 힌트 텍스트만 갱신하도록 축소. 정면/후면 스냅(`snapCameraToNearestFrontBack()`)은 더 이상 "모드 진입 시" 트리거되지 않고, `roiBoxDragArmToggle`을 ON으로 켜는 순간으로 옮김(모드 전환 개념 자체가 없어졌으므로).
- 참고: `gapObjectList`(Hide/Show 버튼이 있는 Gap 컴포넌트 트리)는 `objectList`와 완전히 별개의 DOM/렌더링이라 영향 없음 - Show/Hide 기능은 그대로 유지됨.

### ROI List (구 Scope List) - 체크박스 + 삭제 버튼 + 실제 선택 반영
- 각 ROI 항목에 `id`(순번, `state.roiScopeSeq`로 발급 - 삭제 후에도 겹치지 않는 안정적 키), `active`(기본 `true`) 필드 추가.
- `renderRoiScopeResults()`가 각 항목 앞에 체크박스(활성/비활성)와 "삭제" 버튼을 렌더링. 체크박스를 끄면 `recomputeSelectedFaces()`가 다시 계산되어 그 ROI의 face가 실제 선택(`state.selectedFaces`)에서 즉시 빠짐 - 삭제는 목록 자체에서 제거.
- **핵심 연결**: `recomputeSelectedFaces()`를 완전히 다시 작성 - 기존엔 click/panel 모드만 반영하고 box_drag 스코프는 반영하지 않았음(즉 지금까지 ROI List는 "미리보기"였을 뿐 실제 ROI에는 전혀 반영 안 되고 있었음). 이제는 `state.roiScopes`에서 `active`인 것만 모아 `state.selectedFaces`를 만듦 - ROI List에 체크된 항목이 곧 실제 ROI.
- `addRoiScope()`가 스코프를 만들자마자 `active:true`로 넣고 바로 `recomputeSelectedFaces()`를 호출 - 드래그/좌표 지정 직후 별도 조작 없이 바로 반영됨.
- 여러 영역을 미리 만들어두고 체크박스로 켰다 껐다 하면서 반복 분석할 수 있음 - "할 때마다 ROI 다시 지정해야 하는 번거로움" 해소.
- 좌표 지정(`resolveRoiPoint`)도 동일하게 `addRoiScope()`를 거치므로 체크박스/삭제/즉시반영이 동일하게 적용됨 - 실행 경로가 박스 드래그와 갈라지지 않는지 코드 상으로 확인함(별도 브라우저 클릭 테스트는 필요).
- 문구를 "스코프" → "ROI"로 통일 (팝업 제목, 좌표 지정 결과 메시지, 목록 placeholder 등).

## 현재 한계
- 경계에 걸친 face는 폴리곤 재분할 없이 통째로 포함/제외 (근사) - 정밀도가 문제되면 향후 실제 클리핑 고려.
- JS 쪽 `groupFacesByComponentJs`는 미리보기용 수동 미러링이라, `roi.py` 스키마가 바뀌면 같이 고쳐야 함.
- **브라우저 실사용 테스트 진행 중**: 여러 차례 실제 클릭/드래그 테스트 → 버그 발견 → 수정을 반복해서 현재 버전까지 왔음(회전 잠금 경쟁, THREE 참조 에러, 박스 좌표계 문제, 회전 미복구 등). ROI List 체크박스/삭제/즉시반영은 이번 라운드에서 코드만 작성했고 아직 브라우저에서 직접 클릭해보지 못함 - 특히 체크박스로 여러 ROI를 켰다 껐다 할 때 `state.selectedFaces`가 기대대로 합쳐지는지는 다음 테스트에서 확인 필요.
- **실제 시뮬레이션 실행과는 아직 분리되어 있음**: `state.selectedFaces`(ROI List에서 활성화된 face 집합)는 지금 ROI 미리보기/통계(`roiStat`, `updateViewerMode`)에는 반영되지만, 실제 ray trace를 실행하는 `/api/raytrace/direct`(`runDirectRayTrace()`가 호출)는 emitter/receiver/material/transform만 payload에 넣고 ROI face 목록은 아예 보내지 않음. 즉 지금 이 UI에서 ROI를 아무리 골라도 "실행" 버튼을 누르면 ROI와 무관하게 전체 모델로 시뮬레이션이 돈다 - ROI를 실제 실행에 반영하려면 이 엔드포인트(또는 백엔드 `execute_run`)에 `roi_face_indices`를 연결하는 별도 작업이 필요함 (기존 `roi_faces` 폼 필드는 다른/구버전 실행 경로에서만 읽힘).

## 자동 검증
- `tests/test_roi_native_selection.py` (신규, 9개 테스트, 전부 통과): Z 무제한 프리즘 동작, Hide 컴포넌트 제외, 박스 밖 빈 결과, 경계 겹침 근사, 컴포넌트별 area 합산, `ROIRegionResult` end-to-end 형태, 좌표 지정 최근접 검색(Hide 필터 포함) 검증.
- 실제 STEP 파일(`samples/tv_leakage_full_assembled_no_gap.stp`, 116 face) 기반 end-to-end 확인: `resolve_faces_in_xy_box_grouped` 결과 `face_indices`를 `engine.execute_run()`에 코드 수정 없이 그대로 전달해 정상 실행됨.

## 상태
로컬 전용 구현. 팀 확인 + 브라우저 사용성 검증 완료 전까지 커밋/푸시하지 않음.
