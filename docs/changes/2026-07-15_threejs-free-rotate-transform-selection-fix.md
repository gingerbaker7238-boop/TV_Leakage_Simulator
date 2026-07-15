# Three.js 자유회전 / 3D 선택 Transform 연결 보정

## 배경
- STEP 도면 로드 후 마우스 왼쪽 드래그로 3D view를 회전할 때 모델 아랫면까지 넘어가지 않는 각도 제한이 남아 있었다.
- 3D viewer에서 component를 클릭하면 하이라이트와 transform popup은 뜨지만, popup에 입력한 move/tilt 값이 실제 preview/apply 대상으로 안정적으로 연결되지 않는 문제가 있었다.

## 원인
- Three.js viewer가 `OrbitControls`의 기본 좌클릭 회전을 그대로 사용하고 있어 polar angle 경계에서 카메라가 위/아래 방향으로 완전히 넘어가지 못했다.
- 3D picking으로 component를 선택하는 경로는 `selectedGapObjectId`만 갱신하고, transform rule을 즉시 생성하지 않아 active transform rule이 없는 상태로 입력 popup이 열릴 수 있었다.

## 변경 사항
- `run_web.py`
  - Web UI 버전을 `v0.7.14`로 갱신했다.
  - 좌클릭 drag는 `OrbitControls` 대신 자체 quaternion 기반 free orbit으로 처리한다.
  - wheel zoom, middle drag rotate, right drag pan은 기존 control을 유지한다.
  - `Shift/Alt + 좌클릭 drag`는 기존처럼 view-axis roll로 동작한다.
  - 3D viewer에서 component를 클릭해 transform popup이 뜰 때 해당 component의 transform rule을 즉시 생성하고 active rule로 연결한다.

## 검증
- `run_web.py` Python compile 통과.
- 생성 HTML 내 JavaScript syntax check 통과.

## 사용자 확인 포인트
- 서버 재시작 후 `Web UI v0.7.14`인지 확인한다.
- 좌클릭 drag로 모델을 위/아래로 계속 돌려 아랫면이 보이는지 확인한다.
- 3D viewer에서 component 클릭 → transform popup 입력 → preview 표시 → Apply 후 이동 상태 유지 순서로 확인한다.
