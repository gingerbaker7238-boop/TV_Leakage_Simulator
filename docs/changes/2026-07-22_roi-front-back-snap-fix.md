# 버그 수정: ROI 박스 드래그가 -XY(후면) 뷰로 스냅되지 않던 문제

## 증상
"ROI 지정 시, -XY면 뷰는 설정이 안 되어 있는거 같애. 무조건 XY면임" - 화면을 뒤로 돌려놓고 "+ ROI 추가"를 눌러도 항상 정면(XY)으로만 스냅됨.

## 원인
`snapCameraToNearestFrontBack()`이 `state.transform.yaw`를 보고 정면/후면 중 가까운 쪽으로 스냅할지 결정하는데, **이 필드는 Three.js가 활성 렌더러인 동안 전혀 갱신되지 않는 죽은 값**이었다. 실제 마우스 자유 회전(`LeakageThreeViewer.freeRotateCamera`)은 `this.camera`/`this.controls`를 직접 조작할 뿐 `state.transform`에는 아무것도 기록하지 않는다 - `state.transform.yaw`는 초기값(0.7) 또는 마지막으로 프리셋 버튼을 눌렀을 때 값에 그대로 고정되어 있었다. 그래서 사용자가 실제로 화면을 어떻게 돌려놨든, 판정은 항상 그 낡은 값(항상 정면에 더 가까운 값)만 보고 있었던 것.

## 수정
`snapCameraToNearestFrontBack()`이 `state.transform.yaw` 대신 **`threeFullRenderer.camera.position`의 실제 현재 Z 위치**(모델 중심 대비)를 직접 읽어서 정면/후면을 판정하도록 변경 (`run_web.py`). Three 렌더러가 아직 준비 안 된 극히 드문 경우를 위해 기존 yaw 기반 로직은 폴백으로 남겨둠.

## 검증
- Python 문법 검사, 서버 재부팅(HTTP 200) 확인.
- **브라우저 실사용 테스트 필요**: 화면을 뒤로 돌린 상태에서 "+ ROI 추가"를 눌러 -XY로 정확히 스냅되는지 사용자 확인 대기 중.

## 상태
로컬 전용. 커밋/푸시 안 함.
